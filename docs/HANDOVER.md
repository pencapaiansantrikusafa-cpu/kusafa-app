# HANDOVER - serah terima untuk sesi berikutnya

**Terakhir diperbarui**: 25 November 2026, tahap T6a selesai (tabel Wasilah & Ghayah).
Baca berurutan: `AGENTS.md` → `docs/SPEC.md` → `docs/STATUS.md` → berkas ini.
`docs/STATUS.md` adalah sumber kebenaran kondisi nyata; berkas ini menjelaskan **apa yang harus dikerjakan berikutnya**.
Jangan menulis rahasia (kata sandi, kunci, token, `DATABASE_URL`, kunci service role) atau data santri asli di berkas ini.

---

## 1. Status per tahap

| Tahap | Nama | Status | Berkas yang dibuat / diubah |
|---|---|---|---|
| A-G | Persiapan: alat, proyek, Git, Supabase, seed, uji lokal, Vercel | **SELESAI** | `README.md`, `.env.example`, `supabase/config.toml`, `vercel.json`, skrip A-G |
| T0 | Orientasi & pemetaan data Excel | **SELESAI** | `docs/DATA-NOTES.md`, `data/source/` (5 Excel, tidak di-commit) |
| T1 | Database & seed | **SELESAI** | migrasi `000001–000006`, `scripts/seed/build_seed.py`, `scripts/db/run_sql.py` |
| T2 | Login, kerangka, menu per role | **SELESAI** | `LoginPage.tsx`, `AuthProvider.tsx`, `AppLayout.tsx`, `NavLinks.tsx`, `src/lib/roles.ts` |
| T3 | Tabel capaian halaqah Al Qur'an | **SELESAI** | `CapaianPage.tsx`, `TabelCapaian.tsx`, `TabelAlQuran.tsx`, `src/lib/laporan.ts` |
| T4 | Halaman satu santri | **SELESAI** | `SantriPage.tsx`, `GrafikGaris.tsx`, `GrafikGabungan.tsx` |
| T5 | Input capaian Al Qur'an (+ T5b) | **SELESAI** | `InputPage.tsx`, `FormInputAlQuran.tsx`, `src/lib/putaran.ts`/`posisi.ts`, `KonfirmasiPutaran.tsx`, `KotakBelumLengkap.tsx`, `tests/putaran.test.mjs` |
| Pra-T6 | Audit & perbaikan data (langkah [1]-[5]) | **SELESAI** | migrasi `000007`–`000009`, `scripts/qa/*`, `scripts/db/fixes/*`, `tests/audit-rules.test.mjs`, `docs/qa/*` |
| Pra-T6 [6] | Jawaban Mudir + verifikasi & penutupan celah | **SELESAI** | migrasi `000010`, `scripts/qa/test_auth_signup_closed.py`, `regression_execute.py`, `smoke_e2e.py`, `test_students_without_halaqah_p6.py`, `test_data_awal_tahun_kedua.py`, `docs/SPEC.md` 4a-1 |
| T5c | Percepat halaman Input (pencarian item di server) | **SELESAI** (STATUS 2e) | migrasi `000011`, `InputPage.tsx`, `DropdownCari.tsx` (`diServer`), `KotakBelumLengkap.tsx` |
| T5c-2 | Satu permintaan per tahap (boot + isi form) | **SELESAI** — 0,97 s median produksi (STATUS 2f) | migrasi `000012`, `InputPage.tsx` |
| T5c-3 | Perbaikan bug label dropdown Input ("— belum diisi —") | **SELESAI** — E2E 9/9, data utuh (STATUS 2g) | `DropdownCari.tsx`, `FormInputAlQuran.tsx`, `InputPage.tsx` |
| T6a | Tabel capaian Wasilah & Ghayah | **SELESAI** (STATUS 2h) | `TabelWasilah.tsx`, `TabelCapaian.tsx`, `test_t6a_tabel.py` 14/14 |
| T6b | Input Wasilah & Ghayah | **SELESAI** (STATUS 2i) | migrasi `000013`-`000016`, `InputWasilahPage.tsx`, `test_t6b_*` 29/29 & 14/14 |
| T6d2 | Seragamkan hak input Masul + jejak pengisi | **SELESAI** (STATUS 2k) | migrasi `000017`-`000018`, `roles.ts` (`bolehInputDomain`), `test_t6d2_*` 68/68 & 14/14, matriks RLS 67/75 |
| T6e | Hapus capaian + log perubahan | **SELESAI** (STATUS 2m) | migrasi `000019`-`000020`, `hapus_capaian*`, `change_log`, `DialogHapusCapaian.tsx`, `test_t6e_*` 35/35, 16/16, 15/15, 12/12 |
| T6d3 | Pembersihan data + disiplin uji | **SELESAI** (STATUS 2l) | 3 skrip fix (`hapus_kehadiran_ramadhan`, `pulihkan_shafar`, `pulihkan_capaian_024`, `pulihkan_data_seed.py`), `db_fingerprint.py`, `pulihkan_data.py`, `compare_alquran_full_excel.py`, `test_seed_bersih.py` |
| T6c | "Bulan lalu" tampil sejak awal | **SELESAI** | `FormInputAlQuran.tsx`; E2E 10/10 |
| T6d | Tab domain di halaman Capaian (seperti Input) | **SELESAI** (STATUS 2j) | `TabDomain.tsx`, `CapaianPage.tsx`; E2E 28/28 lokal & produksi |
| T7 | Target dinamis (ajukan/setujui) | **BELUM** | - |
| T8 | Kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | **BELUM** | - |
| T9 | Pengujian & QA penuh | **SEBAGIAN** | `scripts/qa/rls_matrix.py`, `test_no_halaqah.py`, `test_students_without_halaqah.py`, `run_pre_t6_db_tests.py` (sudah ada, belum lengkap) |
| T10 | Deploy akhir (hapus dummy, repo privat) | **BELUM** | - |

Pra-T6 rinci:
- **[1]** hardening fungsi → migrasi `20261121000007_harden_function_grants.sql`; `run_pre_t6_db_tests.py`.
- **[2]** keputusan bulan 0 & santri tanpa halaqah → `docs/SPEC.md` 4a/9; `test_no_halaqah.py`.
- **[3]** Hari Efektif Rabiul Awwal: nilai **3 hari adalah BENAR** (libur ~2 pekan lebih). Perubahan 3→19 pada 24 Nov 2026 **dibatalkan**; dipulihkan ke 3 lewat `scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql`. Skrip lama hanya jejak riwayat.
- **[4]** notifikasi "santri belum punya halaqah" → migrasi `20261121000009_students_without_halaqah.sql`, `KotakBelumLengkap.tsx`, `test_students_without_halaqah.py`.
- **[5]** audit + docs → `scripts/qa/rls_matrix.py`, `tests/audit-rules.test.mjs`, `check_repo_safety.py` (diperkuat), `README.md`, `CHANGELOG.md`, `FILE-MAP.md`, `STATUS.md`.

---

## 2. Tahap yang sedang dikerjakan

**T6a, T6b, T6c, T6d SELESAI** (25 Nov 2026) — tabel Wasilah/Ghayah, input Wasilah/Ghayah,
perbaikan "Bulan lalu", dan tab domain (Al Qur'an / Ilmu Wasilah / Ilmu Ghayah) di halaman Capaian
yang berbagi komponen dengan halaman Input. Rincian: `docs/STATUS.md` 2h (tabel), 2i (input), 2g (dropdown).
**Tahap berikutnya: T7** (target dinamis) — belum boleh dimulai tanpa aba-aba Mudir.

**Sebelumnya: T5c, T5c-2, dan perbaikan T5c-3 SELESAI** (24–25 Nov 2026) — rincian dan angka di `docs/STATUS.md` bagian 2e (T5c), 2f (T5c-2), dan 2g (bug label dropdown). Tidak ada pekerjaan yang berjalan di tengah; semua sudah di-commit dan di-push. Sebelumnya **Pra-T6 [6]** dan **[6a]** selesai (STATUS 2d, DATA-NOTES 3a).

**Yang sudah jalan** — lihat `docs/STATUS.md`: login/menu per role, tabel & input Al Qur'an, halaman santri,
notifikasi "data belum lengkap" dan "santri belum punya halaqah", deploy Vercel tersambung Supabase.

**Yang belum jalan** — T6 s.d. T10 (daftar di `prompts/OPENCODE.md` & `docs/CATATAN-TAHAPAN.md`).

**Bug/error yang diketahui:**
- Tidak ada galat build / `tsc` / uji. Yang tertulis di `docs/STATUS.md` bagian 6 semuanya keterbatasan, bukan galat menggantung.
- ~~Kinerja muat item Al Qur'an lambat~~ — **SELESAI di T5c**: item tidak lagi diunduh penuh; pencarian di server. Sisa ±1,4 s karena penundaan jaringan (`STATUS.md` 2e), lalu dipercepat lagi di T5c-2.
- ~~Dropdown Input menulis "— belum diisi —" setelah memilih item~~ — **SELESAI T5c-3 (25 Nov 2026)**: label pilihan disimpan beserta objeknya; uji E2E `scripts/qa/test_input_dropdown_e2e.py` memeriksa tampilan, simpan, dan muat ulang (`STATUS.md` 2g).
- `npm audit` sisa 2: `vite`/`esbuild` (hanya dev server, tidak ikut bundel produksi).

**Langkah berikutnya (berurutan) — keputusan Mudir 24 November 2026:**
1. ~~Merge react-router 7~~ — **SELESAI** (smoke 29/29 lulus di branch, lalu merge & push).
1a. ~~T5c-3 — perbaikan bug label dropdown Input~~ **SELESAI 25 Nov 2026**: item terpilih tidak lagi jatuh ke "— belum diisi —"; uji E2E 9/9, data 2.036 baris utuh (`STATUS.md` 2g).
1b. ~~T5c-2 — satu permintaan per tahap~~ **SELESAI 25 Nov 2026**: RPC `input_alquran_boot` + `input_alquran_data`; halaman siap **1,4–2,0 s → 0,97 s median produksi** (target <1 detik tercapai pada kondisi jaringan normal; lihat STATUS 2f).
2. ~~T5c — percepat input~~ **SELESAI 24 Nov 2026**: RPC `curriculum_items_search`/`_by_ids`, halaman siap 3,0–4,0 s → **1,4–2,0 s**, permintaan item 128 → 2. **Target <1 detik belum tercapai** karena penundaan jaringan ke database (±20 permintaan berurutan); lihat `STATUS.md` 2e.
3. **T6** — tabel & input Wasilah & Ghayah (ganti tulisan "dikerjakan pada T6" di `TabelCapaian.tsx`; input sekali per halaqah × mata pelajaran disalin ke anggota; `hanyaHalaqahDiampu()`).
4. **T7** — target dinamis (ajukan/setujui); target bulanan = target harian × Hadir, dihitung database.
5. **T8** — Hari Efektif & kunci bulan, penugasan halaqah, kelola kurikulum, tambah tahun (ingat: tahun kedua tanpa Data Awal, SPEC 4a-1).
6. **T9** — jadikan uji RLS manual jadi tetap; uji HP; lengkapi sel SKIP matriks RLS; **pasang ESLint** (ditunda ke sini).
7. **T10** — hapus data dummy, jadikan repo privat, putar/bersihkan sekret.

---

## 3. Keputusan yang sudah final (jangan diubah tanpa persetujuan Mudir)

Aturan bisnis lengkap: `docs/SPEC.md`. Ringkas:
- Hadir = Hari Efektif − (izin+sakit+alpha), dihitung database, bukan React.
- Bulan 0 (Data Awal) = catatan awal, **bukan** bulan efektif/target dan **bukan** bulan input staf; `month_is_open(0,*)=false`. Santri lama memakai Ramadhan tahun lalu sebagai pembanding Syawwal.
- Hari Efektif Rabiul Awwal (Al Qur'an) = **3** dan itu **BENAR** (libur ~2 pekan lebih). Tidak ada yang perlu diperbaiki di Excel. Nilai 19 adalah kekeliruan yang sudah dikembalikan. Hadir bulan itu 1–3.
- Selisih **boleh negatif** (pengulangan); putaran naik **hanya** lewat pilihan eksplisit "khatam" (putaran = bulan lalu + 1).
- Bulan belum diinput **kosong**, bukan 0. Item kurikulum terpakai **tidak dihapus**, hanya `is_active=false`.
- Santri yang tidak ikut semua halaqah adalah keadaan **sah** (NIS 023/024 = kasus uji resmi); di domain yang tidak diikuti santri **tidak ditampilkan**, bukan tampil 0.
- Notifikasi "santri belum punya halaqah": Mudir/Admin semua domain; Masul Al Quran/Wasilah/Ghayah hanya domainnya; Musyrif/Mudarris tidak; anon ditolak.
- Role ditulis lengkap: **Masul Al Quran / Masul Wasilah / Masul Ghayah**.
- Nama bidang: Tilawah, Tahfidz, Kitabah, Baca, Tulis, Sirah, **Hisab**, Adab dan Iman, Aqidah dan Fiqih.

### 3a. Keputusan Mudir 24 November 2026 (pra-T6 [6]) — sudah final

- **Urutan kerja:** pra-T6 [6] → **merge react-router** (bila smoke lulus) → **T5c percepat input** → **T6**. T5c sudah selesai; **T6 menunggu aba-aba Mudir**.
- **react-router 7:** boleh di-merge ke `main` **hanya bila smoke E2E semua role lulus** di branch itu. **Sudah dipenuhi** → di-merge (7.18.6).
- **ESLint:** ditunda, dipasang di **T9**.
- **Excel Rabiul Awwal:** **tidak perlu diubah.** `BZ5:BZ113` = 3 adalah nilai benar (libur ~2 pekan lebih).
- **Signup publik:** sudah dimatikan Mudir. **Catatan teknis:** yang benar adalah `disable_signup = true` dengan provider email **tetap aktif**. Mematikan provider email (`external.email=false`) **ikut mematikan login**; jangan diulang. Keadaan sekarang: `disable_signup=true`, provider email aktif, signup ditolak `422 signup_disabled`, login 7 role lulus.
- **Repo tetap PUBLIK sampai T10**; wajib privat sebelum data asli dimuat.
- **Bulan 0 (Data Awal):** hanya **Admin dan Mudir** yang mengisi, dan **hanya di tahun pertama**. Mulai tahun ajaran kedua Data Awal **tidak diisi manual** — diambil otomatis dari **capaian bulan terakhir (Ramadhan) tahun sebelumnya**, juga untuk santri tahun pertama yang naik ke tahun kedua. `create_academic_year` untuk tahun kedua **tidak boleh** meminta/membuat Data Awal. Rincian + bukti uji: `docs/SPEC.md` bagian 4a-1, `scripts/qa/test_data_awal_tahun_kedua.py`.
- **Jalur "tampil semua" di `students_without_halaqah` dipertahankan**: hanya berlaku untuk koneksi admin tanpa JWT (skrip lokal/service_role), tidak untuk pengguna aplikasi. Sudah diuji: authenticated tanpa profil, musyrif, mudarris → 0 baris; anon ditolak.

### 3b. Koreksi data Hari Efektif — 24 November 2026 (menimpa instruksi sebelumnya)

- **Hari Efektif Rabiul Awwal (bulan 6, Al Qur'an) = 3 hari adalah BENAR** karena ada **libur sekitar dua pekan lebih**. Perubahan 3 → 19 tanggal 24 Nov 2026 adalah **kekeliruan** dan **sudah dikembalikan ke 3**.
- Pemulihan: `scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql`. Skrip lama `2026-11-24_rabiul_awwal_effective_days.sql` **DIBATALKAN** (diberi penghenti keras, disimpan sebagai riwayat).
- Bukti: `scripts/qa/compare_rabiul_awwal_excel.py` **7/7 PASS** (HE, Hadir, izin/sakit/alpha, label+posisi capaian cocok dengan Excel untuk **109 santri**; sampel 15 dirinci). Snapshot `attendance`, `progress_entries`, `targets`, `curriculum_items`, `books`, `students` **identik** sebelum/sesudah pemulihan.
- **Nilai Hari Efektif kecil (mis. Syawwal 4, Rabiul Awwal 3) adalah sah** — jangan ditandai kesalahan dan jangan diubah tanpa konfirmasi Mudir (`AGENTS.md`, `SPEC.md` 4a-2).
- Excel sumber **tidak perlu diubah**; `BZ5:BZ113` = 3 memang benar.

### 3d. Keputusan Mudir 25 November 2026 (T6b) — sudah final

> **DIGANTIKAN oleh Keputusan final 3f (T6d2, 25 November 2026).** Isi di bawah dipertahankan sebagai
> riwayat; yang berlaku sekarang adalah 3f.

- **Masul Wasilah dan Masul Ghayah adalah penanggung jawab domain**, bukan hanya pengampu mata pelajaran. Mereka **boleh menulis capaian semua halaqah di domainnya** walau tidak tercatat di `halaqah_teachers`.
  - Ditegakkan oleh `wasilah_can_write` dan policy `progress_insert_masul_domain` / `progress_update_masul_domain`.
  - Policy itu **khusus `wasilah` dan `ghayah`**. **Masul Al Quran TIDAK ikut berubah** (tetap "halaqah yang diampu"); menyamakannya harus diputuskan Mudir terpisah.
  - Masul tetap **tidak boleh** menulis di domain lain dan **tetap ditolak pada bulan terkunci**.
  - Alasan: pada data dummy, Masul Wasilah dan Masul Ghayah tidak tercatat sebagai pengampu mana pun, sehingga tanpa keputusan ini mereka tidak bisa menginput sama sekali.
- **Data uji E2E boleh menulis** asalkan dipulihkan otomatis dan jumlah baris diverifikasi (dipakai di `test_t6b_e2e.py`: 2.039 → 2.039).
- **Catatan:** 3 baris `progress_entries` bulan Jumadal Ula (25 Nov 2026, `entered_by = Admin`) **bukan** dari pekerjaan T6 — sudah ada sebelum T6 dimulai (2.036 → 2.039) dan **tidak disentuh**. Perlu dikonfirmasi Mudir bila itu percobaan.

### 3c. Keputusan Mudir 25 November 2026 (T6) — sudah final

- **Aba-aba T6:** boleh dimulai, dipecah **T6a (tabel)** lalu **T6b (input)**; satu sub-tugas satu commit.
- **Hari Efektif Syawwal 1447 = 4 hari adalah BENAR.** Bulan pembuka tahun ajaran: libur memotong setengah Ramadhan dan setengah Syawwal. Nilai kecil itu **sah**; jangan ditandai janggal, jangan dinaikkan. **Ramadhan kemungkinan juga pendek** — jangan "dilengkapi" tanpa data Mudir.
- **Hari Efektif Wasilah & Ghayah = DUMMY (izin khusus, hanya untuk Hari Efektif dan kehadiran).**
  - Urutan yang diperintahkan: (1) turunkan dari Excel Wasilah/Ghayah bila ada kolom HE, atau HE = Hadir + izin + sakit + alpha; (2) jika tidak ada, **samakan dengan nilai Al Qur'an per bulan**.
  - **Hasil pemeriksaan:** `data/source/4-Ilmu Wasilah.xlsx` dan `5-Ilmu Ghayah.xlsx` **tidak punya** kolom HE/Hadir/izin/sakit/alpha. Maka dipakai aturan (2).
  - Cakupan: **bulan 1–7 saja** (sama dengan Al Qur'an). Bulan 8–12 tetap kosong untuk semua domain sampai T8.
  - Skrip: `scripts/db/fixes/2026-11-25_he_wasilah_ghayah_dummy.sql` (aman dijalankan ulang, **tidak menimpa** nilai yang sudah ada).
  - **Kehadiran 0/0/0**: Mudir memilih membuat baris `attendance` izin/sakit/alpha = 0 untuk semua anggota × bulan 1–7, karena tanpa baris kehadiran Hadir tetap kosong. Konsekuensi yang dicatat: sementara ini **semua santri tercatat hadir penuh** di Wasilah/Ghayah.
  - Ditandai **DUMMY** di `docs/DATA-NOTES.md` butir 3 dan `docs/STATUS.md` 2h. **Wajib diganti data asli lewat T8/T10.**
  - Izin ini **hanya** untuk Hari Efektif (dan baris kehadiran nol yang mengikutinya). Data lain yang kurang **harus ditanyakan** lebih dulu, tidak boleh dikarang (tidak ada capaian, target, atau catatan karangan).
- **Data uji E2E boleh menulis**, dengan syarat dipulihkan otomatis dan jumlah baris diverifikasi kembali (pola uji T5c-3).
- **Keanggotaan 023/024 tetap kasus uji resmi** (023 tidak di Ghayah; 024 hanya Al Qur'an): di domain yang tidak diikuti santri **tidak ditampilkan**.

### 3e. Keputusan Mudir 25 November 2026 (T6d) — sudah final

- **Halaman Capaian memakai TAB domain** (Al Qur'an / Ilmu Wasilah / Ilmu Ghayah) di bagian atas, sama seperti halaman Input, di HP maupun desktop. Satu komponen bersama `TabDomain`; tab aktif tercermin di URL sehingga muat ulang dan tombol kembali bekerja.
- **Submenu Capaian di menu samping/bilah bawah dihapus** — sudah digantikan tab.
- **Hak akses tidak berubah:** ketiga domain tetap dapat dilihat semua staf; yang tidak berhak (wali, non-staf) tetap tidak membuka halaman Capaian sama sekali. Bila kelak Capaian dibatasi per domain, harus diputuskan Mudir dan diubah bersama RLS.

### 3f. Keputusan Mudir 25 November 2026 (T6d2) — sudah final, MENGGANTIKAN 3d

- **Hak input ketiga Masul diseragamkan.** Masul Al Quran, Masul Wasilah, dan Masul Ghayah boleh
  **input capaian, catatan, dan kehadiran di SEMUA halaqah domainnya** (Al Qur'an / Ilmu Wasilah /
  Ilmu Ghayah), walau tidak tercatat di `halaqah_teachers`. Masul = **penanggung jawab domain**.
- **Cakupan mengikuti satu baris tabel SPEC bagian 3:** capaian + catatan + kehadiran.
- **Tetap ditolak untuk Masul:** domain lain, **bulan terkunci**, **bulan 0 (Data Awal)**, dan
  **menghapus** (hapus tetap hanya Mudir/Admin).
- **Pengampu (Musyrif/ah, Mudarris/ah) tidak berubah:** tetap **hanya halaqah yang diampu**.
- **Rumus Hadir dan view tidak berubah.**
- **Jejak pengisi wajib tercatat** untuk capaian, catatan, dan kehadiran: `entered_by`/`entered_at`
  = pengisi terakhir, `updated_by`/`updated_at` = pengubah terakhir. Kolom `updated_by`/`updated_at`
  ditambahkan lewat migrasi `20261125000017_masul_input_domain.sql`; trigger `catat_jejak` mengisi
  keduanya. Pada koneksi tanpa JWT (seed/skrip) trigger **tidak menyentuh** baris yang sudah ada
  (migrasi `20261125000018_catat_jejak_tanpa_jwt.sql`).
- **Sanksi teknis:** policy `progress_insert`/`progress_update`, `attendance_insert`/`attendance_update`,
  `notes_insert`/`notes_update` memakai aturan yang sama untuk ketiga domain; `is_masul_of(domain)`
  memastikan domain lain tetap ditolak dan `month_is_open` memastikan bulan terkunci/bulan 0 ditolak.
- **Uji:** `test_t6d2_masul_input.py` 68/68, `test_t6d2_e2e_masul.py` 14/14, matriks RLS 67 OK / 8 SKIP
  / 0 GAGAL, seluruh uji lama hijau (rincian di STATUS 2k).

### 3h. Keputusan Mudir 25 November 2026 (T6e) - sudah final

- **Hapus capaian:** hanya **Mudir dan Admin**. Masul (ketiga) dan pengampu tetap **tidak** boleh
  menghapus (hanya input/menimpa). Hapus = menghapus baris `progress_entries`; rumus/view tidak berubah.
- **Cakupan:** (1) satu capaian satu santri; (2) massal satu halaqah x mata pelajaran x bulan
  (hasil input massal), dengan **jumlah santri terdampak** ditampilkan sebelum konfirmasi.
- **Bulan terkunci:** Mudir/Admin boleh, dengan **konfirmasi eksplisit** (centang di dialog).
- **Bulan sesudahnya terisi / putaran:** ditolak dengan pesan jelas (sarankan hapus dari bulan terakhir)
  kecuali dikonfirmasi eksplisit; capaian "khatam, mulai putaran baru" diberi peringatan.
- **Bulan 0:** tidak bisa dihapus lewat fitur ini (bukan bulan input staf).
- **Log perubahan:** satu tabel `change_log` mencatat UPDATE + DELETE pada `progress_entries`,
  `attendance`, `monthly_notes` (nilai lama + baru, aktor, peran, waktu, sumber). Tanpa JWT tercatat
  `skrip:<user>`. Log hanya bisa dibaca Mudir/Admin; tidak bisa diubah/dihapus dari aplikasi; anon tidak.
  UPDATE tanpa perubahan nilai **tidak** dicatat (supaya log tidak penuh baris palsu).
- **Data uji Mudir:** 3 baris capaian Jumadal Ula dihapus **lewat fitur** (uji penerimaan, tercatat di
  log); 7 baris kehadiran Jumadal Ula terbukti percobaan (0/0/0, `entered_by = Admin`, detik yang sama)
  dan dihapus lewat `scripts/db/fixes/2026-11-25_hapus_kehadiran_jumadal_ula.sql`.
- **Langkah 0 (wajib sebelum fitur):** E2E Simpan lewat UI untuk **Mudarris/ah**, **Musyrif/ah**, dan
  halaqah **Level 6** — 12/12 lulus, data dipulihkan persis.

### 3g. Keputusan Mudir 25 November 2026 (T6d3) - sudah final

- **7 baris kehadiran Ramadhan tanpa capaian: HAPUS lagi** (sesuai persetujuan 23 Nov). Penyebab
  kebangkitan: seed dijalankan ulang 24 Nov; penghapusan lama tidak pernah jadi skrip. Sekarang ada
  `scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql` + uji penjaga `test_seed_bersih.py`.
- **Nilai izin/sakit/alpha Shafar: IKUTI seed/Excel.** Dipulihkan lewat 37 baris yang berbeda
  (`scripts/db/fixes/2026-11-25_pulihkan_shafar.sql`), bukan seed penuh. Penyebab perbedaan tidak
  dapat dibuktikan (perubahan manual di luar repo sebelum T6d2; tidak ada jejak); dilaporkan.
- **Rekonsiliasi 2.039 vs 2.038:** selisih = 1 baris `1443.dummy-nis.024` Kitabah Dzul Qa'dah
  "Menyalin - 25", hilang dalam sesi T6d2. Dipulihkan dengan nilai seed asli
  (`scripts/db/fixes/2026-11-25_pulihkan_capaian_024.sql`). Total capaian kembali **2.039**.
- **Uji banding Excel penuh** (`compare_alquran_full_excel.py`, 7/7) menggantikan sampel.
- **Disiplin sidik jari** wajib: `scripts/qa/db_fingerprint.py` sebelum/sesudah setiap uji yang
  menulis; hasil wajib SAMA. **Smoke produksi hanya membaca** (sejak T6d3).
- **Catatan terbuka:** 3 baris `progress_entries` + 7 baris `attendance` bulan Jumadal Ula
  (`entered_by = Admin`, 25 Nov 02:14-02:16 UTC) adalah percobaan Mudir, **tidak disentuh**.
  Konfirmasi apakah boleh dihapus sebelum data asli (T8/T10).

Struktur teknis (SPES & STATUS): `hijri_months` 13 baris, tahun di `academic_years`; semua dropdown `DropdownCari` (panel layang `z-60`); tahun & bulan dua dropdown terpisah; label item ber-awalan nama bidang; daftar panjang wajib `ambilSemua`; frontend hanya `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`; migrasi lama **tidak diubah** (berikutnya `20261121000010_...`).

---

## 4. Status Supabase

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1`.
Kredensial hanya di `.env.local` (**tidak dicetak/commit**). `DATABASE_URL` adalah koneksi Postgres Supabase yang dipakai skrip lokal (`scripts/db/run_sql.py`, seed, uji QA); tipe spesifik (pooler langsung vs transaction-pooler) periksa di Dashboard supaya tidak keliru dipakai dari luar.

- **Migrasi dijalankan (20)**: `000001`–`000009`, `20261124000010_attendance_guard_revoke`, `20261124000011_curriculum_search`, `20261124000012_input_alquran_data` (T5c-2), `20261125000013_wasilah_input`, `20261125000014_wasilah_input_hadir`, `20261125000015_masul_domain_write`, `20261125000016_masul_domain_scope_fix` (T6b), `20261125000017_masul_input_domain` + `20261125000018_catat_jejak_tanpa_jwt` (T6d2), `20261125000019_hapus_capaian_log` + `20261125000020_log_abaikan_update_kosong` (T6e).
- **Auth**: `disable_signup = true`, provider email **aktif** (`external.email=true`), `mailer_autoconfirm=false`. Signup ditolak `422 signup_disabled`; login 7 role lulus (24 Nov 2026). Diubah lewat Management API (`PATCH /v1/projects/<ref>/config/auth`).
- **RLS**: 18 tabel `relrowsecurity=true`; semua kebijakan bertarget role `authenticated`; fungsi di-hardening (cabut `EXECUTE` anon/PUBLIC, grant authenticated+service_role). Matriks RLS otomatis: **67 OK / 8 SKIP / 0 GAGAL** (T6d2; sebelumnya 38). T6e menambah satu tabel baru
  `change_log` (RLS aktif, hanya SELECT untuk `is_full_access()`) dan 4 RPC hapus capaian.
- **Fungsi trigger**: `attendance_guard_override()` kini **tanpa** EXECUTE untuk authenticated/anon/PUBLIC; trigger tetap berjalan (SECURITY DEFINER).
- **Seed**: data dummy 1447 dimuat; destruktif, jangan ulang tanpa izin Mudir. `month_domain_settings` hanya Al Qur'an bulan 1-7 (Rabiul Awwal=3 karena libur, Syawwal=4); `is_locked` semua `false`.
- **Ekstensi**: `pg_trgm` dipasang di skema **`extensions`** (bukan `public`) untuk indeks pencarian label.
- **Fungsi/view**: 28 fungsi public; 4 view (`v_monthly_report`, `_base`, `v_attendance`, `v_months_ordered`).

---

## 5. Pertanyaan terbuka (menunggu jawaban / data Mudir)

- ~~Boleh mulai T6?~~ — **URUTAN SUDAH TERPENUHI:** [6] ✓, merge react-router ✓, T5c ✓. T6 boleh dimulai setelah Mudir memberi aba-aba.
- ~~Signup publik aktif?~~ — **TERJAWAB & DITUTUP:** `disable_signup=true`, provider email tetap aktif, login jalan.
- ~~Naik react-router ke 7.x?~~ — **TERJAWAB & SELESAI:** di-merge setelah smoke 29/29 lulus.
- ~~Pasang ESLint?~~ — **TERJAWAB:** ditunda ke T9.
- ~~Excel Rabiul Awwal masih 3?~~ — **BUKAN MASALAH:** 3 adalah nilai benar (libur ~2 pekan lebih). Nilai 19 dibatalkan dan dipulihkan ke 3.
- ~~Data Awal tahun kedua?~~ — **TERJAWAB:** otomatis dari Ramadhan tahun sebelumnya (HANDOVER 3a, SPEC 4a-1).

Masih terbuka:

1. **Repo masih PUBLIK** sampai T10. Wajib privat sebelum data asli dimuat (`gh repo edit --visibility private`).
2. ~~**Hari Efektif Syawwal 1447 = 4 hari**~~ — **TERJAWAB (Mudir, 25 Nov 2026):** **BENAR**. Bulan pembuka tahun ajaran; libur memotong setengah Ramadhan dan setengah Syawwal. Nilai kecil itu sah dan tidak boleh ditandai janggal. Ramadhan kemungkinan juga pendek (lihat Keputusan final 3b).
3. **Data Awal (252 capaian)** dipertahankan; dikosongkan saat data asli? Keputusan T10.
4. **69 capaian dummy mundur** — disepakati dibiarkan; konfirmasi ulang sebelum T9.
5. **Level 6 (4 santri)** belum punya pengampu/jadwal — apa yang ditampilkan (T8).
6. ~~**Hari Efektif hanya ada untuk Al Qur'an bulan 1–7**~~ — **SEBAGIAN TERJAWAB (Mudir, 25 Nov 2026):** Wasilah dan Ghayah kini punya Hari Efektif **DUMMY** bulan 1-7 (izin khusus, disamakan dengan Al Qur'an) + kehadiran 0/0/0. Bulan 8-12 **masih belum** punya untuk domain mana pun; layar pengisiannya T8. Lihat Keputusan final 3c dan DATA-NOTES butir 3.
7. **Matriks RLS: 8 sel SKIP** — butuh profil wali dan contoh target berstatus `diajukan` (T9).

---

## 6. Cara menjalankan, menguji, dan deploy

```bash
npm install
npm run dev            # http://localhost:5173 (atau port berikutnya)
npm run typecheck      # wajib hijau
npm run test           # 14 uji: putaran + audit-rules
npm run build          # wajib berhasil, hasil di dist/
python scripts/check_repo_safety.py   # wajib lolos sebelum push
git config core.hooksPath .githooks   # sekali saja (hook pre-commit keamanan)
```

### Uji QA pra-T6 [6] (semua membaca `.env.local`, tidak mencetak rahasia)

```bash
python scripts/qa/test_auth_signup_closed.py          # 9/9: signup ditutup + login 7 role
python scripts/qa/regression_execute.py               # 7/7: anon tanpa EXECUTE + musyrif tak bisa ubah data
python scripts/qa/test_students_without_halaqah_p6.py # 6/7 (1 skip: tak ada profil wali)
python scripts/qa/test_data_awal_tahun_kedua.py       # 5/5: tahun kedua tanpa Data Awal
python scripts/qa/run_pre_t6_db_tests.py              # 16/16: RLS/trigger/Hari Efektif
```

Smoke E2E browser (Playwright, memakai Chrome terpasang; kata sandi dibaca dari `users.csv`, tidak dicetak):

```bash
python3 -m venv .venv-qa && .venv-qa/bin/pip install playwright "psycopg[binary]"
.venv-qa/bin/python scripts/qa/smoke_e2e.py                               # lokal, 29/29
BASE_URL=https://kusafa-app.vercel.app DATA_UJI=0 .venv-qa/bin/python scripts/qa/smoke_e2e.py  # produksi, 28/28
# opsi: ROLES=mudir,admin  HEADLESS=0 (lihat jendela)  DATA_UJI=0 (tanpa tulis)
```

Catatan: role Mudir pada smoke **menulis lalu menghapus** satu capaian; skrip hanya menghapus baris
`progress_entries` dengan `entered_at` ≥ waktu mulai uji, jadi data lama tidak tersentuh.

Data/database (membaca `DATABASE_URL` dari `.env.local`, tidak dicetak) & QA:
```bash
python scripts/db/run_sql.py --query "select count(*) from public.students"
python scripts/qa/run_pre_t6_db_tests.py
python scripts/qa/test_no_halaqah.py
python scripts/qa/test_students_without_halaqah.py
python scripts/qa/rls_matrix.py
npm run seed:build     # membangun supabase/seed/*.sql dari data/source/*.xlsx (DESTRUKTIF, hanya uji)
npm run seed:users
```
Deploy: `git push origin main` memicu deploy otomatis Vercel (project `kusafa-app`). Bisa manual: `npx vercel --prod`. Hosting bisa dipindah ke cPanel (`public/.htaccess` ikut). Environment Vercel hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`.

### Jebakan yang pernah menggigit
- Supabase membatasi 1.000 baris/permintaan → wajib `ambilSemua`.
- `selisih` lintas buku butuh `item_position` (posisi kumulatif), jangan jumlahkan value mentah saja.
- `set local role` berlaku per transaksi: setiap probe RLS harus satu transaksi sendiri (lihat `rls_matrix.py`).
- Disimpan di `.env.local`; jangan pernah commit/menulis kunci service role atau `DATABASE_URL`.