# Prompt setup otomatis KUSAFA untuk OpenCode Desktop

## Yang kamu siapkan sekali saja (5 menit)
1. Buat folder kosong di komputermu, misalnya `kusafa`.
2. Masukkan ke folder itu: `kusafa-app.zip` dan lima file Excel versi terbaru:
   `1-User and Role.xlsx`, `2-Dropdown Input Kurikulum KUSAFA.xlsx`, `3-Al Quran (halaqah dan pencapaian).xlsx` (salinan yang sudah 0,5),
   `4-Ilmu Wasilah.xlsx`, `5-Ilmu Ghayah.xlsx`.
3. Punya akun (gratis): GitHub, Supabase, Vercel. Kamu tidak perlu membuka dashboard mereka; OpenCode yang mengerjakan.
4. Buka OpenCode Desktop, buka folder `kusafa` sebagai project, mulai sesi baru, lalu tempel seluruh prompt di bawah garis.
5. Saat OpenCode meminta izin menjalankan perintah, setujui (setelah membaca perintahnya).
6. Tiga kali nanti kamu diminta login ke GitHub, Supabase, dan Vercel. Itu harus kamu jalankan sendiri di jendela terminal biasa
   (Terminal di macOS, PowerShell di Windows, atau panel terminal OpenCode jika ada), karena login butuh persetujuanmu di browser.
   OpenCode akan menuliskan perintah persisnya; kamu tinggal salin, jalankan, setujui di browser, lalu kembali dan ketik "lanjut".

---

PERAN DAN TUJUAN
Kamu adalah asisten teknis untuk Mudir KUSAFA (bukan programmer). Tugasmu: menyiapkan proyek "KUSAFA - Evaluasi dan Capaian Santri" dari nol sampai
berjalan di internet, dari dalam OpenCode ini saja, tanpa aku membuka GitHub, Supabase, atau Vercel secara manual. Jelaskan setiap langkah dengan bahasa
Indonesia sederhana dan singkat: apa yang baru terjadi dan apa yang berikutnya.

ATURAN KERAS
1. Tanyakan dulu sistem operasi dan shell yang kupakai (Windows PowerShell, macOS, atau Linux). Pakai perintah yang sesuai. Jangan memakai grep, unzip, source, atau export jika aku di Windows PowerShell; pakai Python atau Node untuk pekerjaan berkas (mengekstrak zip, memeriksa isi). Di Windows, jika `python` tidak dikenali, coba `py`.
2. Jangan menjalankan perintah interaktif (login, pertanyaan berganda) sendiri. Untuk login, tuliskan perintah persisnya, suruh aku menjalankannya di terminal biasa, dan tunggu aku mengetik "lanjut".
3. Minta persetujuanku sebelum: memasang perangkat lunak, membuat sumber daya online (repo GitHub, project Supabase, project Vercel), dan menjalankan seed (menghapus isi tabel; ini hanya data uji).
4. Jangan menebak. Jika ada yang tidak jelas, tidak sinkron, atau sebuah perintah gagal, berhenti, jelaskan galatnya apa adanya, dan tanyakan. Jika sintaks perintah CLI berbeda dari yang tertulis di sini, cek `--help`; jangan mengarang.
5. Rahasia (service role key, password database, token): jangan dicetak ke layar atau ke chat, jangan masuk riwayat git, jangan ditulis di file selain `.env.local`. Tulis `.env.local` lewat kode (bukan `echo` yang tercetak). Jika aku perlu mengetik nilainya, minta aku melakukannya langsung di berkas `.env.local`.
6. Repo GitHub dibuat PUBLIK selama pengembangan agar Mudir bisa membagikan tautannya untuk ditinjau, sehingga hanya boleh berisi kode, dokumen, dan data dummy. Data santri (file .xlsx, `supabase/seed/*.sql`, `scripts/seed/output/`, `.env*`) tidak boleh ikut ter-commit. Sebelum setiap push jalankan `python scripts/check_repo_safety.py` (harus lolos). Jika gagal, jangan push; jelaskan penyebabnya kepadaku. Sebelum data asli santri dimuat, ingatkan aku untuk menjadikan repo PRIVAT.
7. Tulis nama role selengkapnya: Masul Al Quran, Masul Wasilah, Masul Ghayah (jangan hanya "masul").
8. Setelah tiap tahap, tulis ringkasan 3-5 baris dan tunggu aku mengetik "lanjut" sebelum tahap berikutnya.

TAHAP A - Pemeriksaan alat
Periksa versi: node (butuh 20+), npm, python (butuh 3.10+), git, gh (GitHub CLI). Supabase CLI dan Vercel CLI dijalankan lewat `npx supabase` dan `npx vercel`, tanpa pemasangan global. Tidak perlu psql.
Laporkan yang kurang beserta cara memasangnya untuk sistem operasiku, minta izin, lalu pasang.

TAHAP B - Siapkan proyek
1. Ekstrak `kusafa-app.zip` ke folder `kusafa-app` (misalnya `python -m zipfile -e kusafa-app.zip kusafa-app`; jika hasilnya berlapis satu folder lagi, rapikan). Pindahkan lima file Excel ke `kusafa-app/data/source/` dan pastikan ada tepat 5 file berawalan 1-, 2-, 3-, 4-, 5-.
2. Masuk ke `kusafa-app`. Baca `AGENTS.md`, `docs/SPEC.md`, `docs/DATA-NOTES.md`, `README.md`. Ringkas proyek dalam 8 baris.
3. `npm install`, `npm run typecheck`, `npm run build`. Laporkan hasilnya. Jika gagal, perbaiki galat teknis yang jelas (misalnya versi paket) tanpa mengubah aturan bisnis di `docs/SPEC.md`, dan sebutkan perubahannya.

TAHAP C - Git dan GitHub
1. `git init -b main`. Aktifkan hook: `git config core.hooksPath .githooks`. Jalankan `python scripts/check_repo_safety.py` (harus lolos) dan periksa `git status` (tidak boleh ada .xlsx atau .env). Commit awal.
2. Periksa `gh auth status`. Jika belum masuk, tuliskan `gh auth login` untukku jalankan di terminal biasa, dan tunggu.
3. Tanyakan konfirmasi eksplisit: "Repo akan PUBLIK (siapa saja bisa membaca kode dan dokumen, tidak ada data santri). Lanjut?" Hanya jika aku menjawab ya: `gh repo create kusafa-app --public --source=. --remote=origin --push`. Laporkan alamatnya agar bisa kuberikan kepada Claude untuk dibaca.

TAHAP D - Supabase (database dan login)
1. Suruh aku menjalankan `npx supabase login` di terminal biasa, lalu tunggu. Setelah itu tampilkan organisasi yang ada (`npx supabase orgs list`) dan tanyakan mana yang dipakai.
2. Dengan izinku, buat project Supabase bernama `kusafa`, region Singapore (`ap-southeast-1`), dengan password database acak yang kuat. Simpan password itu hanya di `.env.local`. Jika pembuatan lewat CLI gagal, jelaskan alasannya dan tanyakan apakah aku mau membuatnya sendiri di dashboard.
3. Ambil URL project, anon key, dan service role key (`npx supabase projects api-keys --project-ref <ref>`), lalu isi `.env.local` dengan format `.env.example` (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL). Jangan cetak nilai rahasia. Pastikan `.env.local` ada di `.gitignore`.
4. `npx supabase init`, `npx supabase link --project-ref <ref>`, lalu `npx supabase db push` untuk menjalankan 6 migrasi di `supabase/migrations/`. Jika ada galat SQL, tampilkan pesan lengkapnya. Perbaiki hanya jika penyebabnya jelas dan tidak mengubah aturan bisnis; jelaskan perubahannya kepadaku. Jangan diam-diam mengubah tabel.
5. Verifikasi: `pip install -r scripts/seed/requirements.txt`, lalu `python scripts/db/run_sql.py --query "select tablename, rowsecurity from pg_tables where schemaname = 'public' order by 1"`. Semua tabel harus `rowsecurity = true`.

TAHAP E - Seed data uji
1. `python scripts/seed/build_seed.py`. Baca `scripts/seed/output/seed-report.md`. Harapan: status BERHASIL, 0 galat, sekitar 25 peringatan (semuanya Tilawah mundur atau khatam; itu wajar menurut Mudir), dan angka: 9 bidang, 158 buku, 10954 item, 109 santri, 38 halaqah, 327 target, 2036 capaian, 599 presensi. Jika berbeda atau ada galat, berhenti dan tanyakan.
2. Dengan izinku (seed menghapus isi tabel, hanya data uji), berurutan:
   - `python scripts/db/run_sql.py supabase/seed/01_curriculum.sql`
   - `python scripts/seed/create_auth_users.py` (membaca `.env.local` sendiri)
   - `python scripts/db/run_sql.py supabase/seed/02_school_data.sql`
   Jika koneksi database gagal (misalnya jaringan tidak mendukung alamat langsung), cari alamat koneksi "pooler" Supabase yang cocok dan tanyakan padaku sebelum mengubah `DATABASE_URL`.
3. Verifikasi dengan `--query`: jumlah baris tiap tabel utama sama dengan angka di atas, dan tampilkan 5 baris dari `v_monthly_report` (selisih, hadir, target_monthly).
4. Jangan commit apa pun dari `supabase/seed/` atau `scripts/seed/output/`. Beri tahu aku lokasi `users.csv` (kata sandi akun dummy) tanpa mencetak isinya.

TAHAP F - Uji lokal
`npm run dev`. Pastikan halaman awal menulis "Tersambung ke Supabase." Laporkan alamat lokalnya.

TAHAP G - Vercel
1. Suruh aku menjalankan `npx vercel login` di terminal biasa, lalu tunggu. Lalu `npx vercel link` (buat project baru `kusafa-app`).
2. Isi environment variable di Vercel HANYA `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY` (production dan preview), nilainya diambil dari `.env.local` tanpa dicetak. Kunci service role dan DATABASE_URL tidak boleh ke Vercel.
3. Hubungkan repo GitHub ke project Vercel (`npx vercel git connect`) agar deploy otomatis setiap push. Deploy pertama: `npx vercel --prod`. Laporkan alamat situsnya.
4. Daftarkan alamat situs itu di Supabase sebagai Site URL dan Redirect URL (lewat `supabase/config.toml` dan `npx supabase config push` jika bisa). Jika tidak bisa lewat CLI, beri aku satu instruksi singkat untuk dashboard.
5. Buka situs live dan pastikan "Tersambung ke Supabase." tampil.

TAHAP H - Laporan akhir lalu lanjut membangun
Ingatkan aku: repo masih publik, jadikan privat sebelum data asli dimuat. Tulis tabel ringkas: apa yang sudah berjalan, alamat repo GitHub, alamat situs Vercel, lokasi rahasia (hanya `.env.local` dan `users.csv`, tidak di git), dan apa yang masih perlu kulakukan.
Setelah aku setuju, kerjakan tugas T2 sampai T10 di `prompts/OPENCODE.md` satu per satu. Setiap tugas: kerjakan, jalankan `npm run typecheck` dan `npm run build`, commit dengan pesan jelas, push, tunggu deploy Vercel, ringkas apa yang diubah dan apa yang perlu kucek, lalu minta "lanjut".
