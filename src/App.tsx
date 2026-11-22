import { useEffect, useState } from "react";
import { supabase } from "./lib/supabase";

// Halaman awal sementara: hanya memeriksa sambungan ke Supabase.
// Layar sebenarnya dibuat bertahap mengikuti prompts/OPENCODE.md.
export default function App() {
  const [status, setStatus] = useState("Memeriksa sambungan ke Supabase...");

  useEffect(() => {
    supabase
      .from("academic_years")
      .select("id", { head: true, count: "exact" })
      .then(({ error }) => {
        setStatus(error ? `Gagal tersambung: ${error.message}` : "Tersambung ke Supabase.");
      });
  }, []);

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-bold text-kusafa">KUSAFA - Evaluasi dan Capaian Santri</h1>
      <p className="mt-4 text-sm text-gray-700">{status}</p>
    </main>
  );
}
