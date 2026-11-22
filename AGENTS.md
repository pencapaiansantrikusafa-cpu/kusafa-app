# AGENTS.md - panduan untuk OpenCode

Proyek: **KUSAFA - Evaluasi dan Capaian Santri**. Aplikasi web untuk Mudir, Masul, dan asatidzah KUSAFA agar bisa melihat capaian santri
(Al Qur'an, Ilmu Wasilah, Ilmu Ghayah) per bulan Hijriyah, selisihnya, status terhadap target, dan kehadiran.
Pemilik proyek: Mudir KUSAFA (bukan programmer). Jelaskan keputusan teknis dengan bahasa sederhana.

## Baca dulu (berurutan)
1. `docs/SPEC.md` - aturan bisnis, role, model data, alur kerja. Ini sumber kebenaran.
2. `docs/DATA-NOTES.md` - cara data Excel dipetakan, dan temuan data yang masih terbuka.
3. `supabase/migrations/*.sql` - skema database yang sudah ditetapkan.
4. `prompts/OPENCODE.md` - urutan tugas. Kerjakan satu tugas per sesi.

## Stack
- Frontend: Vite + React + TypeScript + Tailwind CSS + react-router-dom. Hasil build berupa file statis (`dist/`).
- Backend: Supabase (PostgreSQL, Auth, Row Level Security). Tidak ada server sendiri.
- Hosting: Vercel dulu; harus tetap bisa dipindah ke cPanel (jangan memakai fitur yang hanya ada di Vercel: serverless function, edge, ISR).
- Skrip data: Python (`scripts/seed/`), hanya untuk seed dan pembuatan akun dummy.

## Aturan keras
- **Jangan menaruh kunci rahasia di frontend.** Frontend hanya memakai `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`. `SUPABASE_SERVICE_ROLE_KEY` hanya untuk skrip lokal.
- **Aturan bisnis ada di database** (RLS, fungsi, view). Jangan menghitung selisih, target, atau kehadiran di React; baca dari `v_monthly_report`, `v_attendance`.
- **Jangan mengubah migrasi yang sudah dijalankan.** Perubahan skema = file migrasi baru dengan nomor berikutnya.
- **Jangan menebak data.** Jika data atau aturan tidak jelas atau tidak sinkron, berhenti dan tanyakan kepada Mudir.
  Jangan membuat asumsi sendiri, termasuk saat seed.
- Tulis nama role selengkapnya di kode, teks UI, dan dokumen: **Masul Al Quran**, **Masul Wasilah**, **Masul Ghayah** (enum: `masul_alquran`, `masul_wasilah`, `masul_ghayah`). Jangan menulis "masul" saja.
- Selisih capaian **boleh negatif** (santri mengulang). Tampilkan apa adanya; jangan dianggap galat dan jangan dipaksa 0.
- Bulan yang belum diinput **kosong**, bukan 0 (di tabel dan grafik).
- Item kurikulum yang sudah dipakai capaian tidak boleh dihapus, hanya dinonaktifkan (`is_active = false`).
- Data santri (nama, NIS, capaian) adalah data pribadi anak-anak: jangan di-commit, jangan dikirim ke layanan pihak ketiga, jangan masuk log.
- **Repo ini PUBLIK selama pengembangan dan hanya boleh berisi kode, dokumen, dan data dummy.** Jalankan `python scripts/check_repo_safety.py` sebelum setiap push (hook pre-commit di `.githooks/` juga menjalankannya). Jika pemeriksaan gagal, jangan push. **Sebelum data asli santri dimuat ke database, repo harus dijadikan PRIVAT** (`gh repo edit --visibility private --accept-visibility-change-consequences`) dan hal itu harus diingatkan kepada Mudir.

## Bahasa dan tampilan
- Seluruh teks antarmuka berbahasa Indonesia. Nama bidang: Tilawah, Tahfidz, Kitabah, Baca, Tulis, Sirah, **Hisab** (bukan "Hitung"), Adab dan Iman, Aqidah dan Fiqih.
- Acuan tampilan: papan wireframe "KUSAFA - Wireframe UI/UX" (lihat README). Tabel halaqah: Lalu | Kini | Selisih.
  Merah muda = selisih di bawah target. Kuning = Hadir kurang dari Hari Efektif. Mobile-friendly, ringan.
- Aksesibel: label pada input, kontras cukup, jangan mengandalkan warna saja (tambahkan teks/ikon).

## Aturan tampilan dan formulir (berlaku untuk SEMUA halaman, sekarang dan nanti)
- **Dropdown Tahun dan Bulan selalu terpisah dua dropdown.** Jangan pernah membuat satu dropdown berisi "Bulan + Tahun". Saat berganti tahun ajaran, jumlah pilihan bulan tidak boleh bertambah. Pakai komponen `src/components/PemilihTahunBulan.tsx`.
- **Dropdown halaqah/level/kelompok selalu menampilkan pengampunya**: "HLQ-PA-1 - Ust. Fulan 1" (Al Qur'an: musyrif/ah; Wasilah: pengampu; Ghayah: muallim/ah). Jangan menampilkan kategori Putra/Putri karena sudah terbaca dari kode. Pakai `src/components/PemilihHalaqah.tsx`.
- **Semua formulir input (dropdown maupun isian) harus terhubung ke database**: nilai yang tersimpan ditampilkan kembali saat dibuka, dan tombol simpan menulis ke tabel Supabase (bukan sekadar state di browser). Bila hak akses menolak, tampilkan pesan galat dari database apa adanya.

## Perintah
```
npm install
npm run dev          # pengembangan
npm run typecheck    # wajib hijau sebelum selesai
npm run test         # uji aturan putaran (khatam/pengulangan)
npm run build        # wajib berhasil sebelum selesai
python scripts/check_repo_safety.py   # wajib lolos sebelum push
npm run seed:build   # membangun supabase/seed/*.sql dari data/source/*.xlsx
npm run seed:users   # membuat akun dummy di Supabase Auth
npm run db:sql -- <file.sql>   # menjalankan SQL ke database (atau: -- --query "select ...")
```

## Definisi selesai untuk setiap tugas
- `npm run typecheck` dan `npm run build` berhasil.
- Untuk perubahan hak akses: jalankan pemeriksaan di `docs/SPEC.md` bagian "Pemeriksaan RLS" (login sebagai tiap role) dan tuliskan hasilnya.
- Ringkas apa yang diubah dan apa yang perlu dicek Mudir, dalam bahasa sederhana.
