# STATUS - kondisi nyata proyek KUSAFA

**Sumber kebenaran status.** Diperbarui: **24 November 2026** (pra-T6 langkah [3/5], [4/5], audit [5/5], dan **[6]** jawaban Mudir + penutupan celah).
Setiap sub-tugas selesai wajib memperbarui berkas ini bersama `docs/HANDOVER.md`.

| | |
|---|---|
| Repo | `https://github.com/pencapaiansantrikusafa-cpu/kusafa-app` (PUBLIK) |
| Branch | `main` — branch `chore/react-router-fix` **sudah di-merge** 24 Nov 2026 (react-router 7.18.6) |
| Commit terakhir pra-T6 [6] | `74287f5` - dokumentasi pra-T6 [6] |
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
| **Pra-T6 [6]** | Jawaban Mudir + verifikasi & penutupan celah | **SELESAI** | bagian 2d: `scripts/qa/test_auth_signup_closed.py`, `regression_execute.py`, `smoke_e2e.py`, `test_data_awal_tahun_kedua.py`, migrasi `000010` | Urutan berikutnya: merge react-router (**sudah**), T5c percepat input, lalu T6 |
| **T6** | Tabel dan input Wasilah & Ghayah | **BELUM** (belum boleh dimulai) | `TabelCapaian.tsx` masih menulis "dikerjakan pada T6" | Menunggu T5c selesai |
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
| Hari Efektif Rabiul Awwal 3 → 19 | **SELESAI**. DB = 19; `v_attendance` Hadir 17–19 untuk 109 santri; presensi maksimal izin+sakit+alpha = 2. Excel sumber (`BZ5:B113`) masih 3 dan **wajib diperbaiki Mudir** | `scripts/db/fixes/2026-11-24_rabiul_awwal_effective_days.sql`, `docs/DATA-NOTES.md` bagian 3a |
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

### Kinerja muat item (item 3) — **dianalisis, TIDAK diubah**
Penyebab: halaman Input Al Qur'an (`InputPage.tsx`) memuat **semua** `curriculum_items` aktif buku-buku domain itu secara eager (per buku via `ambilSemua`). Ukuran nyata di DB: domain Al Qur'an = **128 buku, 9.177 item aktif** (total 10.954 item, 0 non-aktif). Dropdown hanya menampilkan 60 per buka, tapi 9.177 baris tetap diunduh lebih dulu → lambat (~detik).
- **Opsi A — pencarian di server (RPC)**: tambah fungsi `curriculum_items_search(q)` yang mengembalikan hanya item yang cocok teks/nomor (dibatasi, mis. 100). Dampak: hilang unduh 9 ribu baris; butuh fungsi + RLS + perubahan `DropdownCari` agar memanggil RPC saat mengetik; paling besar dampaknya (disarankan).
- **Opsi B — muat lazy per buku kapital**: muat item buku hanya saat pengguna membuka/berganti buku itu. Dampak: mengurangi transfer awal, tetapi dropdown lintas buku jadi tidak langsung; perlu state buku aktif.
- **Opsi C — cache klien lintas halaman**: simpan daftar item di memori sesi agar hanya halaman pertama lambat; ditambah indeks teks (`pg_trgm`/`tsvector`). Dampak: navigasi berikutnya cepat, tapi muat awal tetap berat; paling kecil usaha.
Rekomendasi: **Opsi A** (paling besar dampak, sesuai kebijakan "ambilSemua untuk daftar 1.000+" dan dropdown 60).

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
| 5. Uji DB pra-T6 16 → 14 | **SELESAI 16/16 PASS**. Penjelasan: tidak pernah ada "16" di repo; yang ada `run_pre_t6_db_tests.py` 14 uji (11-23) → 15 (11-24, +`B4_item_position_function_exists`), tanpa ada yang hilang. Uji `E_hari_efektif_rabiul_awwal` kini **mengharapkan 19** (bukan hanya melaporkan) + uji Hari Efektif mustahil (di luar 1..31). Total kini **16/16** | `docs/qa/db_tests_2026-11-24.json` |
| 6. Smoke E2E per role | **LULUS 29/29 di `main`**, **29/29 di react-router 7**, **28/28 di produksi** (tanpa tulis data). Per role: login, halaman utama, kotak notifikasi, halaman Capaian, konsol bersih. Mudir juga **menyimpan satu capaian lewat UI** lalu menghapus **hanya** baris uji itu (data kembali bersih) | `scripts/qa/smoke_e2e.py`, `docs/qa/smoke_e2e_2026-11-24.json`, `..._prod.json` |
| 7. DATA-NOTES rentang Excel | **SELESAI**. `BZ5:B113` → **`BZ5:BZ113`** (dua tempat) | `docs/DATA-NOTES.md` bagian 3a |
| Jawaban: Bulan 0 | **SESUAI, tanpa ubah kode**. Tahun kedua tanpa bulan 0; Syawwal 1448 memakai Ramadhan 1447; `create_academic_year(...,false)` tidak membuat/meminta Data Awal. Ditulis di SPEC 4a-1 | `scripts/qa/test_data_awal_tahun_kedua.py` — **5/5 PASS** |

Temuan yang perlu jawaban Mudir: **Hari Efektif Syawwal 1447 = 4 hari** (paling kecil di antara bulan lain; mungkin bulan pembuka yang tidak penuh). Dibiarkan, dicatat sebagai pertanyaan terbuka — lihat HANDOVER bagian 5.

---

## 3. Status Supabase

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1` (Singapore).

### Migrasi
10 berkas migrasi, **kesepuluhnya tercatat sudah dijalankan** di `supabase_migrations.schema_migrations`:

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

Migrasi berikutnya wajib memakai nomor `20261124000011_...` dan **tidak boleh** mengubah berkas lama.
(Perhatikan: nomor `000010` di tanggal 24 sudah terpakai, jadi lanjut dari `000011`.)

### RLS (Row Level Security)
- **18 dari 18 tabel** memiliki `relrowsecurity = true`.
- **44 kebijakan** tersebar di 18 tabel (`attendance`, `monthly_notes`, `progress_entries`, `targets` masing-masing 4; sisanya 2).
- Rincian nama kebijakan sengaja tidak disalin ke dokumen ini; dibaca langsung dari `pg_policies` bila perlu.

### Fungsi dan view
- **20 fungsi** di skema `public` - 18 lama + 2 baru (`students_without_halaqah`, `students_without_halaqah_count`). Daftar lengkap di `docs/FILE-MAP.md`.
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
| `attendance` | 599 |
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
8. ~~**Hari Efektif Rabiul Awwal hanya 3 hari** sedangkan bulan lain 15-21.~~ **SELESAI 24 Nov 2026:** dikonfirmasi keliru dan dikoreksi menjadi 19 lewat SQL. Excel sumber masih 3; Mudir harus memperbaikinya agar seed ulang tidak mengembalikan 3.
9. **Pendaftaran (signup) publik di Supabase Auth masih aktif** (`disable_signup = false`). Belum bisa dimatikan dari lingkungan ini karena butuh Dashboard Supabase atau Management API PAT. **Menunggu tindakan Mudir:** Authentication → Providers → Email → matikan "Allow new users to sign up". Setelah nonaktif, akun hanya dibuat Admin.
