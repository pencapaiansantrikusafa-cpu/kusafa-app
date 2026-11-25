import { Navigate, useParams } from "react-router-dom";
import { useAuth } from "../lib/auth-context";
import {
  DOMAIN_LABEL,
  DOMAIN_URUT,
  domainCapaianUntuk,
  navItemsFor,
  type Domain,
} from "../lib/roles";
import TabDomain from "../components/TabDomain";
import TabelCapaian from "./TabelCapaian";

function adalahDomain(v: string | undefined): v is Domain {
  return !!v && (DOMAIN_URUT as string[]).includes(v);
}

/**
 * Halaman Capaian per domain: /capaian/alquran, /capaian/wasilah, /capaian/ghayah.
 *
 * Domain dipilih lewat TAB di bagian atas (komponen bersama `TabDomain`, sama dengan
 * halaman Input). Tab aktif berasal dari URL, sehingga muat ulang dan tombol kembali
 * tetap membuka domain yang sama. Rute yang tidak dikenal atau tidak boleh dilihat
 * role ini dialihkan ke domain pertama yang boleh.
 */
export default function CapaianPage() {
  const { domain } = useParams();
  const { profile } = useAuth();

  if (!profile) return null;
  const item = navItemsFor(profile.role).find((i) => i.key === "capaian");
  if (!item) return <Navigate to="/" replace />;

  const boleh = domainCapaianUntuk(profile.role);
  if (boleh.length === 0) return <Navigate to="/" replace />;

  const aktif: Domain = adalahDomain(domain) && boleh.includes(domain) ? domain : boleh[0];
  if (domain !== undefined && domain !== aktif) {
    return <Navigate to={`/capaian/${aktif}`} replace />;
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Capaian {DOMAIN_LABEL[aktif]}</h1>
        <p className="mt-1 text-sm text-gray-700">{item.description}</p>
      </div>

      <TabDomain
        dasar="/capaian"
        aktif={aktif}
        semua={boleh}
        label="Pilih capaian per domain"
        idPanel="isi-capaian"
      />

      <div id="isi-capaian" role="tabpanel" aria-label={`Capaian ${DOMAIN_LABEL[aktif]}`}>
        <TabelCapaian key={aktif} domain={aktif} />
      </div>
    </div>
  );
}
