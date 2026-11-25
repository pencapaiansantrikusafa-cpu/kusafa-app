import { Navigate, useParams } from "react-router-dom";
import InputAlQuranPage from "./InputAlQuranPage";
import InputWasilahPage from "./InputWasilahPage";
import TabDomain from "../components/TabDomain";
import { useAuth } from "../lib/auth-context";
import { DOMAIN_LABEL, DOMAIN_URUT, domainInputUntuk, type Domain } from "../lib/roles";

function adalahDomain(v: string | undefined): v is Domain {
  return !!v && (DOMAIN_URUT as string[]).includes(v);
}

/**
 * Halaman Input capaian untuk tiga domain.
 *
 * Rute: `/input` (Al Qur'an, kompatibel dengan tautan lama), `/input/alquran`,
 * `/input/wasilah`, `/input/ghayah`. Domain dipilih lewat TAB (komponen bersama
 * `TabDomain`, sama dengan halaman Capaian). Form-nya berbeda karena aturan inputnya
 * berbeda (Al Qur'an individual per santri; Wasilah/Ghayah sekali per halaqah dan
 * mata pelajaran).
 */
export default function InputPage() {
  const { profile } = useAuth();
  const { domain } = useParams();
  if (!profile) return null;

  const boleh = domainInputUntuk(profile.role);
  if (boleh.length === 0) return <Navigate to="/" replace />;

  const aktif: Domain = adalahDomain(domain) && boleh.includes(domain) ? domain : boleh[0];

  // Tab lain / rute tanpa domain diarahkan ke domain pertama yang boleh
  // (mis. Masul Wasilah membuka `/input` -> `/input/wasilah`).
  if (domain !== undefined && domain !== aktif) {
    return <Navigate to={`/input/${aktif}`} replace />;
  }
  if (domain === undefined && boleh[0] !== "alquran") {
    return <Navigate to={`/input/${boleh[0]}`} replace />;
  }

  return (
    <div className="space-y-4">
      <TabDomain
        dasar="/input"
        aktif={aktif}
        semua={boleh}
        label={`Pilih domain input, ${DOMAIN_LABEL[aktif]}`}
        idPanel="isi-input"
      />
      <div id="isi-input" role="tabpanel" aria-label={`Input ${DOMAIN_LABEL[aktif]}`}>
        {aktif === "alquran" ? (
          <InputAlQuranPage />
        ) : (
          <InputWasilahPage key={aktif} domain={aktif} />
        )}
      </div>
    </div>
  );
}
