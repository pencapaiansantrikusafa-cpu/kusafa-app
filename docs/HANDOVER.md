# HANDOVER - serah terima KUSAFA

**Terakhir diperbarui**: 27 November 2026, 06:41 (waktu lokal), commit terakhir **`73970ab`** (`main`, sudah di-push).
Dokumen ini serah terima tetap. Sumber kebenaran status dan angka: `docs/STATUS.md`. Aturan bisnis: `docs/SPEC.md`.
Jangan menulis rahasia (kata sandi, token, `DATABASE_URL` lengkap) atau data santri asli di sini.

---

## 1. Status per tahap

| Tahap | Nama | Status | File utama yang dibuat/diubah |
|---|---|---|---|
| A-G | Alat, proyek, Git, Supabase, seed, uji lokal, Vercel | **SELESAI** | `README.md`, `.env.example`, `supabase/config.toml`, `vercel.json`, `package.json` |
| T0 | Orientasi dan pemetaan Excel | **SELESAI** | `docs/DATA-NOTES.md`, `data/source/` (tidak di-commit) |
| T1 | Database dan seed dummy | **SELESAI** | `supabase/migrations/20261121000001`-`000009`, `scripts/seed/`, `supabase/seed/*.sql` |
| T2 | Login, kerangka, menu per role | **SELESAI** | `src/App.tsx`, `src/lib/auth.ts`, `src/lib/roles.ts`, `src/components/Menu*.tsx`, `src/pages/LoginPage.tsx` |
| T3 | Tabel capaian halaqah Al Qur'an | **SELESAI** | `src/pages/TabelAlQuran.tsx`, `src/lib/laporan.ts`, `src/components/PemilihHalaqah.tsx` |
| T4 | Halaman satu santri | **SELESAI** | `src/pages/SantriPage.tsx`, `src/components/GrafikGaris.tsx`, `GrafikGabungan.tsx` |
| T5 / T5b / T5c / T5c-2 / T5c-3 | Input capaian Al Qur'an, percepat input, pencarian item di server, perbaikan label dropdown | **SELESAI** | `src/pages/InputPage.tsx`, `FormInputAlQuran.tsx`, `DropdownCari.tsx`, `PemilihTahunBulan.tsx`, migrasi `000011`-`000012`, `scripts/qa/test_input_dropdown_e2e.py` |
| Pra-T6 [1-6] | Audit, hardening, data, notifikasi, verifikasi, signup tertutup | **SELESAI** | `scripts/qa/run_pre_t6_db_tests.py`, `regression_execute.py`, `rls_matrix.py`, migrasi `000008`-`000010` |
| T6a | Tabel Ilmu Wasilah dan Ilmu Ghayah | **SELESAI** | `src/pages/TabelWasilah.tsx`, `src/components/TabDomain.tsx` (dipakai T6d), `scripts/qa/test_t6a_tabel.py` |
| T6b / T6c | Input Wasilah dan Ghayah, "Bulan lalu" tampil sejak awal | **SELESAI** | `src/pages/InputWasilahPage.tsx`, `FormInputWasilah.tsx`, migrasi `000013`-`000016` |
| T6d | Tab domain di Capaian dan Input | **SELESAI** | `src/components/TabDomain.tsx`, `src/App.tsx` |
| T6d2 | Ketiga Masul boleh input semua halaqah domainnya + jejak pengisi | **SELESAI** | migrasi `000017`-`000018`, `scripts/qa/test_t6d2_masul_input.py` (68/68) |
| T6d3 | Pembersihan data + disiplin uji (sidik jari, seed bersih, banding Excel penuh) | **SELESAI** | `scripts/qa/db_fingerprint.py`, `pulihkan_data.py`, `test_seed_bersih.py`, `scripts/db/fixes/` |
| T6e | Hapus capaian (Mudir/Admin) + log perubahan | **SELESAI** | migrasi `000019`-`000020`, `hapus_capaian*`, `change_log`, `DialogHapusCapaian.tsx` |
| T7 [1b/2] | Fondasi target dinamis (database, RPC, uji) | **SELESAI** | migrasi `000021`-`000031`, `scripts/qa/test_targets_t7.py`, `scripts/qa/verify_t7_report_unchanged.sql` |
| T7 [2/2] | UI `/target` (daftar, ajukan, setujui/tolak, ubah, riwayat) + uji tulis | **SELESAI** | `src/pages/TargetPage.tsx`, `TargetDomainPage.tsx`, `FormTarget.tsx`, `DialogAksiTarget.tsx`, `DialogRiwayatTarget.tsx`, `src/lib/target.ts`, `test_t7_target_ui.py` 36/36, `test_t7_target_tulis.py` 38/38 |
| **T7c [1/3]** | **Target Wasilah/Ghayah = TUJUAN AKHIR (butir kurikulum): database, RPC, bulk, DUMMY, uji** | **SELESAI** | migrasi `20261126000032_targets_tujuan_akhir.sql`, `scripts/db/fixes/2026-11-26_t7c_*.sql`, `scripts/qa/test_t7c_target_tujuan.py` (48/48) |
| T7c [2/3] | UI target Wasilah/Ghayah: pilih butir, tampilkan butir, bulk di layar, kewajiban target bulan depan | **BELUM** | belum ada |
| T7c [3/3] | Pembuktian akhir T7c (E2E penuh + smoke produksi) | **BELUM** | belum ada |
| T8 | Kelola kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan**, pergantian mapel halaqah | **BELUM** | rute `/kurikulum`, `/halaqah`, `/pengaturan` masih `PlaceholderPage` |
| T9 | Pengujian & QA penuh | **SEBAGIAN** | ± 27 skrip `scripts/qa/`; belum ada proyek Supabase QA terpisah; 3 sel RLS SKIP |
| T10 | Deploy akhir, hapus dummy, repo privat | **BELUM** | belum ada |

Catatan dua penomoran: **A-G** = setup (bukan tahap kerja). **T0-T10** = tahap kerja (`prompts/OPENCODE.md`). Frasa "T8/T10" di dokumen adalah pengingat pekerjaan berikutnya, bukan tanda selesai.

---

## 2. Tahap yang sedang dikerjakan: T7c [1/3] selesai, UI [2/3] belum

### Yang sudah jalan (jangan diulang)

- Skema target T7: `targets` + `alasan_tolak`, `rejected_by/at`, `entered_by/at`, `updated_by/at`; enum `target_status` termasuk `dibatalkan`.
- RPC T7: `ajukan_target`, `setujui_target`, `tolak_target`, `ubah_target`, `ajukan_target_massal_alquran`, `riwayat_target`, `batalkan_target`, helper `target_*`.
- Tulis langsung `targets` ditutup: policy INSERT/UPDATE/DELETE dihapus, privilege tulis dicabut dari `anon`/`authenticated`; hanya SELECT untuk staf. Semua perubahan lewat RPC.
- Trigger audit `catat_jejak_targets` dan `catat_perubahan_targets`; UPDATE/DELETE `targets` tercatat di `change_log`.
- View `v_monthly_report` (kasus f, bulan 0 NULL, individu didahulukan, tiebreak deterministik); Al Qur'an: `target_monthly` = jumlah x Hadir.
- UI `/target` (T7 [2/2]): daftar + saringan Tahun/Bulan terpisah, halaqah, mapel, status; form ajukan/ubah termasuk massal Al Qur'an; setujui/tolak (alasan wajib)/batalkan; riwayat; konfirmasi bulan lewat/terkunci (hanya Mudir/Admin).
- Notifikasi target di kotak "Data belum lengkap"; kolom target di laporan (kosong `–`, 0 tetap `0`).
- **T7c [1/3] (26 November 2026)**: kolom `targets.target_item_id` (FK `curriculum_items`), `amount` kosong untuk Wasilah/Ghayah, constraint `targets_bentuk_check`, unique index `targets_satu_diajukan_uk`, trigger `target_validasi_butir` (butir milik buku mapel itu dan aktif), `setujui_target_halaqah` (bulk per halaqah x bulan), alur "pengajuan baru menggantikan yang masih `diajukan`", parameter butir `DEFAULT NULL` (panggilan lama Al Qur'an tetap jalan), `riwayat_target` menyertakan butir & buku, `REVOKE EXECUTE` PUBLIC + anon untuk 15 fungsi target.
- DUMMY Wasilah 25 + Ghayah 11 bentuk baru (butir, tanpa amount); 36 baris bentuk lama sudah dihapus; skrip idempoten di `scripts/db/fixes/`.
- Migrasi `000032` tercatat di `supabase_migrations.schema_migrations`.

### Yang belum

- **T7c [2/3] (UI)**: form Wasilah/Ghayah masih mengirim `amount`, sehingga pengajuan dari UI **ditolak database** dengan pesan jelas; daftar/riwayat belum menampilkan butir tujuan akhir; belum ada tombol bulk "Setujui semua target halaqah ini" di layar; kewajiban target bulan depan saat input capaian, peringatan target di bawah capaian, dan tampilan Level 6 "Tuntas, belum ada pelajaran lanjutan" belum dibuat.
- **Laporan Wasilah/Ghayah**: `v_monthly_report.target_monthly` untuk target bentuk baru = NULL (tidak ada angka target). Tampilan butir/posisi target menyusul [2/3]. Ini bukan 0 dan bukan galat.
- **T7c [3/3]**: E2E penuh + smoke produksi setelah UI selesai.
- **T8 belum dimulai** (menunggu perintah): kurikulum, halaqah, santri, kalender, Hari Efektif & kunci bulan, pergantian mapel halaqah, notifikasi kekurangan target bulan depan.
- 3 sel matriks RLS masih SKIP (profil `wali`, target `diajukan` sebagai data tetap).
- Usulan proyek Supabase QA terpisah belum dibuat (T9/T10).

### Bug/error yang diketahui

1. **1 baris target Al Qur'an sisa uji T7 [2/2]** (Tahfidz, Santriwan fulan 26, Rabiul Akhir, amount 2, 26 Nov 09:27 UTC) **tidak dihapus** sesuai perintah; tercatat di `docs/DATA-NOTES.md` 0b. Perlu keputusan Mudir.
2. **`test_t6e_hapus_capaian.py` butuh baris capaian bulan 8.** Data dummy tidak punya capaian bulan 8; uji berhasil 35/35 setelah satu baris sementara disisipkan lalu dihapus. Masalah prasyarat uji, bukan regresi. Belum dijalankan ulang pada sesi 26-27 Nov (**BELUM DIVERIFIKASI**).
3. **3 sel matriks RLS SKIP:** profil `wali` belum ada dan tidak ada target `diajukan` di data dummy.
4. **`change_log`** append-only; sekarang **356** baris (bertambah karena uji yang menulis), baris lama utuh.
5. **Skrip `2026-11-26_t7b_target_dummy_wasilah_ghayah.sql` usang** (DUMMY bentuk lama). Berkop peringatan "JANGAN dijalankan lagi"; database otomatis menolak bentuk `amount`.
6. **Capaian Wasilah/Ghayah = 0 baris memang benar**: Excel tidak punya kolom capaian (lihat `docs/DATA-NOTES.md` bagian 12). Capaian asli diinput lewat aplikasi.
7. **Smoke produksi setelah pergantian skema belum dijalankan** (kode frontend tidak berubah): **BELUM DIVERIFIKASI**.
8. **Skrip hapus DUMMY lama pernah berbahaya** (`like 'DUMMY%'` ikut menghapus DUMMY baru). Sudah dipersempit dan diuji; jangan mengembalikan pola lama.

### Langkah berikutnya (berurutan)

1. **T7c [2/3] = UI `/target`** (menunggu perintah Mudir): form Wasilah/Ghayah memilih **butir tujuan akhir** lewat `DropdownCari` (tanpa angka), label "Mapel · Buku - nomor"; daftar/riwayat menampilkan butir; tombol **"Setujui semua target halaqah ini"** memakai `setujui_target_halaqah`; peringatan "target di bawah capaian" (boleh, dengan peringatan); tampilan Level 6 "Tuntas, belum ada pelajaran lanjutan"; kewajiban mengisi target bulan depan bersamaan input capaian.
2. **T7c [3/3]**: jalankan ulang seluruh uji (DB + E2E + smoke produksi), sidik jari SAMA, perbarui STATUS.
3. **Minta keputusan atas 1 baris target sisa uji** (butir 1 di atas).
4. **Setelah T7 disetujui**: mulai **T8** (kurikulum, halaqah, santri, kalender, Hari Efektif & kunci bulan, pergantian mapel halaqah). Jangan mulai T8/T9 lebih awal.
5. Saat T8: ganti DUMMY Wasilah/Ghayah dengan butir asli dari Mudir; isi Hari Efektif bulan 8-12 lewat layar (belum ada).

---

## 3. Keputusan yang sudah final (jangan diubah tanpa persetujuan Mudir)

### 3.1 Role dan hak akses

- Role lengkap: **Mudir**, **Admin**, **Masul Al Quran**, **Masul Wasilah**, **Masul Ghayah**, **Musyrif/ah**, **Mudarris/ah**, `wali` (belum aktif).
- Ketiga **Masul adalah penanggung jawab domain**: boleh input capaian, catatan, kehadiran di **semua halaqah domainnya**, bukan hanya yang tercatat di `halaqah_teachers`.
- Masul tetap **ditolak** di domain lain, bulan terkunci, bulan 0, dan **tidak boleh menghapus** capaian.
- Pengampu (Musyrif/ah, Mudarris/ah) hanya halaqah/mapel yang diampu.
- Hapus capaian dan baca `change_log`: **hanya Mudir/Admin**.
- Hari Efektif, kunci bulan, pengguna: **hanya Mudir/Admin**.
- Target: pengampu mengajukan; **Masul domainnya/Mudir/Admin** menyetujui; pengampu tidak menyetujui. Target yang dibuat langsung Masul/Mudir/Admin otomatis `disetujui`.

### 3.2 Target dinamis T7 (keputusan Mudir 26 November 2026)

- **Pengaju/penyetuju** seperti 3.1. Ubah target = **baris baru** dengan `effective_month_id`; target lama utuh. Bulan lewat/terkunci hanya Mudir/Admin dengan konfirmasi eksplisit. Riwayat wajib tersedia.
- **Bentuk:** Al Qur'an per **santri** per bidang, **harian**; massal per halaqah lalu sesuaikan per santri; individu didahulukan dari halaqah. Wasilah/Ghayah per **halaqah** per mata pelajaran, **bulanan langsung**, **tidak** dikali Hadir (bentuk berlaku sejak T7c: butir tujuan akhir).
- **Bulan berlaku:** dipilih saat mengajukan (default bulan berjalan); berlaku penuh sebulan, tidak dipecah, sampai diganti, lintas tahun ajaran. Bulan 0 tidak boleh menjadi bulan berlaku target.
- **Penolakan:** alasan **wajib**; target tidak dihapus. Pengaju boleh membatalkan target yang masih `diajukan`.
- **`target_monthly`:** NULL bila tidak ada target, Hari Efektif belum diatur, atau bulan 0; **0** hanya bila target harian ada dan Hadir benar-benar 0; bulanan = `amount` (sebelum T7c).
- **Tulis langsung ditutup:** policy INSERT/UPDATE/DELETE `targets` dihapus; privilege tulis dicabut; semua perubahan lewat RPC (SECURITY DEFINER + cek hak internal). Anon tanpa `EXECUTE`.
- **DUMMY:** 25 target Wasilah + 11 Ghayah adalah DUMMY (izin Mudir), wajib diganti data asli T8/T10.

### 3.2a Keputusan T7c: target Wasilah/Ghayah = TUJUAN AKHIR (Mudir, 26 November 2026)

Berlaku di atas 3.2.

- **Pemetaan mapel dari Excel BENAR sebagai kondisi saat ini** (`4-Ilmu Wasilah`, `5-Ilmu Ghayah`). **Tidak ada perubahan data/seed.** Level Dasar B memang sudah tuntas Baca dan Tulis.
- **Pergantian mapel halaqah** = wewenang **Masul domainnya** atas usulan pengampu, "berlaku mulai bulan X", bukan otomatis. Satu halaqah pindah mapel serentak. Layar di **T8**.
- **Level 6 = tuntas semua mapel WASILAH**: tampil "Tuntas, belum ada pelajaran lanjutan", tidak dihitung dalam notifikasi kekurangan.
- **Target Wasilah/Ghayah = TUJUAN AKHIR**: satu butir kurikulum = posisi akhir bulan depan, **bukan jumlah**. Jumlah/angka hanya Al Qur'an.
- **Target bulan depan WAJIB diisi** bersamaan input capaian bulan ini untuk tiap mapel aktif; pengampu tidak boleh mengosongkan. Pengecualian: halaqah sudah di butir terakhir mapel (tuntas), status "Tuntas, menunggu keputusan Masul".
- **Target di bawah capaian boleh** dengan **peringatan** (pengulangan).
- **Persetujuan:** ada **"Setujui semua target halaqah ini"** (bulk per halaqah x bulan). Bulan lewat/terkunci tetap hanya Mudir/Admin + konfirmasi.
- **Satu target menunggu** per (halaqah, mapel, bulan berlaku): pengajuan baru menggantikan yang masih `diajukan` (lama menjadi `dibatalkan`); yang sudah `disetujui` diganti lewat `ubah_target` (baris baru).
- **Penerapan database:** `targets.target_item_id` (FK `curriculum_items`); constraint `targets_bentuk_check` (Al Qur'an: `amount` + `harian`, per santri **atau** halaqah; Wasilah/Ghayah: halaqah + butir, `amount` kosong); unique index `targets_satu_diajukan_uk`; trigger `target_validasi_butir`; parameter butir `DEFAULT NULL`; `setujui_target_halaqah`; `REVOKE EXECUTE` PUBLIC + anon untuk seluruh keluarga fungsi target.
- **DUMMY:** bentuk lama (`amount = 1`) sudah dihapus; bentuk baru (butir) 25 + 11, ditandai `DUMMY` di `note`. Wajib diganti T8/T10.

### 3.3 Struktur tabel dan view yang tidak boleh diubah sembarangan

- `targets`: `id`, `domain`, `subject_id`, `student_id`, `halaqah_id`, `effective_month_id`, `amount`, `amount_period`, `target_item_id`, `status`, `proposed_by`, `approved_by`, `approved_at`, `note`, `created_at`, `alasan_tolak`, `rejected_by`, `rejected_at`, `entered_by`, `entered_at`, `updated_by`, `updated_at`.
- Constraint: `targets_bentuk_check` seperti 3.2a; tepat satu dari `student_id`/`halaqah_id` untuk Al Qur'an; Wasilah/Ghayah wajib `halaqah_id` + `target_item_id`; satu `diajukan` per (halaqah, mapel, bulan).
- View: `v_monthly_report`, `v_monthly_report_base`, `v_attendance`, `v_months_ordered`.
- Rumus di database: posisi (`item_position`), selisih, Hadir, `target_monthly`, `below_target`, `attendance_short`. React **tidak** menghitung ulang.
- Migrasi lama **tidak boleh diubah**; perubahan skema selalu file baru nomor berikutnya (`20261127000033_...` atau lebih baru sesuai tanggal).

### 3.4 Aturan data dan tampilan yang tetap

- **Bulan 0 (Data Awal)** bukan bulan input staf, bukan bulan efektif; `target_monthly` NULL.
- **Hari Efektif kecil SAH**: Syawwal 1447 = 4 hari, Rabiul Awwal 1447 = 3 hari. Jangan diubah tanpa konfirmasi Mudir.
- **Hadir** = Hari Efektif - (izin + sakit + alpha); kolom H Excel diabaikan.
- **Selisih boleh negatif**; jangan dipaksa 0. Bulan belum diinput **kosong**, bukan 0.
- Konfirmasi "pengulangan atau khatam" hanya untuk bidang yang benar-benar diubah; bidang lain cukup penanda (⚠).
- **Nama role lengkap** di kode/UI/dokumen: Masul Al Quran, Masul Wasilah, Masul Ghayah.
- Nama bidang: Tilawah, Tahfidz, Kitabah, Baca, Tulis, Sirah, **Hisab**, Adab dan Iman, Aqidah dan Fiqih.
- **Dropdown:** tahun dan bulan **dua dropdown terpisah** (`PemilihTahunBulan`); halaqah menampilkan pengampu (`PemilihHalaqah`); semua daftar memakai `DropdownCari` dengan `LAPISAN_DROPDOWN = 60`; label item memakai nama mata pelajaran di depan ("Tahfidz · An Naba' - 40").
- Pengampu hanya ditawari halaqah yang diampu (`hanyaHalaqahDiampu` di `src/lib/roles.ts`); Masul melihat semua halaqah domainnya.
- Jangan mengambil daftar panjang tanpa batas; pakai `ambilSemua` atau `range`.
- **Batas keluaran perintah** (AGENTS.md): jangan tampilkan berkas/tabel/JSON besar utuh; pakai `head`/`tail`/`wc -l`/ringkasan; simpan keluaran besar ke `/tmp` lalu ringkas (penyebab galat 413).
- Repo **PUBLIK** selama pengembangan; jangan commit rahasia/data santri asli. Sebelum data asli dimuat, repo wajib **PRIVAT**.

---

## 4. Status Supabase

- Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1` (Singapore).
- **`DATABASE_URL` = pooler Supabase** (host `*.pooler.supabase.com`, port `5432`, user berawalan `postgres`), bukan koneksi langsung. Kata sandi hanya di `.env.local`.
- **32 migrasi** tercatat di `supabase_migrations.schema_migrations`; terakhir **`20261126000032_targets_tujuan_akhir`**. Berikutnya wajib nomor `20261127000033_...` (atau tanggal berjalan) dan tidak boleh mengubah berkas lama.
  - Inti: `000001`-`000009`. Hardening/T5c/T6: `000010`-`000020`. Target T7: `000021`-`000031`. T7c: `000032`. Daftar lengkap: `docs/STATUS.md` bagian 3.
- **19 tabel**, semuanya RLS aktif; **42 kebijakan**; **50 fungsi** public; **4 view**.
- `targets` hanya punya policy SELECT (staf); tulis lewat RPC. **15 fungsi target** tanpa `EXECUTE` untuk `anon` maupun `PUBLIC`; RPC target hanya `authenticated` (dijaga `regression_execute.py`).
- `change_log` hanya SELECT untuk Mudir/Admin, append-only.
- **Seed dummy 1447 sudah dimuat** dan **destruktif (TRUNCATE)**. Jangan jalankan ulang tanpa perintah Mudir.
- Data sekarang (diperiksa 26-27 Nov 2026): santri **109**, capaian **2.036**, kehadiran **599 Al Qur'an / 756 Wasilah / 749 Ghayah** (total 2.104), catatan 0, target **364** (328 Al Qur'an + 25 DUMMY Wasilah + 11 DUMMY Ghayah bentuk tujuan akhir), `change_log` **356** baris, `month_domain_settings` 21, `profiles` 24.
- `month_domain_settings` hanya bulan 1-7; `is_locked` semua `false`; bulan 8-12 dan pengisian Hari Efektif adalah T8.
- **Matriks RLS:** 94 OK / 3 SKIP / 0 GAGAL. SKIP: profil `wali`, target `diajukan`.
- Situs produksi: `https://kusafa-app.vercel.app` (HTTP 200, terakhir diperiksa 26 Nov 2026 sebelum pergantian skema T7c).

---

## 5. Pertanyaan terbuka (menunggu Mudir)

1. **Repo masih PUBLIK.** Harus dijadikan privat sebelum data asli dimuat (`gh repo edit --visibility private --accept-visibility-change-consequences`). Wajib diingatkan lagi di T10.
2. **Data Awal 252 capaian**: dipertahankan atau dikosongkan saat data asli masuk? Keputusan T10.
3. **69 capaian dummy yang "mundur"** (lebih kecil dari bulan lalu): disepakati dibiarkan; konfirmasi ulang sebelum T9.
4. **Halaqah Level 6 (4 santri Wasilah)** belum punya mata pelajaran/pengampu. Tampilan "Tuntas, belum ada pelajaran lanjutan" menunggu T7c [2/3]/T8.
5. **Hari Efektif bulan 8-12** (semua domain) belum ada; layar pengisiannya T8. Notifikasi "data belum lengkap" karena itu tidak memeriksa bulan-bulan tersebut.
6. **3 sel RLS SKIP**: perlu profil `wali` dan contoh target `diajukan` untuk diuji (T9).
7. **DUMMY Wasilah/Ghayah** (25 + 11): kapan butir asli dimasukkan? Perlu daftar butir tujuan akhir dari Mudir (T8).
8. **Proyek Supabase QA terpisah**: usulan belum dibuat; sekarang uji dan produksi memakai SATU database.
9. **Retensi `change_log`**: belum ada pemangkasan; perlu keputusan bila log dianggap terlalu besar.
10. **1 baris target sisa uji** (STATUS 2q, DATA-NOTES 0b): dihapus atau dibiarkan sampai T10?
11. **Pemetaan mapel Excel benar** (keputusan 3.2a) dan tidak ada perubahan data. Konfirmasi bahwa layar pergantian mapel halaqah dan kewajiban target bulan depan cukup dikerjakan di T7c [2/3] / T8.
12. **Smoke produksi setelah T7c [1/3]** belum dijalankan. Perlu izin menjalankan smoke baca-saja (`42/42`) setelah deploy Vercel berikutnya.

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
python scripts/qa/test_t7c_target_tujuan.py      # 48/48 (T7c, baru)
python scripts/qa/test_targets_t7.py             # 34/34
python scripts/qa/regression_execute.py          # 8/8 (termasuk cek EXECUTE PUBLIC)
python scripts/qa/rls_matrix.py                  # 94/97 (3 SKIP)
python scripts/qa/test_t6a_tabel.py              # 14/14
python scripts/qa/test_t6b_input_wasilah.py      # 29/29
python scripts/qa/test_t6d2_masul_input.py       # 68/68
python scripts/qa/test_t6e_hapus_capaian.py      # 35/35 (perlu baris bulan 8 sementara)
python scripts/qa/test_seed_bersih.py            # 6/6
python scripts/qa/test_no_halaqah.py             # 9/9
python scripts/qa/test_students_without_halaqah.py    # 13/13
python scripts/qa/compare_alquran_full_excel.py  # 7/7 (penuh)
python scripts/qa/compare_rabiul_awwal_excel.py  # 7/7
python scripts/qa/test_data_awal_tahun_kedua.py  # 5/5
python scripts/qa/run_pre_t6_db_tests.py         # 16/16
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
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t7_target_ui.py
BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t7_target_tulis.py
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
- **Batasi keluaran perintah** (AGENTS.md) agar sesi tidak mati karena galat 413.
