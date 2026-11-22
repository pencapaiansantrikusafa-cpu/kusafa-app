# SPEC - aturan aplikasi KUSAFA

Sumber lengkap: dokumen "KUSAFA - System Design" dan "Pembuatan Aplikasi KUSAFA". Ringkasan yang mengikat ada di sini.

## 1. Tujuan
Memantau capaian santri per bulan Hijriyah di tiga domain, membandingkannya dengan bulan sebelumnya dan target, dan menampilkan kehadiran.
Kurikulum, halaqah, pengampu, dan dropdown harus bisa diubah dari aplikasi tanpa mengubah kode.

## 2. Domain dan halaqah
| Domain | Bidang | Halaqah | Input capaian |
|---|---|---|---|
| Al Qur'an (`alquran`) | Tilawah (halaman), Tahfidz (baris), Kitabah (halaman) | 14 halaqah: HLQ-PA-1..7 (Putra), HLQ-PI-1..7 (Putri); satu musyrif/ah | Individual per santri |
| Ilmu Wasilah (`wasilah`) | Baca, Tulis, Sirah, Hisab | **Satu halaqah = satu Level.** Tiap mata pelajaran punya pengampu, hari, dan sesi KBM sendiri (Jadwal Ilmu Wasilah). Halaqah boleh belum punya pengampu dan jadwal (Level 6) | Satu kali per halaqah dan mata pelajaran, otomatis disalin ke tiap anggota |
| Ilmu Ghayah (`ghayah`) | Adab dan Iman (Asmaul Husna, Matan Ahsanul Akhlaq), Aqidah dan Fiqih (Matan Safinatun Najah) | Kelompok usia, Putra/Putri; satu muallim + pendamping; semua asatidzah boleh mengajar | Sama dengan Wasilah |

Muhasabah bukan bidang kurikulum; hanya catatan (`monthly_notes`). Level hanyalah label (`student_levels`); posisi belajar dicatat per bidang. Sistem mulazamah: santri pindah ke tahap berikutnya begitu tuntas, tanpa menunggu semester dan tanpa ganti nama level.

## 3. Role dan hak akses
Role: `mudir`, `admin`, `masul_alquran` (Masul Al Quran), `masul_wasilah` (Masul Wasilah), `masul_ghayah` (Masul Ghayah), `musyrif` (Musyrif/ah), `mudarris` (Mudarris/ah), `wali` (disiapkan, belum aktif).

| Aksi | Mudir, Admin | Masul Al Quran / Masul Wasilah / Masul Ghayah | Musyrif/ah, Mudarris/ah |
|---|---|---|---|
| Melihat semua halaqah dan santri | Ya | Ya | Ya |
| Input capaian, catatan, kehadiran | Semua halaqah, kapan saja | Halaqah yang diampu | Halaqah yang diampu |
| Mengajukan target | Ya | Ya | Ya, halaqah yang diampu |
| Menyetujui target | Ya | Hanya domain masing-masing | Tidak |
| Hari Efektif, kunci bulan, pengguna | Ya | Tidak | Tidak |
| Kurikulum, halaqah, pengampu | Ya | Hanya domain masing-masing | Tidak |
Pengampu hanya bisa mengisi bulan yang belum terkunci. Mudir dan Admin bisa mengubah bulan terkunci. Hari Efektif khusus santri hanya Mudir/Admin.

## 4. Model data
Skema ada di `supabase/migrations/`. Inti:
- Kalender: `academic_years`, `hijri_months` (`month_no` 0 = Data Awal hanya di tahun pertama pemakaian, diisi manual Admin; 1 = Syawwal ... 12 = Ramadhan; semester 1 = bulan 1-6, semester 2 = bulan 7-12), `month_domain_settings` (Hari Efektif per bulan per domain, kunci bulan).
- Kurikulum: `subjects` > `books` > `curriculum_items` (`value`, `seq`, `label`, `detail`).
- Halaqah: `halaqahs`, `halaqah_subjects`, `halaqah_teachers` (pengampu per mata pelajaran, hari, sesi), `halaqah_members`.
- Capaian: `progress_entries` (satu baris per santri, bidang, bulan; `putaran`), `attendance` (izin, sakit, alpha), `monthly_notes`, `targets`.
- Laporan: `v_monthly_report` (selisih, hadir, target bulanan, `below_target`, `attendance_short`), `v_attendance`.

## 4b. Pengelolaan dropdown (harus tetap bisa diubah setelah aplikasi jadi)
Layar kelola kurikulum (tugas T8) harus bisa menambah, mengubah, mengurutkan ulang, dan menonaktifkan bidang, buku, dan item, oleh Mudir/Admin atau Masul Al Quran / Masul Wasilah / Masul Ghayah sesuai domain.
- Item yang sudah dipakai capaian tidak dihapus, hanya dinonaktifkan.
- **Wasilah dan Ghayah**: nilai = nomor urut baris. Setelah menambah, menyisipkan, atau memindah item, panggil `resequence_subject(subject_id)`; untuk mengurutkan ulang satu buku panggil `reorder_items(book_id, daftar_semua_id_item_urut_baru)`. Menyisipkan item di tengah buku menambah jarak antara item sebelum dan sesudahnya, jadi selisih lama yang melintasi titik itu ikut berubah. Tampilkan peringatan ini sebelum menyimpan.
- **Al Qur'an**: kolom `value` diisi manual oleh pengelola dan tidak dihitung ulang otomatis; `resequence_subject` menolak bidang Al Qur'an. Tampilkan peringatan bila nilai tumpang tindih atau turun di tengah surat/buku.
- Buku baru di Wasilah/Ghayah otomatis masuk di urutan paling akhir bidangnya (atur `stage_order`/`sort_order`, lalu `resequence_subject`).

## 5. Aturan perhitungan
1. **Posisi** = `curriculum_items.value + books.value_offset + (putaran - 1) * cycle_length` (fungsi `item_position`).
   Al Qur'an: `value` dari file dropdown. Iqro' (jilid 1-6) dijajarkan ke Karima lewat `value_offset`. Wasilah/Ghayah: `value` = nomor urut baris dalam buku, `value_offset` = jumlah item buku-buku sebelumnya di bidang yang sama.
2. **Selisih** = posisi bulan ini - posisi bulan pembanding. Bulan pembanding otomatis bulan sebelumnya (Syawwal dibandingkan dengan Ramadhan tahun lalu; di awal pemakaian, Admin mengisi Data Awal manual). Pengguna hanya memilih bulan yang dilihat.
3. **Putaran Tilawah** (Al Qur'an, 604 halaman). Form input punya pilihan "khatam, mulai putaran baru" yang menaikkan `putaran`. Tanpa pilihan itu, capaian yang lebih kecil dari bulan lalu adalah pengulangan (selisih negatif). Aplikasi tidak menebak.
4. **Kehadiran**: Hadir = Hari Efektif - (izin + sakit + alpha). Hari Efektif sama untuk semua santri dalam satu domain dan bulan, bisa berbeda antar domain. Pengecualian: santri yang masuk terlambat punya Hari Efektif khusus (`attendance.effective_days_override`), hanya diisi Mudir/Admin (dijaga trigger); bila ada, angka itu dipakai. Di tabel tampil sebagai Hadir/HE santri itu.
5. **Target**: Al Qur'an individual dan harian; target bulanan = target harian x Hadir. Wasilah/Ghayah target untuk halaqah dan bulanan. Target individu didahulukan dari target halaqah. Status: diajukan, disetujui, ditolak. Hanya yang disetujui dipakai.
6. **Tampilan halaqah Wasilah dan Ghayah**: per mata pelajaran tampil Capaian Bulan Lalu, Capaian Bulan Ini, Selisih; lalu tabel anggota: Nama Santri, Hadir/HE, Izin, Sakit, Alpha, Catatan.

## 6. Alur kerja
- Input bulanan: Admin isi Hari Efektif > pengampu isi capaian, kehadiran, catatan > sistem menghitung > Admin/Mudir mengunci bulan.
- Target: pengampu mengajukan > Masul Al Quran / Masul Wasilah / Masul Ghayah (sesuai domain), Mudir, atau Admin menyetujui.
- Kurikulum: tambah/ubah/nonaktifkan; dropdown mengikuti otomatis.
- Pergantian tahun ajaran: buat tahun baru (`create_academic_year`), salin halaqah dan anggota lalu sesuaikan; posisi santri berlanjut (tidak direset).

## 7. Ditunda
Login wali santri (tabel `guardians` sudah ada, kebijakan RLS belum dibuat). Hak akses role `wali` tidak ada sampai diaktifkan.

## 8. Pemeriksaan RLS (jalankan setelah mengubah hak akses)
Login sebagai: Mudir, Admin, Masul Al Quran, Masul Wasilah, Masul Ghayah, Musyrif/ah, Mudarris/ah. Untuk tiap role periksa:
- Bisa membaca semua halaqah dan santri.
- Musyrif/ah hanya bisa menulis capaian santri di halaqah Al Qur'an yang diampu; ditolak di halaqah lain.
- Mudarris/ah hanya bisa menulis mata pelajaran yang diampunya di Level tersebut.
- Pengampu ditolak menulis pada bulan terkunci; Mudir/Admin diterima.
- Pengampu tidak bisa menyetujui target; Masul sesuai domain bisa, Masul domain lain tidak.
- Hari Efektif hanya bisa diubah Admin/Mudir.
