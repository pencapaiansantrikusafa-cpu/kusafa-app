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
| Input capaian, catatan, kehadiran | Semua halaqah, kapan saja | **Ilmu Wasilah/Ilmu Ghayah:** semua halaqah di domainnya (penanggung jawab domain). **Al Qur'an:** halaqah yang diampu | Halaqah yang diampu |
| Mengajukan target | Ya | Ya | Ya, halaqah yang diampu |
| Menyetujui target | Ya | Hanya domain masing-masing | Tidak |
| Hari Efektif, kunci bulan, pengguna | Ya | Tidak | Tidak |
| Kurikulum, halaqah, pengampu | Ya | Hanya domain masing-masing | Tidak |
Pengampu hanya bisa mengisi bulan yang belum terkunci. Mudir dan Admin bisa mengubah bulan terkunci. Hari Efektif khusus santri hanya Mudir/Admin.

**Catatan (keputusan Mudir 25 November 2026, T6b):** Masul Wasilah dan Masul Ghayah adalah **penanggung jawab domain**, bukan hanya pengampu mata pelajaran. Mereka boleh menulis capaian **semua halaqah di domainnya** walau tidak tercatat di `halaqah_teachers`. Ditegakkan oleh policy `progress_insert_masul_domain` / `progress_update_masul_domain` (khusus `wasilah` dan `ghayah`) dan oleh `wasilah_can_write`. Yang **tidak** berubah: mereka tetap tidak boleh menyentuh domain lain, tetap tidak boleh menulis pada bulan terkunci, dan **Masul Al Quran tetap "halaqah yang diampu"** (belum ada keputusan untuk menyamakan).

## 4. Model data
Skema ada di `supabase/migrations/`. Inti:
- Kalender: `academic_years`, `hijri_months` (`month_no` 0 = Data Awal hanya di tahun pertama pemakaian, diisi manual Admin; 1 = Syawwal ... 12 = Ramadhan; semester 1 = bulan 1-6, semester 2 = bulan 7-12), `month_domain_settings` (Hari Efektif per bulan per domain, kunci bulan).

- Kurikulum: `subjects` > `books` > `curriculum_items` (`value`, `seq`, `label`, `detail`).
- Halaqah: `halaqahs`, `halaqah_subjects`, `halaqah_teachers` (pengampu per mata pelajaran, hari, sesi), `halaqah_members`.
- Capaian: `progress_entries` (satu baris per santri, bidang, bulan; `putaran`), `attendance` (izin, sakit, alpha), `monthly_notes`, `targets`.
- Laporan: `v_monthly_report` (selisih, hadir, target bulanan, `below_target`, `attendance_short`), `v_attendance`.

### 4a. Aturan bulan 0 (Data Awal) - keputusan final 24 November 2026
`hijri_months` sengaja berisi **13 baris** setiap tahun pertama pemakaian: `month_no` 0 s.d. 12.

- **Bulan 0 adalah catatan awal, bukan bulan efektif.** Ia dipakai sebagai catatan awal santri baru dan pembanding Syawwal pada tahun pertama. Bulan 0 **tidak** punya Hari Efektif, **tidak** dihitung sebagai bulan berjalan oleh notifikasi "data belum lengkap", dan **tidak** menghasilkan target bulanan (Hadir dan Hari Efektifnya kosong, jadi target bulanan kosong).
- **Bulan 1-12 = Syawwal s.d. Ramadhan.** Ini bulan efektif untuk input, target, kehadiran, dan laporan.
- **Pembanding Syawwal mengikuti aturan ini:**
  - Tahun pertama (ada bulan 0): Syawwal dibandingkan dengan **bulan 0 (Data Awal)**.
  - Tahun berikutnya (tidak dibuat bulan 0): Syawwal dibandingkan dengan **bulan 12 (Ramadhan) tahun sebelumnya**. Santri lama memakai bulan terakhir tahun sebelumnya sebagai catatan awal.
- **`v_months_ordered`** memberi `ord = hijri_year * 100 + month_no` dan `prev_month_id = lag(...)`. Bulan 0 punya `prev_month_id` kosong; Syawwal tahun pertama memakai bulan 0; Syawwal tahun berikutnya memakai Ramadhan tahun sebelumnya.
- **`v_monthly_report` / `v_monthly_report_base`**: baris bulan 0 boleh ada (capaian awal), tetapi `selisih`, `hadir`, `effective_days`, dan `target_monthly` bernilai kosong. Baris itu bukan bulan efektif dan bukan target bulanan; hanya pembanding.
- **Target boleh berlaku dari bulan 0.** `targets.effective_month_id` boleh menunjuk bulan 0 sebagai titik mulai ("berlaku dari Data Awal"), tetapi bulan 0 sendiri tidak menghitung target bulanan karena tidak punya kehadiran.
- **Bulan 0 bukan bulan input staf.** `month_is_open(bulan 0, domain)` = **false** (migrasi `20261121000008_month_zero_not_open.sql`). Form input menyembunyikan bulan 0 (`tanpaDataAwal`). Admin/Mudir tetap dapat mengisi Data Awal secara manual karena policy memakai `is_full_access()` lebih dahulu.

#### 4a-1. Tahun kedua dan seterusnya — Data Awal otomatis (keputusan Mudir 24 November 2026)

- **Hanya tahun pertama pemakaian** yang memakai bulan 0 "Data Awal" dan diisi manual oleh **Admin/Mudir**.
- **Mulai tahun ajaran kedua, Data Awal TIDAK diisi manual.** Nilainya otomatis diambil dari capaian **bulan terakhir tahun sebelumnya — Ramadhan** (bulan 12). Aturan ini berlaku juga bagi santri tahun pertama yang naik ke tahun kedua.
- `create_academic_year(hijri_year, name, with_baseline)` **tidak boleh** membuat/meminta bulan 0 untuk tahun kedua: panggil dengan `with_baseline = false` (12 bulan, `month_no` 1..12). Tidak ada layar yang meminta Data Awal santri lama.
- Konsekuensinya: **Syawwal tahun kedua dibandingkan dengan Ramadhan tahun sebelumnya** lewat `v_months_ordered.prev_month_id`, tanpa baris Data Awal baru.
- Bukti uji (transaksi + ROLLBACK): `scripts/qa/test_data_awal_tahun_kedua.py` — 5/5 lulus 24 Nov 2026. Meliputi: 1448 hanya 12 bulan tanpa bulan 0; `prev_month_id` Syawwal 1448 = Ramadhan 1447; `selisih` di `v_monthly_report` = pos(Syawwal 1448) − pos(Ramadhan 1447) untuk santri yang naik tahun; tidak ada baris Data Awal 1448.

#### 4a-2. Hari Efektif kecil = SAH (koreksi Mudir 24 November 2026)

- **`month_domain_settings.effective_days` boleh kecil karena libur.** Rabiul Awwal 1447 domain Al Qur'an = **3 hari** adalah **benar** (libur sekitar dua pekan lebih); Syawwal = 4 hari (bulan pembuka tahun ajaran).
- Nilai 19 untuk Rabiul Awwal pernah diterapkan keliru pada 24 Nov 2026 dan **sudah dikembalikan ke 3** (`scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql`). Skrip lama 3→19 **dibatalkan** dan diberi penghenti keras.
- Akibatnya Hadir bulan itu = 3 − (izin+sakit+alpha), jadi **1–3** untuk data dummy, bukan 17–19.
- Bukti: `scripts/qa/compare_rabiul_awwal_excel.py` — 7/7 PASS, HE/Hadir/absensi/label+posisi capaian cocok dengan Excel untuk seluruh 109 santri.
- Jangan menandai nilai kecil sebagai kesalahan dan jangan mengubahnya tanpa konfirmasi Mudir (lihat `AGENTS.md`).

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
   **Nilai Hari Efektif yang kecil adalah SAH** bila karena libur panjang; contoh yang sudah final: **Rabiul Awwal 1447 = 3 hari** (libur ~2 pekan lebih) dan **Syawwal 1447 = 4 hari** (bulan pembuka tahun ajaran). Jangan menandainya "janggal", jangan menaikkannya, dan jangan mengubahnya tanpa konfirmasi Mudir. Acuan angkanya adalah Excel sumber (`3-Al Quran (halaqah dan pencapaian).xlsx`, blok `HE` per bulan).
5. **Target**: Al Qur'an individual dan harian; target bulanan = target harian x Hadir. Wasilah/Ghayah target untuk halaqah dan bulanan. Target individu didahulukan dari target halaqah. Status: diajukan, disetujui, ditolak. Hanya yang disetujui dipakai.
6. **Tampilan halaqah Wasilah dan Ghayah**: per mata pelajaran tampil Capaian Bulan Lalu, Capaian Bulan Ini, Selisih; lalu tabel anggota: Nama Santri, Hadir/HE, Izin, Sakit, Alpha, Catatan.
   Dilaksanakan di `src/pages/TabelWasilah.tsx` (T6a). Yang ditampilkan hanya mata pelajaran yang **ditetapkan untuk halaqah itu** (`halaqah_subjects`), bukan seluruh bidang domain; halaqah tanpa penetapan (mis. Level 6 Wasilah) menampilkan pesan, bukan tabel kosong. Anggota hanya dari `halaqah_members` dengan `left_on is null`. Semua angka (posisi, selisih, Hadir, Hari Efektif, target) dibaca dari `v_monthly_report`/`v_attendance`. Bulan yang belum diinput tampil "belum diisi", bukan 0.

## 5b. Tab domain di halaman Capaian dan Input (T6d, 25 November 2026)

- Halaman **Capaian** (`/capaian/alquran`, `/capaian/wasilah`, `/capaian/ghayah`) dan halaman **Input**
  menampilkan **tab domain** di bagian atas: **Al Qur'an, Ilmu Wasilah, Ilmu Ghayah** (urutan baku
  `DOMAIN_URUT`). Satu komponen bersama: `src/components/TabDomain.tsx`.
- **Tab aktif tercermin di URL.** Klik tab menuju rute domain itu; muat ulang dan tombol kembali
  membuka domain yang sama.
- **Visibilitas tab mengikuti hak lihat yang sudah ada, bukan aturan baru:** di Capaian ketiga domain
  dapat dilihat semua staf (`progress_read`/`halaqahs_read`/`students_read` = `is_staff()`); di Input,
  tab mengikuti hak tulis (`domainInputUntuk`). Bila kelak Capaian dibatasi per domain, ubah
  `domainCapaianUntuk` dan RLS bersama-sama.
- **Menu Capaian tidak lagi ber-submenu** di menu samping/bilah bawah; tab menggantikannya.
- **Responsif:** HP 360 px - tiga tab dibagi rata, tinggi sentuh minimal 44 px, tanpa geseran ke samping;
  desktop - tombol sebaris.

## 5c. Input Ilmu Wasilah dan Ilmu Ghayah (T6b)

- **Sekali per halaqah x mata pelajaran**, disalin database ke **semua anggota aktif** (`halaqah_members.left_on is null`) dalam **satu transaksi**: `wasilah_input_save(halaqah, bulan, items)`. Bila satu mata pelajaran ditolak (bukan mapel halaqah, item bukan milik mapel itu, tidak berhak, bulan terkunci), **seluruh** penyimpanan batal - tidak ada penyimpanan sebagian.
- **Anggota yang sudah keluar tidak ikut disalin**, dan baris lamanya tidak diubah. Menyimpan ulang memperbarui baris yang sama (tidak menggandakan) karena kunci unik `(student_id, subject_id, month_id)`.
- **Bulan 0 (Data Awal) ditolak oleh fungsi**, bukan hanya disembunyikan di tampilan. **Bulan terkunci** ditolak untuk pengampu dan Masul; hanya Mudir/Admin yang boleh.
- **Halaman**: `/input/wasilah` dan `/input/ghayah` (juga `/input/alquran`); `/input` tetap Al Qur'an. Domain yang ditawarkan mengikuti role (`domainInputUntuk` di `src/lib/roles.ts`); database tetap penjaga terakhir.
- **Satu permintaan per tahap** (`wasilah_input_boot` untuk pembukaan, `wasilah_input_form` untuk isi) dan **pencarian item di server**. Halaman siap 0,86-0,87 s.
- **Hadir dan Hari Efektif dibaca dari `v_attendance`**, tidak dihitung di React (migrasi `20261125000014`).
- **Nilai tersimpan tampil kembali** saat halaman dibuka; label item disimpan beserta objeknya seperti perbaikan T5c-3.
- **Hanya mata pelajaran yang ditetapkan halaqah** (`halaqah_subjects`) yang tampil. Halaqah tanpa penetapan (mis. Level 6 Wasilah) menampilkan pesan, bukan form kosong.

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

## 9. Notifikasi "santri belum punya halaqah" (keputusan final 24 November 2026)
Perluasan dari notifikasi "data belum lengkap" (bukan sistem paralel; satu kotak pemberitahuan di `KotakBelumLengkap.tsx`).

- **Definisi "belum punya halaqah di domain D"** (migrasi `20261121000009_students_without_halaqah.sql`):
  santri **aktif** (`students.is_active`) di **tahun ajaran aktif** (`academic_years.is_active`, tahun terbaru bila lebih dari satu) yang **tidak** punya **keanggotaan aktif** (`halaqah_members.left_on is null`) pada **halaqah aktif** (`halaqahs.is_active`) tahun itu untuk domain D.
  - `halaqah_subjects`/`subjects` **tidak** dipakai untuk menentukan "punya halaqah": domain sudah tersimpan di `halaqahs.domain`. Level 6 Wasilah yang belum punya mata pelajaran/pengampu tetap dihitung sebagai halaqah.
  - Level adalah keterangan tampilan saja (dari `student_levels` domain sama; kosong bila tidak ada). Santri tetap muncul.
- **Hak lihat:** Mudir dan Admin melihat **ketiga** domain; Masul Al Quran hanya Al Qur'an, Masul Wasilah hanya Ilmu Wasilah, Masul Ghayah hanya Ilmu Ghayah; Musyrif/ah dan Mudarris/ah **tidak** melihat; anon ditolak.
- **Implementasi:** dua fungsi `security definer` `students_without_halaqah()` (daftar: domain, tahun, NIS, nama, level) dan `students_without_halaqah_count()` (ringkasan jumlah per domain, termasuk 0). Keduanya memeriksa `can_manage(domain)` di dalam fungsi; `revoke ... from public, anon` dan `grant ... to authenticated, service_role`. Tidak ada tabel baru, jadi daftar **hilang otomatis** begitu santri dimasukkan ke halaqah.
- **Penugasan halaqah** adalah pekerjaan T8; halaman ini hanya menampilkan notifikasi, bukan formulir penugasan.
- **Catatan keamanan:** karena fungsi `security definer`, `current_user` di dalamnya selalu pemilik (postgres). Agar "tampil semua" hanya untuk skrip admin lokal tanpa JWT (bukan pengguna aplikasi), syaratnya `current_app_role() is null and session_user in ('postgres','service_role','supabase_admin')`. Pengguna aplikasi (PostgREST) selalu lewat `can_manage`.
