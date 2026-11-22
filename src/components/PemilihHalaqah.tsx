import { supabase } from "../lib/supabase";

export interface HalaqahData {
  id: string;
  code: string;
  name: string;
}

export interface GuruBaris {
  halaqah_id: string;
  full_name: string;
}

/**
 * Peta halaqah -> daftar pengampu (nama digabung dengan koma).
 * Al Qur'an memakai musyrif/ah, Wasilah pengampu, Ghayah muallim/ah.
 */
export function petaPengampu(baris: GuruBaris[]): Record<string, string> {
  const peta = new Map<string, string[]>();
  for (const r of baris) {
    if (!r.full_name) continue;
    const arr = peta.get(r.halaqah_id) ?? [];
    if (!arr.includes(r.full_name)) arr.push(r.full_name);
    peta.set(r.halaqah_id, arr);
  }
  const hasil: Record<string, string> = {};
  peta.forEach((v, k) => {
    hasil[k] = v.join(", ");
  });
  return hasil;
}

/**
 * Mengambil pengampu untuk banyak halaqah sekaligus.
 * Dipakai semua halaman agar label dropdown selalu memuat nama pengampu.
 */
export async function ambilPengampu(): Promise<Record<string, string>> {
  const { data } = await supabase
    .from("halaqah_teachers")
    .select("halaqah_id, profiles!inner(full_name)")
    .limit(1000);
  const baris = ((data ?? []) as unknown as Array<{
    halaqah_id: string;
    profiles: { full_name: string } | { full_name: string }[];
  }>).map((r) => {
    const p = Array.isArray(r.profiles) ? r.profiles[0] : r.profiles;
    return { halaqah_id: r.halaqah_id, full_name: p?.full_name ?? "" };
  });
  return petaPengampu(baris);
}

/** Label baku: "HLQ-PA-1 - Ust. Fulan 1" (tanpa kategori Putra/Putri). */
export function labelHalaqah(h: HalaqahData, pengampu: Record<string, string>): string {
  const guru = pengampu[h.id];
  return guru ? `${h.code} - ${guru}` : h.code;
}

interface Props {
  id: string;
  label: string;
  halaqah: HalaqahData[];
  pengampu: Record<string, string>;
  nilai: string;
  onChange: (id: string) => void;
  /** Keterangan kecil di bawah (mis. "Pengampu belum ditetapkan"). */
  keterangan?: string;
}

/** Dropdown halaqah/level/kelompok yang selalu menampilkan nama pengampu. */
export default function PemilihHalaqah({ id, label, halaqah, pengampu, nilai, onChange, keterangan }: Props) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-800">
        {label}
      </label>
      <select
        id={id}
        value={nilai}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base"
      >
        {halaqah.map((h) => (
          <option key={h.id} value={h.id}>
            {labelHalaqah(h, pengampu)}
          </option>
        ))}
      </select>
      {keterangan && <p className="mt-1 truncate text-xs text-gray-600">{keterangan}</p>}
    </div>
  );
}