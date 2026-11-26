-- ============================================================================
-- T7a lanjutan 2: ubah target (baris baru) + ajukan massal Al Qur'an + riwayat
-- ============================================================================

-- 8) Ubah target = buat baris BARU, target lama tetap utuh. (b)
create or replace function public.ubah_target(
  p_target_lama_id uuid,
  p_amount numeric,
  p_effective_month_id uuid default null,
  p_note text default null,
  p_konfirmasi boolean default false
) returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_lama public.targets%rowtype;
  v_bulan uuid;
  v_status public.target_status;
  v_id uuid;
  v_approved_by uuid;
  v_approved_at timestamptz;
begin
  if v_uid is null then raise exception 'Harus masuk.'; end if;
  select * into v_lama from public.targets where id = p_target_lama_id;
  if not found then raise exception 'Target lama tidak ditemukan.'; end if;

  if p_amount is null or p_amount < 0 then
    raise exception 'Nilai target wajib diisi dan tidak boleh negatif.';
  end if;

  if not public.target_boleh_ajukan(v_lama.domain, v_lama.subject_id, v_lama.student_id, v_lama.halaqah_id) then
    raise exception 'Anda tidak berhak mengubah target ini.';
  end if;

  v_bulan := coalesce(p_effective_month_id, public.target_bulan_berjalan(v_lama.domain));
  if v_bulan is null then raise exception 'Bulan berlaku tidak ditemukan.'; end if;
  if exists (select 1 from public.hijri_months m where m.id = v_bulan and m.month_no = 0) then
    raise exception 'Bulan Data Awal tidak dapat menjadi bulan berlaku target.';
  end if;

  perform public.target_cek_konfirmasi(v_bulan, v_lama.domain, p_konfirmasi);

  if public.is_full_access() or public.is_masul_of(v_lama.domain) then
    v_status := 'disetujui'; v_approved_by := v_uid; v_approved_at := now();
  else
    v_status := 'diajukan'; v_approved_by := null; v_approved_at := null;
  end if;

  insert into public.targets
    (domain, subject_id, student_id, halaqah_id, effective_month_id, amount, amount_period,
     status, proposed_by, approved_by, approved_at, note)
  values
    (v_lama.domain, v_lama.subject_id, v_lama.student_id, v_lama.halaqah_id, v_bulan, p_amount, v_lama.amount_period,
     v_status, v_uid, v_approved_by, v_approved_at, nullif(trim(p_note), ''))
  returning id into v_id;

  return jsonb_build_object('id', v_id, 'status', v_status, 'effective_month_id', v_bulan, 'menggantikan', p_target_lama_id);
end $$;

-- 9) Ajukan target massal Al Qur'an per halaqah (c): buat baris per santri.
--    Hanya untuk domain alquran, target per santri harian. Pengampu boleh untuk
--    halaqah yang diampu; Masul/Mudir/Admin boleh.
create or replace function public.ajukan_target_massal_alquran(
  p_halaqah_id uuid,
  p_subject_id uuid,
  p_effective_month_id uuid default null,
  p_amount numeric default null,
  p_note text default null,
  p_konfirmasi boolean default false
) returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_domain public.domain_kind := 'alquran';
  v_bulan uuid;
  v_status public.target_status;
  v_approved_by uuid; v_approved_at timestamptz;
  v_n integer := 0;
  v_sid uuid;
begin
  if v_uid is null then raise exception 'Harus masuk.'; end if;
  if p_amount is null or p_amount < 0 then raise exception 'Nilai target wajib diisi dan tidak boleh negatif.'; end if;

  -- harus halaqah alquran dan mapel alquran
  if not exists (select 1 from public.halaqahs h where h.id = p_halaqah_id and h.domain = 'alquran') then
    raise exception 'Halaqah Al Qur''an tidak ditemukan.';
  end if;
  perform public.target_validasi_bentuk('alquran', p_subject_id, '00000000-0000-0000-0000-000000000001'::uuid, null, 'harian');
  -- validasi_bentuk di atas butuh salah satu; kita cek manual bentuk massal alquran:
  if not exists (select 1 from public.subjects s where s.id=p_subject_id and s.domain='alquran') then
    raise exception 'Mata pelajaran Al Qur''an tidak ditemukan.';
  end if;

  if not (public.is_full_access() or public.is_masul_of('alquran') or public.teaches_halaqah_subject(p_halaqah_id, p_subject_id)) then
    raise exception 'Anda tidak berhak mengajukan target massal untuk halaqah ini.';
  end if;

  v_bulan := coalesce(p_effective_month_id, public.target_bulan_berjalan('alquran'));
  if v_bulan is null then raise exception 'Bulan berlaku tidak ditemukan.'; end if;
  if exists (select 1 from public.hijri_months m where m.id = v_bulan and m.month_no = 0) then
    raise exception 'Bulan Data Awal tidak dapat menjadi bulan berlaku target.';
  end if;
  perform public.target_cek_konfirmasi(v_bulan, 'alquran', p_konfirmasi);

  if public.is_full_access() or public.is_masul_of('alquran') then
    v_status := 'disetujui'; v_approved_by := v_uid; v_approved_at := now();
  else
    v_status := 'diajukan'; v_approved_by := null; v_approved_at := null;
  end if;

  for v_sid in
    select hm.student_id
    from public.halaqah_members hm
    where hm.halaqah_id = p_halaqah_id and hm.left_on is null
  loop
    insert into public.targets
      (domain, subject_id, student_id, halaqah_id, effective_month_id, amount, amount_period,
       status, proposed_by, approved_by, approved_at, note)
    values
      ('alquran', p_subject_id, v_sid, p_halaqah_id, v_bulan, p_amount, 'harian',
       v_status, v_uid, v_approved_by, v_approved_at, nullif(trim(p_note), ''));
    v_n := v_n + 1;
  end loop;

  return jsonb_build_object('status', v_status, 'effective_month_id', v_bulan, 'jumlah_santri', v_n);
end $$;

-- 10) Riwayat target untuk satu sasaran (santri+mapel atau halaqah+mapel). (b,e)
create or replace function public.riwayat_target(
  p_subject_id uuid,
  p_student_id uuid default null,
  p_halaqah_id uuid default null
) returns jsonb
language plpgsql stable security definer set search_path = public, pg_temp as $$
declare v_res jsonb;
begin
  if (p_student_id is null) = (p_halaqah_id is null) then
    raise exception 'Isi tepat satu: santri atau halaqah.';
  end if;
  select coalesce(jsonb_agg(row_to_json(x) order by x.ord desc, x.created_at desc), '[]'::jsonb)
  into v_res
  from (
    select t.id, t.amount, t.amount_period, t.status, t.note, t.alasan_tolak,
           t.effective_month_id, vm.name as bulan_berlaku, vm.month_no, vm.hijri_year, vm.ord,
           t.proposed_by, pb.full_name as pengaju,
           t.approved_by, ab.full_name as penyetuju, t.approved_at,
           t.rejected_by, rb.full_name as penolak, t.rejected_at,
           t.created_at
    from public.targets t
    join public.v_months_ordered vm on vm.id = t.effective_month_id
    left join public.profiles pb on pb.id = t.proposed_by
    left join public.profiles ab on ab.id = t.approved_by
    left join public.profiles rb on rb.id = t.rejected_by
    where t.subject_id = p_subject_id
      and ((p_student_id is not null and t.student_id = p_student_id)
        or (p_halaqah_id is not null and t.student_id is null and t.halaqah_id = p_halaqah_id))
  ) x;
  return v_res;
end $$;
