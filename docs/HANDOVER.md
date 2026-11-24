# HANDOVER - serah terima untuk sesi berikutnya

**Terakhir diperbarui**: 24 November 2026, 15:29 WIB, commit `a8b5b45`.
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
| T6 | Tabel & input Wasilah & Ghayah | **BELUM** | - |
| T7 | Target dinamis (ajukan/setujui) | **BELUM** | - |
| T8 | Kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | **BELUM** | - |
| T9 | Pengujian & QA penuh | **SEBAGIAN** | `scripts/qa/rls_matrix.py`, `test_no_halaqah.py`, `test_students_without_halaqah.py`, `run_pre_t6_db_tests.py` (sudah ada, belum lengkap) |
| T10 | Deploy akhir (hapus dummy, repo privat) | **BELUM** | - |

Pra-T6 rinci:
- **[1]** hardening fungsi → migrasi `20261121000007_harden_function_grants.sql`; `run_pre_t6_db_tests.py`.
- **[2]** keputusan bulan 0 & santri tanpa halaqah → `docs/SPEC.md` 4a/9; `test_no_halaqah.py`.
- **[3]** Hari Efektif Rabiul Awwal 3→19 → `scripts/db/fixes/2026-11-24_rabiul_awwal_effective_days.sql`.
- **[4]** notifikasi "santri belum punya halaqah" → migrasi `20261121000009_students_without_halaqah.sql`, `KotakBelumLengkap.tsx`, `test_students_without_halaqah.py`.
- **[5]** audit + docs → `scripts/qa/rls_matrix.py`, `tests/audit-rules.test.mjs`, `check_repo_safety.py` (diperkuat), `README.md`, `CHANGELOG.md`, `FILE-MAP.md`, `STATUS.md`.

---

## 2. Tahap yang sedang dikerjakan

Tidak ada pekerjaan yang berjalan di tengah; semua yang di-inisiasi sudah di-commit. Di luar repo ada satu branch kerja:
**`chore/react-router-fix`** (commit `dc03281`) — uji naik `react-router-dom` ke **7.18.6** (patch
GHSA-wrjc-x8rr-h8h6 & GHSA-337j-9hxr-rhxg). `tsc`, `build`, dan `npm test 14/14` lulus di sana, **belum di-merge**.

**Yang sudah jalan** — lihat `docs/STATUS.md`: login/menu per role, tabel & input Al Qur'an, halaman santri,
notifikasi "data belum lengkap" dan "santri belum punya halaqah", deploy Vercel tersambung Supabase.

**Yang belum jalan** — T6 s.d. T10 (daftar di `docs/OPENCODE.md` & `docs/CATATAN-TAHAPAN.md`).

**Bug/error yang diketahui:**
- Tidak ada galat build / `tsc` / uji. Yang tertulis di `docs/STATUS.md` bagian 6 semuanya keterbatasan, bukan galat menggantung.
- Kinerja muat item Al Qur'an lambat (~9.177 item dimuat eager); 3 opsi perbaikan di `STATUS.md` 2c, **belum diterapkan**.

**Langkah berikutnya (berurutan) — jangan mulai T6 sebelum Mudir menjawab:**
1. T6 — tabel & input Wasilah & Ghayah (ganti tulisan "dikerjakan pada T6" di `TabelCapaian.tsx`; input sekali per halaqah × mata pelajaran disalin ke anggota; `hanyaHalaqahDiampu()`).
2. T7 — target dinamis (ajukan/setujui); target bulanan = target harian × Hadir, dihitung database.
3. T8 — Hari Efektif & kunci bulan, penugasan halaqah, kelola kurikulum, tambah tahun.
4. T9 — jadikan uji RLS manual jadi tetap; uji HP; lengkapi sel SKIP matriks RLS.
5. T10 — hapus data dummy, jadikan repo privat, putar/bersihkan sekret, selesaikan react-router & ESLint.

---

## 3. Keputusan yang sudah final (jangan diubah tanpa persetujuan Mudir)

Aturan bisnis lengkap: `docs/SPEC.md`. Ringkas:
- Hadir = Hari Efektif − (izin+sakit+alpha), dihitung database, bukan React.
- Bulan 0 (Data Awal) = catatan awal, **bukan** bulan efektif/target dan **bukan** bulan input staf; `month_is_open(0,*)=false`. Santri lama memakai Ramadhan tahun lalu sebagai pembanding Syawwal.
- Hari Efektif Rabiul Awwal (Al Qur'an) = **19** (bukan 3); Excel sumber masih 3, wajib diperbaiki Mudir.
- Selisih **boleh negatif** (pengulangan); putaran naik **hanya** lewat pilihan eksplisit "khatam" (putaran = bulan lalu + 1).
- Bulan belum diinput **kosong**, bukan 0. Item kurikulum terpakai **tidak dihapus**, hanya `is_active=false`.
- Santri yang tidak ikut semua halaqah adalah keadaan **sah** (NIS 023/024 = kasus uji resmi); di domain yang tidak diikuti santri **tidak ditampilkan**, bukan tampil 0.
- Notifikasi "santri belum punya halaqah": Mudir/Admin semua domain; Masul Al Quran/Wasilah/Ghayah hanya domainnya; Musyrif/Mudarris tidak; anon ditolak.
- Role ditulis lengkap: **Masul Al Quran / Masul Wasilah / Masul Ghayah**.
- Nama bidang: Tilawah, Tahfidz, Kitabah, Baca, Tulis, Sirah, **Hisab**, Adab dan Iman, Aqidah dan Fiqih.

Struktur teknis (SPES & STATUS): `hijri_months` 13 baris, tahun di `academic_years`; semua dropdown `DropdownCari` (panel layang `z-60`); tahun & bulan dua dropdown terpisah; label item ber-awalan nama bidang; daftar panjang wajib `ambilSemua`; frontend hanya `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`; migrasi lama **tidak diubah** (berikutnya `20261121000010_...`).

---

## 4. Status Supabase

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1`.
Kredensial hanya di `.env.local` (**tidak dicetak/commit**). `DATABASE_URL` adalah koneksi Postgres Supabase yang dipakai skrip lokal (`scripts/db/run_sql.py`, seed, uji QA); tipe spesifik (pooler langsung vs transaction-pooler) periksa di Dashboard supaya tidak keliru dipakai dari luar.

- **Migrasi dijalankan (9)**: `000001` core_calendar, `000002` students_curriculum, `000003` halaqah, `000004` targets_progress, `000005` functions_views, `000006` rls, `000007` harden_function_grants, `000008` month_zero_not_open, `000009` students_without_halaqah.
- **RLS**: 18 tabel `relrowsecurity=true`; semua kebijakan bertarget role `authenticated`; fungsi di-hardening (cabut `EXECUTE` anon, grant authenticated+service_role). Matriks RLS otomatis: **38 OK / 8 SKIP / 0 GAGAL**.
- **Seed**: data dummy 1447 dimuat; destruktif, jangan ulang tanpa izin Mudir. `month_domain_settings` hanya Al Qur'an bulan 1-7 (Rabiul Awwal=19); `is_locked` semua `false`.
- **Fungsi/view**: 20 fungsi public; 4 view (`v_monthly_report`, `_base`, `v_attendance`, `v_months_ordered`).

---

## 5. Pertanyaan terbuka (menunggu jawaban / data Mudir)

1. **Boleh mulai T6?** Pra-T6 [1-5] selesai; belum ada izin.
2. **Repo masih PUBLIK.** Wajib privat sebelum data asli dimuat (`gh repo edit --visibility private`).
3. **Signup publik Supabase masih aktif** (`disable_signup=false`). Matikan di Dashboard → Authentication → Providers → Email → "Allow new users to sign up".
4. **Excel Rabiul Awwal masih `=3`** (`BZ5:B113`) → perbaiki jadi 19 agar seed ulang tidak mengembalikan 3.
5. **Naik react-router ke 7.x?** Cabang uji siap; menunggu keputusan (perubahan mayor).
6. **Pasang ESLint?** Dependensi dev baru; menunggu persetujuan.
7. **Data Awal (252 capaian)** dipertahankan; dikosongkan saat data asli? Keputusan T10.
8. **69 capaian dummy mundur** — disepakati dibiarkan; konfirmasi ulang sebelum T9.
9. **Level 6 (4 santri)** belum punya pengampu/jadwal — apa yang ditampilkan.

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