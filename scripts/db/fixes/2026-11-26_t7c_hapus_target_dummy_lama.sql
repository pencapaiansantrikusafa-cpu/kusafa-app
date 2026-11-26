-- ============================================================================
-- T7c [1/3]: hapus DUMMY target Wasilah/Ghayah bentuk LAMA (amount = 1).
-- Izin Mudir 26 November 2026 (HANYA untuk target Wasilah/Ghayah; target Al Qur'an
-- tidak disentuh). Dihilangkan karena bentuk target Wasilah/Ghayah berubah menjadi
-- TUJUAN AKHIR (butir kurikulum, tanpa amount) sehingga baris `amount = 1` tidak lagi
-- sah oleh constraint baru `targets_bentuk_check`.
--
-- IDEMPOTEN dan AMAN dijalankan ulang: hanya menghapus baris bentuk LAMA, yaitu
--   - domain wasilah/ghayah, `amount = 1`, `target_item_id` kosong, DAN
--   - catatan persis bentuk lama ('...Ghayah, diganti data asli...' dengan KOMA),
-- JADI TIDAK IKUT MENGHAPUS DUMMY BENTUK BARU (tujuan akhir), yang catatannya
-- '...Ghayah (tujuan akhir), diganti data asli...'.
-- Setiap baris tercatat di `change_log` oleh trigger `catat_perubahan_targets`.
-- Jalankan: npm run db:sql -- scripts/db/fixes/2026-11-26_t7c_hapus_target_dummy_lama.sql
-- ============================================================================

delete from public.targets
where domain in ('wasilah', 'ghayah')
  and amount = 1
  and target_item_id is null
  and note like 'DUMMY - target sementara Wasilah/Ghayah,%';
