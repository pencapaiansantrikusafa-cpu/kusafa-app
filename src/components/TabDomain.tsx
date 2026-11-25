import { Link } from "react-router-dom";
import { DOMAIN_LABEL, type Domain } from "../lib/roles";

interface Props {
  /**
   * Awalan rute, tanpa garis miring di ujung: `/input` atau `/capaian`.
   * Tiap tab menuju `${dasar}/${domain}`, sehingga tab aktif selalu tercermin di URL
   * (muat ulang dan tombol kembali bekerja tanpa keadaan tersembunyi di memori).
   */
  dasar: "/input" | "/capaian";
  /** Domain yang sedang dibuka (dari URL). */
  aktif: Domain;
  /** Domain yang boleh dipakai role ini, dalam urutan baku. */
  semua: Domain[];
  /** Nama kumpulan tab untuk pembaca layar, mis. "Pilih domain input". */
  label: string;
  /** id panel isi, agar tab terhubung ke isinya (`aria-controls`). */
  idPanel?: string;
}

/**
 * Tab pemilih domain (Al Qur'an, Ilmu Wasilah, Ilmu Ghayah).
 *
 * Komponen bersama halaman Input dan halaman Capaian — sengaja satu berkas supaya
 * gaya, urutan, dan perilakunya tidak menyimpang di antara kedua halaman.
 *
 * Tampilan:
 * - HP (360 px): tiga tab dibagi rata selebar layar (tiga kolom), tinggi sentuh 44 px,
 *   teks tidak terpotong dan halaman tidak bergeser ke samping.
 * - Desktop (sm ke atas): tombol sebaris dengan lebar sesuai isi.
 *
 * Bila hanya satu domain yang boleh, bilah tab tidak ditampilkan sama sekali
 * (tidak ada gunanya memilih satu-satunya pilihan).
 */
export default function TabDomain({ dasar, aktif, semua, label, idPanel }: Props) {
  if (semua.length < 2) return null;

  return (
    <div
      role="tablist"
      aria-label={label}
      className="grid gap-1 rounded-xl bg-white p-1 ring-1 ring-black/5 sm:inline-flex sm:flex-wrap sm:gap-1.5"
      style={{ gridTemplateColumns: `repeat(${semua.length}, minmax(0, 1fr))` }}
    >
      {semua.map((d) => {
        const dipilih = d === aktif;
        return (
          <Link
            key={d}
            to={`${dasar}/${d}`}
            role="tab"
            aria-selected={dipilih}
            aria-controls={idPanel}
            aria-current={dipilih ? "page" : undefined}
            className={
              "flex min-h-[44px] min-w-0 items-center justify-center rounded-lg px-1.5 text-center text-[13px] font-medium leading-tight transition sm:min-h-0 sm:px-3.5 sm:py-2 sm:text-sm " +
              (dipilih
                ? "bg-kusafa text-white shadow-sm"
                : "text-gray-700 hover:bg-kusafa-light hover:text-kusafa")
            }
          >
            <span className="min-w-0">{DOMAIN_LABEL[d]}</span>
          </Link>
        );
      })}
    </div>
  );
}
