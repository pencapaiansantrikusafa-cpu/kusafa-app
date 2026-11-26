import { supabase } from "../lib/supabase";
import DropdownCari from "./DropdownCari";

export interface HalaqahData {
  id: string;
  code: string;
  name: string;
}

export interface GuruBaris {
  halaqah_id: string;
  profile_id: string;
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
  return petaPengampu(await ambilGuru());
}

/** Baris pengampu beserta id profilnya (untuk menyaring halaqah yang diampu). */
export async function ambilGuru(): Promise<GuruBaris[]> {
  const { data } = await supabase
    .from("halaqah_teachers")
    .select("halaqah_id, profile_id, profiles!inner(full_name)")
    .limit(2000);
  return ((data ?? []) as unknown as Array<{
    halaqah_id: string;
    profile_id: string;
    profiles: { full_name: string } | { full_name: string }[];
  }>).map((r) => {
    const p = Array.isArray(r.profiles) ? r.profiles[0] : r.profiles;
    return { halaqah_id: r.halaqah_id, profile_id: r.profile_id, full_name: p?.full_name ?? "" };
  });
}

/** Halaqah yang diampu oleh satu profil. */
export function halaqahDiampu(guru: GuruBaris[], profileId: string): Set<string> {
  return new Set(guru.filter((g) => g.profile_id === profileId).map((g) => g.halaqah_id));
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
  /** Teks pilihan kosong (mis. "Semua halaqah") untuk dropdown saringan. */
  opsiKosong?: string;
}

/** Dropdown halaqah/level/kelompok yang selalu menampilkan nama pengampu, dengan pencarian. */
export default function PemilihHalaqah({
  id,
  label,
  halaqah,
  pengampu,
  nilai,
  onChange,
  keterangan,
  opsiKosong,
}: Props) {
  return (
    <DropdownCari
      id={id}
      label={label}
      opsi={halaqah.map((h) => ({
        nilai: h.id,
        label: labelHalaqah(h, pengampu),
        // Pencarian juga mencocokkan kode dan nama pengampu.
        cariJuga: `${h.name} ${pengampu[h.id] ?? ""}`,
      }))}
      nilai={nilai}
      onChange={onChange}
      placeholderCari="Ketik halaqah atau nama pengampu..."
      keterangan={keterangan}
      opsiKosong={opsiKosong}
    />
  );
}
