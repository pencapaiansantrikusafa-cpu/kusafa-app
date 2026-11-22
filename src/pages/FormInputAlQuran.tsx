import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { angka } from "../lib/laporan";

export interface BarisInput {
  santri_id: string;
  santri_nama: string;
  /** per bidang: nilai item (id item) atau null = belum diisi */
  itemPerBidang: Record<string, string | null>;
  izin: string;
  sakit: string;
  alpha: string;
  catatan: string;
  /** Hari Efektif khusus santri (hanya boleh diubah Mudir/Admin). */
  heOverride: string;
}

export interface BidangInput {
  id: string;
  name: string;
}

interface Item {
  id: string;
  subject_id: string;
  label: string;
  value: string | null;
}

interface Props {
  bulanId: string;
  bulanNama: string;
  halaqahId: string;
  bidang: BidangInput[];
  baris: BarisInput[];
  setBaris: (b: BarisInput[]) => void;
  items: Item[];
  hariEfektif: number | null;
  terkunci: boolean;
  bolehHariEfektifKhusus: boolean;
  onSelesai: () => void;
}

/**
 * Form input capaian Al Qur'an untuk satu halaqah dan satu bulan.
 * Semua penjagaan hak akses tetap di database (RLS); form hanya menampilkan pesan galatnya.
 */
export default function FormInputAlQuran({
  bulanId,
  bulanNama,
  halaqahId,
  bidang,
  baris,
  setBaris,
  items,
  hariEfektif,
  terkunci,
  bolehHariEfektifKhusus,
  onSelesai,
}: Props) {
  const [menyimpan, setMenyimpan] = useState(false);
  const [pesan, setPesan] = useState<{ jenis: "ok" | "galat"; teks: string } | null>(null);
  const [terbuka, setTerbuka] = useState<string | null>(baris[0]?.santri_id ?? null);
  // "belum" = hanya santri yang belum lengkap (fokus mengisi), "semua" = termasuk yang sudah ada data.
  const [saring, setSaring] = useState<"semua" | "belum" | "sudah">("semua");

  const itemPerBidang = useMemo(() => {
    const p: Record<string, Item[]> = {};
    for (const it of items) (p[it.subject_id] ??= []).push(it);
    return p;
  }, [items]);

  /** Lengkap = semua bidang terisi dan kehadiran (izin+sakit+alpha) masuk akal. */
  function statusSantri(b: BarisInput) {
    const terisi = bidang.filter((bd) => b.itemPerBidang[bd.id]).length;
    return { terisi, total: bidang.length, sudah: terisi === bidang.length };
  }

  const jumlahSudah = baris.filter((b) => statusSantri(b).sudah).length;
  const jumlahBelum = baris.length - jumlahSudah;

  const barisTampil = baris.filter((b) => {
    const sudah = statusSantri(b).sudah;
    return saring === "semua" || (saring === "belum" ? !sudah : sudah);
  });

  function ubah(santriId: string, patch: Partial<BarisInput>) {
    setBaris(baris.map((b) => (b.santri_id === santriId ? { ...b, ...patch } : b)));
  }

  function ubahBidang(santriId: string, bidangId: string, itemId: string) {
    const b = baris.find((x) => x.santri_id === santriId);
    if (!b) return;
    ubah(santriId, {
      itemPerBidang: { ...b.itemPerBidang, [bidangId]: itemId || null },
    });
  }

  async function simpan() {
    setMenyimpan(true);
    setPesan(null);
    try {
      // 1. Kehadiran (izin/sakit/alpha) dan catatan per santri.
      for (const b of baris) {
        const att = {
          student_id: b.santri_id,
          month_id: bulanId,
          domain: "alquran",
          izin: Number(b.izin || 0),
          sakit: Number(b.sakit || 0),
          alpha: Number(b.alpha || 0),
          ...(bolehHariEfektifKhusus && b.heOverride !== ""
            ? { effective_days_override: Number(b.heOverride) }
            : {}),
        };
        const { error: e1 } = await supabase
          .from("attendance")
          .upsert(att, { onConflict: "student_id,month_id,domain" });
        if (e1) throw new Error(`Kehadiran ${b.santri_nama}: ${e1.message}`);

        if (b.catatan.trim()) {
          const { error: e2 } = await supabase
            .from("monthly_notes")
            .upsert(
              {
                student_id: b.santri_id,
                month_id: bulanId,
                domain: "alquran",
                note: b.catatan.trim(),
              },
              { onConflict: "student_id,month_id,domain" },
            );
          if (e2) throw new Error(`Catatan ${b.santri_nama}: ${e2.message}`);
        }

        // 2. Capaian per bidang yang dipilih.
        for (const bd of bidang) {
          const itemId = b.itemPerBidang[bd.id];
          if (!itemId) continue;
          const { error: e3 } = await supabase.from("progress_entries").upsert(
            {
              student_id: b.santri_id,
              halaqah_id: halaqahId,
              subject_id: bd.id,
              month_id: bulanId,
              item_id: itemId,
            },
            { onConflict: "student_id,subject_id,month_id" },
          );
          if (e3) throw new Error(`Capaian ${bd.name} ${b.santri_nama}: ${e3.message}`);
        }
      }
      setPesan({ jenis: "ok", teks: "Data tersimpan." });
      onSelesai();
    } catch (e) {
      setPesan({
        jenis: "galat",
        teks: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setMenyimpan(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-gray-900">Input capaian — {bulanNama}</h2>
            <p className="text-xs text-gray-600">
              Hari Efektif domain: <strong>{angka(hariEfektif)}</strong>
              {terkunci && <span className="ml-2 rounded bg-gray-200 px-1.5 py-0.5">bulan terkunci</span>}
            </p>
          </div>
          <button
            onClick={() => void simpan()}
            disabled={menyimpan || terkunci}
            className="rounded-lg bg-kusafa px-4 py-2 text-sm font-medium text-white hover:bg-kusafa/90 disabled:opacity-50"
          >
            {menyimpan ? "Menyimpan..." : "Simpan"}
          </button>
        </div>
        {terkunci && (
          <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Bulan ini sudah dikunci. Hanya Mudir atau Admin yang dapat mengubahnya.
          </p>
        )}
        {pesan && (
          <p
            role="alert"
            className={
              "mt-2 rounded-lg px-3 py-2 text-sm " +
              (pesan.jenis === "ok" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800")
            }
          >
            {pesan.teks}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl bg-white px-3 py-2 ring-1 ring-black/5">
        <span className="text-sm font-medium text-gray-800">Tampilkan</span>
        {(
          [
            ["semua", `Semua (${baris.length})`],
            ["belum", `Belum lengkap (${jumlahBelum})`],
            ["sudah", `Sudah ada data (${jumlahSudah})`],
          ] as ["semua" | "belum" | "sudah", string][]
        ).map(([nilai, label]) => (
          <button
            key={nilai}
            onClick={() => setSaring(nilai)}
            aria-pressed={saring === nilai}
            className={
              "rounded-lg px-3 py-1.5 text-sm " +
              (saring === nilai
                ? "bg-kusafa text-white"
                : "border border-gray-300 text-gray-700 hover:bg-gray-50")
            }
          >
            {label}
          </button>
        ))}
        <span className="ml-auto flex items-center gap-3 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full bg-pink-400" /> belum lengkap
          </span>
          <span className="flex items-center gap-1">
            <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" /> sudah terisi
          </span>
        </span>
      </div>

      <ul className="space-y-2">
        {barisTampil.map((b) => {
          const buka = terbuka === b.santri_id;
          const st = statusSantri(b);
          return (
            <li
              key={b.santri_id}
              className={
                "rounded-xl border-l-4 bg-white ring-1 ring-black/5 " +
                (st.sudah ? "border-l-emerald-500" : "border-l-pink-400")
              }
            >
              <button
                onClick={() => setTerbuka(buka ? null : b.santri_id)}
                aria-expanded={buka}
                className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
              >
                <span className="min-w-0">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="truncate text-sm font-medium text-gray-900">{b.santri_nama}</span>
                    <span
                      className={
                        "rounded px-1.5 py-0.5 text-[11px] font-medium " +
                        (st.sudah
                          ? "bg-emerald-50 text-emerald-800"
                          : "bg-pink-50 text-pink-900")
                      }
                    >
                      {st.sudah ? "✓ sudah terisi" : "belum lengkap"}
                    </span>
                  </span>
                  <span className="text-xs text-gray-600">
                    {st.terisi}/{st.total} bidang terisi · izin {b.izin || 0}, sakit {b.sakit || 0}, alpha {b.alpha || 0}
                  </span>
                </span>
                <span aria-hidden className="text-gray-400">{buka ? "▴" : "▾"}</span>
              </button>

              {buka && (
                <div className="space-y-3 border-t border-black/5 px-4 py-3">
                  <div className="grid gap-3 sm:grid-cols-3">
                    {bidang.map((bd) => (
                      <div key={bd.id}>
                        <label
                          htmlFor={`item-${b.santri_id}-${bd.id}`}
                          className="block text-xs font-medium text-gray-800"
                        >
                          {bd.name}
                        </label>
                        <select
                          id={`item-${b.santri_id}-${bd.id}`}
                          value={b.itemPerBidang[bd.id] ?? ""}
                          onChange={(e) => ubahBidang(b.santri_id, bd.id, e.target.value)}
                          className="mt-1 w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                        >
                          <option value="">— belum diisi —</option>
                          {(itemPerBidang[bd.id] ?? []).map((it) => (
                            <option key={it.id} value={it.id}>
                              {it.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {(
                      [
                        ["izin", "Izin"],
                        ["sakit", "Sakit"],
                        ["alpha", "Alpha"],
                      ] as ["izin" | "sakit" | "alpha", string][]
                    ).map(([k, label]) => (
                      <div key={k}>
                        <label htmlFor={`${k}-${b.santri_id}`} className="block text-xs font-medium text-gray-800">
                          {label}
                        </label>
                        <input
                          id={`${k}-${b.santri_id}`}
                          type="number"
                          min={0}
                          step={1}
                          inputMode="numeric"
                          value={b[k]}
                          onChange={(e) => ubah(b.santri_id, { [k]: e.target.value } as Partial<BarisInput>)}
                          className="mt-1 w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                        />
                      </div>
                    ))}
                  </div>

                  {bolehHariEfektifKhusus && (
                    <div>
                      <label
                        htmlFor={`he-${b.santri_id}`}
                        className="block text-xs font-medium text-gray-800"
                      >
                        Hari Efektif khusus santri (kosongkan bila sama dengan domain)
                      </label>
                      <input
                        id={`he-${b.santri_id}`}
                        type="number"
                        min={0}
                        step={1}
                        value={b.heOverride}
                        onChange={(e) => ubah(b.santri_id, { heOverride: e.target.value })}
                        className="mt-1 w-32 rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                      />
                    </div>
                  )}

                  <div>
                    <label htmlFor={`catatan-${b.santri_id}`} className="block text-xs font-medium text-gray-800">
                      Catatan
                    </label>
                    <textarea
                      id={`catatan-${b.santri_id}`}
                      rows={2}
                      value={b.catatan}
                      onChange={(e) => ubah(b.santri_id, { catatan: e.target.value })}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                      placeholder="Catatan bulanan (boleh kosong)"
                    />
                  </div>

                  <Link
                    to={`/santri/${b.santri_id}?domain=alquran`}
                    className="inline-block text-xs font-medium text-kusafa underline underline-offset-2"
                  >
                    Lihat capaian santri ini
                  </Link>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}