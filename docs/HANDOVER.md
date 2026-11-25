# HANDOVER - serah terima untuk sesi berikutnya

**Terakhir diperbarui**: 25 November 2026, **T6e selesai** (hapus capaian + log perubahan).
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
| **T7** | **Target dinamis (ajukan/setujui)** | **BELUM** — langkah berikutnya |
| T8 | Kelola kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | **BELUM** |
| T9 | Pengujian & QA penuh | **SEBAGIAN** (banyak uji otomatis sudah ada dan hijau) |
| T10 | Deploy akhir (hapus dummy, **repo privat**) | **BELUM** |

Ringkasan rincian tiap tahap: `docs/STATUS.md` bagian 1 dan 2a-2m. Riwayat perubahan: `docs/CHANGELOG.md`.

---

## 2. Posisi sekarang

- **Semua pekerjaan T6 (a, b, c, d, d2, d3, e) selesai**, di-commit, di-push, dan terverifikasi di produksi.
- **Tidak ada pekerjaan setengah jalan.** Git bersih dan sinkron `origin/main`.
- Migrasi terakhir: **`20261125000020_log_abaikan_update_kosong.sql`**. Migrasi berikutnya wajib
  bernomor **`20261125000021_...`** dan **tidak boleh** mengubah berkas migrasi lama.
- Produksi: `https://kusafa-app.vercel.app`, HTTP 200, bundel sama dengan build lokal, smoke produksi
  **42/42 (baca saja)** dan sidik jari database SAMA sebelum/sesudah.
- Data (setelah T6e, sesuai keputusan Mudir): capaian **2.036** (jumlah seed), kehadiran **599 / 756 /
  749**, catatan 0, log perubahan 96 baris (append-only).

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

---

## 4. Status Supabase (ringkas; rinci di STATUS bagian 3)

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1`. Kredensial hanya di `.env.local`.

- **20 migrasi** tercatat dijalankan (`000001`-`000009`, `000010`-`000012` T5c, `000013`-`000016` T6b,
  `000017`-`000018` T6d2, `000019`-`000020` T6e). Berikutnya: `20261125000021_...`.
- **19 tabel RLS aktif** (termasuk `change_log`), **45 kebijakan**, **34 fungsi** public, 4 view.
- **Matriks RLS otomatis: 67 OK / 8 SKIP / 0 GAGAL** (SKIP menunggu profil wali / target `diajukan`).
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
2. **Data Awal (252 capaian)**: dipertahankan atau dikosongkan saat data asli masuk? Keputusan T10.3. **69 capaian dummy yang "mundur"** (lebih kecil dari bulan lalu): disepakati dibiarkan; konfirmasi
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
python scripts/qa/rls_matrix.py                     # 67/75 (8 SKIP)
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

## 8. Langkah berikutnya — **T7 Target dinamis**

> **Perintah kerja sesi baru: WAJIB mengerjakan LANGKAH 0 dulu. JANGAN menulis kode sebelum Mudir
> menjawab pertanyaan di bawah.**

**LANGKAH 0 (wajib, sebelum kode apa pun):**
1. Baca `docs/SPEC.md` bagian target: bagian 3 (hak "Mengajukan/Menyetujui target"), bagian 4 (tabel
   `targets`), bagian 5 butir "Target", bagian 6 alur kerja.
2. Baca `docs/STATUS.md` (kondisi nyata: 2.036 capaian, 20 migrasi, RLS 67/75, sidik jari) dan
   `docs/DATA-NOTES.md` bagian target.
3. Baca `docs/CATATAN-TAHAPAN.md` bagian **T7** (batasan yang sudah ditetapkan).
4. Periksa data target yang ada di database (jangan menebak): **327 baris `targets`, semuanya
   `status = disetujui`, semuanya domain `alquran`, semuanya `amount_period = harian`**. Artinya
   **belum ada satu pun target Ilmu Wasilah / Ilmu Ghayah** dan belum ada baris `diajukan` — jadi
   `target_monthly` untuk Wasilah/Ghayah di laporan saat ini memang kosong (bukan 0).
5. Tulis **ringkasan rencana maksimal 15 baris** + **daftar pertanyaan untuk Mudir** ke chat.
6. **BERHENTI.** Tunggu jawaban Mudir. Tidak ada migrasi, kode, atau uji sebelum itu.

**Cakupan T7 yang sudah tertulis (bahan rencana, bukan izin mulai):**
- Target Al Qur'an **harian** → **bulanan = target harian × Hadir** (dihitung database, boleh pecahan).
- Status: `diajukan` / `disetujui` / `ditolak`; **hanya `disetujui`** yang dipakai laporan.
- Pengampu mengajukan; **Masul hanya menyetujui domainnya** (Masul Al Quran tidak boleh menyetujui
  Wasilah/Ghayah, dan sebaliknya); Mudir/Admin semua domain. Pengampu **tidak** menyetujui.
- Tombol "Ubah target" memakai `effective_month_id`; target lama tetap berlaku untuk bulan sebelumnya.
- Daftar target menunggu persetujuan **dibatasi halaqah menurut amanah** untuk pengampu.
- Target individu didahulukan dari target halaqah (Wasilah/Ghayah target halaqah, bulanan).
- Semua hak tulis lewat RPC + migrasi baru bernomor **`20261125000021_...`**; anon tanpa `EXECUTE`.
- Uji wajib: role (termasuk Masul lintas domain), `diajukan` tidak dipakai laporan, riwayat
  `effective_month_id`, target harian × Hadir, bulan 0, bulan terkunci, sidik jari SAMA, uji lama hijau.

**Pertanyaan untuk Mudir (susun ulang saat LANGKAH 0; minimal mencakup):**
(a) siapa **mengajukan** dan siapa **menyetujui** per domain (pengampu vs Masul vs Admin/Mudir);
(b) bolehkah target diubah untuk bulan yang **sudah lewat**, dan bagaimana riwayatnya ditampilkan;
(c) apakah target Al Qur'an boleh berbeda per **bidang** (Tilawah/Tahfidz/Kitabah) dan per **santri**;
(d) kapan target baru berlaku bila disetujui **di tengah bulan**;
(e) apakah penolakan wajib menyertakan **alasan**;
(f) perilaku bila **Hadir = 0** (target bulanan kosong atau 0);
(g) **target Wasilah/Ghayah**: sekarang belum ada sama sekali — apakah T7 harus menyediakan
    pengajuan/persetujuan untuk keduanya (bulanan, per halaqah), atau hanya menyiapkan jalurnya?

**Sesudah Mudir menjawab:** kerjakan T7 satu sub-tugas per commit kecil (ajukan → setujui/tolak →
"Ubah target" + riwayat → tampilan daftar menunggu → uji). Tiap selesai: `typecheck`, `build`,
sidik jari sebelum/sesudah, perbarui `docs/STATUS.md` + berkas ini + `CHANGELOG` + `FILE-MAP`,
`check_repo_safety.py`, commit + push.
**T8 dan T9 tidak dimulai sebelum T7 selesai dan disetujui Mudir.**
