-- ============================================================================
-- T6d3 (perintah Mudir, 25 November 2026): pulihkan 1 baris capaian seed yang hilang.
--
-- Temuan (rekonsiliasi 2.038 vs 2.039):
--   - Berkas seed memuat 2.036 baris `progress_entries`. Satu di antaranya TIDAK ada
--     di database: 1443.dummy-nis.024, Kitabah, Dzul Qa'dah (bulan 2), item
--     "Menyalin - 25" (id seed 6352df74-9063-59f6-8128-a0bc85de80a3).
--   - Excel sumber juga memuat "Menyalin : 25" di sel yang sama (santri 024, Dzul Qa'dah).
--   - Bukti kapan hilangnya: laporan `docs/qa/e2e_input_dropdown.json` (25 Nov 11:08)
--     mencatat 2.039 baris; sesudah sesi T6d2 menjadi 2.038. Jadi baris ini hilang pada
--     sesi T6d2, saat kolom jejak (entered_by/updated_by) belum ada sehingga penghapusan
--     tidak meninggalkan bukti siapa/kapan.
--   - Seluruh baris seed lain (termasuk tetangga 024 di bulan 0/3/4/5/6/7) masih ada
--     dengan `entered_at` yang sama (22 Nov 2026 04:10:41.644850): hanya satu baris yang
--     hilang, bukan seluruh baris santri/bulan.
--   - Penyebab yang paling masuk akal: uji/eksplorasi T6d2 versi awal menghapus baris
--     berdasarkan kunci alami (santri, bulan, mapel) di LUAR transaksi untuk menyiapkan
--     uji "menimpa capaian", lalu tidak memulihkan baris lama. Versi uji yang sekarang
--     menyiapkan baris sasaran di dalam transaksi + ROLLBACK (dibuktikan sidik jari).
--
-- Tindakan: masukkan kembali PERSIS baris seed itu (id, halaqah, item, putaran sama).
-- Aman dijalankan ulang (`on conflict do nothing`).
-- ============================================================================

insert into public.progress_entries (id, student_id, halaqah_id, subject_id, month_id, item_id, putaran)
select '6352df74-9063-59f6-8128-a0bc85de80a3'::uuid,
       st.id,
       '03940a34-6115-5c52-ba40-aa5114235b29'::uuid,
       '370dc13e-ae93-559b-93c8-844f8e9c5003'::uuid,
       '42fe3804-492d-5da2-ab50-7385ce68e38e'::uuid,
       '680f10fa-e6ed-55be-8f39-47980140b31e'::uuid,
       1
from public.students st
where st.nis = '1443.dummy-nis.024'
  and not exists (
    select 1 from public.progress_entries pe
    where pe.student_id = st.id
      and pe.subject_id = '370dc13e-ae93-559b-93c8-844f8e9c5003'::uuid
      and pe.month_id = '42fe3804-492d-5da2-ab50-7385ce68e38e'::uuid
  );

-- Verifikasi sesudah menjalankan (harus 1 baris, 2.039 total capaian):
--   select count(*) from public.progress_entries;                       -- 2039
--   select ci.label from public.progress_entries pe
--     join public.students s on s.id=pe.student_id
--     join public.hijri_months m on m.id=pe.month_id
--     join public.curriculum_items ci on ci.id=pe.item_id
--   where s.nis='1443.dummy-nis.024' and m.month_no=2 and ci.label like 'Menyalin%';  -- Menyalin - 25
