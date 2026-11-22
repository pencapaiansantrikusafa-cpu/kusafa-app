import { useMemo } from "react";

export interface BulanData {
  id: string;
  month_no: number;
  name: string;
  hijri_year: number;
}

interface Props {
  /** Semua bulan lintas tahun ajaran. */
  bulan: BulanData[];
  tahun: number | "";
  bulanId: string;
  onTahun: (t: number) => void;
  onBulan: (id: string) => void;
  /** Awalan id elemen agar unik bila dipakai beberapa kali di satu halaman. */
  idAwalan: string;
  /** Sembunyikan bulan "Data Awal" (month_no 0) untuk form input. */
  tanpaDataAwal?: boolean;
  catatan?: string;
}

/**
 * DUA dropdown terpisah: Tahun Hijriyah dan Bulan.
 * Aturan proyek: jangan pernah menggabungkan bulan dan tahun dalam satu dropdown,
 * supaya jumlah pilihan tidak bertambah saat tahun ajaran berganti.
 */
export default function PemilihTahunBulan({
  bulan,
  tahun,
  bulanId,
  onTahun,
  onBulan,
  idAwalan,
  tanpaDataAwal = false,
  catatan,
}: Props) {
  const daftarTahun = useMemo(
    () => [...new Set(bulan.map((b) => Number(b.hijri_year)))].sort((a, b) => a - b),
    [bulan],
  );

  const bulanTahunIni = useMemo(
    () =>
      bulan
        .filter((b) => Number(b.hijri_year) === Number(tahun))
        .filter((b) => (tanpaDataAwal ? b.month_no > 0 : true))
        .sort((a, b) => a.month_no - b.month_no),
    [bulan, tahun, tanpaDataAwal],
  );

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <div>
        <label htmlFor={`${idAwalan}-tahun`} className="block text-sm font-medium text-gray-800">
          Tahun Hijriyah
        </label>
        <select
          id={`${idAwalan}-tahun`}
          value={tahun}
          onChange={(e) => onTahun(Number(e.target.value))}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base"
        >
          {daftarTahun.map((t) => (
            <option key={t} value={t}>
              {t} H
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor={`${idAwalan}-bulan`} className="block text-sm font-medium text-gray-800">
          Bulan
        </label>
        <select
          id={`${idAwalan}-bulan`}
          value={bulanId}
          onChange={(e) => onBulan(e.target.value)}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base"
        >
          {bulanTahunIni.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
        {catatan && <p className="mt-1 text-xs text-gray-500">{catatan}</p>}
      </div>
    </div>
  );
}