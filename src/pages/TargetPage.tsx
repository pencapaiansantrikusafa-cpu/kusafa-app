import { Navigate, useParams } from "react-router-dom";
import TabDomain from "../components/TabDomain";
import { useAuth } from "../lib/auth-context";
import { DOMAIN_LABEL, DOMAIN_URUT, domainInputUntuk, navItemsFor, type Domain } from "../lib/roles";
import TargetDomainPage from "./TargetDomainPage";

function adalahDomain(v: string | undefined): v is Domain {
  return !!v && (DOMAIN_URUT as string[]).includes(v);
}

/**
 * Halaman Target (T7 [2/2]).
 *
 * Rute: `/target` (domain pertama yang boleh), `/target/alquran`, `/target/wasilah`,
 * `/target/ghayah`. Domain dipilih lewat TAB (komponen bersama `TabDomain`), sama
 * seperti halaman Capaian dan Input, sehingga tab aktif tercermin di URL.
 *
 * Domain yang ditawarkan mengikuti hak mengajukan/menyetujui target role ini
 * (`domainInputUntuk`): Mudir/Admin ketiga domain, Masul hanya domainnya,
 * Musyrif/ah Al Qur'an, Mudarris/ah Ilmu Wasilah dan Ilmu Ghayah.
 */
export default function TargetPage() {
  const { profile } = useAuth();
  const { domain } = useParams();

  if (!profile) return null;
  const item = navItemsFor(profile.role).find((i) => i.key === "target");
  if (!item) return <Navigate to="/" replace />;

  const boleh = domainInputUntuk(profile.role);
  if (boleh.length === 0) return <Navigate to="/" replace />;

  const aktif: Domain = adalahDomain(domain) && boleh.includes(domain) ? domain : boleh[0];

  if (domain !== undefined && domain !== aktif) {
    return <Navigate to={`/target/${aktif}`} replace />;
  }
  if (domain === undefined) {
    return <Navigate to={`/target/${aktif}`} replace />;
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Target {DOMAIN_LABEL[aktif]}</h1>
        <p className="mt-1 text-sm text-gray-700">{item.description}</p>
      </div>

      <TabDomain
        dasar="/target"
        aktif={aktif}
        semua={boleh}
        label={`Pilih target per domain, ${DOMAIN_LABEL[aktif]}`}
        idPanel="isi-target"
      />

      <div id="isi-target" role="tabpanel" aria-label={`Target ${DOMAIN_LABEL[aktif]}`}>
        <TargetDomainPage key={aktif} domain={aktif} />
      </div>
    </div>
  );
}
