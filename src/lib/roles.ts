// Tipe dan label role KUSAFA.
// Nama role ditulis lengkap: Masul Al Quran, Masul Wasilah, Masul Ghayah.

export type AppRole =
  | "mudir"
  | "admin"
  | "masul_alquran"
  | "masul_wasilah"
  | "masul_ghayah"
  | "musyrif"
  | "mudarris"
  | "wali";

export type Domain = "alquran" | "wasilah" | "ghayah";

export const ROLE_LABEL: Record<AppRole, string> = {
  mudir: "Mudir",
  admin: "Admin",
  masul_alquran: "Masul Al Quran",
  masul_wasilah: "Masul Wasilah",
  masul_ghayah: "Masul Ghayah",
  musyrif: "Musyrif/ah",
  mudarris: "Mudarris/ah",
  wali: "Wali Santri",
};

/** Urutan baku domain di seluruh aplikasi (tab, menu, laporan). */
export const DOMAIN_URUT: Domain[] = ["alquran", "wasilah", "ghayah"];

export const DOMAIN_LABEL: Record<Domain, string> = {
  alquran: "Al Qur'an",
  wasilah: "Ilmu Wasilah",
  ghayah: "Ilmu Ghayah",
};

export interface Profile {
  id: string;
  full_name: string;
  role: AppRole;
  gender: "L" | "P" | null;
  is_active: boolean;
}

export type NavKey =
  | "capaian"
  | "input"
  | "target"
  | "kurikulum"
  | "halaqah"
  | "pengaturan";

export interface NavItem {
  key: NavKey;
  label: string;
  path: string;
  description: string;
  /** Submenu; dipakai untuk memisahkan Capaian per domain. */
  children?: { label: string; path: string }[];
}

/**
 * Apakah role ini hanya boleh MENULIS capaian/kehadiran/catatan pada halaqah
 * yang diampu (docs/SPEC.md bagian 3)? Berdasarkan keputusan Mudir 25 Nov 2026
 * (T6d2) hanya **Musyrif/ah dan Mudarris/ah**; ketiga **Masul** boleh menulis di
 * SEMUA halaqah domainnya (lihat `bolehInputDomain`). Mudir/Admin semua halaqah.
 *
 * Database tetap penjaga terakhir (RLS `student_in_taught_halaqah`); ini hanya
 * agar tampilan tidak menawarkan halaqah di luar amanah.
 */
export function hanyaHalaqahDiampu(role: AppRole): boolean {
  return role === "musyrif" || role === "mudarris";
}

/**
 * Apakah role ini boleh INPUT di SEMUA halaqah domain tertentu (bukan hanya yang diampu).
 * Mudir/Admin: semua domain. Masul: hanya domainnya sendiri (keputusan Mudir 25 Nov 2026).
 * Database tetap penjaga terakhir (policy `progress_*`, `attendance_*`, `notes_*`).
 */
export function bolehInputDomain(role: AppRole, domain: Domain): boolean {
  if (role === "mudir" || role === "admin") return true;
  if (role === "masul_alquran") return domain === "alquran";
  if (role === "masul_wasilah") return domain === "wasilah";
  if (role === "masul_ghayah") return domain === "ghayah";
  return false;
}

/**
 * Domain yang boleh DILIHAT/DIPILIH di halaman Input untuk role ini (docs/SPEC.md bagian 3).
 * Mudir/Admin: semua. Masul Al Quran hanya Al Qur'an, Masul Wasilah hanya Ilmu Wasilah,
 * Masul Ghayah hanya Ilmu Ghayah. Musyrif/ah mengampu Al Qur'an; Mudarris/ah mengampu
 * Wasilah/Ghayah. Database tetap penjaga terakhir (RLS + cek di dalam fungsi).
 */
export function domainInputUntuk(role: AppRole): Domain[] {
  switch (role) {
    case "mudir":
    case "admin":
      return ["alquran", "wasilah", "ghayah"];
    case "masul_alquran":
      return ["alquran"];
    case "masul_wasilah":
      return ["wasilah"];
    case "masul_ghayah":
      return ["ghayah"];
    case "musyrif":
      return ["alquran"];
    case "mudarris":
      return ["wasilah", "ghayah"];
    default:
      return [];
  }
}

/**
 * Domain yang boleh DILIHAT di halaman Capaian untuk role ini.
 *
 * Ini **bukan aturan akses baru**: ketiga domain memang sudah dapat dibaca semua staf
 * (RLS `progress_read`/`halaqahs_read`/`students_read` memakai `is_staff()`, dan menu
 * Capaian sejak awal menampilkan ketiga submenu untuk semua role). Fungsi ini hanya
 * memusatkan aturan itu supaya tab tidak pernah menawarkan domain yang tidak boleh.
 * Bila kelak Capaian dibatasi per domain, cukup ubah fungsi ini dan RLS-nya bersama.
 */
export function domainCapaianUntuk(role: AppRole): Domain[] {
  return navItemsFor(role).some((i) => i.key === "capaian") ? [...DOMAIN_URUT] : [];
}

/** Pemberitahuan "data belum lengkap" dibatasi ke halaqah sendiri untuk guru pengampu. */
export function batasiPemberitahuan(role: AppRole): boolean {
  return role === "musyrif" || role === "mudarris";
}

/** Siapa yang boleh melihat pemberitahuan "data belum lengkap" seluruh sekolah. */
export function isPeninjau(role: AppRole): boolean {
  return role === "mudir" || role === "admin" || role.startsWith("masul_");
}

/** Mudir/Admin: akses penuh (semua halaqah, semua domain, boleh lewati bulan terkunci). */
export function adalahAksesPenuh(role: AppRole): boolean {
  return role === "mudir" || role === "admin";
}

/**
 * Siapa yang boleh MENYETUJUI/MENOLAK target untuk sebuah domain (keputusan T7 3.2a):
 * Mudir/Admin semua domain; Masul hanya domainnya sendiri
 * (Masul Al Quran → Al Qur'an, Masul Wasilah → Ilmu Wasilah, Masul Ghayah → Ilmu Ghayah).
 * Pengampu (Musyrif/ah, Mudarris/ah) tidak menyetujui. Database tetap penjaga terakhir
 * (RPC `setujui_target`/`tolak_target` memeriksa `is_full_access()` / `is_masul_of()`).
 */
export function bolehSetujuiTarget(role: AppRole, domain: Domain): boolean {
  if (adalahAksesPenuh(role)) return true;
  if (role === "masul_alquran") return domain === "alquran";
  if (role === "masul_wasilah") return domain === "wasilah";
  if (role === "masul_ghayah") return domain === "ghayah";
  return false;
}

/**
 * Menu yang tampil untuk sebuah role, mengikuti docs/SPEC.md bagian 3.
 * Ini hanya kenyamanan tampilan: penjagaan sebenarnya ada di RLS database.
 */
export function navItemsFor(role: AppRole): NavItem[] {
  // Capaian tidak lagi memakai submenu: ketiga domain dipilih lewat TAB di dalam
  // halaman (komponen `TabDomain`), sama seperti halaman Input.
  const capaian: NavItem = {
    key: "capaian",
    label: "Capaian",
    path: "/capaian/alquran",
    description: "Melihat capaian santri per halaqah dan bulan.",
  };
  const input: NavItem = {
    key: "input",
    label: "Input",
    path: "/input",
    description: "Mengisi capaian, kehadiran, dan catatan bulanan.",
  };
  const target: NavItem = {
    key: "target",
    label: "Target",
    path: "/target",
    description: "Mengajukan dan menyetujui target santri.",
  };
  const kurikulum: NavItem = {
    key: "kurikulum",
    label: "Kurikulum",
    path: "/kurikulum",
    description: "Mengelola bidang, buku, dan item dropdown.",
  };
  const halaqah: NavItem = {
    key: "halaqah",
    label: "Halaqah & Santri",
    path: "/halaqah",
    description: "Mengelola halaqah, anggota, pengampu, dan santri.",
  };
  const pengaturan: NavItem = {
    key: "pengaturan",
    label: "Pengaturan",
    path: "/pengaturan",
    description: "Hari Efektif, kunci bulan, tahun ajaran, dan pengguna.",
  };

  switch (role) {
    // Mudir dan Admin: semua menu.
    case "mudir":
    case "admin":
      return [capaian, input, target, kurikulum, halaqah, pengaturan];
    // Masul: melihat semua, input halaqah yang diampu, menyetujui target domainnya,
    // kurikulum domainnya. Hari Efektif, kunci bulan, dan pengguna bukan wewenangnya.
    case "masul_alquran":
    case "masul_wasilah":
    case "masul_ghayah":
      return [capaian, input, target, kurikulum, halaqah];
    // Musyrif/ah dan Mudarris/ah: melihat semua, input dan ajukan target di halaqahnya.
    case "musyrif":
    case "mudarris":
      return [capaian, input, target];
    // Role wali belum aktif (docs/SPEC.md bagian 7).
    case "wali":
      return [];
  }
}