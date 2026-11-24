-- KUSAFA: notifikasi "santri belum punya halaqah" per domain (langkah pra-T6 [4/5]).
--
-- Kebutuhan Mudir 24 November 2026:
--   belum punya halaqah Al Qur'an  -> info ke Masul Al Quran;
--   belum punya halaqah Ilmu Wasilah -> info ke Masul Wasilah;
--   belum punya halaqah Ilmu Ghayah  -> info ke Masul Ghayah;
--   Admin dan Mudir menerima notifikasi dari ketiga domain;
--   Musyrif/ah dan Mudarris/ah tidak menerima.
--
-- Definisi "belum punya halaqah di domain D" (docs/SPEC.md bagian 9):
--   Santri aktif di tahun ajaran aktif, TIDAK punya KEANGGOTAAN AKTIF
--   (halaqah_members.left_on is null) pada halaqah aktif (halaqahs.is_active)
--   di tahun ajaran aktif untuk domain D.
--   - `halaqah_subjects`/`subjects` TIDAK dipakai untuk menentukan "punya halaqah":
--     domain sudah tersimpan di `halaqahs.domain`. Level 6 (Wasilah) yang belum
--     punya mata pelajaran/pengampu tetap dihitung sebagai halaqah (T8 yang
--     menangani pengampu/jadwal).
--   - Kolom `level_label` hanya keterangan tampilan (diambil dari
--     `student_levels` domain yang sama). Bila tidak ada, dikosongkan; santri
--     tetap muncul di notifikasi.
--   - Bila lebih dari satu tahun ajaran aktif, dipakai tahun ajaran terbaru
--     (hijri_year terbesar) agar hasil tidak berganda.
--
-- Bentuk: dua fungsi `security definer` yang memeriksa role di dalam fungsi
-- (pola hardening migrasi 20261121000007), bukan tabel baru. Notifikasi berasal
-- dari data yang ada, jadi baris hilang otomatis begitu santri dimasukkan ke
-- halaqah — tanpa proses ulang apa pun.
--
-- Hak akses:
--   - can_manage(domain)  -> Mudir, Admin, dan Masul domain itu;
--   - skrip lokal (postgres/service_role, tanpa JWT) -> semua domain untuk seed/QA;
--   - Musyrif/ah, Mudarris/ah, Wali, dan anon -> 0 baris (anon ditolak pada fungsi detail).
--
-- CATATAN keamanan: fungsi ini SECURITY DEFINER, jadi `current_user` di dalamnya
-- selalu = pemilik (postgres). Untuk memberi "tampil semua" hanya bagi skrip yang
-- benar-benar memakai akun admin database TANPA JWT, dipakai `session_user` (role
-- login yang sebenarnya) DIPASANGKAN dengan `current_app_role() is null`. Semua
-- pengguna aplikasi (PostgREST, session_user = authenticated, JWT ada) melewati
-- `can_manage` saja, sehingga Musyrif/Mudarris tetap 0 baris.

-- ---------- 1. Ringkasan jumlah per domain (untuk lencana notifikasi)
create or replace function public.students_without_halaqah_count()
returns table (domain public.domain_kind, jumlah bigint)
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  with tahun_aktif as (
    select ay.id, ay.hijri_year
    from public.academic_years ay
    where ay.is_active
    order by ay.hijri_year desc
    limit 1
  ),
  domain as (
    select unnest(enum_range(null::public.domain_kind)) as domain
  )
  select d.domain,
         count(*) filter (
           where not exists (
             select 1
             from public.halaqah_members hm
             join public.halaqahs h on h.id = hm.halaqah_id
             where hm.student_id = s.id
               and hm.left_on is null
               and h.is_active
               and h.academic_year_id = t.id
               and h.domain = d.domain
           )
         )::bigint as jumlah
  from tahun_aktif t
  cross join domain d
  join public.students s on s.is_active
  where (
      public.can_manage(d.domain)
      or (
        public.current_app_role() is null
        and session_user in ('postgres', 'service_role', 'supabase_admin')
      )
    )
  group by d.domain
  order by d.domain
$$;

-- ---------- 2. Daftar santri per domain (NIS, nama, level)
create or replace function public.students_without_halaqah()
returns table (
  domain public.domain_kind,
  academic_year_id uuid,
  hijri_year integer,
  student_id uuid,
  nis text,
  full_name text,
  level_label text
)
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  with tahun_aktif as (
    select ay.id, ay.hijri_year
    from public.academic_years ay
    where ay.is_active
    order by ay.hijri_year desc
    limit 1
  ),
  domain as (
    select unnest(enum_range(null::public.domain_kind)) as domain
  )
  select d.domain,
         t.id            as academic_year_id,
         t.hijri_year,
         s.id            as student_id,
         s.nis,
         s.full_name,
         sl.level_label
  from tahun_aktif t
  cross join domain d
  join public.students s on s.is_active
  left join public.student_levels sl
         on sl.student_id = s.id
        and sl.academic_year_id = t.id
        and sl.domain = d.domain
  where (
      public.can_manage(d.domain)
      or (
        public.current_app_role() is null
        and session_user in ('postgres', 'service_role', 'supabase_admin')
      )
    )
    and not exists (
      select 1
      from public.halaqah_members hm
      join public.halaqahs h on h.id = hm.halaqah_id
      where hm.student_id = s.id
        and hm.left_on is null
        and h.is_active
        and h.academic_year_id = t.id
        and h.domain = d.domain
    )
  order by d.domain,
           case when sl.level_label is null then 1 else 0 end,
           sl.level_label,
           s.full_name
$$;

-- ---------- 3. Bersihkan objek percobaan (belum pernah dirilis)
-- Pendekatan view `v_students_without_halaqah` diganti fungsi di atas karena
-- view `security_invoker` tidak bisa menyembunyikan baris dari Musyrif/ah
-- (policy baca tabel dasar berlaku untuk semua staf).
drop view if exists public.v_students_without_halaqah;

-- ---------- 4. Hardening: tanpa EXECUTE untuk anon/PUBLIC
revoke execute on function public.students_without_halaqah_count() from public, anon;
revoke execute on function public.students_without_halaqah()       from public, anon;
grant execute on function public.students_without_halaqah_count() to authenticated, service_role;
grant execute on function public.students_without_halaqah()       to authenticated, service_role;

-- Verifikasi setelah migrasi (data dummy 24 Nov 2026):
--   select * from public.students_without_halaqah_count();
--   -- alquran 0, wasilah 1 (NIS ...024), ghayah 2 (NIS ...023, ...024)
--   sebagai Musyrif/ah: kedua fungsi mengembalikan 0 baris.
--   sebagai anon: SELECT ditolak (42501).