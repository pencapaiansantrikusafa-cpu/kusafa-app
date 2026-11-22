import { Navigate, useParams } from "react-router-dom";
import { useAuth } from "../lib/auth-context";
import { DOMAIN_LABEL, navItemsFor, type Domain } from "../lib/roles";
import TabelCapaian from "./TabelCapaian";

const DOMAINS: Domain[] = ["alquran", "wasilah", "ghayah"];

function adalahDomain(v: string | undefined): v is Domain {
  return !!v && (DOMAINS as string[]).includes(v);
}

/**
 * Halaman Capaian per domain: /capaian/alquran, /capaian/wasilah, /capaian/ghayah.
 */
export default function CapaianPage() {
  const { domain } = useParams();
  const { profile } = useAuth();

  if (!profile) return null;
  const item = navItemsFor(profile.role).find((i) => i.key === "capaian");
  if (!item) return <Navigate to="/" replace />;
  if (!adalahDomain(domain)) return <Navigate to="/capaian/alquran" replace />;

  const sub = item.children?.find((c) => c.path === `/capaian/${domain}`);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          Capaian {DOMAIN_LABEL[domain]}
        </h1>
        <p className="mt-1 text-sm text-gray-700">
          {sub?.label ? `${sub.label} · ` : ""}
          {item.description}
        </p>
      </div>

      <TabelCapaian key={domain} domain={domain} />
    </div>
  );
}