import { useEffect, useState } from "react";
import { DOMAIN_LABEL, type Domain } from "../lib/roles";
import { supabase } from "../lib/supabase";
import TabelAlQuran from "./TabelAlQuran";
import { angka, type BarisLaporan } from "../lib/laporan";

interface Halaqah {
  id: string;
  code: string;
  name: string;
  category: string | null;
}

interface Bulan {
  id: string;
  month_no: number;
  name: string;
  hijri_year: number;
}

interface Santri {
  id: string;
  full_name: string;
}

interface Bidang {
  id: string;
  name: string;
}

/**
 * Tabel capaian per halaqah dan bulan. Seluruh angka berasal dari view
 * `v_monthly_report` di database; React hanya menyusun tampilan.
 */
export default function TabelCapaian({ domain }: { domain: Domain }) {
  const [halaqahList, setHalaqahList] = useState<Halaqah[]>([]);
  const [bulanList, setBulanList] = useState<Bulan[]>([]);
  const [halaqahId, setHalaqahId] = useState("");
  const [bulanId, setBulanId] = useState("");
  const [baris, setBaris] = useState<BarisLaporan[]>([]);
  const [santri, setSantri] = useState<Santri[]>([]);
  const [bidang, setBidang] = useState<Bidang[]>([]);
  const [memuat, setMemuat] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);

  // Daftar halaqah, bulan, dan bidang.
  useEffect(() => {
    let aktif = true;
    async function muat() {
      setMemuat(true);
      setGalat(null);
      const [h, b, s] = await Promise.all([
        supabase
          .from("halaqahs")
          .select("id, code, name, category")
          .eq("domain", domain)
          .eq("is_active", true)
          .order("code"),
        supabase
          .from("hijri_months")
          .select("id, month_no, name, academic_years!inner(hijri_year)")
          .order("month_no"),
        supabase.from("subjects").select("id, name").eq("domain", domain).order("sort_order"),
      ]);
      if (!aktif) return;
      if (h.error || b.error || s.error) {
        setGalat(h.error?.message ?? b.error?.message ?? s.error?.message ?? null);
        setMemuat(false);
        return;
      }
      setHalaqahList(h.data ?? []);
      setBidang((s.data ?? []) as Bidang[]);
      const semua = ((b.data ?? []) as unknown as Array<{
        id: string;
        month_no: number;
        name: string;
        academic_years: { hijri_year: number } | { hijri_year: number }[];
      }>).map((m) => {
        const ay = Array.isArray(m.academic_years) ? m.academic_years[0] : m.academic_years;
        return { id: m.id, month_no: m.month_no, name: m.name, hijri_year: ay?.hijri_year ?? 0 };
      });
      semua.sort((a, c) => a.hijri_year - c.hijri_year || a.month_no - c.month_no);
      setBulanList(semua);
      setHalaqahId((prev) => prev || h.data?.[0]?.id || "");
      // Bulan default: bulan terakhir yang punya capaian (dihitung dari daftar kecil).
      const { data: adaData } = await supabase
        .from("progress_entries")
        .select("month_id")
        .in("month_id", semua.map((x) => x.id))
        .limit(2000);
      if (!aktif) return;
      const punyaData = new Set((adaData ?? []).map((x) => x.month_id));
      const terakhir = [...semua].reverse().find((x) => punyaData.has(x.id));
      setBulanId((prev) => prev || terakhir?.id || semua[semua.length - 1]?.id || "");
      setMemuat(false);
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, [domain]);

  // Isi tabel ketika pilihan berubah.
  useEffect(() => {
    let aktif = true;
    if (!halaqahId || !bulanId) return;
    setMemuat(true);
    setGalat(null);
    async function muat() {
      const [r, m] = await Promise.all([
        supabase
          .from("v_monthly_report")
          .select(
            "halaqah_id, student_id, subject_id, month_id, pos, selisih, hadir, effective_days, target_monthly, below_target, attendance_short, item_label, prev_item_label",
          )
          .eq("halaqah_id", halaqahId)
          .eq("month_id", bulanId)
          .eq("domain", domain),
        supabase.from("halaqah_members").select("student_id").eq("halaqah_id", halaqahId),
      ]);
      if (!aktif) return;
      if (r.error || m.error) {
        setGalat(r.error?.message ?? m.error?.message ?? null);
        setMemuat(false);
        return;
      }
      const anggota = (m.data ?? []).map((x) => x.student_id);
      const { data: st, error: e2 } = anggota.length
        ? await supabase.from("students").select("id, full_name").in("id", anggota).order("full_name")
        : { data: [], error: null };
      if (!aktif) return;
      if (e2) {
        setGalat(e2.message);
        setMemuat(false);
        return;
      }
      setBaris((r.data ?? []) as unknown as BarisLaporan[]);
      setSantri((st ?? []) as Santri[]);
      setMemuat(false);
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, [halaqahId, bulanId, domain]);

  const ringkas = { kosong: 0, bawahTarget: 0, hadirKurang: 0 };
  for (const b of baris) {
    if (b.pos === null || b.target_monthly === null) ringkas.kosong++;
    if (b.below_target) ringkas.bawahTarget++;
    if (b.attendance_short) ringkas.hadirKurang++;
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor={`halaqah-${domain}`} className="block text-sm font-medium text-gray-800">
              {domain === "wasilah" ? "Level" : "Halaqah"}
            </label>
            <select
              id={`halaqah-${domain}`}
              value={halaqahId}
              onChange={(e) => setHalaqahId(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base"
            >
              {halaqahList.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.code}
                  {h.category ? ` — ${h.category}` : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor={`bulan-${domain}`} className="block text-sm font-medium text-gray-800">
              Bulan
            </label>
            <select
              id={`bulan-${domain}`}
              value={bulanId}
              onChange={(e) => setBulanId(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base"
            >
              {bulanList.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} {b.hijri_year} H
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Bulan pembanding otomatis bulan sebelumnya. Tidak perlu dipilih.
            </p>
          </div>
        </div>
      </div>

      {galat && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          Gagal memuat data: {galat}
        </p>
      )}

      <div className="rounded-xl bg-white ring-1 ring-black/5">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/5 px-4 py-3">
          <h2 className="text-base font-bold text-gray-900">Capaian {DOMAIN_LABEL[domain]}</h2>
          <p className="text-xs text-gray-600">
            {santri.length} santri · {memuat ? "memuat..." : `${ringkas.kosong} sel kosong`}
          </p>
        </div>

        {memuat && santri.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">Memuat data...</p>
        ) : santri.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">
            Belum ada anggota di halaqah ini.
          </p>
        ) : domain === "alquran" ? (
          <TabelAlQuran santri={santri} baris={baris} bidang={bidang} memuat={memuat} />
        ) : (
          <div className="px-4 py-8 text-center text-sm text-gray-700">
            <p>
              Tabel Wasilah/Ghayah (per mata pelajaran: Capaian Bulan Lalu, Bulan Ini, Selisih,
              lalu daftar anggota) dikerjakan pada <strong>T6</strong>.
            </p>
          </div>
        )}
      </div>

      <div className="rounded-lg bg-white px-4 py-3 text-xs text-gray-700 ring-1 ring-black/5">
        <p>
          <span className="mr-1 inline-block rounded bg-pink-100 px-1.5 py-0.5 font-medium text-pink-900">
            di bawah target
          </span>
          selisih kurang dari target bulanan.
          <span className="mx-1">·</span>
          <span className="mr-1 inline-block rounded bg-amber-100 px-1.5 py-0.5 font-medium text-amber-900">
            ⚠ kurang
          </span>
          Hadir kurang dari Hari Efektif.
        </p>
        <p className="mt-1">
          Kolom per bidang berurutan <strong>Lalu · Kini · Selisih</strong>. Sel kosong tertulis
          <em> belum diisi</em>, bukan nol. Selisih negatif berarti santri mengulang.
        </p>
      </div>
    </div>
  );
}