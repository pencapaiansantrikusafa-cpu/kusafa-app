# HANDOVER - serah terima keadaan proyek

Diperbarui: **23 November 2026, 13.22**. Ditulis untuk sesi berikutnya agar bisa melanjutkan tanpa membaca riwayat percakapan.
Jangan menulis rahasia (kata sandi, kunci, token) atau data santri asli di berkas ini.

Baca berurutan: `AGENTS.md` → `docs/SPEC.md` → `docs/DATA-NOTES.md` → `docs/CATATAN-TAHAPAN.md` → `prompts/OPENCODE.md` (urutan tugas T1-T10) → berkas ini.

---

## 1. Status tiap tahap

Urutan tugas tetap mengikuti `prompts/OPENCODE.md`: T1 → T2 → ... → T10. Lihat `docs/CATATAN-TAHAPAN.md` untuk hal yang harus diperhatikan saat mengerjakan T6-T10.

| Tahap | Status | Berkas yang dibuat/diubah |
|---|---|---|
| **A-G** (alat, proyek, Git, Supabase, seed, uji lokal, Vercel) | SELESAI | `README.md`, `.env.example`, `supabase/config.toml` |
| **T1** (migrasi + seed) | SELESAI | `supabase/migrations/2026112100000[1-6]_*.sql`, `scripts/seed/build_seed.py`, `scripts/seed/create_auth_users.py`, `scripts/db/run_sql.py` |
| **T2** Login, profil, menu per role | SELESAI | `src/pages/LoginPage.tsx`, `src/components/AuthProvider.tsx`, `src/lib/auth-context.ts`, `src/lib/roles.ts`, `src/components/AppLayout.tsx`, `src/components/NavLinks.tsx`, `src/lib/supabase.ts` |
| **T3** Tabel capaian Al Qur'an | SELESAI | `src/pages/CapaianPage.tsx`, `src/pages/TabelCapaian.tsx`, `src/pages/TabelAlQuran.tsx`, `src/components/PemilihTahunBulan.tsx`, `src/components/PemilihHalaqah.tsx`, `src/lib/laporan.ts` |
| **T4** Halaman satu santri | SELESAI | `src/pages/SantriPage.tsx`, `src/components/GrafikGaris.tsx`, `src/components/GrafikGabungan.tsx` |
| **T5** Input capaian Al Qur'an | **SELESAI (termasuk T5b & perbaikan masukan)** | `src/pages/InputPage.tsx`, `src/pages/FormInputAlQuran.tsx`, `src/lib/putaran.ts`, `src/lib/posisi.ts`, `src/lib/ambil-semua.ts`, `src/components/DropdownCari.tsx`, `src/components/KonfirmasiPutaran.tsx`, `src/components/KotakBelumLengkap.tsx`, `tests/putaran.test.mjs`, `package.json` (skrip `test`) |
| **T6** Tabel + input Wasilah & Ghayah | BELUM | - (halaman Capaian Wasilah/Ghayah masih pesan "dikerjakan pada T6") |
| **T7** Target dinamis (ajukan/setujui) | BELUM | - (menu Target masih `PlaceholderPage`) |
| **T8** Kelola kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | BELUM | - (menu Kurikulum, Halaqah & Santri, Pengaturan masih `PlaceholderPage`) |
| **T9** Pengujian & QA (RLS otomatis, tampilan HP) | BELUM | baru uji manual + `tests/putaran.test.mjs` (6 uji) |
| **T10** Deploy akhir (hapus data dummy, repo privat) | BELUM | - |

Catatan: T5 sudah ditutup atas permintaan pemilik proyek, lalu ditegaskan lagi oleh permintaan khusus (T5b) pada 23 Nov 2026.

---

## 2. T5 - Input capaian Al Qur'an

### Sudah jalan
- Halaman `/input`: pilih halaqah dan **Tahun + Bulan** (dua dropdown terpisah, sesuai aturan), daftar santri per halaqah.
- Isian per bidang (Tilawah, Tahfidz, Kitabah) dari item aktif; izin/sakit/alpha; Hari Efektif khusus (hanya Mudir/Admin, dijaga trigger database); catatan.
- Simpan langsung ke tabel `attendance`, `monthly_notes`, `progress_entries` (upsert). Isi tersimpan tampil lagi saat dibuka.
- Bulan terkunci: tombol simpan dinonaktifkan, dan pesan galat dari database ditampilkan apa adanya bila tetap ditolak.
- Saringan "Semua / Belum lengkap / Sudah ada data"; penanda warna hijau/pink disertai teks.
- **Putaran Tilawah**: centang "khatam, mulai putaran baru" hanya untuk buku siklik dan hanya bila putaran bulan lalu diketahui; putaran = **putaran bulan lalu + 1**.
- **Konfirmasi sebelum simpan**: bila capaian lebih kecil dari bulan lalu, muncul "Capaian lebih kecil dari bulan lalu. Pengulangan atau khatam?"; simpan tertahan sampai semua dijawab. Tidak menebak.
- **Peringatan bulan lampau**: bila bulan sesudahnya sudah terisi dan isian bulan ini diubah, muncul peringatan meninjau putaran bulan berikutnya.
- Dropdown item memakai pencarian (`DropdownCari`); urutan mengikuti urutan buku lalu `seq`.
- "Bulan lalu" tampil sebagai **teks label** (`item_label` dari `v_monthly_report`), bukan angka posisi.
- Notifikasi "Data belum lengkap — awal tahun sampai bulan berjalan" dengan kolom musyrif/ah, ringkasan x/y terisi per bulan, saringan halaqah untuk Mudir/Admin/Masul Al Quran.
- Halaqah yang ditawarkan mengikuti amanah (`hanyaHalaqahDiampu`); RLS database sudah menolak halaqah lain (diuji).

### Uji browser dengan akun pengampu (23 Nov 2026, Musyrif HLQ-PA-1)
- Login, pilih halaqah + bulan, isi 3 bidang dengan pencarian dropdown, simpan → **3 baris tertulis ke `progress_entries`**; setelah muat ulang nilai tampil lagi; tab "Belum lengkap" menjadi 0 dan "Sudah ada data" 7.
- **Konfirmasi pengulangan** muncul benar (posisi 514 → 117) dan simpan tertahan sampai dijawab; setelah memilih "Pengulangan", putaran tetap 1 dan selisih negatif.
- Data uji dikembalikan (capaian yang diisi dihapus). Jumlah akhir sama dengan seed: 2.036 capaian, 606 presensi.
- Tampilan HP 390 px: bilah bawah muncul, dropdown menumpuk satu kolom, tidak ada teks terpotong.
- **Dua cacat ditemukan dan diperbaiki**:
  1. Ringkasan baris menulis `izin 0, sakit 0, alpha 0` untuk bulan yang belum diisi kehadiran (melanggar "kosong bukan 0"). Kini kosong tampil "—" (`FormInputAlQuran.tsx`).
  2. Peringatan React "dua anak dengan kunci sama" di dropdown item: `useMemo` `itemPerBidang` ikut mengubah array state, sehingga Mode Ketat React menduplikasi item. Kini memo murni. Sebelumnya ini membuat satu pilihan bisa muncul/terpilih ganda.

### Belum
- **Belum ada layar untuk mengisi Hari Efektif** (menu Pengaturan masih kosong). Sampai T8, Hari Efektif hanya diisi lewat SQL/dashboard. Akibatnya bulan yang belum diisi Hari Efektifnya tidak diperiksa oleh notifikasi.
- Hanya domain Al Qur'an; input Wasilah & Ghayah di T6.

### Bug/error yang diketahui (belum ada yang menggantung)
- Tidak ada galat typecheck/build/test saat serah terima ini.
- Batas **1.000 baris** per permintaan Supabase; semua daftar panjang sudah memakai `ambilSemua`.
- Query item ±4,7 detik untuk ~1.000 baris (butuh beberapa permintaan karena diambil per buku). Bisa dipercepat dengan view/migrasi baru bila perlu (belum dikerjakan, perlu izin karena menambah migrasi).
- Kolom pengampu di notifikasi baru musyrif/ah Al Qur'an (pengampu Wasilah, muallim/ah Ghayah menyusul T6).
- **Dropdown item hanya menampilkan 60 hasil pertama** yang cocok (`batasTampil`, belum ada gulir-tambah). Contoh: pada Kitabah, mencari "menyalin" berhenti di "Menyalin - 60" sehingga "Menyalin - 88" tidak tercapai; harus mengetik label utuh. Saran perbaikan: tampilkan lebih banyak saat kata kunci mendekati label, atau "muat lebih banyak". Belum dikerjakan (perlu keputusan Mudir).
- **Label item Al Qur'an dan Tahfidz tumpang tindih** ("Al Ghasyiyah - 26" ada di dua bidang). Aman karena dropdown dipisah per bidang, tetapi bisa membingungkan pengguna. Perlu keputusan apakah label diberi nama buku di depan.
- **Bulan 12 (Ramadhan) punya 7 baris presensi tanpa capaian dan tanpa Hari Efektif**. Untuk data uji ini tidak masalah; Mohon dipastikan ini memang disengaja sebelum T9.

### Langkah berikutnya yang konkret
1. Mulai **T6**: tabel & input Wasilah/Ghayah sesuai `docs/SPEC.md` §2 dan §5.6. Satu isian per halaqah + mata pelajaran, disalin ke semua anggota aktif; perubahan anggota kemudian tidak mengubah baris lama.
2. Perluas `KotakBelumLengkap` agar menerima `domain` dan nama pengampu sesuai domain (T6).
3. Pada T8, buat layar Hari Efektif per bulan per domain + kunci bulan, lalu perbarui cara menandai "bulan berjalan".

---

## 3. Keputusan teknis yang tidak boleh berubah

### Struktur & aturan database (sudah dijalankan, jangan diubah)
- Migrasi **tidak boleh diubah** setelah dijalankan; perubahan skema = migrasi baru nomor berikutnya (`20261121000007_...`).
- `hijri_months` **tidak punya** `hijri_year`; tahun ada di `academic_years` (relasi `academic_years!inner(hijri_year)`). `month_no` 0 = Data Awal, 1 = Syawwal ... 12 = Ramadhan.
- Posisi = `value + value_offset + (putaran - 1) * cycle_length` (fungsi `public.item_position`). Buku siklik hanya "Al Qur'an" (604 halaman).
- Selisih dihitung di database (`v_monthly_report`, `v_attendance`). **Jangan menghitung selisih/target/kehadiran di React.**
- Target bulanan = target harian × Hadir; hanya target `disetujui` dipakai; individu didahulukan dari halaqah.
- `putaran` naik 1 hanya lewat pilihan khatam eksplisit.
- Bulan kosong = **belum diisi**, bukan 0. Selisih boleh negatif.
- Item kurikulum yang sudah dipakai tidak dihapus, hanya `is_active = false`.
- `month_domain_settings.effective_days` = Hari Efektif per bulan per domain; **dipakai sebagai penanda "bulan sudah berjalan"** pada notifikasi (keputusan opsi B, 23 Nov 2026).

### Komponen dan pola frontend yang wajib dipakai
- `src/components/DropdownCari.tsx` - **semua** dropdown (pencarian). Jangan `<select>` biasa.
- `src/components/PemilihTahunBulan.tsx` - dua dropdown terpisah; tidak pernah digabung.
- `src/components/PemilihHalaqah.tsx` - label "HLQ-PA-1 - Ust. Fulan 1"; `ambilGuru()`/`halaqahDiampu()` untuk menyaring amanah.
- `src/lib/roles.ts` - `hanyaHalaqahDiampu()` (Masul/Musyrif/Mudarris), `batasiPemberitahuan()`, `isPeninjau()`.
- `src/lib/ambil-semua.ts` - wajib untuk daftar yang bisa >1.000 baris.
- `src/lib/putaran.ts` - aturan putaran; diuji `tests/putaran.test.mjs`.
- `src/components/KonfirmasiPutaran.tsx`, `src/components/KotakBelumLengkap.tsx`.
- Grafik halaman santri: Tilawah/Tahfidz/Kitabah satu kotak, kehadiran kotak terpisah.
- Tata letak: menu samping `z-30`, submenu mode ikon melayang `z-50`, isi halaman `isolate`. Tabel ber-heading beku: `thead` sticky z-30 + `thead` kedua setinggi 0 dengan sel sudut `sticky left-0 z-40` (lihat `KotakBelumLengkap`).
- Struktur Supabase CLI 3.2.0: perintah ke project online butuh `--remote`.

---

## 4. Status Supabase

- **Project**: `kusafa` (ref `vcmamapzkhzgikpsvcdo`), region Singapore (`ap-southeast-1`).
- **Migrasi dijalankan** (6, semua tercatat di `supabase_migrations.schema_migrations`):
  `20261121000001 core_calendar`, `...0002 students_curriculum`, `...0003 halaqah`, `...0004 targets_progress`, `...0005 functions_views`, `...0006 rls`.
- **RLS**: 18 dari 18 tabel `rowsecurity = true`; 44 kebijakan di `pg_policies`. Diverifikasi 23 Nov 2026 (hanya baca). Uji tulis manual (dibatalkan): Musyrif A ditolak menulis capaian/kehadiran/catatan ke halaqah Musyrif B.
- **DATABASE_URL**: memakai **pooler** `aws-0-ap-southeast-1.pooler.supabase.com:5432` (jaringan tanpa IPv6, alamat langsung `db.<ref>.supabase.co` tidak bisa diresolusi). Jangan diubah tanpa bertanya kepada Mudir.
- **Seed**: **sudah dijalankan** (data dummy). Isi saat ini: 109 santri, 38 halaqah, 10.954 item, 327 target, 2.036 capaian, 606 presensi, 24 akun dummy. Seed bersifat destruktif (truncate) — jangan dijalankan ulang tanpa izin.
- `.env.local` berisi 6 nama kunci (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `VERCEL_OIDC_TOKEN`); nilainya tidak boleh dicetak atau di-commit. Kunci service role dan `DATABASE_URL` tidak boleh masuk Vercel.
- **Vercel**: project `kusafa-app` terhubung ke repo GitHub, production siap; environment hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`.
- **Repo GitHub**: `https://github.com/pencapaiansantrikusafa-cpu/kusafa-app` — **masih publik**; wajib dijadikan privat sebelum data asli dimuat.
- **Data uji yang menunggu keputusan Mudir**: Level 6 belum punya pengampu/jadwal; `1447.dummy-nis.024` hanya di Al Qur'an; `1447.dummy-nis.023` belum di Ghayah; Hari Efektif & capaian berhenti di Rabiul Akhir.

---

## 5. Perintah

```bash
npm install                 # pasang dependensi
npm run dev                 # server pengembangan (default http://localhost:5173/)
npm run typecheck           # wajib hijau sebelum selesai
npm run test                # uji aturan putaran (node --test tests/)
npm run build               # wajib berhasil sebelum selesai (hasil: dist/)
python scripts/check_repo_safety.py   # wajib lolos sebelum push (hook .githooks juga menjalankannya)
```

Data & database (membaca `DATABASE_URL` dari `.env.local`, tidak pernah mencetaknya):

```bash
python scripts/db/run_sql.py --query "select count(*) from public.students"
python scripts/db/run_sql.py supabase/seed/01_curriculum.sql      # DESTRUKTIF, hanya data uji
npm run seed:build          # bangun seed dari data/source/*.xlsx
npm run seed:users          # buat akun dummy di Supabase Auth
```

Uji RLS manual (contoh pola, jalankan dalam transaksi lalu `rollback`):

```bash
# tiru sesi login: set_config('request.jwt.claims', '{"sub":"<profil_id>","role":"authenticated"}', true)
# lalu: set_config('role','authenticated',true) dan coba insert; tutup dengan rollback()
```

Deploy:

```bash
npx vercel ls               # melihat daftar deployment (baca saja)
npx vercel --prod           # deploy production (atau push ke main -> deploy otomatis)
npm run build && # unggah isi dist/ ke public_html untuk cPanel
```
