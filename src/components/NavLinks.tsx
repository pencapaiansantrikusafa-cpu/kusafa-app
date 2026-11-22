import { Link, useLocation } from "react-router-dom";
import type { NavItem } from "../lib/roles";

interface Props {
  items: NavItem[];
  onNavigate?: () => void;
}

/** Daftar menu; dipakai di sidebar (desktop) dan panel menu (HP). */
export default function NavLinks({ items, onNavigate }: Props) {
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
            aria-current={aktif ? "page" : undefined}
            className={
              "block rounded-lg px-3 py-2 text-sm font-medium transition " +
              (aktif
                ? "bg-kusafa text-white"
                : "text-gray-700 hover:bg-kusafa-light hover:text-kusafa")
            }
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}