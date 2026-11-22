import { Link, useLocation } from "react-router-dom";
import type { NavItem, NavKey } from "../lib/roles";

/** Ikon sederhana (SVG sebaris) untuk tiap menu. Tidak memakai pustaka tambahan. */
function Ikon({ navKey, className }: { navKey: NavKey; className?: string }) {
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

interface Props {
  items: NavItem[];
  /** true = hanya ikon (lebar sempit). */
  ringkas?: boolean;
  onNavigate?: () => void;
}

/**
 * Daftar menu; dipakai di samping (desktop) dan panel menu (HP).
 * Saat `ringkas`, hanya ikon tampil dan nama menu muncul sebagai tooltip (title).
 */
export default function NavLinks({ items, ringkas = false, onNavigate }: Props) {
  const { pathname } = useLocation();

  return (
    <nav aria-label="Menu utama" className="space-y-1">
      {items.map((item) => {
        const aktif = pathname === item.path || pathname.startsWith(item.path + "/");
        return (
          <Link
            key={item.key}
            to={item.path}
            onClick={onNavigate}
            title={item.label}
            aria-current={aktif ? "page" : undefined}
            aria-label={item.label}
            className={
              "flex items-center rounded-lg text-sm font-medium transition " +
              (ringkas ? "justify-center px-2 py-2.5 " : "gap-2.5 px-3 py-2 ") +
              (aktif
                ? "bg-kusafa text-white"
                : "text-gray-700 hover:bg-kusafa-light hover:text-kusafa")
            }
          >
            <Ikon navKey={item.key} />
            {!ringkas && <span>{item.label}</span>}
          </Link>
        );
      })}
    </nav>
  );
}