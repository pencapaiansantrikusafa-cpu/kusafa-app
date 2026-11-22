import { useMemo, useState } from "react";

export interface Seri {
  nama: string;
  warna: string;
  /** true = garis putus-putus (mis. Kehadiran). */
  putus?: boolean;
  titik: { label: string; nilai: number | null }[];
}

interface Props {
  judul: string;
  seri: Seri[];
  satuan?: string;
}

const W = 660;
const H = 240;
const PAD_KIRI = 40;
const PAD_KANAN = 12;
const PAD_ATAS = 14;
const PAD_BAWAH = 30;

/**
 * Grafik garis SVG dengan banyak seri dalam satu kotak.
 * Label bulan datang dari seri pertama. Bulan tanpa nilai dilewati
 * (garis diputus), jadi terlihat sebagai celah, bukan turun ke nol.
 */
export default function GrafikGabungan({ judul, seri, satuan }: Props) {
  const [aktif, setAktif] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(seri.map((s) => [s.nama, true])),
  );

  const labels = seri[0]?.titik.map((t) => t.label) ?? [];
  const n = labels.length;

  const { min, max } = useMemo(() => {
    const angka = seri
      .filter((s) => aktif[s.nama] !== false)
      .flatMap((s) => s.titik.map((t) => t.nilai))
      .filter((v): v is number => v !== null && v !== undefined);
    if (angka.length === 0) return { min: 0, max: 1 };
    const lo = Math.min(...angka);
    const hi = Math.max(...angka);
    return { min: Math.min(0, lo), max: hi === lo ? lo + 1 : hi };
  }, [seri, aktif]);

  const x = (i: number) => PAD_KIRI + (n <= 1 ? 0 : (i * (W - PAD_KIRI - PAD_KANAN)) / (n - 1));
  const y = (v: number) => PAD_ATAS + ((max - v) / (max - min || 1)) * (H - PAD_ATAS - PAD_BAWAH);

  const adaData = seri.some((s) => s.titik.some((t) => t.nilai !== null));

  return (
    <figure className="rounded-xl bg-white p-3 ring-1 ring-black/5">
      <figcaption className="mb-2 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="text-sm font-semibold text-gray-900">{judul}</span>
        {satuan && <span className="text-xs text-gray-500">{satuan}</span>}
      </figcaption>

      {/* Keterangan warna; bisa diketuk untuk menyembunyikan garis. */}
      <div className="mb-1 flex flex-wrap gap-x-3 gap-y-1 text-xs">
        {seri.map((s) => (
          <button
            key={s.nama}
            type="button"
            onClick={() => setAktif((a) => ({ ...a, [s.nama]: a[s.nama] === false }))}
            aria-pressed={aktif[s.nama] !== false}
            className={
              "flex items-center gap-1.5 rounded px-1 py-0.5 " +
              (aktif[s.nama] === false ? "opacity-40" : "opacity-100")
            }
            title="Ketuk untuk sembunyikan/tampilkan garis"
          >
            <span
              aria-hidden
              className="inline-block h-0.5 w-5 rounded"
              style={{
                backgroundColor: s.warna,
                backgroundImage: s.putus
                  ? `repeating-linear-gradient(90deg, ${s.warna} 0 4px, transparent 4px 7px)`
                  : undefined,
              }}
            />
            <span className="text-gray-700">{s.nama}</span>
          </button>
        ))}
      </div>

      {!adaData ? (
        <p className="py-10 text-center text-xs text-gray-500">Belum ada data.</p>
      ) : (
        <div className="overflow-x-auto">
          <svg viewBox={`0 0 ${W} ${H}`} className="h-60 w-full min-w-[560px]" role="img" aria-label={judul}>
            {[max, min + (max - min) * 0.75, min + (max - min) * 0.5, min + (max - min) * 0.25, min].map((v, i) => (
              <g key={i}>
                <line x1={PAD_KIRI} x2={W - PAD_KANAN} y1={y(v)} y2={y(v)} stroke="#e5e7eb" />
                <text x={4} y={y(v) + 3} fontSize="9" fill="#6b7280">
                  {Math.round(v * 10) / 10}
                </text>
              </g>
            ))}

            {labels.map((lb, i) => (
              <text key={i} x={x(i)} y={H - 10} fontSize="8" fill="#6b7280" textAnchor="middle">
                {lb.slice(0, 7)}
              </text>
            ))}

            {seri.map((s) => {
              if (aktif[s.nama] === false) return null;
              const segmen: string[] = [];
              let jalan = "";
              s.titik.forEach((t, i) => {
                if (t.nilai === null || t.nilai === undefined) {
                  if (jalan) segmen.push(jalan);
                  jalan = "";
                  return;
                }
                jalan += `${jalan ? " L" : "M"} ${x(i).toFixed(1)} ${y(t.nilai).toFixed(1)}`;
              });
              if (jalan) segmen.push(jalan);
              return (
                <g key={s.nama}>
                  {segmen.map((d, i) => (
                    <path
                      key={i}
                      d={d}
                      fill="none"
                      stroke={s.warna}
                      strokeWidth="2"
                      strokeDasharray={s.putus ? "5 4" : undefined}
                      strokeLinejoin="round"
                    />
                  ))}
                  {s.titik.map((t, i) =>
                    t.nilai === null || t.nilai === undefined ? null : (
                      <circle key={i} cx={x(i)} cy={y(t.nilai)} r="2.6" fill={s.warna}>
                        <title>{`${s.nama} · ${t.label}: ${t.nilai}`}</title>
                      </circle>
                    ),
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      )}
    </figure>
  );
}