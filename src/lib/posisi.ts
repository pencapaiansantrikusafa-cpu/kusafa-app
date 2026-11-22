import { supabase } from "./supabase";

/**
 * Posisi kumulatif sebuah item pada putaran tertentu.
 *
 * Rumusnya ada di database (`public.item_position`), bukan di React:
 * posisi = value + value_offset + (putaran - 1) * cycle_length untuk buku siklik.
 * Hasil disimpan sementara agar satu halaman tidak memanggil berulang kali.
 */
const cache = new Map<string, number | null>();

export async function posisiItem(itemId: string, putaran: number): Promise<number | null> {
  const kunci = `${itemId}|${putaran}`;
  if (cache.has(kunci)) return cache.get(kunci) ?? null;
  const { data, error } = await supabase.rpc("item_position", {
    p_item: itemId,
    p_putaran: putaran,
  });
  if (error) throw new Error(`Gagal menghitung posisi: ${error.message}`);
  const nilai = data === null || data === undefined ? null : Number(data);
  cache.set(kunci, nilai);
  return nilai;
}
