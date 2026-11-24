# HANDOVER - serah terima untuk sesi berikutnya

Diperbarui: **24 November 2026** (pra-T6 langkah [3/5] dan [4/5]).
Commit terakhir yang sudah ada di remote sebelum commit langkah [4/5]: `e9e292c`.
Baca berurutan: `AGENTS.md` → `docs/SPEC.md` → `docs/STATUS.md` → berkas ini.
`docs/STATUS.md` adalah sumber kebenaran kondisi nyata; berkas ini menjelaskan **apa yang harus dikerjakan berikutnya**.
Jangan menulis rahasia (kata sandi, kunci, token) atau data santri asli di berkas ini.

---

## 1. Posisi sekarang

**T5 selesai** (termasuk T5b dan perbaikan 23 Nov 2026). **Pra-T6 langkah [1]-[4] selesai** pada 24 Nov 2026. **T6 belum dimulai** dan menunggu jawaban Mudir atas laporan audit.
Build/tsc/uji hijau (lihat STATUS bagian 2, 2a, dan 2b).

Yang berfungsi hari ini:
- Login dan menu per role (Mudir, Admin, Masul Al Quran, Masul Wasilah, Masul Ghayah, Musyrif/ah, Mudarris/ah).
- Tabel capaian Al Qur'an per halaqah dan bulan (Lalu/Kini/Selisih, target, Hadir/HE).
- Halaman satu santri (grafik + riwayat).
- Input capaian Al Qur'an: simpan ke database, putaran khatam/pengulangan, kehadiran, catatan, notifikasi data belum lengkap.
- Notifikasi **"santri belum punya halaqah"** per domain (perluasan kotak "data belum lengkap"); lihat `docs/SPEC.md` bagian 9.
- Deploy Vercel yang benar-benar tersambung ke Supabase (diuji 23 Nov 2026).

Yang **belum** ada sama sekali: tabel & input Wasilah/Ghayah (T6), target dinamis (T7), semua layar pengelolaan termasuk **Hari Efektif** dan **penugasan halaqah** (T8), uji otomatis dan QA (T9), pembersihan data dummy + repo privat (T10).

---

## 2. Langkah berikutnya (kerjakan berurutan)

> **Jangan mulai T6 sebelum Mudir menjawab laporan pra-T6.** Bila diizinkan, mulai dari Langkah 1 di bawah.

### Langkah 1 - mulai T6: tabel dan input Wasilah serta Ghayah
1. Baca `docs/CATATAN-TAHAPAN.md` bagian T6 dan `docs/SPEC.md` §2, §5.6.
2. `TabelCapaian.tsx` masih menampilkan "dikerjakan pada T6" untuk Wasilah/Ghayah. Ganti dengan tabel sungguhan: per mata pelajaran tampil **Capaian bulan lalu, Capaian bulan ini, Selisih**, lalu tabel anggota (Nama, Hadir/HE, Izin, Sakit, Alpha, Catatan).
3. Input Wasilah/Ghayah: **satu kali per halaqah dan mata pelajaran**, disalin ke semua anggota aktif saat disimpan. Perubahan anggota sesudahnya tidak boleh mengubah baris lama.
4. Halaman Input harus menyaring halaqah sesuai amanah dengan cara yang sama seperti Al Qur'an (`hanyaHalaqahDiampu()` di `src/lib/roles.ts`).
5. `KotakBelumLengkap.tsx` perlu menerima `domain` dan nama pengampu sesuai domain: **Wasilah** memakai nama pengampu per mata pelajaran, **Ghayah** memakai muallim/ah + pendamping.
6. Definisi "lengkap" = semua bidang aktif domain itu terisi (Wasilah: Baca, Tulis, Sirah, Hisab; Ghayah: Adab dan Iman, Aqidah dan Fiqih), sama seperti Al Qur'an.

### Langkah 2 - T7 target dinamis
- Bulan berlaku `effective_month_id`; target lama tetap untuk bulan sebelumnya.
- Status `diajukan` → hanya `disetujui` yang dipakai.
- Masul Al Quran hanya menyetujui domain Al Qur'an; Masul Wasilah hanya Wasilah; Masul Ghayah hanya Ghayah. Mudir/Admin semua domain.
- Target bulanan Al Qur'an = target harian × Hadir, boleh pecahan, **dihitung database**.

### Langkah 3 - T8 pengelolaan (paling mendesak: Hari Efektif)
- Layar **Hari Efektif per bulan per domain** + **kunci bulan**. Saat ini hanya bisa lewat SQL/dashboard, dan hanya domain `alquran` bulan 1-7 yang terisi.
- Pertimbangkan penanda "bulan berjalan" yang eksplisit; sekarang notifikasi menyimpulkan dari Hari Efektif yang terisi.
- Kelola item: `resequence_subject` (menolak Al Qur'an), `reorder_items`. Tampilkan peringatan bahwa menyisipkan item mengubah selisih lama.
- Hari Efektif khusus santri hanya Mudir/Admin (sudah dijaga trigger `attendance_guard_override`).
- Tambah tahun ajaran lewat `create_academic_year`.

### Langkah 4 - T9 dan T10
- T9: jadikan uji RLS manual (pernah dilakukan, lihat bagian 5) sebagai uji tetap; uji tampilan HP; uji selisih lintas buku dan putaran.
- T10: hapus data dummy, jadikan repo **privat**, selesaikan kerentanan npm, pastikan `ambilSemua` tetap dipakai.

---

## 3. Keputusan final - jangan diubah tanpa persetujuan Mudir

### Aturan bisnis
1. **Hadir dihitung aplikasi/database**: Hadir = Hari Efektif − (izin + sakit + alpha). Tidak diisi manual.
2. **Hari Efektif** sama untuk semua santri dalam satu domain dan bulan, bisa berbeda antar domain. Santri baru (mis. NIS berawalan 1447) boleh punya Hari Efektif khusus lewat `attendance.effective_days_override`, hanya Mudir/Admin.
3. **Target bersifat dinamis** (bisa diubah). Target bulanan = target harian × Hadir, **boleh pecahan**.
4. **Capaian boleh mundur** (pengulangan atau khatam lalu mulai putaran baru). Selisih negatif ditampilkan apa adanya, bukan galat dan bukan 0.
5. **Bulan yang belum diinput kosong, bukan 0** di tabel maupun grafik.
6. **Putaran** naik 1 hanya lewat pilihan eksplisit "khatam"; khatam = putaran bulan lalu + 1, bukan angka tetap.
7. **Konfirmasi "pengulangan atau khatam" hanya untuk bidang yang diubah pada kunjungan itu.** Bidang yang sudah mundur tetapi tidak disentuh diberi penanda ⚠, bukan pertanyaan.
8. **Item kurikulum yang sudah dipakai tidak dihapus**, hanya `is_active = false`.
9. **Notifikasi "data belum lengkap"** memeriksa bulan dari awal tahun sampai bulan berjalan; penandanya `month_domain_settings.effective_days` terisi (opsi B, 23 Nov 2026).
10. **Bulan 0 (Data Awal) adalah catatan awal, bukan bulan efektif dan bukan bulan target.** Ia membandingkan Syawwal tahun pertama; tahun berikutnya Syawwal membandingkan dengan Ramadhan tahun sebelumnya. `month_is_open(bulan 0, domain) = false`; form input menyembunyikan bulan 0; Admin/Mudir tetap bisa mengisi manual. Aturan lengkap di `docs/SPEC.md` bagian 4a.
11. **Santri yang tidak ikut semua halaqah adalah keadaan sah, bukan data rusak.** NIS `1447.dummy-nis.023` (tanpa Ghayah) dan `1447.dummy-nis.024` (hanya Al Qur'an) **dibiarkan** sebagai kasus uji resmi. Jangan menambah/mengarang baris. Di domain yang tidak diikuti, santri tidak ditampilkan (bukan 0) dan semua view/fungsi tetap jalan.
12. **Hari Efektif Rabiul Awwal = 19 hari** (bukan 3), keputusan Mudir 24 Nov 2026. Database sudah dikoreksi lewat SQL; **Excel sumber masih 3** dan harus diperbaiki Mudir agar seed ulang tidak mengembalikan 3.
13. **Notifikasi "santri belum punya halaqah" per domain** (24 Nov 2026): Mudir/Admin melihat semua domain; Masul Al Quran/Wasilah/Ghayah hanya domainnya; Musyrif/Mudarris tidak; anon ditolak. Implementasi: fungsi `students_without_halaqah`(/_count) (migrasi `000009`), definisi "punya halaqah" = keanggotaan aktif pada halaqah aktif di tahun ajaran aktif. Penugasan halaqah adalah T8.

### Struktur teknis
1. Migrasi yang sudah dijalankan **tidak boleh diubah**; perubahan skema = `20261121000007_...` dan seterusnya.
2. `hijri_months` **tidak punya** `hijri_year`; tahun ada di `academic_years` (relasi `academic_years!inner(hijri_year)`).
3. `month_no`: 0 = Data Awal (hanya tahun pertama), 1 = Syawwal ... 12 = Ramadhan.
4. **Jangan menghitung selisih, target, atau kehadiran di React.** Baca dari `v_monthly_report` dan `v_attendance`.
5. **Semua dropdown memakai `DropdownCari`** (`absolute <select>` dilarang). Panelnya dilayangkan ke `<body>` dengan `LAPISAN_DROPDOWN = 60`; **jangan** dikembalikan ke `absolute z-30`.
6. **Tahun dan Bulan selalu dua dropdown terpisah** (`PemilihTahunBulan`).
7. **Dropdown halaqah selalu memuat pengampu** (`PemilihHalaqah`): "HLQ-PA-1 - Ust. Fulan 1".
8. **Label item memakai nama mata pelajaran di depan**: "Tahfidz · An Naba' - 40".
9. **Setiap query yang bisa > 1.000 baris wajib memakai `ambilSemua`** (`src/lib/ambil-semua.ts`).
10. Frontend hanya memakai `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`. Kunci service role dan `DATABASE_URL` hanya untuk skrip lokal.
11. Tata letak: menu samping `z-30`, submenu mode ikon melayang `z-50`, isi halaman `isolate`, panel dropdown `60`.
12. Supabase CLI 3.2.0: perintah ke project online butuh `--remote`.

### Istilah dan nama
- Tulis role lengkap: **Masul Al Quran, Masul Wasilah, Masul Ghayah** (jangan "masul" saja).
- Nama bidang: Tilawah, Tahfidz, Kitabah, Baca, Tulis, Sirah, **Hisab** (bukan "Hitung"), Adab dan Iman, Aqidah dan Fiqih.
- Seluruh teks antarmuka berbahasa Indonesia.

---

## 4. Pertanyaan terbuka (menunggu jawaban Mudir)

1. **Excel Hari Efektif Rabiul Awwal masih 3.** Database sudah 19; Mohon perbaiki `BZ5:B113` di `data/source/3-Al Quran (halaqah dan pencapaian).xlsx` sheet `Halaqah Al Quran dan pencapaian` menjadi 19 agar seed ulang tidak mengembalikan 3.
2. **Pendaftaran publik Supabase Auth masih aktif.** Mohon matikan di Dashboard (Authentication → Providers → Email → "Allow new users to sign up").
3. **Dropdown item dibatasi 60 hasil.** Sudah bisa dicari dengan nomor. Apakah perlu tombol "muat lebih banyak"?
4. **Level 6 (4 santri)** belum punya pengampu dan jadwal. Apa yang harus ditampilkan?
5. **69 capaian data dummy mundur** dari bulan sebelumnya (Tahfidz 27, Kitabah 26, Tilawah 16). Disepakati dibiarkan karena dummy. Konfirmasi ulang sebelum T9, karena uji QA akan sering bertemu angka ini.
6. **Isi Data Awal (252 capaian)** dipertahankan untuk sekarang. Apakah dikosongkan saat data asli dimuat? Keputusan ditunda ke T10.
7. **Repo masih publik.** Harus dijadikan privat sebelum data asli dimuat (T10).
8. **Boleh mulai T6?** Pra-T6 langkah [1]-[4] selesai dan dilaporkan; T6 menunggu jawaban Mudir.

---

## 5. Cara menjalankan, menguji, deploy

```bash
npm install
npm run dev            # http://localhost:5173 (atau port berikutnya bila terpakai)
npm run typecheck      # wajib hijau
npm run test           # 6 uji aturan putaran
npm run build          # wajib berhasil, hasil di dist/
python scripts/check_repo_safety.py   # wajib lolos sebelum push
git config core.hooksPath .githooks   # sekali saja, mengaktifkan hook keamanan
python scripts/qa/run_pre_t6_db_tests.py   # uji DB pra-T6 (tulis dalam ROLLBACK)
python scripts/qa/test_no_halaqah.py       # uji santri tanpa halaqah (tulis dalam ROLLBACK)
python scripts/qa/test_students_without_halaqah.py   # uji notifikasi "belum punya halaqah" (13 uji)
```

Data dan database (membaca `DATABASE_URL` dari `.env.local`, tidak pernah dicetak):

```bash
python scripts/db/run_sql.py --query "select count(*) from public.students"
python scripts/db/run_sql.py supabase/seed/01_curriculum.sql   # DESTRUKTIF, hanya data uji
npm run seed:build     # bangun seed dari data/source/*.xlsx
npm run seed:users     # buat akun dummy di Supabase Auth
python scripts/seed/smoke_login.py    # uji login tanpa browser
```

Akun dummy: `<nama>@kusafa.test`; kata sandi ada di `scripts/seed/output/users.csv` (**tidak di-commit**).
Contoh akun untuk uji: Mudir, Admin, Masul Al Quran 1/2, Masul Wasilah, Masul Ghayah, Ust. Fulan 1 (Musyrif/ah HLQ-PA-1), dst.

### Uji RLS manual (pola)
Jalankan dalam transaksi lalu `rollback`, meniru sesi login:
```sql
select set_config('request.jwt.claims', '{"sub":"<profil_id>","role":"authenticated"}', true);
select set_config('role','authenticated',true);
-- coba insert/update; tutup dengan rollback();
```
Uji yang pernah lolos (23 Nov 2026): Musyrif A **ditolak** menulis capaian, kehadiran, dan catatan pada halaqah Musyrif B.

### Deploy
```bash
npx vercel ls          # daftar deployment (baca saja)
npx vercel --prod      # deploy manual (push ke main juga memicu deploy otomatis)
npm run build && # unggah isi dist/ ke public_html (cPanel, .htaccess ikut tersalin)
```
Environment Vercel hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`.

### Jebakan yang sudah pernah menggigit
- Batas **1.000 baris** per permintaan Supabase: tanpa `ambilSemua`, data terpotong diam-diam.
- Kueri item harus **per buku** lalu digabung; `ORDER BY seq` sendirian menghasilkan urutan acak karena `seq` mulai dari 1 di tiap buku.
- `v_monthly_report` tanpa filter bisa kena *statement timeout*; selalu filter `halaqah_id` + `month_id`.
- Jangan memakai `useMemo` yang mengubah state (pernah menyebabkan item dropdown ganda).
- Login di situs produksi butuh beberapa detik pada kunjungan pertama; jangan buru-buru menyimpulkan gagal.
