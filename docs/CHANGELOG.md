# CHANGELOG - ringkasan perubahan per tahap

Disusun dari riwayat Git (diperiksa 23 November 2026). Tanggal memakai waktu komit lokal.
Ini ringkasan, bukan daftar komit lengkap; daftar lengkap ada di `git log`.

---

## 22 November 2026

### A-G - Persiapan dan rilis awal
- **A. Alat**: Node 26.13, npm 11.20, Python 3.12.16, git 2.39, gh 2.105. Tidak ada yang perlu dipasang.
- **B. Proyek**: kerangka Vite + React + TypeScript + Tailwind; `npm install`, `typecheck`, dan `build` hijau.
- **C. Git dan GitHub**: repo publik `pencapaiansantrikusafa-cpu/kusafa-app`; hook `.githooks/pre-commit` menjalankan pemeriksaan keamanan.
- **D. Supabase**: project `kusafa` (Singapore); 6 migrasi diterapkan; 18 tabel dengan RLS, 44 kebijakan.
- **E. Seed**: `build_seed.py` berhasil tanpa galat; data dummy dimuat (9 bidang, 158 buku, 10.954 item, 109 santri, 38 halaqah, 327 target, 2.036 capaian).
- **F. Uji lokal**: aplikasi tersambung ke Supabase.
- **G. Vercel**: situs produksi aktif.

### T2 - Login, kerangka, dan menu per role
- Halaman login bahasa Indonesia, profil dari tabel `profiles`, menu berbeda per role.
- Kerangka: header, menu samping yang bisa dilipat jadi ikon, bilah bawah untuk HP.

### T3 - Tabel capaian halaqah Al Qur'an
- Tabel per halaqah dan bulan: Lalu / Kini / Selisih per bidang, target bulanan, Hadir/HE.
- Sorotan merah muda untuk selisih di bawah target, kuning untuk Hadir kurang dari Hari Efektif, selalu disertai teks.
- Sel kosong tampil "belum diisi", bukan 0.
- Dropdown Tahun dan Bulan dipisah; nama musyrif/ah dan pengampu ditampilkan.
- Submenu Capaian (Al Qur'an, Ilmu Wasilah, Ilmu Ghayah) bisa diketuk, termasuk dalam mode ikon.

### T4 - Halaman satu santri
- Grafik dan tabel riwayat per rentang Semester 1 / Semester 2 / satu tahun.
- Grafik memakai posisi kumulatif; bulan kosong memutus garis (bukan 0).
- Tilawah, Tahfidz, dan Kitabah dalam satu kotak grafik; kehadiran di kotak terpisah.

### T5 - Input capaian Al Qur'an
- Formulir per santri: Tilawah, Tahfidz, Kitabah, izin/sakit/alpha, Hari Efektif khusus (Mudir/Admin saja), catatan.
- Simpan langsung ke database (`progress_entries`, `attendance`, `monthly_notes`); isi tersimpan tampil lagi saat dibuka.
- Putaran Tilawah: pilihan "khatam, mulai putaran baru" hanya untuk buku siklik dan bila putaran bulan lalu diketahui; putaran = putaran bulan lalu + 1.
- Konfirmasi "Capaian lebih kecil dari bulan lalu. Pengulangan atau khatam?" menahan simpan sampai dijawab (aplikasi tidak menebak).
- Peringatan bila bulan sesudahnya sudah terisi (putaran bulan berikutnya perlu ditinjau).
- Bulan terkunci: simpan dinonaktifkan dan pesan galat database ditampilkan apa adanya.
- Uji unit aturan putaran: `tests/putaran.test.mjs` (6 uji).

## 23 November 2026

### T5b - Perbaikan masukan
- Semua dropdown memakai `DropdownCari` (ada kotak pencarian).
- Halaqah yang ditawarkan mengikuti amanah (`hanyaHalaqahDiampu`).
- Notifikasi "Data belum lengkap - awal tahun sampai bulan berjalan": kolom musyrif/ah, ringkasan x/y terisi per bulan, saringan halaqah untuk Mudir/Admin/Masul Al Quran.
- Tabel notifikasi: kepala kolom beku dua arah (atas dan kiri).
- Submenu mode ikon kembali melayang dan menutupi isi halaman.

### T5 - Uji browser dengan akun pengampu
- Simpan sungguhan dari browser berhasil: 3 bidang tertulis ke `progress_entries` lalu tampil lagi setelah muat ulang. Data uji dihapus kembali.
- **Perbaikan:** ringkasan kehadiran menampilkan "izin 0, sakit 0, alpha 0" untuk bulan yang belum diisi. Kini "—" (kosong bukan 0).
- **Perbaikan:** item dropdown terduplikasi karena `useMemo` mengubah state (peringatan kunci ganda React). Kini memo murni.

### T5 - Perapian atas keputusan Mudir
- **Dropdown selalu melayang di atas semua isi**: panel dipindahkan ke `<body>` (portal) dengan `LAPISAN_DROPDOWN = 60`. Sebelumnya terpotong kartu/`rounded-xl` dan tertutup kotak notifikasi. Bila ruang di bawah sempit, panel terbuka ke atas.
- **Pencarian dropdown mengutamakan nomor**: "88" atau "menyalin 88" langsung menemukan "Menyalin - 88"; panel menulis "Menampilkan 60 dari N".
- **Label item memakai nama mata pelajaran**: "Tahfidz · An Naba' - 40".
- **Dialog konfirmasi memakai teks dropdown**, bukan angka posisi.
- **Konfirmasi hanya untuk bidang yang diubah**; bidang yang sudah mundur tetapi tidak disentuh diberi penanda ⚠. Selisih dibaca dari `v_monthly_report`.
- **Data Ramadhan dirapikan**: 7 baris kehadiran tanpa capaian dihapus (presensi 606 → 599).

### Dokumentasi
- Ditambahkan `docs/STATUS.md` (sumber kebenaran status) dan `docs/FILE-MAP.md` (peta kode dan database).
- `docs/HANDOVER.md`, `docs/DATA-NOTES.md`, `README.md`, dan `AGENTS.md` disusun ulang agar sesuai kondisi nyata.
- **Koreksi angka**: jumlah capaian dummy yang mundur dari bulan sebelumnya adalah **69** (Tahfidz 27, Kitabah 26, Tilawah 16), bukan 43 seperti tertulis pada catatan sebelumnya.

---

## Belum dikerjakan
T6 (tabel dan input Wasilah/Ghayah), T7 (target dinamis), T8 (kurikulum, halaqah, santri, kalender, Hari Efektif & kunci bulan), T9 (QA otomatis), T10 (hapus data dummy, repo privat).
