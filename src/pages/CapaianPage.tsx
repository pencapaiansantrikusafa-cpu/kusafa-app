import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { navItemsFor } from "../lib/roles";
import { supabase } from "../lib/supabase";
import PlaceholderPage from "./PlaceholderPage";

interface Ringkasan {
  halaqah: number;
  santri: number;
  tahunAjaran: string | null;
  galat: string | null;
}

/** Halaman Capaian sementara: ringkasan isi database (T3 akan menggantinya). */
export default function CapaianPage() {
  const { profile } = useAuth();
  const [data, setData] = useState<Ringkasan | null>(null);

  useEffect(() => {
    let aktif = true;
    async function muat() {
      const [h, s, t] = await Promise.all([
        supabase.from("halaqahs").select("id", { count: "exact", head: true }).eq("is_active", true),
        supabase.from("students").select("id", { count: "exact", head: true }).eq("is_active", true),
        supabase
          .from("academic_years")
          .select("name, hijri_year")
          .eq("is_active", true)
          .maybeSingle(),
      ]);
      if (!aktif) return;
      const galat = h.error?.message ?? s.error?.message ?? t.error?.message ?? null;
      setData({
        halaqah: h.count ?? 0,
        santri: s.count ?? 0,
        tahunAjaran: t.data ? `${t.data.name} (${t.data.hijri_year} H)` : null,
        galat,
      });
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, []);

  if (!profile) return null;
  const item = navItemsFor(profile.role).find((i) => i.key === "capaian")!;

  return (
    <PlaceholderPage item={item} roleLabel={profile.full_name}>
      <dl className="mt-5 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
        <div className="rounded-lg bg-kusafa-light px-3 py-2">
          <dt className="text-xs text-gray-600">Halaqah aktif</dt>
          <dd className="text-lg font-bold text-kusafa">{data ? data.halaqah : "..."}</dd>
        </div>
        <div className="rounded-lg bg-kusafa-light px-3 py-2">
          <dt className="text-xs text-gray-600">Santri aktif</dt>
          <dd className="text-lg font-bold text-kusafa">{data ? data.santri : "..."}</dd>
        </div>
        <div className="rounded-lg bg-kusafa-light px-3 py-2">
          <dt className="text-xs text-gray-600">Tahun ajaran</dt>
          <dd className="text-sm font-semibold text-kusafa">
            {data ? (data.tahunAjaran ?? "belum ada") : "..."}
          </dd>
        </div>
      </dl>
      {data?.galat && (
        <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          Gagal memuat ringkasan: {data.galat}
        </p>
      )}
      <p className="mt-3 text-xs text-gray-500">
        Angka di atas adalah jumlah data uji (data asli belum dimuat).
      </p>
    </PlaceholderPage>
  );
}