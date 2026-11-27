-- ============================================================================
-- R5 / DATA-NOTES 0b (perintah Mudir, 27 November 2026): hapus SATU baris target
-- Al Qur'an percobaan Mudir (26 November 2026) yang tertinggal dari uji T7 [2/2].
--
-- Baris yang dihapus (DIVERIFIKASI lewat query sebelum dihapus):
--   domain      = alquran
--   santri      = NIS 1444.dummy-nis.013 ("Santriwan fulan 26")
--   mapel       = Tahfidz
--   bulan       = Rabiul Akhir (month_no 7)
--   amount      = 2 (harian), status = disetujui, note = kosong
--   dibuat      = 2026-11-26 09:27:07 UTC
--   proposed_by = approved_by = Ust. Fulan 1 (role musyrif)
--
-- Ini PERCOBAAN, bukan data sah: pengampu (musyrif) tidak boleh menyetujui
-- target sendiri, jadi baris ini hanya bisa lahir dari koneksi admin (uji).
-- Penghapusan dicatat otomatis di `change_log` oleh trigger `catat_perubahan`
-- (DELETE pada `targets`). Aman dijalankan ulang: bila baris sudah tidak ada,
-- DELETE menghapus 0 baris.
--
-- Jalankan: npm run db:sql -- scripts/db/fixes/2026-11-27_hapus_target_percobaan_r5.sql
-- ============================================================================

delete from public.targets t
using public.students s, public.hijri_months m, public.subjects sub
where t.student_id = s.id
  and t.effective_month_id = m.id
  and t.subject_id = sub.id
  and t.domain = 'alquran'
  and s.nis = '1444.dummy-nis.013'
  and sub.name = 'Tahfidz'
  and m.name = 'Rabiul Akhir'
  and t.amount = 2
  and t.amount_period = 'harian'
  and t.status = 'disetujui'
  and t.note is null
  and t.created_at::date = date '2026-11-26';

-- Verifikasi setelah dijalankan:
--   select count(*) from targets where domain='alquran';        -- 327
--   select count(*) from change_log
--     where tabel='targets' and aksi='delete'
--       and terjadi_pada::date = date '2026-11-27';   -- 1 baris baru
