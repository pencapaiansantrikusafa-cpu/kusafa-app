import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { DOMAIN_LABEL, type Domain } from "../lib/roles";
import { supabase } from "../lib/supabase";

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

interface BarisLaporan {
  student_id: string;
  halaqah_id: string;
  subject_id: string;
  month_id: string;
  pos: number | null;
  selisih: number | null;
  hadir: number | null;
  effective_days: number | null;
  target_monthly: number | null;
  below_target: boolean | null;
  attendance_short: boolean | null;
  item_label: string | null;
}

interface Santri {
  id: string;
  full_name: string;
  nis: string;
}

interface Bidang {
  id: string;
  name: string;
}

interface Props {
  domain: Domain;
}

/** Format angka: pecahan hanya bila perlu, kosong bila null. */
function angka(v: number | null | undefined): string {
  if (v === null || v === undefined) return "";
  return Number.isInteger(v) ? String(v) : v.toFixed(1);
}

/**
 * Tabel capaian per halaqah dan bulan.
 * Data SELURUHNYA dari view database (v_monthly_report), tidak dihitung di React.
 */
export default function TabelCapaian({ domain }: Props) {
  const { profile } = useAuth();
  const [halaqahList, setHalaqahList] = useState<Halaqah[]>([]);
  const [bulanList, setBulanList] = useState<Bulan[]>([]);
  const [halaqahId, setHalaqahId] = useState("");
  const [bulanId, setBulanId] = useState("");
  const [baris, setBaris] = useState<BarisLaporan[]>([]);
  const [santri, setSantri] = useState<Santri[]>([]);
  const [bidang, setBidang] = useState<Bidang[]>([]);
  const [memuat, setMemuat] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);

  // Daftar halaqah dan bulan untuk domain ini.
  useEffect(() => {
    let aktif = true;
    async function muat() {
      setMemuat(true);
      setGalat(null);
      const [h, b] = await Promise.all([
        supabase
          .from("halaqahs")
          .select("id, code, name, category")
          .eq("domain", domain)
          .eq("is_active", true)
          .order("code"),
        supabase
          .from("hijri_months")
          .select("id, month_no, name, academic_years!inner(hijri_year)")
          .order("month_no", { ascending: true }),
      ]);
      if (!aktif) return;
      if (h.error || b.error) {
        setGalat(h.error?.message ?? b.error?.message ?? null);
        setMemuat(false);
        return;
      }
      setHalaqahList(h.data ?? []);
      // Bulan diambil bersama tahun ajaran induknya (hijri_year ada di academic_years).
      const semua = ((b.data ?? []) as unknown as Array<{
        id: string;
        month_no: number;
        name: string;
        academic_years: { hijri_year: number } | { hijri_year: number }[];
      }>).map((m) => {
        const ay = Array.isArray(m.academic_years) ? m.academic_years[0] : m.academic_years;
        return {
          id: m.id,
          month_no: m.month_no,
          name: m.name,
          hijri_year: ay?.hijri_year ?? 0,
        } satisfies Bulan;
      });
      semua.sort((a, b) => a.hijri_year - b.hijri_year || a.month_no - b.month_no);
      setBulanList(semua);
      setHalaqahId((prev) => prev || h.data?.[0]?.id || "");
      // Default: bulan terakhir yang punya capaian. Dihitung dari daftar kecil
      // (bukan query ke view yang bisa kehabisan waktu).
      const daftarId = semua.map((x) => x.id);
      const { data: adaData } = await supabase
        .from("progress_entries")
        .select("month_id")
        .in("month_id", daftarId)
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
      const [r, m, s] = await Promise.all([
        supabase
          .from("v_monthly_report")
          .select(
            "student_id, halaqah_id, subject_id, month_id, pos, selisih, hadir, effective_days, target_monthly, below_target, attendance_short, item_label",
          )
          .eq("halaqah_id", halaqahId)
          .eq("month_id", bulanId)
          .eq("domain", domain),
        supabase.from("halaqah_members").select("student_id").eq("halaqah_id", halaqahId),
        supabase.from("subjects").select("id, name").eq("domain", domain).order("sort_order"),
      ]);
      if (!aktif) return;
      if (r.error || m.error || s.error) {
        setGalat(r.error?.message ?? m.error?.message ?? s.error?.message ?? null);
        setMemuat(false);
        return;
      }
      const anggota = (m.data ?? []).map((x) => x.student_id);
      const { data: st, error: e2 } = anggota.length
        ? await supabase.from("students").select("id, full_name, nis").in("id", anggota).order("full_name")
        : { data: [], error: null };
      if (!aktif) return;
      if (e2) {
        setGalat(e2.message);
        setMemuat(false);
        return;
      }
      setBaris((r.data ?? []) as BarisLaporan[]);
      setSantri((st ?? []) as Santri[]);
      setBidang((s.data ?? []) as Bidang[]);
      setMemuat(false);
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, [halaqahId, bulanId, domain]);

  // Susun data per santri per bidang (tanpa menghitung apa pun: hanya menyusun).
  const peta = useMemo(() => {
    const p = new Map<string, BarisLaporan>();
    for (const b of baris) p.set(`${b.student_id}|${b.subject_id}`, b);
    return p;
  }, [baris]);

  const ringkas = useMemo(() => {
    let kosong = 0;
    let bawahTarget = 0;
    let hadirKurang = 0;
    for (const s of santri) {
      for (const b of bidang) {
        const r = peta.get(`${s.id}|${b.id}`);
        if (!r || r.pos === null || r.target_monthly === null) kosong++;
        if (r?.below_target) bawahTarget++;
        if (r?.attendance_short) hadirKurang++;
      }
    }
    return { kosong, bawahTarget, hadirKurang };
  }, [santri, bidang, peta]);

  const judulBidang = bidang.map((b) => b.name);

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor="halaqah" className="block text-sm font-medium text-gray-800">
              Halaqah
            </label>
            <select
              id="halaqah"
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
            <label htmlFor="bulan" className="block text-sm font-medium text-gray-800">
              Bulan
            </label>
            <select
              id="bulan"
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
          <h2 className="text-base font-bold text-gray-900">
            Capaian {DOMAIN_LABEL[domain]}
          </h2>
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
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-sm">
              <thead>
                <tr className="bg-kusafa-light text-left text-xs uppercase tracking-wide text-kusafa">
                  <th scope="col" className="sticky left-0 z-10 bg-kusafa-light px-3 py-2">
                    Santri
                  </th>
                  <th scope="col" className="px-3 py-2 whitespace-nowrap">
                    Hadir/HE
                  </th>
                  {judulBidang.map((n) => (
                    <th key={n} scope="col" colSpan={3} className="border-l border-white/60 px-3 py-2">
                      {n} <span className="font-normal normal-case">(Lalu · Kini · Selisih)</span>
                    </th>
                  ))}
                  <th scope="col" className="border-l border-white/60 px-3 py-2">
                    Target bulanan
                  </th>
                </tr>
              </thead>
              <tbody>
                {santri.map((s) => {
                  const barisSantri = bidang.map((b) => peta.get(`${s.id}|${b.id}`));
                  const hadir = barisSantri.find((r) => r?.hadir !== null && r?.hadir !== undefined);
                  return (
                    <tr key={s.id} className="border-t border-black/5 align-top">
                      <th
                        scope="row"
                        className="sticky left-0 z-10 bg-white px-3 py-2 text-left font-medium text-gray-900"
                      >
                        {s.full_name}
                      </th>
                      <td className="whitespace-nowrap px-3 py-2">
                        {hadir && hadir.hadir !== null ? (
                          <span
                            className={
                              hadir.attendance_short
                                ? "rounded bg-amber-100 px-1.5 py-0.5 font-semibold text-amber-900"
                                : "text-gray-800"
                            }
                          >
                            {hadir.hadir}/{angka(hadir.effective_days)}
                            {hadir.attendance_short && (
                              <span className="ml-1 text-xs font-normal">⚠ kurang</span>
                            )}
                          </span>
                        ) : (
                          <span className="text-gray-400" title="Belum diinput">
                            –
                          </span>
                        )}
                      </td>
                      {barisSantri.map((r, i) => {
                        const tidakAdaData = !r || r.pos === null;
                        return (
                          <td
                            key={bidang[i].id}
                            className="border-l border-black/5 px-3 py-2"
                          >
                            {tidakAdaData ? (
                              <span className="text-xs text-gray-500">belum diisi</span>
                            ) : (
                              <div className="flex items-baseline gap-2 whitespace-nowrap">
                                <span className="font-medium text-gray-900">{r.item_label ?? "–"}</span>
                                <span
                                  className={
                                    r.selisih !== null && r.selisih < 0
                                      ? "font-semibold text-red-700"
                                      : "font-semibold text-kusafa"
                                  }
                                >
                                  {r.selisih === null ? "–" : (r.selisih > 0 ? "+" : "") + angka(r.selisih)}
                                </span>
                                {r.below_target && (
                                  <span className="rounded bg-pink-100 px-1.5 py-0.5 text-xs font-medium text-pink-900">
                                    di bawah target
                                  </span>
                                )}
                              </div>
                            )}
                          </td>
                        );
                      })}
                      <td className="border-l border-black/5 px-3 py-2 whitespace-nowrap">
                        {barisSantri
                          .map((r) => r?.target_monthly)
                          .filter((v) => v !== null && v !== undefined)
                          .map((v, i) => (
                            <div key={i} className="text-gray-800">
                              {angka(v as number)}
                            </div>
                          ))}
                        {barisSantri.every((r) => r?.target_monthly === null || r?.target_monthly === undefined) && (
                          <span className="text-xs text-gray-500">belum ada</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="rounded-lg bg-white px-4 py-3 text-xs text-gray-700 ring-1 ring-black/5">
        <p>
          <span className="mr-1 inline-block rounded bg-pink-100 px-1.5 py-0.5 font-medium text-pink-900">
            di bawah target
          </span>
          selisih kurang dari target bulanan. <span className="mx-1">·</span>
          <span className="mr-1 inline-block rounded bg-amber-100 px-1.5 py-0.5 font-medium text-amber-900">
            ⚠ kurang
          </span>
          Hadir kurang dari Hari Efektif.
        </p>
        <p className="mt-1">
          Sel bertanda <em>belum diisi</em> atau <em>–</em> kosong, bukan nol. Selisih negatif berarti santri mengulang.
        </p>
        {profile && (
          <p className="mt-1 text-gray-500">
            Anda masuk sebagai {profile.full_name}. Angka diambil langsung dari laporan database.
          </p>
        )}
      </div>
    </div>
  );
}