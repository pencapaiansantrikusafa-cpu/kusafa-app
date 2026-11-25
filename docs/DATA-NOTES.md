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
| 7 baris `attendance` Ramadhan tanpa capaian (izin/sakit/alpha semuanya 0) | **Dihapus** 23 Nov 2026 atas persetujuan Mudir. Presensi 606 → 599. **Muncul lagi** karena seed dijalankan ulang 24 Nov (penghapusan lama tidak pernah jadi skrip); **dihapus lagi 25 Nov** lewat `scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql` + uji penjaga `test_seed_bersih.py` | 25 Nov 2026 |
| Ringkasan kehadiran menampilkan "0" untuk bulan yang belum diisi | Diperbaiki: kini tampil "—" (kosong bukan 0) | 23 Nov 2026 |
| Item dropdown terduplikasi (kunci ganda React) | Diperbaiki: memo tidak lagi mengubah state | 23 Nov 2026 |
| Hari Efektif Rabiul Awwal (domain Al Qur'an) | **3 hari adalah BENAR** (ada libur ~2 pekan lebih). Nilai 19 sempat diterapkan keliru lalu **dikembalikan ke 3** 24 Nov 2026 (lihat 3a) | 24 Nov 2026 |
| Bulan 0 (Data Awal) bisa ditulis staf lewat API | **Ditutup**: `month_is_open(bulan 0, domain)` = false (migrasi `20261121000008`) | 24 Nov 2026 |
| Santri tanpa halaqah di suatu domain | Dinyatakan **kasus uji resmi** (NIS 023/024), ditambah uji otomatis `scripts/qa/test_no_halaqah.py` (9/9 PASS) | 24 Nov 2026 |
| Jejak pengisi capaian/kehadiran/catatan | Sejak T6d2 ketiga tabel punya `entered_by`/`entered_at` (pengisi terakhir) dan `updated_by`/`updated_at` (pengubah terakhir). Trigger `catat_jejak`; koneksi tanpa JWT (seed) tidak menyentuh baris lama. Uji `test_t6d2_masul_input.py` 68/68 | 25 Nov 2026 |
| Notifikasi "santri belum punya halaqah" per domain | Dibuat (fungsi `students_without_halaqah`/`_count`, migrasi 000009); tanpa tabel baru; hilang otomatis saat santri diberi halaqah. Uji 13/13 PASS. Lihat bagian 8 dan SPEC §9 | 24 Nov 2026 |

### 3a. Hari Efektif Rabiul Awwal = 3 hari adalah BENAR (koreksi 24 November 2026)

**Keputusan Mudir (koreksi, menimpa instruksi sebelumnya):** Hari Efektif Rabiul Awwal (bulan ke-6) domain Al Qur'an = **3 hari** adalah **BENAR**, karena ada **libur sekitar dua pekan lebih**. Perubahan 3 → 19 pada 24 November 2026 adalah **kekeliruan** dan sudah **dikembalikan ke 3**.

| Hal | Isi |
|---|---|
| Nilai yang benar | **3 hari** (`month_domain_settings.effective_days` untuk `month_no = 6`, domain `alquran`, tahun 1447) |
| Alasan | Libur sekitar dua pekan lebih pada Rabiul Awwal |
| Sumber acuan | `data/source/3-Al Quran (halaqah dan pencapaian).xlsx` → `BZ4` = header `HE`; `BZ5:BZ113` = 3 untuk 109 santri; `CA`=H, `CB`=S, `CC`=I, `CD`=A |
| Skrip pemulihan | `scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql` (19 → 3) |
| Skrip lama 3 → 19 | `scripts/db/fixes/2026-11-24_rabiul_awwal_effective_days.sql` — **DIBATALKAN**, diberi penghenti keras; hanya jejak riwayat |
| Verifikasi sesudah | DB = 3; `v_attendance` Hadir **1–3** untuk 109 santri (Hadir = 3 − izin − sakit − alpha), tidak ada Hadir negatif |
| Kecocokan dengan Excel | `scripts/qa/compare_rabiul_awwal_excel.py` **7/7 PASS**: HE, Hadir, izin/sakit/alpha, dan label+posisi capaian **cocok untuk seluruh 109 santri**; sampel 15 santri (termasuk Hadir 1 dan 2) dirinci di laporan |
| Kolom turunan | **Tidak ada yang ikut berubah.** `hadir`, `selisih`, `target_monthly` dihitung view (bukan kolom tersimpan). Snapshot `attendance`, `progress_entries`, `targets`, `curriculum_items`, `books`, `students` identik sebelum/sesudah pemulihan |
| UI | Halaman Capaian Al Qur'an bulan Rabiul Awwal menampilkan Hadir **3/3** (bukan 17/19) |

**Catatan:** Hari Efektif kecil (mis. Syawwal = 4, Rabiul Awwal = 3) adalah **data sah** karena libur. Jangan menaikkannya atau menandainya "janggal" tanpa konfirmasi Mudir (lihat `AGENTS.md`).

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
3. **Hari Efektif hanya terisi untuk domain `alquran`, bulan 1-7** (Syawwal s.d. Rabiul Akhir). Bulan 8-12 belum punya `month_domain_settings`. Akibatnya notifikasi "data belum lengkap" tidak memeriksa bulan-bulan itu. Penyebabnya: layar pengisiannya baru dibuat di T8.
   **DUMMY (25 Nov 2026, izin Mudir):** `wasilah` dan `ghayah` kini punya Hari Efektif **DUMMY** bulan 1-7, **disamakan dengan Al Qur'an** bulan yang sama, plus baris kehadiran **0/0/0**. Excel Wasilah (`4-Ilmu Wasilah.xlsx`) dan Ghayah (`5-Ilmu Ghayah.xlsx`) **tidak punya kolom HE/Hadir/izin/sakit/alpha**, jadi aturan "turunkan dari Excel" tidak dapat dipakai. Skrip: `scripts/db/fixes/2026-11-25_he_wasilah_ghayah_dummy.sql` (aman dijalankan ulang; tidak menimpa nilai yang sudah ada). **Wajib diganti data asli lewat T8/T10.**
4. ~~**Hari Efektif Rabiul Awwal hanya 3 hari** sedangkan bulan sejenis 15-21.~~ **BUKAN MASALAH (koreksi Mudir 24 Nov 2026):** 3 hari **BENAR** karena libur sekitar dua pekan lebih. Nilai 19 sempat dipakai keliru dan sudah dikembalikan ke 3 (bagian 3a). Jangan diubah tanpa konfirmasi Mudir.
5. **`guardians` dan `monthly_notes` kosong (0 baris).** Wali belum diisi pada data dummy, dan catatan bulanan belum pernah diisi.
6. **`is_locked` belum pernah `true`.** Fitur kunci bulan belum dipakai pada data uji.
7. **Riwayat capaian berhenti di Rabiul Akhir**, dan Hari Efektif juga berhenti di bulan itu. Bulan Jumadal Ula dan sesudahnya kosong (bukan 0).
8. **Hari Efektif Syawwal 1447 = 4 hari dan Rabiul Awwal = 3 hari** adalah **data SAH** (bulan pembuka tahun ajaran & bulan dengan libur ~2 pekan lebih). **Bukan kesalahan**, jangan diubah tanpa konfirmasi Mudir (lihat `AGENTS.md`). Hanya 7 baris `month_domain_settings` (bulan 1–7); bulan 8–12 dan Wasilah/Ghayah belum ada (layar T8).
9. ~~**7 baris `attendance` Ramadhan tanpa capaian** dan **nilai Shafar berbeda dari seed**~~ **SELESAI 25 Nov 2026 (keputusan Mudir, T6d3):** keduanya dipulihkan/dihapus lewat skrip terdokumentasi di `scripts/db/fixes/`; lihat `docs/STATUS.md` 2l. Penyebab Ramadhan: seed dijalankan ulang. Penyebab Shafar: perubahan manual di luar repo sebelum T6d2 (tidak ada jejak, tidak dapat dibuktikan lebih jauh).
10. **Kolom H (Hadir) di Excel tidak selalu = HE - (S+I+A).** 10 sel berbeda, semuanya bulan Muharram (mis. HE 19, H 7, S+I+A 1). Aplikasi memang **mengabaikan kolom H** dan menghitung Hadir sendiri (keputusan yang sudah ada), jadi bukan galat aplikasi; dicatat oleh uji penuh `compare_alquran_full_excel.py`.
11. **`students_without_halaqah` mengembalikan semua domain** hanya untuk koneksi admin tanpa JWT (skrip lokal `postgres`, PostgREST `service_role`). Pengguna aplikasi ber-JWT selalu lewat `can_manage(domain)`. Diuji `scripts/qa/test_students_without_halaqah_p6.py`.

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

## 8. Notifikasi "santri belum punya halaqah" (24 November 2026, langkah pra-T6 [4/5])

Kebutuhan Mudir: santri yang belum punya halaqah di satu domain dikabarkan ke pengampu domain itu
(Masul Al Quran / Masul Wasilah / Masul Ghayah); Admin dan Mudir menerima dari ketiga domain;
Musyrif/ah dan Mudarris/ah tidak.

Hasil hitung langsung di database dummy (tahun ajaran aktif 1447, 109 santri aktif):

| Domain | Tanpa halaqah | Santri |
|---|---|---|
| Al Qur'an | **0** | – |
| Ilmu Wasilah | **1** | `1447.dummy-nis.024` (hanya Al Qur'an) |
| Ilmu Ghayah | **2** | `1447.dummy-nis.023` (belum di Ghayah), `1447.dummy-nis.024` |

Jumlah ini sesuai kebutuhan minimal (023 tidak di Ghayah; 024 tidak di Wasilah dan Ghayah), jauh di bawah
ambang 30%, dan tidak memerlukan keputusan tambahan Mudir.

Perilaku yang diverifikasi (uji 13/13 PASS, semua uji tulis di-ROLLBACK):
- Mudir dan Admin melihat ketiga domain.
- Masul Al Quran hanya Al Qur'an; Masul Wasilah hanya Wasilah; Masul Ghayah hanya Ghayah.
- Musyrif/ah dan Mudarris/ah tidak melihat apa pun (0 baris).
- Setelah santri diberi halaqah (023 ke Ghayah), santri itu hilang otomatis dari notifikasi; ROLLBACK mengembalikan data.
- anon ditolak.

Catatan implementasi: memakai dua fungsi `security definer` (`students_without_halaqah()` dan
`students_without_halaqah_count()`), bukan tabel atau view baru; `revoke ... from public, anon`. Karena
`security definer`, `current_user` di dalam fungsi selalu = pemilik, jadi pengecualian "tampil semua untuk
skrip lokal" memakai `session_user` yang digabung `current_app_role() is null`. Aturan detail di
`docs/SPEC.md` bagian 9.
