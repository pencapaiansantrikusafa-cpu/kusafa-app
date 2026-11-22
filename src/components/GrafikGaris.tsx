import { useMemo, useState } from "react";

export interface TitikGrafik {
  label: string;
  /** null = bulan tanpa data (ditampilkan kosong, bukan nol). */
  nilai: number | null;
}

interface Props {
  judul: string;
  titik: TitikGrafik[];
  satuan?: string;
  /** Warna garis (kelas tailwind tidak dipakai agar SVG aman). */
  warna?: string;
}

/**
 * Grafik garis sederhana (SVG). Bulan tanpa data dilewati garisnya,
 * jadi terlihat sebagai celah, bukan turun ke nol.
 */
export default function GrafikGaris({ judul, titik, satuan, warna = "#0f5b45" }: Props) {
  const [hover, setHover] = useState<number | null>(null);

  const adaNilai = titik.filter((t) => t.nilai !== null).length;

  const { min, max } = useMemo(() => {
    const angka = titik.map((t) => t.nilai).filter((v): v is number => v !== null);
    if (angka.length === 0) return { min: 0, max: 1 };
    return { min: Math.min(0, ...angka), max: Math.max(1, ...angka) };
  }, [titik]);

  const W = 620;
  const H = 190;
  const PAD_KIRI = 36;
  const PAD_KANAN = 10;
  const PAD_ATAS = 12;
  const PAD_BAWAH = 26;

  const x = (i: number) =>
    PAD_KIRI + (titik.length <= 1 ? 0 : (i * (W - PAD_KIRI - PAD_KANAN)) / (titik.length - 1));
  const y = (v: number) =>
    PAD_ATAS + ((max - v) / (max - min || 1)) * (H - PAD_ATAS - PAD_BAWAH);

  // Garis diputus saat ada bulan kosong.
  const segmen: string[] = [];
  let jalan = "";
  titik.forEach((t, i) => {
    if (t.nilai === null) {
      if (jalan) segmen.push(jalan);
      jalan = "";
      return;
    }
    jalan += `${jalan ? " L" : "M"} ${x(i).toFixed(1)} ${y(t.nilai).toFixed(1)}`;
  });
  if (jalan) segmen.push(jalan);

  const garisBantu = [max, (max + min) / 2, min];

  return (
    <figure className="rounded-xl bg-white p-3 ring-1 ring-black/5">
      <figcaption className="mb-1 flex items-baseline justify-between gap-2">
        <span className="text-sm font-semibold text-gray-900">{judul}</span>
        <span className="text-xs text-gray-600">
          {satuan ? `${satuan} · ` : ""}
          {adaNilai === 0 ? "belum ada data" : `terisi ${adaNilai} dari ${titik.length} bulan`}
        </span>
      </figcaption>

      {adaNilai === 0 ? (
        <p className="py-10 text-center text-xs text-gray-500">
          Belum ada data untuk bidang ini.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <svg
            viewBox={`0 0 ${W} ${H}`}
            className="h-44 w-full min-w-[520px]"
            role="img"
            aria-label={`Grafik ${judul}`}
          >
            {garisBantu.map((v, i) => (
              <g key={i}>
                <line
                  x1={PAD_KIRI}
                  x2={W - PAD_KANAN}
                  y1={y(v)}
                  y2={y(v)}
                  stroke="#e5e7eb"
                  strokeDasharray={i === 1 ? "3 3" : undefined}
                />
                <text x={4} y={y(v) + 3} fontSize="9" fill="#6b7280">
                  {Math.round(v * 10) / 10}
                </text>
              </g>
            ))}

            {segmen.map((d, i) => (
              <path key={i} d={d} fill="none" stroke={warna} strokeWidth="2" strokeLinejoin="round" />
            ))}

            {titik.map((t, i) =>
              t.nilai === null ? (
                <g key={i}>
                  <line
                    x1={x(i)}
                    x2={x(i)}
                    y1={PAD_ATAS}
                    y2={H - PAD_BAWAH}
                    stroke="#f3f4f6"
                    strokeWidth="6"
                  />
                  <text x={x(i)} y={H - 8} fontSize="8" fill="#9ca3af" textAnchor="middle">
                    {t.label.slice(0, 6)}
                  </text>
                </g>
              ) : (
                <g key={i} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
                  <circle cx={x(i)} cy={y(t.nilai)} r={hover === i ? 5 : 3.2} fill={warna} />
                  <text x={x(i)} y={H - 8} fontSize="8" fill="#6b7280" textAnchor="middle">
                    {t.label.slice(0, 6)}
                  </text>
                </g>
              ),
            )}
          </svg>
        </div>
      )}
    </figure>
  );
}