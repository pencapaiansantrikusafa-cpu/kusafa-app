-- ============================================================================
-- T7a: Target dinamis - fondasi database (skema + RPC + view + change_log)
-- Keputusan Mudir (HANDOVER 3, 26 Nov 2026): lihat bagian (a)-(g).
-- Prinsip: aturan bisnis di database (RPC/view/RLS), bukan di frontend.
-- ============================================================================

-- 1) Kolom tambahan targets (e): alasan penolakan wajib, pelacak penolak.
alter table public.targets
  add column if not exists alasan_tolak text,
  add column if not exists rejected_by uuid references public.profiles(id),
  add column if not exists rejected_at timestamptz;

comment on column public.targets.alasan_tolak is
  'Alasan penolakan target. WAJIB saat status ditolak.';
comment on column public.targets.rejected_by is 'Pengguna yang menolak target.';
comment on column public.targets.rejected_at is 'Waktu penolakan target.';

-- 2) change_log untuk targets (b). Trigger generik catat_perubahan sudah ada.
drop trigger if exists catat_perubahan_targets on public.targets;
create trigger catat_perubahan_targets
  after update or delete on public.targets
  for each row execute function public.catat_perubahan();

-- 3) View laporan: kasus (f) + bulan 0.
--    - bulan 0 (month_no=0) => target_monthly NULL
--    - tidak ada target disetujui => NULL
--    - harian: effective_days/hadir NULL => NULL; hadir=0 dan target ada => 0
--    - bulanan (Wasilah/Ghayah): amount langsung, tidak dikali Hadir
--    - individu didahulukan dari halaqah, effective_month_id terbaru, lintas tahun
create or replace view public.v_monthly_report_base with (security_invoker = true) as
select
  e.id as entry_id, e.student_id, e.halaqah_id, e.subject_id, sj.domain,
  e.month_id, vm.hijri_year, vm.month_no, vm.name as month_name, vm.prev_month_id,
  e.item_id, ci.label as item_label, e.putaran,
  pe.item_id as prev_item_id, pci.label as prev_item_label, pe.putaran as prev_putaran,
  public.item_position(e.item_id, e.putaran) as pos,
  case when pe.id is null then null
       else public.item_position(e.item_id, e.putaran) - public.item_position(pe.item_id, pe.putaran) end as selisih,
  att.hadir, att.effective_days,
  tgt.id as target_id, tgt.amount as target_amount, tgt.amount_period as target_period,
  case
    when vm.month_no = 0 then null
    when tgt.id is null then null
    when tgt.amount_period = 'harian' then
      case
        when att.effective_days is null then null
        when att.hadir is null then null
        else tgt.amount * att.hadir
      end
    else tgt.amount
  end as target_monthly
from public.progress_entries e
join public.subjects sj on sj.id = e.subject_id
join public.curriculum_items ci on ci.id = e.item_id
join public.v_months_ordered vm on vm.id = e.month_id
left join public.progress_entries pe
  on pe.student_id = e.student_id and pe.subject_id = e.subject_id and pe.month_id = vm.prev_month_id
left join public.curriculum_items pci on pci.id = pe.item_id
left join public.v_attendance att
  on att.student_id = e.student_id and att.month_id = e.month_id and att.domain = sj.domain
left join lateral (
  select t.* from public.targets t
  join public.v_months_ordered tm on tm.id = t.effective_month_id
  where t.status = 'disetujui' and t.subject_id = e.subject_id and tm.ord <= vm.ord
    and (t.student_id = e.student_id or (t.student_id is null and t.halaqah_id = e.halaqah_id))
  order by (t.student_id is not null) desc, tm.ord desc
  limit 1
) tgt on true;

create or replace view public.v_monthly_report with (security_invoker = true) as
select b.*,
       (b.selisih < b.target_monthly) as below_target,
       (b.hadir < b.effective_days) as attendance_short
from public.v_monthly_report_base b;

-- 4) Helper RPC target

-- Bulan berjalan per domain: bulan non-0 dengan ord terbesar yang punya setting.
create or replace function public.target_bulan_berjalan(p_domain public.domain_kind)
returns uuid language sql stable security definer set search_path = public, pg_temp as $$
  select m.id
  from public.v_months_ordered m
  join public.month_domain_settings s on s.month_id = m.id and s.domain = p_domain
  where m.month_no <> 0
  order by m.ord desc limit 1
$$;

-- Info konfirmasi: lewat/terkunci/bulan 0. (b)
create or replace function public.target_info_konfirmasi(p_month_id uuid, p_domain public.domain_kind)
returns jsonb language plpgsql stable security definer set search_path = public, pg_temp as $$
declare
  v_ord integer; v_no integer; v_cur_ord integer; v_locked boolean; v_lewat boolean;
begin
  select vm.ord, vm.month_no into v_ord, v_no from public.v_months_ordered vm where vm.id = p_month_id;
  if v_ord is null then raise exception 'Bulan tidak ditemukan.'; end if;
  select vm.ord into v_cur_ord
  from public.v_months_ordered vm
  join public.month_domain_settings s on s.month_id = vm.id and s.domain = p_domain
  where vm.month_no <> 0
  order by vm.ord desc limit 1;
  v_lewat := v_cur_ord is not null and v_ord < v_cur_ord;
  select coalesce(s.is_locked, false) into v_locked
  from public.month_domain_settings s where s.month_id = p_month_id and s.domain = p_domain;
  return jsonb_build_object(
    'month_no', v_no,
    'lewat', coalesce(v_lewat,false),
    'terkunci', coalesce(v_locked,false),
    'perlu_konfirmasi', coalesce(v_lewat,false) or coalesce(v_locked,false)
  );
end $$;

create or replace function public.target_cek_konfirmasi(
  p_month_id uuid, p_domain public.domain_kind, p_konfirmasi boolean
) returns void language plpgsql stable security definer set search_path = public, pg_temp as $$
declare v_info jsonb;
begin
  v_info := public.target_info_konfirmasi(p_month_id, p_domain);
  if (v_info->>'perlu_konfirmasi')::boolean then
    if not public.is_full_access() then
      if (v_info->>'lewat')::boolean then
        raise exception 'Bulan target sudah lewat. Hanya Mudir/Admin yang dapat mengubahnya dengan konfirmasi eksplisit.';
      else
        raise exception 'Bulan target terkunci. Hanya Mudir/Admin yang dapat mengubahnya dengan konfirmasi eksplisit.';
      end if;
    end if;
    if not coalesce(p_konfirmasi, false) then
      if (v_info->>'lewat')::boolean then
        raise exception 'Bulan target sudah lewat. Konfirmasi eksplisit diperlukan.';
      else
        raise exception 'Bulan target terkunci. Konfirmasi eksplisit diperlukan.';
      end if;
    end if;
  end if;
end $$;

-- Hak pengaju (a): pengampu hanya santri/halaqah yang diampu; Masul domain/Mudir/Admin boleh.
create or replace function public.target_boleh_ajukan(
  p_domain public.domain_kind, p_subject_id uuid, p_student_id uuid, p_halaqah_id uuid
) returns boolean language plpgsql stable security definer set search_path = public, pg_temp as $$
declare v_role public.app_role;
begin
  v_role := public.current_app_role();
  if v_role is null then return false; end if;
  if public.is_full_access() or public.is_masul_of(p_domain) then return true; end if;
  if p_student_id is not null then
    return coalesce(public.student_in_taught_halaqah(p_student_id, p_subject_id), false);
  end if;
  if p_halaqah_id is not null then
    return coalesce(public.teaches_halaqah_subject(p_halaqah_id, p_subject_id), false);
  end if;
  return false;
end $$;

-- Validasi bentuk target (c,g)
create or replace function public.target_validasi_bentuk(
  p_domain public.domain_kind, p_subject_id uuid, p_student_id uuid, p_halaqah_id uuid, p_amount_period public.target_period
) returns void language plpgsql stable security definer set search_path = public, pg_temp as $$
declare v_subj_domain public.domain_kind;
begin
  if p_subject_id is null then raise exception 'Mata pelajaran wajib diisi.'; end if;
  select domain into v_subj_domain from public.subjects where id = p_subject_id;
  if v_subj_domain is null then raise exception 'Mata pelajaran tidak ditemukan.'; end if;
  if v_subj_domain <> p_domain then raise exception 'Mata pelajaran tidak sesuai domain.'; end if;
  if (p_student_id is null) = (p_halaqah_id is null) then
    raise exception 'Isi tepat satu: santri (individu) atau halaqah.';
  end if;
  if p_domain = 'alquran' then
    if p_student_id is null then raise exception 'Target Al Qur''an harus per santri.'; end if;
    if p_amount_period <> 'harian' then raise exception 'Target Al Qur''an harus harian.'; end if;
  elsif p_domain in ('wasilah','ghayah') then
    if p_halaqah_id is null then raise exception 'Target Wasilah/Ghayah harus per halaqah.'; end if;
    if p_amount_period <> 'bulanan' then raise exception 'Target Wasilah/Ghayah harus bulanan (tidak dikali Hadir).'; end if;
  end if;
end $$;
