# STATUS - kondisi nyata proyek KUSAFA

**Sumber kebenaran status.** Diperbarui: **24 November 2026** (pra-T6 langkah [3/5]: perbaikan data, aturan bulan 0, kasus uji santri tanpa halaqah).
Setiap sub-tugas selesai wajib memperbarui berkas ini bersama `docs/HANDOVER.md`.

| | |
|---|---|
| Repo | `https://github.com/pencapaiansantrikusafa-cpu/kusafa-app` (PUBLIK) |
| Branch | `main` (satu-satunya branch; tidak ada branch lain, lokal maupun remote) |
| Commit terakhir sebelum commit ini | `b11b90e` - hardening: migrasi 20261121000007 + skrip dan laporan QA pra-T6 |
| Keadaan Git saat pembaruan | perubahan langkah [3/5] dikomit lalu di-push ke `origin/main` |
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
| **Pra-T6 [1-3/5]** | Audit, hardening fungsi, perbaikan data pra-T6 | **SELESAI untuk langkah [1]-[3]** | `docs/qa/`, `scripts/qa/test_no_halaqah.py`, migrasi `20261121000007` dan `20261121000008`, `scripts/db/fixes/2026-11-24_rabiul_awwal_effective_days.sql` | Hasil di bagian 2a; langkah [4]-[5] menunggu instruksi Mudir |
| **T6** | Tabel dan input Wasilah & Ghayah | **BELUM** | `TabelCapaian.tsx` masih menulis "dikerjakan pada T6" | Rencana kerja di `docs/CATATAN-TAHAPAN.md` |
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
| Uji unit | `npm run test` | **LULUS 6/6** (`tests/putaran.test.mjs`, aturan khatam/pengulangan) |
| Lint | `npm run lint` | **TIDAK ADA** perintahnya di `package.json`. Tidak ada ESLint di repo. Jadi tidak ada hasil lint |
| Audit dependensi | `npm audit --omit=dev` | **2 kerentanan sedang** pada `react-router`/`react-router-dom` 6.0.0-7.17.0 (GHSA-wrjc-x8rr-h8h6, GHSA-337j-9hxr-rhxg). Perbaikan tersedia lewat `npm audit fix --force` (breaking change). Belum dijalankan. |
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

---

## 3. Status Supabase

Project `kusafa`, ref `vcmamapzkhzgikpsvcdo`, region `ap-southeast-1` (Singapore).

### Migrasi
8 berkas migrasi, **kedelapannya tercatat sudah dijalankan** di `supabase_migrations.schema_migrations`:

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

Migrasi berikutnya wajib memakai nomor `20261121000009_...` dan **tidak boleh** mengubah berkas lama.

### RLS (Row Level Security)
- **18 dari 18 tabel** memiliki `relrowsecurity = true`.
- **44 kebijakan** tersebar di 18 tabel (`attendance`, `monthly_notes`, `progress_entries`, `targets` masing-masing 4; sisanya 2).
- Rincian nama kebijakan sengaja tidak disalin ke dokumen ini; dibaca langsung dari `pg_policies` bila perlu.

### Fungsi dan view
- **18 fungsi** di skema `public` (daftar lengkap di `docs/FILE-MAP.md`).
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
| Bundel yang disajikan | `/assets/index-BlqT8R6H.js` dan `/assets/index-JYoo1kxl.css` - **sama persis** dengan hasil `npm run build` lokal dari commit `cdb7c98`, jadi yang tayang adalah kode terbaru |
| Sambungan Supabase | **TERBUKTI** 23 Nov 2026: login sebagai Mudir di `https://kusafa-app.vercel.app` berhasil dan halaman `/capaian/alquran` memuat data dari Supabase, tanpa galat konsol |
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
6. **2 kerentanan npm sedang** (`react-router`/`react-router-dom` 6.0.0-7.17.0; GHSA-wrjc-x8rr-h8h6, GHSA-337j-9hxr-rhxg). `npm audit fix --force` belum dijalankan karena berpotensi breaking change.
7. **Level 6 belum punya pengampu dan jadwal** (4 santri). Ini data, bukan kode; menunggu keputusan Mudir.
8. ~~**Hari Efektif Rabiul Awwal hanya 3 hari** sedangkan bulan lain 15-21.~~ **SELESAI 24 Nov 2026:** dikonfirmasi keliru dan dikoreksi menjadi 19 lewat SQL. Excel sumber masih 3; Mudir harus memperbaikinya agar seed ulang tidak mengembalikan 3.
9. **Pendaftaran (signup) publik di Supabase Auth masih aktif** (`disable_signup = false`). Belum bisa dimatikan dari lingkungan ini karena butuh Dashboard Supabase atau Management API PAT. **Menunggu tindakan Mudir:** Authentication → Providers → Email → matikan "Allow new users to sign up". Setelah nonaktif, akun hanya dibuat Admin.
