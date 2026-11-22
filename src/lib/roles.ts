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
}

/**
 * Menu yang tampil untuk sebuah role, mengikuti docs/SPEC.md bagian 3.
 * Ini hanya kenyamanan tampilan: penjagaan sebenarnya ada di RLS database.
 */
export function navItemsFor(role: AppRole): NavItem[] {
  const capaian: NavItem = {
    key: "capaian",
    label: "Capaian",
    path: "/capaian",
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