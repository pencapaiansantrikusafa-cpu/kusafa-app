import { useState } from "react";
import { supabase } from "../lib/supabase";

/** Halaman login: email + kata sandi lewat Supabase Auth. */
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [pesan, setPesan] = useState<string | null>(null);

  async function masuk(e: React.FormEvent) {
    e.preventDefault();
    setPesan(null);
    setBusy(true);
    const { error } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });
    setBusy(false);
    if (error) {
      // Pesan dari Supabase diterjemahkan ke bahasa sederhana.
      const p = error.message.toLowerCase();
      if (p.includes("invalid login credentials")) {
        setPesan("Email atau kata sandi salah. Silakan periksa lagi.");
      } else if (p.includes("email not confirmed")) {
        setPesan("Akun ini belum dikonfirmasi. Hubungi Admin.");
      } else if (p.includes("too many")) {
        setPesan("Terlalu banyak percobaan. Tunggu sebentar lalu coba lagi.");
      } else {
        setPesan(`Gagal masuk: ${error.message}`);
      }
      return;
    }
    // Jika berhasil, AuthProvider akan memuat profil dan menampilkan aplikasi.
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-kusafa-light px-4 py-10">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-sm ring-1 ring-black/5">
        <h1 className="text-xl font-bold text-kusafa">KUSAFA</h1>
        <p className="mt-1 text-sm text-gray-600">Evaluasi dan Capaian Santri</p>

        <form onSubmit={masuk} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-800">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-kusafa focus:outline-none focus:ring-2 focus:ring-kusafa/30"
              placeholder="nama@contoh.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-800">
              Kata sandi
            </label>
            <div className="mt-1 flex gap-2">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-kusafa focus:outline-none focus:ring-2 focus:ring-kusafa/30"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="shrink-0 rounded-lg border border-gray-300 px-3 text-sm text-gray-700 hover:bg-gray-50"
                aria-pressed={showPassword}
              >
                {showPassword ? "Sembunyikan" : "Lihat"}
              </button>
            </div>
          </div>

          {pesan && (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
              {pesan}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-kusafa px-4 py-2.5 font-medium text-white hover:bg-kusafa/90 disabled:opacity-60"
          >
            {busy ? "Memeriksa..." : "Masuk"}
          </button>
        </form>

        <p className="mt-5 text-xs text-gray-500">
          Lupa kata sandi? Hubungi Admin untuk pengaturan ulang.
        </p>
      </div>
    </main>
  );
}