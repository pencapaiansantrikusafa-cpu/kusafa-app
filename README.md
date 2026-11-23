# KUSAFA - Evaluasi dan Capaian Santri

Aplikasi web evaluasi capaian santri KUSAFA. Stack: Vite + React + TypeScript + Tailwind, Supabase, Vercel (bisa pindah ke cPanel).

Dokumen acuan (di akun Claude pemilik proyek): "KUSAFA - System Design" dan papan "KUSAFA - Wireframe UI/UX". Ringkasannya ada di `docs/SPEC.md`.

## Status pembangunan

Diperbarui: 23 November 2026. Bagian ini diperbarui setiap selesai satu tahap atau satu tugas.
Jangan menulis rahasia (kunci, kata sandi) atau data santri di sini.

**Ringkas:** T1-T5 **SELESAI** (termasuk T5b dan perbaikan masukan 23 Nov 2026). **T6-T10 BELUM** dan dikerjakan berurutan sesuai `prompts/OPENCODE.md`.
Serah terima lengkap (daftar berkas per tahap, keputusan teknis yang tidak boleh berubah, status Supabase, langkah berikutnya, perintah) ada di **`docs/HANDOVER.md`**. Catatan khusus per tahap T6-T10 ada di **`docs/CATATAN-TAHAPAN.md`**.

| Bagian | Status |
|---|---|
| A-G (alat, proyek, Git, Supabase, seed, uji lokal, Vercel) | Selesai |
| T1 (migrasi + seed) | Selesai |
| T2 Login & menu per role | Selesai |
| T3 Tabel capaian Al Qur'an | Selesai |
| T4 Halaman satu santri | Selesai |
| T5 Input capaian Al Qur'an (+ T5b) | Selesai |
| T6 Wasilah & Ghayah | Belum |
| T7 Target dinamis | Belum |
| T8 Kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | Belum |
| T9 Pengujian & QA (RLS otomatis) | Belum |
| T10 Deploy akhir (hapus data dummy, repo privat) | Belum |

Pemeriksaan terakhir (23 Nov 2026, sesi uji T5 di browser): `npm run typecheck` hijau, `npm run test` 6/6 lulus, `npm run build` berhasil, `python scripts/check_repo_safety.py` lolos. Rincian tiap tahap ada di `docs/HANDOVER.md` bagian 1-2.

**Tabel rincian tahap A-G** (arsip)

| Tahap | Status | Hasil |
|---|---|---|
| A - Pemeriksaan alat | Selesai | Node 26.13, npm 11.20, Python 3.12.16, git 2.39, gh 2.105. Tidak ada yang perlu dipasang. |
| B - Siapkan proyek | Selesai | 5 file Excel di `data/source/`; `npm install` berhasil; `npm run typecheck` dan `npm run build` hijau. |
| C - Git dan GitHub | Selesai | Repo publik: https://github.com/pencapaiansantrikusafa-cpu/kusafa-app — hook keamanan `.githooks/pre-commit` aktif. |
| D - Supabase | Selesai | Project `kusafa` (ref `vcmamapzkhzgikpsvcdo`), region Singapore. 6 migrasi diterapkan (`db push --remote`). 18 tabel, semua `rowsecurity = true`, 44 kebijakan RLS. `.env.local` berisi 5 variabel; `DATABASE_URL` memakai pooler (`aws-0-ap-southeast-1.pooler.supabase.com:5432`) karena jaringan tanpa IPv6. |
| E - Seed data uji | Selesai | `build_seed.py`: BERHASIL, 0 galat, 25 peringatan (Tilawah mundur/khatam, wajar). Data masuk ke Supabase: 9 bidang, 158 buku, 10954 item, 109 santri, 38 halaqah, 327 target, 2036 capaian, 599 presensi, 24 akun dummy. |
| F - Uji lokal | Selesai | `npm run dev` jalan di http://localhost:5173/ ; halaman menampilkan "Tersambung ke Supabase." tanpa galat konsol. |
| G - Vercel | Selesai | Situs live: https://kusafa-app.vercel.app — "Tersambung ke Supabase." tanpa galat. Repo GitHub terhubung (deploy otomatis tiap push). Environment di Vercel hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY` (Production/Preview/Development). Site URL Supabase diatur manual di dashboard. |
| T2 - Login & kerangka | Selesai | Halaman login bahasa Indonesia, profil dari `profiles`, menu sesuai role (Mudir/Admin 6 menu; Masul 5; Musyrif/ah, Mudarris/ah 3). Diuji: 7 role login OK, form login OK, pesan galat saat sandi salah OK. `typecheck` & `build` hijau. |
| T3 - Tabel capaian Al Qur'an | Selesai | Tabel per halaqah + bulan (bulan pembanding otomatis), kolom Hadir/HE, Lalu/Kini/Selisih per bidang, target bulanan. Sorotan `di bawah target` (merah muda) dan `⚠ kurang` (kuning) disertai teks. Sel kosong tampil "belum diisi", bukan 0. Bulan default = bulan terakhir yang berisi data. Tabel Wasilah & Ghayah masih versi dasar (dirapikan di T6). |
| T4 - Halaman satu santri | Selesai | `/santri/:id` — pilih domain (Al Qur'an/Wasilah/Ghayah) dan rentang (Semester 1 / Semester 2 / Satu tahun). Grafik (SVG sendiri, tanpa pustaka), garis diputus pada bulan kosong. Sejak 23 Nov: **Tilawah, Tahfidz, dan Kitabah dalam satu kotak grafik**, dan **kehadiran di grafik terpisah** (pilihan "satu kotak gabungan semua" dihapus). Tabel riwayat dengan posisi kumulatif, selisih, Hadir/HE, target. Nama santri di tabel capaian bisa diketuk. |

**Pemeriksaan serah terima 22 November 2026**
- `npm run typecheck` hijau, `npm run build` berhasil, dan `npm run test` lulus 6 uji (99 modul; bundel 460,65 kB, gzip 131,42 kB).
- Uji aturan putaran di database nyata (dalam transaksi yang dibatalkan, data tidak berubah): halaman 587 putaran 1 → halaman 10 **khatam** putaran 2 = **selisih +27**; halaman 10 tanpa khatam (**pengulangan**) = **selisih −577**. Keduanya sesuai `docs/SPEC.md`.
- `python scripts/check_repo_safety.py` lolos: berkas token uji (`.smoke-tokens.js`) sudah dihapus dan pemeriksaan kini menolak JWT/refresh token apa pun, bukan hanya kunci service role.
- Vercel: project `kusafa-app` terhubung dan production siap.
- Jumlah baris database terverifikasi ulang (hanya baca): 109 santri, 2036 capaian — seed tidak dijalankan ulang.

**Pemeriksaan 23 November 2026 (T5b)**
- `npm run typecheck` hijau, `npm run build` berhasil, `npm run test` lulus 6 uji, `python scripts/check_repo_safety.py` lolos.- RLS diuji langsung di database (transaksi dibatalkan, tidak ada data berubah): Musyrif A ditolak menulis capaian, kehadiran, dan catatan pada halaqah milik Musyrif B.
- Antarmuka diuji di browser: pencarian "qura" → 4 pilihan Quraisy; Musyrif hanya melihat halaqah yang diampu (1 halaqah) dan notifikasi belum lengkap berisi 10 santri halaqahnya.
- Jumlah item Tilawah aktif yang termuat di dropdown: 1.464 (sama dengan hitungan database); sebelumnya terpotong 74.
- Catatan untuk pengembangan berikutnya: setiap query Supabase **wajib** memakai `ambilSemua` (atau `range` yang cukup besar) bila barisnya bisa lebih dari 1.000.

**Pemeriksaan 23 November 2026 (uji browser T5, akun Musyrif/ah HLQ-PA-1)**
- Simpan sungguhan dari browser berhasil: 3 bidang terisi → tertulis ke `progress_entries`, tampil lagi setelah muat ulang, halaqah menjadi 7/7 terisi. Data uji sudah dihapus kembali (2.036 capaian, 599 presensi).
- Konfirmasi "Pengulangan atau khatam?" muncul untuk capaian yang lebih kecil dari bulan lalu dan menahan simpan sampai dijawab.
- Dua cacat diperbaiki: ringkasan kehadiran menampilkan "0" untuk bulan yang belum diisi (kini "—"), dan item dropdown terduplikasi (kunci ganda React) karena memo mengubah state.

**Perbaikan 23 November 2026 (lanjutan, keputusan Mudir)**
- **Dropdown selalu melayang di atas semua isi** (portal ke `<body>`, lapisan 60). Sebelumnya panel Bulan tertutup kotak notifikasi dan bisa terpotong kartu. Bila ruang di bawah sempit, panel terbuka ke atas. Berlaku untuk semua dropdown, termasuk yang dibuat nanti.
- **Cari dengan nomor**: `88` → "Kitabah · Menyalin - 88" peringkat pertama; `menyalin 88` juga ketemu. Panel menulis "Menampilkan 60 dari N".
- **Label item memakai mata pelajaran**: "Tahfidz · An Naba' - 40". Buku Juz 'Amma dipakai Tilawah dan Kitabah sehingga label mentah bisa sama.
- **Dialog konfirmasi memakai teks dropdown**, bukan angka posisi.
- **Konfirmasi hanya untuk bidang yang diubah**; bidang yang sudah mundur tetapi tidak disentuh diberi penanda ⚠ (bukan pertanyaan). Selisih dibaca dari `v_monthly_report`.
- **Data Ramadhan dirapikan**: 7 baris presensi nol tanpa capaian dihapus. Presensi 606 → 599.
- Data uji yang mundur (43 kejadian) **dibiarkan** atas keputusan Mudir karena dummy (dihapus di T10).
**Notifikasi "Data belum lengkap" — keputusan Mudir 23 Nov 2026**
- **Batas bulan (opsi B):** yang diperiksa hanya bulan dari awal tahun sampai **bulan yang sudah berjalan**. Penandanya: bulan itu sudah punya Hari Efektif di `month_domain_settings` untuk domain tersebut. Bulan yang belum dimulai tidak dihitung, sehingga tidak dianggap kelalaian. Judul kotak: "awal tahun sampai bulan berjalan".
- **Kolom musyrif/ah** ada di tabel (nama dari `halaqah_teachers`; "belum ditetapkan" bila kosong). Kolom pengampu Wasilah/Ghayah ditambahkan saat T6.
- **Ringkasan "x/y terisi" per bulan** tampil sebagai deretan label per bulan ("Muharram 99/109"), hijau bila tuntas, kuning bila belum. Angkanya dihitung dari santri dalam lingkup yang boleh dilihat.
- **Lingkup dan saringan:** Mudir, Admin, dan Masul Al Quran melihat seluruh halaqah dan bisa **menyaring per halaqah** (dropdown pencarian "Lihat per halaqah"). Musyrif/ah (dan Mudarris/ah) hanya melihat halaqahnya sendiri, dengan ringkasan "N santri yang Anda ampu belum lengkap".
- **"Lengkap"** = santri punya capaian di **semua bidang aktif** bulan itu (Tilawah + Tahfidz + Kitabah). Santri yang hanya terisi satu bidang tetap dihitung belum lengkap.
- **Dropdown halaqah di notifikasi** selalu memuat nama musyrif/ah ("HLQ-PA-4 - Ust. Fulan 3"; "musyrif/ah belum ditetapkan" bila kosong), sesuai aturan AGENTS.md.
- **Tabel notifikasi:** kepala kolom tetap terlihat saat digulir ke bawah dan kolom Santri dibekukan di kiri saat digeser ke samping (HP sempit).
- **Submenu Capaian di menu samping** kini ikut alur menu (tidak melayang ke samping), sehingga tidak lagi menutupi dropdown Tahun Hijriyah.

**Pertanyaan terbuka**
- **Data kosong di Excel adalah sengaja** (dikonfirmasi Mudir, 22 Nov 2026): sel Hari Efektif/kehadiran yang kosong berarti bulan itu belum diinput.
  Aplikasi **wajib** menampilkan notifikasi "data belum lengkap" kepada **Mudir, Admin, Masul Al Quran, Masul Wasilah, Masul Ghayah, dan Musyrif/ah** yang terkait,
  berisi daftar santri/halaqah yang target atau capaiannya masih kosong, beserta kolom pengampu yang perlu menghubungi/bertindak.
  Musyrif/ah dapat mengisi sendiri atau meminta Admin mengisikan. Kosong tetap tampil kosong (bukan 0), sesuai `docs/SPEC.md`.
  Rincian jumlah per bulan (Muharram 77/109 terisi, dst.) ada di laporan percakapan 22 Nov 2026.
- **Keputusan Mudir (22 Nov 2026):** repo tetap **publik** selama pengembangan karena seluruh data (Excel dan isi database) masih data palsu (NIS berpola `144x.dummy-nis.xxx`, nama Fulan/Fulanah bernomor).
  Repo baru dijadikan **privat** ketika aplikasi sudah sempurna:
  `gh repo edit --visibility private --accept-visibility-change-consequences`.
- **Sebelum dipakai publik:** semua data dummy harus dihapus sehingga situs dimulai dengan data kosong (bukan seed). Seed hanya untuk pengembangan dan uji.
- `npm install` melaporkan 4 kerentanan dependensi (3 sedang, 1 tinggi). Belum diperbaiki karena `npm audit fix --force` berisiko merusak versi paket.
- Berkas `.smoke-tokens.js` (token uji sementara) sudah **dihapus** dan `.gitignore` tetap mengecualikannya.

**Catatan teknis**
- Supabase CLI 3.2.0: perintah ke project online butuh penanda `--remote` (mis. `npx supabase db push --remote`).
- `hijri_months` **tidak punya** kolom `hijri_year`; tahun ada di `academic_years` (ambil lewat relasi `academic_years!inner(hijri_year)`).
- Query `v_monthly_report` tanpa filter bisa kena *statement timeout*. Selalu filter `halaqah_id` + `month_id`.
- Posisi capaian dihitung database (`public.item_position`), dipanggil dari form lewat RPC `item_position` hanya saat tombol Simpan — untuk memeriksa apakah capaian lebih kecil dari bulan lalu. Tidak ada perhitungan selisih di React.
- Dropdown item di halaman Input diambil **per buku** (buku urut `stage_order`, `sort_order`; item urut `seq`), lalu digabung. Satu query `ORDER BY seq` tidak boleh dipakai: `seq` mulai dari 1 di setiap buku dan tidak unik, sehingga urutannya acak.
- Teks "Bulan lalu" di form memakai `item_label` dari `v_monthly_report` (teks dropdown bulan lalu), bukan angka posisi.
- **Batas 1.000 baris per permintaan** (bawaan Supabase pada proyek ini): query yang hasilnya bisa lebih dari 1.000 baris wajib memakai `ambilSemua` di `src/lib/ambil-semua.ts`. Tanpa itu data diam-diam terpotong.
- Semua dropdown wajib memakai `src/components/DropdownCari.tsx` (pencarian + `▾`); jangan memakai `<select>` biasa untuk daftar siswa/halaqah/level/bidang (aturan AGENTS.md).
- Alamat koneksi langsung `db.<ref>.supabase.co` tidak bisa diresolusi di jaringan ini (tanpa IPv6), jadi semua skrip memakai pooler.
- Data uji sudah dimuat. Kata sandi akun dummy ada di `scripts/seed/output/users.csv` (tidak di git). Laporan seed: `scripts/seed/output/seed-report.md`.
- Site URL dan Redirect URL Supabase diatur **manual di dashboard** (Authentication → URL Configuration), bukan lewat `supabase config push`, karena perintah itu akan ikut mengubah 11 pengaturan Auth lain (konfirmasi email, MFA, panjang OTP, pooler). Nilai yang diinginkan sudah tercatat di `supabase/config.toml` sebagai acuan.

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
