-- ============================================================================
-- T6d3 (keputusan Mudir, 25 November 2026): pulihkan izin/sakit/alpha Shafar
-- (bulan 5, Al Qur'an) agar SAMA dengan sumber data (Excel -> seed).
--
-- Hasil penyelidikan (yang bisa dibuktikan):
--   - Sumber data: `data/source/3-Al Quran (halaqah dan pencapaian).xlsx`, kolom
--     Shafar (67 = HE, 68 = H, 69 = S, 70 = I, 71 = A). 93 santri punya HE Shafar;
--     36 di antaranya punya S/I/A > 0 (total S 24, I 43, A 6). Seed sama dengan Excel.
--   - Di database ke-36 baris itu bernilai 0/0/0. Tidak ada uji QA di repo yang
--     menulis ke `public.attendance` (test_t6a/test_t6b/test_t6d2/regression/
--     compare_rabiul_awwal/smoke hanya MEMBACA tabel itu).
--   - Tidak ada jejak perubahan: `updated_by`/`updated_at` baru ada sejak migrasi
--     T6d2 (20261125000017); koneksi tanpa JWT juga tidak mengisi `entered_by`.
--   - Semua baris Shafar bertanggal seed (22 Nov 2026 04:10 UTC, entered_by NULL):
--     barisnya tidak dibuat ulang, NILAINYA yang diubah. Kesimpulan: pengubahan
--     manual di luar repo sebelum T6d2.
--
-- Tindakan: ubah HANYA 37 baris yang berbeda di database dibanding seed (36 bernilai
-- > 0 + 1 baris bernilai 0). Tidak menjalankan seed penuh. Aman dijalankan ulang
-- (baris yang sudah sama tidak diubah).
-- ============================================================================

-- Nilai acuan dari berkas seed (NIS = kunci stabil santri).
with acuan(nis, izin, sakit, alpha) as (
  values
  ('1442.dummy-nis.001', 0, 0, 3),
  ('1442.dummy-nis.009', 0, 0, 1),
  ('1442.dummy-nis.010', 3, 0, 0),
  ('1442.dummy-nis.011', 2, 0, 0),
  ('1442.dummy-nis.012', 1, 1, 0),
  ('1442.dummy-nis.014', 1, 0, 0),
  ('1442.dummy-nis.030', 1, 0, 0),
  ('1442.dummy-nis.036', 1, 0, 0),
  ('1443.dummy-nis.012', 0, 1, 0),
  ('1443.dummy-nis.018', 1, 0, 0),
  ('1443.dummy-nis.020', 1, 0, 0),
  ('1443.dummy-nis.024', 1, 2, 0),
  ('1443.dummy-nis.026', 1, 1, 0),
  ('1444.dummy-nis.001', 2, 1, 0),
  ('1444.dummy-nis.005', 1, 0, 0),
  ('1444.dummy-nis.007', 1, 0, 0),
  ('1444.dummy-nis.014', 1, 0, 0),
  ('1444.dummy-nis.015', 2, 0, 0),
  ('1444.dummy-nis.016', 1, 0, 0),
  ('1444.dummy-nis.019', 1, 0, 0),
  ('1444.dummy-nis.021', 1, 0, 0),
  ('1444.dummy-nis.022', 1, 1, 0),
  ('1445.dummy-nis.003', 1, 0, 0),
  ('1445.dummy-nis.011', 4, 0, 2),
  ('1445.dummy-nis.020', 3, 2, 0),
  ('1446.dummy-nis.001', 1, 2, 0),
  ('1446.dummy-nis.004', 2, 0, 0),
  ('1446.dummy-nis.007', 1, 4, 0),
  ('1446.dummy-nis.008', 1, 0, 0),
  ('1446.dummy-nis.012', 1, 0, 0),
  ('1446.dummy-nis.019', 1, 0, 0),
  ('1446.dummy-nis.022', 0, 3, 0),
  ('1447.dummy-nis.013', 0, 2, 0),
  ('1447.dummy-nis.015', 3, 0, 0),
  ('1447.dummy-nis.017', 1, 0, 0),
  ('1447.dummy-nis.019', 0, 2, 0),
  ('1447.dummy-nis.021', 0, 2, 0)
)
update public.attendance a
set izin = acuan.izin,
    sakit = acuan.sakit,
    alpha = acuan.alpha
from acuan
join public.students st on st.nis = acuan.nis
join public.hijri_months m on m.month_no = 5
where a.student_id = st.id
  and a.month_id = m.id
  and a.domain = 'alquran'
  and (a.izin, a.sakit, a.alpha) is distinct from (acuan.izin, acuan.sakit, acuan.alpha);

-- Verifikasi sesudah menjalankan: Hadir Shafar = HE - (izin + sakit + alpha)
-- harus sama dengan Excel untuk semua 93 santri. Buktikan dengan:
--   python scripts/qa/compare_rabiul_awwal_excel.py --semua
