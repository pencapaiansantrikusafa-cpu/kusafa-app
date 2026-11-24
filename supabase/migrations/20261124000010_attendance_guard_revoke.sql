-- KUSAFA: pra-T6 [6/1] cabut EXECUTE `attendance_guard_override()` dari authenticated/PUBLIC.
--
-- Fungsi `attendance_guard_override` dipakai sebagai trigger `attendance_guard`
-- (migrasi 000006) dan bersifat SECURITY DEFINER (dijalankan sebagai pemilik = postgres),
-- jadi trigger TETAP berjalan meskipun EXECUTE dicabut dari authenticated.
-- Migrasi 000007 sengaja tidak memberi GRANT ke authenticated, tetapi karena fungsi itu
-- dibuat sebelum hardening, ACL `authenticated=X` masih tertinggal. Mencabutnya di sini
-- tidak menghentikan pemanggilan oleh trigger.
--
-- Aturan: fungsi trigger TIDAK boleh dipanggil langsung oleh authenticated/anon/PUBLIC.
-- Hanya pemilik (postgres) dan service_role yang boleh, agar tidak menjadi jalur bypass
-- aturan "effective_days_override hanya Admin/Mudir" lewat RPC langsung.

-- Cabut dari klien aplikasi dan PUBLIC.
revoke execute on function public.attendance_guard_override() from authenticated;
revoke execute on function public.attendance_guard_override() from public, anon;

-- Pastikan pemilik (postgres) dan service_role tetap bisa (untuk keperluan pemeliharaan/QA);
-- ini tidak membuka jalur ke aplikasi (service_role bukan role klien browser).
grant execute on function public.attendance_guard_override() to service_role;

-- Verifikasi (jalankan setelah migrasi):
--   select has_function_privilege('authenticated','public.attendance_guard_override()','EXECUTE'); -- false
--   select has_function_privilege('public','public.attendance_guard_override()','EXECUTE');      -- false
--   Trigger `attendance_guard` masih terpasang:
--   select tgname from pg_trigger where tgfoid = 'public.attendance_guard_override()'::regprocedure;
--   Pengujian B2 di scripts/qa/run_pre_t6_db_tests.py tetap memastikan trigger menolak
--   override dari musyrif dan menerima dari admin (transaksi ROLLBACK).