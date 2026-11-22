# Prompt untuk OpenCode

Cara pakai: buka repo di OpenCode, mulai **sesi baru untuk setiap tugas**, tempel satu prompt. Tugas berikutnya hanya setelah tugas sebelumnya lolos
`npm run typecheck` dan `npm run build`, dan Mudir sudah mengecek hasilnya. Jika OpenCode bertanya soal data atau aturan, tanyakan ke Mudir; jangan biarkan menebak.

Awalan yang selalu ditambahkan di setiap prompt:
> Baca `AGENTS.md`, `docs/SPEC.md`, dan `docs/DATA-NOTES.md` lebih dulu. Jangan menebak aturan atau data; jika tidak jelas, berhenti dan tanyakan. Tulis nama role selengkapnya (Masul Al Quran, Masul Wasilah, Masul Ghayah). Ringkas hasil dengan bahasa sederhana untuk Mudir.

## T0 - Orientasi dan sambungan
> Jalankan `npm install`, `npm run typecheck`, `npm run build`. Pastikan `.env.local` terbaca dan halaman awal menulis "Tersambung ke Supabase." Jelaskan struktur repo dalam 10 baris. Jangan mengubah kode.

## T1 - Database dan seed
> Jalankan migrasi di `supabase/migrations/` ke project Supabase (lihat README langkah 4), lalu bangun seed (langkah 5-8). Laporkan isi `scripts/seed/output/seed-report.md` apa adanya, termasuk galat dan peringatan. Jangan menghapus galat dengan mengubah data atau skrip tanpa persetujuan Mudir. Setelah berhasil, tulis query SQL pemeriksaan: jumlah santri per halaqah, jumlah capaian per bulan, dan 5 baris `v_monthly_report`.

## T2 - Login, kerangka, dan menu per role
> Buat halaman login (Supabase Auth, email + kata sandi), pengambilan profil dari `profiles`, dan kerangka aplikasi dengan menu: Capaian, Input, Target, Kurikulum, Halaqah & Santri, Pengaturan. Menu hanya muncul sesuai role di `docs/SPEC.md` bagian 3, tetapi keamanan sebenarnya tetap dari RLS. Bahasa Indonesia, ramah HP.

## T3 - Tabel capaian halaqah Al Qur'an (baca saja)
> Buat layar "Tabel capaian halaqah Al Qur'an" sesuai wireframe: pilih halaqah dan bulan (tanpa pilihan bulan pembanding; otomatis bulan sebelumnya), tabel per santri dengan Hadir/HE, serta Tilawah, Tahfidz, Kitabah dalam format Lalu | Kini | Selisih dan target. Data dari `v_monthly_report`. Merah muda untuk `below_target`, kuning untuk `attendance_short`, jangan hanya warna (tambahkan teks). Bulan tanpa data tampil kosong. Selisih negatif tampil apa adanya.

## T4 - Halaman satu santri
> Buat halaman capaian satu santri: pilih Semester 1, Semester 2, atau Satu tahun ajaran; grafik selisih per bulan untuk Tilawah, Tahfidz, Kitabah, dan Kehadiran; tabel riwayat. Bulan tanpa data dibiarkan kosong di grafik (bukan 0). Grafik memakai posisi kumulatif agar tidak turun saat santri berpindah buku.

## T5 - Input capaian Al Qur'an
> Buat form input capaian Al Qur'an per halaqah dan bulan: pilih item dropdown dari `curriculum_items` per bidang, Hari Efektif ditampilkan (tidak diisi di sini; santri dengan Hari Efektif khusus menampilkan angkanya sendiri, dan hanya Mudir/Admin yang boleh mengubahnya), izin/sakit/alpha, catatan. Untuk Tilawah buku Al Qur'an tambahkan pilihan "khatam, mulai putaran baru" (menaikkan `putaran`). Hormati RLS: pengampu hanya halaqahnya dan bulan yang belum terkunci; tampilkan pesan jelas bila ditolak.

## T6 - Tabel dan input Wasilah dan Ghayah
> Buat layar halaqah Wasilah/Ghayah sesuai wireframe: judul halaqah (Level atau Kelompok), tabel mata pelajaran (Bidang, Capaian Bulan Lalu, Capaian Bulan Ini, Selisih) dengan pengampu dan jadwal di bawah nama mata pelajaran, lalu tabel anggota (Nama Santri, Hadir/HE, Izin, Sakit, Alpha, Catatan). Capaian diisi satu kali per mata pelajaran dan disalin ke semua anggota aktif (satu baris `progress_entries` per santri). Perubahan anggota di kemudian hari tidak boleh mengubah baris lama.

## T7 - Target (dinamis)
> Target Al Qur'an bersifat dinamis: dinaikkan atau diturunkan sesuai kemampuan santri. Buat: (a) dari tabel halaqah Al Qur'an, tombol "Ubah target" per santri dan per bidang (Tilawah, Tahfidz, Kitabah) untuk mengajukan target harian baru yang berlaku mulai bulan yang dipilih (`effective_month_id`; target lama tetap berlaku untuk bulan sebelumnya, riwayat tidak berubah); (b) pengajuan sekaligus untuk beberapa santri dalam satu halaqah; (c) riwayat target per santri (berlaku mulai, nilai, status, pengaju, penyetuju); (d) daftar target menunggu persetujuan untuk Mudir, Admin, atau Masul Al Quran / Masul Wasilah / Masul Ghayah sesuai domain. Pengampu mengajukan (status `diajukan`); target baru dipakai di laporan setelah `disetujui`. Wasilah dan Ghayah: target bulanan per halaqah dan bidang dengan alur yang sama. Nilai target boleh pecahan. Uji: target dinaikkan mulai bulan X tidak mengubah `target_monthly` bulan sebelum X.

## T8 - Kelola kurikulum (dropdown), halaqah, santri, kalender
> Buat layar kelola agar dropdown tetap bisa diubah setelah aplikasi jadi, sesuai `docs/SPEC.md` bagian 4b: bidang, buku, item (tambah, ubah, urutkan ulang, nonaktifkan; jangan hapus item yang sudah dipakai). Untuk Wasilah dan Ghayah pakai fungsi `resequence_subject` dan `reorder_items`, dan tampilkan peringatan bahwa menyisipkan item di tengah buku mengubah selisih lama yang melintasi titik itu. Untuk Al Qur'an, sediakan kolom `value` yang diisi manual dengan peringatan bila tumpang tindih atau turun. Juga: halaqah, anggota, pengampu per mata pelajaran dengan hari dan sesi; santri; tahun ajaran dan 12 bulan Hijriyah (`create_academic_year`); Hari Efektif per bulan per domain dan Hari Efektif khusus santri; kunci bulan.

## T9 - Pengujian dan QA
> Tulis pemeriksaan RLS sesuai `docs/SPEC.md` bagian 8 (skrip SQL atau uji otomatis), jalankan untuk setiap role, dan laporkan hasilnya. Uji aturan: selisih lintas buku (Iqro' ke Juz 'Amma), putaran Tilawah, selisih negatif, target bulanan = harian x Hadir, bulan terkunci. Periksa tampilan di HP dan kecepatan muat.

## T10 - Deploy
> Siapkan deploy ke Vercel (lihat README) dan periksa variabel environment. Pastikan hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY` yang ada di frontend. Verifikasi login dan satu alur input di situs yang sudah live. Catat langkah pindah ke cPanel.
