import { Navigate, useNavigate, useParams } from "react-router-dom";
import InputAlQuranPage from "./InputAlQuranPage";
import InputWasilahPage from "./InputWasilahPage";
import { useAuth } from "../lib/auth-context";
import { DOMAIN_LABEL, domainInputUntuk, type Domain } from "../lib/roles";

const SEMUA_DOMAIN: Domain[] = ["alquran", "wasilah", "ghayah"];

function adalahDomain(v: string | undefined): v is Domain {
  return !!v && (SEMUA_DOMAIN as string[]).includes(v);
}

/**
 * Halaman Input capaian untuk tiga domain.
 *
 * Rute: `/input` (Al Qur'an, kompatibel dengan tautan lama), `/input/alquran`,
 * `/input/wasilah`, `/input/ghayah`. Ketiganya memakai komponen form yang berbeda
 * karena aturan inputnya berbeda (Al Qur'an individual per santri; Wasilah/Ghayah
 * sekali per halaqah dan mata pelajaran).
 */
export default function InputPage() {
  const { profile } = useAuth();
  const { domain } = useParams();
  const navigate = useNavigate();
  if (!profile) return null;

  const boleh = domainInputUntuk(profile.role);
  if (boleh.length === 0) return <Navigate to="/" replace />;
  const aktif: Domain = adalahDomain(domain) && boleh.includes(domain) ? domain : boleh[0];

  // Tab lain diarahkan ke domain pertama yang boleh (mis. Masul Wasilah membuka /input).
  if (adalahDomain(domain) && domain !== aktif) {
    return <Navigate to={aktif === "alquran" ? "/input/alquran" : `/input/${aktif}`} replace />;
  }
  if (!adalahDomain(domain) && boleh[0] !== "alquran") {
    return <Navigate to={`/input/${boleh[0]}`} replace />;
  }

  if (aktif === "alquran") {
    // Pemilih domain tetap ditampilkan agar pengguna bisa berpindah tanpa kembali ke menu.
    return (
      <div className="space-y-4">
        <PemilihDomain
          aktif={aktif}
          semua={boleh}
          onPilih={(d) => navigate(d === "alquran" ? "/input/alquran" : `/input/${d}`)}
        />
        <InputAlQuranPage />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <PemilihDomain
        aktif={aktif}
        semua={boleh}
        onPilih={(d) => navigate(d === "alquran" ? "/input/alquran" : `/input/${d}`)}
      />
      <InputWasilahPage key={aktif} domain={aktif} />
    </div>
  );
}

/** Tiga tombol domain; hanya domain yang boleh diinput role ini yang ditawarkan (lihat roles.ts). */
function PemilihDomain({
  aktif,
  semua,
  onPilih,
}: {
  aktif: Domain;
  /** Domain yang boleh diinput role ini. */
  semua: Domain[];
  onPilih: (d: Domain) => void;
}) {
  if (semua.length < 2) return null;
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Pilih domain input">
      {SEMUA_DOMAIN.filter((d) => semua.includes(d)).map((d) => {
        const dipilih = d === aktif;
        return (
          <button
            key={d}
            role="tab"
            aria-selected={dipilih}
            onClick={() => onPilih(d)}
            className={
              "rounded-lg px-3 py-1.5 text-sm font-medium ring-1 " +
              (dipilih
                ? "bg-kusafa text-white ring-kusafa"
                : "bg-white text-gray-700 ring-black/10 hover:bg-gray-50")
            }
          >
            {DOMAIN_LABEL[d]}
          </button>
        );
      })}
    </div>
  );
}
