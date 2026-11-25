-- ============================================================================
-- T6e: hapus capaian (Admin/Mudir) + log perubahan.
--
-- (1) HAPUS CAPAIAN
--   Hanya Mudir/Admin (`is_full_access()`), diperiksa DI DALAM fungsi. Pengampu dan
--   Masul tetap hanya bisa input/menimpa, TIDAK bisa menghapus. Hapus = menghapus
--   baris `progress_entries`; rumus/view tidak berubah.
--   Cakupan: satu capaian satu santri, dan massal satu halaqah x mapel x bulan.
--   Bulan terkunci: boleh untuk Mudir/Admin, tetapi wajib konfirmasi eksplisit.
--   Bulan 0 (Data Awal) tetap bukan bulan input staf: tidak boleh dihapus lewat
--   fitur ini (data itu titik awal tahun; perubahan harus lewat Admin dengan
--   keputusan Mudir).
--   Dampak putaran/selisih: bila bulan SESUDAHNYA sudah terisi untuk santri+mapel
--   yang sama, penghapusan membuat `prev_item` bulan sesudahnya berubah (selisih
--   jadi tidak konsisten). Fungsi menolak dengan pesan jelas (sarankan hapus mulai
--   dari bulan terakhir) KECUALI pemanggil memberi `p_setuju_lanjutan = true`
--   (konfirmasi eksplisit). Bila capaian itu "khatam, mulai putaran baru"
--   (putaran > putaran bulan lalu), itu juga dilaporkan di pratinjau.
--
-- (2) LOG PERUBAHAN (satu mekanisme)
--   Tabel `public.change_log` mencatat UPDATE dan DELETE pada `progress_entries`,
--   `attendance`, dan `monthly_notes`: nilai lama, nilai baru, aktor, peran, waktu,
--   dan sumber. Trigger `catat_perubahan` (SECURITY DEFINER, hanya untuk trigger)
--   menulis log. Koneksi tanpa JWT (seed/skrip) tetap tercatat dengan
--   `sumber = 'skrip:<current_user>'` dan `aktor` NULL.
--   Log tidak bisa diubah/dihapus dari aplikasi: RLS aktif, hanya policy SELECT
--   untuk `is_full_access()`; tidak ada policy INSERT/UPDATE/DELETE; hak
--   UPDATE/DELETE/TRUNCATE/INSERT dicabut dari authenticated. anon tanpa akses.
--   Catatan: TRUNCATE (dipakai seed ulang) TIDAK memicu trigger baris; karena itu
--   `scripts/qa/test_seed_bersih.py` + sidik jari tetap wajib setelah seed.
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

-- ----------------------------------------------------------------------------
-- 1. Tabel log
-- ----------------------------------------------------------------------------
drop table if exists public.change_log cascade;

create table public.change_log (
  id bigserial primary key,
  terjadi_pada timestamptz not null default now(),
  tabel text not null,
  aksi text not null check (aksi in ('update', 'delete')),
  kunci jsonb not null,
  nilai_lama jsonb not null,
  nilai_baru jsonb,
  aktor uuid references public.profiles (id),
  aktor_role public.app_role,
  sumber text not null
);

create index if not exists change_log_waktu_idx on public.change_log (terjadi_pada desc);
create index if not exists change_log_tabel_idx on public.change_log (tabel, terjadi_pada desc);

alter table public.change_log enable row level security;

revoke all on public.change_log from anon, authenticated;
grant select on public.change_log to authenticated;
revoke insert, update, delete, truncate on public.change_log from authenticated, anon;

drop policy if exists change_log_read on public.change_log;
create policy change_log_read on public.change_log
  for select to authenticated
  using (public.is_full_access());

-- (Tidak ada policy INSERT/UPDATE/DELETE: aplikasi tidak bisa mengubah log.
--  Satu-satunya penulis adalah trigger SECURITY DEFINER di bawah.)

-- ----------------------------------------------------------------------------
-- 2. Trigger pencatat perubahan
-- ----------------------------------------------------------------------------
create or replace function public.catat_perubahan() returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_kunci jsonb;
  v_aktor uuid := auth.uid();
  v_role public.app_role;
  v_sumber text;
begin
  if tg_op not in ('UPDATE', 'DELETE') then
    return coalesce(new, old);
  end if;

  -- Kunci baris: id untuk progress_entries, kunci alami untuk kehadiran/catatan.
  if tg_table_name = 'progress_entries' then
    v_kunci := jsonb_build_object('id', old.id);
  elsif tg_table_name in ('attendance', 'monthly_notes') then
    v_kunci := jsonb_build_object('student_id', old.student_id,
                                  'month_id', old.month_id,
                                  'domain', old.domain);
  else
    v_kunci := jsonb_build_object('id', old.id);
  end if;

  if v_aktor is not null then
    select p.role into v_role from public.profiles p where p.id = v_aktor;
    v_sumber := 'aplikasi';
  else
    v_role := null;
    v_sumber := 'skrip:' || current_user;
  end if;

  insert into public.change_log
    (tabel, aksi, kunci, nilai_lama, nilai_baru, aktor, aktor_role, sumber)
  values
    (tg_table_name, lower(tg_op), v_kunci,
     to_jsonb(old),
     case when tg_op = 'UPDATE' then to_jsonb(new) else null end,
     v_aktor, v_role, v_sumber);

  return coalesce(new, old);
end $$;

revoke execute on function public.catat_perubahan() from public, anon, authenticated;

drop trigger if exists catat_perubahan_progress on public.progress_entries;
create trigger catat_perubahan_progress
  after update or delete on public.progress_entries
  for each row execute function public.catat_perubahan();

drop trigger if exists catat_perubahan_attendance on public.attendance;
create trigger catat_perubahan_attendance
  after update or delete on public.attendance
  for each row execute function public.catat_perubahan();

drop trigger if exists catat_perubahan_notes on public.monthly_notes;
create trigger catat_perubahan_notes
  after update or delete on public.monthly_notes
  for each row execute function public.catat_perubahan();

-- ----------------------------------------------------------------------------
-- 3. (Urutan bulan dipakai dari view `v_months_ordered`: ord = tahun*100 + bulan.)
-- ----------------------------------------------------------------------------
-- ----------------------------------------------------------------------------
-- 4. Pratinjau hapus SATU capaian
-- ----------------------------------------------------------------------------
create or replace function public.hapus_capaian_info(p_siswa uuid, p_mapel uuid, p_bulan uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  v_baris public.progress_entries;
  v_santri text;
  v_mapel text;
  v_bulan text;
  v_bulan_no integer;
  v_terkunci boolean;
  v_pos numeric;
  v_label text;
  v_sesudah jsonb;
  v_jml_sesudah integer := 0;
  v_putaran integer;
  v_putaran_lalu integer;
begin
  if not coalesce(public.is_full_access(), false) then
    raise exception 'Hanya Mudir atau Admin yang dapat menghapus capaian.'
      using errcode = 'insufficient_privilege';
  end if;

  select m.month_no, m.name into v_bulan_no, v_bulan from public.hijri_months m where m.id = p_bulan;
  if v_bulan_no is null then
    raise exception 'Bulan tidak ditemukan.';
  end if;
  if v_bulan_no = 0 then
    raise exception 'Bulan Data Awal bukan bulan input staf, jadi tidak dapat dihapus lewat fitur ini.';
  end if;

  select st.full_name into v_santri from public.students st where st.id = p_siswa;
  select s.name into v_mapel from public.subjects s where s.id = p_mapel;
  if v_santri is null or v_mapel is null then
    raise exception 'Santri atau mata pelajaran tidak ditemukan.';
  end if;

  select * into v_baris from public.progress_entries pe
  where pe.student_id = p_siswa and pe.subject_id = p_mapel and pe.month_id = p_bulan;
  if not found then
    return jsonb_build_object('ada', false, 'santri', v_santri, 'mapel', v_mapel, 'bulan', v_bulan);
  end if;

  select coalesce(ms.is_locked, false) into v_terkunci
  from public.month_domain_settings ms
  join public.hijri_months m on m.id = ms.month_id
  where ms.month_id = p_bulan and ms.domain = public.domain_of_subject(p_mapel);
  v_terkunci := coalesce(v_terkunci, false);

  select v.pos, v.item_label into v_pos, v_label
  from public.v_monthly_report v
  where v.entry_id = v_baris.id;

  v_putaran := greatest(coalesce(v_baris.putaran, 1), 1);
  select pe2.putaran into v_putaran_lalu
  from public.progress_entries pe2
  join public.v_months_ordered m2 on m2.id = pe2.month_id
  where pe2.student_id = p_siswa and pe2.subject_id = p_mapel
    and m2.ord = (select vmo.ord - 1 from public.v_months_ordered vmo where vmo.id = p_bulan)
  limit 1;

  select coalesce(jsonb_agg(jsonb_build_object('bulan', m.name, 'label', v.item_label) order by m.ord), '[]'::jsonb),
         count(*)
    into v_sesudah, v_jml_sesudah
  from public.v_months_ordered m
  join public.progress_entries pe2 on pe2.month_id = m.id
  join public.v_monthly_report v on v.entry_id = pe2.id
  where pe2.student_id = p_siswa and pe2.subject_id = p_mapel
    and m.month_no >= 1
    and m.ord > (select vmo.ord from public.v_months_ordered vmo where vmo.id = p_bulan);

  return jsonb_build_object(
    'ada', true,
    'santri', v_santri,
    'mapel', v_mapel,
    'bulan', v_bulan,
    'label', v_label,
    'pos', v_pos,
    'putaran', v_putaran,
    'putaran_lalu', v_putaran_lalu,
    'mulai_putaran_baru', (v_putaran_lalu is not null and v_putaran > v_putaran_lalu),
    'terkunci', v_terkunci,
    'bulan_sesudah', v_sesudah,
    'jumlah_sesudah', v_jml_sesudah,
    'perlu_setuju_lanjutan', v_jml_sesudah > 0
  );
end $$;

-- ----------------------------------------------------------------------------
-- 5. Pratinjau hapus MASSAL (satu halaqah x mapel x bulan)
-- ----------------------------------------------------------------------------
create or replace function public.hapus_capaian_massal_info(p_halaqah uuid, p_mapel uuid, p_bulan uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  v_halaqah text;
  v_mapel text;
  v_bulan text;
  v_bulan_no integer;
  v_domain public.domain_kind;
  v_terkunci boolean;
  v_jml integer;
  v_santri jsonb;
  v_variasi integer;
  v_sesudah jsonb;
  v_jml_sesudah integer;
begin
  if not coalesce(public.is_full_access(), false) then
    raise exception 'Hanya Mudir atau Admin yang dapat menghapus capaian.'
      using errcode = 'insufficient_privilege';
  end if;

  select h.code into v_halaqah from public.halaqahs h where h.id = p_halaqah;
  select s.name, s.domain into v_mapel, v_domain from public.subjects s where s.id = p_mapel;
  select m.month_no, m.name into v_bulan_no, v_bulan from public.hijri_months m where m.id = p_bulan;
  if v_halaqah is null or v_mapel is null or v_bulan_no is null then
    raise exception 'Halaqah, mata pelajaran, atau bulan tidak ditemukan.';
  end if;
  if v_bulan_no = 0 then
    raise exception 'Bulan Data Awal bukan bulan input staf, jadi tidak dapat dihapus lewat fitur ini.';
  end if;
  if v_domain <> (select h.domain from public.halaqahs h where h.id = p_halaqah) then
    raise exception 'Mata pelajaran itu bukan bagian dari domain halaqah ini.';
  end if;

  select coalesce(ms.is_locked, false) into v_terkunci
  from public.month_domain_settings ms
  where ms.month_id = p_bulan and ms.domain = v_domain;
  v_terkunci := coalesce(v_terkunci, false);

  select count(*), coalesce(jsonb_agg(jsonb_build_object(
             'santri', st.full_name, 'label', v.item_label, 'pos', v.pos) order by st.full_name), '[]'::jsonb),
         count(distinct v.item_label)
    into v_jml, v_santri, v_variasi
  from public.progress_entries pe
  join public.students st on st.id = pe.student_id
  join public.v_monthly_report v on v.entry_id = pe.id
  where pe.halaqah_id = p_halaqah and pe.subject_id = p_mapel and pe.month_id = p_bulan;

  select coalesce(jsonb_agg(distinct jsonb_build_object('bulan', m.name)), '[]'::jsonb), count(*)
    into v_sesudah, v_jml_sesudah
  from public.progress_entries pe2
  join public.v_months_ordered m on m.id = pe2.month_id
  where pe2.halaqah_id = p_halaqah and pe2.subject_id = p_mapel
    and m.month_no >= 1
    and m.ord > (select vmo.ord from public.v_months_ordered vmo where vmo.id = p_bulan);

  return jsonb_build_object(
    'ada', v_jml > 0,
    'halaqah', v_halaqah,
    'mapel', v_mapel,
    'bulan', v_bulan,
    'baris', v_jml,
    'santri', v_santri,
    'variasi_nilai', v_variasi,
    'terkunci', v_terkunci,
    'bulan_sesudah', v_sesudah,
    'jumlah_sesudah', v_jml_sesudah,
    'perlu_setuju_lanjutan', v_jml_sesudah > 0
  );
end $$;

-- ----------------------------------------------------------------------------
-- 6. Hapus SATU capaian
-- ----------------------------------------------------------------------------
create or replace function public.hapus_capaian(
  p_siswa uuid, p_mapel uuid, p_bulan uuid,
  p_setuju_terkunci boolean default false,
  p_setuju_lanjutan boolean default false
)
returns jsonb
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  v_info jsonb;
  v_baris public.progress_entries;
  v_jml integer;
begin
  if not coalesce(public.is_full_access(), false) then
    raise exception 'Hanya Mudir atau Admin yang dapat menghapus capaian.'
      using errcode = 'insufficient_privilege';
  end if;

  v_info := public.hapus_capaian_info(p_siswa, p_mapel, p_bulan);
  if not (v_info->>'ada')::boolean then
    raise exception 'Capaian itu tidak ada (mungkin sudah dihapus).';
  end if;

  if (v_info->>'terkunci')::boolean and not coalesce(p_setuju_terkunci, false) then
    raise exception 'Bulan ini sudah dikunci. Hapus hanya boleh setelah dikonfirmasi eksplisit.'
      using errcode = 'check_violation';
  end if;
  if (v_info->>'perlu_setuju_lanjutan')::boolean and not coalesce(p_setuju_lanjutan, false) then
    raise exception 'Bulan sesudahnya sudah terisi (%). Menghapus bulan ini akan membuat selisih bulan sesudahnya tidak konsisten. Hapus mulai dari bulan terakhir, atau beri konfirmasi eksplisit.',
      (v_info->>'bulan_sesudah')::text
      using errcode = 'check_violation';
  end if;

  delete from public.progress_entries pe
  where pe.student_id = p_siswa and pe.subject_id = p_mapel and pe.month_id = p_bulan
  returning * into v_baris;
  get diagnostics v_jml = row_count;

  return jsonb_build_object(
    'baris', v_jml,
    'santri', v_info->>'santri',
    'mapel', v_info->>'mapel',
    'bulan', v_info->>'bulan',
    'label', v_info->>'label',
    'putaran', v_baris.putaran
  );
end $$;

-- ----------------------------------------------------------------------------
-- 7. Hapus MASSAL (halaqah x mapel x bulan)
-- ----------------------------------------------------------------------------
create or replace function public.hapus_capaian_massal(
  p_halaqah uuid, p_mapel uuid, p_bulan uuid,
  p_setuju_terkunci boolean default false,
  p_setuju_lanjutan boolean default false
)
returns jsonb
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  v_info jsonb;
  v_jml integer;
begin
  if not coalesce(public.is_full_access(), false) then
    raise exception 'Hanya Mudir atau Admin yang dapat menghapus capaian.'
      using errcode = 'insufficient_privilege';
  end if;

  v_info := public.hapus_capaian_massal_info(p_halaqah, p_mapel, p_bulan);
  if not (v_info->>'ada')::boolean then
    raise exception 'Tidak ada capaian untuk halaqah, mata pelajaran, dan bulan itu.';
  end if;

  if (v_info->>'terkunci')::boolean and not coalesce(p_setuju_terkunci, false) then
    raise exception 'Bulan ini sudah dikunci. Hapus hanya boleh setelah dikonfirmasi eksplisit.'
      using errcode = 'check_violation';
  end if;
  if (v_info->>'perlu_setuju_lanjutan')::boolean and not coalesce(p_setuju_lanjutan, false) then
    raise exception 'Bulan sesudahnya sudah terisi (%). Menghapus bulan ini akan membuat selisih bulan sesudahnya tidak konsisten. Hapus mulai dari bulan terakhir, atau beri konfirmasi eksplisit.',
      (v_info->>'bulan_sesudah')::text
      using errcode = 'check_violation';
  end if;

  delete from public.progress_entries pe
  where pe.halaqah_id = p_halaqah and pe.subject_id = p_mapel and pe.month_id = p_bulan;
  get diagnostics v_jml = row_count;

  return jsonb_build_object(
    'baris', v_jml,
    'halaqah', v_info->>'halaqah',
    'mapel', v_info->>'mapel',
    'bulan', v_info->>'bulan'
  );
end $$;

-- ----------------------------------------------------------------------------
-- 8. Hak akses fungsi: hanya authenticated (anon tanpa EXECUTE).
--    Cek role tetap di dalam fungsi; RLS tabel tetap penjaga terakhir.
-- ----------------------------------------------------------------------------
revoke execute on function public.hapus_capaian_info(uuid, uuid, uuid) from public, anon;
revoke execute on function public.hapus_capaian_massal_info(uuid, uuid, uuid) from public, anon;
revoke execute on function public.hapus_capaian(uuid, uuid, uuid, boolean, boolean) from public, anon;
revoke execute on function public.hapus_capaian_massal(uuid, uuid, uuid, boolean, boolean) from public, anon;

grant execute on function public.hapus_capaian_info(uuid, uuid, uuid) to authenticated, service_role;
grant execute on function public.hapus_capaian_massal_info(uuid, uuid, uuid) to authenticated, service_role;
grant execute on function public.hapus_capaian(uuid, uuid, uuid, boolean, boolean) to authenticated, service_role;
grant execute on function public.hapus_capaian_massal(uuid, uuid, uuid, boolean, boolean) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- Verifikasi:
--   select tablename, policyname, cmd from pg_policies where tablename='change_log';
--   select tgname, tgrelid::regclass from pg_trigger where tgfoid='public.catat_perubahan()'::regprocedure;
--   select proname, proacl from pg_proc where proname like 'hapus_capaian%';
-- ----------------------------------------------------------------------------
