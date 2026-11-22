import { useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth-context";
import { ROLE_LABEL, navItemsFor } from "../lib/roles";
import NavLinks from "./NavLinks";

/** Kerangka aplikasi setelah login: header, menu sesuai role, dan isi halaman. */
export default function AppLayout() {
  const { profile, signOut } = useAuth();
  const [menuTerbuka, setMenuTerbuka] = useState(false);
  const navigate = useNavigate();

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
  const pertama = items[0];

  async function keluar() {
    await signOut();
    navigate("/", { replace: true });
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-20 border-b border-black/5 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <button
            className="rounded-lg border border-gray-300 px-2.5 py-1.5 text-sm lg:hidden"
            onClick={() => setMenuTerbuka((v) => !v)}
            aria-expanded={menuTerbuka}
            aria-controls="menu-hp"
          >
            Menu
          </button>

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

        {menuTerbuka && (
          <div id="menu-hp" className="border-t border-black/5 px-4 py-3 lg:hidden">
            <NavLinks items={items} onNavigate={() => setMenuTerbuka(false)} />
          </div>
        )}
      </header>

      <div className="mx-auto flex max-w-6xl gap-6 px-4 py-6">
        <aside className="hidden w-56 shrink-0 lg:block">
          <NavLinks items={items} />
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
            <Outlet context={{ defaultPath: pertama?.path ?? "/" }} />
          )}
        </main>
      </div>
    </div>
  );
}