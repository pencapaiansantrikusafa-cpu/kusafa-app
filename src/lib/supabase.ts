import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  throw new Error("VITE_SUPABASE_URL dan VITE_SUPABASE_ANON_KEY belum diisi. Salin .env.example menjadi .env.local.");
}

// Hanya kunci publik (anon) yang boleh ada di frontend. Kunci service role TIDAK BOLEH dipakai di sini.
export const supabase = createClient(url, anonKey);
