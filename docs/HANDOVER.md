# HANDOVER - serah terima KUSAFA

**Terakhir diperbarui**: 26 November 2026 (T7c [1/3]: target Wasilah/Ghayah = tujuan akhir di database + RPC + bulk + DUMMY baru + uji 48/48). Hash commit handover ini: lihat `git log -1`.

Dokumen ini adalah serah terima tetap. Sumber kebenaran status dan angka: `docs/STATUS.md`. Aturan bisnis: `docs/SPEC.md`. Jangan menulis rahasia (kata sandi, token, `DATABASE_URL` lengkap) atau data santri asli di sini.

---

## 1. Status per tahap

| Tahap | Nama | Status | File utama yang dibuat/diubah |
|---|---|---|---|
| A-G | Alat, proyek, Git, Supabase, seed, uji lokal, Vercel | **SELESAI** | `README.md`, `.env.example`, `supabase/config.toml`, `vercel.json`, `package.json` |
| T0 | Orientasi dan pemetaan Excel | **SELESAI** | `docs/DATA-NOTES.md`, `data/source/` (tidak di-commit) |
| T1 | Database dan seed dummy | **SELESAI** | `supabase/migrations/20261121000001`-`000009`, `scripts/seed/`, `supabase/seed/*.sql` |
| T2 | Login, kerangka, menu per role | **SELESAI** | `src/App.tsx`, `src/lib/auth.ts`, `src/components/Menu*.tsx`, `src/pages/LoginPage.tsx` |
| T3 | Tabel capaian halaqah Al Qur'an | **SELESAI** | `src/pages/TabelAlQuran.tsx`, `src/lib/laporan.ts`, `src/components/PemilihHalaqah.tsx` |
| T4 | Halaman satu santri | **SELESAI** | `src/pages/SantriPage.tsx`, grafik riwayat, `src/lib/laporan.ts` |
| T5 / T5b | Input capaian Al Qur'an | **SELESAI** | `src/pages/InputPage.tsx`, `src/components/DropdownCari.tsx`, `src/components/PemilihTahunBulan.tsx` |
| T5c / T5c-2 / T5c-3 | Percepat input, pencarian server, label dropdown | **SELESAI** | migrasi `20261124000011`-`000012`, `scripts/qa/test_input_dropdown_e2e.py` |
| Pra-T6 [1-6] | Audit, hardening, data, notifikasi, verifikasi | **SELESAI** | `scripts/qa/run_pre_t6_db_tests.py`, `regression_execute.py`, `test_auth_signup_closed.py`, migrasi `000010` |
| T6a | Tabel Ilmu Wasilah dan Ilmu Ghayah | **SELESAI** | `src/pages/TabelWasilah.tsx`, `src/components/TabDomain.tsx` (dipakai T6d) |
| T6b | Input Ilmu Wasilah dan Ilmu Ghayah | **SELESAI** | `src/pages/InputWasilahPage.tsx`, `src/components/FormInputWasilah.tsx`, migrasi `000013`-`000016` |
| T6c | "Bulan lalu" tampil sejak awal | **SELESAI** | `src/pages/TabelWasilah.tsx`, `src/lib/laporan.ts` |
| T6d | Tab domain di Capaian dan Input | **SELESAI** | `src/components/TabDomain.tsx`, `src/App.tsx`, menu tanpa submenu Capaian |
| T6d2 | Ketiga Masul boleh input semua halaqah domainnya + jejak pengisi | **SELESAI** | migrasi `000017`-`000018`, `src/lib/roles.ts`, `scripts/qa/test_t6d2_masul_input.py` |
| T6d3 | Pembersihan data + disiplin uji | **SELESAI** | `scripts/qa/db_fingerprint.py`, `pulihkan_data.py`, `test_seed_bersih.py`, `scripts/db/fixes/` |
| T6e | Hapus capaian (Mudir/Admin) + log perubahan | **SELESAI** | migrasi `000019`-`000020`, `hapus_capaian*`, `change_log`, `src/components/DialogHapusCapaian.tsx` |
| **T7 [1b/2]** | **Fondasi target dinamis (database + RPC + uji)** | **SELESAI** | migrasi `20261126000021`-`000031`, `scripts/qa/test_targets_t7.py`, `scripts/qa/verify_t7_report_unchanged.sql`, `scripts/db/fixes/2026-11-26_t7b_target_dummy_wasilah_ghayah.sql` |
| **T7 [2/2]** | **UI `/target` (daftar, ajukan, setujui/tolak, ubah, riwayat) + uji tulis** | **SELESAI** | `src/pages/TargetPage.tsx`, `TargetDomainPage.tsx`, `FormTarget.tsx`, `DialogAksiTarget.tsx`, `DialogRiwayatTarget.tsx`, `src/lib/target.ts`, `scripts/qa/test_t7_target_tulis.py` (38/38), E2E ulang + smoke produksi 42/42 |
| **T7c [1/3]** | **Target Wasilah/Ghayah = TUJUAN AKHIR (database, RPC, bulk, DUMMY, uji)** | **SELESAI** (lihat §2) | migrasi `20261126000032`, `test_t7c_target_tujuan.py` 48/48, `regression_execute.py` 8/8 |
| T8 | Kelola kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | **BELUM** | belum ada |
| T9 | Pengujian & QA penuh | **SEBAGIAN** | ± 25 skrip `scripts/qa/`; belum ada proyek Supabase QA terpisah; 3 sel RLS SKIP |
| T10 | Deploy akhir, hapus dummy, repo privat | **BELUM** | belum ada |

---

## 2. Tahap yang sedang dikerjakan: T7c [1/3] database target tujuan akhir (SELESAI); UI [2/3] belum

### Catatan dua penomoran (jangan tertukar)

- **A-G** = tahap **setup** (alat, proyek, Git, Supabase, seed, uji lokal, Vercel). "Tahap C" di
  `LANJUT-TAHAP-C-OPENCODE.md` (folder luar repo) adalah penomoran setup, **bukan** tahap kerja.
- **T0-T10** = tahap **kerja aplikasi** (`prompts/OPENCODE.md`). Status nyatanya ada di `docs/STATUS.md`.
- **T10 belum dimulai.** Frasa "T8/T10" di dokumen adalah pengingat pekerjaan berikutnya
  (mis. "target DUMMY diganti di T8/T10"), bukan tanda selesai. `git log` tidak punya commit T8/T9/T10.

### Yang sudah jalan (jangan diulang)

- Skema `targets` + kolom `alasan_tolak`, `rejected_by/at`, `entered_by/at`, `updated_by/at`; enum `target_status` termasuk `dibatalkan`.
- RPC: `ajukan_target`, `setujui_target`, `tolak_target`, `ubah_target`, `ajukan_target_massal_alquran`, `riwayat_target`, `batalkan_target`, helper `target_*`.
- Semua tulis langsung `targets` ditutup: policy INSERT/UPDATE/DELETE dihapus, privilege tulis dicabut dari `anon`/`authenticated`; hanya SELECT untuk staf.
- Trigger audit `catat_jejak_targets` dan `catat_perubahan_targets`; log UPDATE/DELETE `targets` teruji.
- View `v_monthly_report`: kasus (f), bulan 0 NULL, individu didahulukan, tiebreak deterministik, Wasilah/Ghayah bulanan tidak dikali Hadir.
- Target DUMMY Wasilah 25 + Ghayah 11 (izin Mudir), diganti T8/T10.
- Uji `test_targets_t7.py` **34/34 LULUS**; banding rumus lama vs baru 2.036 baris Al Qur'an **0 beda**; RLS **94/97 OK, 3 SKIP, 0 GAGAL**.
- **UI `/target`** (commit `653fec1`): daftar + saringan Tahun/Bulan terpisah, halaqah, mapel, status;
  form ajukan/ubah (termasuk massal Al Qur'an), konfirmasi bulan lewat/terkunci (checkbox hanya Mudir/Admin),
  setujui/tolak (alasan wajib)/batalkan, riwayat. Nama sasaran/mapel/bulan/pelaku diambil lewat embed
  PostgREST (tanpa mengunduh seluruh santri/profil). Kartu ringkas di HP 360 px.
- **Notifikasi target** di kotak "Data belum lengkap" (Masul domainnya/Mudir/Admin): jumlah menunggu
  persetujuan, jumlah target DUMMY, dan sasaran yang belum punya target (santri×mapel Al Qur'an,
  halaqah×mapel Wasilah/Ghayah).
- **Kolom target di laporan**: kosong ditampilkan `–` dan 0 tetap `0`; angka dari view (aturan (f)).
- Uji baca-saja `scripts/qa/test_t7_target_ui.py` **36/36 LULUS**; halaman siap **847 ms** (< 1,5 detik).
- **Uji UI yang MENULIS** (commit `5d377ac`): `scripts/qa/test_t7_target_tulis.py` **38/38 LULUS** lewat
  tampilan/RPC per role - pengampu ajukan (3 target `diajukan`), Masul Al Quran setujui (laporan
  `v_monthly_report` memakai target baru, 3×Hadir), tolak + alasan (pengampu melihat alasan), pengaju
  batalkan, Masul lintas domain dialihkan & tidak menyetujui, bulan lewat diblokir untuk pengampu dan
  butuh centang Mudir/Admin (berhasil), bulan terkunci butuh centang Mudir/Admin, tab & URL 1280/360 px.
  `pulihkan_data.py` mendapat parameter `urus` agar **baris target baru milik orang lain tidak dihapus**;
  sidik jari **SAMA**, `targets` kembali 363.
- **E2E ulang (26 Nov):** T6a **14/14**, T6b **14/14**, T6d2 **14/14**, T6e **16/16**, dropdown **10/10**,
  smoke produksi Vercel **42/42** (baca saja). Sidik jari/data dipulihkan tiap rangkaian.
- **T7c [1/3] (26 Nov):** migrasi `20261126000032_targets_tujuan_akhir` (kolom `target_item_id`,
  constraint `targets_bentuk_check`, unique index satu target menunggu, trigger butir aktif milik mapel);
  `setujui_target_halaqah` (bulk), alur "pengajuan baru menggantikan";
  **REVOKE EXECUTE dari PUBLIC + anon** untuk 15 fungsi target (sempat terbuka untuk 2 fungsi);
  DUMMY bentuk baru 25 Wasilah + 11 Ghayah. Uji `test_t7c_target_tujuan.py` **48/48**,
  `test_targets_t7.py` **34/34**, `regression_execute.py` **8/8**, RLS **94/97** (3 SKIP),
  E2E target baca-saja **36/36**, E2E tulis **38/38**, sidik jari **SAMA**. Rincian: STATUS 2q.

### Yang belum

- **T7c [2/3] = UI** BELUM: form Wasilah/Ghayah di `/target` masih mengirim `amount`, sehingga **pengajuan
  Wasilah/Ghayah dari UI ditolak database** (pesan jelas). Daftar/riwayat belum menampilkan butir tujuan
  akhir; laporan belum punya kolom target butir untuk Wasilah/Ghayah (angkanya NULL).
- **T7c [3/3]** (pembuktian akhir E2E + smoke) belum.
- **T8 belum dimulai** (menunggu perintah Mudir). Isinya: kelola kurikulum, halaqah, santri, kalender,
  **Hari Efektif & kunci bulan**; ganti target DUMMY Wasilah/Ghayah dengan angka asli.
- 3 sel matriks RLS masih SKIP (profil `wali`, target `diajukan` sebagai data tetap).
- Usulan proyek Supabase QA terpisah belum dibuat (T9/T10).

### Bug/error yang diketahui

1. **`test_t6e_hapus_capaian.py` butuh baris capaian bulan 8.** Data dummy tidak punya capaian bulan 8; uji berhasil 35/35 setelah satu baris sementara disisipkan lalu dihapus (sidik jari SAMA). Masalah prasyarat uji, bukan regresi.
2. **3 sel matriks RLS SKIP:** profil `wali` belum ada dan tidak ada target `diajukan` di data dummy.
3. **Uji dropdown a2 diperbaiki (data-dependent):** dulu memakai "Jumadal Akhir" yang bulan sebelumnya (Jumadal Ula, bulan 8) memang kosong di seed, sehingga "belum diisi" itu BENAR. Kini memakai "Jumadal Ula" (bulan sebelumnya Rabiul Akhir terisi) → 10/10. Logika aplikasi tidak diubah.
4. **`change_log`** append-only; sekarang **305** baris (bertambah karena uji yang menulis), baris lama utuh (sidik jari memeriksa log terpisah).
5. **Target DUMMY Wasilah/Ghayah** masih ada dan terbaca sebagai target nyata sampai diganti T8/T10
   (kini berbentuk **butir kurikulum**, tanpa angka).
6. **1 baris target Al Qur'an sisa uji T7 [2/2]** (Tahfidz, Santriwan fulan 26, Rabiul Akhir, amount 2,
   26 Nov 09:27 UTC) **tidak dihapus** sesuai perintah; tercatat di DATA-NOTES 0b. Perlu keputusan
   Mudir: dihapus atau dibiarkan sampai T10.
7. **Skrip `2026-11-26_t7b_target_dummy_wasilah_ghayah.sql` usang** (DUMMY bentuk lama); berkepala
   peringatan "JANGAN dijalankan lagi". Database otomatis menolaknya.
6. **Capaian Wasilah/Ghayah = 0 baris memang benar**: Excel tidak punya kolom capaian (lihat `docs/DATA-NOTES.md` bagian 12). Capaian asli diinput lewat aplikasi.
7. **Baris target baru manual Mudir** (bila ada di `/target`) **tidak dihapus** oleh uji; skrip melaporkan jumlah & isinya. Pada run terakhir: 0 baris.

### Langkah berikutnya (berurutan)

1. **T7c [1/3] selesai** (database + RPC + bulk + DUMMY + uji + dokumen).
2. **T7c [2/3] = UI `/target`** (menunggu perintah): form Wasilah/Ghayah memilih **butir tujuan akhir**
   (tanpa angka), daftar/riwayat menampilkan butir, tombol **"Setujui semua target halaqah ini"** (bulk),
   kewajiban target bulan depan saat input capaian, peringatan target di bawah capaian, tampilan
   Level 6 "Tuntas, belum ada pelajaran lanjutan".
3. **T7c [3/3]** pembuktian akhir (E2E + smoke produksi).
4. **Baru setelah T7 disetujui:** mulai **T8** (kurikulum, halaqah, santri, kalender, Hari Efektif & kunci
   bulan). Jangan mulai T8/T9 lebih awal. Saat T8: ganti DUMMY Wasilah/Ghayah dengan butir asli dari
   Mudir; isi Hari Efektif bulan 8-12 lewat layar (belum ada).

---

## 3. Keputusan yang sudah final (jangan diubah tanpa persetujuan Mudir)

### 3.1 Role dan hak akses

- Role lengkap: **Mudir**, **Admin**, **Masul Al Quran**, **Masul Wasilah**, **Masul Ghayah**, **Musyrif/ah**, **Mudarris/ah**, `wali` (belum aktif).
- Ketiga **Masul adalah penanggung jawab domain**: boleh input capaian, catatan, kehadiran di **semua halaqah domainnya**, bukan hanya yang tercatat di `halaqah_teachers`.
- Masul tetap **ditolak** di domain lain, bulan terkunci, bulan 0, dan **tidak boleh menghapus** capaian.
- Pengampu (Musyrif/ah, Mudarris/ah) hanya halaqah/mapel yang diampu.
- Hapus capaian dan baca `change_log`: **hanya Mudir/Admin**.
- Hari Efektif, kunci bulan, pengguna: **hanya Mudir/Admin**.

### 3.2 Target dinamis T7 (keputusan Mudir 26 November 2026)

- **(a) Pengaju/penyetuju:** pengampu mengajukan untuk santri/halaqah yang diampu; Masul menyetujui **hanya domainnya**; Mudir/Admin semua domain; pengampu tidak menyetujui. Target yang dibuat langsung Masul/Mudir/Admin otomatis `disetujui`.
- **(b) Ubah target:** membuat **baris baru** dengan `effective_month_id`; target lama utuh. Bulan lewat/terkunci hanya Mudir/Admin dengan konfirmasi eksplisit. Riwayat wajib tersedia.
- **(c) Bentuk:** Al Qur'an per **santri** per bidang, **harian**; massal per halaqah lalu sesuaikan per santri; individu didahulukan dari halaqah. Wasilah/Ghayah per **halaqah** per mata pelajaran, **bulanan langsung**, **tidak** dikali Hadir.
- **(d) Bulan berlaku:** dipilih saat mengajukan (default bulan berjalan); berlaku penuh sebulan, tidak dipecah, sampai diganti, lintas tahun ajaran. Bulan 0 tidak boleh menjadi bulan berlaku target.
- **(e) Penolakan:** alasan **wajib**; target tidak dihapus, tetap riwayat; pengaju boleh mengajukan ulang. Pengaju boleh membatalkan target yang masih `diajukan` lewat `batalkan_target`; target ditolak/disetujui tidak dihapus.
- **(f) `target_monthly`:** NULL bila tidak ada target, Hari Efektif belum diatur, atau bulan 0; **0** hanya bila target harian ada dan Hadir benar-benar 0; bulanan = `amount`.
- **(g) Ketiga domain** memakai mekanisme yang sama.
- **Tulis langsung ditutup:** policy INSERT/UPDATE/DELETE `targets` dihapus; privilege tulis dicabut dari `anon`/`authenticated`; semua perubahan lewat RPC (SECURITY DEFINER + cek hak internal). Anon tanpa `EXECUTE`.
- **DUMMY:** 25 target Wasilah + 11 Ghayah adalah DUMMY (izin Mudir), skrip idempoten di `scripts/db/fixes/2026-11-26_t7b_target_dummy_wasilah_ghayah.sql`; wajib diganti data asli T8/T10.

### 3.2a Keputusan T7c - target Wasilah/Ghayah = TUJUAN AKHIR (Mudir, 26 November 2026)

Berlaku di atas 3.2; menggantikan arti "bulanan = amount" untuk Wasilah/Ghayah.

- **Pemetaan mapel dari Excel BENAR sebagai kondisi saat ini** (`4-Ilmu Wasilah` sheet jadwal; `5-Ilmu Ghayah`). **Tidak ada perubahan data/seed.** Level Dasar B memang **sudah tuntas Baca dan Tulis**.
- **Pergantian mapel halaqah** = wewenang **Masul domainnya** atas usulan pengampu, **"berlaku mulai bulan X"**, **bukan otomatis**. Satu halaqah pindah mapel **serentak**. Layar/pengaturannya menyusul di **T8**.
- **Level 6 = tuntas semua mapel WASILAH**: tampil **"Tuntas, belum ada pelajaran lanjutan"**, **tidak** dihitung dalam notifikasi kekurangan. Kurikulum lanjutan mungkin ditambah kelak.
- **Target Wasilah/Ghayah = TUJUAN AKHIR**: satu butir kurikulum = **posisi akhir bulan depan**, **bukan jumlah**. Jumlah/angka hanya untuk **Al Qur'an** (tidak berubah).
- **Target bulan depan WAJIB diisi bersamaan input capaian bulan ini** untuk tiap mapel aktif; pengampu **tidak boleh mengosongkan**. Pengecualian: halaqah sudah di **butir terakhir** mapel (tuntas) -> target tidak wajib, status **"Tuntas, menunggu keputusan Masul"**.
- **Target di bawah capaian boleh** dengan **peringatan** (pengulangan).
- **Persetujuan:** pengampu mengajukan; **Masul domain/Mudir/Admin** menyetujui; ada **"Setujui semua target halaqah ini"** (bulk per halaqah x bulan). Bulan lewat/terkunci tetap hanya Mudir/Admin + konfirmasi.
- **Satu target menunggu** per (halaqah, mapel, bulan berlaku): pengajuan baru dari pengaju **menggantikan** yang masih `diajukan` (status lama menjadi `dibatalkan`); yang sudah `disetujui` diganti lewat `ubah_target` (baris baru).

- **Penerapan T7c [1/3] (26 November 2026):** kolom `targets.target_item_id` (FK `curriculum_items`),
  constraint `targets_bentuk_check` (Al Qur'an: `amount` + `harian`, per santri **atau** per halaqah;
  Wasilah/Ghayah: halaqah + butir, `amount` kosong), unique index `targets_satu_diajukan_uk`, trigger
  butir harus milik buku mapel itu & aktif. RPC: `ajukan_target`/`ubah_target` (parameter butir DEFAULT
  NULL agar panggilan lama tetap jalan), `setujui_target_halaqah` (bulk), `riwayat_target` menyertakan
  butir & buku. `REVOKE EXECUTE` dari PUBLIC + anon untuk seluruh keluarga fungsi target.

### 3.3 Struktur tabel dan view yang tidak boleh diubah sembarangan

- `targets`: `id`, `domain`, `subject_id`, `student_id`, `halaqah_id`, `effective_month_id`, `amount`, `amount_period`, `status`, `proposed_by`, `approved_by`, `approved_at`, `note`, `created_at`, `alasan_tolak`, `rejected_by`, `rejected_at`, `entered_by`, `entered_at`, `updated_by`, `updated_at`.
- Constraint: tepat satu dari `student_id`/`halaqah_id`; Al Qur'an per santri harian; Wasilah/Ghayah per halaqah bulanan.
- View: `v_monthly_report`, `v_monthly_report_base`, `v_attendance`, `v_months_ordered`.
- Rumus di database: posisi (`item_position`), selisih, Hadir, `target_monthly`, `below_target`, `attendance_short`. React **tidak** menghitung ulang.
- Migrasi lama **tidak boleh diubah**; perubahan skema selalu file baru nomor berikutnya.

### 3.4 Aturan data dan tampilan yang tetap

- **Bulan 0 (Data Awal)** bukan bulan input staf, bukan bulan efektif; `target_monthly` NULL; Syawwal tahun pertama membandingkan dengan bulan 0, tahun berikutnya dengan Ramadhan tahun lalu.
- **Hari Efektif kecil SAH**: Syawwal 1447 = 4 hari, Rabiul Awwal 1447 = 3 hari. Jangan diubah tanpa konfirmasi Mudir.
- **Hadir** = Hari Efektif - (izin + sakit + alpha); kolom H Excel diabaikan.
- **Selisih boleh negatif**; jangan dipaksa 0.
- Bulan belum diinput **kosong**, bukan 0.
- Konfirmasi "pengulangan atau khatam" hanya untuk bidang yang benar-benar diubah; bidang lain cukup penanda ⚠.
- Dropdown: tahun dan bulan **dua dropdown terpisah** (`PemilihTahunBulan`); halaqah menampilkan pengampu (`PemilihHalaqah`); semua daftar memakai `DropdownCari` dengan `LAPISAN_DROPDOWN = 60`; label item memakai nama mata pelajaran di depan.
- Pengampu hanya ditawari halaqah yang diampu (`hanyaHalaqahDiampu` di `src/lib/roles.ts`).
- Jangan mengambil daftar panjang tanpa batas; pakai `ambilSemua` atau `range`.
- Repo **PUBLIK** selama pengembangan; jangan commit rahasia/data santri asli. Sebelum data asli dimuat, repo wajib **PRIVAT**.

---

## 4. Status Supabase

- Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1` (Singapore).
- **Koneksi `DATABASE_URL`: pooler Supabase** (host `*.pooler.supabase.com`, port `5432`, user berawalan `postgres`), bukan koneksi langsung. Kata sandi hanya di `.env.local`, tidak dicatat di dokumen.
- **32 migrasi** tercatat di `supabase_migrations.schema_migrations`; terakhir **`20261126000032_targets_tujuan_akhir`**. Berikutnya wajib `20261126000033_...`.
- **19 tabel**, semuanya RLS aktif; **42 kebijakan**; **50 fungsi** public; **4 view**.
- **Semua 15 fungsi target** tanpa EXECUTE untuk `anon` maupun `PUBLIC`; RPC target ber-EXECUTE untuk `authenticated`.
- `targets` hanya punya policy SELECT; tulis lewat RPC. `change_log` hanya SELECT untuk Mudir/Admin, append-only.
- **Seed dummy 1447 sudah dimuat** dan **destruktif** (TRUNCATE). Jangan jalankan ulang tanpa perintah Mudir.
- Data sekarang: santri **109**, capaian **2.036**, kehadiran **599 Al Qur'an / 756 Wasilah / 749 Ghayah** (total 2.104), catatan 0, target **364** (328 Al Qur'an + 25 DUMMY Wasilah + 11 DUMMY Ghayah, bentuk tujuan akhir), `change_log` **356** baris.
- `month_domain_settings` hanya bulan 1-7; `is_locked` semua `false`; bulan 8-12 dan pengisian Hari Efektif adalah T8.
- **Matriks RLS:** 94 OK / 3 SKIP / 0 GAGAL. SKIP: profil `wali`, target `diajukan`.

---

## 5. Pertanyaan terbuka (menunggu Mudir)

1. **Repo masih PUBLIK.** Harus dijadikan privat sebelum data asli dimuat (`gh repo edit --visibility private --accept-visibility-change-consequences`). Wajib diingatkan lagi di T10.
2. **Data Awal 252 capaian**: dipertahankan atau dikosongkan saat data asli masuk? Keputusan T10.
3. **69 capaian dummy yang "mundur"** (lebih kecil dari bulan lalu): disepakati dibiarkan; konfirmasi ulang sebelum T9.
4. **Halaqah Level 6 (4 santri Wasilah)** belum punya mata pelajaran/pengampu. Apa yang harus ditampilkan/diisi? (T8).
5. **Hari Efektif bulan 8-12** (semua domain) belum ada; layar pengisiannya T8. Notifikasi "data belum lengkap" karena itu tidak memeriksa bulan-bulan tersebut.
6. **3 sel RLS SKIP**: perlu profil `wali` dan contoh target `diajukan` untuk diuji (T9).
7. **Target DUMMY Wasilah/Ghayah** (25 + 11): kapan data asli dimasukkan? Rencana T8/T10; perlu angka target asli dari Mudir.
8. **Proyek Supabase QA terpisah**: usulan belum dibuat; sekarang uji dan produksi memakai SATU database.
9. **Retensi `change_log`**: belum ada pemangkasan; perlu keputusan bila log dianggap terlalu besar.
10. **1 baris target sisa uji** (STATUS 2q, DATA-NOTES 0b): dihapus atau dibiarkan sampai T10?
11. **Pemetaan mapel Excel benar** (keputusan Mudir 26 Nov 2026, 3.2a) - tidak ada perubahan data; layar penggantian mapel & kewajiban target bulan depan masuk T7c [2/3] / T8.

---

## 6. Cara menjalankan, menguji, dan deploy

### Menjalankan

```bash
cd kusafa-app
npm install
npm run dev            # http://localhost:5173 atau port berikutnya
```

Environment Vercel hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`. **Jangan** menaruh service role key di frontend.

### Menguji

```bash
npm run typecheck      # wajib hijau
npm run test           # 14 uji aturan putaran
npm run build          # wajib berhasil
python scripts/check_repo_safety.py   # wajib lolos sebelum push
```

Uji database (membaca `.env.local`, tidak mencetak rahasia; sebagian menulis + ROLLBACK):

```bash
python scripts/qa/test_t7c_target_tujuan.py      # 48/48 (baru, T7c)
python scripts/qa/test_targets_t7.py             # 34/34
python scripts/qa/verify_t7_report_unchanged.sql # 2.036 baris, 0 beda
python scripts/qa/test_t6e_hapus_capaian.py      # 35/35 (perlu baris bulan 8 sementara)
python scripts/qa/rls_matrix.py                  # 94/97 (3 SKIP)
python scripts/qa/run_pre_t6_db_tests.py         # 16/16
python scripts/qa/regression_execute.py          # 7/7
python scripts/qa/test_t6a_tabel.py              # 14/14
python scripts/qa/test_t6b_input_wasilah.py      # 29/29
python scripts/qa/test_t6d2_masul_input.py       # 68/68
python scripts/qa/test_seed_bersih.py            # 6/6
python scripts/qa/compare_alquran_full_excel.py  # 7/7
python scripts/qa/compare_rabiul_awwal_excel.py  # 7/7
python scripts/qa/test_data_awal_tahun_kedua.py  # 5/5
python scripts/qa/test_no_halaqah.py             # 9/9
python scripts/qa/test_students_without_halaqah.py    # 13/13
python scripts/qa/test_students_without_halaqah_p6.py # 6/7 (1 SKIP wali)
python scripts/qa/test_auth_signup_closed.py     # 9/9
```

Sidik jari database (wajib untuk uji yang menulis):

```bash
python scripts/qa/db_fingerprint.py --simpan /tmp/fp_sebelum.json
# ...jalankan uji...
python scripts/qa/db_fingerprint.py --banding /tmp/fp_sebelum.json   # harus "SAMA"
```

E2E browser memakai Playwright dan `dist/` yang disajikan:

```bash
npm run build
python3 scripts/qa/serve_dist.py 4173 &
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/smoke_e2e.py
```

### Deploy

```bash
git push origin main
```

Vercel otomatis membangun project `kusafa-app`. Verifikasi HTTP 200 dan bundel `dist/assets/index-*.js` sama dengan build lokal. Smoke produksi **baca saja**; jangan menulis di produksi tanpa pemulihan + sidik jari.

### Aturan uji yang mengikat

- Database lokal = produksi (satu Supabase). Uji yang menulis hanya boleh menyentuh baris yang dibuatnya sendiri, menyimpan lebih dulu, memulihkan di `finally`, lalu **sidik jari wajib SAMA**.
- `change_log` append-only: boleh tumbuh, baris lama wajib utuh; `db_fingerprint.py` memeriksa log terpisah.
- Seed ulang menghidupkan data yang sudah dihapus. Setiap penghapusan yang disetujui wajib punya skrip idempoten di `scripts/db/fixes/`.
- Uji banding Excel harus **penuh**, bukan sampel.
