# AGENTS.md - panduan untuk OpenCode

Proyek: **KUSAFA - Evaluasi dan Capaian Santri**. Aplikasi web untuk Mudir, Masul, dan asatidzah KUSAFA agar bisa melihat capaian santri
(Al Qur'an, Ilmu Wasilah, Ilmu Ghayah) per bulan Hijriyah, selisihnya, status terhadap target, dan kehadiran.
Pemilik proyek: Mudir KUSAFA (bukan programmer). Jelaskan keputusan teknis dengan bahasa sederhana.

## Baca dulu (berurutan)
1. `docs/SPEC.md` - aturan bisnis, role, model data, alur kerja. Ini sumber kebenaran aturan.
2. `docs/DATA-NOTES.md` - cara data Excel dipetakan, dan temuan data yang masih terbuka.
3. `supabase/migrations/*.sql` - skema database yang sudah ditetapkan.
4. `prompts/OPENCODE.md` - urutan tugas. Kerjakan satu tugas per sesi.
   Keputusan dan catatan per tahap (T6-T10) ada di `docs/CATATAN-TAHAPAN.md`; baca sebelum mulai tahap terkait. Urutan tugas tidak berubah.
5. `docs/STATUS.md` - status nyata tiap tahap (sumber kebenaran status).
6. `docs/HANDOVER.md` - serah terima: langkah berikutnya, keputusan final, pertanyaan terbuka.
7. `docs/FILE-MAP.md` - peta kode, tabel database, fungsi dan view SQL.

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
- **Nilai Hari Efektif yang kecil bisa SAH.** Bulan dengan libur panjang (mis. Rabiul Awwal 1447 = **3 hari** karena libur sekitar dua pekan lebih, Syawwal = 4 hari) adalah data yang benar. Jangan menandainya sebagai "janggal"/kesalahan, jangan "memperbaiki" naik, dan jangan mengubahnya tanpa konfirmasi Mudir. Angka Excel sumber adalah acuan.
- Tulis nama role selengkapnya di kode, teks UI, dan dokumen: **Masul Al Quran**, **Masul Wasilah**, **Masul Ghayah** (enum: `masul_alquran`, `masul_wasilah`, `masul_ghayah`). Jangan menulis "masul" saja.
- Selisih capaian **boleh negatif** (santri mengulang). Tampilkan apa adanya; jangan dianggap galat dan jangan dipaksa 0.
- Konfirmasi "pengulangan atau khatam" **hanya ditanyakan untuk bidang yang benar-benar diubah pada kunjungan itu**. Bidang yang capaiannya sudah lebih kecil dari bulan lalu tetapi tidak disentuh cukup diberi **penanda teks** (⚠), bukan pertanyaan.
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
- **Semua dropdown memakai `src/components/DropdownCari.tsx`** (ada kotak pencarian; pengguna cukup mengetik sebagian teks, mis. "qura" menampilkan Quraisy ayat 1, 2, ...). Jangan memakai `<select>` biasa untuk daftar halaqah, santri, item, level, atau bidang.
- **Panel dropdown selalu melayang di lapisan tertinggi** (`LAPISAN_DROPDOWN = 60` di `DropdownCari`), karena panelnya dipindahkan ke `<body>` (portal) dan diposisikan sendiri. Jangan kembali ke `absolute z-30`: panel seperti itu terpotong oleh kartu/tabel/bingkai bergulir dan tertutup notifikasi. Halaman atau komponen baru tidak perlu mengurus lapisan ini — cukup memakai `DropdownCari`.
- **Pencarian dropdown mengutamakan nomor**: mengetik "88" atau "menyalin 88" langsung menampilkan "Kitabah · Menyalin - 88" di urutan pertama. Bila hasil terpotong, panel menulis "Menampilkan 60 dari N" — jangan menghapus keterangan itu.
- **Label item selalu memakai nama mata pelajaran di depan**: "Tahfidz · An Naba' - 40". Buku yang sama dipakai lebih dari satu mata pelajaran (mis. Juz 'Amma di Tilawah dan Kitabah) dengan urutan dan fokus berbeda, sehingga label mentah bisa sama. Aturan ini berlaku untuk halaman Input dan halaman lain yang menampilkan pilihan item.
- **Pengampu hanya ditawari halaqah yang diampu**: Masul, Musyrif/ah, dan Mudarris/ah hanya melihat halaqahnya di halaman Input (`hanyaHalaqahDiampu` di `src/lib/roles.ts`). Hanya Mudir/Admin mengisi semua halaqah. Database (RLS) tetap penjaga terakhir.
- **Jangan pernah mengambil daftar panjang dengan satu query tanpa batas**: Supabase mengembalikan maksimal 1.000 baris per permintaan. Pakai `ambilSemua` di `src/lib/ambil-semua.ts` atau `range` yang cukup besar.

## Batas keluaran perintah (wajib, perintah Mudir 26 November 2026)

- **Jangan pernah menampilkan berkas, tabel, atau JSON besar secara utuh di percakapan.**
  Ini pernah menyebabkan sesi mati karena galat **413 (request terlalu besar)**.
- Batasi keluaran: `head`, `tail`, `wc -l`, `grep -c`, atau ringkasan (jumlah per kelompok).
  Untuk `npm run db:sql -- --query`, pilih kolom yang perlu saja dan tambahkan `limit`.
- Keluaran besar (mis. sidik jari, hasil uji, dump) **simpan ke berkas** (`/tmp` atau
  `docs/qa/*.json`) lalu tampilkan ringkasannya (jumlah baris, beberapa contoh, kesimpulan).
- Jangan mencetak data santri, UUID panjang berderet, atau seluruh isi `change_log`.
- Bila butuh memeriksa isi berkas panjang, pakai `read` dengan `offset`/`limit` atau `grep`
  untuk bagian yang relevan, bukan seluruh berkas.

## Batas token sesi (perintah Mudir 27 November 2026)

- **Hentikan dan buat handover bila Total Tokens sesi mencapai 250.000** (angka sementara), JANGAN
  menunggu 50% dari 1.000.000. Sesi sebelumnya mati oleh galat **413 (request terlalu besar)** dari gateway,
  bukan karena kehabisan token model.
- Pantau angka **Total Tokens** di info sesi. Bila angka itu **tidak bisa dibaca sendiri** oleh agent,
  hentikan setiap **3-4 sub-tugas selesai**, commit + push + perbarui `docs/HANDOVER.md`, lalu beri tahu
  Mudir agar sesi dapat ditutup secara terkendali.

## Cara bekerja (aturan tetap)
- **Satu sub-tugas, satu commit kecil.** Setelah sub-tugas selesai: jalankan `npm run typecheck` dan `npm run build`,
  perbarui `docs/STATUS.md` dan `docs/HANDOVER.md`, lalu commit dan **push** ke `main`. Jangan menumpuk banyak perubahan dalam satu commit besar.
- **`docs/STATUS.md` adalah sumber kebenaran status.** Perbarui setiap sub-tugas selesai: status tahap, hasil build/tsc/uji, kondisi Supabase, deploy.
  Jangan menulis SELESAI untuk sesuatu yang belum dijalankan atau diuji; tulis **BELUM DIVERIFIKASI**.
- **Tulis hanya fakta yang sudah diperiksa sendiri** (baca kode, jalankan perintah, tanya database). Jangan mengarang angka.
- **`docs/HANDOVER.md`** diperbarui setiap sub-tugas selesai: posisi sekarang, langkah berikutnya yang berurutan, keputusan final, pertanyaan terbuka.
- **Jangan mengubah "Keputusan final"** di `docs/HANDOVER.md` bagian 3 tanpa persetujuan Mudir. Bila perlu diubah, tanya dulu dan catat persetujuannya.
- **Bila data atau aturan janggal atau tidak sinkron, berhenti dan tanya.** Jangan berasumsi, termasuk saat seed atau saat memperbaiki data.
  Catat temuan di bagian "Pertanyaan terbuka" (`docs/HANDOVER.md`) dan/atau `docs/DATA-NOTES.md`.
- **Tulis nama role selengkapnya** di kode, teks UI, dan dokumen: **Masul Al Quran**, **Masul Wasilah**, **Masul Ghayah**. Jangan menulis "masul" saja.
- **Repo publik:** jalankan `python scripts/check_repo_safety.py` sebelum setiap push. Jangan pernah menulis kunci, kata sandi, `DATABASE_URL`, atau data santri.
  Ingatkan Mudir bahwa repo harus dijadikan privat sebelum data asli dimuat.
- Jangan mengubah logika aplikasi saat hanya diminta memperbarui dokumentasi.

## Disiplin data dan uji (T6d3, perintah Mudir 25 November 2026)

- **Database lokal dan produksi adalah SATU Supabase.** Tidak ada salinan terpisah. Setiap uji yang MENULIS
  harus memulihkan barisnya **PERSIS** dan **lolos pemeriksaan sidik jari**.
- **Sidik jari database wajib:** `python scripts/qa/db_fingerprint.py --simpan <berkas.json>` sebelum dan
  sesudah setiap rangkaian uji, lalu `--banding <berkas.json>`. Jika hasilnya bukan "SAMA", rangkaian uji
  **GAGAL** dan penyebabnya harus dicari dan dilaporkan. Rujukan sidik jari resmi: `docs/qa/db_fingerprint_*.json`.
- **Uji yang menulis** (E2E, smoke, uji DB) hanya boleh menyentuh baris yang **dibuatnya sendiri**, menyimpannya
  lebih dulu, memulihkannya di blok `finally`, dan tidak menghapus/mengubah baris lama. Ingat: sejak T6d2
  menyimpan juga menimpa `entered_by`/`entered_at`, jadi jejak harus ikut dipulihkan.
- **Smoke produksi sebaiknya HANYA MEMBACA.** Menulis di produksi hanya bila dipaksa oleh keputusan, dan
  harus dengan pemulihan + sidik jari.
- **Seed ulang menghidupkan kembali data yang sudah dihapus Mudir.** Berkas seed membuka dengan `truncate`
  lalu mengisi semua yang ada di Excel. Setiap penghapusan data yang disetujui Mudir **wajib** punya skrip
  di `scripts/db/fixes/` (aman dijalankan ulang) dan uji penjaga yang gagal bila data itu muncul lagi.
- Uji banding Excel **penuh**: `python scripts/qa/compare_alquran_full_excel.py` (semua bulan, semua santri,
  kehadiran + capaian). Sampel tidak cukup.

## Perintah
```
npm install
npm run dev          # pengembangan
npm run typecheck    # wajib hijau sebelum selesai
npm run test         # uji aturan putaran (khatam/pengulangan)
npm run build        # wajib berhasil sebelum selesai
python scripts/check_repo_safety.py   # wajib lolos sebelum push
python scripts/qa/db_fingerprint.py --simpan X.json   # sebelum/sesudah uji yang menulis
python scripts/qa/db_fingerprint.py --banding X.json  # harus "SAMA"
npm run seed:build   # membangun supabase/seed/*.sql dari data/source/*.xlsx
npm run seed:users   # membuat akun dummy di Supabase Auth
npm run db:sql -- <file.sql>   # menjalankan SQL ke database (atau: -- --query "select ...")
```

## Definisi selesai untuk setiap tugas
- `npm run typecheck` dan `npm run build` berhasil.
- Untuk perubahan hak akses: jalankan pemeriksaan di `docs/SPEC.md` bagian "Pemeriksaan RLS" (login sebagai tiap role) dan tuliskan hasilnya.
- Ringkas apa yang diubah dan apa yang perlu dicek Mudir, dalam bahasa sederhana.
