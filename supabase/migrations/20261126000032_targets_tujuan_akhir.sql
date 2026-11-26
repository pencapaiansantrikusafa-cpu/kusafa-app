-- ============================================================================
-- T7c [1/3]: target Wasilah/Ghayah = TUJUAN AKHIR (butir kurikulum), bukan jumlah.
-- Keputusan Mudir 26 November 2026 (SPEC 5e, HANDOVER 3.2a).
--
-- Al Qur'an TIDAK berubah: amount + harian per santri, target_monthly = amount x Hadir.
-- Wasilah/Ghayah: target_item_id (butir kurikulum) = posisi akhir bulan depan;
--   wajib halaqah_id + subject + target_item_id, TANPA amount.
--
-- Catatan penerapan: migrasi ini IDEMPOTEN (aman dijalankan ulang):
--   add column if not exists / drop constraint if exists / drop function if exists /
--   create or replace / drop trigger if exists / create unique index if not exists.
-- Untuk menghapus 36 DUMMY lama (bentuk amount=1) dipakai
--   scripts/db/fixes/2026-11-26_t7c_hapus_target_dummy_lama.sql
-- (idempoten, tiap baris tercatat di change_log). Skrip itu WAJIB jalan SEBELUM
-- migrasi ini bila masih ada baris bentuk lama, karena constraint di bawah VALID.
-- DUMMY BENTUK BARU dibuat ulang lewat
--   scripts/db/fixes/2026-11-26_t7c_target_dummy_tujuan.sql (satu per halaqah x mapel).
-- ============================================================================

-- 1) Kolom butir target untuk Wasilah/Ghayah.
alter table public.targets
  add column if not exists target_item_id uuid references public.curriculum_items (id);

comment on column public.targets.target_item_id is
  'Wasilah/Ghayah: butir kurikulum tujuan akhir bulan depan (posisi). Al Qur''an: NULL.';

-- Amount hanya untuk Al Qur'an. Wasilah/Ghayah memakai target_item_id.
alter table public.targets alter column amount drop not null;

-- 2) Bentuk sah per domain (VALID; 36 DUMMY lama sudah dihapus skrip fix).
--    Al Qur'an TIDAK berubah: jumlah + harian, dan tetap boleh per SANTRI (individu)
--    atau per HALAQAH (aturan lama (c): "individu didahulukan dari halaqah").
--    Hanya Wasilah/Ghayah yang wajib halaqah + butir dan tanpa amount.
alter table public.targets drop constraint if exists targets_bentuk_check;
alter table public.targets add constraint targets_bentuk_check check (
  case
    when domain = 'alquran' then
      amount is not null and amount >= 0
      and amount_period = 'harian'
      and ((student_id is not null) <> (halaqah_id is not null))
      and target_item_id is null
    when domain in ('wasilah', 'ghayah') then
      amount is null
      and amount_period = 'bulanan'
      and student_id is null and halaqah_id is not null and target_item_id is not null
    else false
  end
);

-- 3) Butir harus milik BUKU mata pelajaran itu dan aktif (lintas tabel -> trigger).
create or replace function public.target_validasi_butir() returns trigger
language plpgsql security invoker set search_path = public, pg_temp as $$
begin
  if new.target_item_id is null then
    return new;
  end if;
  if not exists (
    select 1
    from public.curriculum_items ci
    join public.books b on b.id = ci.book_id
    where ci.id = new.target_item_id
      and ci.is_active and b.is_active
      and b.subject_id = new.subject_id
  ) then
    raise exception 'Butir target harus milik buku mata pelajaran ini dan aktif.';
  end if;
  return new;
end $$;

revoke execute on function public.target_validasi_butir() from public, anon, authenticated;
drop trigger if exists target_validasi_butir_trg on public.targets;
create trigger target_validasi_butir_trg
  before insert or update of target_item_id, subject_id on public.targets
  for each row execute function public.target_validasi_butir();

-- 4) Satu target MENUNGGU per (halaqah, mapel, bulan berlaku).
create unique index if not exists targets_satu_diajukan_uk
  on public.targets (halaqah_id, subject_id, effective_month_id)
  where status = 'diajukan' and halaqah_id is not null;

-- 5) Validasi bentuk tujuan akhir.
create or replace function public.target_validasi_tujuan(
  p_domain public.domain_kind,
  p_subject_id uuid,
  p_student_id uuid,
  p_halaqah_id uuid,
  p_amount numeric,
  p_amount_period public.target_period,
  p_target_item_id uuid
) returns void language plpgsql stable security definer set search_path = public, pg_temp as $$
declare v_subj public.domain_kind; v_halaqah public.domain_kind;
begin
  if p_subject_id is null then raise exception 'Mata pelajaran wajib diisi.'; end if;
  select domain into v_subj from public.subjects where id = p_subject_id;
  if v_subj is null then raise exception 'Mata pelajaran tidak ditemukan.'; end if;
  if v_subj <> p_domain then raise exception 'Mata pelajaran tidak sesuai domain.'; end if;

  if p_domain = 'alquran' then
    if p_student_id is null then raise exception 'Target Al Qur''an harus per santri.'; end if;
    if p_halaqah_id is not null then raise exception 'Target Al Qur''an per santri, bukan per halaqah.'; end if;
    if p_target_item_id is not null then raise exception 'Target Al Qur''an memakai jumlah, bukan butir kurikulum.'; end if;
    if p_amount_period <> 'harian' then raise exception 'Target Al Qur''an harus harian.'; end if;
    if p_amount is null or p_amount < 0 then raise exception 'Nilai target Al Qur''an wajib diisi dan tidak boleh negatif.'; end if;
  elsif p_domain in ('wasilah', 'ghayah') then
    if p_halaqah_id is null then raise exception 'Target Wasilah/Ghayah harus per halaqah.'; end if;
    if p_student_id is not null then raise exception 'Target Wasilah/Ghayah per halaqah, bukan per santri.'; end if;
    if p_target_item_id is null then raise exception 'Target Wasilah/Ghayah wajib memilih butir kurikulum (tujuan akhir).'; end if;
    if p_amount is not null then raise exception 'Target Wasilah/Ghayah memakai butir kurikulum (posisi), bukan jumlah.'; end if;
    if p_amount_period <> 'bulanan' then raise exception 'Target Wasilah/Ghayah harus bulanan.'; end if;
    select domain into v_halaqah from public.halaqahs where id = p_halaqah_id;
    if v_halaqah is null then raise exception 'Halaqah tidak ditemukan.'; end if;
    if v_halaqah <> p_domain then raise exception 'Halaqah tidak sesuai domain target.'; end if;
    if not exists (select 1 from public.halaqah_subjects hs
                   where hs.halaqah_id = p_halaqah_id and hs.subject_id = p_subject_id) then
      raise exception 'Mata pelajaran itu tidak ditetapkan untuk halaqah ini.';
    end if;
  else
    raise exception 'Domain target tidak dikenal.';
  end if;
end $$;

revoke execute on function public.target_validasi_tujuan(public.domain_kind, uuid, uuid, uuid, numeric, public.target_period, uuid) from public, anon;

-- 6) Ajukan target (bentuk baru). p_target_item_id ditambahkan; untuk Al Qur'an
--    parameter tetap dipakai (butir NULL). Pengajuan Wasilah/Ghayah baru menggantikan
--    pengajuan yang masih 'diajukan' pada (halaqah, mapel, bulan) -> lama menjadi 'dibatalkan'.
--
--    PENTING: versi lama bertanda tangan 9 parameter DIHAPUS agar tidak ada OVERLOAD.
--    Kalau dua fungsi bernama sama tetap ada, PostgREST balas HTTP 300 PGRST203
--    ("Could not choose the best candidate function") dan seluruh halaman Target
--    di produksi gagal. Karena parameter baru punya nilai bawaan (default null),
--    panggilan lama dengan 9 argumen tetap cocok ke fungsi 10 parameter ini.
drop function if exists public.ajukan_target(
  public.domain_kind, uuid, uuid, uuid, uuid, numeric, public.target_period, text, boolean);
create or replace function public.ajukan_target(
  p_domain public.domain_kind,
  p_subject_id uuid,
  p_student_id uuid default null,
  p_halaqah_id uuid default null,
  p_effective_month_id uuid default null,
  p_amount numeric default null,
  p_amount_period public.target_period default null,
  p_note text default null,
  p_konfirmasi boolean default false,
  p_target_item_id uuid default null
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
  v_diganti integer := 0;
begin
  if v_uid is null then raise exception 'Harus masuk untuk mengajukan target.'; end if;
  v_role := public.current_app_role();
  if v_role is null then raise exception 'Profil tidak ditemukan.'; end if;
  if p_amount_period is null then raise exception 'Periode target wajib diisi.'; end if;

  perform public.target_validasi_tujuan(
    p_domain, p_subject_id, p_student_id, p_halaqah_id, p_amount, p_amount_period, p_target_item_id);

  if not public.target_boleh_ajukan(p_domain, p_subject_id, p_student_id, p_halaqah_id) then
    raise exception 'Anda tidak berhak mengajukan target untuk santri/halaqah ini.';
  end if;

  v_bulan := coalesce(p_effective_month_id, public.target_bulan_berjalan(p_domain));
  if v_bulan is null then raise exception 'Bulan berlaku tidak ditemukan.'; end if;
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

  -- Satu target menunggu per (halaqah, mapel, bulan): pengajuan baru menggantikan yang
  -- masih 'diajukan'. Status yang dipakai untuk baris lama = 'dibatalkan' (riwayat tetap).
  if p_domain in ('wasilah', 'ghayah') then
    update public.targets
    set status = 'dibatalkan'
    where halaqah_id = p_halaqah_id and subject_id = p_subject_id
      and effective_month_id = v_bulan and status = 'diajukan';
    get diagnostics v_diganti = row_count;
  end if;

  insert into public.targets
    (domain, subject_id, target_item_id, student_id, halaqah_id, effective_month_id,
     amount, amount_period, status, proposed_by, approved_by, approved_at, note)
  values
    (p_domain, p_subject_id, p_target_item_id, p_student_id, p_halaqah_id, v_bulan,
     p_amount, p_amount_period, v_status, v_uid, v_approved_by, v_approved_at, nullif(trim(p_note), ''))
  returning id into v_id;

  return jsonb_build_object(
    'id', v_id, 'status', v_status, 'effective_month_id', v_bulan,
    'target_item_id', p_target_item_id, 'digantikan', v_diganti);
end $$;

-- 7) Ubah target = baris BARU (bentuk baru). Untuk Wasilah/Ghayah butir baru diisi;
--    untuk Al Qur'an jumlah baru. Target lama tetap utuh.
--    Versi lama 5 parameter dihapus agar tidak ada OVERLOAD (lihat catatan di atas).
drop function if exists public.ubah_target(uuid, numeric, uuid, text, boolean);
create or replace function public.ubah_target(
  p_target_lama_id uuid,
  p_amount numeric,
  p_effective_month_id uuid default null,
  p_note text default null,
  p_konfirmasi boolean default false,
  p_target_item_id uuid default null
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
  v_butir uuid;
begin
  if v_uid is null then raise exception 'Harus masuk.'; end if;
  select * into v_lama from public.targets where id = p_target_lama_id;
  if not found then raise exception 'Target lama tidak ditemukan.'; end if;

  if not public.target_boleh_ajukan(v_lama.domain, v_lama.subject_id, v_lama.student_id, v_lama.halaqah_id) then
    raise exception 'Anda tidak berhak mengubah target ini.';
  end if;

  v_butir := case when v_lama.domain in ('wasilah', 'ghayah') then p_target_item_id else null end;
  perform public.target_validasi_tujuan(
    v_lama.domain, v_lama.subject_id, v_lama.student_id, v_lama.halaqah_id,
    case when v_lama.domain = 'alquran' then p_amount else null end,
    v_lama.amount_period, v_butir);

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

  if v_lama.domain in ('wasilah', 'ghayah') then
    update public.targets
    set status = 'dibatalkan'
    where halaqah_id = v_lama.halaqah_id and subject_id = v_lama.subject_id
      and effective_month_id = v_bulan and status = 'diajukan' and id <> v_lama.id;
  end if;

  insert into public.targets
    (domain, subject_id, target_item_id, student_id, halaqah_id, effective_month_id,
     amount, amount_period, status, proposed_by, approved_by, approved_at, note)
  values
    (v_lama.domain, v_lama.subject_id, v_butir, v_lama.student_id, v_lama.halaqah_id, v_bulan,
     case when v_lama.domain = 'alquran' then p_amount else null end, v_lama.amount_period,
     v_status, v_uid, v_approved_by, v_approved_at, nullif(trim(p_note), ''))
  returning id into v_id;

  return jsonb_build_object('id', v_id, 'status', v_status, 'effective_month_id', v_bulan,
                            'target_item_id', v_butir, 'menggantikan', p_target_lama_id);
end $$;

-- 8) Setujui satu target (tambah target_item_id pada hasil; logika hak tetap).
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
    return jsonb_build_object('id', v_t.id, 'status', v_t.status, 'changed', false,
                              'target_item_id', v_t.target_item_id);
  end if;
  perform public.target_cek_konfirmasi(v_t.effective_month_id, v_t.domain, p_konfirmasi);
  update public.targets
  set status = 'disetujui', approved_by = v_uid, approved_at = now(),
      alasan_tolak = null, rejected_by = null, rejected_at = null
  where id = p_target_id;
  return jsonb_build_object('id', p_target_id, 'status', 'disetujui', 'changed', true,
                            'target_item_id', v_t.target_item_id);
end $$;

-- 9) Tolak target (tambah target_item_id pada hasil).
create or replace function public.tolak_target(
  p_target_id uuid,
  p_alasan text,
  p_konfirmasi boolean default false
) returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_t public.targets%rowtype;
  v_alasan text := nullif(trim(coalesce(p_alasan, '')), '');
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
  return jsonb_build_object('id', p_target_id, 'status', 'ditolak', 'changed', true,
                            'target_item_id', v_t.target_item_id);
end $$;

-- 10) Batalkan pengajuan (tidak berubah bentuk; tetap hanya pengaju + status diajukan).
create or replace function public.batalkan_target(p_target_id uuid)
returns jsonb language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_target public.targets%rowtype;
begin
  if v_uid is null then raise exception 'Harus masuk untuk membatalkan pengajuan target.'; end if;
  select * into v_target from public.targets where id = p_target_id for update;
  if not found then raise exception 'Target tidak ditemukan.'; end if;
  if v_target.proposed_by is distinct from v_uid then
    raise exception 'Hanya pengaju target ini yang dapat membatalkannya.';
  end if;
  if v_target.status <> 'diajukan' then
    raise exception 'Hanya target berstatus diajukan yang dapat dibatalkan. Target ditolak atau disetujui tetap menjadi riwayat.';
  end if;
  update public.targets set status = 'dibatalkan' where id = p_target_id;
  return jsonb_build_object('id', p_target_id, 'status', 'dibatalkan', 'target_item_id', v_target.target_item_id);
end $$;

-- 11) Bulk: setujui semua target menunggu untuk satu halaqah (opsional satu bulan).
create or replace function public.setujui_target_halaqah(
  p_halaqah_id uuid,
  p_effective_month_id uuid default null,
  p_konfirmasi boolean default false
) returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_domain public.domain_kind;
  v_t public.targets%rowtype;
  v_n integer := 0;
begin
  if v_uid is null then raise exception 'Harus masuk.'; end if;
  select domain into v_domain from public.halaqahs where id = p_halaqah_id;
  if v_domain is null then raise exception 'Halaqah tidak ditemukan.'; end if;
  if not (public.is_full_access() or public.is_masul_of(v_domain)) then
    raise exception 'Hanya Masul domain terkait, Mudir, atau Admin yang dapat menyetujui target halaqah ini.';
  end if;

  for v_t in
    select * from public.targets
    where halaqah_id = p_halaqah_id and status = 'diajukan'
      and (p_effective_month_id is null or effective_month_id = p_effective_month_id)
    order by effective_month_id, subject_id
    for update
  loop
    perform public.target_cek_konfirmasi(v_t.effective_month_id, v_t.domain, p_konfirmasi);
    update public.targets
    set status = 'disetujui', approved_by = v_uid, approved_at = now(),
        alasan_tolak = null, rejected_by = null, rejected_at = null
    where id = v_t.id;
    v_n := v_n + 1;
  end loop;

  return jsonb_build_object('jumlah', v_n, 'halaqah_id', p_halaqah_id,
                            'effective_month_id', p_effective_month_id, 'domain', v_domain);
end $$;

-- 12) Riwayat: sertakan butir tujuan akhir + buku.
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
           t.target_item_id, ci.label as butir, b.name as buku,
           t.effective_month_id, vm.name as bulan_berlaku, vm.month_no, vm.hijri_year, vm.ord,
           t.proposed_by, pb.full_name as pengaju,
           t.approved_by, ab.full_name as penyetuju, t.approved_at,
           t.rejected_by, rb.full_name as penolak, t.rejected_at,
           t.created_at
    from public.targets t
    join public.v_months_ordered vm on vm.id = t.effective_month_id
    left join public.curriculum_items ci on ci.id = t.target_item_id
    left join public.books b on b.id = ci.book_id
    left join public.profiles pb on pb.id = t.proposed_by
    left join public.profiles ab on ab.id = t.approved_by
    left join public.profiles rb on rb.id = t.rejected_by
    where t.subject_id = p_subject_id
      and ((p_student_id is not null and t.student_id = p_student_id)
        or (p_halaqah_id is not null and t.student_id is null and t.halaqah_id = p_halaqah_id))
  ) x;
  return v_res;
end $$;

-- 13) Hak EXECUTE: RPC target hanya authenticated; PUBLIC dan anon dicabut untuk
--     SELURUH keluarga fungsi target (target_*, ajukan/ubah/setujui/tolak/batalkan/
--     riwayat/setujui_target_halaqah/ajukan_target_massal_alquran).
--     (Versi lama 9-arg/5-arg sudah di-DROP di atas, jadi tidak ada lagi overload.
--      Fungsi yang baru dibuat mewarisi EXECUTE PUBLIC dari PostgreSQL, jadi WAJIB
--      dicabut eksplisit; kalau tidak, anon bisa memanggilnya. DO-block di bawah
--      IDEMPOTEN: menyapu semua fungsi target yang ada saat migrasi dijalankan,
--      termasuk helper yang dibuat migrasi berikutnya bila ditambahkan ke berkas ini.)
do $$
declare r record;
begin
  for r in
    select p.oid::regprocedure as sig
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and (
        p.proname like 'target\_%'
        or p.proname in (
          'ajukan_target', 'ubah_target', 'setujui_target', 'tolak_target',
          'batalkan_target', 'riwayat_target', 'setujui_target_halaqah',
          'ajukan_target_massal_alquran'
        )
      )
  loop
    execute format('revoke execute on function %s from public, anon', r.sig);
  end loop;
end $$;

-- Hanya RPC yang dipakai aplikasi yang diberi EXECUTE untuk authenticated.
grant execute on function public.ajukan_target(public.domain_kind, uuid, uuid, uuid, uuid, numeric, public.target_period, text, boolean, uuid) to authenticated;
grant execute on function public.ubah_target(uuid, numeric, uuid, text, boolean, uuid) to authenticated;
grant execute on function public.setujui_target_halaqah(uuid, uuid, boolean) to authenticated;
grant execute on function public.setujui_target(uuid, boolean) to authenticated;
grant execute on function public.tolak_target(uuid, text, boolean) to authenticated;
grant execute on function public.batalkan_target(uuid) to authenticated;
grant execute on function public.riwayat_target(uuid, uuid, uuid) to authenticated;
grant execute on function public.ajukan_target_massal_alquran(uuid, uuid, uuid, numeric, text, boolean) to authenticated;
