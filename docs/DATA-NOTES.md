# DATA-NOTES - pemetaan data dan temuan yang masih terbuka

## Alur seed
1. Taruh 5 file Excel di `data/source/` (berawalan `1-`, `2-`, `3-`, `4-`, `5-`). Satu file per awalan.
2. `python scripts/seed/build_seed.py` memvalidasi data dan menulis `supabase/seed/01_curriculum.sql`, `02_school_data.sql`, `scripts/seed/output/users.csv`, dan `seed-report.md`.
   Skrip berhenti dengan galat jika data tidak dikenali. Baca `seed-report.md`.
3. Jalankan migrasi, lalu `01_curriculum.sql`, lalu `python scripts/seed/create_auth_users.py`, lalu `02_school_data.sql` (lihat README).
Seed bersifat destruktif (truncate). Hanya untuk data uji.

## Aturan pemetaan (satu-satunya aturan yang dipakai skrip)
- Tahun ajaran dummy: 1447 (`ACADEMIC_HIJRI_YEAR` di skrip). Ubah jika berbeda.
- Dropdown Al Qur'an memakai kolom Value dari file. Wasilah dan Ghayah: value = nomor urut baris dalam buku; **urutan buku dalam satu bidang mengikuti urutan baris di sheet** (dikonfirmasi Mudir).
- Iqro' 1-6 adalah buku terpisah, dijajarkan ke Karima: `value_offset` = akhir Karima - akhir Iqro'.
- Tilawah buku "Al Qur'an" bersifat siklik (604 halaman). Label santri "Halaman N" = buku Al Qur'an halaman N (dikonfirmasi Mudir). Label lain berbentuk "Buku : N".
- Level dinormalkan: "level 3D" menjadi "Level 3D", "Al-Qur'an" menjadi "Al Qur'an".
- Gender santri dari kolom L/P (Al Qur'an), atau dari Kategori Putra/Putri (Ghayah) bila tidak ada.
- Target Al Qur'an (Tilawah, Tahfidz, Kitabah) per santri dibuat sebagai target harian berstatus disetujui, berlaku dari bulan Data Awal.
- Riwayat capaian dummy: kenaikan putaran Tilawah hanya untuk seed dan memakai pola "halaman >= 450 lalu <= 150 = khatam"; semua kasus dicatat di seed-report.md. Di aplikasi, khatam hanya lewat pilihan eksplisit.
- Satuan (`subjects.unit`) diambil dari satuan yang paling sering di bidang itu; sebagian bidang punya satuan campuran antar buku.
- Akun dummy: `<nama>@kusafa.test`, kata sandi acak di `scripts/seed/output/users.csv`.

## Sudah beres (dikonfirmasi Mudir, file Excel diperbaiki 21 November 2026)
- Pergeseran kolom di sheet Al Qur'an: tidak ada lagi (seed berjalan tanpa `--auto-align-columns`; opsi itu tetap ada bila kelak muncul lagi).
- Hari Efektif: satu angka per domain per bulan (Muharram = 19). Santri yang masuk terlambat (NIS berawalan 1447, 24 santri) memakai Hari Efektif khusus (9 hari pada Muharram). Seed menyimpannya sebagai `attendance.effective_days_override`; angka domain diambil dari nilai yang paling sering.
- Target Kitabah 0 untuk 4 santri (1444.dummy-nis.005, 1444.dummy-nis.009, 1445.dummy-nis.007, 1445.dummy-nis.008) diganti menjadi 0,5 oleh Mudir di file Excel.
- Kolom H (hadir) di sheet Al Qur'an diabaikan. Aplikasi menghitung Hadir otomatis dari Hari Efektif dikurangi (izin + sakit + alpha); seed hanya menyimpan Hari Efektif, izin, sakit, alpha.
- Sisa penggantian "Hitung" menjadi "Hisab" di file dropdown sudah dikembalikan; hanya nama bidang yang "Hisab".
- Urutan buku Wasilah dan Ghayah dalam satu bidang = urutan baris di sheet (dikonfirmasi). Urutan dan isi dropdown dapat diubah lewat aplikasi (lihat docs/SPEC.md bagian 4b).

## Temuan data yang masih terbuka (menunggu Mudir)
1. Level 6 (4 santri) belum punya pengampu dan jadwal. Halaqah dibuat tanpa mata pelajaran dan pengampu.
2. Santri 1447.dummy-nis.024 hanya di Al Qur'an, dan 1447.dummy-nis.023 belum di Ghayah. Dianggap santri baru yang belum ditata.
3. Capaian yang mundur (pengulangan atau khatam) tercatat di seed-report.md. Menurut Mudir pengulangan itu wajar; tidak perlu diperbaiki.
