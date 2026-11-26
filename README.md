# KUSAFA - Evaluasi dan Capaian Santri

Aplikasi web untuk memantau capaian santri KUSAFA per bulan Hijriyah di tiga domain: **Al Qur'an**, **Ilmu Wasilah**, dan **Ilmu Ghayah** - beserta selisih dari bulan sebelumnya, status terhadap target, dan kehadiran.
Stack: Vite + React + TypeScript + Tailwind CSS, backend Supabase, hosting Vercel (harus tetap bisa dipindah ke cPanel).

Situs: https://kusafa-app.vercel.app

**Dokumen penting**
- `docs/STATUS.md` - **sumber kebenaran status** tiap tahap, kondisi database dan deploy.
- `docs/HANDOVER.md` - serah terima untuk sesi berikutnya: langkah konkret, keputusan final, pertanyaan terbuka, cara menjalankan/deploy.
- `docs/FILE-MAP.md` - peta kode, tabel database, fungsi dan view SQL.
- `docs/DATA-NOTES.md` - pemetaan Excel dan temuan data terbuka.
- `docs/SPEC.md` - aturan bisnis dan model data (sumber kebenaran aturan).
- `docs/CATATAN-TAHAPAN.md` - catatan khusus T6-T10.
- `prompts/OPENCODE.md` - urutan tugas T0-T10.
- `docs/CHANGELOG.md` - riwayat ringkas per tahap.

---

## Status pembangunan

Diperbarui 26 November 2026, HEAD sebelum dokumen ini `417a7ec`. Rincian lengkap, keputusan final, pertanyaan terbuka, dan langkah berikutnya ada di **`docs/HANDOVER.md`**. Angka dan bukti uji ada di **`docs/STATUS.md`**.

| Tahap | Nama | Status |
|---|---|---|
| A-G | Alat, proyek, Git, Supabase, seed, uji lokal, Vercel | SELESAI |
| T0 | Orientasi dan pemetaan Excel | SELESAI |
| T1 | Database dan seed dummy | SELESAI |
| T2 | Login, kerangka, menu per role | SELESAI |
| T3 | Tabel capaian halaqah Al Qur'an | SELESAI |
| T4 | Halaman satu santri | SELESAI |
| T5 / T5b / T5c | Input capaian Al Qur'an, percepat input, pencarian server | SELESAI |
| Pra-T6 | Audit, hardening, data, notifikasi, verifikasi | SELESAI |
| T6a-T6e | Tabel/input Wasilah & Ghayah, tab domain, Masul, hapus capaian + log | SELESAI |
| **T7 [1b/2]** | **Fondasi target dinamis (database, RPC, uji)** | **SELESAI** |
| **T7 [2/2]** | **UI `/target` + uji tulis** | **SELESAI** |
| T8 | Kurikulum, halaqah, santri, kalender, Hari Efektif & kunci bulan | BELUM |
| T9 | Pengujian & QA penuh | SEBAGIAN |
| T10 | Deploy akhir, hapus dummy, repo privat | BELUM |

Pemeriksaan terakhir (26 Nov 2026): `npm run typecheck` **hijau**, `npm run build` **berhasil**, `npm run test` **14/14**, `test_targets_t7.py` **34/34**, matriks RLS **94/97 (3 SKIP, 0 GAGAL)**, banding rumus laporan lama vs baru **2.036 baris, 0 beda**, sidik jari database **SAMA**, `check_repo_safety.py` **lolos**. E2E target T7 **baca-saja 36/36** dan **menulis 38/38**; E2E T6a/T6b/T6d2/T6e **14/14/14/16**, dropdown **10/10**, smoke produksi Vercel **42/42** (baca saja).

**Serah terima**: `docs/HANDOVER.md`. **Status nyata**: `docs/STATUS.md`. **Aturan bisnis**: `docs/SPEC.md`.

Situs produksi `https://kusafa-app.vercel.app` **HTTP 200**. Repo masih **PUBLIK**; wajib dijadikan privat sebelum data santri asli dimuat.

---

## Isi repo

```
AGENTS.md                     aturan kerja tetap untuk developer/agent
README.md                     berkas ini
docs/SPEC.md                  aturan bisnis, role, model data
docs/STATUS.md                status tiap tahap + kondisi database/deploy
docs/HANDOVER.md              serah terima untuk sesi berikutnya
docs/FILE-MAP.md              peta kode, tabel, fungsi, dan view
docs/DATA-NOTES.md            pemetaan data Excel dan temuan terbuka
docs/CHANGELOG.md             riwayat ringkas per tahap
docs/CATATAN-TAHAPAN.md       catatan khusus untuk T6-T10
prompts/OPENCODE.md           urutan tugas T0-T10
prompts/00-SETUP-OTOMATIS.md  prompt setup awal (arsip)
index.html, vite.config.ts, tailwind.config.js, postcss.config.js, tsconfig.json
vercel.json                   aturan rute untuk Vercel
public/.htaccess              aturan rute untuk cPanel/Apache
src/main.tsx, App.tsx, index.css       titik masuk aplikasi
src/components/               10 komponen (dropdown, pemilih, grafik, notifikasi, dialog)
src/lib/                      7 modul (supabase, role, laporan, putaran, posisi, dll)
src/pages/                    10 halaman (login, capaian, satu santri, input, formulir, placeholder)
supabase/migrations/          6 berkas migrasi (skema, fungsi, view, RLS)
supabase/seed/                hasil build_seed.py (TIDAK di-commit)
scripts/check_repo_safety.py  pemeriksaan keamanan sebelum commit
scripts/db/run_sql.py         menjalankan SQL ke database tanpa psql
scripts/seed/                 build_seed.py, create_auth_users.py, smoke_login.py
tests/putaran.test.mjs        6 uji aturan khatam/pengulangan
data/source/                  taruh 5 file Excel di sini (TIDAK di-commit)
.githooks/pre-commit          hook pemeriksaan keamanan
```

Hasil `dist/` dan `node_modules/` tidak di-commit.

---

## Persiapan sekali saja

Pasang: Git, Node.js 20+, Python 3.10+, dan GitHub CLI (`gh`). Supabase dan Vercel dijalankan lewat `npx`. Tidak perlu `psql`.

```bash
npm install
cp .env.example .env.local     # lalu isi nilainya dari dashboard Supabase
git config core.hooksPath .githooks   # mengaktifkan pemeriksaan keamanan sebelum commit
```

Isi `.env.local` (jangan pernah di-commit):
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` - untuk frontend.
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` - hanya untuk skrip lokal.

Catatan jaringan: alamat langsung `db.<ref>.supabase.co` tidak bisa diresolusi di jaringan pengembang ini (tanpa IPv6), jadi `DATABASE_URL` memakai **pooler** `aws-0-ap-southeast-1.pooler.supabase.com:5432`.

### Migrasi
```bash
npx supabase init
npx supabase link --project-ref <ref>
npx supabase db push --remote      # Supabase CLI 3.2.0 butuh --remote
```
Migrasi yang sudah dijalankan **tidak boleh diubah**. Perubahan skema = berkas baru `20261121000007_...`.

### Seed data uji (destruktif, hanya untuk pengembangan)
```bash
pip install -r scripts/seed/requirements.txt
npm run seed:build                    # dari data/source/*.xlsx
python scripts/db/run_sql.py supabase/seed/01_curriculum.sql
npm run seed:users                    # membuat 24 akun dummy
python scripts/db/run_sql.py supabase/seed/02_school_data.sql
```
Baca `scripts/seed/output/seed-report.md`. Kata sandi akun dummy ada di `scripts/seed/output/users.csv` (tidak di-commit).

### Menjalankan
```bash
npm run dev        # http://localhost:5173
npm run typecheck
npm run test
npm run build
```

---

## Deploy

### Vercel (dipakai sekarang)
1. Import repo GitHub ke Vercel. Build command `npm run build`, output `dist`.
2. Environment Variables: **hanya** `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`.
3. `vercel.json` sudah mengatur rute satu halaman.
4. Deploy otomatis setiap push ke `main`; atau `npx vercel --prod`.
5. Di Supabase (Authentication → URL Configuration) tambahkan alamat situs ke daftar yang diizinkan.

### cPanel
Jalankan `npm run build` di komputer, unggah isi `dist/` ke `public_html`. File `.htaccess` ikut tersalin dari `public/`. Tidak perlu Node.js di server.

---

## Keamanan

- Repo ini **PUBLIK selama pengembangan** dan hanya boleh berisi kode, dokumen, dan data **dummy**.
- **Sebelum data asli santri dimuat, repo wajib dijadikan PRIVAT:**
  `gh repo edit --visibility private --accept-visibility-change-consequences`
- Jangan pernah commit atau tulis di dokumen: isi `.env`/`.env.local`, kunci `service_role` maupun `anon`, `DATABASE_URL` lengkap, kata sandi, `scripts/seed/output/users.csv`, file Excel di `data/source/`, atau data santri.
- `python scripts/check_repo_safety.py` wajib lolos sebelum setiap push (hook `.githooks/pre-commit` menjalankannya otomatis).
- Kunci `service_role` hanya di komputer lokal; jangan pernah ada di frontend maupun di Vercel.
- Sebelum dipakai publik: data dummy dihapus sehingga situs dimulai kosong. Seed hanya untuk pengembangan.
