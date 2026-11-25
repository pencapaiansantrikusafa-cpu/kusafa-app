# CHANGELOG - ringkasan perubahan per tahap

Disusun dari riwayat Git (diperiksa 23 November 2026). Tanggal memakai waktu komit lokal.
Ini ringkasan, bukan daftar komit lengkap; daftar lengkap ada di `git log`.

---

## 25 November 2026 - T6d3 (pembersihan data + disiplin uji)

- **7 baris kehadiran Ramadhan** (Al Qur'an, tanpa capaian) dihapus lagi. Penyebab munculnya: seed dijalankan ulang 24 Nov; penghapusan 23 Nov tidak pernah dibuat skrip. Skrip baru `scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql` + uji penjaga `scripts/qa/test_seed_bersih.py`. Kehadiran Al Qur'an 613 → 606.
- **Nilai izin/sakit/alpha Shafar** dipulihkan sesuai seed/Excel (37 baris yang berbeda) lewat `scripts/db/fixes/2026-11-25_pulihkan_shafar.sql`; penyebab perbedaan dilaporkan (perubahan manual di luar repo sebelum T6d2, tidak ada jejak).
- **Rekonsiliasi 2.039 vs 2.038:** 1 baris seed hilang — `1443.dummy-nis.024` Kitabah Dzul Qa'dah "Menyalin - 25" — dipulihkan (`2026-11-25_pulihkan_capaian_024.sql`). Total capaian kembali 2.039.
- **Uji banding Excel penuh** `scripts/qa/compare_alquran_full_excel.py` (7/7): 109 santri, 599 pasangan santri-bulan, 1.673 sel capaian.
- **Sidik jari database** `scripts/qa/db_fingerprint.py` (18 tabel, jumlah + checksum) dan `scripts/qa/pulihkan_data.py` (pemulihan persis). Semua uji yang menulis memakainya; **smoke produksi hanya membaca**.
- Uji lama `test_input_dropdown_e2e.py` ternyata menghapus 20 baris seed saat dijalankan (dalam sesi ini); sudah diperbaiki dan barisnya dipulihkan dengan `scripts/db/fixes/2026-11-25_pulihkan_data_seed.py`.
- `AGENTS.md`: bagian "Disiplin data dan uji" ditambahkan.

---

## 25 November 2026 - T6d2 (seragamkan hak input Masul + jejak pengisi)

- **Keputusan Mudir:** Masul Al Quran, Masul Wasilah, dan Masul Ghayah boleh **input capaian, catatan, dan kehadiran di SEMUA halaqah domainnya**. Tetap ditolak: domain lain, bulan terkunci, bulan 0, menghapus. Pengampu tetap hanya halaqahnya. Menggantikan keputusan 3d.
- **Migrasi `20261125000017_masul_input_domain.sql`**: satu aturan tulis untuk ketiga domain; policy khusus `wasilah`/`ghayah` dihapus; kolom `updated_by`/`updated_at` + trigger `catat_jejak` pada capaian, kehadiran, catatan.
- **Migrasi `20261125000018_catat_jejak_tanpa_jwt.sql`**: trigger tidak menyentuh baris lama saat `auth.uid()` NULL (seed/skrip), agar jejak seed tidak tertimpa.
- **Kode**: `roles.ts` (`hanyaHalaqahDiampu` kini hanya Musyrif/ah & Mudarris/ah, fungsi baru `bolehInputDomain`), `InputAlQuranPage.tsx`, `InputWasilahPage.tsx`, `TabelCapaian.tsx` (`ambilSemua` menggantikan `.limit(2000)`).
- **Uji**: `test_t6d2_masul_input.py` **68/68**; `test_t6d2_e2e_masul.py` **14/14**; matriks RLS **67 OK / 8 SKIP / 0 GAGAL**; seluruh uji lama hijau (T6a 14/14, T6b 29/29, DB 16/16, regresi 7/7, Excel 7/7, smoke).
- **Perbaikan data**: 1 baris capaian Wasilah sisa uji matriks dihapus; 1 baris kehadiran Ghayah yang hilang dipulihkan; kedua skrip uji diperbaiki agar tidak lagi meninggalkan/menghapus baris (baris sasaran uji hapus kini dibuat di dalam transaksi; uji T6d2 memeriksa hitungan per domain).
- Dokumen: STATUS 2k + catatan data terbuka, HANDOVER 3f (menggantikan 3d) & 3g, SPEC bagian 3 dan 8, FILE-MAP.

---

### Langkah [6] - Jawaban Mudir + verifikasi & penutupan celah
- **Signup**: celah ditemukan — signup tertutup hanya karena provider email dimatikan, yang **ikut mematikan login**; dengan email valid signup berhasil. Ditutup dengan `disable_signup=true` (provider email aktif). Uji `scripts/qa/test_auth_signup_closed.py` **9/9**.
- **`students_without_halaqah`**: jalur "tampil semua" hanya untuk koneksi admin tanpa JWT (skrip lokal/service_role) — dipertahankan; authenticated tanpa profil/musyrif/mudarris **0 baris**, anon ditolak. Uji `test_students_without_halaqah_p6.py` 6/7 (1 SKIP).
- **`attendance_guard_override`**: migrasi `20261124000010_attendance_guard_revoke.sql` mencabut EXECUTE dari authenticated/PUBLIC/anon; trigger tetap jalan.
- **Uji regresi** `scripts/qa/regression_execute.py` **7/7**: 20 fungsi public tanpa EXECUTE anon; musyrif tak bisa mengubah data lewat fungsi admin.
- **Uji DB pra-T6** kini **16/16**; uji Rabiul Awwal mengharapkan 19 — **DIKOREKSI di [6a] menjadi 3**.
- **Smoke E2E browser** `scripts/qa/smoke_e2e.py`: 29/29 lokal (7 role, Mudir simpan+hapus satu capaian), 29/29 di react-router 7, 28/28 produksi.
- **react-router 7.18.6 di-merge** ke `main` setelah smoke lulus (izin Mudir); `npm audit` react-router bersih.
- **Data Awal tahun kedua**: tanpa bulan 0, Syawwal 1448 membandingkan Ramadhan 1447; ditulis di `docs/SPEC.md` 4a-1; uji `test_data_awal_tahun_kedua.py` 5/5.
- `docs/DATA-NOTES.md`: rentang Excel dikoreksi `BZ5:B113` → `BZ5:BZ113`. Favicon ditambahkan (menghapus 404 konsol).

### Langkah [6a] - Koreksi data: Hari Efektif Rabiul Awwal = 3 (24 November 2026)
- **Koreksi Mudir:** Hari Efektif Rabiul Awwal (bulan 6, Al Qur'an) = **3 hari** adalah **BENAR** (libur ~2 pekan lebih). Perubahan 3→19 adalah kekeliruan.
- Pemulihan 19→3: `scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql`. Skrip lama 3→19 **dibatalkan** (penghenti keras, hanya riwayat).
- Bukti: `scripts/qa/compare_rabiul_awwal_excel.py` **7/7 PASS** — HE, Hadir, izin/sakit/alpha, label+posisi capaian cocok dengan Excel untuk 109 santri; sampel 15. Tidak ada kolom turunan tersimpan yang berubah (Hadir/selisih dihitung view).
- Uji `run_pre_t6_db_tests.py` kembali mengharapkan **3** (`E_hari_efektif_rabiul_awwal_3`), 16/16 PASS. Seluruh QA lain hijau; smoke E2E 29/29.
- `AGENTS.md`: ditambahkan aturan "nilai Hari Efektif kecil bisa sah (libur); jangan diubah tanpa konfirmasi Mudir".
- Dokumen diselaraskan: DATA-NOTES 3a, SPEC 4a-2, STATUS, HANDOVER 3b, FILE-MAP.

### T5c - Percepat halaman Input Al Qur'an (pencarian item di server)
- Migrasi `20261124000011_curriculum_search.sql`: RPC `curriculum_items_search(subject, q, limit 60)` & `curriculum_items_by_ids(ids)`; indeks GIN trigram pada label; `pg_trgm` di skema `extensions`.
- `DropdownCari` mendapat mode `diServer` (tunda 200 ms, urutan skor sama dengan versi klien); `InputPage` tidak lagi mengunduh 9.177 item; `KotakBelumLengkap` memakai data halaqah & pengampu dari halaman induk.
- Hasil: halaman siap **3,0-4,0 s -> 1,44-1,95 s**; permintaan item **128 -> 2**; payload ~1,4 MB -> ~0,55 MB. **Target <1 detik belum** (penundaan jaringan). Perhitungan identik (114 baris dibandingkan).
- Uji regresi menangkap 31 fungsi ekstensi terbuka ke anon -> dipindah ke skema `extensions`; kini 0.
- QA: `npm test` 14/14, tsc/build lulus, DB 16/16, regresi 7/7, smoke E2E 29/29.

### T5c-2 - Satu permintaan per tahap halaman Input (25 November 2026)
- Migrasi `20261124000012_input_alquran_data.sql`: RPC `input_alquran_boot()` dan `input_alquran_data(halaqah, bulan, bulan_lalu)`.
  `SECURITY INVOKER`, cek `is_staff()`, EXECUTE hanya authenticated/service_role, anon ditolak.
- `InputPage`: ±20 permintaan berurutan -> **2 RPC**; aturan "hanya halaqah diampu" tetap di React; nama halaqah tidak dikirim.
- `KotakBelumLengkap`: opsi `tunda` agar tidak menahan form.
- Hasil: halaman siap **1,44-1,95 s -> 0,97 s median produksi** (0,93-0,99 s lokal); HP 360 ~0,95-1,05 s; permintaan data 3.
- Perhitungan identik (114 baris; paket RPC vs view: 0 beda). QA: npm test 14/14, DB 16/16, regresi 7/7, smoke 29/29 lokal & 28/28 produksi.

### T6d - Tab domain di halaman Capaian (25 November 2026)
- `src/components/TabDomain.tsx` (baru, komponen bersama): tab Al Qur'an / Ilmu Wasilah / Ilmu Ghayah memakai `<Link>`, jadi tab aktif tercermin di URL. HP 360: tiga tab dibagi rata, tinggi sentuh 44 px, tanpa geseran samping; desktop: sebaris.
- `CapaianPage` memakai tab; `InputPage` memakai komponen yang sama (fungsi `PemilihDomain` lama dihapus — tidak ada duplikat).
- Menu Capaian tidak lagi ber-submenu di menu samping/bilah bawah (digantikan tab). `roles.ts`: `DOMAIN_URUT`, `domainCapaianUntuk`.
- Hak akses tidak berubah: ketiga domain tetap dapat dilihat semua staf (RLS `is_staff`); RLS/view/perhitungan tidak disentuh.
- Uji `test_t6d_tab_capaian.py` **28/28** lokal & produksi; smoke 43/43 lokal, 42/42 produksi.

### T6b - Input Ilmu Wasilah & Ilmu Ghayah (25 November 2026)
- Migrasi `000013`: `wasilah_input_boot`, `wasilah_input_form`, `wasilah_input_save`, `wasilah_can_write`. Input sekali per halaqah x mapel, disalin ke semua anggota aktif dalam satu transaksi (semua-atau-tidak-sama-sekali). Bulan 0 & bulan terkunci ditolak. SECURITY INVOKER, cek staf di dalam fungsi, anon tanpa EXECUTE.
- Migrasi `000014`: Hadir & Hari Efektif dari `v_attendance` (sebelumnya form menghitung di React - dilarang).
- Migrasi `000015`: keputusan Mudir - Masul Wasilah/Ghayah = penanggung jawab domain (policy tulis).
- Migrasi `000016`: koreksi temuan uji - policy 000015 ikut memberi Masul Al Quran akses semua halaqah Al Qur'an; dibatasi ke wasilah/ghayah.
- Halaman `/input/wasilah` & `/input/ghayah` (plus `/input/alquran`): satu RPC per tahap, pencarian item di server, satu dropdown per mata pelajaran. Halaman siap **0,86-0,87 s**.
- Uji: DB `test_t6b_input_wasilah.py` **29/29**; E2E `test_t6b_e2e.py` **14/14**; matriks RLS **44 OK/8 SKIP/0 GAGAL**; smoke per role **43/43**.

### T6c - "Bulan lalu" tampil sejak awal (25 November 2026)
- Laporan Mudir: keterangan "Bulan lalu" baru muncul setelah item dipilih. Kini selalu tampil, termasuk saat dropdown masih kosong; datanya dari view.
- Uji E2E Al Qur'an bertambah langkah a2 (bulan Jumadal Akhir): 3 dropdown kosong + "Bulan lalu" berisi. **10/10**.

### T6a - Tabel capaian Ilmu Wasilah & Ilmu Ghayah (25 November 2026)
- `src/pages/TabelWasilah.tsx` (baru): per mata pelajaran Lalu / Kini / Selisih / target, lalu tabel anggota Nama Santri, Hadir/HE, Izin, Sakit, Alpha, Catatan (SPEC 5.6). Semua angka dari `v_monthly_report`/`v_attendance`.
- `TabelCapaian.tsx`: tulisan "dikerjakan pada T6" dihapus; anggota hanya `left_on is null`; mata pelajaran dari `halaqah_subjects`.
- `PemilihTahunBulan.tsx`: notifikasi "data belum lengkap" per domain (dulu selalu "capaian Al Qur'an").
- **DUMMY (izin Mudir):** `scripts/db/fixes/2026-11-25_he_wasilah_ghayah_dummy.sql` - Hari Efektif Wasilah/Ghayah = Al Qur'an bulan 1-7 + kehadiran 0/0/0. Excel sumber tidak punya kolom HE. Wajib diganti data asli (T8/T10).
- Uji `scripts/qa/test_t6a_tabel.py` **14/14**; tampilan diuji Playwright (Mudir) untuk kedua domain, konsol bersih.

### T5c-3 - Perbaikan bug label dropdown Input (25 November 2026)
- **Laporan Mudir (produksi):** setelah memilih item, dropdown tetap menulis "— belum diisi —".
- **Akar masalah:** pada mode pencarian server (T5c), `opsi` dropdown hanya berisi item yang sudah tersimpan; item yang baru dipilih tidak masuk daftar sehingga `DropdownCari` tidak menemukan labelnya. Akibat turunan: keterangan "Bulan lalu" dan centang "khatam" juga tidak muncul karena item baru tidak dikenali.
- **Perbaikan:** `DropdownCari` menyimpan objek pilihan (nilai+label+siklik) dan meneruskannya lewat `onChange`; `FormInputAlQuran` menyimpan item baru beserta label & siklik; `InputPage` menyertakan `siklik` pada hasil cari dan membuang `itemTambahan` yang menduplikasi `items`.
- **Data:** 2.036 baris tetap utuh; 0 baris baru hari ini. Uji E2E menyimpan satu capaian dummy lalu mengembalikan baris itu persis (diverifikasi).
- **Celah uji lama:** smoke hanya memeriksa halaman termuat & simpan, tidak teks tombol dropdown. Uji baru `scripts/qa/test_input_dropdown_e2e.py` **9/9 LULUS**: label tampil setelah pilih dari daftar/pencarian, khatam muncul, simpan -> database cocok -> muat ulang label tetap tampil. Reproduksi: `scripts/qa/repro_input_dropdown.py`.
- QA lain hijau: npm test 14/14, DB 16/16, regresi 7/7, Excel 7/7, RLS 38 OK/8 SKIP/0 GAGAL, smoke 29/29 lokal.

### Langkah [1] - Audit dan hardening fungsi
- Daftar 18 fungsi public; migrasi `20261121000007_harden_function_grants.sql`: cabut `EXECUTE` anon/PUBLIC, grant hanya authenticated+service_role, `SET search_path` fungsi INVOKER.
- Uji DB pra-T6 (`scripts/qa/run_pre_t6_db_tests.py`).

### Langkah [2] - Keputusan bulan 0 dan santri tanpa halaqah
- Aturan bulan 0 (Data Awal) ditetapkan: bukan bulan efektif/target, bukan bulan input staf; migrasi `20261121000008_month_zero_not_open.sql` (`month_is_open(bulan 0)=false`).
- NIS 023/024 dibiarkan sebagai kasus uji "santri yang tidak ikut semua halaqah"; `scripts/qa/test_no_halaqah.py` (9/9 PASS).

### Langkah [3] - Perbaikan data
- ~~Hari Efektif Rabiul Awwal 3→19~~ **DIBATALKAN 24 Nov 2026:** 3 hari adalah nilai **BENAR** (libur ~2 pekan lebih). Lihat koreksi [6a].

### Langkah [4] - Notifikasi "santri belum punya halaqah"
- Migrasi `20261121000009_students_without_halaqah.sql`: fungsi `students_without_halaqah`(_count) security definer, cek `can_manage`, revoke anon.
- UI di `KotakBelumLengkap.tsx` (perluasan "data belum lengkap", bukan sistem baru). Uji 13/13 PASS.

### Langkah [5] - Audit lengkap + dokumentasi
- Matriks RLS otomatis `scripts/qa/rls_matrix.py` (38/46 OK, 8 SKIP, 0 GAGAL).
- Uji unit `tests/audit-rules.test.mjs` (npm test 14/14).
- Analisis kinerja muat item (9.177 item Al Qur'an) + 3 opsi; **belum diubah**.
- react-router: kedua advisory tertambal hanya di mayor 7; diuji di branch `chore/react-router-fix` (tidak di-merge).
- Rencana ESLint; `check_repo_safety.py` diperkuat (pola VERCEL_OIDC_TOKEN, sb_secret, service_role, postgres://).
- `npm run typecheck` dan `npm run build` lulus.

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

### Audit dokumentasi dan verifikasi kondisi nyata (sesi ini)
- **Diperiksa langsung**: `npx tsc --noEmit` lulus (0 galat), `npm run build` berhasil (2,34 dtk, 475,43 kB/gzip 136,20 kB), `npm run test` 6/6 lulus, `python scripts/check_repo_safety.py` lolos. Tidak ada skrip `lint`.
- **Supabase diverifikasi via query**: 6 migrasi tercatat, 18 tabel semua RLS aktif (44 kebijakan), 4 view, 18 fungsi `public`, hitung baris tabel sesuai STATUS, `month_domain_settings` hanya domain `alquran` bulan 1-7, 7 presensi Ramadhan tanpa capaian memang sudah 0 (599 presensi).
- **Vercel/produksi**: situs `https://kusafa-app.vercel.app` HTTP 200; bundel produksi sama dengan build lokal commit `cdb7c98`.
- **Dokumen diperbarui**: `docs/STATUS.md`, `docs/HANDOVER.md`, `docs/FILE-MAP.md`, `docs/DATA-NOTES.md`, `README.md`, `docs/CHANGELOG.md` disesuaikan dengan fakta terverifikasi. Koreksi: fungsi `public` = 18 (bukan 19); kerentanan npm = 2 sedang (`react-router`/`react-router-dom`).
- **Tidak ada perubahan logika aplikasi.** Tidak ada rahasia/data santri yang di-commit.

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
