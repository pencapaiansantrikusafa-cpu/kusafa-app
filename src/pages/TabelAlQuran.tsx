import { useMemo } from "react";
import { angka, type BarisLaporan } from "../lib/laporan";

/**
 * Tabel capaian Al Qur'an.
 * Tiap kolom bidang berisi bertumpuk: Capaian lalu → Capaian kini → Selisih → keterangan target.
 * Tidak ada perhitungan di sini; semua angka berasal dari view v_monthly_report.
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
      <div className="w-full overflow-x-auto">
        <table className="w-full table-fixed border-collapse text-sm">
          <colgroup>
            <col className="w-[13%]" />
            <col className="w-[8%]" />
            {bidang.map((b) => (
              <col key={b.id} className="w-[19%]" />
            ))}
            <col className="w-[9%]" />
          </colgroup>
          <thead>
            <tr className="bg-kusafa-light text-xs uppercase tracking-wide text-kusafa">
              <th scope="col" className="px-2 py-2 text-left">
                Santri
              </th>
              <th scope="col" className="px-2 py-2 text-left">
                Hadir/HE
              </th>
              {bidang.map((b) => (
                <th key={b.id} scope="col" className="border-l border-white/60 px-2 py-2 text-left">
                  {b.name}
                </th>
              ))}
              <th scope="col" className="border-l border-white/60 px-2 py-2 text-left">
                Target
              </th>
            </tr>
          </thead>
          <tbody>
            {santri.map((s) => {
              const perBidang = bidang.map((b) => peta.get(`${s.id}|${b.id}`));
              const hadir = perBidang.find((r) => r?.hadir !== null && r?.hadir !== undefined);
              return (
                <tr key={s.id} className="border-t border-black/5 align-top">
                  <th scope="row" className="px-2 py-3 text-left align-top font-medium text-gray-900">
                    {s.full_name}
                  </th>
                  <td className="whitespace-nowrap px-2 py-3 align-top">
                    {hadir && hadir.hadir !== null ? (
                      <span
                        className={
                          hadir.attendance_short
                            ? "rounded bg-amber-100 px-1.5 py-0.5 font-semibold text-amber-900"
                            : "text-gray-800"
                        }
                      >
                        {hadir.hadir}/{angka(hadir.effective_days)}
                        {hadir.attendance_short && <div className="mt-0.5 text-xs font-normal">⚠ kurang</div>}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500">belum diisi</span>
                    )}
                  </td>

                  {perBidang.map((r, i) => (
                    <td key={bidang[i].id} className="border-l border-black/5 px-2 py-3 align-top">
                      {!r || r.pos === null ? (
                        <div className="space-y-0.5 text-xs text-gray-500">
                          <div>Lalu: –</div>
                          <div>Kini: –</div>
                          <div>Selisih: –</div>
                          <div className="text-amber-800">belum diisi</div>
                        </div>
                      ) : (
                        <div className="space-y-0.5 text-xs leading-snug">
                          <div className="text-gray-600" title="Capaian bulan lalu">
                            <span className="sr-only">Capaian bulan lalu: </span>
                            {r.prev_item_label ?? "–"}
                          </div>
                          <div className="font-medium text-gray-900" title="Capaian bulan ini">
                            <span className="sr-only">Capaian bulan ini: </span>
                            {r.item_label ?? "–"}
                          </div>
                          <div
                            className={
                              r.selisih !== null && r.selisih < 0
                                ? "font-semibold text-red-700"
                                : "font-semibold text-kusafa"
                            }
                            title="Selisih"
                          >
                            <span className="font-normal text-gray-500">Selisih: </span>
                            {r.selisih === null ? "–" : (r.selisih > 0 ? "+" : "") + angka(r.selisih)}
                          </div>
                          {r.target_monthly === null ? (
                            <div className="text-amber-800">target belum ada</div>
                          ) : r.below_target ? (
                            <div className="rounded bg-pink-100 px-1.5 py-0.5 font-medium text-pink-900">
                              di bawah target
                            </div>
                          ) : (
                            <div className="rounded bg-emerald-50 px-1.5 py-0.5 font-medium text-emerald-800">
                              sesuai target
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                  ))}

                  <td className="border-l border-black/5 px-2 py-3 align-top text-xs">
                    {perBidang.every((r) => r?.target_monthly === null || r?.target_monthly === undefined) ? (
                      <span className="text-gray-500">belum ada</span>
                    ) : (
                      <div className="space-y-0.5">
                        {perBidang.map((r, i) => (
                          <div key={i} className="text-gray-800">
                            <span className="text-gray-500">{bidang[i].name}: </span>
                            {angka(r?.target_monthly)}
                          </div>
                        ))}
                      </div>
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