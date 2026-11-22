import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { angka, type BarisLaporan } from "../lib/laporan";
import { DOMAIN_LABEL, type Domain } from "../lib/roles";
import GrafikGaris from "../components/GrafikGaris";
import GrafikGabungan, { type Seri } from "../components/GrafikGabungan";

/** Warna garis tiap bidang (juga dipakai di grafik gabungan). */
const WARNA = ["#0f5b45", "#1d4ed8", "#b45309", "#7c3aed", "#0891b2"];

interface Santri {
  id: string;
  nis: string;
  full_name: string;
  gender: "L" | "P";
}

interface Bulan {
  id: string;
  month_no: number;
  name: string;
  semester: number | null;
  hijri_year: number;
}

interface Bidang {
  id: string;
  name: string;
  domain: Domain;
}

interface BarisRiwayat extends BarisLaporan {
  subject_id: string;
  month_id: string;
}

type Rentang = "s1" | "s2" | "tahun";

const DOMAINS: Domain[] = ["alquran", "wasilah", "ghayah"];

function adalahDomain(v: string | undefined): v is Domain {
  return !!v && (DOMAINS as string[]).includes(v);
}

/** Halaman capaian satu santri: grafik selisih per bulan dan riwayat. */
export default function SantriPage() {
  const { id } = useParams();
  const [cari, setCari] = useSearchParams();
  const domainParam = cari.get("domain") ?? "alquran";
  const domain: Domain = adalahDomain(domainParam) ? domainParam : "alquran";

  const [santri, setSantri] = useState<Santri | null>(null);
  const [bulan, setBulan] = useState<Bulan[]>([]);
  const [bidang, setBidang] = useState<Bidang[]>([]);
  const [riwayat, setRiwayat] = useState<BarisRiwayat[]>([]);
  const [rentang, setRentang] = useState<Rentang>("tahun");
  const [modeGrafik, setModeGrafik] = useState<"gabung" | "pisah">("gabung");
  const [memuat, setMemuat] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);

  useEffect(() => {
    let aktif = true;
    if (!id) return;
    async function muat() {
      setMemuat(true);
      setGalat(null);
      const [s, b, sub, r] = await Promise.all([
        supabase.from("students").select("id, nis, full_name, gender").eq("id", id).maybeSingle(),
        supabase
          .from("hijri_months")
          .select("id, month_no, name, semester, academic_years!inner(hijri_year)")
          .order("month_no"),
        supabase.from("subjects").select("id, name, domain").order("sort_order"),
        supabase
          .from("v_monthly_report")
          .select(
            "student_id, subject_id, month_id, pos, selisih, hadir, effective_days, target_monthly, below_target, attendance_short, item_label, prev_item_label",
          )
          .eq("student_id", id)
          .limit(2000),
      ]);
      if (!aktif) return;
      if (s.error || b.error || sub.error || r.error) {
        setGalat(
          s.error?.message ?? b.error?.message ?? sub.error?.message ?? r.error?.message ?? null,
        );
        setMemuat(false);
        return;
      }
      setSantri((s.data ?? null) as Santri | null);
      const daftarBulan = ((b.data ?? []) as unknown as Array<{
        id: string;
        month_no: number;
        name: string;
        semester: number | null;
        academic_years: { hijri_year: number } | { hijri_year: number }[];
      }>).map((m) => {
        const ay = Array.isArray(m.academic_years) ? m.academic_years[0] : m.academic_years;
        return {
          id: m.id,
          month_no: m.month_no,
          name: m.name,
          semester: m.semester,
          hijri_year: ay?.hijri_year ?? 0,
        };
      });
      daftarBulan.sort((a, c) => a.hijri_year - c.hijri_year || a.month_no - c.month_no);
      setBulan(daftarBulan);
      setBidang((sub.data ?? []) as Bidang[]);
      setRiwayat((r.data ?? []) as unknown as BarisRiwayat[]);
      setMemuat(false);
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, [id]);

  // Bulan dalam rentang pilihan.
  const bulanRentang = useMemo(() => {
    if (rentang === "tahun") return bulan;
    return bulan.filter((b) => b.semester === (rentang === "s1" ? 1 : 2));
  }, [bulan, rentang]);

  const bidangDomain = useMemo(() => bidang.filter((b) => b.domain === domain), [bidang, domain]);

  /**
   * Garis posisi kumulatif per bidang (bukan selisih bulanan), supaya tidak
   * pernah turun hanya karena naiknya kecil. Semua angka berasal dari view.
   */
  function titikPosisi(subjectId: string) {
    return bulanRentang.map((b) => {
      const r = riwayat.find((x) => x.subject_id === subjectId && x.month_id === b.id);
      return { label: b.name, nilai: r?.pos === null || r?.pos === undefined ? null : Number(r.pos) };
    });
  }

  /** Kehadiran (Hadir) diambil sekali per bulan dari baris mana pun di domain ini. */
  function titikHadir() {
    return bulanRentang.map((b) => {
      const r = riwayat.find(
        (x) => x.month_id === b.id && bidangDomain.some((bd) => bd.id === x.subject_id),
      );
      return { label: b.name, nilai: r?.hadir === null || r?.hadir === undefined ? null : Number(r.hadir) };
    });
  }

  const seriPosisi: Seri[] = bidangDomain.map((b, i) => ({
    nama: b.name,
    warna: WARNA[i % WARNA.length],
    titik: titikPosisi(b.id),
  }));

  // Kehadiran ikut dalam grafik gabungan (garis putus-putus, satuan hari).
  const seriGabungan: Seri[] = [
    ...seriPosisi,
    { nama: "Kehadiran (hari)", warna: "#b45309", putus: true, titik: titikHadir() },
  ];

  // Tampilkan tautan kembali bila pengguna datang dari halaman capaian.
  const asal = cari.get("dari");

  const gantiDomain = (d: Domain) => {
    const next = new URLSearchParams(cari);
    next.set("domain", d);
    setCari(next, { replace: true });
  };

  if (!santri && memuat) {
    return <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">Memuat data santri...</p>;
  }
  if (!santri) {
    return (
      <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">
        Santri tidak ditemukan atau Anda tidak berhak melihatnya.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <Link
          to={asal === "capaian" ? `/capaian/${domain}` : "/"}
          className="mb-2 inline-block text-xs font-medium text-kusafa underline underline-offset-2"
        >
          ← {asal === "capaian" ? "Kembali ke tabel capaian" : "Kembali"}
        </Link>
        <h1 className="text-xl font-bold text-gray-900">{santri.full_name}</h1>
        <p className="mt-0.5 text-xs text-gray-600">
          NIS {santri.nis} · {santri.gender === "L" ? "Putra" : "Putri"}
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          {DOMAINS.map((d) => (
            <button
              key={d}
              onClick={() => gantiDomain(d)}
              aria-pressed={domain === d}
              className={
                "rounded-lg px-3 py-1.5 text-sm font-medium " +
                (domain === d
                  ? "bg-kusafa text-white"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-50")
              }
            >
              {DOMAIN_LABEL[d]}
            </button>
          ))}
        </div>

        <fieldset className="mt-3">
          <legend className="text-sm font-medium text-gray-800">Rentang</legend>
          <div className="mt-1 flex flex-wrap gap-2">
            {(
              [
                ["s1", "Semester 1"],
                ["s2", "Semester 2"],
                ["tahun", "Satu tahun ajaran"],
              ] as [Rentang, string][]
            ).map(([nilai, label]) => (
              <button
                key={nilai}
                onClick={() => setRentang(nilai)}
                aria-pressed={rentang === nilai}
                className={
                  "rounded-lg px-3 py-1.5 text-sm " +
                  (rentang === nilai
                    ? "bg-kusafa-light font-semibold text-kusafa"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50")
                }
              >
                {label}
              </button>
            ))}
          </div>
        </fieldset>
      </div>

      {galat && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          Gagal memuat: {galat}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 rounded-xl bg-white px-3 py-2 ring-1 ring-black/5">
        <span className="text-sm font-medium text-gray-800">Tampilan grafik</span>
        {(
          [
            ["gabung", "Satu kotak (gabungan)"],
            ["pisah", "Terpisah per bidang"],
          ] as ["gabung" | "pisah", string][]
        ).map(([nilai, label]) => (
          <button
            key={nilai}
            onClick={() => setModeGrafik(nilai)}
            aria-pressed={modeGrafik === nilai}
            className={
              "rounded-lg px-3 py-1.5 text-sm " +
              (modeGrafik === nilai
                ? "bg-kusafa text-white"
                : "border border-gray-300 text-gray-700 hover:bg-gray-50")
            }
          >
            {label}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-500">
          Garis = posisi kumulatif (selalu naik selama santri maju)
        </span>
      </div>

      {modeGrafik === "gabung" ? (
        <GrafikGabungan
          judul="Posisi capaian kumulatif & kehadiran"
          seri={seriGabungan}
          satuan={`${bulanRentang.length} bulan · kehadiran dalam hari`}
        />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {bidangDomain.map((b, i) => (
            <GrafikGaris
              key={b.id}
              judul={`${b.name} — posisi kumulatif`}
              titik={titikPosisi(b.id)}
              warna={WARNA[i % WARNA.length]}
            />
          ))}
          {/* Kehadiran diletakkan tepat di samping kanan grafik Kitabah. */}
          <GrafikGaris
            judul="Kehadiran (Hadir)"
            titik={titikHadir()}
            satuan="hari"
            warna="#b45309"
          />
        </div>
      )}

      <div className="rounded-xl bg-white ring-1 ring-black/5">
        <div className="border-b border-black/5 px-4 py-3">
          <h2 className="text-base font-bold text-gray-900">Riwayat</h2>
          <p className="text-xs text-gray-600">
            Kolom kosong berarti bulan itu belum diisi — bukan nol.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] border-collapse text-sm">
            <thead>
              <tr className="bg-kusafa-light text-left text-xs uppercase tracking-wide text-kusafa">
                <th scope="col" className="px-3 py-2">Bulan</th>
                {bidangDomain.map((b) => (
                  <th key={b.id} scope="col" className="border-l border-white/60 px-3 py-2">
                    {b.name}
                  </th>
                ))}
                <th scope="col" className="border-l border-white/60 px-3 py-2">Hadir/HE</th>
                <th scope="col" className="border-l border-white/60 px-3 py-2">Target</th>
              </tr>
            </thead>
            <tbody>
              {bulanRentang.map((b) => {
                const perBidang = bidangDomain.map((bd) =>
                  riwayat.find((x) => x.subject_id === bd.id && x.month_id === b.id),
                );
                const hadir = perBidang.find((r) => r && r.hadir !== null && r.hadir !== undefined);
                const adaTarget = perBidang.filter((r) => r?.target_monthly !== null && r?.target_monthly !== undefined);
                return (
                  <tr key={b.id} className="border-t border-black/5 align-top">
                    <th scope="row" className="px-3 py-2 text-left font-medium text-gray-900">
                      {b.name}
                      {b.semester && <span className="ml-1 text-xs font-normal text-gray-500">S{b.semester}</span>}
                    </th>
                    {perBidang.map((r, i) => (
                      <td key={bidangDomain[i].id} className="border-l border-black/5 px-3 py-2">
                        {!r || r.selisih === null ? (
                          <span className="text-xs text-gray-500">belum diisi</span>
                        ) : (
                          <div className="whitespace-nowrap text-xs">
                            <div className="text-gray-800" title="Posisi kumulatif">
                              {r.item_label ?? "–"}
                            </div>
                            <div className="flex flex-wrap items-center gap-1">
                              <span
                                className={
                                  r.below_target
                                    ? "rounded bg-pink-100 px-1.5 font-semibold text-pink-900"
                                    : "rounded bg-emerald-50 px-1.5 font-semibold text-emerald-800"
                                }
                              >
                                selisih {(r.selisih > 0 ? "+" : "") + angka(r.selisih)}
                              </span>
                              {r.target_monthly === null ? (
                                <span className="text-amber-800">target belum ada</span>
                              ) : r.below_target ? (
                                <span className="text-pink-900">di bawah target</span>
                              ) : (
                                <span className="text-emerald-800">tercapai</span>
                              )}
                            </div>
                          </div>
                        )}
                      </td>
                    ))}
                    <td className="border-l border-black/5 px-3 py-2 text-xs">
                      {hadir ? (
                        <span
                          className={
                            hadir.attendance_short
                              ? "rounded bg-amber-100 px-1.5 py-0.5 font-semibold text-amber-900"
                              : "text-gray-800"
                          }
                        >
                          {angka(hadir.hadir)}/{angka(hadir.effective_days)}
                        </span>
                      ) : (
                        <span className="text-gray-500">belum diisi</span>
                      )}
                    </td>
                    <td className="border-l border-black/5 px-3 py-2 text-xs text-gray-800">
                      {adaTarget.length === 0 ? (
                        <span className="text-gray-500">belum ada</span>
                      ) : (
                        adaTarget.map((r, i) => (
                          <div key={i}>
                            <span className="text-gray-500">
                              {bidangDomain.find((bd) => bd.id === r?.subject_id)?.name}:{" "}
                            </span>
                            {angka(r?.target_monthly)}
                          </div>
                        ))
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}