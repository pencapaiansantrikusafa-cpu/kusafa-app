# KUSAFA - Evaluasi dan Capaian Santri

Aplikasi web evaluasi capaian santri KUSAFA. Stack: Vite + React + TypeScript + Tailwind, Supabase, Vercel (bisa pindah ke cPanel).

Dokumen acuan (di akun Claude pemilik proyek): "KUSAFA - System Design" dan papan "KUSAFA - Wireframe UI/UX". Ringkasannya ada di `docs/SPEC.md`.

## Isi repo
```
AGENTS.md                panduan untuk OpenCode
docs/SPEC.md             aturan bisnis, role, model data
docs/DATA-NOTES.md       pemetaan data Excel dan temuan terbuka
prompts/OPENCODE.md      urutan tugas dan prompt awal untuk OpenCode
supabase/migrations/     skema database, fungsi, view, RLS (6 file)
supabase/seed/           hasil build_seed.py (tidak di-commit)
scripts/seed/            build_seed.py, create_auth_users.py
data/source/             taruh 5 file Excel di sini (tidak di-commit)
src/                     aplikasi React
```

**Cara tercepat:** tempel prompt di `prompts/00-SETUP-OTOMATIS.md` ke OpenCode Desktop; semua langkah di bawah dikerjakan dari terminal tanpa membuka GitHub, Supabase, atau Vercel secara manual (hanya login sekali ke tiap layanan).

## Persiapan sekali saja
Pasang: Git, Node.js 20+, Python 3.10+, dan GitHub CLI (`gh`). Supabase dan Vercel dijalankan lewat `npx`. Tidak perlu `psql`: file SQL dijalankan dengan `python scripts/db/run_sql.py`.
Buat akun GitHub, Supabase, dan Vercel. Buat satu project Supabase (region terdekat, misalnya Singapore).

## Langkah
1. `git init`, lalu buat repo di GitHub dan push. Pastikan `.gitignore` ikut ter-commit.
2. `npm install`
3. Salin `.env.example` menjadi `.env.local` dan isi nilainya dari dashboard Supabase (Project Settings > API dan Database).
4. Jalankan migrasi berurutan:
   `npx supabase init`, `npx supabase link --project-ref <ref>`, `npx supabase db push`.
5. Taruh 5 file Excel di `data/source/`, lalu: `pip install -r scripts/seed/requirements.txt` dan `python scripts/seed/build_seed.py`.
   Baca `scripts/seed/output/seed-report.md`. Perbaiki data jika ada galat (lihat `docs/DATA-NOTES.md`).
6. `python scripts/db/run_sql.py supabase/seed/01_curriculum.sql`
7. `python scripts/seed/create_auth_users.py` (membuat 24 akun dummy; kata sandi ada di `scripts/seed/output/users.csv`).
8. `python scripts/db/run_sql.py supabase/seed/02_school_data.sql`
9. `npm run dev`, buka alamat yang tampil. Halaman awal harus menulis "Tersambung ke Supabase."
10. Lanjutkan pengembangan dengan OpenCode mengikuti `prompts/OPENCODE.md`.

## Deploy
- **Vercel:** import repo GitHub. Build command `npm run build`, output `dist`. Isi Environment Variables: `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY` saja. `vercel.json` sudah mengatur rute.
- **cPanel:** jalankan `npm run build` di komputer, unggah isi `dist/` ke `public_html` (file `.htaccess` ikut tersalin dari `public/`). Tidak perlu Node.js di server.
- Di Supabase (Authentication > URL Configuration) tambahkan alamat situs ke daftar yang diizinkan.

## Keamanan singkat
Repo boleh publik selama pengembangan karena hanya berisi kode dan data dummy. Sebelum data asli dimuat: jadikan repo privat. `python scripts/check_repo_safety.py` memeriksa berkas terlarang dan rahasia sebelum commit (hook di `.githooks/`; aktifkan dengan `git config core.hooksPath .githooks`).
Kunci `service_role` hanya di komputer lokal. Data santri tidak boleh di-commit (sudah di `.gitignore`). Akun dummy hanya untuk uji; akun asli dibuat manual.
