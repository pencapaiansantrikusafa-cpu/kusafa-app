import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PemilihTahunBulan from "../components/PemilihTahunBulan";
import PemilihHalaqah, { ambilPengampu } from "../components/PemilihHalaqah";
import { DOMAIN_LABEL, type Domain } from "../lib/roles";
import { supabase } from "../lib/supabase";
import { angka, type BarisLaporan } from "../lib/laporan";
import TabelAlQuran from "./TabelAlQuran";

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

export default function TabelCapaian({ domain }: { domain: Domain }) {
  const [halaqahList, setHalaqahList] = useState<Halaqah[]>([]);
  const [pengampu, setPengampu] = useState<Record<string, string>>({});
  const [bulanList, setBulanList] = useState<Bulan[]>([]);
  const [tahun, setTahun] = useState<number | "">("");
  const [halaqahId, setHalaqahId] = useState("");
  const [bulanId, setBulanId] = useState("");
  const [baris, setBaris] = useState<BarisLaporan[]>([]);
  const [santri, setSantri] = useState<Santri[]>([]);
  const [bidang, setBidang] = useState<Bidang[]>([]);
  const [memuat, setMemuat] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);
  const [detail, setDetail] = useState<Santri | null>(null);

  // Daftar halaqah + pengampu, bulan, dan bidang.
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

      setPengampu(await ambilPengampu());
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
      const halaqahAwal = h.data?.[0]?.id || "";
      setHalaqahId((prev) => prev || halaqahAwal);

      // Bulan default: bulan terakhir yang punya capaian.
      const { data: adaData } = await supabase
        .from("progress_entries")
        .select("month_id")
        .in("month_id", semua.map((x) => x.id))
        .limit(2000);
      if (!aktif) return;
      const punyaData = new Set((adaData ?? []).map((x) => x.month_id));
      const terakhir = [...semua].reverse().find((x) => punyaData.has(x.id));
      const dipilih = terakhir ?? semua[semua.length - 1];
      setTahun((prev) => (prev !== "" ? prev : dipilih?.hijri_year ?? ""));
      // Hanya terapkan pada pemuatan pertama; domain berikutnya punya state sendiri.
      setBulanId((prev) => prev || dipilih?.id || "");
      setMemuat(false);
    }
    void muat().catch((e: unknown) => {
      setGalat(`Gagal memuat: ${e instanceof Error ? e.message : String(e)}`);
      setMemuat(false);
    });
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

  function gantiTahun(t: number) {
    setTahun(t);
    const calon = bulanList.filter((b) => Number(b.hijri_year) === t);
    if (!calon.some((b) => b.id === bulanId)) {
      setBulanId(calon[calon.length - 1]?.id ?? "");
    }
  }

  // Ringkasan singkat untuk HP: santri mana yang belum sesuai target, bidang apa.
  const ringkasanHp = useMemo(() => {
    const peta = new Map<string, BarisLaporan>();
    for (const b of baris) peta.set(`${b.student_id}|${b.subject_id}`, b);
    return santri.map((s) => {
      const masalah: string[] = [];
      const kosong: string[] = [];
      for (const bd of bidang) {
        const r = peta.get(`${s.id}|${bd.id}`);
        if (!r || r.pos === null || r.target_monthly === null) kosong.push(bd.name);
        else if (r.below_target) masalah.push(bd.name);
      }
      return { santri: s, masalah, kosong };
    });
  }, [santri, bidang, baris]);

  const pengampuTerpilih = pengampu[halaqahId] ?? "";

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <PemilihHalaqah
              id={`halaqah-${domain}`}
              label={domain === "wasilah" ? "Level" : domain === "ghayah" ? "Kelompok" : "Halaqah"}
              halaqah={halaqahList}
              pengampu={pengampu}
              nilai={halaqahId}
              onChange={setHalaqahId}
              keterangan={pengampu[halaqahId] ? `Pengampu: ${pengampu[halaqahId]}` : "Pengampu belum ditetapkan"}
            />
          </div>

          <PemilihTahunBulan
            bulan={bulanList}
            tahun={tahun}
            bulanId={bulanId}
            idAwalan={`tahun-bulan-${domain}`}
            onTahun={gantiTahun}
            onBulan={setBulanId}
            catatan="Pembanding otomatis bulan sebelumnya."
          />
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
            {santri.length} santri · {memuat ? "memuat..." : `${baris.filter((b) => b.below_target).length} di bawah target`}
          </p>
        </div>

        {memuat && santri.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">Memuat data...</p>
        ) : santri.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">Belum ada anggota di halaqah ini.</p>
        ) : (
          <>
            {/* HP: ringkasan singkat, detail lewat pop-up. */}
            <ul className="divide-y divide-black/5 lg:hidden">
              {ringkasanHp.map(({ santri: s, masalah, kosong }) => (
                <li key={s.id}>
                  <button
                    onClick={() => setDetail(s)}
                    className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left hover:bg-gray-50"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium text-gray-900">{s.full_name}</span>
                      <span className="mt-0.5 block text-xs">
                        {masalah.length > 0 ? (
                          <span className="text-pink-900">
                            di bawah target: {masalah.join(", ")}
                          </span>
                        ) : (
                          <span className="text-emerald-800">sesuai target</span>
                        )}
                        {kosong.length > 0 && (
                          <span className="text-amber-800"> · belum diisi: {kosong.join(", ")}</span>
                        )}
                      </span>
                    </span>
                    <span aria-hidden className="shrink-0 text-gray-400">
                      ›
                    </span>
                  </button>
                </li>
              ))}
            </ul>

            {/* Desktop: tabel lengkap. */}
            <div className="hidden lg:block">
              {domain === "alquran" ? (
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
          </>
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
            belum diisi
          </span>
          data belum ada di Excel/database, bukan nol.
        </p>
      </div>

      {detail && (
        <DialogDetail
          santri={detail}
          bidang={bidang}
          baris={baris}
          domain={domain}
          namaHalaqah={halaqahList.find((h) => h.id === halaqahId)?.code ?? ""}
          hadirTeks={(() => {
            const hd = baris.find((b) => b.student_id === detail.id && b.hadir !== null);
            return hd
              ? `${angka(hd.hadir)}/${angka(hd.effective_days)}${hd.attendance_short ? " — kurang" : ""}`
              : "belum diisi";
          })()}
          onTutup={() => setDetail(null)}
        />
      )}
    </div>
  );
}

/** Pop-up detail capaian satu santri (dipakai di HP). */
function DialogDetail({
  santri,
  bidang,
  baris,
  domain,
  namaHalaqah,
  hadirTeks,
  onTutup,
}: {
  santri: Santri;
  bidang: Bidang[];
  baris: BarisLaporan[];
  domain: Domain;
  namaHalaqah: string;
  /** Hadir/HE cukup ditampilkan sekali di kepala pop-up. */
  hadirTeks: string;
  onTutup: () => void;
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onTutup();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onTutup]);

  return (
    <div
      className="fixed inset-0 z-40 flex items-end bg-black/40 sm:items-center sm:justify-center"
      onClick={onTutup}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Detail capaian ${santri.full_name}`}
        className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:max-w-md sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-gray-900">{santri.full_name}</h3>
            <p className="text-xs text-gray-600">
              {namaHalaqah} · Hadir/HE: <strong className="text-gray-800">{hadirTeks}</strong>
            </p>
          </div>
          <button
            onClick={onTutup}
            className="rounded-lg border border-gray-300 px-2.5 py-1 text-sm text-gray-700"
          >
            Tutup
          </button>
        </div>

        <Link
          to={`/santri/${santri.id}?domain=${domain}&dari=capaian`}
          className="mt-3 block rounded-lg bg-kusafa px-3 py-2 text-center text-sm font-medium text-white hover:bg-kusafa/90"
        >
          Buka halaman santri (grafik & riwayat)
        </Link>

        <div className="mt-3 space-y-3">
          {bidang.map((b) => {
            const r = baris.find((x) => x.student_id === santri.id && x.subject_id === b.id);
            return (
              <div key={b.id} className="rounded-lg bg-gray-50 p-3">
                <p className="text-sm font-semibold text-kusafa">{b.name}</p>
                {!r || r.pos === null ? (
                  <p className="mt-1 text-xs text-amber-800">Belum diisi</p>
                ) : (
                  <dl className="mt-1 space-y-0.5 text-xs">
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Capaian lalu</dt>
                      <dd className="text-gray-800">{r.prev_item_label ?? "–"}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Capaian kini</dt>
                      <dd className="font-medium text-gray-900">{r.item_label ?? "–"}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Selisih</dt>
                      <dd
                        className={
                          r.selisih !== null && r.selisih < 0
                            ? "font-semibold text-red-700"
                            : "font-semibold text-kusafa"
                        }
                      >
                        {r.selisih === null ? "–" : (r.selisih > 0 ? "+" : "") + angka(r.selisih)}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Target bulanan</dt>
                      <dd className="text-gray-800">{angka(r.target_monthly)}</dd>
                    </div>
                    <div className="pt-1">
                      {r.target_monthly === null ? (
                        <span className="rounded bg-amber-100 px-1.5 py-0.5 font-medium text-amber-900">
                          target belum ada
                        </span>
                      ) : r.below_target ? (
                        <span className="rounded bg-pink-100 px-1.5 py-0.5 font-medium text-pink-900">
                          di bawah target
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-50 px-1.5 py-0.5 font-medium text-emerald-800">
                          sesuai target
                        </span>
                      )}
                    </div>
                  </dl>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}