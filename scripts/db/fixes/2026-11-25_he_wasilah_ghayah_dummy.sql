-- ============================================================================
-- DUMMY - Hari Efektif & kehadiran Ilmu Wasilah dan Ilmu Ghayah, bulan 1-7.
--
-- Status: **DATA DUMMY**. Bukan angka dari Mudir. Wajib diganti data asli.
-- Izin: Mudir, 25 November 2026 (perintah kerja T6): "Hari Efektif Wasilah dan
--   Ghayah belum ada data dari Mudir. IZIN KHUSUS: kamu boleh membuat data DUMMY
--   Hari Efektif untuk Wasilah dan Ghayah, bulan 1-7 saja ... (1) turunkan dari
--   Excel Wasilah/Ghayah bila ada ...; (2) jika tidak ada, samakan dengan nilai
--   Al Qur'an per bulan."
--   Kehadiran: Mudir memilih "buat baris kehadiran 0/0/0" (25 November 2026),
--   karena Hadir = Hari Efektif - (izin+sakit+alpha) dan tanpa baris kehadiran
--   Hadir tetap kosong walau Hari Efektif diisi.
--
-- Sumber yang diperiksa (Langkah 0, 25 November 2026):
--   data/source/4-Ilmu Wasilah.xlsx  -> sheet "Halaqah Ilmu Wasilah" & "Jadwal
--       Ilmu Wasilah". TIDAK ADA kolom Hari Efektif / Hadir / izin / sakit / alpha.
--   data/source/5-Ilmu Ghayah.xlsx   -> sheet "Halaqah Ilmu Ghayah". TIDAK ADA
--       kolom Hari Efektif / Hadir / izin / sakit / alpha.
--   Karena itu aturan (1) tidak bisa dipakai; dipakai aturan (2): Hari Efektif
--   Wasilah dan Ghayah = Hari Efektif Al Qur'an pada bulan yang sama.
--
-- Yang dibuat skrip ini:
--   1. month_domain_settings (domain wasilah & ghayah, bulan 1-7, tahun 1447):
--      effective_days = angka Al Qur'an bulan itu; is_locked = false.
--   2. attendance (domain wasilah & ghayah): satu baris per anggota aktif halaqah
--      domain itu, bulan 1-7, izin = sakit = alpha = 0, effective_days_override
--      kosong. Tanpa ini, Hadir kosong.
--
-- Yang TIDAK dibuat skrip ini (sengaja):
--   - Tidak ada `progress_entries` untuk Wasilah/Ghayah. Capaian diisi pengampu
--     lewat halaman Input (T6b). Capaian karangan akan mengaburkan data asli.
--   - Tidak ada target (`targets`). Target adalah pekerjaan T7.
--   - Tidak ada catatan (`monthly_notes`).
--
-- Aman dijalankan berulang: memakai `on conflict ... do nothing` sehingga nilai
-- yang sudah ada (termasuk bila Mudir sudah mengisi angka asli) TIDAK ditimpa.
--
-- Jalankan:
--   python scripts/db/run_sql.py scripts/db/fixes/2026-11-25_he_wasilah_ghayah_dummy.sql
-- ============================================================================

begin;

-- ---------- 1. Hari Efektif: samakan dengan Al Qur'an pada bulan yang sama
insert into public.month_domain_settings (month_id, domain, effective_days, is_locked)
select aq.month_id, d.domain, aq.effective_days, false
from public.month_domain_settings aq
cross join (values ('wasilah'::public.domain_kind), ('ghayah'::public.domain_kind)) as d(domain)
join public.hijri_months m on m.id = aq.month_id
where aq.domain = 'alquran'
  and m.month_no between 1 and 7
on conflict (month_id, domain) do nothing;

-- ---------- 2. Kehadiran 0/0/0 untuk tiap anggota aktif halaqah domain itu
insert into public.attendance
  (student_id, month_id, domain, izin, sakit, alpha, effective_days_override)
select distinct
  hm.student_id,
  s.month_id,
  h.domain,
  0, 0, 0,
  null::integer
from public.halaqahs h
join public.halaqah_members hm on hm.halaqah_id = h.id and hm.left_on is null
join public.month_domain_settings s on s.domain = h.domain
join public.hijri_months m on m.id = s.month_id
where h.domain in ('wasilah', 'ghayah')
  and h.is_active
  and m.month_no between 1 and 7
on conflict (student_id, month_id, domain) do nothing;

-- ---------- Verifikasi (dicetak saat dijalankan sebagai skrip)
select d.domain,
       count(*) as bulan,
       min(s.effective_days) as he_min,
       max(s.effective_days) as he_max
from public.month_domain_settings s
join (values ('wasilah'::public.domain_kind), ('ghayah'::public.domain_kind)) as d(domain)
  on d.domain = s.domain
group by d.domain
order by d.domain;

select domain, count(*) as baris_kehadiran, sum(izin + sakit + alpha) as total_absen
from public.attendance
where domain in ('wasilah', 'ghayah')
group by domain
order by domain;

commit;
