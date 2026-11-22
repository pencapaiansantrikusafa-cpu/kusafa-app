-- KUSAFA: perhitungan posisi, selisih, kehadiran, dan status target. Semua view memakai security_invoker agar RLS tetap berlaku.

-- posisi = value + value_offset + (putaran - 1) * cycle_length (bila siklik)
create or replace function public.item_position(p_item uuid, p_putaran integer default 1)
returns numeric language sql stable as $$
  select ci.value + b.value_offset
         + case when b.is_cyclic then (coalesce(p_putaran, 1) - 1) * b.cycle_length else 0 end
  from public.curriculum_items ci
  join public.books b on b.id = ci.book_id
  where ci.id = p_item
$$;

-- Urutan bulan lintas tahun ajaran. Bulan pembanding = bulan sebelumnya dalam urutan ini
-- (Syawwal dibandingkan dengan Ramadhan tahun lalu; bulan 0 hanya ada pada tahun pertama pemakaian).
create or replace view public.v_months_ordered with (security_invoker = true) as
select m.id, m.academic_year_id, ay.hijri_year, m.month_no, m.name, m.semester,
       (ay.hijri_year * 100 + m.month_no) as ord,
       lag(m.id) over (order by ay.hijri_year, m.month_no) as prev_month_id
from public.hijri_months m
join public.academic_years ay on ay.id = m.academic_year_id;

-- effective_days = Hari Efektif khusus santri bila ada, selain itu Hari Efektif domain pada bulan itu.
create or replace view public.v_attendance with (security_invoker = true) as
select a.student_id, a.month_id, a.domain,
       coalesce(a.effective_days_override, s.effective_days) as effective_days,
       a.izin, a.sakit, a.alpha,
       case when coalesce(a.effective_days_override, s.effective_days) is null then null
            else coalesce(a.effective_days_override, s.effective_days) - (a.izin + a.sakit + a.alpha) end as hadir
from public.attendance a
left join public.month_domain_settings s on s.month_id = a.month_id and s.domain = a.domain;

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
  case when tgt.id is null then null
       when tgt.amount_period = 'harian' then tgt.amount * att.hadir
       else tgt.amount end as target_monthly
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
  -- target disetujui terbaru yang berlaku; target individu didahulukan dari target halaqah
  select t.* from public.targets t
  join public.v_months_ordered tm on tm.id = t.effective_month_id
  where t.status = 'disetujui' and t.subject_id = e.subject_id and tm.ord <= vm.ord
    and (t.student_id = e.student_id or (t.student_id is null and t.halaqah_id = e.halaqah_id))
  order by (t.student_id is not null) desc, tm.ord desc
  limit 1
) tgt on true;

-- Selisih boleh negatif (santri mengulang). below_target dan attendance_short hanya bernilai bila datanya lengkap.
create or replace view public.v_monthly_report with (security_invoker = true) as
select b.*,
       (b.selisih < b.target_monthly) as below_target,
       (b.hadir < b.effective_days) as attendance_short
from public.v_monthly_report_base b;

-- ---------------------------------------------------------------------------------------------
-- Pengelolaan dropdown Wasilah dan Ghayah (nilai = nomor urut baris dalam buku).
-- Setelah menambah, menyisipkan, atau memindah item, panggil resequence_subject agar seq, value,
-- dan value_offset buku-buku di bidang itu konsisten. Menyisipkan item di tengah buku menambah jarak
-- antara item sebelum dan sesudahnya, sehingga selisih lama yang melintasi titik itu ikut berubah.
-- Nilai Al Qur'an diisi manual lewat kolom value dan tidak dihitung ulang.
-- Fungsi berjalan sebagai pemanggil, jadi RLS berlaku (Mudir/Admin atau Masul sesuai domain).
create or replace function public.resequence_subject(p_subject uuid) returns void
language plpgsql as $$
declare
  v_domain public.domain_kind;
  b record;
  v_run integer := 0;
  v_n integer;
begin
  select domain into v_domain from public.subjects where id = p_subject;
  if v_domain is null then raise exception 'Bidang tidak ditemukan.'; end if;
  if v_domain = 'alquran' then
    raise exception 'Nilai Al Qur''an diisi manual dan tidak dihitung ulang otomatis.';
  end if;
  set constraints all deferred;
  for b in select id from public.books where subject_id = p_subject order by stage_order, sort_order, name loop
    update public.books set value_offset = v_run where id = b.id;
    update public.curriculum_items ci
       set seq = r.rn, value = r.rn
      from (select id, row_number() over (order by seq, id)::integer as rn
              from public.curriculum_items where book_id = b.id) r
     where ci.id = r.id;
    select count(*) into v_n from public.curriculum_items where book_id = b.id;
    v_run := v_run + v_n;
  end loop;
end $$;

-- p_ordered = SEMUA id item buku itu dalam urutan baru.
create or replace function public.reorder_items(p_book uuid, p_ordered uuid[]) returns void
language plpgsql as $$
begin
  set constraints all deferred;
  update public.curriculum_items ci
     set seq = o.ord
    from unnest(p_ordered) with ordinality as o(id, ord)
   where ci.id = o.id and ci.book_id = p_book;
  perform public.resequence_subject((select subject_id from public.books where id = p_book));
end $$;
