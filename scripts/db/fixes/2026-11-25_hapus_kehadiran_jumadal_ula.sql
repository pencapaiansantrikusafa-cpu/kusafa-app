-- ============================================================================
-- T6e (perintah Mudir, 25 November 2026): hapus 7 baris kehadiran Jumadal Ula
-- percobaan Admin (0/0/0) yang tidak punya capaian lagi.
--
-- Bukti bahwa ini percobaan, bukan data sah:
--   - 7 baris, semuanya halaqah HLQ-PA-1, izin/sakit/alpha = 0, override NULL;
--   - `entered_by = Admin`, `entered_at` 25 Nov 2026 02:14 - detik yang sama dengan
--     3 baris capaian percobaan yang sudah dihapus lewat fitur "Hapus capaian" (T6e);
--   - bulan Jumadal Ula (month_no 8) belum punya Hari Efektif untuk domain mana pun
--     (`month_domain_settings` hanya bulan 1-7), jadi tidak ada laporan yang memakainya;
--   - setelah 3 capaian dihapus, bulan 8 tidak berisi apa pun.
--
-- Skrip ini hanya menghapus baris kehadiran bulan 8 yang TIDAK punya capaian untuk
-- santri+bulan yang sama. Aman dijalankan ulang.
-- ============================================================================

delete from public.attendance a
using public.hijri_months m
where a.month_id = m.id
  and m.month_no = 8
  and not exists (
    select 1 from public.progress_entries pe
    where pe.student_id = a.student_id and pe.month_id = a.month_id
  );

-- Verifikasi: baris kehadiran bulan 8 harus 0
--   select count(*) from public.attendance a join public.hijri_months m on m.id = a.month_id
--   where m.month_no = 8;   -- 0
-- Kehadiran bulan 1-7 tetap 606 / 756 / 749.
