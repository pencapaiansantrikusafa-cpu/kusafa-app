# HANDOVER - serah terima KUSAFA

**Terakhir diperbarui**: 26 November 2026, 10:29 WIB. HEAD sebelum dokumen ini disusun: `417a7ec` (`T7: uji log perubahan targets, hasil 34/34, dokumen disesuaikan`). Hash commit handover ini: lihat `git log -1`.

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
| **T7 [2/2]** | **UI `/target` (daftar, ajukan, setujui/tolak, ubah, riwayat)** | **BELUM** | rute masih `PlaceholderPage`; belum ada file UI target |
| T8 | Kelola kurikulum, halaqah, santri, kalender, **Hari Efektif & kunci bulan** | **BELUM** | belum ada |
| T9 | Pengujian & QA penuh | **SEBAGIAN** | ± 25 skrip `scripts/qa/`; belum ada proyek Supabase QA terpisah; 3 sel RLS SKIP |
| T10 | Deploy akhir, hapus dummy, repo privat | **BELUM** | belum ada |

---

## 2. Tahap yang sedang dikerjakan: T7 [2/2] UI Target

### Yang sudah jalan (jangan diulang)

- Skema `targets` + kolom `alasan_tolak`, `rejected_by/at`, `entered_by/at`, `updated_by/at`; enum `target_status` termasuk `dibatalkan`.
- RPC: `ajukan_target`, `setujui_target`, `tolak_target`, `ubah_target`, `ajukan_target_massal_alquran`, `riwayat_target`, `batalkan_target`, helper `target_*`.
- Semua tulis langsung `targets` ditutup: policy INSERT/UPDATE/DELETE dihapus, privilege tulis dicabut dari `anon`/`authenticated`; hanya SELECT untuk staf.
- Trigger audit `catat_jejak_targets` dan `catat_perubahan_targets`; log UPDATE/DELETE `targets` teruji.
- View `v_monthly_report`: kasus (f), bulan 0 NULL, individu didahulukan, tiebreak deterministik, Wasilah/Ghayah bulanan tidak dikali Hadir.
- Target DUMMY Wasilah 25 + Ghayah 11 (izin Mudir), diganti T8/T10.
- Uji `test_targets_t7.py` **34/34 LULUS**; banding rumus lama vs baru 2.036 baris Al Qur'an **0 beda**; RLS **94/97 OK, 3 SKIP, 0 GAGAL**.

### Yang belum

- Halaman `/target`: daftar target + filter tahun/bulan/domain/halaqah/status.
- Form ajukan/ubah target, pemilihan bulan berlaku, konfirmasi bulan lewat/terkunci.
- Layar persetujuan Masul/Mudir/Admin, penolakan wajib alasan, pembatalan oleh pengaju.
- Riwayat target.
- E2E UI T7.
- Smoke produksi setelah UI selesai.

### Bug/error yang diketahui

1. **`test_t6e_hapus_capaian.py` butuh baris capaian bulan 8.** Data dummy sekarang tidak punya capaian bulan 8, sehingga uji gagal di persiapan (`sid8, mapel8` None) bila dijalankan langsung. Uji berhasil 35/35 setelah satu baris sementara disisipkan lalu dihapus; sidik jari SAMA. Ini masalah prasyarat uji, bukan regresi T7.
2. **3 sel matriks RLS SKIP:** profil `wali` belum ada dan tidak ada target berstatus `diajukan` di data dummy. Bukan lolos, belum diuji.
3. **E2E browser T6a/T6b/T6d2/T6e dan smoke produksi belum dijalankan ulang** setelah perubahan database T7. UI belum berubah, tetapi statusnya **BELUM DIVERIFIKASI**.
4. **`change_log` bertambah** dari 96 menjadi 103 baris karena uji yang menulis (append-only). Baris lama utuh; sidik jari memeriksa log terpisah.
5. **Target DUMMY Wasilah/Ghayah** masih ada dan akan terbaca sebagai target nyata sampai diganti T8/T10.

### Langkah berikutnya (berurutan)

1. Bangun halaman `/target` daftar: filter dua dropdown Tahun/Bulan (`PemilihTahunBulan`), domain, halaqah (`PemilihHalaqah`), status; baca target lewat SELECT/`riwayat_target`; tampilkan status, pengaju/penyetuju, alasan tolak.
2. Bangun form ajukan/ubah memakai RPC `ajukan_target`/`ubah_target`; default bulan berjalan; tolak bulan 0 di UI dan database; tampilkan galat database apa adanya.
3. Tambah dialog konfirmasi untuk bulan lewat/terkunci; panggil ulang RPC dengan `p_konfirmasi = true` hanya untuk Mudir/Admin.
4. Tambah aksi persetujuan/penolakan/pembatalan sesuai role; alasan tolak wajib; target `diajukan`/`ditolak`/`dibatalkan` tidak dipakai laporan.
5. Tambah tampilan riwayat dari `riwayat_target`.
6. Uji E2E UI T7, `npm run typecheck`, `npm run build`, `db_fingerprint` sebelum/sesudah, `check_repo_safety.py`, perbarui `STATUS`/`HANDOVER`/`CHANGELOG`/`FILE-MAP`, commit + push.
7. **Baru setelah T7 UI selesai dan disetujui Mudir:** mulai T8. Jangan mulai T8/T9 lebih awal.

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
- **31 migrasi** tercatat di `supabase_migrations.schema_migrations`; terakhir **`20261126000031_targets_audit_semantics`**. Berikutnya wajib `20261126000032_...`.
- **19 tabel**, semuanya RLS aktif; **42 kebijakan**; **47 fungsi** public; **4 view**.
- `targets` hanya punya policy SELECT; tulis lewat RPC. `change_log` hanya SELECT untuk Mudir/Admin, append-only.
- **Seed dummy 1447 sudah dimuat** dan **destruktif** (TRUNCATE). Jangan jalankan ulang tanpa perintah Mudir.
- Data sekarang: santri **109**, capaian **2.036**, kehadiran **599 Al Qur'an / 756 Wasilah / 749 Ghayah** (total 2.104), catatan 0, target **363** (327 Al Qur'an + 25 DUMMY Wasilah + 11 DUMMY Ghayah), `change_log` **103** baris.
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
