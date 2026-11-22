import { useAuth } from "../lib/auth-context";
import { DOMAIN_LABEL, navItemsFor, type Domain } from "../lib/roles";
import TabelCapaian from "./TabelCapaian";

/** Sub-tab per domain di halaman Capaian. */
const DOMAIN_TABS: Domain[] = ["alquran", "wasilah", "ghayah"];

export default function CapaianPage() {
  const { profile } = useAuth();
  if (!profile) return null;
  const item = navItemsFor(profile.role).find((i) => i.key === "capaian")!;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{item.label}</h1>
        <p className="mt-1 text-sm text-gray-700">{item.description}</p>
      </div>

      {DOMAIN_TABS.map((d) => (
        <section key={d} aria-labelledby={`judul-${d}`}>
          <h2 id={`judul-${d}`} className="sr-only">
            {DOMAIN_LABEL[d]}
          </h2>
          <TabelCapaian domain={d} />
        </section>
      ))}
    </div>
  );
}