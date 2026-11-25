# STATUS - kondisi nyata proyek KUSAFA

**Sumber kebenaran status.** Diperbarui: **24 November 2026** (pra-T6 langkah [3/5], [4/5], audit [5/5], dan **[6]** jawaban Mudir + penutupan celah).
Setiap sub-tugas selesai wajib memperbarui berkas ini bersama `docs/HANDOVER.md`.

| | |
|---|---|
| Repo | `https://github.com/pencapaiansantrikusafa-cpu/kusafa-app` (PUBLIK) |
| Branch | `main` — branch `chore/react-router-fix` **sudah di-merge** 24 Nov 2026 (react-router 7.18.6) |
| Commit terakhir | `30ceb8c` - T6d tab domain Capaian & Input |
| Keadaan Git saat pembaruan | bersih, sinkron `origin/main` |
| Situs produksi | `https://kusafa-app.vercel.app` |

Semua angka di bawah diperiksa langsung pada 23-24 November 2026 (perintah dan hasilnya dicatat di bagian terkait).
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
| **T3** | Tabel capaian halaqah Al Qur'an | **SELESAI** | `src/pages/CapaianPage.tsx`, `TabelCapaian.tsx`, `TabelAlQuran.tsx`, `src/lib/laporan.ts` | Wasilah/Ghayah masih pesan "dikerjakan pada T6" |
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
| **T6d** | Tab domain di halaman Capaian (seperti halaman Input) | **SELESAI** (lihat 2j) | `TabDomain.tsx`, `CapaianPage.tsx`, `InputPage.tsx`; E2E 28/28 lokal & produksi | — |
| **T7** | Target dinamis (ajukan/setujui) | **BELUM** | Rute `/target` memakai `PlaceholderPage` | - |
| **T8** | Kurikulum, halaqah, santri, kalender, Hari Efektif & kunci bulan | **BELUM** | Rute `/kurikulum`, `/halaqah`, `/pengaturan` memakai `PlaceholderPage` | Hari Efektif saat ini hanya bisa diisi lewat SQL/dashboard |
| **T9** | Pengujian & QA | **BELUM** | Baru `tests/putaran.test.mjs` (6 uji) + uji manual ad hoc | Uji RLS otomatis belum dibuat; uji tulis RLS manual pernah dilakukan (lihat HANDOVER) |
| **T10** | Deploy akhir (hapus data dummy, repo privat) | **BELUM** | - | Repo masih publik, data dummy masih ada |

Catatan kejujuran status:
- T5 ditutup atas permintaan Mudir pada 22-23 November 2026. Yang **belum** di T5 bukan cacat tersembunyi, melainkan bagian yang memang milik T8 (layar Hari Efektif).
- T9 **belum** dikerjakan walaupun beberapa pengujian sudah dilakukan; pengujian yang ada bersifat manual dan tidak otomatis.

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
- Tangkapan layar: `docs/qa/t6d2/` (`masul_alquran_simpan.png`, `masul_wasilah_simpan.png`,
  `masul_ghayah_simpan.png`).

### Catatan data yang perlu keputusan Mudir (bukan bagian T6d2)

1. **7 baris `attendance` Ramadhan (Al Qur'an) tanpa capaian** masih ada di database, padahal
   `docs/DATA-NOTES.md` butir 3 mencatat penghapusannya (606 → 599) sudah disetujui 23 November 2026.
   Baris ini bertanggal seed (22 November) dan tidak tersentuh T6d2. Perlu keputusan: dihapus lagi
   atau dipertahankan.
2. **Nilai izin/sakit/alpha Shafar (bulan 5) di database berbeda dari berkas seed** (36 baris di seed
   bernilai > 0, di database 0). Tidak ada uji yang memeriksa bulan itu dan tidak ada jejak perubahan
   (kolom jejak baru ada sejak T6d2). Perlu keputusan: ikuti seed atau pertahankan database.

---

---

## 3. Status Supabase

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1` (Singapore).

### Migrasi
18 berkas migrasi, **kedelapan belasnya tercatat sudah dijalankan** di `supabase_migrations.schema_migrations`:

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

Migrasi berikutnya wajib memakai nomor `20261125000019_...` dan **tidak boleh** mengubah berkas lama.

### RLS (Row Level Security)
- **18 dari 18 tabel** memiliki `relrowsecurity = true`.
- **44 kebijakan** tersebar di 18 tabel (`attendance`, `monthly_notes`, `progress_entries`, `targets` masing-masing 4; sisanya 2).
- Sejak T6d2 `progress_entries`, `attendance`, dan `monthly_notes` masing-masing **4 kebijakan**
  (insert/update seragam untuk ketiga domain, read, delete khusus Mudir/Admin). Rincian nama kebijakan sengaja tidak disalin ke dokumen ini; dibaca langsung dari `pg_policies` bila perlu.

### Fungsi dan view
- **29 fungsi** di skema `public` - 18 awal + `students_without_halaqah`(_count) + `curriculum_items_search`/`_by_ids` + `input_alquran_data` + `input_alquran_boot` + `wasilah_input_boot`/`_form`/`_save` + `wasilah_can_write` + `catat_jejak` (T6d2). Daftar lengkap di `docs/FILE-MAP.md`.
- **4 view**: `v_monthly_report`, `v_monthly_report_base`, `v_attendance`, `v_months_ordered`. (View percobaan `v_students_without_halaqah` DROPPED di migrasi 000009; diganti fungsi.)

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
| `targets` | 327 |
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
| `/capaian/:domain` | `CapaianPage` | Al Qur'an berfungsi; Wasilah/Ghayah menampilkan pesan "dikerjakan pada T6" |
| `/santri/:id` | `SantriPage` | Berfungsi |
| `/input` | `InputPage` | Berfungsi (Al Qur'an saja) |
| `/target` | `PlaceholderPage` | Belum diisi (T7) |
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
6. **2 kerentanan npm sedang** (`react-router`/`react-router-dom`; GHSA-wrjc-x8rr-h8h6, GHSA-337j-9hxr-rhxg). Keduanya tertambal **hanya** di `7.18.0` (mayor 7); tidak ada versi 6.x tertambal. GHSA-337j tidak memengaruhi SPA ini (tanpa SSR); GHSA-wrjc tidak saat ini dieksploitasi (navigasi memakai rute internal tetap). Naik 6→7 dicoba di branch `chore/react-router-fix` (belum di-merge).
7. **Level 6 belum punya pengampu dan jadwal** (4 santri). Ini data, bukan kode; menunggu keputusan Mudir.
8. ~~**Hari Efektif Rabiul Awwal hanya 3 hari** sedangkan bulan lain 15-21.~~ **BUKAN MASALAH (koreksi Mudir 24 Nov 2026):** 3 hari **BENAR** karena libur ~2 pekan lebih. Nilai 19 dibatalkan dan dipulihkan ke 3. Excel sumber tidak perlu diubah.
9. **Pendaftaran (signup) publik di Supabase Auth masih aktif** (`disable_signup = false`). Belum bisa dimatikan dari lingkungan ini karena butuh Dashboard Supabase atau Management API PAT. **Menunggu tindakan Mudir:** Authentication → Providers → Email → matikan "Allow new users to sign up". Setelah nonaktif, akun hanya dibuat Admin.
