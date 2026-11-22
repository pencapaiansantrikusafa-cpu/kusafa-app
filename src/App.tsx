import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./lib/auth-context";
import { navItemsFor } from "./lib/roles";
import LoginPage from "./pages/LoginPage";
import CapaianPage from "./pages/CapaianPage";
import SantriPage from "./pages/SantriPage";
import InputPage from "./pages/InputPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import AppLayout from "./components/AppLayout";

function Memuat() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <p className="text-sm text-gray-600">Memuat...</p>
    </main>
  );
}

/** Rute awal sesuai role: cari menu pertama yang tersedia. */
function Beranda() {
  const { profile } = useAuth();
  if (!profile) return <Navigate to="/" replace />;
  const pertama = navItemsFor(profile.role)[0];
  return <Navigate to={pertama ? pertama.path : "/"} replace />;
}

export default function App() {
  const { profile, loading } = useAuth();

  if (loading) return <Memuat />;
  if (!profile) return <LoginPage />;

  const items = navItemsFor(profile.role);

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Beranda />} />
        <Route path="capaian" element={<Navigate to="/capaian/alquran" replace />} />
        <Route path="capaian/:domain" element={<CapaianPage />} />
        <Route path="santri/:id" element={<SantriPage />} />
        <Route path="input" element={<InputPage />} />
        {items
          .filter((i) => i.key !== "capaian" && i.key !== "input")
          .map((i) => (
            <Route
              key={i.key}
              path={i.path.replace(/^\//, "")}
              element={<PlaceholderPage item={i} roleLabel={profile.full_name} />}
            />
          ))}
        <Route path="*" element={<Beranda />} />
      </Route>
    </Routes>
  );
}