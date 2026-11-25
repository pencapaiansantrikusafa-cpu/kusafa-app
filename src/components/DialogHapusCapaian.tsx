import { useEffect, useMemo, useState } from "react";
import { angka } from "../lib/laporan";

/** Pratinjau hapus satu capaian dari RPC `hapus_capaian_info`. */
export interface InfoHapus {
  ada: boolean;
  santri: string;
  mapel: string;
  bulan: string;
  label?: string | null;
  pos?: number | null;
  putaran?: number;
  putaran_lalu?: number | null;
  mulai_putaran_baru?: boolean;
  terkunci?: boolean;
  bulan_sesudah?: Array<{ bulan: string; label: string | null }>;
  jumlah_sesudah?: number;
  perlu_setuju_lanjutan?: boolean;
}

/** Pratinjau hapus massal dari RPC `hapus_capaian_massal_info`. */
export interface InfoHapusMassal {
  ada: boolean;
  halaqah: string;
  mapel: string;
  bulan: string;
  baris: number;
  santri: Array<{ santri: string; label: string | null; pos: number | null }>;
  variasi_nilai: number;
  terkunci?: boolean;
  bulan_sesudah?: Array<{ bulan: string }>;
  jumlah_sesudah?: number;
  perlu_setuju_lanjutan?: boolean;
}

interface Props {
  info: InfoHapus | InfoHapusMassal;
  massal: boolean;
  sedang: boolean;
  onBatal: () => void;
  onHapus: (opsi: { setujuTerkunci: boolean; setujuLanjutan: boolean }) => void;
}

/**
 * Dialog konfirmasi hapus capaian (Admin/Mudir):
 * - menyebut santri (atau jumlah santri), bidang, bulan, dan nilai yang dihapus;
 * - memberi tahu bila bulan terkunci (centang konfirmasi eksplisit);
 * - memperingatkan bila bulan sesudahnya sudah terisi / capaian itu mulai putaran baru,
 *   dan menolak sampai konfirmasi diberikan (atau menyarankan hapus dari bulan terakhir).
 */
export default function DialogHapusCapaian({ info, massal, sedang, onBatal, onHapus }: Props) {
  const [setujuTerkunci, setSetujuTerkunci] = useState(false);
  const [setujuLanjutan, setSetujuLanjutan] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !sedang) onBatal();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onBatal, sedang]);

  const massalInfo = massal ? (info as InfoHapusMassal) : null;
  const santriMassal = useMemo(
    () => (massalInfo && Array.isArray(massalInfo.santri) ? massalInfo.santri : []),
    [massalInfo],
  );

  const bulanSesudah = (info.bulan_sesudah ?? [])
    .map((b) => ("label" in b && b.label ? `${b.bulan}: ${b.label}` : b.bulan))
    .join(", ");
  const mulaiBaru = "mulai_putaran_baru" in info && info.mulai_putaran_baru;
  const putaran = "putaran" in info ? info.putaran : undefined;
  const putaranLalu = "putaran_lalu" in info ? info.putaran_lalu : undefined;

  const bolehHapus =
    (!info.terkunci || setujuTerkunci) && (!info.perlu_setuju_lanjutan || setujuLanjutan);

  return (
    <div className="fixed inset-0 z-50 flex items-end bg-black/40 sm:items-center sm:justify-center" role="presentation">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="judul-hapus-capaian"
        className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:max-w-lg sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="judul-hapus-capaian" className="text-base font-bold text-gray-900">
          Hapus capaian
        </h2>

        <p className="mt-2 text-sm text-gray-800">
          <strong>{info.mapel}</strong> · <strong>{info.bulan}</strong>
          {massalInfo ? (
            <>
              {" "}
              · <strong>{massalInfo.baris} santri</strong> di halaqah <strong>{massalInfo.halaqah}</strong>
            </>
          ) : (
            <>
              {" "}
              · <strong>{String((info as InfoHapus).santri)}</strong>
            </>
          )}
        </p>

        {!massal && (
          <p className="mt-1 text-sm text-gray-700">
            Nilai sekarang: <strong>{String((info as InfoHapus).label ?? "—")}</strong>
            {typeof (info as InfoHapus).pos === "number"
              ? ` (posisi ${angka((info as InfoHapus).pos as number)})`
              : ""}
          </p>
        )}

        {massal && santriMassal.length > 0 && (
          <div className="mt-3 max-h-56 overflow-y-auto rounded-lg bg-gray-50 p-3">
            <p className="text-xs font-medium text-gray-700">
              Santri terdampak ({massalInfo?.baris ?? 0}):
              {"variasi_nilai" in info && info.variasi_nilai > 1
                ? ` nilai berbeda antar santri (${info.variasi_nilai} nilai)`
                : ""}
            </p>
            <ul className="mt-1 space-y-0.5 text-xs text-gray-700">
              {santriMassal.map((s) => (
                <li key={s.santri}>
                  {s.santri} — <span className="text-gray-800">{s.label ?? "—"}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {(info.terkunci || info.perlu_setuju_lanjutan) && (
          <div className="mt-3 space-y-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
            {info.terkunci && (
              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={setujuTerkunci}
                  onChange={(e) => setSetujuTerkunci(e.target.checked)}
                />
                <span>
                  Bulan ini <strong>sudah dikunci</strong>. Saya (Mudir/Admin) tetap ingin menghapus.
                </span>
              </label>
            )}
            {info.perlu_setuju_lanjutan && (
              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={setujuLanjutan}
                  onChange={(e) => setSetujuLanjutan(e.target.checked)}
                />
                <span>
                  Bulan sesudahnya <strong>sudah terisi</strong> ({bulanSesudah || "—"}).
                  Menghapus bulan ini membuat selisih bulan sesudahnya tidak konsisten.
                  Lebih aman hapus mulai dari bulan terakhir. Saya tetap ingin melanjutkan.
                </span>
              </label>
            )}
          </div>
        )}

        {mulaiBaru && (
          <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Capaian ini tercatat <strong>khatam, mulai putaran baru</strong> (putaran {angka(putaran ?? 0)}
            {putaranLalu !== null && putaranLalu !== undefined ? `, bulan lalu putaran ${angka(putaranLalu)}` : ""}).
            Setelah dihapus, putaran bulan sesudahnya perlu ditinjau.
          </p>
        )}

        <p className="mt-3 text-xs text-gray-600">
          Tampilan akan kembali <strong>“belum diisi”</strong> (kosong, bukan 0). Penghapusan dicatat di
          log perubahan (siapa, kapan, nilai lama).
        </p>

        <div className="mt-4 flex flex-wrap justify-end gap-2">
          <button
            onClick={onBatal}
            disabled={sedang}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Batal
          </button>
          <button
            onClick={() => onHapus({ setujuTerkunci, setujuLanjutan })}
            disabled={sedang || !bolehHapus}
            className="rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            {sedang ? "Menghapus..." : massal ? `Hapus ${massalInfo?.baris ?? 0} capaian` : "Hapus capaian"}
          </button>
        </div>
      </div>
    </div>
  );
}
