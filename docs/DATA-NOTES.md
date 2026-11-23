# DATA-NOTES - pemetaan data Excel dan temuan data terbuka

Diperbarui: 23 November 2026. Angka di sini diperiksa langsung di database pada tanggal itu.
Jangan menulis data santri asli di berkas ini; semua contoh di bawah adalah data dummy.

---

## 1. Alur seed (tidak berubah)

1. Taruh 5 file Excel di `data/source/` (berawalan `1-` s.d. `5-`). Berkas tidak di-commit.
2. `python scripts/seed/build_seed.py` memvalidasi data lalu menulis `supabase/seed/01_curriculum.sql`, `02_school_data.sql`, `scripts/seed/output/users.csv`, dan `seed-report.md`.
   Skrip berhenti dengan galat bila ada data yang tidak dikenali. Selalu baca `seed-report.md`.
3. Urutan menjalankan: migrasi → `01_curriculum.sql` → `python scripts/seed/create_auth_users.py` → `02_school_data.sql`.
4. Seed bersifat **destruktif (truncate)**. Hanya untuk data uji, jangan dijalankan ulang tanpa izin Mudir.

## 2. Aturan pemetaan yang dipakai skrip (jangan diubah tanpa persetujuan)

- Tahun ajaran dummy: 1447 (`ACADEMIC_HIJRI_YEAR`).
- Dropdown Al Qur'an memakai kolom Value dari Excel. Wasilah dan Ghayah: `value` = nomor urut baris dalam buku; urutan buku dalam satu bidang mengikuti urutan baris di sheet (dikonfirmasi Mudir).
- Iqro' 1-6 adalah buku terpisah, dijajarkan ke Karima: `value_offset` = akhir Karima − akhir Iqro'.
- Tilawah buku "Al Qur'an" bersifat siklik (604 halaman). Label "Halaman N" berarti buku Al Qur'an halaman N.
- Level dinormalkan ("level 3D" → "Level 3D", "Al-Qur'an" → "Al Qur'an").
- Gender diambil dari kolom L/P (Al Qur'an), atau Kategori Putra/Putri (Ghayah) bila tidak ada.
- Target Al Qur'an (Tilawah, Tahfidz, Kitabah) per santri dibuat sebagai target harian berstatus `disetujui`, berlaku dari bulan Data Awal.
- Riwayat capaian dummy: kenaikan putaran Tilawah dibuat dengan pola "halaman ≥ 450 lalu ≤ 150 = khatam"; semua kasus dicatat di `seed-report.md`. **Di aplikasi, khatam hanya lewat pilihan eksplisit.**
- Satuan (`subjects.unit`) diambil dari yang paling sering muncul per bidang; sebagian bidang punya satuan campuran antar buku.
- Akun dummy: `<nama>@kusafa.test`, kata sandi acak di `scripts/seed/output/users.csv` (tidak di-commit).
- Kolom H (hadir) di sheet Al Qur'an **diabaikan**; Hadir dihitung aplikasi dari Hari Efektif − (izin + sakit + alpha).

## 3. Sudah beres

| Hal | Keadaan | Tanggal |
|---|---|---|
| Pergeseran kolom di sheet Al Qur'an | Tidak ada lagi; seed berjalan tanpa `--auto-align-columns` (opsi tetap tersedia bila muncul lagi) | 21 Nov 2026 |
| Hari Efektif per domain per bulan | Satu angka per domain per bulan; Muharram = 19 | 21 Nov 2026 |
| 24 santri baru (NIS berawalan 1447) | Memakai Hari Efektif khusus (9 hari pada Muharram) lewat `attendance.effective_days_override` | 21 Nov 2026 |
| Target Kitabah 0 untuk 4 santri (`1444.dummy-nis.005`, `.009`, `1445.dummy-nis.007`, `.008`) | Diganti 0,5 di Excel oleh Mudir | 21 Nov 2026 |
| Kolom H (hadir) di Excel | Diabaikan; dihitung aplikasi | 21 Nov 2026 |
| Sisa penulisan "Hitung" | Dikembalikan menjadi "Hisab" | 21 Nov 2026 |
| Urutan buku Wasilah dan Ghayah | Mengikuti urutan baris sheet (dikonfirmasi) | 21 Nov 2026 |
| 7 baris `attendance` Ramadhan tanpa capaian (izin/sakit/alpha semuanya 0) | **Dihapus** 23 Nov 2026 atas persetujuan Mudir. Presensi 606 → 599 | 23 Nov 2026 |
| Ringkasan kehadiran menampilkan "0" untuk bulan yang belum diisi | Diperbaiki: kini tampil "—" (kosong bukan 0) | 23 Nov 2026 |
| Item dropdown terduplikasi (kunci ganda React) | Diperbaiki: memo tidak lagi mengubah state | 23 Nov 2026 |

## 4. Penyimpangan data dummy yang sudah disepakati (jangan "diperbaiki" tanpa izin)

1. **69 capaian lebih kecil dari bulan sebelumnya** (Tahfidz 27, Kitabah 26, Tilawah 16; menyentuh 49 santri).
   Ini pengulangan/khatam yang memang wajar menurut Mudir, ditambah pola seed yang tidak selalu naik.
   **Keputusan Mudir 23 Nov 2026: dibiarkan** karena data akan dihapus di T10. Jangan diperbaiki dengan menebak.
   Di aplikasi, bidang seperti ini tampil dengan penanda ⚠ dan tidak ditanyakan bila tidak diubah.
2. **Data Awal (bulan 0) berisi 252 capaian.** Dipakai sebagai pembanding Syawwal pada tahun pertama. Belum diputuskan apakah akan kosong saat data asli dimuat.
3. **Label item bisa sama antar mata pelajaran** (mis. "Juz 'Amma - Al Ghasyiyah : 12" ada di Tilawah dan Kitabah karena buku Juz 'Amma dipakai dua bidang dengan urutan dan fokus berbeda). Di aplikasi sudah dibedakan dengan awalan nama mata pelajaran; **label di database tidak diubah**.

## 5. Masih terbuka - menunggu Excel atau keputusan Mudir

1. **Level 6 (4 santri) belum punya pengampu dan jadwal.** Halaqah dibuat tanpa mata pelajaran dan pengampu.
2. **`1447.dummy-nis.024` hanya ada di Al Qur'an**, dan **`1447.dummy-nis.023` belum ada di Ghayah**. Dianggap santri baru yang belum ditata.
3. **Hari Efektif hanya terisi untuk domain `alquran`, bulan 1-7** (Syawwal s.d. Rabiul Akhir). Bulan 8-12 dan seluruh domain Wasilah/Ghayah belum punya `month_domain_settings`. Akibatnya notifikasi "data belum lengkap" tidak memeriksa bulan-bulan itu. Penyebabnya: layar pengisiannya baru dibuat di T8.
4. **Hari Efektif Rabiul Awwal hanya 3 hari** sedangkan bulan sejenis 15-21. Terlihat janggal; **belum diubah**, menunggu konfirmasi apakah memang begitu di Excel.
5. **`guardians` dan `monthly_notes` kosong (0 baris).** Wali belum diisi pada data dummy, dan catatan bulanan belum pernah diisi.
6. **`is_locked` belum pernah `true`.** Fitur kunci bulan belum dipakai pada data uji.
7. **Riwayat capaian berhenti di Rabiul Akhir**, dan Hari Efektif juga berhenti di bulan itu. Bulan Jumadal Ula dan sesudahnya kosong (bukan 0).
