import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth-context";
import { ROLE_LABEL, navItemsFor } from "../lib/roles";
import NavLinks, { Ikon } from "./NavLinks";

const KUNCI_MENU = "kusafa:menu-ringkas";

/**
 * Kerangka aplikasi setelah login.
 * - Desktop: header + menu samping (bisa dilipat jadi ikon saja) + isi.
 * - HP: header + isi + bilah menu di bawah (bottom bar).
 */
export default function AppLayout() {
  const { profile, signOut } = useAuth();
  const [ringkas, setRingkas] = useState<boolean>(() => {
    try {
      return localStorage.getItem(KUNCI_MENU) === "1";
    } catch {
      return false;
    }
  });
  const navigate = useNavigate();

  useEffect(() => {
    try {
      localStorage.setItem(KUNCI_MENU, ringkas ? "1" : "0");
    } catch {
      /* localStorage bisa diblokir; abaikan */
    }
  }, [ringkas]);

  if (!profile) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <h1 className="text-lg font-bold text-kusafa">Akun belum siap</h1>
        <p className="mt-2 text-sm text-gray-700">
          Anda berhasil masuk, tetapi profil Anda belum ada atau belum aktif.
          Hubungi Admin agar akun ini diaktifkan dan diberi role.
        </p>
        <button
          onClick={() => void signOut()}
          className="mt-4 rounded-lg bg-kusafa px-4 py-2 text-sm font-medium text-white hover:bg-kusafa/90"
        >
          Keluar
        </button>
      </main>
    );
  }

  const items = navItemsFor(profile.role);
  const { pathname } = useLocation();
  // Bilah bawah: submenu hanya terbuka untuk menu yang Diketuk, di halaman mana pun.
  const [subBawahKey, setSubBawahKey] = useState<string | null>(null);
  const menuSubBawah = subBawahKey ? items.find((i) => i.key === subBawahKey) : undefined;
  const subBawah = menuSubBawah?.children ?? [];

  async function keluar() {
    await signOut();
    navigate("/", { replace: true });
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-20 border-b border-black/5 bg-white">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-base font-bold text-kusafa">KUSAFA</p>
            <p className="truncate text-xs text-gray-600">
              {profile.full_name} · {ROLE_LABEL[profile.role]}
            </p>
          </div>
          <button
            onClick={() => void keluar()}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            Keluar
          </button>
        </div>
      </header>

      <div className="flex w-full gap-4 px-3 py-4 pb-24 lg:pb-4">
        <aside className={"hidden shrink-0 lg:block " + (ringkas ? "w-16" : "w-56")}>
          <div className="sticky top-20 space-y-2">
            <button
              onClick={() => setRingkas((v) => !v)}
              className="flex w-full items-center justify-center rounded-lg border border-gray-300 px-2 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
              aria-pressed={ringkas}
              title={ringkas ? "Tampilkan teks menu" : "Sembunyikan teks menu"}
            >
              {ringkas ? "»" : "« Ikon saja"}
            </button>
            <NavLinks items={items} ringkas={ringkas} />
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          {items.length === 0 ? (
            <div className="rounded-xl bg-white p-6 ring-1 ring-black/5">
              <h1 className="text-lg font-bold text-gray-900">Akses belum tersedia</h1>
              <p className="mt-2 text-sm text-gray-700">
                Role Anda belum memiliki menu. Fitur wali santri masih disiapkan.
              </p>
            </div>
          ) : (
            <Outlet context={{ defaultPath: items[0]?.path ?? "/" }} />
          )}
        </main>
      </div>

      {/* Bilah menu bawah untuk HP; desktop memakai menu samping. */}
      {items.length > 0 && (
        <nav
          aria-label="Menu bawah"
          className="fixed inset-x-0 bottom-0 z-30 border-t border-black/10 bg-white pb-[env(safe-area-inset-bottom)] lg:hidden"
        >
          {/* Submenu hanya muncul setelah menu bertingkat diketuk. */}
          {subBawah.length > 0 && (
            <div className="flex gap-1 overflow-x-auto border-b border-black/5 px-2 py-1.5">
              {subBawah.map((c) => {
                const aktif = pathname === c.path;
                return (
                  <Link
                    key={c.path}
                    to={c.path}
                    onClick={() => setSubBawahKey(null)}
                    aria-current={aktif ? "page" : undefined}
                    className={
                      "shrink-0 rounded-full px-3 py-1 text-xs font-medium " +
                      (aktif ? "bg-kusafa text-white" : "bg-gray-100 text-gray-700")
                    }
                  >
                    {c.label}
                  </Link>
                );
              })}
            </div>
          )}
          <ul className="grid grid-flow-col auto-cols-fr">
            {items.map((item) => (
              <li key={item.key}>
                {!item.children?.length ? (
                <NavLink
                  to={item.path}
                  aria-current={pathname.startsWith(item.path.split("/").slice(0, 2).join("/")) ? "page" : undefined}
                  className={({ isActive }) =>
                    "flex flex-col items-center gap-0.5 px-1 py-2 text-[11px] leading-tight " +
                    (isActive || pathname.startsWith(item.path.split("/").slice(0, 2).join("/"))
                      ? "text-kusafa font-semibold"
                      : "text-gray-600")
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={
                          "flex h-7 w-7 items-center justify-center rounded-lg " +
                          (isActive ? "bg-kusafa-light" : "")
                        }
                      >
                        <Ikon navKey={item.key} className="h-4.5 w-4.5" />
                      </span>
                      <span className="text-center">{item.label}</span>
                    </>
                  )}
                </NavLink>
                ) : (
                  <button
                    type="button"
                    onClick={() => setSubBawahKey((v) => (v === item.key ? null : item.key))}
                    aria-expanded={subBawahKey === item.key}
                    className={
                      "flex w-full flex-col items-center gap-0.5 px-1 py-2 text-[11px] leading-tight " +
                      (pathname.startsWith(item.path.split("/").slice(0, 2).join("/"))
                        ? "text-kusafa font-semibold"
                        : "text-gray-600")
                    }
                  >
                    <span
                      className={
                        "flex h-7 w-7 items-center justify-center rounded-lg " +
                        (pathname.startsWith(item.path.split("/").slice(0, 2).join("/")) ? "bg-kusafa-light" : "")
                      }
                    >
                      <Ikon navKey={item.key} className="h-4.5 w-4.5" />
                    </span>
                    <span className="text-center">
                      {item.label} <span aria-hidden>{subBawahKey === item.key ? "▴" : "▾"}</span>
                    </span>
                  </button>
                )}
              </li>
            ))}
          </ul>
        </nav>
      )}
    </div>
  );
}