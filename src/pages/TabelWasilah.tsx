import { useMemo } from "react";
import { Link } from "react-router-dom";
import { angka, type BarisLaporan } from "../lib/laporan";
import type { Domain } from "../lib/roles";

/** Kehadiran satu santri dari view `v_attendance` (angka mentah, bukan hitungan React). */
export interface BarisHadir {
  student_id: string;
  effective_days: number | null;
  izin: number | null;
  sakit: number | null;
  alpha: number | null;
  hadir: number | null;
}

interface Santri {
  id: string;
  full_name: string;
}

/**
 * Tabel capaian Ilmu Wasilah dan Ilmu Ghayah.
 *
 * Bentuk mengikuti `docs/SPEC.md` bagian 5.6: **per mata pelajaran** tampil
 * Capaian Bulan Lalu, Capaian Bulan Ini, dan Selisih; lalu tabel anggota
 * (Nama Santri, Hadir/HE, Izin, Sakit, Alpha, Catatan).
 *
 * Tidak ada perhitungan di sini. Semua angka berasal dari view database:
 * `v_monthly_report` (posisi, selisih, Hadir, Hari Efektif, target) dan
 * `v_attendance` (izin, sakit, alpha). Bulan yang belum diinput tampil
 * "belum diisi", bukan 0.
 */
export default function TabelWasilah({
  santri,
  baris,
  bidang,
  hadir,
  catatan,
  domain,
  memuat,
  onHapus,
}: {
  santri: Santri[];
  baris: BarisLaporan[];
  /** Mata pelajaran yang benar-benar ditetapkan untuk halaqah ini. */
  bidang: { id: string; name: string }[];
  hadir: BarisHadir[];
  /** Catatan bulanan per santri (`monthly_notes`). */
  catatan: Record<string, string>;
  domain: Domain;
  memuat: boolean;
  /** T6e: hanya diberikan untuk Mudir/Admin; tombol hapus per santri+mata pelajaran. */
  onHapus?: (santriId: string, mapelId: string) => void;
}) {
  const petaBaris = useMemo(() => {
    const p = new Map<string, BarisLaporan>();
    for (const b of baris) p.set(`${b.student_id}|${b.subject_id}`, b);
    return p;
  }, [baris]);

  const petaHadir = useMemo(() => {
    const p = new Map<string, BarisHadir>();
    for (const h of hadir) p.set(h.student_id, h);
    return p;
  }, [hadir]);

  /**
   * Satu baris ringkasan per mata pelajaran. Input Wasilah/Ghayah disalin ke semua
   * anggota, jadi nilai yang dipakai adalah baris pertama yang sudah terisi. Bila
   * belum ada satu pun yang terisi, baris dianggap kosong ("belum diisi").
   */
  const ringkas = useMemo(
    () =>
      bidang.map((bd) => {
        const rows = santri
          .map((s) => petaBaris.get(`${s.id}|${bd.id}`))
          .filter((r): r is BarisLaporan => !!r && r.pos !== null);
        const r = rows[0];
        return {
          bidang: bd,
          ada: !!r,
          lalu: r?.prev_item_label ?? null,
          kini: r?.item_label ?? null,
          selisih: r?.selisih ?? null,
          target: r?.target_monthly ?? null,
          below: !!r?.below_target,
        };
      }),
    [bidang, santri, petaBaris],
  );

  const adaRincian = bidang.length > 0;

  return (
    <div className="divide-y divide-black/5">
      {/* Ringkasan per mata pelajaran: Lalu | Kini | Selisih (acuan SPEC 5.6). */}
      <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
        {ringkas.map((k) => (
          <div key={k.bidang.id} className="rounded-lg bg-gray-50 p-3">
            <p className="text-sm font-semibold text-kusafa">{k.bidang.name}</p>
            {!k.ada ? (
              <p className="mt-1 text-xs text-amber-800">
                Belum diisi untuk halaqah ini pada bulan yang dipilih.
              </p>
            ) : (
              <dl className="mt-1.5 space-y-1 text-xs">
                <div className="flex justify-between gap-2">
                  <dt className="text-gray-600">Capaian bulan lalu</dt>
                  <dd className="text-right text-gray-800">{k.lalu ?? "–"}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-gray-600">Capaian bulan ini</dt>
                  <dd className="text-right font-medium text-gray-900">{k.kini ?? "–"}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-gray-600">Selisih</dt>
                  <dd
                    className={
                      (k.selisih ?? 0) < 0
                        ? "font-semibold text-red-700"
                        : "font-semibold text-kusafa"
                    }
                  >
                    {k.selisih === null ? "–" : (k.selisih > 0 ? "+" : "") + angka(k.selisih)}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-gray-600">Target bulanan</dt>
                  <dd className="text-right">
                    {k.target === null ? (
                      <span className="text-amber-800">belum ada</span>
                    ) : k.below ? (
                      <span className="rounded bg-pink-100 px-1.5 py-0.5 font-medium text-pink-900">
                        di bawah target
                      </span>
                    ) : (
                      <span className="rounded bg-emerald-50 px-1.5 py-0.5 font-medium text-emerald-800">
                        {angka(k.target)}
                      </span>
                    )}
                  </dd>
                </div>
              </dl>
            )}
          </div>
        ))}
        {!adaRincian && (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Halaqah ini belum punya mata pelajaran yang ditetapkan. Penetapannya dikerjakan pada T8.
          </p>
        )}
      </div>

      {/* Tabel anggota: Nama Santri, Hadir/HE, Izin, Sakit, Alpha, Catatan. */}
      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-kusafa-light text-xs uppercase tracking-wide text-kusafa">
              <th scope="col" className="px-3 py-2 text-left">
                Nama Santri
              </th>
              <th scope="col" className="px-3 py-2 text-left">
                Hadir/HE
              </th>
              <th scope="col" className="px-3 py-2 text-left">
                Izin
              </th>
              <th scope="col" className="px-3 py-2 text-left">
                Sakit
              </th>
              <th scope="col" className="px-3 py-2 text-left">
                Alpha
              </th>
              <th scope="col" className="px-3 py-2 text-left">
                Catatan
              </th>
              {onHapus && (
                <th scope="col" className="px-3 py-2 text-left">
                  Hapus capaian
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {santri.map((s) => {
              const h = petaHadir.get(s.id);
              const ada = !!h && h.effective_days !== null;
              return (
                <tr key={s.id} className="border-t border-black/5 align-top">
                  <th scope="row" className="px-3 py-3 text-left font-medium text-gray-900">
                    <Link
                      to={`/santri/${s.id}?domain=${domain}&dari=capaian`}
                      className="underline decoration-gray-300 underline-offset-2 hover:text-kusafa"
                      title="Buka halaman santri"
                    >
                      {s.full_name}
                    </Link>
                  </th>
                  <td className="whitespace-nowrap px-3 py-3">
                    {ada ? (
                      <span
                        className={
                          // "Kurang" bukan hitungan React: dibandingkan dengan angka Hari Efektif
                          // yang sudah dihitung database untuk baris yang sama.
                          h.hadir !== null && h.hadir < (h.effective_days ?? 0)
                            ? "rounded bg-amber-100 px-1.5 py-0.5 font-semibold text-amber-900"
                            : "text-gray-800"
                        }
                        title={
                          h.hadir !== null && h.hadir < (h.effective_days ?? 0)
                            ? "Hadir kurang dari Hari Efektif"
                            : undefined
                        }
                      >
                        {angka(h.hadir)}/{angka(h.effective_days)}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500">belum diisi</span>
                    )}
                  </td>
                  {[h?.izin, h?.sakit, h?.alpha].map((v, i) => (
                    <td key={i} className="px-3 py-3 text-gray-800">
                      {v === null || v === undefined ? (
                        <span className="text-xs text-gray-500">–</span>
                      ) : (
                        angka(v)
                      )}
                    </td>
                  ))}
                  {onHapus && (
                    <td className="whitespace-nowrap px-3 py-3">
                      <div className="flex flex-col gap-1">
                        {bidang.map((bd) => {
                          const r = petaBaris.get(`${s.id}|${bd.id}`);
                          if (!r || r.pos === null || r.pos === undefined) return null;
                          return (
                            <button
                              key={bd.id}
                              type="button"
                              onClick={() => onHapus(s.id, bd.id)}
                              className="rounded border border-red-300 px-1.5 py-0.5 text-[11px] font-medium text-red-700 hover:bg-red-50"
                              aria-label={`Hapus capaian ${bd.name} ${s.full_name}`}
                            >
                              Hapus {bd.name}
                            </button>
                          );
                        })}
                      </div>
                    </td>
                  )}
                  <td className="max-w-[22rem] px-3 py-3 text-xs text-gray-700">
                    {catatan[s.id] ? catatan[s.id] : <span className="text-gray-400">–</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {memuat && <p className="px-4 py-2 text-xs text-gray-500">Memuat...</p>}
    </div>
  );
}
