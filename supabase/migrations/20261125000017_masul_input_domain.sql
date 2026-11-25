-- ============================================================================
-- T6d2: masul (Al Quran / Wasilah / Ghayah) boleh input di SEMUA halaqah domainnya,
--       + jejak siapa yang mengisi dan mengubah.
--
-- Keputusan Mudir 25 November 2026 (menggantikan keputusan T6b/3d sebelumnya):
--   Tiap Masul boleh INPUT **capaian, catatan, dan kehadiran** di SEMUA halaqah
--   domainnya masing-masing. Tetap DITOLAK: domain lain, bulan terkunci, bulan 0,
--   dan menghapus. Pengampu (Musyrif/ah, Mudarris/ah) tetap hanya halaqahnya sendiri.
--   Rumus Hadir dan view TIDAK berubah.
--
-- (1) HAK TULIS. Sebelum migrasi ini, policy tulis untuk capaian hanya:
--     - `progress_insert` / `progress_update`: is_full_access ATAU
--       student_in_taught_halaqah (pengampu);
--     - `progress_insert_masul_domain` / `progress_update_masul_domain`: Masul
--       untuk wasilah + ghayah saja.
--     Kehadiran (`attendance_insert/update`) dan catatan (`notes_insert/update`)
--     hanya `student_in_taught_domain` (pengampu) untuk SEMUA domain. Akibatnya
--     ketiga Masul tidak bisa menulis apa pun kecuali halaqah yang diampu.
--
--     Migrasi ini mengganti keempat policy capaian dan keempat policy kehadiran/
--     catatan dengan versi seragam untuk KETIGA domain:
--       is_full_access()                                        -> semua
--       ATAU is_masul_of(domain) AND month_is_open(domain)       -> semua halaqah domainnya
--       ATAU pengampu AND month_is_open(domain)                  -> halaqah yang diampu
--     Hak hapus TIDAK diubah: `progress_delete`/`attendance_delete`/`notes_delete`
--     tetap hanya `is_full_access()` (Mudir/Admin).
--
-- (2) JEJAK PENGISI. Ketiga tabel sudah punya `entered_by` (default `auth.uid()`)
--     dan `entered_at`, tetapi:
--       - saat menimpa (`upsert`/update), `entered_by`/`entered_at` TIDAK ikut
--         berubah, jadi isian terbaru bisa tercatat atas nama pengisi pertama;
--       - tidak ada kolom "terakhir diubah oleh".
--     Ditambahkan `updated_by` + `updated_at` pada ketiga tabel serta trigger
--     `catat_jejak` yang: (a) mengisi `entered_by` bila kosong, (b) pada UPDATE
--     memindahkan pengisi lama ke `updated_by`/`updated_at` bila `entered_by` tidak
--     berubah eksplisit, atau mencatat pengubah baru. Fungsi ini SECURITY INVOKER
--     dan hanya menyentuh NEW, tidak membaca data lain.
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

-- ----------------------------------------------------------------------------
-- 1. CAPAIAN (progress_entries)
-- ----------------------------------------------------------------------------
drop policy if exists progress_insert on public.progress_entries;
drop policy if exists progress_update on public.progress_entries;
drop policy if exists progress_insert_masul_domain on public.progress_entries;
drop policy if exists progress_update_masul_domain on public.progress_entries;

create policy progress_insert on public.progress_entries for insert to authenticated
  with check (
    public.is_full_access()
    or (
      public.month_is_open(month_id, public.domain_of_subject(subject_id))
      and (
        -- Masul: semua halaqah di domainnya (keputusan Mudir 25 Nov 2026).
        public.is_masul_of(public.domain_of_subject(subject_id))
        -- Pengampu: hanya halaqah/mapel yang diampu.
        or public.student_in_taught_halaqah(student_id, subject_id)
      )
    )
  );

create policy progress_update on public.progress_entries for update to authenticated
  using (
    public.is_full_access()
    or (
      public.month_is_open(month_id, public.domain_of_subject(subject_id))
      and (
        public.is_masul_of(public.domain_of_subject(subject_id))
        or public.student_in_taught_halaqah(student_id, subject_id)
      )
    )
  )
  with check (
    public.is_full_access()
    or (
      public.month_is_open(month_id, public.domain_of_subject(subject_id))
      and (
        public.is_masul_of(public.domain_of_subject(subject_id))
        or public.student_in_taught_halaqah(student_id, subject_id)
      )
    )
  );

-- ----------------------------------------------------------------------------
-- 2. KEHADIRAN (attendance) dan CATATAN (monthly_notes)
-- ----------------------------------------------------------------------------
drop policy if exists attendance_insert on public.attendance;
drop policy if exists attendance_update on public.attendance;
drop policy if exists notes_insert on public.monthly_notes;
drop policy if exists notes_update on public.monthly_notes;

create policy attendance_insert on public.attendance for insert to authenticated
  with check (
    public.is_full_access()
    or (
      public.month_is_open(month_id, domain)
      and (public.is_masul_of(domain) or public.student_in_taught_domain(student_id, domain))
    )
  );

create policy attendance_update on public.attendance for update to authenticated
  using (
    public.is_full_access()
    or (
      public.month_is_open(month_id, domain)
      and (public.is_masul_of(domain) or public.student_in_taught_domain(student_id, domain))
    )
  )
  with check (
    public.is_full_access()
    or (
      public.month_is_open(month_id, domain)
      and (public.is_masul_of(domain) or public.student_in_taught_domain(student_id, domain))
    )
  );

create policy notes_insert on public.monthly_notes for insert to authenticated
  with check (
    public.is_full_access()
    or (
      public.month_is_open(month_id, domain)
      and (public.is_masul_of(domain) or public.student_in_taught_domain(student_id, domain))
    )
  );

create policy notes_update on public.monthly_notes for update to authenticated
  using (
    public.is_full_access()
    or (
      public.month_is_open(month_id, domain)
      and (public.is_masul_of(domain) or public.student_in_taught_domain(student_id, domain))
    )
  )
  with check (
    public.is_full_access()
    or (
      public.month_is_open(month_id, domain)
      and (public.is_masul_of(domain) or public.student_in_taught_domain(student_id, domain))
    )
  );

-- ----------------------------------------------------------------------------
-- 3. Kolom jejak "terakhir diubah oleh"
-- ----------------------------------------------------------------------------
alter table public.progress_entries
  add column if not exists updated_by uuid references public.profiles (id),
  add column if not exists updated_at timestamptz;

alter table public.attendance
  add column if not exists updated_by uuid references public.profiles (id),
  add column if not exists updated_at timestamptz;

alter table public.monthly_notes
  add column if not exists updated_by uuid references public.profiles (id),
  add column if not exists updated_at timestamptz;

-- ----------------------------------------------------------------------------
-- 4. Trigger jejak: isi entered_by, catat pengubah terakhir.
--
--    Aturan:
--    - INSERT: `entered_by` kosong -> auth.uid(); `entered_at` kosong -> now().
--    - UPDATE: bila `entered_by` TIDAK diubah secara eksplisit (kasus `upsert`
--      biasa yang tidak mengirim kolom itu), pengisi lama dipindahkan ke
--      `updated_by`/`updated_at` dan `entered_by` menjadi pengubah sekarang.
--      Bila pemanggil memang mengirim `entered_by` baru, nilai itu dipakai.
--    - Koneksi tanpa JWT (skrip seed/service_role): auth.uid() null -> dibiarkan
--      kosong, sama seperti perilaku lama; tidak ada penebakan.
-- ----------------------------------------------------------------------------
create or replace function public.catat_jejak() returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_uid uuid := auth.uid();
begin
  if tg_op = 'INSERT' then
    if new.entered_by is null then
      new.entered_by := v_uid;
    end if;
    if new.entered_at is null then
      new.entered_at := now();
    end if;
    return new;
  end if;

  -- UPDATE
  if new.entered_by is distinct from old.entered_by then
    -- Pemanggil mengubah pengisi secara eksplisit: catat pengubahnya.
    if v_uid is not null then
      new.updated_by := v_uid;
      new.updated_at := now();
    end if;
  else
    -- Menimpa isian lama: pengisi lama dipindah ke jejak "diubah".
    if new.entered_by is distinct from v_uid then
      new.updated_by := coalesce(old.entered_by, new.updated_by);
      new.updated_at := coalesce(old.entered_at, now());
      new.entered_by := v_uid;
      new.entered_at := now();
    end if;
  end if;
  return new;
end $$;

drop trigger if exists catat_jejak_progress on public.progress_entries;
create trigger catat_jejak_progress
  before insert or update on public.progress_entries
  for each row execute function public.catat_jejak();

drop trigger if exists catat_jejak_attendance on public.attendance;
create trigger catat_jejak_attendance
  before insert or update on public.attendance
  for each row execute function public.catat_jejak();

drop trigger if exists catat_jejak_notes on public.monthly_notes;
create trigger catat_jejak_notes
  before insert or update on public.monthly_notes
  for each row execute function public.catat_jejak();

-- Trigger `catat_jejak` hanya dipanggil oleh trigger; tidak perlu EXECUTE langsung.
revoke execute on function public.catat_jejak() from public, anon;
grant execute on function public.catat_jejak() to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- Verifikasi:
--   select policyname, cmd from pg_policies where schemaname='public'
--     and tablename in ('progress_entries','attendance','monthly_notes')
--     order by tablename, cmd, policyname;
--   -- hak hapus harus tetap: progress_delete/attendance_delete/notes_delete
-- ----------------------------------------------------------------------------
