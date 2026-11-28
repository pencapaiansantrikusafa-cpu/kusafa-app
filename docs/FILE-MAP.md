# FILE-MAP - peta kode KUSAFA

Diperbarui 26 November 2026. Satu baris per berkas penting: apa fungsinya.
Dibaca bersama `docs/STATUS.md` (kondisi nyata) dan `docs/HANDOVER.md` (serah terima).

---

## 1. Akar repo

| Berkas | Fungsi |
|---|---|
| `index.html` | Halaman tunggal Vite; memuat `/src/main.tsx`. |
| `package.json` | Skrip `dev`, `build`, `preview`, `typecheck`, `test`, `seed:build`, `seed:users`, `db:sql`. Tidak ada `lint`. |
| `vite.config.ts` | Konfigurasi Vite + plugin React. |
| `tsconfig.json` | Konfigurasi TypeScript (mode ketat). |
| `tailwind.config.js` | Tema Tailwind; warna `kusafa` dan `kusafa-light`. |
| `postcss.config.js` | Tailwind + autoprefixer. |
| `vercel.json` | Aturan penulisan ulang rute agar aplikasi satu halaman tidak 404 di Vercel. |
| `public/.htaccess` | Aturan penulisan ulang rute untuk hosting cPanel/Apache. |
| `.env.example` | Contoh nama variabel lingkungan (tanpa nilai). |
| `.githooks/pre-commit` | Hook: menjalankan `check_repo_safety.py --staged` sebelum tiap commit. Aktif lewat `git config core.hooksPath .githooks`. |
| `AGENTS.md` | Aturan kerja tetap untuk agent/developer. |
| `README.md` | Ringkasan proyek, status, cara setup dan deploy. |
| `docs/SPEC.md` | Aturan bisnis, role, model data (sumber kebenaran aturan). |
| `docs/STATUS.md` | Status tiap tahap dan kondisi nyata database/deploy. |
| `docs/HANDOVER.md` | Serah terima untuk sesi berikutnya. |
| `docs/FILE-MAP.md` | Berkas ini. |
| `docs/DATA-NOTES.md` | Pemetaan Excel dan temuan data terbuka. |
| `docs/CHANGELOG.md` | Ringkasan perubahan per tahap. |
| `docs/CATATAN-TAHAPAN.md` | Catatan khusus T6-T10 (tidak mengubah urutan tugas). |
| `prompts/OPENCODE.md` | Urutan tugas T0-T10. |
| `prompts/00-SETUP-OTOMATIS.md` | Prompt setup awal (arsip). |

---

## 2. `src/` - aplikasi React

### 2.1 Titik masuk

| Berkas | Fungsi |
|---|---|
| `src/main.tsx` | Melekatkan React ke `#root`; membungkus `BrowserRouter` + `AuthProvider` + `StrictMode`. |
| `src/App.tsx` | Daftar rute. Bila belum login menampilkan `LoginPage`; setelah login memakai `AppLayout`; menu yang belum dibuat memakai `PlaceholderPage`. |
| `src/index.css` | Impor Tailwind + gaya dasar. |
| `src/vite-env.d.ts` | Tipe variabel lingkungan Vite. |

### 2.2 `src/components/`

| Berkas | Fungsi |
|---|---|
| `AppLayout.tsx` | Kerangka setelah login: header, menu samping (bisa dilipat jadi ikon), bilah bawah untuk HP, isi halaman ber-`isolate`. |
| `AuthProvider.tsx` | Menyediakan profil pengguna yang login (dari tabel `profiles`) ke seluruh aplikasi. |
| `NavLinks.tsx` | Menu dan ikon SVG-nya; submenu "Capaian" (Al Qur'an, Ilmu Wasilah, Ilmu Ghayah). |
| `DropdownCari.tsx` | **Satu-satunya dropdown** yang boleh dipakai. Punya kotak cari (cocok teks + nomor), panel dilayangkan ke `<body>` dengan `LAPISAN_DROPDOWN = 60`, dan menulis "Menampilkan 60 dari N". Menyimpan objek pilihan (label & `siklik`) di state agar label tetap tampil walau item tidak ada di daftar/hasil pencarian terakhir; `onChange` meneruskan objek pilihan. |
| `PemilihTahunBulan.tsx` | Dua dropdown terpisah: Tahun Hijriyah dan Bulan. Tidak pernah digabung. |
| `PemilihHalaqah.tsx` | Dropdown halaqah berlabel "HLQ-PA-1 - Ust. Fulan 1" + fungsi `ambilGuru()`, `ambilPengampu()`, `halaqahDiampu()` untuk menyaring sesuai amanah. |
| `KotakBelumLengkap.tsx` | Kotak "Data belum lengkap" (awal tahun s.d. bulan berjalan): ringkasan x/y per bulan, tabel santri belum lengkap dengan kepala kolom beku dua arah, saringan halaqah. **T7**: bagian Target (menunggu persetujuan, target DUMMY, sasaran belum punya target) untuk Masul domainnya/Mudir/Admin. **T7c [3c]**: untuk Wasilah/Ghayah memakai `target_belum_domain` (kekurangan = mapel aktif tanpa target bulan depan; "Tuntas, menunggu keputusan Masul"; Level 6 tak dihitung; jumlah & daftar sesuai database). |
| `FormTarget.tsx` | **T7**: form ajukan/ubah target (alquran per santri harian; wasilah/ghayah per halaqah bulanan), pilihan target massal Al Qur'an, bulan berlaku default bulan berjalan, peringatan + centang konfirmasi bulan lewat/terkunci (hanya Mudir/Admin), catatan. Semua tulis lewat RPC. |
| `DialogAksiTarget.tsx` | **T7**: dialog Setujui / Tolak (alasan **wajib**) / Batalkan, dengan centang konfirmasi bila bulan berlaku lewat atau terkunci. |
| `DialogRiwayatTarget.tsx` | **T7**: riwayat target satu sasaran dari RPC `riwayat_target` (nilai, periode, status, pengaju/penyetuju/penolak, alasan, catatan). |
| `KonfirmasiPutaran.tsx` | Dialog "Capaian lebih kecil dari bulan lalu. Pengulangan atau khatam?" - memakai teks dropdown, bukan angka posisi. |
| `GrafikGaris.tsx` | Grafik garis SVG sederhana; bulan kosong ditampilkan kosong (bukan 0). |
| `GrafikGabungan.tsx` | Beberapa garis dalam satu kotak; garis putus-putus untuk kehadiran. |

### 2.3 `src/lib/`

| Berkas | Fungsi |
|---|---|
| `supabase.ts` | Klien Supabase dari `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`. Tidak boleh memakai kunci service role. |
| `auth-context.ts` | Konteks React untuk profil pengguna. |
| `roles.ts` | Tipe role, label role lengkap (Masul Al Quran, Masul Wasilah, Masul Ghayah), daftar menu per role, `hanyaHalaqahDiampu()` (kini hanya Musyrif/ah & Mudarris/ah), `bolehInputDomain()` (Masul = semua halaqah domainnya), `batasiPemberitahuan()`, `isPeninjau()`. |
| `laporan.ts` | Tipe baris `v_monthly_report` + pemformat angka. **Tidak** menghitung selisih/target/kehadiran (itu di database). |
| `putaran.ts` | Aturan putaran Tilawah: `bolehKhatam()`, `putaranUntukSimpan()`. Diuji di `tests/putaran.test.mjs`. |
| `posisi.ts` | Pemanggil RPC `item_position` dengan cache, dipakai form input saat memeriksa capaian lebih kecil dari bulan lalu. |
| `ambil-semua.ts` | Pengambil bertahap: Supabase membatasi 1.000 baris per permintaan, jadi daftar panjang wajib memakai ini. |
| `target.ts` | **T7**: pembungkus RPC target (`ajukan_target`, `ubah_target`, `setujui_target`, `tolak_target`, `batalkan_target`, `ajukan_target_massal_alquran`, `riwayat_target`, `target_info_konfirmasi`), tipe `BarisTarget`, dan `STATUS_LABEL`/`STATUS_GAYA`. Tidak ada aturan target dihitung di sini. |

### 2.4 `src/pages/`

| Berkas | Fungsi |
|---|---|
| `LoginPage.tsx` | Formulir login (email + kata sandi) lewat Supabase Auth. |
| `CapaianPage.tsx` | Halaman Capaian per domain; memilih halaqah, tahun, bulan. |
| `TabelCapaian.tsx` | Tabel capaian halaqah + nama pengampu; **T6e**: tombol "Hapus capaian" per santri & "Hapus semua <mapel>" (massal) hanya untuk Mudir/Admin, memanggil RPC hapus. |
| `DialogHapusCapaian.tsx` | **T6e**: dialog konfirmasi hapus (menyebut santri/jumlah, bidang, bulan, nilai), peringatan putaran, centang konfirmasi bulan terkunci/bulan sesudahnya. |
| `TabDomain.tsx` | Komponen **bersama** tab domain (Al Qur'an / Ilmu Wasilah / Ilmu Ghayah) untuk halaman Capaian, Input, dan **Target** (`dasar` = `/capaian`, `/input`, `/target`). Memakai `<Link>` ke `${dasar}/${domain}` sehingga tab aktif tercermin di URL; HP 360 tiga tab dibagi rata, tinggi sentuh 44 px. |
| `InputPage.tsx` | Pemilih domain halaman Input; rute `/input`, `/input/alquran`, `/input/wasilah`, `/input/ghayah`. Domain mengikuti role (`domainInputUntuk`). |
| `InputAlQuranPage.tsx` | Halaman Input Al Qur'an (T5/T5c-2); isi tidak berubah, hanya berkas dipisah dari pemilih domain. |
| `InputWasilahPage.tsx` | Halaman Input Ilmu Wasilah/Ghayah: `wasilah_input_boot` + `wasilah_input_form`, pencarian item server, batas halaqah sesuai amanah. |
| `FormInputWasilah.tsx` | Form input Wasilah/Ghayah: satu dropdown per **mata pelajaran** (bukan per santri), label pilihan disimpan beserta objeknya, tabel anggota dengan Hadir/HE dari database. |
| `TabelWasilah.tsx` | Tabel capaian Ilmu Wasilah & Ilmu Ghayah (T6a): ringkasan Lalu/Kini/Selisih/target per mata pelajaran + tabel anggota (Hadir/HE, Izin, Sakit, Alpha, Catatan). Angka dari view; mata pelajaran dari `halaqah_subjects`. **T7c [3b]**: menampilkan label butir target + status "Tercapai"/"Kurang N butir" ("–" bila tak ada target disetujui). |
| `TabelAlQuran.tsx` | Tabel Al Qur'an: kolom per bidang berisi Lalu / Kini / Selisih, target, Hadir/HE, sorotan di bawah target. Target kosong ditampilkan `–` (0 tetap `0`). |
| `TargetPage.tsx` | **T7**: tab 3 domain rute `/target`, `/target/alquran`, `/target/wasilah`, `/target/ghayah` (domain mengikuti role). |
| `TargetDomainPage.tsx` | **T7**: daftar target satu domain; saringan Tahun+Bulan terpisah, halaqah (batas amanah untuk pengampu), mata pelajaran, status; tombol Ajukan/Ubah/Setujui/Tolak/Batalkan/Riwayat; tabel desktop + kartu ringkas HP 360 px. Nama sasaran/mapel/bulan/pelaku lewat embed PostgREST. Baca `targets` langsung; tulis hanya lewat RPC. **T7c [3b]**: Wasilah/Ghayah memakai `TabelTargetHalaqah` (satu baris per halaqah) + bulk `setujui_target_halaqah` + konfirmasi bulan terkunci/lewat (Mudir/Admin). |
| `TabelTargetHalaqah.tsx` | **T7c [3b]**: matriks target Wasilah/Ghayah satu baris per halaqah (kolom = mapel aktif bulan itu), sel berisi label butir target + status + pengaju/penyetuju, tombol Setujui/Tolak/Batalkan/Ubah/Riwayat + "Setujui semua target halaqah ini"; HP = kartu per halaqah tanpa tabel lebar. |
| `SantriPage.tsx` | Halaman satu santri: pilih domain + rentang (Semester 1/2/satu tahun), grafik dan riwayat. |
| `InputPage.tsx` | Halaman Input: pilih halaqah + tahun + bulan, daftar santri, Hari Efektif domain, kotak belum lengkap. Memuat item per buku (label diberi nama mata pelajaran). |
| `FormInputAlQuran.tsx` | Formulir input per santri: Tilawah/Tahfidz/Kitabah, izin/sakit/alpha, Hari Efektif khusus, catatan; konfirmasi hanya untuk bidang yang diubah; penanda ⚠ untuk yang sudah mundur. |
| `PlaceholderPage.tsx` | Bingkai "belum diisi" untuk menu T7-T8. |

---

## 3. `supabase/`

| Berkas | Fungsi |
|---|---|
| `config.toml` | Konfigurasi Supabase CLI (acuan; Site URL diatur manual di dashboard). |
| `migrations/20261121000001_core_calendar.sql` | Tahun ajaran, bulan Hijriyah, Hari Efektif + kunci bulan per domain. |
| `migrations/20261121000002_students_curriculum.sql` | Santri, wali, level, bidang, buku, item kurikulum. |
| `migrations/20261121000003_halaqah.sql` | Halaqah, anggota, mata pelajaran per halaqah, pengampu/jadwal. |
| `migrations/20261121000004_targets_progress.sql` | Target, capaian (`progress_entries`), kehadiran, catatan bulanan. |
| `migrations/20261121000005_functions_views.sql` | Fungsi bantu (posisi, hak akses, urut ulang) dan view laporan. |
| `migrations/20261121000006_rls.sql` | Semua kebijakan Row Level Security. |
| `migrations/20261121000007_harden_function_grants.sql` | Hardening fungsi: cabut `EXECUTE` anon/PUBLIC, grant hanya authenticated+service_role, `SET search_path` pada fungsi INVOKER. |
| `migrations/20261121000008_month_zero_not_open.sql` | Bulan 0 (Data Awal) bukan bulan input staf: `month_is_open(bulan 0, domain)` = false; bulan 1-12 tetap ikut `is_locked`. |
| `migrations/20261121000009_students_without_halaqah.sql` | Notifikasi "santri belum punya halaqah": fungsi `students_without_halaqah`(_count) security definer, periksa `can_manage` di dalam fungsi, `revoke` anon. |
| `migrations/20261124000010_attendance_guard_revoke.sql` | Cabut `EXECUTE` `attendance_guard_override()` dari authenticated/PUBLIC/anon (fungsi trigger; trigger tetap jalan karena SECURITY DEFINER). |
| `migrations/20261124000012_input_alquran_data.sql` | T5c-2: RPC `input_alquran_boot()` (halaqah+bulan+pengampu) & `input_alquran_data()` (seluruh isi form dalam satu JSON; angka dari view, tidak dihitung ulang). |
| `migrations/20261124000011_curriculum_search.sql` | T5c: RPC `curriculum_items_search` (cari item per bidang, maks 60, skor = versi klien) & `curriculum_items_by_ids`; indeks GIN trigram label; `pg_trgm` di skema `extensions`; EXECUTE hanya authenticated/service_role. |
| `migrations/20261125000017_masul_input_domain.sql` | T6d2: satu aturan tulis untuk **ketiga domain** (`is_full_access` ATAU Masul domainnya ATAU pengampu halaqah, dengan `month_is_open`); hapus tetap hanya Mudir/Admin. Menambah `updated_by`/`updated_at` di `progress_entries`, `attendance`, `monthly_notes` + trigger `catat_jejak`. |
| `migrations/20261125000019_hapus_capaian_log.sql` | T6e: RPC `hapus_capaian_info`/`hapus_capaian`/`hapus_capaian_massal_info`/`hapus_capaian_massal` (cek `is_full_access()` di dalam fungsi) + tabel `change_log` + trigger `catat_perubahan` (UPDATE/DELETE tiga tabel). |
| `migrations/20261125000020_log_abaikan_update_kosong.sql` | T6e: `catat_perubahan` mengabaikan UPDATE yang tidak mengubah nilai (cegah log palsu dari pemulihan data). |
| `migrations/20261125000018_catat_jejak_tanpa_jwt.sql` | T6d2: trigger `catat_jejak` tidak menyentuh baris lama bila `auth.uid()` NULL (seed/skrip), supaya jejak seed tidak tertimpa. |
| `migrations/20261126000021_targets_dinamis.sql` | T7a: helper `target_*`, view target bulan 0/kasus (f) + target individu/halaqah. |
| `migrations/20261126000022_targets_rpc.sql` | T7a: RPC `ajukan_target`, `setujui_target`, `tolak_target`. |
| `migrations/20261126000023_targets_rpc2.sql` | T7a: RPC `ubah_target`, `ajukan_target_massal_alquran`, `riwayat_target`. |
| `migrations/20261126000024_targets_grants.sql` | T7a: `EXECUTE` RPC target hanya `authenticated`; anon dicabut. |
| `migrations/20261126000025_targets_rpc_fix_volatile.sql` | T7a: RPC tulis `VOLATILE`; perbaikan validasi massal. |
| `migrations/20261126000026_targets_view_f_fix.sql` | T7a: `target_monthly` NULL bila Hari Efektif kosong; bulan 0 NULL. |
| `migrations/20261126000027_targets_view_tiebreak.sql` | T7a: tiebreak `created_at desc, id desc` saat beberapa target seord. |
| `migrations/20261126000028_targets_status_cancel.sql` | T7a: enum `target_status` + `dibatalkan`. |
| `migrations/20261126000029_targets_rpc_only_audit_cancel.sql` | T7a: hapus policy tulis + cabut privilege tulis; RPC `batalkan_target`. |
| `migrations/20261126000030_targets_massal_xor_fix.sql` | T7a: massal Al Qur'an tetap per santri (bukan halaqah). |
| `migrations/20261126000031_targets_audit_semantics.sql` | T7a: `catat_jejak_target` mencatat pengubah, pengaju asli tetap. |
| `migrations/20261127000033_halaqah_mapel_aktif.sql` | **T7c [2/3]**: `halaqah_mapel_aktif(halaqah, bulan)` sumber tunggal mapel aktif (+ `bulan_berikutnya`, `mapel_butir_terakhir`, `mapel_tuntas`, `halaqah_tanpa_mapel`); `wasilah_input_boot`/`form` memakainya. |
| `migrations/20261127000034_wasilah_simpan_gabungan.sql` | **T7c [2/3]**: RPC `wasilah_simpan_gabungan(halaqah, bulan, capaian, target, konfirmasi)` (capaian + target bulan depan satu transaksi), `wasilah_target_bulan_depan` (DEFINER), `halaqah_status_tuntas` (notifikasi Masul). |
| `migrations/20261127000035_v_monthly_report_tujuan_akhir.sql` | **T7c [2/3]**: `v_monthly_report` (+base) menambah `target_item_id, target_label, target_pos, target_tercapai, target_kurang, target_status` untuk Wasilah/Ghayah; Al Qur'an identik. |
| `migrations/20261126000032_targets_tujuan_akhir.sql` | **T7c**: kolom `targets.target_item_id` (FK `curriculum_items`), `amount` boleh kosong untuk Wasilah/Ghayah, constraint `targets_bentuk_check`, unique index `targets_satu_diajukan_uk`, trigger `target_validasi_butir` (butir milik buku mapel & aktif), RPC `ajukan_target`/`ubah_target` versi butir (parameter baru DEFAULT NULL, tanpa overload), `setujui_target_halaqah` (bulk), `riwayat_target` + butir/buku, `REVOKE EXECUTE` PUBLIC+anon untuk seluruh keluarga fungsi target. |
| `seed/01_curriculum.sql`, `seed/02_school_data.sql` | Hasil `build_seed.py`. **Tidak di-commit** (`.gitignore`) karena berisi data. |
| `.temp/` | Berkas kerja Supabase CLI. Tidak di-commit. |

Migrasi **tidak boleh diubah** setelah dijalankan. Perubahan skema = berkas baru `20261125000019_...`
(nomor `000010`-`000018` sudah terpakai).

---

## 4. `scripts/` dan `tests/`

| Berkas | Fungsi |
|---|---|
| `scripts/check_repo_safety.py` | Memeriksa repo sebelum commit: menolak `.env`, `.xlsx`, `.zip`, seed SQL, `users.csv`, token, kunci rahasia. |
| `scripts/db/fixes/2026-11-25_hapus_kehadiran_jumadal_ula.sql` | T6e: hapus 7 baris kehadiran Jumadal Ula percobaan Admin (0/0/0, tanpa capaian). Aman dijalankan ulang. |
| `scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql` | **T6d3** (keputusan Mudir): hapus baris kehadiran Ramadhan tanpa capaian. Aman dijalankan ulang; jalankan sesudah seed. |
| `scripts/db/fixes/2026-11-25_pulihkan_shafar.sql` | **T6d3**: pulihkan izin/sakit/alpha Shafar (37 baris berbeda) sesuai seed/Excel. |
| `scripts/db/fixes/2026-11-25_pulihkan_capaian_024.sql` | **T6d3**: masukkan kembali 1 baris seed yang hilang (024 Kitabah Dzul Qa'dah "Menyalin - 25"). |
| `scripts/db/fixes/2026-11-25_pulihkan_data_seed.py` | **T6d3**: pemulihan umum baris seed yang hilang/berbeda + jejak. `--jalankan` untuk menulis. |
| `scripts/db/fixes/2026-11-25_he_wasilah_ghayah_dummy.sql` | **DUMMY**: Hari Efektif Wasilah & Ghayah = Al Qur'an bulan 1-7 + baris kehadiran 0/0/0. Idempoten, tidak menimpa nilai yang ada. Wajib diganti data asli. |
| `scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql` | Pemulihan Hari Efektif Rabiul Awwal 19 → 3 (koreksi Mudir). |
| `scripts/db/fixes/2026-11-24_rabiul_awwal_effective_days.sql` | **DIBATALKAN** — skrip 3→19 keliru; hanya jejak riwayat, diberi penghenti keras. |
| `scripts/db/run_sql.py` | Menjalankan berkas SQL atau satu query ke database tanpa `psql`; membaca `DATABASE_URL` dari `.env.local` dan tidak pernah mencetaknya. |
| `scripts/seed/build_seed.py` | Membangun `supabase/seed/*.sql`, `scripts/seed/output/users.csv`, dan `seed-report.md` dari 5 file Excel. |
| `scripts/seed/create_auth_users.py` | Membuat akun dummy di Supabase Auth (memakai kunci service role di `.env.local`, hanya lokal). |
| `scripts/seed/smoke_login.py` | Menguji login beberapa akun dummy tanpa browser; kata sandi tidak dicetak. |
| `scripts/seed/requirements.txt` | Dependensi Python untuk skrip seed. |
| `scripts/qa/db_fingerprint.py` | **T6d3**: sidik jari database (19 tabel, jumlah baris + checksum md5). `--simpan` sebelum uji, `--banding` sesudah; hasil wajib SAMA. Hanya membaca. |
| `scripts/qa/pulihkan_data.py` | **T6d3**: simpan salinan penuh `progress_entries`/`attendance`/`monthly_notes`/`targets` lalu pulihkan persis (nilai + jejak). **T7 [2/2]**: parameter `urus` membatasi baris yang boleh disentuh uji, sehingga baris baru milik orang lain (mis. Mudir mencoba `/target`) tidak dihapus. Dipakai semua uji yang menulis. |
| `scripts/qa/test_t6e_hapus_capaian.py` | T6e (35 uji, transaksi + ROLLBACK): role, pratinjau, hapus satu/massal, bulan terkunci, bulan sesudahnya, bulan 0, log DELETE/UPDATE tiga tabel, log tanpa JWT, log tidak bisa diubah/dihapus/ditulis. |
| `scripts/qa/test_t6e_e2e_hapus.py` | T6e E2E (16 uji): Masul tanpa tombol hapus, dialog (santri/bulan/nilai), hapus satu & massal, bulan terkunci minta centang, data dipulihkan persis. |
| `scripts/qa/test_t6e_uji_penerimaan.py` | T6e **uji penerimaan** (15 uji): 3 baris capaian percobaan Mudir dihapus lewat UI; log 3 DELETE; sidik jari tepat -3/+3. Tidak dipulihkan. |
| `scripts/qa/test_t6e_langkah0_pengampu.py` | T6e langkah 0 (12 uji): E2E Simpan Mudarris/ah, Musyrif/ah, halaqah Level 6; data dipulihkan persis. |
| `scripts/qa/test_seed_bersih.py` | **T6d3**: uji penjaga sesudah seed (capaian 2.039, Ramadhan tanpa capaian 0, kehadiran 606/756/749, Wasilah/Ghayah 0, catatan 0). Hanya membaca. |
| `scripts/qa/compare_alquran_full_excel.py` | **T6d3**: banding Excel **PENUH** (109 santri, semua bulan 1-7, kehadiran + capaian). Hanya membaca. |
| `scripts/qa/rls_matrix.py` | Matriks RLS role × tabel × operasi (94 OK / 3 SKIP); tiap probe transaksi sendiri + ROLLBACK — termasuk baris sasaran uji hapus yang dibuat **di dalam** transaksi agar tidak tertinggal. |
| `scripts/qa/test_t6d2_masul_input.py` | T6d2 (68 uji, transaksi + ROLLBACK): ketiga Masul boleh insert/update capaian+kehadiran+catatan di semua halaqah domainnya, ditolak di domain lain/bulan terkunci/bulan 0, tidak boleh hapus; jejak `entered_by`/`updated_by`; hitungan baris per domain tidak berubah. |
| `scripts/qa/test_t6d2_e2e_masul.py` | T6d2 E2E (14 uji): ketiga Masul melihat semua halaqah domainnya, domain lain dialihkan, Simpan menulis capaian dengan `entered_by`, Musyrif tetap satu halaqah, data & jejak dipulihkan. |
| `scripts/qa/run_pre_t6_db_tests.py` | Uji DB pra-T6 (16 uji): trigger Hari Efektif, bulan terkunci, RLS lintas halaqah, `can_manage`, Hari Efektif Rabiul Awwal = **3** (libur). |
| `scripts/qa/test_no_halaqah.py` | Santri tanpa halaqah di suatu domain: tidak tampil, RLS menolak penulisan. |
| `scripts/qa/test_students_without_halaqah.py` | Notifikasi per role (Mudir/Admin semua domain, Masul domainnya, Musyrif/Mudarris 0). |
| `scripts/qa/test_students_without_halaqah_p6.py` | Jalur "tampil semua" fungsi: authenticated tanpa profil/musyrif/mudarris 0 baris, koneksi admin melihat semua, anon ditolak. |
| `scripts/qa/regression_execute.py` | Regresi: tiap fungsi public tanpa `EXECUTE` anon **dan tanpa `EXECUTE` PUBLIC** (loop `pg_proc` + `aclexplode`); musyrif tak bisa mengubah data lewat fungsi admin. |
| `scripts/qa/test_auth_signup_closed.py` | `disable_signup=true`, signup ditolak `signup_disabled`, login 7 role berhasil. |
| `scripts/qa/measure_input_perf.py` | Ukur waktu siap halaman Input, jumlah permintaan, byte item (Playwright; `VIEWPORT=360`, `ULANG=n`, `HASIL=...`). |
| `scripts/qa/test_t6d_tab_capaian.py` | E2E tab domain: terlihat di 1280 & 360 px, tanpa geseran samping, sentuh >= 44 px, klik mengganti isi & URL, muat ulang & tombol kembali bekerja, tab per role, menu lama tidak ada. |
| `scripts/qa/test_t6b_input_wasilah.py` | Uji tulis Wasilah/Ghayah (29 uji, transaksi + ROLLBACK): salinan ke anggota, luar halaqah aman, anggota keluar aman, bulan 0/terkunci, item salah, RLS per role, Masul per domain, anon. |
| `scripts/qa/test_t6b_e2e.py` | E2E tampilan Wasilah/Ghayah: pilih -> label tampil, simpan -> database semua anggota, muat ulang -> label tetap; data uji dipulihkan. |
| `scripts/qa/test_t6a_tabel.py` | Uji baca T6a (14 uji): angka dari view, santri tanpa halaqah tidak muncul, bulan kosong bukan 0, HE DUMMY Wasilah/Ghayah = Al Qur'an bulan 1-7, kehadiran 0/0/0, anon 0 baris. |
| `scripts/qa/test_t7c_simpan_gabungan.py` | **T7c [2/3]** (18 uji, transaksi + ROLLBACK): simpan gabungan berhasil, ditolak tanpa target (capaian tak tersimpan), tuntas dikecualikan, bulan terakhir tanpa target, hak per role & lintas domain, target di bawah capaian, Level 6, lintas buku Tercapai/Kurang N, `v_monthly_report` Al Qur'an identik. |
| `scripts/qa/test_t7c_target_tujuan.py` | **T7c** (48 uji, transaksi + ROLLBACK): bentuk target (Al Qur'an panggilan lama tetap jalan; Wasilah/Ghayah wajib butir, amount ditolak jelas), constraint, satu target menunggu (penggantian + unique index), hak per role & lintas domain, bulk `setujui_target_halaqah` (termasuk bulan terkunci), ubah/batal, `v_monthly_report` Al Qur'an identik, DUMMY bentuk baru, dan tidak ada overload. |
| `scripts/qa/test_targets_t7.py` | T7 (34 uji, transaksi + ROLLBACK): role pengaju/penyetuju, Masul lintas domain, Mudir/Admin, anon, status tidak dipakai laporan, tolak wajib alasan, ubah baris baru, massal, riwayat, bulan 0, lewat/terkunci, kasus (f), individu vs halaqah, tiebreak, bulanan tidak dikali Hadir, tulis langsung ditolak. |
| `scripts/qa/verify_t7_report_unchanged.sql` | T7: bandingkan rumus laporan **sebelum** vs **sesudah** untuk seluruh 2.036 baris Al Qur'an; hasil 0 beda. |
| `scripts/qa/test_t7_target_tulis.py` | T7 [2/2] E2E **menulis lewat UI/RPC** (38 uji): pengampu ajukan -> Masul setujui (laporan pakai target baru), tolak + alasan (dilihat pengampu), batalkan, Masul lintas domain, bulan lewat/terkunci butuh konfirmasi Mudir/Admin, tab & URL 1280/360 px; semua target uji bertanda `note`, dipulihkan persis, sidik jari SAMA. |
| `scripts/db/fixes/2026-11-26_t7b_target_dummy_wasilah_ghayah.sql` | T7b: DUMMY bentuk LAMA - **DIGANTIKAN T7c, jangan dijalankan** (database menolak bentuk amount). |
| `scripts/db/fixes/2026-11-26_t7c_hapus_target_dummy_lama.sql` | **T7c**: hapus DUMMY bentuk lama (`amount = 1`, tanpa butir, catatan berpola koma). Idempoten; **tidak** menyentuh DUMMY bentuk baru. |
| `scripts/db/fixes/2026-11-26_t7c_target_dummy_tujuan.sql` | **T7c**: buat DUMMY bentuk baru (satu per halaqah x mapel, butir pertama, Syawwal 1447). Idempoten; wajib diganti data asli T8/T10. |
| `scripts/qa/test_input_dropdown_e2e.py` | Uji E2E **tampilan** dropdown Input: label terpilih setelah pilih dari daftar/pencarian, centang khatam, simpan -> database -> muat ulang; memulihkan data uji. Langkah a2 memakai bulan Jumadal Ula (bulan sebelumnya Rabiul Akhir terisi). |
| `scripts/qa/test_t7_target_ui.py` | T7 [2/2] E2E **baca-saja** (36 uji, 1280 & 360 px): tab & URL halaman Target, saringan, form, dialog aksi, riwayat, notifikasi target; konsol bersih. |
| `scripts/qa/repro_input_dropdown.py` | Reproduksi bug label dropdown per langkah + sapuan dropdown tiap role (Playwright). |
| `scripts/qa/serve_dist.py` | Server statis `dist/` (SPA) untuk mengukur hasil build tanpa `serve`. |
| `scripts/qa/compare_rabiul_awwal_excel.py` | Bandingkan HE/Hadir/izin-sakit-alpha/label+posisi capaian Rabiul Awwal DB vs Excel (109 santri, sampel 15); hanya baca. |
| `scripts/qa/test_data_awal_tahun_kedua.py` | Tahun kedua tanpa bulan 0; Syawwal 1448 membandingkan Ramadhan 1447 (transaksi + ROLLBACK). |
| `scripts/qa/smoke_e2e.py` | Smoke browser Playwright 7 role; Mudir menulis lalu menghapus satu capaian (`entered_at` baru saja). |
| `tests/putaran.test.mjs` | 6 uji aturan putaran (khatam +27, pengulangan -577, dll). |
| `tests/audit-rules.test.mjs` | 8 uji cermin rumus SPEC (posisi lintas buku, target×Hadir, mundur, khatam, bulan terkunci). |

---

## 5. Tabel database (`public`)

Semua 18 tabel ber-RLS aktif. Kolom yang ditulis di sini hanya yang penting.

| Tabel | Kolom utama | Relasi |
|---|---|---|
| `academic_years` | `id`, `hijri_year`, `name`, `is_active` | - |
| `hijri_months` | `id`, `academic_year_id`, `month_no` (0 = Data Awal, 1 = Syawwal ... 12 = Ramadhan), `name`, `semester`, `start_date`, `end_date` | `academic_year_id` → `academic_years` |
| `month_domain_settings` | `month_id`, `domain`, `effective_days`, `is_locked` | `month_id` → `hijri_months` |
| `subjects` | `id`, `domain`, `code`, `name`, `unit`, `sort_order`, `is_active` | - |
| `books` | `id`, `subject_id`, `name`, `stage_order`, `sort_order`, `is_cyclic`, `cycle_length`, `value_offset`, `is_active` | `subject_id` → `subjects` |
| `curriculum_items` | `id`, `book_id`, `label`, `detail`, `value`, `seq`, `is_active` | `book_id` → `books` |
| `students` | `id`, `nis`, `full_name`, `gender`, `angkatan`, `is_active` | - |
| `guardians` | `profile_id`, `student_id` | ke `profiles`, `students` |
| `student_levels` | `student_id`, `academic_year_id`, `domain`, `level_label` | ke `students`, `academic_years` |
| `profiles` | `id` (= `auth.users.id`), `full_name`, `role`, `gender`, `is_active` | - |
| `halaqahs` | `id`, `academic_year_id`, `domain`, `code`, `name`, `category`, `level_label`, `is_active` | `academic_year_id` → `academic_years` |
| `halaqah_members` | `id`, `halaqah_id`, `student_id`, `joined_on`, `left_on` | ke `halaqahs`, `students` |
| `halaqah_subjects` | `halaqah_id`, `subject_id` | ke `halaqahs`, `subjects` |
| `halaqah_teachers` | `id`, `halaqah_id`, `profile_id`, `subject_id`, `schedule_days`, `kbm_session`, `teacher_role` | ke `halaqahs`, `profiles`, `subjects` |
| `progress_entries` | `id`, `student_id`, `halaqah_id`, `subject_id`, `month_id`, `item_id`, `putaran`, `entered_by`, `entered_at` | ke `students`, `halaqahs`, `subjects`, `hijri_months`, `curriculum_items` |
| `attendance` | `student_id`, `month_id`, `domain`, `izin`, `sakit`, `alpha`, `effective_days_override` | ke `students`, `hijri_months` |
| `monthly_notes` | `student_id`, `month_id`, `domain`, `note` | ke `students`, `hijri_months` |
| `targets` | `id`, `domain`, `subject_id`, `student_id`, `halaqah_id`, `effective_month_id`, `amount`, `amount_period`, `status`, `proposed_by`, `approved_by`, `approved_at`, `alasan_tolak`, `rejected_by/at`, `entered_by/at`, `updated_by/at` | ke `subjects`, `students`, `halaqahs`, `hijri_months`, `profiles` |

Kunci unik penting: `progress_entries (student_id, subject_id, month_id)`, `attendance (student_id, month_id, domain)`, `monthly_notes (student_id, month_id, domain)`.

---

## 6. Fungsi dan view SQL

| Nama | Jenis | Fungsi |
|---|---|---|
| `item_position(item, putaran)` | fungsi | Posisi = `value + value_offset + (putaran-1) * cycle_length`. |
| `month_is_open(month, domain)` | fungsi | `not is_locked` untuk bulan+domain itu. |
| `current_app_role()` | fungsi | Role pengguna yang login. |
| `is_staff()` / `is_full_access()` / `is_any_masul()` | fungsi | Pemeriksaan hak akses dasar untuk RLS. |
| `is_masul_of(domain)` | fungsi | Apakah pengguna Masul untuk domain itu. |
| `can_manage(domain)` | fungsi | Boleh mengelola domain (Mudir/Admin/Masul domain). |
| `student_in_taught_domain(santri, domain)` | fungsi | Santri berada di halaqah domain itu yang diampu pengguna. |
| `student_in_taught_halaqah(santri, bidang)` | fungsi | Versi per mata pelajaran. |
| `teaches_halaqah_subject(halaqah, bidang)` | fungsi | Apakah pengguna mengampu mata pelajaran itu di halaqah itu. |
| `domain_of_subject(bidang)` / `domain_of_book(buku)` / `domain_of_halaqah(halaqah)` | fungsi | Menurunkan domain dari id. |
| `create_academic_year(tahun, nama, dengan_baseline)` | fungsi | Membuat tahun ajaran baru. |
| `resequence_subject(bidang)` | fungsi | Menomori ulang `value` item Wasilah/Ghayah; menolak Al Qur'an. |
| `reorder_items(buku, daftar_id)` | fungsi | Mengurutkan ulang item dalam satu buku. |
| `attendance_guard_override()` | trigger | Menjaga `effective_days_override` hanya boleh diisi Mudir/Admin. |
| `v_months_ordered` | view | Bulan berurutan + `prev_month_id` (bulan pembanding otomatis). |
| `v_monthly_report_base` | view | Dasar perhitungan laporan (posisi, posisi bulan lalu, kehadiran, target). |
| `v_monthly_report` | view | Laporan bulanan siap pakai: `pos`, `selisih`, `hadir`, `effective_days`, `target_monthly`, `below_target`, `attendance_short`, `item_label`, `prev_item_label`. **T7c [2/3]**: + `target_item_id, target_label, target_pos, target_tercapai, target_kurang, target_status` (Wasilah/Ghayah menampilkan tujuan akhir + status `Tercapai`/`Kurang N butir`; Al Qur'an NULL). |
| `v_attendance` | view | Kehadiran per santri/bulan/domain (Hadir dihitung database). |
| `target_bulan_berjalan(domain)` | fungsi | Bulan berjalan per domain (bulan non-0 dengan setting terbaru). |
| `target_info_konfirmasi` / `target_cek_konfirmasi` | fungsi | Deteksi bulan lewat/terkunci dan wajib konfirmasi. |
| `target_boleh_ajukan` / `target_validasi_bentuk` | fungsi | Cek hak pengaju dan bentuk target per domain. |
| `ajukan_target` / `setujui_target` / `tolak_target` | fungsi | RPC target (tolak wajib alasan). |
| `ubah_target` | fungsi | Membuat baris target baru; baris lama tetap. |
| `ajukan_target_massal_alquran` | fungsi | Membuat target Al Qur'an per santri dalam satu halaqah. |
| `riwayat_target` | fungsi | Riwayat target satu sasaran (santri/halaqah + mapel). |
| `batalkan_target` | fungsi | Pengaju membatalkan target `diajukan` (tidak menghapus). |
| `catat_jejak_target` | trigger | Mengisi `entered_*`/`updated_*` target. |
| `catat_perubahan` | trigger | Menulis `change_log` untuk UPDATE/DELETE `progress_entries`, `attendance`, `monthly_notes`, `targets`. |
