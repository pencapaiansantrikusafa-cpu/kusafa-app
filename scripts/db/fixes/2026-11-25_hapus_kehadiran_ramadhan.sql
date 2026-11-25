-- ============================================================================
-- T6d3 (keputusan Mudir, 25 November 2026): hapus lagi 7 baris kehadiran Ramadhan
-- Al Qur'an yang tanpa capaian.
--
-- Latar belakang:
--   23 November 2026 Mudir menyetujui penghapusan 7 baris `attendance` Ramadhan
--   (Al Qur'an) yang tidak punya capaian sama sekali (presensi 606 -> 599).
--   Penghapusan itu TIDAK pernah di-commit sebagai skrip, hanya dicatat di
--   docs/DATA-NOTES.md dan docs/CHANGELOG.md.
--   Pada 24 November 2026, sebelum commit pertama pukul 10:04, penyiapan sesi
--   menjalankan ULANG seed (`supabase/seed/02_school_data.sql`) - berkas seed
--   membuka dengan `truncate public.attendance ...` lalu mengisi semua baris yang
--   ada di Excel, termasuk 7 baris Ramadhan itu. Akibatnya baris yang sudah dihapus
--   Mudir hidup lagi. Tidak ada uji yang menulis ke tabel `attendance`, jadi
--   penyebabnya bukan uji melainkan seed ulang tanpa skrip lanjutan.
--
-- Perbaikan permanen:
--   (1) skrip ini, yang aman dijalankan ulang setelah seed mana pun;
--   (2) `scripts/qa/test_seed_bersih.py` memeriksa keadaan sesudah seed.
--       Bila seed dijalankan ulang, Jalankan:
--         python scripts/db/run_sql.py scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql
--
-- Yang dihapus HANYA baris kehadiran bulan Ramadhan (month_no = 12) Al Qur'an yang
-- santrinya tidak punya satu pun capaian di bulan itu. Baris dengan capaian,
-- domain lain, dan bulan lain tidak disentuh.
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI / run_sql membungkusnya.)

delete from public.attendance a
using public.hijri_months m
where a.month_id = m.id
  and m.month_no = 12
  and a.domain = 'alquran'
  and not exists (
    select 1 from public.progress_entries pe
    where pe.student_id = a.student_id
      and pe.month_id = a.month_id
  );

-- Verifikasi sesudah menjalankan (harus 0):
--   select count(*) from public.attendance a join public.hijri_months m on m.id = a.month_id
--   where m.month_no = 12
--     and not exists (select 1 from public.progress_entries pe
--                     where pe.student_id = a.student_id and pe.month_id = a.month_id);
