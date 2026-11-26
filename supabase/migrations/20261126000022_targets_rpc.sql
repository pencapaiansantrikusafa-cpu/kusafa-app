-- ============================================================================
-- T7a lanjutan: RPC pengelolaan target (ajukan/setujui/tolak/ubah/riwayat/massal)
-- Semua RPC cek hak di dalam fungsi; anon tidak diberi EXECUTE.
-- ============================================================================

-- 5) Ajukan / buat target (baris baru). (a,b,d)
--    - Pengampu: hanya santri/halaqah yang diampu, status diajukan.
--    - Masul domain sendiri / Mudir / Admin: status disetujui.
--    - Bulan lewat/terkunci: hanya Mudir/Admin dengan p_konfirmasi=true.
create or replace function public.ajukan_target(
  p_domain public.domain_kind,
  p_subject_id uuid,
  p_student_id uuid default null,
  p_halaqah_id uuid default null,
  p_effective_month_id uuid default null,
  p_amount numeric default null,
  p_amount_period public.target_period default null,
  p_note text default null,
  p_konfirmasi boolean default false
) returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_role public.app_role;
  v_bulan uuid;
  v_status public.target_status;
  v_id uuid;
  v_approved_by uuid;
  v_approved_at timestamptz;
begin
  if v_uid is null then
    raise exception 'Harus masuk untuk mengajukan target.';
  end if;
  v_role := public.current_app_role();
  if v_role is null then raise exception 'Profil tidak ditemukan.'; end if;

  if p_amount is null or p_amount < 0 then
    raise exception 'Nilai target wajib diisi dan tidak boleh negatif.';
  end if;
  if p_amount_period is null then
    raise exception 'Periode target wajib diisi.';
  end if;

  perform public.target_validasi_bentuk(p_domain, p_subject_id, p_student_id, p_halaqah_id, p_amount_period);

  if not public.target_boleh_ajukan(p_domain, p_subject_id, p_student_id, p_halaqah_id) then
    raise exception 'Anda tidak berhak mengajukan target untuk santri/halaqah ini.';
  end if;

  -- Bulan berlaku: default bulan berjalan (d)
  v_bulan := p_effective_month_id;
  if v_bulan is null then
    v_bulan := public.target_bulan_berjalan(p_domain);
  end if;
  if v_bulan is null then
    raise exception 'Bulan berlaku tidak ditemukan.';
  end if;
  -- bulan 0 tidak boleh jadi bulan berlaku target
  if exists (select 1 from public.hijri_months m where m.id = v_bulan and m.month_no = 0) then
    raise exception 'Bulan Data Awal tidak dapat menjadi bulan berlaku target.';
  end if;

  perform public.target_cek_konfirmasi(v_bulan, p_domain, p_konfirmasi);

  if public.is_full_access() or public.is_masul_of(p_domain) then
    v_status := 'disetujui';
    v_approved_by := v_uid;
    v_approved_at := now();
  else
    v_status := 'diajukan';
    v_approved_by := null;
    v_approved_at := null;
  end if;

  insert into public.targets
    (domain, subject_id, student_id, halaqah_id, effective_month_id, amount, amount_period,
     status, proposed_by, approved_by, approved_at, note)
  values
    (p_domain, p_subject_id, p_student_id, p_halaqah_id, v_bulan, p_amount, p_amount_period,
     v_status, v_uid, v_approved_by, v_approved_at, nullif(trim(p_note), ''))
  returning id into v_id;

  return jsonb_build_object(
    'id', v_id,
    'status', v_status,
    'effective_month_id', v_bulan
  );
end $$;

-- 6) Setujui target. (a,b,e)
--    Masul hanya domain sendiri; Mudir/Admin semua domain. Pengampu tidak boleh.
create or replace function public.setujui_target(
  p_target_id uuid,
  p_konfirmasi boolean default false
) returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_t public.targets%rowtype;
begin
  if v_uid is null then raise exception 'Harus masuk.'; end if;
  select * into v_t from public.targets where id = p_target_id;
  if not found then raise exception 'Target tidak ditemukan.'; end if;

  if not (public.is_full_access() or public.is_masul_of(v_t.domain)) then
    raise exception 'Hanya Masul domain terkait, Mudir, atau Admin yang dapat menyetujui target.';
  end if;
  if v_t.status = 'disetujui' then
    return jsonb_build_object('id', v_t.id, 'status', v_t.status, 'changed', false);
  end if;

  perform public.target_cek_konfirmasi(v_t.effective_month_id, v_t.domain, p_konfirmasi);

  update public.targets
  set status = 'disetujui', approved_by = v_uid, approved_at = now(),
      alasan_tolak = null, rejected_by = null, rejected_at = null
  where id = p_target_id;

  return jsonb_build_object('id', p_target_id, 'status', 'disetujui', 'changed', true);
end $$;

-- 7) Tolak target. (a,e) Alasan wajib. Tidak dihapus.
create or replace function public.tolak_target(
  p_target_id uuid,
  p_alasan text,
  p_konfirmasi boolean default false
) returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_t public.targets%rowtype;
  v_alasan text := nullif(trim(coalesce(p_alasan,'')), '');
begin
  if v_uid is null then raise exception 'Harus masuk.'; end if;
  if v_alasan is null then raise exception 'Alasan penolakan wajib diisi.'; end if;

  select * into v_t from public.targets where id = p_target_id;
  if not found then raise exception 'Target tidak ditemukan.'; end if;

  if not (public.is_full_access() or public.is_masul_of(v_t.domain)) then
    raise exception 'Hanya Masul domain terkait, Mudir, atau Admin yang dapat menolak target.';
  end if;

  perform public.target_cek_konfirmasi(v_t.effective_month_id, v_t.domain, p_konfirmasi);

  update public.targets
  set status = 'ditolak', alasan_tolak = v_alasan, rejected_by = v_uid, rejected_at = now(),
      approved_by = null, approved_at = null
  where id = p_target_id;

  return jsonb_build_object('id', p_target_id, 'status', 'ditolak', 'changed', true);
end $$;
