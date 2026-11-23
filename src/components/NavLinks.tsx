import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import type { NavItem, NavKey } from "../lib/roles";

/** Ikon sederhana (SVG sebaris) untuk tiap menu. Tidak memakai pustaka tambahan. */
export function Ikon({ navKey, className }: { navKey: NavKey; className?: string }) {
  const c = className ?? "h-5 w-5";
  const common = {
    className: c,
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    viewBox: "0 0 24 24",
    "aria-hidden": true,
  };
  switch (navKey) {
    case "capaian":
      return (
        <svg {...common}>
          <path d="M4 19V9m5 10V5m5 14v-7m5 7V11" />
        </svg>
      );
    case "input":
      return (
        <svg {...common}>
          <path d="M12 20h9" />
          <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
        </svg>
      );
    case "target":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      );
    case "kurikulum":
      return (
        <svg {...common}>
          <path d="M4 5a2 2 0 0 1 2-2h11v18H6a2 2 0 0 1-2-2Z" />
          <path d="M8 7h6M8 11h6" />
        </svg>
      );
    case "halaqah":
      return (
        <svg {...common}>
          <circle cx="9" cy="8" r="3" />
          <circle cx="17" cy="10" r="2" />
          <path d="M3 20c0-3 3-5 6-5s6 2 6 5M15 20c0-2 2-3 3.5-3S22 18 22 20" />
        </svg>
      );
    case "pengaturan":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2v3m0 14v3M4.2 4.2l2.1 2.1m11.4 11.4 2.1 2.1M2 12h3m14 0h3M4.2 19.8l2.1-2.1m11.4-11.4 2.1-2.1" />
        </svg>
      );
  }
}

/** Apakah suatu menu sedang aktif (termasuk sub-halamannya). */
export function menuAktif(item: NavItem, pathname: string): boolean {
  const akar = item.path.split("/").slice(0, 2).join("/") + "/";
  return pathname === item.path || pathname.startsWith(akar);
}

/** Apakah path cocok dengan submenu tertentu. */
export function subAktif(path: string, pathname: string): boolean {
  return pathname === path;
}

interface Props {
  items: NavItem[];
  /** true = hanya ikon (lebar sempit). */
  ringkas?: boolean;
  onNavigate?: () => void;
}

/**
 * Daftar menu (menu samping desktop).
 * Menu bertingkat (Capaian) dibuka/tutup dengan mengetuk menunya, tidak tampil terus.
 */
export default function NavLinks({ items, ringkas = false, onNavigate }: Props) {
  const { pathname } = useLocation();
  // Menu yang submenunya sedang dibuka. Semula tidak ada.
  const [terbuka, setTerbuka] = useState<string | null>(null);

  // Bila pengguna mengetuk submenu, submenu ikut menutup.
  function pilihSub() {
    setTerbuka(null);
  }

  // Submenu hanya dibuka oleh pengguna, tidak otomatis mengikuti halaman.
  // (Dulu otomatis terbuka saat halaman dibuka, membuat submenu menetap.)

  return (
    <nav aria-label="Menu utama" className="space-y-1">
      {items.map((item) => {
        const aktif = menuAktif(item, pathname);
        const punyaAnak = !!item.children?.length;
        const bukaSub = punyaAnak && terbuka === item.key;

        const kelas =
          "flex w-full items-center rounded-lg text-sm font-medium transition " +
          (ringkas ? "justify-center px-2 py-2.5 " : "gap-2.5 px-3 py-2 ") +
          (aktif
            ? "bg-kusafa text-white"
            : "text-gray-700 hover:bg-kusafa-light hover:text-kusafa");

        const isi = (
          <>
            <Ikon navKey={item.key} />
            {!ringkas && <span className="flex-1 text-left">{item.label}</span>}
            {!ringkas && punyaAnak && (
              <span aria-hidden className="text-xs opacity-80">
                {bukaSub ? "▾" : "▸"}
              </span>
            )}
          </>
        );

        return (
          <div key={item.key} className={ringkas ? "relative" : undefined}>
            {punyaAnak ? (
              <button
                type="button"
                onClick={() => setTerbuka((v) => (v === item.key ? null : item.key))}
                aria-expanded={bukaSub}
                aria-controls={`submenu-${item.key}`}
                title={item.label}
                className={kelas}
              >
                {isi}
              </button>
            ) : (
              <Link
                to={item.path}
                onClick={onNavigate}
                title={item.label}
                aria-current={aktif ? "page" : undefined}
                aria-label={item.label}
                className={kelas}
              >
                {isi}
              </Link>
            )}

            {bukaSub && item.children && (
              <ul
                id={`submenu-${item.key}`}
                // Mode ikon: submenu melayang ke samping dan harus MENUTUPI isi halaman.
                // Lapisan naik di atas kartu/isi halaman (z-50 > z-30 dropdown, z-20 header),
                // beririsan 8px dengan tombolnya agar tidak ada celah saat kursor bergerak,
                // dan diberi latar putih + bayangan supaya jelas berada di depan.
                className={
                  ringkas
                    ? "absolute left-full top-0 z-50 -ml-2 w-44 rounded-lg border border-black/10 bg-white p-1 shadow-xl"
                    : "relative z-10 mt-1 ml-2 space-y-0.5 rounded-lg border-l border-kusafa/20 py-1 pl-3"
                }
              >
                {item.children.map((c) => {
                  const sa = subAktif(c.path, pathname);
                  return (
                    <li key={c.path}>
                      <Link
                        to={c.path}
                        onClick={pilihSub}
                        aria-current={sa ? "page" : undefined}
                        className={
                          "block rounded-md px-2 py-1.5 text-[13px] " +
                          (sa
                            ? "bg-kusafa-light font-semibold text-kusafa"
                            : "text-gray-600 hover:bg-gray-100")
                        }
                      >
                        {c.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        );
      })}
    </nav>
  );
}