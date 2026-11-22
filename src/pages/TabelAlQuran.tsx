import { useMemo } from "react";
import { angka, type BarisLaporan } from "../lib/laporan";

/**
 * Kolom sesuai wireframe: Santri | Hadir/HE | [per bidang Lalu | Kini | Selisih] | Target bulanan.
 * Jumlah sel badan tabel WAJIB sama dengan jumlah kolom kepala tabel.
 */
export default function TabelAlQuran({
  santri,
  baris,
  bidang,
  memuat,
}: {
  santri: { id: string; full_name: string }[];
  baris: BarisLaporan[];
  bidang: { id: string; name: string }[];
  memuat: boolean;
}) {
  const peta = useMemo(() => {
    const p = new Map<string, BarisLaporan>();
    for (const b of baris) p.set(`${b.student_id}|${b.subject_id}`, b);
    return p;
  }, [baris]);

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] border-collapse text-sm">
          <thead>
            <tr className="bg-kusafa-light text-xs uppercase tracking-wide text-kusafa">
              <th scope="col" className="px-3 py-2 text-left">
                Santri
              </th>
              <th scope="col" className="px-3 py-2 text-left whitespace-nowrap">
                Hadir/HE
              </th>
              {bidang.map((b) => (
                <th key={b.id} scope="col" className="border-l border-white/60 px-3 py-2 text-left">
                  {b.name}
                  <span className="ml-1 font-normal normal-case">(Lalu · Kini · Selisih)</span>
                </th>
              ))}
              <th scope="col" className="border-l border-white/60 px-3 py-2 text-left">
                Target bulanan
              </th>
            </tr>
          </thead>
          <tbody>
            {santri.map((s) => {
              const perBidang = bidang.map((b) => peta.get(`${s.id}|${b.id}`));
              const hadir = perBidang.find((r) => r?.hadir !== null && r?.hadir !== undefined);
              return (
                <tr key={s.id} className="border-t border-black/5 align-top">
                  <th scope="row" className="px-3 py-2 text-left font-medium text-gray-900">
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
                        {hadir.attendance_short && <span className="ml-1 text-xs font-normal">⚠ kurang</span>}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500">belum diisi</span>
                    )}
                  </td>
                  {perBidang.map((r, i) => (
                    <td key={bidang[i].id} className="border-l border-black/5 px-3 py-2">
                      {!r || r.pos === null ? (
                        <span className="text-xs text-gray-500">belum diisi</span>
                      ) : (
                        <div className="flex items-baseline gap-2 whitespace-nowrap">
                          <span className="text-gray-500" title="Bulan lalu">
                            {r.prev_item_label ?? "–"}
                          </span>
                          <span className="font-medium text-gray-900" title="Bulan ini">
                            {r.item_label ?? "–"}
                          </span>
                          <span
                            className={
                              r.selisih !== null && r.selisih < 0
                                ? "font-semibold text-red-700"
                                : "font-semibold text-kusafa"
                            }
                            title="Selisih"
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
                  ))}
                  <td className="border-l border-black/5 px-3 py-2 whitespace-nowrap">
                    {perBidang.every((r) => r?.target_monthly === null || r?.target_monthly === undefined) ? (
                      <span className="text-xs text-gray-500">belum ada</span>
                    ) : (
                      perBidang.map((r, i) => (
                        <div key={i} className="text-gray-800">
                          <span className="text-xs text-gray-500">{bidang[i].name}: </span>
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
      {memuat && <p className="px-4 py-2 text-xs text-gray-500">Memuat...</p>}
    </>
  );
}