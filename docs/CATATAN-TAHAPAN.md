# Catatan untuk tahapan berikutnya (T6-T10)

Catatan ini **tidak mengubah urutan tugas**. Urutan tetap T6 → T7 → T8 → T9 → T10 sesuai `prompts/OPENCODE.md`.
Saat mengerjakan tahap yang disebut, baca poin di bawahnya lebih dulu.

## Keputusan Mudir yang mengikat semua tahap (23 Nov 2026)

1. **Bulan berjalan ditandai Hari Efektif.** Notifikasi "data belum lengkap" hanya memeriksa bulan yang sudah punya `month_domain_settings.effective_days` untuk domain itu. Konsekuensinya: **selama Admin belum mengisi Hari Efektif, bulan itu tidak diperiksa** — lihat poin T8.
2. **Dropdown halaqah/level/kelompok selalu memuat pengampu** ("HLQ-PA-4 - Ust. Fulan 3"; bila kosong: "musyrif/ah belum ditetapkan"). Termasuk dropdown saringan, filter, dan dropdown baru di T6-T8.
3. **Semua dropdown memakai `src/components/DropdownCari.tsx`** (ada pencarian). Jangan memakai `<select>` biasa.
4. **Batas 1.000 baris per permintaan Supabase.** Setiap daftar yang bisa lebih dari 1.000 baris wajib memakai `ambilSemua` di `src/lib/ambil-semua.ts`.
5. **Hak mengisi sesuai amanah:** Masul, Musyrif/ah, Mudarris/ah hanya ditawari halaqah yang diampu di layar Input (`hanyaHalaqahDiampu`). RLS database sudah menolak yang lain.
6. **Teks "bulan lalu" tampil sebagai teks dropdown**, bukan angka posisi.
7. **Grafik halaman santri:** Tilawah/Tahfidz/Kitabah satu kotak, kehadiran kotak terpisah. Tidak ada lagi pilihan gabung semua.
8. **Submenu mode ikon melayang dan menutupi** isi halaman (menu samping `z-30`, submenu `z-50`, isi halaman `isolate`). Jangan kembalikan ke submenu dalam alur.

## T6 - Tabel dan input Wasilah serta Ghayah

- Kolom **pengampu** di notifikasi data belum lengkap khusus Al Qur'an memakai musyrif/ah. Untuk **Wasilah** pakai nama pengampu per mata pelajaran, untuk **Ghayah** pakai muallim/ah + pendamping (lihat `docs/SPEC.md` bagian 2). Tambahkan saat halaman input Wasilah/Ghayah dibuat.
- Input Wasilah/Ghayah: satu kali per halaqah dan mata pelajaran, disalin ke semua anggota aktif. Perubahan anggota kemudian tidak boleh mengubah baris lama.
- Halaman input perlu menyaring halaqah sesuai amanah dengan cara yang sama seperti Al Qur'an (`hanyaHalaqahDiampu`).
- Perhitungan x/y terisi per bulan pada notifikasi memakai `subjects` domain tersebut; bidang aktifnya Baca, Tulis, Sirah, Hisab (Wasilah) dan Adab dan Iman, Aqidah dan Fiqih (Ghayah). Pastikan definisi "lengkap" = semua bidang aktif terisi, seperti Al Qur'an.

## T7 - Target (dinamis)

- Target Al Qur'an harian → bulanan = target harian × Hadir (dihitung database). Boleh pecahan.
- Pengajuan `diajukan`; hanya `disetujui` dipakai. Masul hanya menyetujui domainnya sendiri (Masul Al Quran tidak boleh menyetujui Wasilah/Ghayah dan sebaliknya). Mudir/Admin semua domain.
- Tombol "Ubah target" memakai `effective_month_id`; target lama tetap berlaku untuk bulan sebelumnya.
- Daftar target menunggu persetujuan juga perlu dibatasi halaqah menurut amanah untuk pengampu.

## T8 - Kelola kurikulum, halaqah, santri, kalender

- **Paling penting:** layar **Hari Efektif per bulan per domain** dan **kunci bulan** dikerjakan di sini. Sebelum itu tidak ada cara di aplikasi untuk mengisi Hari Efektif (sekarang hanya lewat SQL/dashboard).
  Saat membuat layar ini, pertimbangkan juga cara menandai **bulan berjalan** secara eksplisit: notifikasi sekarang menyimpulkan "sudah berjalan" dari Hari Efektif yang terisi. Bila Admin mengisi Hari Efektif untuk bulan yang belum dimulai, bulan itu ikut diperiksa.
- Kemungkinan besar butuh **migrasi baru** (nomor berikutnya, jangan ubah migrasi lama) bila perlu kolom penanda bulan berjalan.
- Kelola item: `resequence_subject` untuk Wasilah/Ghayah (tolak Al Qur'an), `reorder_items` untuk urutan dalam satu buku. Tampilkan peringatan bahwa menyisipkan item mengubah selisih lama.
- Kelola halaqah + pengampu per mata pelajaran (hari dan sesi): pastikan dropdown memakai `DropdownCari` dan label memuat pengampu.
- Hari Efektif khusus santri hanya Mudir/Admin (sudah dijaga trigger `attendance_guard`).
- Tambah tahun ajaran lewat `create_academic_year`; posisi santri berlanjut.

## T9 - Pengujian dan QA

- Tambahkan pemeriksaan RLS otomatis untuk tiap role, termasuk **Masul tidak bisa mengisi halaqah yang tidak diampu** dan **Musyrif tidak bisa menulis ke halaqah guru lain** (sudah diuji manual 23 Nov 2026; jadikan uji tetap).
- Uji selisih lintas buku (Iqro' ke Juz 'Amma), putaran khatam (+27) dan pengulangan (−577), selisih negatif, target bulanan = harian × Hadir, bulan terkunci.
- Periksa tampilan di HP sempit: tabel notifikasi (kepala beku + kolom Santri beku), submenu ikon yang melayang harus menutupi isi halaman (z-50), dan dropdown yang terbuka tidak terpotong.
- **Tabel yang kepala kolomnya harus beku dua arah:** sticky saja tidak cukup bila bingkai bergulirnya ikut tergulir bersama halaman. Pola yang dipakai sekarang (lihat `KotakBelumLengkap`): `thead` sticky z-30 untuk baris judul, ditambah `thead` kedua setinggi 0 berisi sel sudut `sticky left-0 z-40` (tidak terlihat) agar waktu scroll ke samping teks baris tidak tampak di atas label "Santri".

## T10 - Deploy

- Sebelum data asli dimuat: hapus data dummy, jadikan repo **privat**, selesaikan 4 kerentanan npm.
- Lingkungan Vercel hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`.
- Pastikan `ambilSemua` tetap dipakai setelah ada data asli (jumlah santri akan lebih dari 1.000 baris capaian per tahun).

## Temuan data yang masih menunggu Mudir (jangan ditebak)

- Level 6 (4 santri) belum punya pengampu dan jadwal.
- Santri `1447.dummy-nis.024` hanya di Al Qur'an; `1447.dummy-nis.023` belum di Ghayah.
- Bulan Jumadal Ula dan sesudahnya belum punya Hari Efektif; data capaian berhenti di Rabiul Akhir.
