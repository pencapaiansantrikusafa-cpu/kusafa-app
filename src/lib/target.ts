/**
 * Lapisan tipis untuk target dinamis (T7).
 *
 * Aturan bisnis target ada di database (RPC + view + RLS). Berkas ini hanya
 * membungkus pemanggilan RPC dan menyeragamkan tipe/label status, JANGAN
 * menghitung target bulanan di sini — `target_monthly` dibaca dari
 * `v_monthly_report` (lihat `src/lib/laporan.ts`).
 *
 * RPC: `ajukan_target`, `ubah_target`, `setujui_target`, `tolak_target`,
 * `batalkan_target`, `ajukan_target_massal_alquran`, `riwayat_target`,
 * `target_info_konfirmasi`.
 */
import { supabase } from "./supabase";
import type { Domain } from "./roles";

export type TargetStatus = "diajukan" | "disetujui" | "ditolak" | "dibatalkan";
export type PeriodeTarget = "harian" | "bulanan";

export const STATUS_LABEL: Record<TargetStatus, string> = {
  diajukan: "Diajukan",
  disetujui: "Disetujui",
  ditolak: "Ditolak",
  dibatalkan: "Dibatalkan",
};

/** Kelas tampilan status; selalu disertai teks (jangan mengandalkan warna saja). */
export const STATUS_GAYA: Record<TargetStatus, string> = {
  diajukan: "bg-amber-100 text-amber-900",
  disetujui: "bg-emerald-50 text-emerald-800",
  ditolak: "bg-red-50 text-red-700",
  dibatalkan: "bg-gray-100 text-gray-600",
};

/** Satu baris tabel `targets` (baca langsung; SELECT terbuka untuk seluruh staf). */
export interface BarisTarget {
  id: string;
  domain: Domain;
  subject_id: string;
  student_id: string | null;
  halaqah_id: string | null;
  effective_month_id: string;
  amount: number;
  amount_period: PeriodeTarget;
  status: TargetStatus;
  proposed_by: string | null;
  approved_by: string | null;
  approved_at: string | null;
  rejected_by: string | null;
  rejected_at: string | null;
  alasan_tolak: string | null;
  note: string | null;
  created_at: string;
}

export interface InfoKonfirmasi {
  month_no: number;
  lewat: boolean;
  terkunci: boolean;
  perlu_konfirmasi: boolean;
}

/** Satu baris riwayat dari RPC `riwayat_target`. */
export interface RiwayatBaris {
  id: string;
  amount: number;
  amount_period: PeriodeTarget;
  status: TargetStatus;
  note: string | null;
  alasan_tolak: string | null;
  effective_month_id: string;
  bulan_berlaku: string;
  month_no: number;
  hijri_year: number;
  proposed_by: string | null;
  pengaju: string | null;
  approved_by: string | null;
  penyetuju: string | null;
  approved_at: string | null;
  rejected_by: string | null;
  penolak: string | null;
  rejected_at: string | null;
  created_at: string;
}

export interface HasilTarget {
  id?: string;
  status?: TargetStatus;
  effective_month_id?: string;
  menggantikan?: string;
  jumlah_santri?: number;
  changed?: boolean;
}

/**
 * Bulan lewat / terkunci perlu konfirmasi eksplisit, dan hanya Mudir/Admin yang
 * boleh melanjutkan (RPC `target_cek_konfirmasi` yang menolak).
 */
export async function infoKonfirmasi(
  domain: Domain,
  bulanId: string,
): Promise<InfoKonfirmasi | null> {
  const { data, error } = await supabase.rpc("target_info_konfirmasi", {
    p_domain: domain,
    p_month_id: bulanId,
  });
  if (error) throw new Error(error.message);
  return (data as unknown as InfoKonfirmasi) ?? null;
}

function kePesan(e: unknown, awalan: string): Error {
  return new Error(`${awalan}: ${e instanceof Error ? e.message : String(e)}`);
}

export async function ajukanTarget(p: {
  domain: Domain;
  subjectId: string;
  studentId?: string | null;
  halaqahId?: string | null;
  bulanId?: string | null;
  amount: number;
  periode: PeriodeTarget;
  note?: string | null;
  konfirmasi?: boolean;
}): Promise<HasilTarget> {
  const { data, error } = await supabase.rpc("ajukan_target", {
    p_domain: p.domain,
    p_subject_id: p.subjectId,
    p_student_id: p.studentId ?? null,
    p_halaqah_id: p.halaqahId ?? null,
    p_effective_month_id: p.bulanId ?? null,
    p_amount: p.amount,
    p_amount_period: p.periode,
    p_note: p.note ?? null,
    p_konfirmasi: p.konfirmasi ?? false,
  });
  if (error) throw kePesan(error, "Gagal mengajukan target");
  return (data as unknown as HasilTarget) ?? {};
}

/** Mengubah target = membuat baris baru; target lama tetap utuh (keputusan T7 3.2b). */
export async function ubahTarget(p: {
  targetLamaId: string;
  amount: number;
  bulanId?: string | null;
  note?: string | null;
  konfirmasi?: boolean;
}): Promise<HasilTarget> {
  const { data, error } = await supabase.rpc("ubah_target", {
    p_target_lama_id: p.targetLamaId,
    p_amount: p.amount,
    p_effective_month_id: p.bulanId ?? null,
    p_note: p.note ?? null,
    p_konfirmasi: p.konfirmasi ?? false,
  });
  if (error) throw kePesan(error, "Gagal mengubah target");
  return (data as unknown as HasilTarget) ?? {};
}

/** Target massal Al Qur'an: satu baris per santri anggota halaqah. */
export async function ajukanTargetMassalAlquran(p: {
  halaqahId: string;
  subjectId: string;
  bulanId?: string | null;
  amount: number;
  note?: string | null;
  konfirmasi?: boolean;
}): Promise<HasilTarget> {
  const { data, error } = await supabase.rpc("ajukan_target_massal_alquran", {
    p_halaqah_id: p.halaqahId,
    p_subject_id: p.subjectId,
    p_effective_month_id: p.bulanId ?? null,
    p_amount: p.amount,
    p_note: p.note ?? null,
    p_konfirmasi: p.konfirmasi ?? false,
  });
  if (error) throw kePesan(error, "Gagal mengajukan target massal");
  return (data as unknown as HasilTarget) ?? {};
}

export async function setujuiTarget(targetId: string, konfirmasi = false): Promise<HasilTarget> {
  const { data, error } = await supabase.rpc("setujui_target", {
    p_target_id: targetId,
    p_konfirmasi: konfirmasi,
  });
  if (error) throw kePesan(error, "Gagal menyetujui target");
  return (data as unknown as HasilTarget) ?? {};
}

/** Alasan penolakan WAJIB (dicek juga di database). */
export async function tolakTarget(
  targetId: string,
  alasan: string,
  konfirmasi = false,
): Promise<HasilTarget> {
  const { data, error } = await supabase.rpc("tolak_target", {
    p_target_id: targetId,
    p_alasan: alasan,
    p_konfirmasi: konfirmasi,
  });
  if (error) throw kePesan(error, "Gagal menolak target");
  return (data as unknown as HasilTarget) ?? {};
}

/** Hanya pengaju, hanya status `diajukan`; target tidak dihapus. */
export async function batalkanTarget(targetId: string): Promise<HasilTarget> {
  const { data, error } = await supabase.rpc("batalkan_target", { p_target_id: targetId });
  if (error) throw kePesan(error, "Gagal membatalkan target");
  return (data as unknown as HasilTarget) ?? {};
}

export async function ambilRiwayat(
  subjectId: string,
  studentId?: string | null,
  halaqahId?: string | null,
): Promise<RiwayatBaris[]> {
  const { data, error } = await supabase.rpc("riwayat_target", {
    p_subject_id: subjectId,
    p_student_id: studentId ?? null,
    p_halaqah_id: halaqahId ?? null,
  });
  if (error) throw kePesan(error, "Gagal memuat riwayat target");
  return ((data as unknown as RiwayatBaris[]) ?? []) ?? [];
}
