# DATA-NOTES - pemetaan data Excel dan temuan data terbuka

Diperbarui: 24 November 2026 (perbaikan data pra-T6 langkah [3/5]). Angka di sini diperiksa langsung di database pada tanggal itu.
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
| Hari Efektif Rabiul Awwal (domain Al Qur'an) | **3 → 19 hari** lewat SQL terdokumentasi (lihat 3a). Excel sumber masih 3 dan **wajib diperbaiki Mudir** | 24 Nov 2026 |
| Bulan 0 (Data Awal) bisa ditulis staf lewat API | **Ditutup**: `month_is_open(bulan 0, domain)` = false (migrasi `20261121000008`) | 24 Nov 2026 |
| Santri tanpa halaqah di suatu domain | Dinyatakan **kasus uji resmi** (NIS 023/024), ditambah uji otomatis `scripts/qa/test_no_halaqah.py` (9/9 PASS) | 24 Nov 2026 |

### 3a. Koreksi Hari Efektif Rabiul Awwal (24 November 2026)

Keputusan Mudir: Hari Efektif Rabiul Awwal (bulan ke-6) domain Al Qur'an yang benar adalah **19 hari**, bukan 3.

| Hal | Isi |
|---|---|
| Nilai lama di database | `month_domain_settings.effective_days = 3` untuk `month_no = 6`, domain `alquran`, tahun ajaran 1447 |
| Nilai baru | **19** (diterapkan 24 Nov 2026) |
| Sumber Excel | `data/source/3-Al Quran (halaqah dan pencapaian).xlsx` |
| Sheet | `Halaqah Al Quran dan pencapaian` |
| Sel | `BZ4` = header `HE`; nilai `BZ5:B113` = 3 untuk 109 santri (blok Rabiul Awwal: BZ=HE, CA=H, CB=S, CC=I, CD=A) |
| Cara perbaikan | SQL terdokumentasi `scripts/db/fixes/2026-11-24_rabiul_awwal_effective_days.sql` (bukan mengedit Excel) |
| Cek presensi sebelum koreksi | 109 baris presensi Rabiul Awwal, semua `effective_days_override = NULL`, maksimum izin+sakit+alpha = 2, tidak ada yang melebihi 19 |
| Verifikasi sesudah | DB = 19; `v_attendance` Hadir 17–19 untuk 109 santri, tidak ada hadir negatif |

**Tindakan yang masih harus dilakukan Mudir:** perbaiki `BZ5:B113` di file Excel tersebut menjadi 19. Skrip seed membaca angka dari Excel, jadi selama Excel masih 3, **seed ulang akan mengembalikan nilai 3**. SQL koreksi di atas hanya untuk database yang sekarang; ia tidak mengubah Excel.

## 4. Penyimpangan data dummy yang sudah disepakati (jangan "diperbaiki" tanpa izin)

1. **69 capaian lebih kecil dari bulan sebelumnya** (Tahfidz 27, Kitabah 26, Tilawah 16; menyentuh 49 santri).
   Ini pengulangan/khatam yang memang wajar menurut Mudir, ditambah pola seed yang tidak selalu naik.
   **Keputusan Mudir 23 Nov 2026: dibiarkan** karena data akan dihapus di T10. Jangan diperbaiki dengan menebak.
   Di aplikasi, bidang seperti ini tampil dengan penanda ⚠ dan tidak ditanyakan bila tidak diubah.
2. **Data Awal (bulan 0) berisi 252 capaian.** Dipakai sebagai pembanding Syawwal pada tahun pertama. **Keputusan final 24 Nov 2026:** bulan 0 adalah catatan awal, bukan bulan efektif/target dan bukan bulan input staf; aturan lengkap ada di `docs/SPEC.md` bagian 4a. Isi 252 capaian itu dipertahankan untuk saat ini; pengosongan saat data asli dimuat diputuskan di T10.
3. **Label item bisa sama antar mata pelajaran** (mis. "Juz 'Amma - Al Ghasyiyah : 12" ada di Tilawah dan Kitabah karena buku Juz 'Amma dipakai dua bidang dengan urutan dan fokus berbeda). Di aplikasi sudah dibedakan dengan awalan nama mata pelajaran; **label di database tidak diubah**.

## 5. Masih terbuka - menunggu Excel atau keputusan Mudir

1. **Level 6 (4 santri) belum punya pengampu dan jadwal.** Halaqah dibuat tanpa mata pelajaran dan pengampu.
2. ~~**`1447.dummy-nis.024` hanya ada di Al Qur'an**, dan **`1447.dummy-nis.023` belum ada di Ghayah**.~~ **SELESAI 24 Nov 2026 (keputusan Mudir):** keduanya **dibiarkan** sebagai kasus uji resmi "santri yang tidak ikut semua halaqah". Jangan menambah atau mengarang baris. Perilaku yang benar: di domain yang tidak diikuti, santri **tidak ditampilkan** (bukan tampil 0), dan semua view/fungsi tetap berjalan tanpa galat. Diuji otomatis oleh `scripts/qa/test_no_halaqah.py` (9/9 PASS).
3. **Hari Efektif hanya terisi untuk domain `alquran`, bulan 1-7** (Syawwal s.d. Rabiul Akhir). Bulan 8-12 dan seluruh domain Wasilah/Ghayah belum punya `month_domain_settings`. Akibatnya notifikasi "data belum lengkap" tidak memeriksa bulan-bulan itu. Penyebabnya: layar pengisiannya baru dibuat di T8.
4. ~~**Hari Efektif Rabiul Awwal hanya 3 hari** sedangkan bulan sejenis 15-21.~~ **SELESAI 24 Nov 2026:** dikonfirmasi keliru; dikoreksi menjadi 19 lewat SQL (lihat bagian 3a). Excel sumber masih 3 dan wajib diperbaiki Mudir agar seed ulang tidak mengembalikan 3.
5. **`guardians` dan `monthly_notes` kosong (0 baris).** Wali belum diisi pada data dummy, dan catatan bulanan belum pernah diisi.
6. **`is_locked` belum pernah `true`.** Fitur kunci bulan belum dipakai pada data uji.
7. **Riwayat capaian berhenti di Rabiul Akhir**, dan Hari Efektif juga berhenti di bulan itu. Bulan Jumadal Ula dan sesudahnya kosong (bukan 0).

## 6. Bulan 0 (Data Awal) - aturan final dan bukti verifikasi 24 November 2026

Aturan lengkap ada di `docs/SPEC.md` bagian 4a. Ringkasnya: `hijri_months` sengaja 13 baris; `month_no` 0 = catatan awal (bukan bulan efektif/target), 1-12 = Syawwal s.d. Ramadhan.

Yang diperiksa langsung di database pada 24 November 2026:

| Pemeriksaan | Hasil |
|---|---|
| `v_months_ordered` tahun 1447 | 13 baris; bulan 0 `prev_month_id = NULL`; Syawwal `prev_month_id` = bulan 0 |
| Syawwal tahun berikutnya (uji dalam transaksi `create_academic_year(1448)`, lalu ROLLBACK) | Syawwal 1448 `prev_month_id` = **Ramadhan 1447**, bukan bulan 0 |
| `v_monthly_report` bulan 0 | `selisih`, `hadir`, `effective_days`, `target_monthly` semuanya **NULL** (bukan 0) |
| `targets.effective_month_id` | 327 baris sah menunjuk bulan 0 sebagai titik mulai; bulan 0 sendiri tidak menghitung target bulanan |
| `month_is_open(bulan 0, domain)` sebelum perbaikan | **true** (celah: staf bisa menulis lewat API) |
| `month_is_open(bulan 0, domain)` sesudah migrasi `20261121000008` | **false**; bulan 1-12 tetap mengikuti `is_locked` |
| Uji RLS dalam transaksi: Musyrif menulis capaian bulan 0 | **ditolak** `42501` (`InsufficientPrivilege`), lalu ROLLBACK |
| Uji RLS dalam transaksi: Admin menulis capaian bulan 0 | diterima (sesuai aturan: Admin/Mudir mengisi Data Awal manual), lalu ROLLBACK |

`can_manage(NULL)` mengembalikan `false` (aman, tidak error).

## 7. Uji otomatis santri tanpa halaqah (24 November 2026)

- Skrip: `scripts/qa/test_no_halaqah.py`; laporan: `docs/qa/no_halaqah_2026-11-24.json`.
- Hasil: **9/9 PASS**.
- Cakupan: keanggotaan 023 (alquran + wasilah, tanpa ghayah) dan 024 (hanya alquran); `v_monthly_report` tidak error dan **tidak menampilkan** baris untuk domain yang tidak diikuti; domain yang diikuti tetap tampil (024 alquran = 4 baris); `student_in_taught_domain`, `student_in_taught_halaqah`, `can_manage(NULL)` aman; RLS menolak pengampu menulis Ghayah untuk 023.
- Semua uji tulis berjalan di dalam transaksi lalu `ROLLBACK`; tidak ada baris data yang ditambah atau diubah.
