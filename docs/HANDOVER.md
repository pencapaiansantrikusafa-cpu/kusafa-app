# HANDOVER - serah terima untuk sesi berikutnya

**Terakhir diperbarui**: 26 November 2026, **T7 [1b/2] selesai** (fondasi database + RPC + uji; UI belum).
Baca berurutan: `AGENTS.md` → `docs/SPEC.md` → `docs/STATUS.md` → berkas ini.
`docs/STATUS.md` = sumber kebenaran kondisi nyata (angka, hasil uji, migrasi). Berkas ini =
posisi sekarang, keputusan final, pertanyaan terbuka, risiko, dan langkah berikutnya.
Jangan menulis rahasia (kata sandi, kunci, token, `DATABASE_URL`) atau data santri asli di sini.

---

## 1. Status per tahap

| Tahap | Nama | Status |
|---|---|---|
| A-G | Alat, proyek, Git, Supabase, seed, uji lokal, Vercel | **SELESAI** |
| T0 | Orientasi & pemetaan Excel | **SELESAI** (`docs/DATA-NOTES.md`) |
| T1 | Database & seed dummy | **SELESAI** (migrasi `000001`-`000009`, `scripts/seed/`) |
| T2 | Login, kerangka, menu per role | **SELESAI** |
| T3 | Tabel capaian halaqah Al Qur'an | **SELESAI** |
| T4 | Halaman satu santri | **SELESAI** |
| T5 | Input capaian Al Qur'an (+ T5b) | **SELESAI** |
| Pra-T6 [1-6] | Audit, hardening, data, notifikasi, verifikasi | **SELESAI** |
| T5c / T5c-2 / T5c-3 | Percepat Input (server search), satu permintaan, bug label dropdown | **SELESAI** |
| T6a | Tabel capaian Ilmu Wasilah & Ilmu Ghayah | **SELESAI** |
| T6b | Input Ilmu Wasilah & Ilmu Ghayah | **SELESAI** |
| T6c | "Bulan lalu" tampil sejak awal | **SELESAI** |
| T6d | **Tab domain di halaman Capaian** (Al Qur'an / Ilmu Wasilah / Ilmu Ghayah), submenu Capaian dihapus | **SELESAI** |
| T6d2 | Ketiga Masul boleh input di semua halaqah domainnya + jejak pengisi | **SELESAI** |
| T6d3 | Pembersihan data + disiplin uji (sidik jari, uji seed, banding Excel penuh) | **SELESAI** |
| T6e | **Hapus capaian (Mudir/Admin) + log perubahan (`change_log`)** | **SELESAI** |
| **T7** | **Target dinamis (ajukan/setujui)** | **SEBAGIAN: [1b/2] SELESAI; UI [2/2] belum** |
| T8 | Kelola kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | **BELUM** |
| T9 | Pengujian & QA penuh | **SEBAGIAN** (banyak uji otomatis sudah ada dan hijau) |
| T10 | Deploy akhir (hapus dummy, **repo privat**) | **BELUM** |

Ringkasan rincian tiap tahap: `docs/STATUS.md` bagian 1 dan 2a-2m. Riwayat perubahan: `docs/CHANGELOG.md`.

---

## 2. Posisi sekarang

- **Semua pekerjaan T6 (a, b, c, d, d2, d3, e) selesai**, di-commit, di-push, dan terverifikasi di produksi.
- **T7 [1b/2] selesai**: fondasi database target dinamis (migrasi `000021`-`000031`), RPC, penguncian
  tulis langsung, audit, target DUMMY Wasilah/Ghayah, dan uji `test_targets_t7.py` 34/34.
- **T7 [2/2] belum**: halaman `/target` masih `PlaceholderPage`; belum ada form/UI/E2E target.
- Git bersih dan sinkron `origin/main` setelah commit dokumentasi.
- Migrasi terakhir: **`20261126000031_targets_audit_semantics.sql`**. Migrasi berikutnya wajib
  bernomor **`20261126000032_...`** dan **tidak boleh** mengubah berkas migrasi lama.
- Produksi: `https://kusafa-app.vercel.app`, HTTP 200, smoke produksi **BELUM DIVERIFIKASI** ulang
  pada sesi ini (UI belum berubah).
- Data: capaian **2.036**, kehadiran **599 / 756 / 749**, catatan 0, log perubahan 96 baris (append-only),
  target **363** = 327 Al Qur'an + 25 DUMMY Wasilah + 11 DUMMY Ghayah.

---

## 3. Keputusan final (JANGAN diubah tanpa persetujuan Mudir)

### 3.1 Masul = penanggung jawab domain (T6d2, menggantikan keputusan T6b/3d lama)
- **Masul Al Quran, Masul Wasilah, Masul Ghayah boleh INPUT capaian + catatan + kehadiran di SEMUA
  halaqah domainnya**, walau tidak tercatat di `halaqah_teachers`.
- **Tetap ditolak:** domain lain, **bulan terkunci**, **bulan 0**, dan **menghapus**.
- **Pengampu (Musyrif/ah, Mudarris/ah) hanya halaqah yang diampu.**
- Ditegakkan policy seragam (`progress_*`, `attendance_*`, `notes_*`) + `is_masul_of`.
- **Jejak pengisi:** `entered_by`/`entered_at` = pengisi terakhir, `updated_by`/`updated_at` = pengubah
  terakhir (trigger `catat_jejak`; koneksi tanpa JWT tidak menyentuh baris lama).

### 3.2 Hapus capaian + log perubahan (T6e)
- **Hanya Mudir dan Admin** yang boleh menghapus capaian (Al Qur'an, Wasilah, Ghayah). Masul &
  pengampu tetap hanya input/menimpa. Diperiksa **di dalam RPC**, RLS tabel penjaga terakhir, anon tanpa
  `EXECUTE`.
- Hapus = menghapus baris `progress_entries`; **rumus/view/target tidak berubah**; tampilan kembali
  **“belum diisi”** (bukan 0).
- **Cakupan:** satu capaian satu santri; **massal** satu halaqah × mata pelajaran × bulan (dengan
  **jumlah santri terdampak** tampil sebelum konfirmasi).
- **Bulan terkunci:** boleh untuk Mudir/Admin dengan **konfirmasi eksplisit**.
- **Bulan sesudahnya terisi / khatam putaran baru:** RPC **menolak** dengan pesan jelas (sarankan
  hapus dari bulan terakhir) kecuali diberi konfirmasi eksplisit `p_setuju_lanjutan`.
- **Bulan 0 (Data Awal):** tidak bisa dihapus lewat fitur ini.
- **Log perubahan `public.change_log`:** mencatat **UPDATE + DELETE** pada `progress_entries`,
  `attendance`, `monthly_notes` (nilai lama + baru, aktor, peran, waktu, sumber). Tanpa JWT →
  `sumber = skrip:<user>`, `aktor = NULL`. **UPDATE tanpa perubahan nilai tidak dicatat.** Log hanya
  boleh dibaca Mudir/Admin; tidak bisa diubah/dihapus/ditulis dari aplikasi; anon tidak.
  Seed ulang (TRUNCATE) **tidak** tercatat di log → penjaga tetap uji seed + sidik jari.

### 3.3 Data Excel & Hari Efektif (keputusan tetap)
- **Hari Efektif Syawwal 1447 = 4 hari** dan **Rabiul Awwal = 3 hari** adalah **BENAR** (libur
  panjang). Jangan ditandai janggal, jangan dinaikkan, jangan diubah tanpa konfirmasi Mudir.
  Angka Excel adalah acuan.
- **Hari Efektif Wasilah & Ghayah bulan 1-7 = DUMMY** (disamakan dengan Al Qur'an bulan yang sama)
  + baris kehadiran 0/0/0, karena Excel Wasilah/Ghayah tidak punya kolom HE/H/S/I/A. Wajib diganti data
  asli di T8/T10.
- **Kolom H (Hadir) Excel diabaikan**; Hadir dihitung aplikasi dari HE − (izin + sakit + alpha).
- **Bulan 0 (Data Awal)** = catatan awal, bukan bulan input staf: tanpa Hari Efektif, tanpa target
  bulanan; tidak dihapus lewat fitur hapus capaian.
- **Data dummy terpelihara:** 7 baris kehadiran Ramadhan tanpa capaian **dihapus**; nilai Shafar
  dipulihkan sesuai seed/Excel; 1 baris seed yang hilang (024 Kitabah Dzul Qa'dah) dipulihkan.
- **Percobaan Mudir dihapus (T6e):** 3 capaian + 7 kehadiran bulan Jumadal Ula (0/0/0) dihapus atas
  perintah Mudir — capaian lewat fitur (tercatat di log), kehadiran lewat SQL terdokumentasi.

### 3.4 Disiplin data & uji (perintah Mudir, T6d3 — mengikat semua tahap)
- **Database lokal = produksi (satu Supabase).** Setiap uji yang MENULIS wajib memulihkan baris
  **PERSIS** dan **lolos sidik jari** (`scripts/qa/db_fingerprint.py --simpan` sebelum,
  `--banding` sesudah; hasil wajib **SAMA**). Bila berbeda → uji **GAGAL**, penyebab wajib dicari.
- **Log `change_log` ditangani terpisah** oleh sidik jari (boleh tumbuh, isi lama wajib utuh).
  `pulihkan_data.py` tidak menyentuh log dan memasukkan kembali baris yang dihapus uji.
- **Smoke produksi hanya membaca** (menulis hanya bila `DATA_UJI=1` eksplisit).
- **Seed ulang menghidupkan data yang sudah dihapus**: setiap penghapusan yang disetujui wajib punya
  skrip idempoten di `scripts/db/fixes/` + uji penjaga (`test_seed_bersih.py`).
- **Uji banding Excel penuh** (`compare_alquran_full_excel.py`), bukan sampel.

### 3.5 Tab domain & menu
- Halaman Capaian dan Input memakai **tab** Al Qur'an / Ilmu Wasilah / Ilmu Ghayah; submenu Capaian di
  menu samping/bilah bawah **dihapus**. Semua staf melihat ketiga domain (hak lihat tidak berubah).

### 3.6 Target dinamis T7 (keputusan Mudir 26 November 2026)

- **(a) Pengaju & penyetuju:** pengampu (Musyrif/ah, Mudarris/ah) mengajukan untuk santri/halaqah yang
  diampu; **Masul** menyetujui **hanya domainnya**; **Mudir/Admin** semua domain. Pengampu tidak
  menyetujui. Target yang dibuat langsung oleh Masul/Mudir/Admin otomatis `disetujui`.
- **(b) Ubah target:** membuat **baris baru** dengan `effective_month_id`; target lama tetap utuh.
  Bulan lewat/terkunci: **hanya Mudir/Admin** dan wajib `p_konfirmasi = true`. Riwayat dapat dibaca.
- **(c) Bentuk:** Al Qur'an per **santri** per bidang, **harian**; massal per halaqah lalu sesuaikan
  per santri, individu didahulukan dari halaqah. Wasilah/Ghayah per **halaqah** per mata pelajaran,
  **bulanan langsung**, **tidak** dikali Hadir.
- **(d) Bulan berlaku:** dipilih saat mengajukan (default bulan berjalan); berlaku penuh sebulan,
  tidak dipecah, sampai diganti; lintas tahun ajaran. Bulan 0 tidak boleh menjadi bulan berlaku target.
- **(e) Penolakan:** alasan **wajib**; target tidak dihapus, tetap riwayat; pengaju dapat mengajukan ulang.
  Pengaju dapat **membatalkan** targetnya yang masih `diajukan` lewat RPC `batalkan_target`.
- **(f) `target_monthly`:** NULL bila tidak ada target, Hari Efektif belum diatur, atau bulan 0;
  **0** hanya bila target harian ada dan Hadir benar-benar 0; bulanan = `amount`.
- **(g) Ketiga domain** memakai mekanisme yang sama.
- **Tulis langsung ditutup:** policy INSERT/UPDATE/DELETE `targets` dihapus; privilege tulis dicabut
  dari `anon`/`authenticated`; hanya RPC (SECURITY DEFINER + cek hak internal) yang boleh menulis.
- **DUMMY:** 25 target Wasilah + 11 target Ghayah adalah DUMMY (izin Mudir), diganti data asli T8/T10;
  skrip `scripts/db/fixes/2026-11-26_t7b_target_dummy_wasilah_ghayah.sql`.

---

## 4. Status Supabase (ringkas; rinci di STATUS bagian 3)

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1`. Kredensial hanya di `.env.local`.

- **31 migrasi** tercatat dijalankan (`000001`-`000009`, `000010`-`000012` T5c, `000013`-`000016` T6b,
  `000017`-`000018` T6d2, `000019`-`000020` T6e, `000021`-`000031` T7a). Berikutnya: `20261126000032_...`.
- **19 tabel RLS aktif** (termasuk `change_log`), **42 kebijakan**, **47 fungsi** public, 4 view.
- **Matriks RLS otomatis: 94 OK / 3 SKIP / 0 GAGAL** (SKIP menunggu profil wali / target `diajukan`).
- **Auth:** `disable_signup=true`, provider email aktif, `mailer_autoconfirm=false`.
- **Ekstensi** `pg_trgm` di skema `extensions` (bukan `public`).
- **Seed dummy 1447** sudah dimuat; **destruktif** (TRUNCATE) — jangan diulang tanpa perintah Mudir.
  `month_domain_settings` hanya Al Qur'an bulan 1-7 (Wasilah/Ghayah DUMMY bulan 1-7), `is_locked` semua
  `false`.

---

## 5. Pertanyaan terbuka (menunggu keputusan / data Mudir)

1. **Repo masih PUBLIK.** Harus dijadikan **privat** sebelum data asli santri dimuat
   (`gh repo edit --visibility private --accept-visibility-change-consequences`). Pengingat wajib
   disebut lagi di T10.
2. **Data Awal (252 capaian)**: dipertahankan atau dikosongkan saat data asli masuk? Keputusan T10.
3. **69 capaian dummy yang "mundur"** (lebih kecil dari bulan lalu): disepakati dibiarkan; konfirmasi
   ulang sebelum T9.
4. **Halaqah Level 6 (4 santri Wasilah)** belum punya mata pelajaran/pengampu. Apa yang harus
   ditampilkan/diisi? (T8).
5. **Hari Efektif bulan 8-12** (semua domain) belum ada; layar pengisiannya T8. Notifikasi "data
   belum lengkap" karena itu tidak memeriksa bulan-bulan tersebut.
6. **Matriks RLS 8 sel SKIP** — perlu profil `wali` dan contoh target `diajukan` (T9).
7. **Reproduksi log:** seed ulang (TRUNCATE) tidak tercatat di `change_log`; bila Mudir ingin seed
   ulang tercatat, perlu keputusan (mis. penanda `seed_log` manual) — belum dibuat.
8. **T7 sendiri** punya pertanyaan yang harus dijawab Mudir **sebelum kode** — lihat bagian 8.

---

## 6. Risiko yang harus diingat

- **Satu database untuk uji & produksi.** Uji yang salah bisa merusak data dummy (dan nanti data
  asli). Mitigasi sekarang: `db_fingerprint.py` + `pulihkan_data.py` + smoke produksi baca-saja.
  **Usulan (belum dibuat, menunggu persetujuan):** proyek Supabase **terpisah khusus QA** sebelum
  T9/T10 — langkah & dampak di `docs/STATUS.md` 2l butir 7.
- **Seed ulang menghidupkan kembali data yang pernah dihapus** (truncate + isi ulang). Jalankan
  `scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql` dan `test_seed_bersih.py` sesudah seed.
- **`test_input_dropdown_e2e.py` versi lama** pernah menghapus 20 baris seed; sudah diperbaiki. Jangan
  kembali memakai pola `delete ... where entered_at >= mulai`.
- **Log append-only** bisa membesar; sementara tidak ada pemangkasan. Bila perlu, keputusan Mudir.
- **Supabase mengembalikan maks 1.000 baris/permintaan** → wajib `ambilSemua`.
- **`selisih` lintas buku** butuh `item_position` (posisi kumulatif), jangan jumlahkan nilai mentah.
- **Migrasi lama tidak boleh diubah**; perubahan skema = berkas baru nomor berikutnya.
- **Repo publik**: jangan pernah menulis kata sandi, kunci, `DATABASE_URL`, atau data santri asli.

---

## 7. Cara menjalankan, menguji, dan deploy

```bash
npm install
npm run dev            # http://localhost:5173 (atau port berikutnya)
npm run typecheck      # wajib hijau
npm run test           # 14 uji aturan putaran + audit
npm run build          # wajib berhasil; hasil di dist/
python scripts/check_repo_safety.py   # WAJIB lolos sebelum push
git config core.hooksPath .githooks   # sekali saja (hook pre-commit keamanan)
```

**Sidik jari database (wajib untuk uji yang menulis):**
```bash
python scripts/qa/db_fingerprint.py --simpan /tmp/fp_sebelum.json
# ...jalankan uji...
python scripts/qa/db_fingerprint.py --banding /tmp/fp_sebelum.json   # harus "SAMA"
```

**Uji database (membaca `.env.local`, tidak mencetak rahasia, sebagian menulis + ROLLBACK):**
```bash
python scripts/qa/run_pre_t6_db_tests.py            # 16/16
python scripts/qa/regression_execute.py             # 7/7
python scripts/qa/rls_matrix.py                     # 94/97 (3 SKIP)
python scripts/qa/test_t6a_tabel.py                 # 14/14
python scripts/qa/test_t6b_input_wasilah.py         # 29/29
python scripts/qa/test_t6d2_masul_input.py          # 68/68
python scripts/qa/test_t6e_hapus_capaian.py         # 35/35 (hapus + log)
python scripts/qa/test_seed_bersih.py               # 6/6 (penjaga setelah seed)
python scripts/qa/compare_alquran_full_excel.py     # 7/7 (banding Excel PENUH)
python scripts/qa/compare_rabiul_awwal_excel.py     # 7/7
python scripts/qa/test_data_awal_tahun_kedua.py     # 5/5
python scripts/qa/test_no_halaqah.py                # 9/9
python scripts/qa/test_students_without_halaqah.py  # 13/13
python scripts/qa/test_students_without_halaqah_p6.py # 6/7 (1 SKIP: tak ada wali)
python scripts/qa/test_auth_signup_closed.py        # 9/9
```

**E2E browser (Playwright, Chrome terpasang; butuh `dist/` disajikan):**
```bash
python3 scripts/qa/serve_dist.py 4173 &            # server statis dist
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t6d2_e2e_masul.py   # 14/14
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t6b_e2e.py          # 14/14
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_input_dropdown_e2e.py # 10/10
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t6e_e2e_hapus.py     # 16/16
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t6e_langkah0_pengampu.py # 12/12
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/smoke_e2e.py               # 43/43 lokal
```
`test_t6e_uji_penerimaan.py` **menghapus permanen** (perintah Mudir); jangan dijalankan lagi tanpa
perintah baru.

**Deploy:** `git push origin main` → Vercel otomatis (project `kusafa-app`). Verifikasi: HTTP 200
dan nama bundel `dist/assets/index-*.js` sama dengan yang disajikan produksi. Smoke produksi:
`BASE_URL=https://kusafa-app.vercel.app .venv-qa/bin/python scripts/qa/smoke_e2e.py` (**baca saja**).
Hosting bisa dipindah ke cPanel; environment Vercel hanya `VITE_SUPABASE_URL` + anon key.

---

## 8. Langkah berikutnya — **T7 [2/2] UI Target**

**Fondasi database/RPC sudah selesai dan diuji 34/34.** Yang belum: antarmuka `/target`.

1. **Halaman daftar target** (`/target`): filter tahun/bulan, domain, halaqah, status; tampilkan
   target berlaku, status, pengaju/penyetuju, alasan tolak, dan tombol aksi sesuai role.
   Baca `targets` lewat `SELECT` (RLS staf) atau RPC riwayat; **jangan** menulis langsung.
2. **Form ajukan/ubah** memakai RPC `ajukan_target` / `ubah_target`; pilih bulan berlaku dengan
   `PemilihTahunBulan` (dua dropdown terpisah). Bulan 0 tidak ditawarkan. Tampilkan pesan galat
   database apa adanya; bila RPC meminta konfirmasi bulan lewat/terkunci, tampilkan dialog centang
   lalu panggil ulang dengan `p_konfirmasi = true`.
3. **Layar persetujuan Masul/Mudir/Admin:** `setujui_target`, `tolak_target` (alasan wajib),
   `batalkan_target` untuk pengaju. Target `diajukan`/`ditolak` tidak boleh masuk laporan.
4. **Riwayat** lewat `riwayat_target` (berlaku mulai, nilai, status, pengaju, penyetuju, alasan).
5. **Uji E2E UI** dan sidik jari sebelum/sesudah; perbarui `docs/STATUS.md`, berkas ini,
   `CHANGELOG`, `FILE-MAP`; `typecheck`, `build`, `check_repo_safety.py`, commit + push.
6. **Jangan mulai T8/T9** sebelum UI T7 selesai dan disetujui Mudir.

Catatan: target DUMMY Wasilah/Ghayah (25 + 11) wajib diganti data asli di T8/T10.
