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
 * yang diampu (docs/SPEC.md bagian 3)? Berlaku untuk Masul, Musyrif/ah, dan
 * Mudarris/ah. Hanya Mudir/Admin yang boleh menulis semua halaqah.
 *
 * Database tetap penjaga terakhir (RLS `student_in_taught_halaqah`); ini hanya
 * agar tampilan tidak menawarkan halaqah di luar amanah.
 */
export function hanyaHalaqahDiampu(role: AppRole): boolean {
  return (
    role === "masul_alquran" ||
    role === "masul_wasilah" ||
    role === "masul_ghayah" ||
    role === "musyrif" ||
    role === "mudarris"
  );
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

/** Pemberitahuan "data belum lengkap" dibatasi ke halaqah sendiri untuk guru pengampu. */
export function batasiPemberitahuan(role: AppRole): boolean {
  return role === "musyrif" || role === "mudarris";
}

/** Siapa yang boleh melihat pemberitahuan "data belum lengkap" seluruh sekolah. */
export function isPeninjau(role: AppRole): boolean {
  return role === "mudir" || role === "admin" || role.startsWith("masul_");
}

/**
 * Menu yang tampil untuk sebuah role, mengikuti docs/SPEC.md bagian 3.
 * Ini hanya kenyamanan tampilan: penjagaan sebenarnya ada di RLS database.
 */
export function navItemsFor(role: AppRole): NavItem[] {
  const capaian: NavItem = {
    key: "capaian",
    label: "Capaian",
    path: "/capaian/alquran",
    description: "Melihat capaian santri per halaqah dan bulan.",
    children: [
      { label: "Al Qur'an", path: "/capaian/alquran" },
      { label: "Ilmu Wasilah", path: "/capaian/wasilah" },
      { label: "Ilmu Ghayah", path: "/capaian/ghayah" },
    ],
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