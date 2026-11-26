-- T7a: massal Al Qur'an membuat target per santri (student_id), bukan per halaqah.
-- Constraint targets mewajibkan tepat satu dari student_id/halaqah_id.
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
  v_bulan uuid;
  v_status public.target_status;
  v_approved_by uuid; v_approved_at timestamptz;
  v_n integer := 0;
  v_sid uuid;
begin
  if v_uid is null then raise exception 'Harus masuk.'; end if;
  if p_amount is null or p_amount < 0 then raise exception 'Nilai target wajib diisi dan tidak boleh negatif.'; end if;
  if not exists (select 1 from public.halaqahs h where h.id=p_halaqah_id and h.domain='alquran') then
    raise exception 'Halaqah Al Qur''an tidak ditemukan.';
  end if;
  if not exists (select 1 from public.subjects s where s.id=p_subject_id and s.domain='alquran') then
    raise exception 'Mata pelajaran Al Qur''an tidak ditemukan.';
  end if;
  if not (public.is_full_access() or public.is_masul_of('alquran')
          or public.teaches_halaqah_subject(p_halaqah_id,p_subject_id)) then
    raise exception 'Anda tidak berhak mengajukan target massal untuk halaqah ini.';
  end if;
  v_bulan := coalesce(p_effective_month_id, public.target_bulan_berjalan('alquran'));
  if v_bulan is null then raise exception 'Bulan berlaku tidak ditemukan.'; end if;
  if exists (select 1 from public.hijri_months m where m.id=v_bulan and m.month_no=0) then
    raise exception 'Bulan Data Awal tidak dapat menjadi bulan berlaku target.';
  end if;
  perform public.target_cek_konfirmasi(v_bulan,'alquran',p_konfirmasi);
  if public.is_full_access() or public.is_masul_of('alquran') then
    v_status := 'disetujui'; v_approved_by := v_uid; v_approved_at := now();
  else
    v_status := 'diajukan'; v_approved_by := null; v_approved_at := null;
  end if;
  for v_sid in
    select hm.student_id from public.halaqah_members hm
    where hm.halaqah_id=p_halaqah_id and hm.left_on is null
  loop
    insert into public.targets
      (domain,subject_id,student_id,halaqah_id,effective_month_id,amount,amount_period,
       status,proposed_by,approved_by,approved_at,note)
    values ('alquran',p_subject_id,v_sid,null,v_bulan,p_amount,'harian',
            v_status,v_uid,v_approved_by,v_approved_at,nullif(trim(p_note),''));
    v_n := v_n + 1;
  end loop;
  return jsonb_build_object('status',v_status,'effective_month_id',v_bulan,'jumlah_santri',v_n);
end $$;
