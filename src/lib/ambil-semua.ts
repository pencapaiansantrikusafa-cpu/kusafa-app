/**
 * Supabase membatasi setiap permintaan ke maksimal 1.000 baris (proyek ini memakainya).
 * Query tanpa "ambil semua" akan diam-diam terpotong, sehingga daftar item atau
 * capaian menjadi tidak lengkap. Helper ini mengambil bertahap sampai habis.
 */

/** Batas per permintaan; 1.000 adalah batas server Supabase, jangan dinaikkan. */
export const UKURAN_HALAMAN = 1000;

/**
 * Panggil `ambil(awal, jumlah)` berulang kali sampai halaman terakhir lebih pendek
 * dari jumlah yang diminta. Urutan harus stabil (sertakan kolom unik dalam ORDER BY).
 */
export async function ambilSemua<T>(
  ambil: (awal: number, jumlah: number) => PromiseLike<{ data: T[] | null; error: { message: string } | null }>,
  ukuran = UKURAN_HALAMAN,
): Promise<{ data: T[]; error: { message: string } | null }> {
  const hasil: T[] = [];
  let awal = 0;
  // Pengaman agar tidak berputar tanpa akhir bila server mengabaikan rentang.
  for (let putaran = 0; putaran < 100; putaran++) {
    const { data, error } = await ambil(awal, ukuran);
    if (error) return { data: hasil, error };
    const baris = data ?? [];
    hasil.push(...baris);
    if (baris.length < ukuran) return { data: hasil, error: null };
    awal += ukuran;
  }
  return { data: hasil, error: null };
}
