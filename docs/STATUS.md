# STATUS - kondisi nyata proyek KUSAFA

**Sumber kebenaran status.** Diperbarui: **28 November 2026** (T7c **[3b] selesai**: tab `/target` Wasilah/Ghayah satu baris per halaqah + "Setujui semua target halaqah ini" + tolak beralasan + konfirmasi bulan terkunci/lewat (Mudir/Admin) + `FormTarget` DropdownCari; tabel Capaian menampilkan target + "Tercapai"/"Kurang N butir"; E2E 24/24 (per role, 360/1280 px), semua uji lama hijau, sidik jari SAMA; ambang beban halaman Input median **1,382 s**). Notifikasi + E2E penuh + tangkapan layar tambahan (**[3c]**) menyusul.
Setiap sub-tugas selesai wajib memperbarui berkas ini bersama `docs/HANDOVER.md`.

| | |
|---|---|
| Repo | `https://github.com/pencapaiansantrikusafa-cpu/kusafa-app` (PUBLIK) |
| Branch | `main` — branch `chore/react-router-fix` **sudah di-merge** 24 Nov 2026 (react-router 7.18.6) |
| Commit terakhir | lihat `git log -1` (dokumen ini ikut di-commit) |
| Keadaan Git saat pembaruan | bersih, sinkron `origin/main` setelah commit dokumentasi |
| Situs produksi | `https://kusafa-app.vercel.app` |
| Migrasi terakhir | `20261128000036_kewajiban_target_gabungan.sql` (tercatat; berikutnya `20261129000037_...` atau tanggal berjalan) |

### Hasil uji terakhir (T7c [3b], 28 November 2026)

| Rangkaian | Hasil |
|---|---|
| `test_t7c3_e2e.py` (E2E penuh, 24 uji: pengampu tanpa tombol Setujui/Tolak; Masul domain "Setujui semua" + tolak beralasan tampil ke pengaju; lintas domain; **bulan terkunci: Masul diblokir, Mudir konfirmasi eksplisit**; Level 6; tab & URL 360/1280 px; ambang median 5 putaran; pulihkan data) | **24/24 LULUS**; sidik jari **SAMA** (16.504 baris, 19 tabel) |
| `test_t7c_form_e2e.py` / `test_t7c_simpan_gabungan.py` / `test_t7c3_kewajiban_target.py` | **4/4 / 19/19 / 13/13 LULUS** |
| T6a / T6b (DB) / T6b (E2E) / T6d2 / T6e | **14 / 29 / 14 / 68 / 35 LULUS** |
| `test_targets_t7` / `test_t7_target_tulis` / `test_t7c_target_tujuan` / `regression_execute` / `rls_matrix` | **34/34 / 38/38 / 48/48 / 8/8 / 94/97 (3 SKIP) LULUS** |
| `npm run typecheck` / `npm run build` / `npm test` | hijau / berhasil / 14/14 |
| Ambang beban halaman Input (5 putaran) | median **1,382 s**, maksimum **2,394 s** (< 1,5 s median → tidak perlu optimasi) |
| Smoke produksi Vercel (baca saja) | **42/42 PASS** setelah deploy form T7c (27 Nov) — diulang setelah merge [3b] |

**Data sekarang:** capaian **2.036** (jumlah seed), kehadiran **599 / 756 / 749**, `monthly_notes` 0,
`change_log` bertambah (append-only; baris lama utuh), `targets` **363** (327 Al Qur'an setelah R5 dihapus + 25 DUMMY Wasilah + 11 DUMMY Ghayah; DUMMY berbentuk TUJUAN AKHIR tanpa amount). Migrasi **36**.

Semua angka di bawah diperiksa langsung pada 23-26 November 2026 (perintah dan hasilnya dicatat di bagian terkait).
Sesuatu yang belum dijalankan atau belum diuji ditulis **BELUM DIVERIFIKASI**, bukan SELESAI.

---

## 1. Status tiap tahap

Urutan tugas mengikuti `prompts/OPENCODE.md` dan **tidak boleh diubah**.

| Tahap | Nama | Status | Bukti | Catatan |
|---|---|---|---|---|
| **A-G** | Alat, proyek, Git, Supabase, seed, uji lokal, Vercel | **SELESAI** | `README.md`, `.env.example`, `supabase/config.toml`, `vercel.json` | Lihat CHANGELOG 22 Nov 2026 bagian A-G |
| **T0** | Orientasi dan sambungan | **SELESAI** | `data/source/` (5 file Excel, tidak di-commit), `docs/DATA-NOTES.md` | Excel sudah dipetakan; temuan terbuka di DATA-NOTES |
| **T1** | Database dan seed | **SELESAI** | 6 migrasi diterapkan (bagian 3), `scripts/seed/build_seed.py`, `scripts/db/run_sql.py` | Seed dummy sudah dimuat; destruktif, jangan diulang tanpa izin |
| **T2** | Login, kerangka, menu per role | **SELESAI** | `src/pages/LoginPage.tsx`, `src/components/AuthProvider.tsx`, `AppLayout.tsx`, `NavLinks.tsx`, `src/lib/roles.ts` | Login diuji ulang 23 Nov 2026 sebagai Mudir dan Musyrif/ah (lokal dan produksi) |
| **T3** | Tabel capaian halaqah Al Qur'an | **SELESAI** | `src/pages/CapaianPage.tsx`, `TabelCapaian.tsx`, `TabelAlQuran.tsx`, `src/lib/laporan.ts` | Wasilah/Ghayah dilengkapi di T6a |
| **T4** | Halaman satu santri | **SELESAI** | `src/pages/SantriPage.tsx`, `src/components/GrafikGaris.tsx`, `GrafikGabungan.tsx` | Tilawah/Tahfidz/Kitabah satu kotak; kehadiran kotak terpisah |
| **T5** | Input capaian Al Qur'an | **SELESAI** | `src/pages/InputPage.tsx`, `FormInputAlQuran.tsx`, `src/lib/putaran.ts`, `posisi.ts`, `KonfirmasiPutaran.tsx`, `KotakBelumLengkap.tsx`, `tests/putaran.test.mjs` | Termasuk T5b dan perbaikan 23 Nov. **Kekurangan yang disengaja:** layar Hari Efektif belum ada (T8). Lihat bagian 6 |
| **Pra-T6 [1-5/5]** | Audit, hardening, perbaikan data, notifikasi, audit & dokumentasi | **SELESAI untuk langkah [1]-[5]** | `docs/qa/rls_matrix_2026-11-24.json`, `scripts/qa/rls_matrix.py`, `tests/audit-rules.test.mjs` | Hasil di bagian 2a/2b/2c |
| **T5c** | Percepat halaman Input (pencarian item di server) | **SELESAI** (lihat 2e) | `src/pages/InputPage.tsx`, `DropdownCari.tsx`, migrasi `000011`, bagian 2e |
| **T5c-2** | Satu permintaan per tahap (boot + isi form) | **SELESAI** — 0,97 s median produksi (lihat 2f) | migrasi `000012`, `InputPage.tsx`, bagian 2f |
| **T5c-3** | Perbaikan bug label dropdown Input ("— belum diisi —") | **SELESAI** — uji E2E 9/9, data utuh (lihat 2g) | `DropdownCari.tsx`, `FormInputAlQuran.tsx`, `InputPage.tsx`, bagian 2g |
| **Pra-T6 [6]** | Jawaban Mudir + verifikasi & penutupan celah | **SELESAI** | bagian 2d: `scripts/qa/test_auth_signup_closed.py`, `regression_execute.py`, `smoke_e2e.py`, `test_data_awal_tahun_kedua.py`, migrasi `000010` | Urutan berikutnya: merge react-router (**sudah**), T5c percepat input, lalu T6 |
| **T6a** | Tabel capaian Wasilah & Ghayah | **SELESAI** (lihat 2h) | `src/pages/TabelWasilah.tsx`, `TabelCapaian.tsx`; uji `scripts/qa/test_t6a_tabel.py` 14/14 | — |
| **T6b** | Input Wasilah & Ghayah | **SELESAI** (lihat 2i) | migrasi `000013`-`000016`, `InputWasilahPage.tsx`, `FormInputWasilah.tsx`; uji DB 29/29, E2E 14/14 | — |
| **T6c** | "Bulan lalu" tampil sejak awal (laporan Mudir) | **SELESAI** | `FormInputAlQuran.tsx`; E2E 10/10 | — |
| **T6d** | Tab domain di halaman Capaian (seperti halaman Input) | **SELESAI** (lihat 2j) | `TabDomain.tsx`, `CapaianPage.tsx`, `InputPage.tsx`; E2E 28/28 lokal & produksi | Menu Capaian lama dihapus |
| **T6d2** | Ketiga Masul boleh input di semua halaqah domainnya + jejak pengisi | **SELESAI** (lihat 2k) | migrasi `000017`-`000018`; uji DB 68/68, E2E 14/14, RLS 67/75 | Menggantikan keputusan T6b soal cakupan Masul |
| **T6d3** | Pembersihan data + disiplin uji (sidik jari, seed bersih, banding Excel penuh) | **SELESAI** (lihat 2l) | `scripts/qa/db_fingerprint.py`, `pulihkan_data.py`, `test_seed_bersih.py`, `scripts/db/fixes/` | Aturan mengikat semua tahap |
| **T6e** | Hapus capaian (Mudir/Admin) + log perubahan | **SELESAI** (lihat 2m) | migrasi `000019`-`000020`, `hapus_capaian*`, `change_log`, `DialogHapusCapaian.tsx`; uji 35/35, 16/16, 15/15, 12/12 | Bulan terkunci & bulan sesudahnya wajib konfirmasi |
| **T7** | Target dinamis (ajukan/setujui) | **SELESAI** (lihat 2n, 2o, 2p); uji tulis 38/38 & E2E ulang hijau | migrasi `000021`-`000031`, RPC lengkap, `src/pages/Target*` + `FormTarget` dkk, `test_targets_t7.py` 34/34, `test_t7_target_ui.py` 36/36 (baca saja), `test_t7_target_tulis.py` 38/38 (menulis) | Uji UI yang menulis (item 4) & E2E lama (item 5) **LULUS**; sidik jari SAMA |
| **T7c [1/3]** | Target Wasilah/Ghayah = TUJUAN AKHIR (database, RPC, DUMMY, uji) | **SELESAI** (lihat 2q); BACKEND [2/3] **SELESAI**, UI [3/3] menyusul | migrasi `000032`, `test_t7c_target_tujuan.py` 48/48, `regression_execute.py` 8/8, sidik jari SAMA | Form UI Wasilah/Ghayah **belum** mengirim butir; pengajuan dari UI ditolak sampai [3/3] |
| **T7c [2/3]** | **BACKEND**: simpan gabungan capaian + target bulan depan, `halaqah_mapel_aktif`, tuntas & Level 6, laporan Wasilah/Ghayah = butir/posisi target | **SELESAI** (lihat 2r) | migrasi `000033`-`000035`, `test_t7c_simpan_gabungan.py` 18/18, regresi penuh hijau, sidik jari SAMA | Kewajiban target = mapel aktif yang **boleh ditulis pemanggil**; dikonfirmasi Mudir sebagai **keputusan ⓐ** (jawaban §5.13) |
| **T7c [3/3] form** | **UI butir 1-2**: form Input Wasilah/Ghayah = capaian + **target bulan depan** (butir kurikulum via `DropdownCari`), simpan gabungan `wasilah_simpan_gabungan`, kewajiban target keputusan ⓐ, peringatan + konfirmasi target di bawah capaian, "Tuntas, target tidak wajib", Level 6 | **SELESAI** (butir 1-2); **[3b] & [3c] belum** | migrasi `000036`, `FormInputWasilah.tsx`, `InputWasilahPage.tsx`, `DropdownCari.tsx`, `test_t7c_form_e2e.py` 4/4 (sidik jari SAMA), banner sukses dipindah ke induk agar tampil | Jalur simpan lama `wasilah_input_save` **ditutup** (melempar galat); produksi kembali konsisten setelah UI baru di-push. [3b]=tab `/target` massal; [3c]=notifikasi, E2E penuh, tangkapan layar |
| **T7c [3b]** | **UI tab `/target` + tabel Capaian**: satu baris per halaqah, kolom = mapel aktif bulan itu (label butir target), tombol **"Setujui semua target halaqah ini"** (`setujui_target_halaqah`, Masul domain/Mudir/Admin), tolak beralasan wajib, bulan terkunci/lewat hanya Mudir/Admin + dialog konfirmasi, `FormTarget` Ubah memakai `DropdownCari`; tabel Capaian menampilkan `target_label` + "Tercapai"/"Kurang N butir"/"–"; HP 360 px kartu per halaqah tanpa geser samping | **SELESAI** | `TabelTargetHalaqah.tsx` (baru), `TargetDomainPage.tsx`, `TabelWasilah.tsx`, `TabelCapaian.tsx`, `laporan.ts`, `target.ts`, `FormTarget.tsx`, `test_t7c3_e2e.py` 24/24 (sidik jari SAMA) | **[3c] belum** (notifikasi `target_belum_domain`, tangkapan layar tambahan). Ambang halaman Input: median 5 putaran **1,382 s** (maks 2,394 s) → tidak perlu optimasi |
| **T8** | Kurikulum, halaqah, santri, kalender, Hari Efektif & kunci bulan | **BELUM** | Rute `/kurikulum`, `/halaqah`, `/pengaturan` memakai `PlaceholderPage` | Hari Efektif saat ini hanya bisa diisi lewat SQL/dashboard |
| **T9** | Pengujian & QA | **SEBAGIAN** | Panggung otomatis luas: `tests/` 14 uji, `scripts/qa/` ± 20 rangkaian (DB, E2E, RLS, banding Excel, sidik jari) | Masih ada 8 sel RLS SKIP dan belum ada proyek QA terpisah |
| **T10** | Deploy akhir (hapus data dummy, repo privat) | **BELUM** | - | Repo masih publik, data dummy masih ada |

Catatan kejujuran status:
- T5 ditutup atas permintaan Mudir pada 22-23 November 2026. Yang **belum** di T5 bukan cacat tersembunyi, melainkan bagian yang memang milik T8 (layar Hari Efektif).
- T9 baru **SEBAGIAN**: uji otomatis sudah banyak dan hijau (termasuk sidik jari database dan banding Excel penuh), tetapi belum ada proyek Supabase QA terpisah dan 3 sel matriks RLS masih SKIP (menunggu profil wali + target `diajukan`).

---

## 2. Hasil pemeriksaan kode (23 November 2026)

| Pemeriksaan | Perintah | Hasil |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | **LULUS**, 0 galat (kode keluar 0) |
| Build | `npm run build` | **BERHASIL**. 102 modul. `dist/index.html` 0,42 kB; CSS 18,11 kB (gzip 4,34 kB); JS 475,43 kB (gzip 136,20 kB) |
| Uji unit | `npm run test` | **LULUS 14/14** (`tests/putaran.test.mjs` 6 + `tests/audit-rules.test.mjs` 8: lintas buku, target×Hadir, mundur, khatam, bulan terkunci) |
| Lint | `npm run lint` | **TIDAK ADA** perintahnya di `package.json`. Tidak ada ESLint di repo. Jadi tidak ada hasil lint |
| Audit dependensi | `npm audit --omit=dev` | **react-router BERSIH** (6→7.18.6 sudah di-merge 24 Nov 2026). Sisa **2**: `vite` (high) + `esbuild` (moderate) — hanya **dev server**, tidak ikut bundel produksi; perbaikan menuntut `vite@8` (breaking). Belum dijalankan. |
| Pemeriksaan keamanan repo | `python scripts/check_repo_safety.py` | **LOLOS** |

---

## 2a. Hasil pra-T6 langkah [3/5] (24 November 2026)

| Butir | Hasil | Bukti |
|---|---|---|
| Hari Efektif Rabiul Awwal 3 hari | **BENAR** (koreksi Mudir 24 Nov 2026: libur ~2 pekan lebih). Perubahan 3→19 **dibatalkan**, dipulihkan ke 3; Hadir **1–3** untuk 109 santri. Cocok 100% dengan Excel | `scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql`, `scripts/qa/compare_rabiul_awwal_excel.py` (7/7), `docs/DATA-NOTES.md` 3a |
| Aturan bulan 0 (Data Awal) | **SELESAI**. Bulan 0 bukan bulan efektif/target dan bukan bulan input staf; `month_is_open(bulan 0, domain) = false`; Syawwal 1448 (uji transaksi) membandingkan dengan Ramadhan 1447 | `docs/SPEC.md` bagian 4a, migrasi `20261121000008_month_zero_not_open.sql`, `docs/DATA-NOTES.md` bagian 6 |
| Santri tanpa halaqah (NIS 023/024) | **SELESAI**. Dibesarkan sebagai kasus uji resmi; di domain yang tidak diikuti santri tidak ditampilkan dan tidak ada galat; RLS menolak pengampu menulis domain itu | `scripts/qa/test_no_halaqah.py` — **9/9 PASS**, `docs/qa/no_halaqah_2026-11-24.json` |
| Uji DB pra-T6 | **14/14 PASS** | `scripts/qa/run_pre_t6_db_tests.py`, `docs/qa/db_tests_2026-11-24.json` |
| Uji unit frontend | **6/6 PASS** (`npm test`) | `tests/putaran.test.mjs` |

Catatan kejujuran: seluruh uji tulis di atas berjalan dalam transaksi lalu `ROLLBACK`; tidak ada baris data yang ditambah atau diubah.

## 2b. Hasil pra-T6 langkah [4/5] — notifikasi santri belum punya halaqah (24 November 2026)

| Butir | Hasil | Bukti |
|---|---|---|
| Halaman/komponen | Notifikasi "santri belum punya halaqah" ditambahkan sebagai perluasan kotak "data belum lengkap" (`KotakBelumLengkap.tsx`), bukan sistem baru | `src/components/KotakBelumLengkap.tsx` (memanggil `rpc("students_without_halaqah")`) |
| Implementasi database | Dua fungsi `security definer` `students_without_halaqah()` dan `students_without_halaqah_count()`, memeriksa `can_manage(domain)` di dalam fungsi; tanpa tabel baru; `revoke from public, anon` | migrasi `20261121000009_students_without_halaqah.sql` |
| Hitung data dummy | Al Qur'an 0; Wasilah 1 (`...024`); Ghayah 2 (`...023`, `...024`) — sesuai kebutuhan minimal, jauh di bawah 30% | diukur langsung dari DB; `docs/DATA-NOTES.md` bagian 8 |
| Uji otomatis peran | **13/13 PASS** (Mudir/Admin semua domain; Masul per domain; Musyrif/Mudarris 0 baris; diberi halaqah → hilang; anon ditolak; ROLLBACK mengembalikan) | `scripts/qa/test_students_without_halaqah.py`, `docs/qa/students_without_halaqah_2026-11-24.json` |
| Frontend | `tsc`, `build`, `npm test` hijau | bagian 2 |

Catatan: prompt menulis "Migrasi 000008", tetapi nomor itu sudah dipakai langkah [3/5] untuk `month_zero_not_open`, sehingga migrasi notifikasi ini memakai nomor berikutnya `20261121000009`.

---

## 2c. Audit pra-T6 langkah [5/5] — hasil dan keterbatasan (24 November 2026)

### Matriks RLS otomatis (item 1) — `scripts/qa/rls_matrix.py`, `docs/qa/rls_matrix_2026-11-24.json`
**38/46 OK • 8 SKIP (BELUM DIUJI) • 0 GAGAL.** Semua probe di dalam transaksi lalu `ROLLBACK`.
- SKIP = wali (3, role belum aktif, tidak ada profil wali) dan penyetujuan target (5, tidak ada target berstatus `diajukan` di data dummy) → **BELUM DIUJI**, bukan lolos.
- Yang terbukti: semua 7 staf membaca; Musyrif menulis hanya halaqah diampu; Admin/Mudir menulis di mana pun; bulan terkunci menolak Musyrif/Masul dan menerima Admin; Hari Efektif hanya Admin/Mudir; profil hanya Admin/Mudir; anon disembunyikan RLS untuk semua tabel yang diuji.
- Catatan pengukuran: UPDATE/DELETE yang disembunyikan RLS berhasil "tanpa galat" tapi 0 baris; matriks menilai 0 baris sebagai ditolak. Kalau tidak, hasil palsu "DITERIMA".

### Uji otomatis frontend (item 2) — `tests/audit-rules.test.mjs`
`npm test` kini **14/14** (6 lama + 8 baru). Yang ditambahkan (cermin rumus `docs/SPEC.md` §5, dijalankan tanpa DB): selisih lintas buku memakai `item_position`, target bulanan = target harian × Hadir (boleh pecahan), capaian mundur/pengulangan tetap selisih negatif, khatam = putaran + 1, bulan terkunci (bulan 0 tutup, bulan efektif ikut `is_locked`, hanya Admin/Mudir yang lolos).

### Kinerja muat item (item 3) — **SELESAI di T5c (Opsi A)**

**Masalah awal:** halaman Input Al Qur'an (`InputPage.tsx`) memuat **semua** `curriculum_items` aktif
domain itu (128 buku, **9.177 item**). Dropdown hanya menampilkan 60, tetapi 9.177 baris diunduh dulu
lewat **129 permintaan** (+783,9 KB) → halaman input butuh beberapa detik.

**Perbaikan (Opsi A — pencarian di server):** migrasi `20261124000011_curriculum_search.sql` menambah
RPC `curriculum_items_search(subject, q, limit 60)` dan `curriculum_items_by_ids(ids)`. Halaman hanya
meminta 60 hasil yang cocok saat kotak dibuka/diketik; item yang sudah tersimpan diambil by-id.
`DropdownCari` mendapat mode `diServer` (bertunda 200 ms, urutan skor sama dengan versi klien).
Notifikasi "data belum lengkap" kini memakai data halaqah & pengampu dari halaman induk (tidak unduh ulang).

Rincian hasil dan angka: bagian **2e**. Opsi B/C (lazy per buku, cache klien) tidak diperlukan lagi.

### react-router (item 4) — **SUDAH DI-MERGE ke `main` (24 Nov 2026)**
- Dulu terpasang 6.30.6; kini **`react-router`/`react-router-dom` 7.18.6**.
- **GHSA-wrjc-x8rr-h8h6 (CVE-2026-53669)** *open redirect* dan **GHSA-337j-9hxr-rhxg (CVE-2026-53666)** *deserializeErrors*: keduanya tertambal di **7.18.0**; naik 6→7 adalah satu-satunya jalan (tidak ada patch mayor 6).
- **Alasan merge:** Mudir mengizinkan merge **hanya bila smoke E2E semua role lulus** di branch itu. Terbukti: `tsc` + `build` + `npm test 14/14` hijau, dan smoke E2E **29/29 PASS** di branch `test/react-router-7-smoke` (= `main` + react-router 7), lalu di-merge ke `main`.
- `npm audit`: react-router **tidak lagi** dilaporkan.

### Rencana ESLint (item 5) — **ditunda ke T9** (keputusan Mudir 24 Nov 2026)
Tidak ada `lint` di `package.json`. Rencana (tanpa mengubah kode sekarang): pasang `eslint` + `@typescript-eslint/*` + `eslint-plugin-react-hooks`; skrip `lint`; mulai dari aturan error ringan (hooks, unused, `any`), lalu tingkatkan. Dikerjakan di **T9**.

### Secret-scan & gitleaks (item 6)
`gitleaks` **tidak terpasang** (tidak bisa dipasang tanpa mengubah sistem). Karena itu pola ditambahkan ke `scripts/check_repo_safety.py`: `VERCEL_OIDC_TOKEN` (penugasan/issuer OIDC Vercel), `sb_secret_`, `service_role` mentah, dan `postgres://` (sudah ada, dipertegas). Diverifikasi: string tiruan terdeteksi; penyebutan nama tanpa nilai **tidak** salah-positif; `check_repo_safety.py` **LULUS** (rc 0).

### Kebugaran artefak QA (item 7)
`grep` pada `docs/qa/` dan `scripts/qa/` hanya menemukan penyebutan pola (metadata audit), **tanpa nilai rahasia nyata**. Semua berkas QA berisi data dummy NIS/nama.

---

## 2d. Hasil pra-T6 langkah [6] — jawaban Mudir + penutupan celah (24 November 2026)

Semua butir dikerjakan; T6 **belum** dimulai (urutan: [6] → merge react-router → T5c percepat input → T6).

| Butir | Hasil | Bukti |
|---|---|---|
| 1. Signup tertutup, login tetap jalan | **LULUS 9/9**. **Celah ditemukan & ditutup:** sebelumnya signup hanya tertutup karena seluruh provider email dimatikan (`external.email=false`) — itu **ikut mematikan login** (semua role 422 "Email logins are disabled"); dengan domain email valid signup justru **berhasil**. Kini `disable_signup=true`, provider email **aktif**: signup ditolak `422 signup_disabled`, login 7 role berhasil | `scripts/qa/test_auth_signup_closed.py`, `docs/qa/auth_signup_closed_2026-11-24.json`; diubah lewat Management API Supabase |
| 2. `students_without_halaqah()/_count()` | **LULUS 6/7 (1 SKIP: tidak ada profil wali)**. Jawaban: fungsi mengembalikan **SEMUA domain tanpa cek role** hanya bila `current_app_role() IS NULL` **dan** `session_user` = `postgres`/`service_role`/`supabase_admin` — yaitu koneksi admin/skrip lokal & PostgREST service_role, **bukan** pengguna aplikasi. authenticated tanpa profil (diuji lewat REST dengan token sungguhan) → **0 baris**; musyrif/mudarris → **0 baris**; anon ditolak 42501. Karena jalur itu **dipakai skrip QA lokal**, fungsi **tidak dihapus** | `scripts/qa/test_students_without_halaqah_p6.py`, `docs/qa/students_without_halaqah_p6_2026-11-24.json` |
| 3. `attendance_guard_override()` | **SELESAI**. EXECUTE dicabut dari `authenticated`, `public`, `anon`; trigger **tetap jalan** (fungsi `SECURITY DEFINER` → dijalankan sebagai pemilik). Uji B2 (musyrif ditolak, admin diterima) tetap lulus | migrasi `20261124000010_attendance_guard_revoke.sql` |
| 4. Uji regresi `scripts/qa/` | **LULUS 7/7**. (A) loop `pg_proc`: **20 fungsi** public, **0** punya EXECUTE untuk anon. (B) musyrif memanggil `create_academic_year`/`reorder_items`/`resequence_subject` **tidak mengubah data** (RLS INVOKER: 0 baris berubah; `create_academic_year` ditolak 42501) | `scripts/qa/regression_execute.py`, `docs/qa/regression_execute_2026-11-24.json` |
| 5. Uji DB pra-T6 16 → 14 | **SELESAI 16/16 PASS**. Penjelasan: tidak pernah ada "16" di repo; yang ada `run_pre_t6_db_tests.py` 14 uji (11-23) → 15 (11-24, +`B4_item_position_function_exists`), tanpa ada yang hilang. Uji **`E_hari_efektif_rabiul_awwal_3`** mengharapkan **3** (nilai benar) + uji Hari Efektif mustahil (di luar 1..31). Total **16/16** | `docs/qa/db_tests_2026-11-24.json` |
| 6. Smoke E2E per role | **LULUS 29/29 di `main`**, **29/29 di react-router 7**, **28/28 di produksi** (tanpa tulis data). Per role: login, halaman utama, kotak notifikasi, halaman Capaian, konsol bersih. Mudir juga **menyimpan satu capaian lewat UI** lalu menghapus **hanya** baris uji itu (data kembali bersih) | `scripts/qa/smoke_e2e.py`, `docs/qa/smoke_e2e_2026-11-24.json`, `..._prod.json` |
| 7. DATA-NOTES rentang Excel | **SELESAI**. `BZ5:B113` → **`BZ5:BZ113`** (dua tempat; lihat `DATA-NOTES.md` 3a) | `docs/DATA-NOTES.md` bagian 3a |
| Jawaban: Bulan 0 | **SESUAI, tanpa ubah kode**. Tahun kedua tanpa bulan 0; Syawwal 1448 memakai Ramadhan 1447; `create_academic_year(...,false)` tidak membuat/meminta Data Awal. Ditulis di SPEC 4a-1 | `scripts/qa/test_data_awal_tahun_kedua.py` — **5/5 PASS** |

Temuan data: **Hari Efektif Syawwal 1447 = 4 hari dan Rabiul Awwal = 3 hari adalah SAH** (bulan pembuka & libur ~2 pekan lebih), bukan kesalahan — lihat `docs/SPEC.md` 4a-2. Tidak ada lagi butir "janggal" untuk Hari Efektif.

## 2e. Hasil T5c — percepat halaman Input Al Qur'an (24 November 2026)

**Cara ukur:** `scripts/qa/measure_input_perf.py` (Playwright + Chrome). Halaman Input dibuka dari
jendela bersih, waktu dihitung dari navigasi sampai tombol **Simpan** muncul (form siap dipakai).
Baseline memakai build dari commit `6a97eed` di worktree terpisah (port berbeda), sesudah memakai build
commit ini. Semua di komputer & jaringan yang sama.

| Ukuran | Baseline (sebelum) | Sesudah (T5c) |
|---|---|---|
| Halaman siap (desktop) | **3,0–4,0 s** (3 putaran) | **1,44–1,95 s** (3 putaran) |
| Halaman siap (HP 360 px) | tidak diukur sebelum | **1,44 s** (3 putaran) |
| Permintaan `curriculum_items` | **128** permintaan | **2** (kosong, `by_ids` tanpa item) |
| Byte data item | **783,9 KB** | **≈0 KB** |
| Payload REST halaman ini | ~1,34–1,50 MB | **≈0,55 MB** (atau ~1,0 MB bila cache kosong) |
| Geser horizontal HP 360 px | - | **tidak ada** (`scrollWidth` 360 = lebar layar) |
| **Produksi (Vercel)** | **3,0–3,9 s**, 129 permintaan item (bundel lama) | **1,51–2,04 s**, **2** permintaan item; HP 360: 1,51–2,63 s; smoke produksi 28/28 |

- **Target "di bawah 1 detik" BELUM tercapai.** Sisa waktu ±1,4 s berasal dari penundaan jaringan ke
  database (`ap-southeast-1`): round-trip REST dari mesin ini **0,24–1,3 s** (median ≈0,4 s), dan halaman
  masih menjalankan **±20 permintaan berurutan** ke database. Query sendiri cepat (0,1–0,2 s). Hal ini
  dicatat sebagai keterbatasan jaringan, bukan rumus/daftar item.
- **Perhitungan tidak berubah:** dibandingkan 114 baris `v_monthly_report` (3 halaqah × 2 bulan) —
  identik sebelum/sesudah untuk label item, putaran, posisi, selisih, Hadir, Hari Efektif, target bulanan,
  `below_target`, dan `attendance_short`.
- **Uji:** `npm test` 14/14; `tsc` & `build` lulus; DB 16/16; regresi 7/7; banding Excel 7/7; data awal 5/5;
  no-halaqah 9/9; tanpa-halaqah 13/13 (+6/7, 1 SKIP wali); matriks RLS 38/46 OK, 8 SKIP, 0 GAGAL;
  smoke E2E **29/29** (termasuk Mudir menyimpan satu capaian lewat UI lalu dikembalikan bersih).
- **Keamanan:** fungsi baru `SECURITY INVOKER` + cek `is_staff()`; EXECUTE hanya untuk authenticated &
  service_role; anon ditolak 42501. `pg_trgm` dipasang di skema **`extensions`** — saat sempat di `public`,
  uji regresi menangkap **31 fungsi ekstensi terbuka ke anon**; kini **0** fungsi public terbuka ke anon.

## 2f. Hasil T5c-2 — satu permintaan per tahap halaman Input (25 November 2026)

**Yang diubah:** `InputPage` tidak lagi menjalankan ±20 permintaan berurutan ke database.
Sekarang ada **2 RPC**:
- `input_alquran_boot()` → halaqah, bulan, pengampu (pembukaan halaman);
- `input_alquran_data(halaqah, bulan, bulan_lalu)` → bidang, Hari Efektif/kunci, santri, capaian,
  item terpilih, buku, kehadiran, catatan, pos/putaran/teks bulan lalu, pos/selisih bulan ini,
  dan bulan sesudahnya — **satu baris JSON**.

Migrasi `20261124000012_input_alquran_data.sql`; `SECURITY INVOKER` + cek `is_staff()` (pola koneksi
admin tanpa JWT seperti 000009/000011); EXECUTE hanya authenticated & service_role; **anon ditolak**.
Posisi, selisih, putaran, target bulanan, dan Hadir **tetap dibaca dari view**, bukan dihitung ulang.

| Ukuran | T5c (sebelum T5c-2) | T5c-2 (lokal, build) | T5c-2 (produksi) |
|---|---|---|---|
| Halaman siap, desktop | 1,44–1,95 s | **0,93–0,99 s** (5 putaran; 1 putaran 1,45 s) | **0,97–1,19 s** (5 putaran; 1 putaran 1,79 s) |
| Halaman siap, HP 360 px | 1,44 s | 0,93–1,44 s | **0,95–1,05 s** |
| Permintaan data (REST) | ±20 | **3** (boot, isi form, notifikasi) | **3** |
| Permintaan `curriculum_items` | 2 | **0** | **0** |
| Payload halaman | ~0,55 MB | ~0,54 MB | ~0,54 MB |

- **Target < 1 detik tercapai pada kondisi jaringan normal** (median ±0,97 s lokal & produksi).
  Sebagian pengukuran tertinggal di atas 1 s karena penundaan jaringan ke database (`ap-southeast-1`)
  yang tidak stabil — dicatat apa adanya, bukan diabaikan.
- **Perhitungan identik:** 114 baris `v_monthly_report` (3 halaqah × 2 bulan) sama persis sebelum/sesudah,
  dan setiap baris paket RPC dibandingkan langsung dengan view (`pos`, `putaran`, `item_label`,
  `prev_item_label`, `selisih`): **0 beda**.
- **Uji:** `npm test` 14/14; `tsc` & `build` lulus; DB 16/16; regresi 7/7; banding Excel 7/7; data awal 5/5;
  no-halaqah 9/9; tanpa-halaqah 13/13 (+6/7, 1 SKIP wali); matriks RLS 38/46 OK, 8 SKIP, 0 GAGAL;
  smoke E2E **29/29** lokal (Mudir menyimpan satu capaian lewat UI lalu dikembalikan) & **28/28** produksi.

## 2g. Perbaikan bug label dropdown Input (T5c-3, 25 November 2026)

**Laporan Mudir:** di halaman Input (produksi, role Mudir), setelah memilih item, tombol dropdown
tetap menulis "— belum diisi —".

**Reproduksi** (`scripts/qa/repro_input_dropdown.py`, build lokal 4173, role Mudir, bulan Rabiul Awwal):

| Langkah | Sebelum perbaikan | Setelah perbaikan |
|---|---|---|
| a. Buka santri yang sudah punya nilai | label tampil (benar) | label tampil |
| b. Pilih item dari daftar | **"— belum diisi —"** | label pilihan tampil |
| c. Pilih lewat pencarian (mis. `quraisy` / `351`) | **"— belum diisi —"** | label pilihan tampil |
| d. Centang/batalkan "khatam, mulai putaran baru" | **centang tidak muncul** (item baru tak dikenali sebagai buku siklik) | centang muncul, bisa dicentang & dibatalkan |
| e. Muat ulang halaman | label tersimpan tampil | label tersimpan tampil |

Sapuan dropdown per role: Mudir, Admin, dan Musyrif/ah memiliki form Al Qur'an dan **0 placeholder
yang salah**. Masul Al Quran, Masul Wasilah, Masul Ghayah, dan Mudarris/ah tidak memiliki halaqah
Al Qur'an pada data dummy (penugasan mereka di Wasilah/Ghayah), sehingga halaman Input tidak
menampilkan form item — bukan kegagalan dropdown; form Wasilah/Ghayah memang milik T6.

**Akar masalah:** sejak T5c pencarian item dilakukan di server, daftar `opsi` dropdown hanya memuat
item yang **sudah tersimpan** (`item_terpilih` dari RPC). `DropdownCari` mencari label terpilih hanya
di daftar itu; item yang baru dipilih dari hasil pencarian tidak pernah masuk daftar, sehingga
`terpilih` tidak ditemukan dan tombol memakai teks kosong. Akibat turunan: `petaItem` di
`FormInputAlQuran` juga tidak mengenal item baru, sehingga keterangan "Bulan lalu" dan centang
"khatam" (yang membaca `siklik`) tidak tampil.

**Perbaikan (tanpa mengubah rumus):**
- `DropdownCari`: objek pilihan yang diklik (nilai + label + `siklik`) disimpan di state komponen;
  `onChange` meneruskan objek itu. Label benar walau item tidak ada di hasil pencarian terakhir.
- `FormInputAlQuran`: item baru disimpan beserta label & `siklik`, sehingga keterangan bulan lalu,
  centang khatam, dan nilai yang ditulis ke database memakai data yang benar.
- `InputPage`: hasil pencarian menyertakan `siklik`; `itemTambahan` (duplikat `items` sejak T5c-2) dibuang.
- Posisi, selisih, putaran, target, dan Hadir **tetap dibaca dari view database**.

**Dampak data:** sebelum dan sesudah perbaikan, `progress_entries` tetap **2.036 baris** dan
**0 baris** `entered_at` hari ini (baris seed bertanggal 22 Nov 2026, `entered_by` kosong). Uji E2E
menyimpan satu capaian dummy untuk membuktikan tulisan database, lalu **mengembalikan baris itu
persis** (item, putaran, entered_by, entered_at) — sudah diverifikasi; tidak ada baris yang dihapus.

**Celah uji lama:** `smoke_e2e.py` hanya memeriksa halaman termuat, simpan berhasil, dan konsol bersih;
ia tidak pernah memeriksa **teks tombol dropdown** setelah memilih. Uji baru
`scripts/qa/test_input_dropdown_e2e.py` menutup celah itu: pilih dari daftar, pilih lewat pencarian,
centang/batalkan khatam, simpan → periksa isi database → muat ulang → label harus tetap tampil.
Hasil: **9/9 LULUS** lokal dan **9/9 LULUS** di produksi; data uji pulih (2.036 baris).

**Uji lain:** `npm test` 14/14, `tsc` & `build` lulus, DB 16/16, regresi 7/7, banding Excel 7/7,
data awal 5/5, no-halaqah 9/9, tanpa-halaqah 13/13 (+6/7, 1 SKIP), signup tertutup 9/9,
matriks RLS 38/46 OK (8 SKIP, 0 GAGAL), smoke E2E **29/29** lokal & **28/28** produksi.

## 2h. T6a - Tabel capaian Ilmu Wasilah & Ilmu Ghayah (25 November 2026)

**Aba-aba Mudir:** T6 boleh dimulai, dipecah T6a (tabel) lalu T6b (input).

**Yang diubah**
- `src/pages/TabelWasilah.tsx` (baru): per mata pelajaran **Capaian bulan lalu / bulan ini / selisih / target**,
  lalu tabel anggota **Nama Santri, Hadir/HE, Izin, Sakit, Alpha, Catatan** (bentuk `docs/SPEC.md` 5.6).
- `TabelCapaian.tsx`: tulisan "dikerjakan pada T6" dihapus; Wasilah/Ghayah memakai `TabelWasilah`.
  Anggota kini hanya dari `halaqah_members` dengan `left_on is null`; mata pelajaran dari `halaqah_subjects`.
- `PemilihTahunBulan.tsx`: notifikasi "data belum lengkap" kini **per domain** (sebelumnya selalu menulis
  "capaian Al Qur'an" walau halaman Wasilah/Ghayah). Yang dihitung hanya santri yang punya halaqah di domain itu
  dan hanya mata pelajaran yang ditetapkan halaqahnya.

**Tidak ada perhitungan di React.** Posisi, selisih, Hadir, Hari Efektif, dan target dibaca dari
`v_monthly_report` / `v_attendance`. Bulan kosong = "belum diisi", bukan 0.

**Data DUMMY (izin khusus Mudir)**
- `scripts/db/fixes/2026-11-25_he_wasilah_ghayah_dummy.sql`: Hari Efektif **Wasilah & Ghayah = Al Qur'an**
  untuk bulan 1-7, plus kehadiran **0/0/0** untuk tiap anggota (dipilih Mudir, karena tanpa baris kehadiran
  Hadir tetap kosong). Skrip aman dijalankan ulang dan **tidak menimpa** nilai yang sudah ada.
- Alasan: Excel Wasilah/Ghayah **tidak punya** kolom HE/Hadir/izin/sakit/alpha.
- Hasil: 14 baris `month_domain_settings` Wasilah/Ghayah (HE 3-21), 756 baris kehadiran Wasilah,
  749 baris kehadiran Ghayah, total absen 0. **Wajib diganti data asli di T8/T10** (DATA-NOTES butir 3).
- **Tidak** dibuat `progress_entries` (capaian), target, atau catatan: itu tugas T6b/T7 dan tidak boleh dikarang.

**Uji `scripts/qa/test_t6a_tabel.py`: 14/14 LULUS** — baris view selalu punya entri asli; posisi = `item_position`;
Hadir = HE − (izin+sakit+alpha); santri tanpa halaqah tidak muncul (023/024); tidak ada posisi 0 palsu;
0 baris capaian Wasilah/Ghayah (belum dikarang); halaqah tanpa mata pelajaran dikenali (Level 6);
HE DUMMY = Al Qur'an bulan 1-7 dan tidak melebar ke bulan 8-12; kehadiran DUMMY 0/0/0 tanpa override;
tiap anggota punya kehadiran 7 bulan; anon 0 baris (RLS); authenticated boleh membaca `halaqah_subjects`.

**Tampilan diuji (Playwright, role Mudir):** halaman Capaian Ilmu Wasilah dan Ilmu Ghayah termuat tanpa galat
konsol, tulisan "dikerjakan pada T6" hilang, tabel anggota tampil (6 santri Level 1A, 13 santri Kelompok 1),
notifikasi menulis "capaian Ilmu Wasilah"/"capaian Ilmu Ghayah" (bukan Al Qur'an).

---

## 2i. T6b/T6c - Input Ilmu Wasilah & Ilmu Ghayah (25 November 2026)

**Aturan yang dilaksanakan:** input **sekali per halaqah x mata pelajaran**, disalin database ke
**semua anggota aktif** dalam **satu transaksi**; bulan 0 dan bulan terkunci ditolak oleh fungsi.

**Migrasi**
| Nomor | Isi |
|---|---|
| `20261125000013_wasilah_input.sql` | `wasilah_input_boot`, `wasilah_input_form`, `wasilah_input_save`, `wasilah_can_write`. SECURITY INVOKER, cek staf di dalam fungsi, anon tanpa EXECUTE. |
| `20261125000014_wasilah_input_hadir.sql` | Form memuat `hadir` & `effective_days` dari `v_attendance`; sebelumnya form menghitungnya di React (dilarang). |
| `20261125000015_masul_domain_write.sql` | **Keputusan Mudir:** Masul Wasilah/Masul Ghayah = penanggung jawab domain; policy tulis tambahan. |
| `20261125000016_masul_domain_scope_fix.sql` | **Koreksi temuan uji:** policy 000015 ikut memberi Masul Al Quran akses semua halaqah Al Qur'an. Dibatasi ke `wasilah`/`ghayah`; Al Qur'an tidak berubah. |

**Halaman**
- `/input` tetap Al Qur'an; `/input/alquran`, `/input/wasilah`, `/input/ghayah`.
  Domain yang ditawarkan mengikuti role (`domainInputUntuk`): Mudir/Admin tiga domain, Masul satu
  domain, Musyrif/ah Al Qur'an, Mudarris/ah Wasilah+Ghayah. Database tetap penjaga terakhir.
- **Satu permintaan per tahap** + **pencarian item di server**: halaman siap **0,86–0,87 s lokal**
  dan **median 0,95 s produksi** (5 putaran per domain). Target <1,5 s tercapai. Satu putaran
  produksi sempat 1,55 s karena jaringan ke database `ap-southeast-1`.
- Satu dropdown item **per mata pelajaran** (bukan per santri), memakai `DropdownCari` yang
  menyimpan objek pilihan + labelnya — pelajaran bug T5c-3. Nilai tersimpan tampil saat dibuka.
- Hanya mata pelajaran yang **ditetapkan halaqah** (`halaqah_subjects`) yang tampil. Level 6
  Wasilah (belum punya mapel) menampilkan pesan, bukan form kosong — penetapannya T8.
- Anggota yang tidak ikut halaqah domain itu tidak ditampilkan (023/024 tetap kasus uji).

**T6c (laporan Mudir saat T6):** keterangan "Bulan lalu" dulu baru muncul setelah item dipilih.
Kini tampil **sejak awal** (termasuk saat dropdown masih "— belum diisi —"), datanya dari view
(teks + putaran), bukan hitungan React. Bukti: bulan Jumadal Akhir — 3 dropdown kosong,
3 baris "Bulan lalu" berisi ("Karima - 1 (putaran 2)" dan seterusnya).

**Uji**
- `test_t6b_input_wasilah.py` **29/29**: salinan ke semua anggota; santri luar halaqah tidak
  tersentuh; anggota keluar tidak diubah; simpan ulang tidak menggandakan; dua mapel sekaligus;
  bulan 0 ditolak; item/mapel salah ditolak; RLS per role (14-22e); Masul tetap ditolak pada bulan
  terkunci dan pada Al Qur'an; anon ditolak; rollback bersih.
- `test_t6b_e2e.py` **14/14 lokal** dan **13/14 produksi** (satu putaran 1,55 s > batas 1,5 s pada
  pengukuran pertama; pengukuran 5 putaran terpisah memberi median 0,95 s): pilih → label tampil;
  simpan → database untuk semua anggota dengan item sama; muat ulang → label tetap tampil;
  konsol bersih; data uji dipulihkan.
- `test_t6a_tabel.py` **14/14**; E2E dropdown Al Qur'an **10/10** (termasuk langkah a2 baru).
- Matriks RLS **44/52 OK, 8 SKIP, 0 GAGAL** (6 sel baru untuk Masul per domain).
- Smoke per role **43/43** lokal dan **42/42** produksi (naik dari 29: tiap role kini juga memeriksa
  `/input/wasilah` dan `/input/ghayah`, termasuk bahwa role yang tidak berhak **dialihkan**).
- `npm test` 14/14, `tsc` & `build` lulus, DB 16/16, regresi 7/7, Excel 7/7, data awal 5/5,
  no-halaqah 9/9, tanpa-halaqah 13/13 (+6/7, 1 SKIP), signup tertutup 9/9.

---

## 2j. T6d - Tab domain di halaman Capaian (25 November 2026)

**Permintaan Mudir:** sub-menu Capaian dibuat seperti halaman Input — tab Al Qur'an / Ilmu Wasilah /
Ilmu Ghayah di bagian atas, di HP maupun desktop.

- **Komponen bersama `src/components/TabDomain.tsx`** (baru). Tab lama di `InputPage` (fungsi
  `PemilihDomain`) **dihapus** dan digantikan komponen ini; kedua halaman kini memakai satu kode.
- Tab memakai `<Link>` ke `${dasar}/${domain}`, jadi **tab aktif tercermin di URL**:
  `/capaian/wasilah`, `/input/wasilah`. Muat ulang dan tombol kembali bekerja tanpa keadaan di memori.
- **Halaman Capaian**: tab di atas judul-bagian, isi di `role="tabpanel"`. Rute tidak dikenal atau
  tidak boleh dilihat dialihkan ke domain pertama yang boleh (`domainCapaianUntuk`).
- **Visibilitas:** semua staf (Mudir, Admin, Masul Al Quran, Masul Wasilah, Masul Ghayah, Musyrif/ah,
  Mudarris/ah) melihat ketiga tab — sama persis dengan hak lihat yang SUDAH ada (`progress_read`,
  `halaqahs_read`, `students_read` memakai `is_staff()`; menu Capaian sejak awal menampilkan tiga
  submenu untuk semua role). Fungsi `domainCapaianUntuk` hanya **memusatkan** aturan itu.
  **RLS, view, dan perhitungan tidak berubah.**
- **Menu lama dihapus:** entri `children` pada menu Capaian di `roles.ts` dihapus, sehingga menu
  samping dan bilah bawah tidak lagi membuka submenu Capaian (digantikan tab).
- **Responsif:** HP 360 px — tiga tab dibagi rata (grid 3 kolom), tinggi sentuh **44 px**, tanpa
  geseran horizontal; desktop — tombol sebaris dengan lebar sesuai isi.

**Uji `scripts/qa/test_t6d_tab_capaian.py`: 28/28 LULUS lokal dan 28/28 produksi**
- desktop 1280 px: 3 tab terlihat, tab aktif awal Al Qur'an, klik tab mengganti URL dan isi tabel,
  muat ulang tetap di tab Wasilah, tombol kembali mengembalikan tab Al Qur'an, tab Ghayah bekerja;
- HP 360 px: lebar dokumen = lebar layar (tidak bergeser samping) di ketiga domain, 3 tab muat,
  tinggi tab >= 44 px, klik tab bekerja;
- 7 role: masing-masing melihat 3 tab (sesuai hak lihat yang ada);
- menu samping Capaian bukan lagi submenu; halaman Input memakai tab yang sama; konsol bersih.

**Uji lain:** `npm test` 14/14; `tsc` & `build` lulus; DB 16/16; regresi 7/7; Excel 7/7; data awal 5/5;
no-halaqah 9/9; tanpa-halaqah 13/13 (+6/7, 1 SKIP); signup 9/9; matriks RLS 44 OK/8 SKIP/0 GAGAL;
T6a 14/14; T6b DB 29/29; E2E T6b 14/14; E2E input 10/10; smoke per role **43/43 lokal & 42/42 produksi**.

Tangkapan layar: `docs/qa/t6d/` (`hp360_capaian_*.png`, `desktop_0*_capaian_*.png`, `desktop_04_input_tab.png`).

---

## 2k. T6d2 - Masul boleh input di semua halaqah domainnya + jejak pengisi (25 November 2026)

**Keputusan Mudir (25 November 2026, menggantikan keputusan 3d):** **seragamkan** hak input ketiga Masul.
Masul Al Quran, Masul Wasilah, dan Masul Ghayah boleh **input capaian + catatan + kehadiran di SEMUA
halaqah domainnya** (walau tidak tercatat di `halaqah_teachers`). **Tetap ditolak:** domain lain, bulan
terkunci, bulan 0, dan menghapus. Pengampu (Musyrif/ah, Mudarris/ah) **tetap hanya halaqahnya sendiri**.
Rumus Hadir dan view **tidak berubah**. Jejak siapa mengisi/mengubah wajib tercatat.

- **Migrasi `20261125000017_masul_input_domain.sql`** (sudah dijalankan di produksi):
  - menulis ulang `progress_insert` / `progress_update`, `attendance_insert` / `attendance_update`,
    `notes_insert` / `notes_update` menjadi **satu aturan seragam untuk ketiga domain**:
    `is_full_access()` ATAU `month_is_open(...)` dan (`is_masul_of(domain)` ATAU pengampu halaqah itu);
  - **hak hapus tidak berubah** (`progress_delete`, `attendance_delete`, `notes_delete` tetap hanya
    `is_full_access()` = Mudir/Admin);
  - menghapus policy lama `progress_insert_masul_domain` / `progress_update_masul_domain` (khusus
    Wasilah/Ghayah) karena sudah tercakup aturan baru;
  - menambah kolom **`updated_by`** + **`updated_at`** pada `progress_entries`, `attendance`, dan
    `monthly_notes`, serta trigger **`catat_jejak`** (satu fungsi untuk tiga tabel).
- **Migrasi `20261125000018_catat_jejak_tanpa_jwt.sql`** (sudah dijalankan di produksi): koreksi
  trigger. Versi pertama memakai `is distinct from` sehingga pada koneksi **tanpa JWT** (seed/skrip
  `service_role`) `null is distinct from null` = FALSE dan jejak baris seed ikut tertimpa.
  Sekarang: bila `auth.uid()` NULL trigger **tidak menyentuh** baris yang sudah ada.
- **Arti jejak:** `entered_by`/`entered_at` = **pengisi terakhir**; `updated_by`/`updated_at` =
  **pengubah terakhir** (pengisi lama dipindahkan ke sini saat orang lain menimpa). Menyunting isian
  sendiri tidak menghapus jejak.
- **Kode**:
  - `src/lib/roles.ts` — `hanyaHalaqahDiampu()` kini **hanya** `musyrif`/`mudarris`; fungsi baru
    `bolehInputDomain(role, domain)` (Mudir/Admin semua domain, tiap Masul domainnya).
  - `InputAlQuranPage.tsx` & `InputWasilahPage.tsx` — daftar halaqah memakai `bolehInputDomain`,
    jadi Masul melihat **semua** halaqah domainnya dan pengampu tetap satu halaqah.
  - `TabelCapaian.tsx` — `.limit(2000)` (terpotong diam-diam di 1.000 baris) diganti `ambilSemua`
    + saringan domain, untuk menentukan bulan awal yang benar.
- **Uji baru**:
  - `scripts/qa/test_t6d2_masul_input.py` **68/68 LULUS** — matriks role x domain x tabel
    (capaian, kehadiran, catatan) untuk INSERT & UPDATE, tolak domain lain/bulan terkunci/bulan 0,
    tolak hapus untuk Masul & pengampu, terima hapus untuk Mudir, anon ditolak, dan uji jejak
    (`entered_by` terisi, `updated_by` mencatat pengubah). Semua penulisan di-ROLLBACK; jumlah baris
    **per domain** dibandingkan sebelum/sesudah.
  - `scripts/qa/test_t6d2_e2e_masul.py` **14/14 LULUS** — lewat UI: ketiga Masul ditawari semua
    halaqah domainnya, domain lain dialihkan, tombol **Simpan** benar-benar menulis capaian
    (`entered_by` tercatat), Musyrif tetap hanya halaqahnya, konsol bersih, data dipulihkan
    (jumlah & jejak sama).
  - `scripts/qa/rls_matrix.py` diperluas: **67 OK / 8 SKIP / 0 GAGAL** (sebelumnya 44 OK).
- **Pembersihan data (temuan saat menguji)**: dua uji sempat meninggalkan jejak di database produksi
  dan sudah dibersihkan/diperbaiki:
  - **1 baris capaian Wasilah** (`Santriwan fulan 51`, Shafar) tertinggal dari uji hapus matriks RLS
    yang me-COMMIT baris sasaran → dihapus; matriks kini menyiapkan baris **di dalam transaksi** lalu
    ROLLBACK.
  - **1 baris kehadiran Ghayah** (bulan Dzul Hijjah) hilang karena uji T6d2 menghapus baris kehadiran
    lama → dipulihkan (0/0/0); uji tidak lagi menghapus data lama dan kini memeriksa hitungan
    **per domain**.
- **Keadaan data setelah T6d2**: `progress_entries` 2.038 (2.035 seed + 3 baris uji Mudir bulan
  Jumadal Ula), capaian Wasilah/Ghayah **0**; `attendance` alquran 613 (606 + 7 baris uji Mudir
  bulan Jumadal Ula), Wasilah 756, Ghayah 749; `monthly_notes` 0.
- **Uji lain tetap hijau:** `npm test` 14/14; `tsc` & `build` lulus; DB 16/16; regresi 7/7; Excel 7/7;
  data awal 5/5; no-halaqah 9/9; tanpa-halaqah 13/13 (+6/7, 1 SKIP); signup 9/9; T6a 14/14; T6b DB 29/29.
- **Produksi (25 November 2026)**: bundel `index-1de03EWI.js` **sama persis** dengan build lokal dari
  commit `fb95727`; smoke produksi **43/43 PASS**; pemeriksaan baca-saja sebagai ketiga Masul **7/7**
  (semua halaqah domainnya ditawarkan, domain lain dialihkan, Musyrif tetap satu halaqah).
- **Jejak uji smoke dipulihkan**: langkah "Mudir simpan" pada smoke kini ikut mengembalikan
  `entered_by`/`entered_at` baris lama (sebelumnya jejak 18 baris Rabiul Akhir berubah menjadi
  `entered_by = Mudir` tanpa perubahan nilai). Jejak produksi sudah dipulihkan: hanya 3 baris
  `entered_by = Admin` (uji Mudir) yang tersisa.
- Tangkapan layar: `docs/qa/t6d2/` (`masul_alquran_simpan.png`, `masul_wasilah_simpan.png`,
  `masul_ghayah_simpan.png`).

## 2l. T6d3 - Pembersihan data dan disiplin uji (25 November 2026)

**Perintah kerja Mudir:** hapus lagi 7 baris kehadiran Ramadhan + cari penyebabnya; pulihkan
nilai Shafar sesuai seed/Excel + laporkan penyebab perbedaannya; rekonsiliasi 2.039 vs 2.038;
ubah uji banding Excel menjadi penuh; tegakkan disiplin sidik jari database.

### 1. 7 baris kehadiran Ramadhan - DIHAPUS lagi, penyebab ditemukan
- **Penyebab:** penghapusan 23 Nov 2026 **tidak pernah dibuat sebagai skrip** (hanya dicatat di
  DATA-NOTES/CHANGELOG). Saat penyiapan sesi 24 Nov (sebelum commit pertama pukul 10:04), seed
  dijalankan ulang: `02_school_data.sql` membuka dengan `truncate public.attendance ...` lalu mengisi
  semua baris yang ada di Excel, termasuk 7 baris Ramadhan. Tidak ada uji yang menulis ke tabel
  `attendance` (diperiksa satu per satu di `scripts/qa`), jadi bukan uji.
- **Perbaikan permanen:** `scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql` (aman dijalankan
  ulang; hanya menghapus baris Ramadhan Al Qur'an **tanpa capaian**) + uji penjaga
  `scripts/qa/test_seed_bersih.py` (gagal bila baris itu muncul lagi). Dijalankan: 7 baris terhapus,
  kehadiran Al Qur'an **613 → 606**.

### 2. Nilai Shafar (izin/sakit/alpha) - DIPULIHKAN sesuai seed/Excel
- **Yang terbukti:** Excel dan seed sama (36 baris > 0; total S 24, I 43, A 6). Di database ke-36
  baris itu 0/0/0. **Tidak ada skrip/uji di repo yang menulis ke `attendance`** (semua hanya membaca).
  Tidak ada jejak perubahan: `updated_by`/`updated_at` baru ada sejak migrasi T6d2, dan koneksi tanpa
  JWT tidak mengisi `entered_by`. Semua baris Shafar bertanggal seed (22 Nov 04:10, `entered_by` NULL):
  baris tidak dibuat ulang, **nilainya** yang diubah. **Kesimpulan: perubahan manual di luar repo
  sebelum T6d2; sebab pastinya tidak dapat dibuktikan dari data yang tersedia.**
- **Tindakan:** `scripts/db/fixes/2026-11-25_pulihkan_shafar.sql` mengubah **hanya 37 baris** yang
  berbeda (36 bernilai > 0 + 1 bernilai 0); seed penuh tidak dijalankan. Diverifikasi oleh uji banding
  Excel penuh (semua 599 pasangan santri-bulan lolos) dan uji `--bulan 5` (93 santri, 0 berbeda).

### 3. Rekonsiliasi 2.039 vs 2.038 - SELISIH 1 BARIS DITEMUKAN
- Selisihnya **tepat satu baris**: `1443.dummy-nis.024`, **Kitabah Dzul Qa'dah (bulan 2)**, item
  **"Menyalin - 25"** (id seed `6352df74-...`). Baris itu ada di seed **dan** di Excel, tetapi tidak ada
  di DB. Seluruh baris seed lain (termasuk tetangga 024 di bulan 0/3/4/5/6/7) utuh.
- **Bukti waktu:** laporan `docs/qa/e2e_input_dropdown.json` (25 Nov 11:08) mencatat 2.039 baris;
  pada akhir T6d2 menjadi 2.038. Kolom jejak belum ada saat itu, jadi tidak ada catatan siapa/kapan.
  Kemungkinan paling masuk akal: SQL ad-hoc saat penyelidikan T6d2 menghapus baris berdasarkan kunci
  alami di luar transaksi. **Tidak dikarang:** baris dipulihkan dengan nilai seed asli
  (`scripts/db/fixes/2026-11-25_pulihkan_capaian_024.sql`), bukan dibuat baru.
- **Tambahan temuan T6d3:** versi lama `test_input_dropdown_e2e.py` menghapus semua baris dengan
  `entered_at >= mulai`; saat dijalankan hari ini ia menghapus **20 baris** seed (19 baris Rabiul Awwal
  + 1 baru) → 2.019. Skrip diuji ulang setelah diperbaiki, dan 20 baris dipulihkan dengan
  `scripts/db/fixes/2026-11-25_pulihkan_data_seed.py`. Capaian kembali **2.039**.
- **Rekap:** 2.036 seed + 3 baris Jumadal Ula (percobaan Mudir, tidak disentuh) = **2.039**.

### 4. Uji banding Excel menjadi PENUH
`scripts/qa/compare_alquran_full_excel.py` **7/7 PASS** — 109 santri, **599 pasangan santri-bulan**
(Data Awal + Syawwal..Rabiul Akhir), **1.673 sel capaian**:
1. kelengkapan (tidak ada santri-bulan Excel yang terlewat);
2. Hari Efektif sama;
3. Hadir DB = HE - (izin+sakit+alpha);
4. izin/sakit/alpha sama dengan Excel (semua bulan);
5. label capaian sama + posisi DB = `item_position` (+ putaran; `value_offset` buku dihormati);
6. ringkasan per bulan (jumlah santri/sel capaian).
Dua hal DICATAT, bukan galat (di luar T6d3): kolom H Excel tidak selalu = HE-(S+I+A) (aplikasi memang
mengabaikan kolom H, 10 sel berbeda); angka manual Excel sering beda dari posisi kumulatif (1.482 sel).

### 5. Disiplin uji & sidik jari database
- **`scripts/qa/db_fingerprint.py`** (baru): jumlah baris + checksum md5 seluruh isi **18 tabel**.
  Dipakai `--simpan` sebelum dan `--banding` sesudah setiap rangkaian uji; hasil wajib **SAMA**.
- **`scripts/qa/pulihkan_data.py`** (baru): menyimpan salinan penuh tiga tabel uji lalu memulihkan
  **persis** (hapus baris baru, kembalikan nilai + `entered_by`/`entered_at`/`updated_by`/`updated_at`).
- Uji yang menulis sudah memakainya: `test_t6d2_e2e_masul.py`, `test_t6b_e2e.py`,
  `test_input_dropdown_e2e.py`, `smoke_e2e.py`. **Smoke produksi kini HANYA MEMBACA**
  (`DATA_UJI` default 0 bila BASE_URL Vercel).
- Bukti: sidik jari identik (16.478 baris, 18 tabel) sebelum/sesudah E2E T6d2, T6b, dropdown,
  smoke lokal, dan smoke produksi.
- `AGENTS.md` bagian "Disiplin data dan uji" ditambahkan.

### 6. Hasil uji T6d3
`npm test` 14/14; `tsc` & `build` lulus; DB 16/16; regresi 7/7; Excel penuh **7/7**; Excel Rabiul
Awwal 7/7; data awal 5/5; no-halaqah 9/9; tanpa-halaqah 13/13 (+6/7, 1 SKIP); signup 9/9; T6a 14/14;
T6b DB 29/29; T6b E2E 14/14; T6d2 DB 68/68; T6d2 E2E 14/14; dropdown E2E 10/10; matriks RLS 67/75
(8 SKIP); seed bersih 5/5; smoke lokal 43/43; smoke produksi 42/42 (baca saja).

### 7. Usulan (BELUM dibuat, menunggu persetujuan Mudir): Supabase khusus QA sebelum T9/T10
**Masalah:** database lokal = produksi, jadi satu uji yang salah bisa merusak data dummy (atau nanti
data asli). **Usulan:** buat **satu proyek Supabase kedua** (`kusafa-qa`) khusus uji.
- Langkah: (1) buat proyek baru region Singapore; (2) terapkan semua migrasi + seed dummy; (3) buat
  akun dummy (`npm run seed:users`) di proyek itu; (4) `.env.qa` berisi URL/anon key QA — **jangan
  pernah** di-commit; (5) skrip uji menerima `QA_DATABASE_URL`; (6) Vercel preview (opsional) memakai
  QA env; (7) jalankan seluruh rangkaian uji di QA + sidik jari di sana; produksi hanya smoke baca.
- Dampak: biaya satu proyek Supabase (free tier cukup untuk 109 santri dummy); data produksi tidak
  pernah ditulis uji; perlu disiplin `.env.qa` (rahasia tidak boleh masuk repo); perlu satu kali
  penyiapan ±1 jam.
- **Belum dibuat** — perintah kerja T6d3 melarang membuatnya sekarang.

## 2m. T6e - Hapus capaian + log perubahan (25 November 2026)

**Perintah Mudir:** Admin/Mudir dapat menghapus capaian yang salah input (Al Qur'an, Wasilah, Ghayah);
Masul & pengampu tetap hanya input/menimpa. Satu mekanisme log perubahan untuk UPDATE+DELETE pada tiga
tabel. Bulan terkunci boleh dengan konfirmasi eksplisit. Cakupan satu capaian + massal. Lewat RPC.

### Langkah 0 - E2E pengampu yang belum pernah diuji lewat UI
`scripts/qa/test_t6e_langkah0_pengampu.py` **12/12 LULUS**, sidik jari **SAMA**:
- **Mudarris/ah** (Ilmu Wasilah): hanya halaqah yang diampu, Simpan menulis ke semua anggota,
  label tampil lagi setelah muat ulang.
- **Musyrif/ah** (Al Qur'an): hanya halaqah yang diampu, Simpan menulis capaian, konsol bersih.
- **Halaqah Level 6 (Ilmu Wasilah):** 4 anggota, 0 mata pelajaran, 0 pengampu → halaman terbuka tanpa
  galat, **tidak menawarkan mata pelajaran**, dan **tidak menulis apa pun** (capaian Level 6 = 0).

### Migrasi (2 berkas)
- **`20261125000019_hapus_capaian_log.sql`**: tabel `change_log` + trigger `catat_perubahan` (UPDATE/DELETE
  pada `progress_entries`, `attendance`, `monthly_notes`) + 4 RPC: `hapus_capaian_info`,
  `hapus_capaian`, `hapus_capaian_massal_info`, `hapus_capaian_massal`. Cek `is_full_access()` di dalam
  fungsi; `EXECUTE` hanya authenticated (anon dicabut). Log: RLS SELECT hanya `is_full_access()`,
  INSERT/UPDATE/DELETE/TRUNCATE dicabut dari authenticated, anon tanpa akses.
- **`20261125000020_log_abaikan_update_kosong.sql`**: UPDATE dengan `to_jsonb(new) = to_jsonb(old)`
  **tidak** dicatat. Tanpa ini, `pulihkan_data` menghasilkan 2.111 baris log palsu dalam satu uji.

### Aturan hapus (yang dipilih dan dijelaskan)
- **Bulan terkunci:** boleh untuk Mudir/Admin, **wajib** `p_setuju_terkunci = true`; tanpa itu ditolak.
- **Bulan sesudahnya terisi:** pembanding bulan sesudahnya akan berubah → **ditolak** dengan pesan
  "hapus mulai dari bulan terakhir, atau beri konfirmasi eksplisit"; dengan `p_setuju_lanjutan = true`
  diizinkan. Bila capaian itu **khatam/putaran baru** (`putaran > putaran bulan lalu`), pratinjau
  melaporkan `mulai_putaran_baru` dan dialog memperingatkan.
- **Bulan 0 (Data Awal):** ditolak (bukan bulan input staf).
- **Massal** (halaqah × mapel × bulan): pratinjau mengembalikan **jumlah santri + daftar nilai**;
  hapus massal juga menghormati konfirmasi terkunci/lanjutan.

### UI
- `src/components/DialogHapusCapaian.tsx` (baru): dialog menyebut **santri/nama (atau jumlah santri),
  bidang, bulan, nilai + posisi**, peringatan putaran, dan pilihan konfirmasi (terkunci / bulan
  sesudahnya). Tombol Hapus **nonaktif** sampai konfirmasi dicentang.
- `TabelCapaian.tsx`: tombol **"Hapus capaian <bidang>"** per santri (tabel Al Qur'an desktop + dialog
  detail HP + tabel Wasilah/Ghayah) dan baris tombol **"Hapus semua <mapel>"** (massal). Hanya tampil
  untuk Mudir/Admin (`profile.role`), dan RPC tetap penjaga akhir.
- Setelah hapus, tabel dimuat ulang → sel kembali **“belum diisi”** (bukan 0), dan pesan hasil tampil.

### DATA UJI MUDIR (jawaban T6d3) - dijalankan sebagai uji penerimaan
- **(a) 3 baris capaian Jumadal Ula** dihapus **lewat fitur baru** (UI, bukan SQL):
  `scripts/qa/test_t6e_uji_penerimaan.py` **15/15 LULUS**. Isi log (tabel `change_log`):
  tiga baris `progress_entries`/`delete`/`aktor_role = mudir`/`sumber = aplikasi`, dengan `nilai_lama`
  memuat `item_id` dan `putaran` (Kitabah `IBQ PAUD - 1` putaran 1, Tahfidz `Al Fatihah - 1` putaran 1,
  Tilawah `Karima - 1` putaran 2). Sidik jari berubah **tepat −3 capaian** dan **+3 baris log**;
  tidak ada tabel lain yang berubah. Capaian sekarang **2.036** (kembali ke jumlah seed).
- **(b) 7 baris kehadiran Jumadal Ula** isinya: `izin/sakit/alpha = 0/0/0`, override NULL,
  `entered_by = Admin`, `25 Nov 2026 02:14` (detik yang sama dengan capaian percobaan), halaqah
  HLQ-PA-1. Bulan 8 belum punya Hari Efektif. **Jelas percobaan** → dihapus lewat
  `scripts/db/fixes/2026-11-25_hapus_kehadiran_jumadal_ula.sql` (7 baris, tercatat di log sebagai
  `skrip:postgres`). Kehadiran Al Qur'an **606 → 599** (sama dengan jumlah baris seed). Total
  kehadiran 2.104.

### Uji
- `test_t6e_hapus_capaian.py` **35/35** (DB, transaksi + ROLLBACK): role (3 Masul + pengampu + anon
  ditolak; Mudir/Admin diterima), pratinjau, hapus satu, massal, bulan terkunci (tolak/terima),
  bulan sesudahnya terisi (tolak/terima), bulan 0, putaran, log DELETE & UPDATE di tiga tabel,
  UPDATE tanpa perubahan tidak dicatat, log tanpa JWT `skrip:postgres`, log tidak bisa
  diubah/dihapus/ditulis dari aplikasi, Masul tidak bisa membacanya, anon ditolak.
- `test_t6e_e2e_hapus.py` **16/16** (UI): Masul tidak melihat tombol; dialog menyebut
  santri/bulan/nilai; hapus satu & massal; bulan terkunci minta centang (tombol nonaktif sebelum
  dicentang); data dipulihkan persis; log bertambah.
- `test_t6e_uji_penerimaan.py` **15/15** (permanen, tidak dipulihkan — perintah Mudir).
- `test_t6e_langkah0_pengampu.py` **12/12**.
- Uji lama hijau: `npm test` 14/14; `tsc` & `build`; DB 16/16; regresi 7/7; Excel penuh 7/7; Excel
  Rabiul Awwal 7/7; data awal 5/5; no-halaqah 9/9; tanpa-halaqah 13/13 (+6/7, 1 SKIP); signup 9/9;
  T6a 14/14; T6b 29/29 & E2E 14/14; T6d2 68/68 & E2E 14/14; dropdown 10/10; matriks RLS 67/75;
  seed bersih **6/6**.
- **Sidik jari:** SAMA (16.468 baris, 19 tabel) untuk semua rangkaian uji T6e, kecuali uji penerimaan
  yang memang menghapus 3 capaian + 7 kehadiran (perubahan dilaporkan tepat).

### Catatan penting
- **Log bersifat append-only.** Uji yang menulis MEMANG menambah baris log; `db_fingerprint.py` kini
  memeriksa log **terpisah** (boleh tumbuh, baris lama wajib utuh — dibuktikan dengan checksum
  potongan lama, dan alat ini terbukti menangkap baris log lama yang diubah). `pulihkan_data.py`
  sengaja tidak menyentuh log.
- **Seed ulang (TRUNCATE)** tidak memicu trigger baris → tidak tercatat di log; penjaga tetap
  `test_seed_bersih.py` + sidik jari.
- Semua penulisan uji T6e memakai `pulihkan_data.py` yang kini **memasukkan kembali baris yang dihapus**
  (bukan hanya memperbaiki baris yang masih ada).

### Catatan data yang perlu keputusan Mudir (bukan bagian T6d2)

1. **7 baris `attendance` Ramadhan (Al Qur'an) tanpa capaian** masih ada di database, padahal
   `docs/DATA-NOTES.md` butir 3 mencatat penghapusannya (606 → 599) sudah disetujui 23 November 2026.
   Baris ini bertanggal seed (22 November) dan tidak tersentuh T6d2. Perlu keputusan: dihapus lagi
   atau dipertahankan.
2. **Nilai izin/sakit/alpha Shafar (bulan 5) di database berbeda dari berkas seed** (36 baris di seed
   bernilai > 0, di database 0). Tidak ada uji yang memeriksa bulan itu dan tidak ada jejak perubahan
   (kolom jejak baru ada sejak T6d2). Perlu keputusan: ikuti seed atau pertahankan database.

---

## 2n. T7 [1b/2] - fondasi target dinamis (26 November 2026)

**Cakupan sesi ini:** database + RPC + uji + dokumen. **UI `/target` belum dikerjakan** (T7 [2/2]).

### effective_month_id 327 target lama: SEBELUM vs SESUDAH (tidak berubah)

| Waktu | Nilai | Jumlah |
|---|---|---|
| SEBELUM T7 (seed `20261121000004` + `supabase/seed/02_school_data.sql`) | `52c4961d-6f33-5abc-bcc8-89b3e94c8cf7` = Data Awal 1447, `month_no=0` | **327** |
| SESUDAH migrasi `000021`-`000031` (query langsung 26 Nov 2026) | `52c4961d-...` = Data Awal 1447, `month_no=0` | **327** |

**Tidak ada perubahan.** Berkas migrasi final `000021` **tidak** memuat backfill `effective_month_id`;
kolom itu sudah ada sejak `20261121000004` dan tidak pernah diubah oleh T7. Karena data lama tidak
berubah, tidak ada persetujuan Mudir yang diperlukan untuk butir ini. Bulan 0 tetap sah sebagai titik
mulai target ("berlaku dari Data Awal") dan tidak menghasilkan `target_monthly` di bulan 0.

### Yang ditambahkan
- **Kolom `targets`:** `alasan_tolak`, `rejected_by`, `rejected_at`, `entered_by`, `entered_at`,
  `updated_by`, `updated_at`; enum `target_status` + `dibatalkan`.
- **RPC:** `ajukan_target`, `setujui_target`, `tolak_target` (alasan wajib), `ubah_target` (baris baru),
  `ajukan_target_massal_alquran` (per santri), `riwayat_target`, `batalkan_target` (hanya pengaju,
  hanya status `diajukan`), plus helper `target_*`.
- **Kunci tulis:** policy INSERT/UPDATE/DELETE `targets` **dihapus**; privilege tulis dicabut dari
  `anon`/`authenticated`; `SELECT` tetap untuk staf. Seluruh perubahan hanya lewat RPC.
- **Audit:** trigger `catat_jejak_targets` (BEFORE INSERT/UPDATE) mengisi `entered_*`/`updated_*`;
  trigger `catat_perubahan_targets` (AFTER UPDATE/DELETE) menulis `change_log` nilai lama + baru.
- **View:** `target_monthly` = NULL bila tidak ada target / Hari Efektif belum diatur / bulan 0;
  = 0 hanya bila target harian ada dan Hadir = 0; target bulanan (Wasilah/Ghayah) = `amount` tanpa
  dikali Hadir. Individu didahulukan dari halaqah; tiebreak `created_at desc, id desc`.

### Bukti uji
- `scripts/qa/test_targets_t7.py`: **34/34 LULUS**, semua tulis di transaksi `ROLLBACK`, sidik jari SAMA.
  Mencakup: pengampu ajukan/tidak setujui; Masul domain sendiri vs lintas domain; Mudir/Admin; anon;
  target `diajukan`/`ditolak` tidak dipakai laporan; tolak wajib alasan; `ubah_target` baris baru;
  massal Al Qur'an; riwayat; bulan 0; bulan lewat/terkunci hanya Mudir/Admin + konfirmasi; kasus (f)
  kosong vs 0 vs bulan 0 NULL; individu vs halaqah; tiebreak; Wasilah/Ghayah bulanan tidak dikali
  Hadir; tulis langsung ditolak; anon tanpa EXECUTE untuk 13 fungsi target.
- `scripts/qa/verify_t7_report_unchanged.sql`: rumus laporan **sebelum** vs **sesudah** pada seluruh
  **2.036 baris Al Qur'an** → `beda_lama_baru = 0`, `beda_baru_lama = 0` untuk pos, selisih, hadir,
  effective_days, target_amount, target_period, target_monthly, below_target, attendance_short.
- `rls_matrix.py`: **94/97 OK, 3 SKIP, 0 GAGAL**. Semua tulis langsung `targets` ditolak untuk semua
  role (termasuk Mudir/Admin); SELECT staf diterima, anon ditolak. 3 SKIP tetap wali/target `diajukan`.
- Uji lama dijalankan ulang: `run_pre_t6_db_tests.py` 16/16, `regression_execute.py` 7/7,
  `compare_alquran_full_excel.py` 7/7, `compare_rabiul_awwal_excel.py` 7/7, `test_t6e_hapus_capaian.py`
  35/35 (dengan prasyarat bulan 8 sementara, dipulihkan + sidik jari SAMA), `test_t6a_tabel.py` 14/14,
  `test_t6b_input_wasilah.py` 29/29, `test_t6d2_masul_input.py` 68/68, `test_seed_bersih.py` 6/6,
  `test_data_awal_tahun_kedua.py` 5/5, `test_no_halaqah.py` 9/9, `test_students_without_halaqah.py`
  13/13, `test_students_without_halaqah_p6.py` 6/7 (1 SKIP wali), `test_auth_signup_closed.py` 9/9,
  `npm test` 14/14. `typecheck` hijau; `build` berhasil.
- **Sidik jari:** 16.504 baris, 19 tabel, **SAMA** sebelum/sesudah rangkaian uji T7. Perubahan skema
  (`+36` target DUMMY dan kolom baru) sudah terjadi **sebelum** sidik jari pembanding di sesi ini;
  kolom baru tidak mengubah baris lama.

### DUMMY yang harus diganti
- **25 target Wasilah + 11 target Ghayah** = DUMMY, `amount=1`, `bulanan`, berlaku Syawwal 1447,
  catatan `DUMMY - target sementara Wasilah/Ghayah...`. Skrip: `scripts/db/fixes/2026-11-26_t7b_target_dummy_wasilah_ghayah.sql`.
  Wajib diganti data asli di T8/T10. Sudah dicatat di `docs/DATA-NOTES.md`.

### Belum selesai (T7 [2/2])
- Halaman `/target`: daftar target, form ajukan/ubah, persetujuan Masul, penolakan dengan alasan,
  pembatalan, riwayat, dan konfirmasi bulan lewat/terkunci.
- Uji E2E UI T7.
- Verifikasi produksi/smoke setelah UI selesai.

---

## 3. Status Supabase

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1` (Singapore).

### Migrasi
32 berkas migrasi, **ketigapuluh duanya tercatat sudah dijalankan** di `supabase_migrations.schema_migrations`:

| Versi | Nama |
|---|---|
| 20261121000001 | core_calendar |
| 20261121000002 | students_curriculum |
| 20261121000003 | halaqah |
| 20261121000004 | targets_progress |
| 20261121000005 | functions_views |
| 20261121000006 | rls |
| 20261121000007 | harden_function_grants |
| 20261121000008 | month_zero_not_open |
| 20261121000009 | students_without_halaqah |
| 20261124000010 | attendance_guard_revoke |
| 20261124000011 | curriculum_search (T5c) |
| 20261124000012 | input_alquran_data (T5c-2) |
| 20261125000013 | wasilah_input (T6b) |
| 20261125000014 | wasilah_input_hadir (T6b) |
| 20261125000015 | masul_domain_write (T6b) |
| 20261125000016 | masul_domain_scope_fix (T6b) |
| 20261125000017 | masul_input_domain (T6d2 - seragamkan hak Masul + kolom jejak) |
| 20261125000018 | catat_jejak_tanpa_jwt (T6d2 - koreksi trigger tanpa JWT) |
| 20261125000019 | hapus_capaian_log (T6e - RPC hapus capaian + tabel change_log) |
| 20261125000020 | log_abaikan_update_kosong (T6e - jangan catat UPDATE tanpa perubahan) |
| 20261126000021 | targets_dinamis (T7a - view target bulan 0/kasus f, helper) |
| 20261126000022 | targets_rpc (T7a - ajukan/setujui/tolak) |
| 20261126000023 | targets_rpc2 (T7a - ubah/massal/riwayat) |
| 20261126000024 | targets_grants (T7a - EXECUTE hanya authenticated) |
| 20261126000025 | targets_rpc_fix_volatile (T7a) |
| 20261126000026 | targets_view_f_fix (T7a - kasus f) |
| 20261126000027 | targets_view_tiebreak (T7a - deterministik) |
| 20261126000028 | targets_status_cancel (T7a - enum dibatalkan) |
| 20261126000029 | targets_rpc_only_audit_cancel (T7a - kunci tulis + RPC batalkan) |
| 20261126000030 | targets_massal_xor_fix (T7a - massal per santri) |
| 20261126000031 | targets_audit_semantics (T7a - jejak pengubah) |
| 20261126000032 | targets_tujuan_akhir (T7c - butir tujuan akhir Wasilah/Ghayah, constraint, unique index, REVOKE PUBLIC/anon) |

Migrasi berikutnya wajib memakai nomor `20261126000033_...` dan **tidak boleh** mengubah berkas lama.

### RLS (Row Level Security)
- **19 dari 19 tabel** memiliki `relrowsecurity = true` (termasuk `change_log`, hanya SELECT).
- **42 kebijakan** tersebar di **19 tabel** (diperiksa langsung 26 Nov 2026): `attendance`, `monthly_notes`,
  `progress_entries` masing-masing 4; `targets` **hanya 1 (SELECT)**; `change_log` 1 (hanya SELECT); sisanya 2.
- `targets` sejak T7 **tidak punya policy INSERT/UPDATE/DELETE** dan privilege tulis dicabut dari
  `anon`/`authenticated`; seluruh perubahan target lewat RPC (`SECURITY DEFINER`, cek hak di dalam).
- `targets_read` tetap `is_staff()`: semua staf membaca, anon tidak.

### Fungsi dan view
- **50 fungsi** di skema `public` (diperiksa langsung 26 Nov 2026). Tambahan T7: `target_bulan_berjalan`,
  `target_info_konfirmasi`, `target_cek_konfirmasi`, `target_boleh_ajukan`, `target_validasi_bentuk`,
  `ajukan_target`, `setujui_target`, `tolak_target`, `ubah_target`, `ajukan_target_massal_alquran`,
  `riwayat_target`, `batalkan_target`, `catat_jejak_target`.
- **4 view**: `v_monthly_report`, `v_monthly_report_base`, `v_attendance`, `v_months_ordered`.

### Isi seed (data dummy, hasil hitung langsung)

| Tabel | Baris |
|---|---|
| `academic_years` | 1 |
| `hijri_months` | 13 |
| `subjects` | 9 |
| `books` | 158 |
| `curriculum_items` | 10.954 |
| `students` | 109 |
| `guardians` | **0** |
| `student_levels` | 217 |
| `halaqahs` | 38 |
| `halaqah_members` | 324 |
| `halaqah_teachers` | 55 |
| `halaqah_subjects` | 78 |
| `targets` | **364** (328 Al Qur'an + 25 DUMMY Wasilah + 11 DUMMY Ghayah bentuk tujuan akhir) |
| `progress_entries` | 2.036 |
| `attendance` | 599 (berkas seed; DB produksi 613 - lihat 2k) |
| `monthly_notes` | **0** |
| `month_domain_settings` | 7 |
| `profiles` | 24 |

Catatan:
- `month_domain_settings` **hanya berisi domain `alquran`** untuk bulan 1-7 (Syawwal s.d. Rabiul Akhir), `is_locked` semuanya `false`. Belum ada baris Wasilah maupun Ghayah, dan bulan 8-12 belum punya Hari Efektif.
- `guardians` dan `monthly_notes` kosong: fitur wali belum aktif, catatan bulanan belum pernah diisi pada data uji.

---

## 4. Status Vercel

| Hal | Hasil |
|---|---|
| Project | `kusafa-app` (akun `pencapaiansantrikusafa`), terhubung ke repo GitHub |
| Deploy terakhir | status **Ready** (Production) |
| Halaman utama | `HTTP 200`, judul "KUSAFA - Evaluasi dan Capaian Santri" |
| Bundel yang disajikan | `/assets/index-BR2k_-OJ.js` (react-router 7.18.6) — **sama persis** dengan hasil `npm run build` lokal dari commit `0378f87` |
| Sambungan Supabase | **TERBUKTI 24 Nov 2026**: smoke E2E produksi **28/28 PASS** (7 role login, halaman utama, kotak notifikasi, halaman Capaian, konsol bersih) tanpa menulis data |
| Environment | hanya `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY` (menurut catatan setup; isi nilainya tidak diperiksa ulang dan tidak boleh ditulis di repo) |

Catatan: teks "Tersambung ke Supabase." yang dulu dipakai pada tahap F **sudah tidak ada** di kode sumber (itu halaman uji sementara). Halaman pertama sekarang adalah formulir login. Jadi pertanyaan "apakah situs menampilkan 'Tersambung ke Supabase.'" jawabannya: tidak lagi, dan itu wajar - bukti sambungan sekarang adalah login berhasil.

---

## 5. Rute dan halaman yang benar-benar ada

Dari `src/App.tsx`:

| Rute | Komponen | Keadaan |
|---|---|---|
| `/` | `Beranda` | Mengalihkan ke menu pertama sesuai role |
| `/capaian` | pengalihan | ke `/capaian/alquran` |
| `/capaian/:domain` | `CapaianPage` | Berfungsi untuk ketiga domain (tab Al Qur'an / Ilmu Wasilah / Ilmu Ghayah); tombol hapus capaian untuk Mudir/Admin (T6e) |
| `/santri/:id` | `SantriPage` | Berfungsi |
| `/input` | `InputPage` | Berfungsi (tab Al Qur'an / Ilmu Wasilah / Ilmu Ghayah) |
| `/target`, `/target/:domain` | `TargetPage` | Berfungsi (T7 [2/2]); form Wasilah/Ghayah mengirim `amount` sampai T7c [3/3] |
| `/kurikulum` | `PlaceholderPage` | Belum diisi (T8) |
| `/halaqah` | `PlaceholderPage` | Belum diisi (T8) |
| `/pengaturan` | `PlaceholderPage` | Belum diisi (T8) |
| `*` | `Beranda` | Rute tak dikenal dialihkan |

---

## 6. Bug dan galat yang diketahui

**Tidak ada galat build, tsc, atau uji.** Yang berikut ini adalah keterbatasan yang diketahui, bukan galat yang menggantung:

1. **Dropdown item dibatasi 60 hasil pertama** (`batasTampil`). Sudah diringankan: pencarian bisa memakai nomor ("88" atau "menyalin 88") dan panel menulis "Menampilkan 60 dari N". Item ke-61 dan seterusnya tetap harus lewat pencarian yang lebih spesifik.
2. **Label item bisa sama antar mata pelajaran** karena buku yang sama dipakai lebih dari satu bidang (mis. Juz 'Amma di Tilawah dan Kitabah). Sudah diatasi dengan awalan nama mata pelajaran ("Tahfidz · An Naba' - 40"). Label di database tidak diubah.
3. **69 capaian pada data dummy lebih kecil dari bulan sebelumnya** (Tahfidz 27, Kitabah 26, Tilawah 16; menyentuh 49 santri). Keputusan Mudir: dibiarkan karena dummy dan akan dihapus di T10. Di aplikasi, bidang seperti ini tampil dengan penanda ⚠ dan tidak ditanyakan bila tidak diubah.
4. **Hari Efektif belum bisa diisi dari aplikasi** (T8). Akibatnya bulan 8-12 tidak diperiksa oleh notifikasi "data belum lengkap" selama `month_domain_settings` belum punya barisnya. Ini disengaja dan sudah disepakati (opsi B, 23 Nov 2026).
5. **Kinerja memuat daftar item**: catatan sesi sebelumnya menyebut sekitar 4,7 detik untuk ±1.000 baris karena diambil per buku. **BELUM DIVERIFIKASI ulang** pada sesi ini.
6. ~~Kerentanan `react-router` 6.x~~ **SELESAI**: naik ke react-router 7.18.6 (branch `chore/react-router-fix` sudah di-merge 24 Nov 2026). Bila `npm audit` masih menyebut 2 kerentanan, periksa ulang dengan `npm audit --omit=dev` sebelum menyimpulkan.
7. **Level 6 belum punya pengampu dan jadwal** (4 santri). Ini data, bukan kode; menunggu keputusan Mudir.
8. ~~**Hari Efektif Rabiul Awwal hanya 3 hari** sedangkan bulan lain 15-21.~~ **BUKAN MASALAH (koreksi Mudir 24 Nov 2026):** 3 hari **BENAR** karena libur ~2 pekan lebih. Nilai 19 dibatalkan dan dipulihkan ke 3. Excel sumber tidak perlu diubah.
9. ~~Pendaftaran (signup) publik masih aktif~~ **SELESAI (24 Nov 2026)**: `disable_signup = true` lewat Management API; signup ditolak `422 signup_disabled` (diuji `test_auth_signup_closed.py` 9/9). Akun baru hanya dibuat Admin.
10. **Log `change_log` tumbuh terus (append-only)**: 96 baris saat penutupan sesi T6e. Belum ada pemangkasan/retensi; bila perlu, keputusan Mudir (T9/T10).
11. **8 sel matriks RLS masih SKIP**: menunggu profil `wali` dan contoh target berstatus `diajukan` (T9).

## 2o. T7 [2/2] - UI `/target` + notifikasi target (26 November 2026)

**Cakupan sesi ini:** UI target, notifikasi target, tampilan kolom target, dan uji baca-saja.
Uji UI yang **menulis** diselesaikan pada bagian **2p** (38/38, sidik jari SAMA); peragaan ulang E2E lama
dan smoke produksi juga sudah dijalankan di 2p.

### Berkas baru/diubah

- `src/pages/TargetPage.tsx` (tab 3 domain), `src/pages/TargetDomainPage.tsx` (daftar, saringan, aksi,
  kartu HP), `src/components/FormTarget.tsx` (ajukan/ubah + massal Al Qur'an + konfirmasi bulan),
  `src/components/DialogAksiTarget.tsx` (setujui/tolak wajib alasan/batalkan),
  `src/components/DialogRiwayatTarget.tsx`, `src/lib/target.ts` (pembungkus RPC + label status).
- `src/components/KotakBelumLengkap.tsx`: bagian **Target** (menunggu persetujuan, DUMMY, belum punya target).
- `src/pages/TabelAlQuran.tsx`, `TabelWasilah.tsx`, `TabelCapaian.tsx`, `SantriPage.tsx`: target kosong
  ditampilkan `–`, angka 0 tetap `0`; semua angka dari `v_monthly_report`.
- `src/components/PemilihHalaqah.tsx`: dukungan `opsiKosong` untuk saringan "Semua halaqah".
- `scripts/qa/pulihkan_data.py`: `targets` ikut disimpan/dipulihkan PERSIS (seluruh kolom).
- `scripts/qa/test_t7_target_ui.py`: uji E2E **baca-saja** 36/36.

### Hasil yang sudah dijalankan

| Pemeriksaan | Hasil |
|---|---|
| `npm run typecheck` | **HIJAU** |
| `npm run build` | **BERHASIL** |
| `npm run test` | **14/14** |
| `test_t7_target_ui.py` (E2E baca-saja, 1280 px + 360 px) | **36/36 LULUS** |
| Waktu siap halaman `/target` (buka rute -> baris target tampil) | **847 ms** (< 1,5 detik) |
| Console browser | bersih (0 error) |
| `check_repo_safety.py` | **LOLOS** |

### Catatan teknis

- Nama sasaran, mata pelajaran, bulan, dan pengaju/penyetuju diambil **satu query dengan embed PostgREST**
  (`students`, `halaqahs`, `subjects`, `hijri_months`, `profiles!targets_*_fkey`), bukan mengunduh seluruh
  daftar santri/profil. Saringan halaqah Al Qur'an memakai `halaqah_members` karena target Al Qur'an
  menyimpan `student_id` (bukan `halaqah_id`).
- Semua tulis `targets` tetap lewat RPC; tidak ada INSERT/UPDATE/DELETE langsung dari UI.
- Target DUMMY dikenali dari `note like 'DUMMY - target sementara Wasilah/Ghayah%'`.
- Capaian Wasilah/Ghayah 0 baris adalah BENAR (Excel tidak punya kolom capaian); lihat `docs/DATA-NOTES.md` bagian 12.

---

## 2p. T7 [2/2] - uji UI target yang MENULIS + E2E ulang (26 November 2026)

**Perintah kerja:** uji tulis lewat RPC (bukan SQL) per role sambil memeriksa tampilan; jalankan ulang E2E
T6a/T6b/T6d2/T6e + dropdown + smoke produksi; pulihkan data PERSIS; jangan menghapus baris target baru
buatan Mudir; berhenti sebelum T8.

### Berkas
- `scripts/qa/test_t7_target_tulis.py` (baru): E2E yang menulis lewat UI (RPC), **38 uji**.
- `scripts/qa/pulihkan_data.py`: `pulihkan(db, asli, urus=...)`. `urus` membatasi baris yang boleh
  disentuh uji; baris baru milik orang lain (mis. Mudir mencoba `/target`) **tidak dihapus/ ditimpa**.
  Tanpa `urus`, perilaku lama dipertahankan (dipakai uji-uji T6).
- `scripts/qa/test_input_dropdown_e2e.py`: langkah a2 memakai bulan **Jumadal Ula** (sebelumnya
  Jumadal Akhir). Alasannya di bawah.

### Hasil `test_t7_target_tulis.py` - 38/38 LULUS (sidik jari SAMA)
Konteks run: HLQ-PA-1, pengampu Ust. Fulan 1, santri Santriwan fulan 7, Hadir bulan 7 = 18.

| Alur | Bukti di tampilan & database |
|---|---|
| Pengampu mengajukan | 3 target (Tilawah 3, Tahfidz 2, Kitabah 1) berstatus **Diajukan**; pengampu **tidak** melihat tombol Setujui/Tolak; bulan default = bulan berjalan (Rabiul Akhir) |
| Masul Al Quran menyetujui | Tilawah **disetujui**, `approved_by` = Masul Al Quran; `v_monthly_report` `target_amount` 3, `target_monthly` 54 (=3×18); halaman Capaian menampilkan target baru |
| Tolak dengan alasan | Tahfidz **ditolak**, `alasan_tolak` tersimpan; pengampu melihat status **Ditolak** + alasannya |
| Pengaju membatalkan | Kitabah **dibatalkan** (baris tetap tersimpan sebagai riwayat) |
| Masul lintas domain | Masul Wasilah dialihkan dari `/target/alquran` ke `/target/wasilah`; target uji tetap `diajukan` (tidak disetujui) |
| Bulan lewat (pengampu) | Peringatan "SUDAH LEWAT"; Simpan **nonaktif**; hanya Mudir/Admin yang boleh |
| Bulan lewat (Mudir) | Centang "Saya (Mudir/Admin) tetap ingin melanjutkan" muncul; Simpan aktif setelah dicentang; target bulan Rabiul Awwal tersimpan & disetujui |
| Bulan terkunci | Dengan `is_locked=true` sementara, Mudir/Admin melihat peringatan "SUDAH DIKUNCI" + centang konfirmasi (lalu `is_locked` dipulihkan) |
| Tab & URL | 1280 px: `/target` → `/target/alquran`, 3 tab, klik tab mengganti URL. 360 px: ketiga domain, 3 tab ≥44 px, tanpa geseran samping |
| Konsol | bersih (0 error) |

**Disiplin data:** salinan penuh di awal, semua target uji ditandai `note` `UJI-T7-TULIS-<waktu>`;
pemulihan hanya menghapus baris bertanda itu. Diverifikasi: tidak ada baris target lama yang hilang,
nilai baris lama tidak berubah, tidak ada baris uji tertinggal, `targets` kembali **363**, sidik jari
**SAMA** (16.504 baris, 19 tabel). `change_log` bertambah (append-only, baris lama utuh) - itu bukti.
Pada run ini **0 baris target baru milik Mudir** ditemukan; bila ada, skrip melaporkan jumlah & isinya
dan sengaja **tidak menghapusnya** (bukan kegagalan sidik jari).

### E2E ulang + smoke produksi
| Rangkaian | Hasil |
|---|---|
| `test_t6a_tabel.py` | **14/14** |
| `test_t6b_e2e.py` | **14/14** (data dipulihkan persis, sidik jari sama) |
| `test_t6d2_e2e_masul.py` | **14/14** (data & jejak dipulihkan) |
| `test_t6e_e2e_hapus.py` | **16/16** (data dipulihkan, log bertambah) |
| `test_input_dropdown_e2e.py` | **10/10** (capaian 2.036 → 2.036) |
| `smoke_e2e.py` produksi (`https://kusafa-app.vercel.app`) | **42/42 PASS** (baca saja) |

**Perbaikan uji dropdown:** langkah a2 memilih "Jumadal Akhir" dan mengharapkan "Bulan lalu" berisi dari
"Jumadal Ula". Namun data seed berhenti di **Rabiul Akhir (bulan 7)**; bulan 8-9 kosong, sehingga
"belum diisi" **benar**. Uji kini memakai **Jumadal Ula (bulan 8)** yang bulan sebelumnya (Rabiul Akhir)
terisi: dropdown kosong tetapi "Bulan lalu" berisi. Ini memperbaiki uji yang bergantung data, bukan
mengubah logika aplikasi.

### Keadaan data akhir
`targets` **363** (327 Al Qur'an + 36 DUMMY), `progress_entries` **2.036**, kehadiran **599 / 756 / 749**,
`monthly_notes` 0, `month_domain_settings` 21, `change_log` **305**. Tidak ada baris target uji tersisa;
`is_locked` bulan 7 kembali `false`.

---

## 2q. T7c [1/3] - target Wasilah/Ghayah = TUJUAN AKHIR (database + RPC + uji, 26 November 2026)

**Cakupan sesi ini:** database, RPC, DUMMY, uji, dokumen. **UI belum diubah** (itu T7c [2/3]).
Sesi sebelumnya terputus (galat 413) setelah migrasi `000032` diterapkan langsung lewat `db:sql`;
sesi ini **melanjutkan**, bukan mengulang.

### Kondisi awal yang ditemukan (audit baca-saja)

| Yang diperiksa | Temuan |
|---|---|
| Migrasi | Berkas `20261126000032_targets_tujuan_akhir.sql` ada, tetapi **belum tercatat** di `supabase_migrations.schema_migrations` (terakhir 000031) |
| Objek database | Kolom `targets.target_item_id`, constraint `targets_bentuk_check`, index `targets_satu_diajukan_uk`, trigger `target_validasi_butir_trg`, dan RPC baru **sudah ada** (diterapkan sesi lalu) |
| Overload fungsi | **Tidak ada** (satu signature per nama; 9-arg/5-arg sudah di-DROP) |
| Hak EXECUTE | `ajukan_target` dan `ubah_target` **masih terbuka ke PUBLIC/anon** (berkas yang diterapkan sesi lalu belum memuat REVOKE untuk keduanya) |
| DUMMY | 36 baris lama (`amount=1`) **sudah dihapus** (change_log 11:26 UTC, 25 Wasilah + 11 Ghayah); 36 baris bentuk baru (butir) **sudah dibuat** |
| Target Al Qur'an hari ini | **1 baris**: Tahfidz, Santriwan fulan 26, Rabiul Akhir, amount 2, `disetujui`, `proposed_by` = Ust. Fulan 1 (musyrif), 26 Nov 09:27 UTC. **Tidak dihapus** (perintah kerja); lihat DATA-NOTES 0b |
| Sidik jari | `docs/qa/db_fingerprint_t7c_sebelum.json` (sesi lalu) vs sekarang: **hanya `targets`** yang berubah (364 -> 364 baris, checksum berubah) = perubahan DUMMY yang diperintahkan; tabel lain SAMA |

### Yang dikerjakan

1. **Constraint bentuk diperbaiki**: `targets_bentuk_check` semula melarang target Al Qur'an per HALAQAH.
   Aturan (c) T7 tetap "individu didahulukan dari halaqah", jadi Al Qur'an **kembali** boleh per santri
   ATAU per halaqah (tetap `amount` + `harian`, `target_item_id` kosong). Wasilah/Ghayah: halaqah +
   butir, `amount` kosong. Berkas `000032` = berkas final yang diterapkan.
2. **REVOKE EXECUTE dari PUBLIC + anon untuk SELURUH keluarga fungsi target** lewat DO-block idempoten
   di migrasi `000032` (bukan hanya 7 nama). Diverifikasi: 15 fungsi target, `anon=0`, `PUBLIC=0`,
   `authenticated=1` untuk RPC.
3. **Migrasi `000032` dicatat** di `supabase_migrations.schema_migrations` (idempoten, hanya bila belum ada).
4. **Skrip DUMMY lama diperbaiki**: `2026-11-26_t7c_hapus_target_dummy_lama.sql` semula memakai
   `note like 'DUMMY%'` sehingga **ikut menghapus DUMMY bentuk baru** bila dijalankan ulang. Kini hanya
   bentuk lama (`amount = 1`, `target_item_id` kosong, catatan berpola koma). Diverifikasi: 0 baris cocok.
5. **Skrip DUMMY T7b ditandai DIGANTIKAN** (tidak boleh dijalankan lagi; database akan menolaknya).
6. **Uji baru `scripts/qa/test_t7c_target_tujuan.py` - 48/48 LULUS**, semuanya transaksi + ROLLBACK.
7. **Uji lama disesuaikan** ke bentuk baru (dua tempat di `test_targets_t7.py`; satu di antaranya
   menguji prioritas individu vs halaqah yang kini memakai target halaqah Wasilah berbentuk butir).
8. **`regression_execute.py` diperluas** dengan pemeriksaan **PUBLIC** EXECUTE (bukan hanya anon): **8/8 PASS**.

### Hasil uji

| Rangkaian | Hasil |
|---|---|
| `test_t7c_target_tujuan.py` (baru, 48 uji) | **48/48 LULUS** |
| `test_targets_t7.py` (lama, 34 uji) | **34/34 LULUS** |
| `regression_execute.py` | **8/8 PASS** (A2 baru: 0 fungsi public ber-EXECUTE PUBLIC) |
| `rls_matrix.py` | **94/97 OK, 3 SKIP, 0 GAGAL** |
| `test_t7_target_ui.py` (E2E baca-saja) | **36/36 LULUS** |
| `test_t7_target_tulis.py` (E2E menulis lewat UI/RPC) | **38/38 LULUS** |
| `npm run typecheck` / `npm run build` | hijau / berhasil |
| Sidik jari sesudah seluruh uji | **SAMA** (16.505 baris, 19 tabel) |

Cakupan uji baru (per butir perintah kerja):

- **Bentuk**: panggilan LAMA Al Qur'an 9 argumen sukses (frontend produksi tetap jalan); Wasilah bentuk
  lama (`amount`, tanpa butir) ditolak **"wajib memilih butir kurikulum"**; amount + butir ditolak;
  butir mapel lain / nonaktif / mapel tak ditetapkan halaqah ditolak; Wasilah per santri ditolak;
  INSERT langsung bentuk lama & bentuk campuran ditolak constraint; `.amount` tersimpan KOSONG.
- **Satu target menunggu** per (halaqah, mapel, bulan): pengajuan baru -> lama `dibatalkan`, hanya 1
  `diajukan`; unique index menolak dua baris `diajukan` dengan kunci sama.
- **Hak & lintas domain**: pengampu mengajukan (`diajukan`) & tidak menyetujui; Masul Wasilah menyetujui,
  Masul Ghayah/Al Quran ditolak; Masul Wasilah mengajukan -> otomatis disetujui; Masul lintas domain
  ditolak; pengampu halaqah lain ditolak; anon ditolak (`42501`).
- **Bulk `setujui_target_halaqah`**: menyetujui semua yang menunggu untuk halaqah x bulan; bulan lain
  tidak ikut; Masul domain lain & pengampu ditolak; bulan terkunci: Masul ditolak, Mudir dengan
  konfirmasi diterima.
- **Pengganti & ubah**: `ubah_target` membuat baris baru (butir baru, amount kosong), lama utuh;
  panggilan LAMA `ubah_target` 5 argumen Al Qur'an tetap jalan; hanya pengaju dapat membatalkan.
- **Laporan**: checksum `v_monthly_report` **Al Qur'an identik** sebelum/di dalam/sesudah perubahan
  Wasilah; Al Qur'an `target_monthly` = jumlah x Hadir (2,5 x 18 = 45); target Wasilah dikenali
  (`target_id` ada) tetapi **tanpa angka** (`target_monthly` NULL, bukan 0) - lihat "Belum" di bawah.
- **DUMMY**: 25 Wasilah + 11 Ghayah bentuk baru, 0 baris bentuk lama, semua butir milik buku mapelnya & aktif.
- **Overload**: 1 signature per RPC; `riwayat_target` menyertakan butir & buku.

### Keadaan data akhir

`targets` **364** (327 seed + 1 baris sisa uji T7 [2/2] + 25 DUMMY Wasilah + 11 DUMMY Ghayah),
`progress_entries` 2.036, kehadiran 599 / 756 / 749, `monthly_notes` 0, `month_domain_settings` 21,
`change_log` bertambah (append-only; baris lama utuh). Tidak ada baris uji T7c yang tertinggal.

### Belum - BACKEND [2/3] dan UI [3/3]

- **BACKEND [2/3]**: `halaqah_mapel_aktif`, RPC simpan gabungan capaian + target bulan depan, tuntas/Level 6,
  dan kolom target butir untuk Wasilah/Ghayah di `v_monthly_report` (angka targetnya kini NULL —
  jujur: tidak ada angka; tampilan "target = posisi/butir" menyusul di [2/3]).
- **UI [3/3]**: halaman `/target` belum mengenal `target_item_id`: form Wasilah/Ghayah masih mengirim
  `amount`, sehingga **pengajuan Wasilah/Ghayah dari UI akan ditolak database** sampai [3/3] selesai.
  Daftar/riwayat juga belum menampilkan butir tujuan akhir.
- Notifikasi "target DUMMY" masih mengenali catatan DUMMY (pola lama tetap cocok).

### Uji lama yang dijalankan ulang setelah T7c [1/3]

| Rangkaian | Hasil |
|---|---|
| `test_t6a_tabel.py` | **14/14** |
| `test_t6b_input_wasilah.py` | **29/29** |
| `test_t6d2_masul_input.py` | **68/68** |
| `test_no_halaqah.py` / `test_students_without_halaqah.py` | **9/9** / **13/13** |
| `test_seed_bersih.py` | **6/6** |
| `compare_alquran_full_excel.py` (penuh) | **7/7** |
| `compare_rabiul_awwal_excel.py` | **7/7** |
| `test_data_awal_tahun_kedua.py` | **5/5** |

Keduanya kini **SUDAH dijalankan ulang 27 November 2026** (lihat 2r): `test_t6e_hapus_capaian.py`
**35/35** (dengan baris capaian bulan 8 sementara, sidik jari SAMA) dan smoke produksi Vercel
**42/42 PASS** (baca saja).

---

## 2r. T7c [2/3] BACKEND - simpan gabungan capaian + target bulan depan (27 November 2026)

**Perintah Mudir 27 November 2026.** Penamaan dikoreksi: **[2/3] = BACKEND, [3/3] = UI** (sebelumnya
tertukar di dokumen). Tidak menyentuh UI dan tidak memulai T8.

### Migrasi baru (3 berkas, tercatat; total kini 35)

| Nomor | Isi |
|---|---|
| `20261127000033_halaqah_mapel_aktif.sql` | `halaqah_mapel_aktif(halaqah, bulan)` sebagai **sumber tunggal** mapel aktif (kini `halaqah_subjects`; T8 tinggal menambah masa berlaku di dalam fungsi tanpa mengubah pemanggil); `bulan_berikutnya(bulan)`; helper tuntas `mapel_butir_terakhir`, `mapel_tuntas`, `halaqah_tanpa_mapel`. Dipakai di `wasilah_input_boot` & `wasilah_input_form` (menggantikan baca `halaqah_subjects` langsung). |
| `20261127000034_wasilah_simpan_gabungan.sql` | RPC **`wasilah_simpan_gabungan(halaqah, bulan, capaian, target, konfirmasi)`** — capaian bulan ini (alur T6b: sekali per halaqah x mapel, disalin ke anggota) + target bulan depan, **satu transaksi** (gagal satu, batal semua). Menolak bila ada mapel aktif (yang boleh ditulis pemanggil) tanpa target, **kecuali tuntas**; tanpa bulan berikutnya = target tidak diminta. Pengampu → `diajukan`; Masul domain/Mudir/Admin → `disetujui` (via **`wasilah_target_bulan_depan`** SECURITY DEFINER). Target di bawah capaian diterima + dilaporkan di `di_bawah_capaian`. Level 6 = "Tuntas, belum ada pelajaran lanjutan". Juga `halaqah_status_tuntas(halaqah, bulan)` untuk notifikasi Masul. |
| `20261127000035_v_monthly_report_tujuan_akhir.sql` | **`v_monthly_report`** (dan base) menambah kolom `target_item_id, target_label, target_pos, target_tercapai, target_kurang, target_status` untuk Wasilah/Ghayah: status `'Tercapai'` / `'Kurang N butir'` (lintas buku lewat `item_position`), NULL bila tak ada target disetujui. Al Qur'an **identik** (butir target NULL; hash baris Al Qur'an tak berubah). Hanya menambah kolom di akhir; `security_invoker` dipertahankan. |

### Yang diuji — `test_t7c_simpan_gabungan.py` **18/18 LULUS**, sidik jari **SAMA**

- Mudir menyimpan gabungan: capaian tersalin ke semua anggota + target bulan depan `disetujui`.
- **Ditolak** bila mapel aktif (yang boleh ditulis) tanpa target; capaian **tidak** tersimpan.
- Mapel **tuntas** (butir terakhir buku terakhir) **dikecualikan** dari kewajiban target.
- Bulan **terakhir** (Ramadhan): target tidak diminta; mengirim target ditolak jelas.
- **Hak per role**: pengampu mapelnya → `diajukan`; Masul Wasilah/Mudir/Admin → `disetujui`;
  Masul Ghayah & Masul Al Quran di halaqah Wasilah → **ditolak**; **anon → ditolak**.
- **Target di bawah capaian diterima** + dilaporkan di `di_bawah_capaian`.
- **Level 6** → "Tuntas, belum ada pelajaran lanjutan", tidak menulis apa pun.
- **Lintas buku** (Hisab): capaian *Anak Islam Pandai Berhitung 4* (pos 175) → target *Matematika
  Jilid 1* (pos 176) = **`Kurang 1 butir`**; capaian maju (pos 177) = **`Tercapai`**; mapel tanpa
  target = kolom target **kosong (null), bukan 0**.
- **`v_monthly_report` Al Qur'an sebelum vs sesudah simpan gabungan identik.**

### Regresi penuh (semua hijau)

`regression_execute.py` 8/8; `test_targets_t7.py` 34/34; `test_t7c_target_tujuan.py` 48/48;
`rls_matrix.py` 94/97 (3 SKIP, 0 GAGAL); `test_t6a_tabel.py` 14/14; `test_t6b_input_wasilah.py`
29/29; `test_t6e_hapus_capaian.py` 35/35; `npm run typecheck` hijau; `npm run build` berhasil;
`npm test` 14/14. Smoke produksi (baca saja) **42/42 PASS**.

### Catatan penting / jujur

- **Asumsi (HANDOVER §5.13, mohon konfirmasi Mudir):** keputusan 3.2a "target wajib tiap mapel
  aktif" bila harfiah membuat pengampu 1-mapel dari halaqah 2-mapel **tidak bisa** menyimpan.
  Diimplementasikan: kewajiban target hanya untuk **mapel aktif yang boleh ditulis pemanggil**.
- **Tulis langsung `targets` tetap tertutup**: RPC gabungan (INVOKER) menulis target lewat
  `wasilah_target_bulan_depan` (DEFINER). Tidak ada policy tulis `targets` baru.
- **Tidak ada penggantian fungsi lama** kecuali `wasilah_input_boot`/`form` (create or replace,
  kini memakai `halaqah_mapel_aktif`; perilaku form/boot sama — T6a/T6b tetap hijau).
- **UI belum diubah** (itu [3/3]). T8 **belum** dimulai.
