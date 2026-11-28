/** Tipe baris laporan bulanan dari view `v_monthly_report`. */
export interface BarisLaporan {
  halaqah_id: string;
  student_id: string;
  subject_id: string;
  month_id: string;
  pos: number | null;
  selisih: number | null;
  hadir: number | null;
  effective_days: number | null;
  target_monthly: number | null;
  below_target: boolean | null;
  attendance_short: boolean | null;
  item_label: string | null;
  prev_item_label: string | null;
  /** Target tujuan akhir (Wasilah/Ghayah): butir + status capaian. */
  target_item_id: string | null;
  target_label: string | null;
  target_pos: number | null;
  target_tercapai: boolean | null;
  target_kurang: number | null;
  target_status: string | null;
}

/** Format angka: bilangan bulat tanpa desimal, pecahan dengan satu desimal. */
export function angka(v: number | null | undefined): string {
  if (v === null || v === undefined) return "";
  return Number.isInteger(v) ? String(v) : v.toFixed(1);
}