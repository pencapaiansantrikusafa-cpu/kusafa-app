/**
 * Logika putaran Tilawah Al Qur'an (buku siklik).
 *
 * Aturan (docs/SPEC.md bagian 5.3):
 * - putaran naik 1 HANYA lewat pilihan eksplisit "khatam, mulai putaran baru";
 * - khatam selalu berarti putaran bulan sebelumnya + 1, bukan angka mutlak;
 * - tanpa khatam, capaian yang lebih kecil dari bulan lalu adalah pengulangan (selisih negatif).
 *
 * Posisi dan selisih TIDAK dihitung di sini; keduanya dihitung database
 * (`public.item_position` dan view `v_monthly_report`).
 */

/** Data posisi bulan sebelumnya untuk satu santri di satu bidang. */
export interface DataBulanLalu {
  pos: number | null;
  putaran: number | null;
}

/**
 * Pilihan "khatam, mulai putaran baru" hanya boleh ditawarkan untuk item
 * di buku siklik dan hanya bila putaran bulan sebelumnya diketahui.
 */
export function bolehKhatam(siklik: boolean, bulanLalu: DataBulanLalu | undefined): boolean {
  return siklik && !!bulanLalu && bulanLalu.putaran !== null;
}

/**
 * Putaran yang akan disimpan.
 * - khatam  -> putaran bulan lalu + 1 (tidak pernah angka mutlak).
 * - selain itu -> putaran yang sudah tersimpan, lalu putaran bulan lalu, lalu 1.
 */
export function putaranUntukSimpan(args: {
  khatam: boolean;
  putaranBulanLalu: number | null;
  putaranTersimpan: number | null;
}): number {
  const { khatam, putaranBulanLalu, putaranTersimpan } = args;
  if (khatam) {
    if (putaranBulanLalu === null) {
      throw new Error("Putaran bulan lalu belum ada, jadi khatam belum bisa dihitung.");
    }
    return putaranBulanLalu + 1;
  }
  return putaranTersimpan ?? putaranBulanLalu ?? 1;
}
