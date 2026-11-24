# HANDOVER - serah terima untuk sesi berikutnya

**Terakhir diperbarui**: 24 November 2026, commit `fc0340a` (pra-T6 [6a]).
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
| T6 | Tabel & input Wasilah & Ghayah | **BELUM (belum boleh dimulai)** | - |
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

**Pra-T6 [6] SELESAI** (commit `1752176`, `38b71dc`, `0378f87`) — rincian hasil di `docs/STATUS.md` bagian 2d. Tidak ada pekerjaan yang berjalan di tengah; semua sudah di-commit dan di-push.

**Yang sudah jalan** — lihat `docs/STATUS.md`: login/menu per role, tabel & input Al Qur'an, halaman santri,
notifikasi "data belum lengkap" dan "santri belum punya halaqah", deploy Vercel tersambung Supabase.

**Yang belum jalan** — T6 s.d. T10 (daftar di `prompts/OPENCODE.md` & `docs/CATATAN-TAHAPAN.md`).

**Bug/error yang diketahui:**
- Tidak ada galat build / `tsc` / uji. Yang tertulis di `docs/STATUS.md` bagian 6 semuanya keterbatasan, bukan galat menggantung.
- Kinerja muat item Al Qur'an lambat (~9.177 item dimuat eager); 3 opsi perbaikan di `STATUS.md` 2c — **ini menjadi tugas T5c** (lihat langkah berikutnya).
- `npm audit` sisa 2: `vite`/`esbuild` (hanya dev server, tidak ikut bundel produksi).

**Langkah berikutnya (berurutan) — keputusan Mudir 24 November 2026:**
1. ~~Merge react-router 7~~ — **SELESAI** (smoke 29/29 lulus di branch, lalu merge & push).
2. **T5c — percepat input** (Opsi A di `STATUS.md` 2c: pencarian item di server lewat RPC). Kerjakan sebelum T6.
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

- **Urutan kerja:** pra-T6 [6] → **merge react-router** (bila smoke lulus) → **T5c percepat input** → **T6**. T6 **belum** boleh dimulai sebelum T5c selesai.
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

Struktur teknis (SPES & STATUS): `hijri_months` 13 baris, tahun di `academic_years`; semua dropdown `DropdownCari` (panel layang `z-60`); tahun & bulan dua dropdown terpisah; label item ber-awalan nama bidang; daftar panjang wajib `ambilSemua`; frontend hanya `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`; migrasi lama **tidak diubah** (berikutnya `20261121000010_...`).

---

## 4. Status Supabase

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1`.
Kredensial hanya di `.env.local` (**tidak dicetak/commit**). `DATABASE_URL` adalah koneksi Postgres Supabase yang dipakai skrip lokal (`scripts/db/run_sql.py`, seed, uji QA); tipe spesifik (pooler langsung vs transaction-pooler) periksa di Dashboard supaya tidak keliru dipakai dari luar.

- **Migrasi dijalankan (10)**: `000001`–`000009` + `20261124000010_attendance_guard_revoke`.
- **Auth**: `disable_signup = true`, provider email **aktif** (`external.email=true`), `mailer_autoconfirm=false`. Signup ditolak `422 signup_disabled`; login 7 role lulus (24 Nov 2026). Diubah lewat Management API (`PATCH /v1/projects/<ref>/config/auth`).
- **RLS**: 18 tabel `relrowsecurity=true`; semua kebijakan bertarget role `authenticated`; fungsi di-hardening (cabut `EXECUTE` anon/PUBLIC, grant authenticated+service_role). Matriks RLS otomatis: **38 OK / 8 SKIP / 0 GAGAL**.
- **Fungsi trigger**: `attendance_guard_override()` kini **tanpa** EXECUTE untuk authenticated/anon/PUBLIC; trigger tetap berjalan (SECURITY DEFINER).
- **Seed**: data dummy 1447 dimuat; destruktif, jangan ulang tanpa izin Mudir. `month_domain_settings` hanya Al Qur'an bulan 1-7 (Rabiul Awwal=3 karena libur, Syawwal=4); `is_locked` semua `false`.
- **Fungsi/view**: 20 fungsi public; 4 view (`v_monthly_report`, `_base`, `v_attendance`, `v_months_ordered`).

---

## 5. Pertanyaan terbuka (menunggu jawaban / data Mudir)

- ~~Boleh mulai T6?~~ — **TERJAWAB:** belum; urutan [6] → merge react-router (selesai) → T5c → T6.
- ~~Signup publik aktif?~~ — **TERJAWAB & DITUTUP:** `disable_signup=true`, provider email tetap aktif, login jalan.
- ~~Naik react-router ke 7.x?~~ — **TERJAWAB & SELESAI:** di-merge setelah smoke 29/29 lulus.
- ~~Pasang ESLint?~~ — **TERJAWAB:** ditunda ke T9.
- ~~Excel Rabiul Awwal masih 3?~~ — **BUKAN MASALAH:** 3 adalah nilai benar (libur ~2 pekan lebih). Nilai 19 dibatalkan dan dipulihkan ke 3.
- ~~Data Awal tahun kedua?~~ — **TERJAWAB:** otomatis dari Ramadhan tahun sebelumnya (HANDOVER 3a, SPEC 4a-1).

Masih terbuka:

1. **Repo masih PUBLIK** sampai T10. Wajib privat sebelum data asli dimuat (`gh repo edit --visibility private`).
2. **Hari Efektif Syawwal 1447 = 4 hari** (bulan lain 15–21). Apakah memang bulan pembuka yang tidak penuh, atau angkanya salah? Belum diubah; hanya dicatat (`STATUS.md` 2d).
3. **Data Awal (252 capaian)** dipertahankan; dikosongkan saat data asli? Keputusan T10.
4. **69 capaian dummy mundur** — disepakati dibiarkan; konfirmasi ulang sebelum T9.
5. **Level 6 (4 santri)** belum punya pengampu/jadwal — apa yang ditampilkan (T8).
6. **Hari Efektif hanya ada untuk Al Qur'an bulan 1–7**; bulan 8–12 dan Wasilah/Ghayah belum punya (layar pengisian di T8).
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