import { useEffect, useState } from "react";

export type JenisAksiTarget = "setujui" | "tolak" | "batalkan";

interface Props {
  aksi: JenisAksiTarget;
  /** Ringkasan target yang disentuh (sasaran · mapel · nilai · bulan). */
  ringkasan: string;
  /** Bulan berlaku lewat/terkunci: perlu centang konfirmasi Mudir/Admin. */
  perluKonfirmasi: boolean;
  lewat: boolean;
  /** Hanya Mudir/Admin yang boleh melanjutkan bulan lewat/terkunci. */
  aksesPenuh: boolean;
  sedang: boolean;
  onBatal: () => void;
  onJalankan: (opsi: { alasan: string; konfirmasi: boolean }) => void;
}

const JUDUL: Record<JenisAksiTarget, string> = {
  setujui: "Setujui target",
  tolak: "Tolak target",
  batalkan: "Batalkan pengajuan target",
};

/**
 * Dialog aksi target: setujui, tolak (alasan WAJIB), atau batalkan pengajuan.
 * Bila bulan berlakunya lewat/terkunci, Mudir/Admin harus mencentang konfirmasi
 * (RPC `target_cek_konfirmasi` menolak role lain).
 */
export default function DialogAksiTarget({
  aksi,
  ringkasan,
  perluKonfirmasi,
  lewat,
  aksesPenuh,
  sedang,
  onBatal,
  onJalankan,
}: Props) {
  const [alasan, setAlasan] = useState("");
  const [konfirmasi, setKonfirmasi] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !sedang) onBatal();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onBatal, sedang]);

  const alasanKurang = aksi === "tolak" && alasan.trim() === "";
  const terkunciTidakBoleh = perluKonfirmasi && !aksesPenuh;
  const konfirmasiKurang = perluKonfirmasi && aksesPenuh && !konfirmasi;
  const tidakBoleh = alasanKurang || terkunciTidakBoleh || konfirmasiKurang;

  const tombol =
    aksi === "setujui" ? "Setujui target" : aksi === "tolak" ? "Tolak target" : "Batalkan pengajuan";

  return (
    <div className="fixed inset-0 z-50 flex items-end bg-black/40 sm:items-center sm:justify-center" role="presentation">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="judul-aksi-target"
        className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:max-w-lg sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="judul-aksi-target" className="text-base font-bold text-gray-900">
          {JUDUL[aksi]}
        </h2>
        <p className="mt-2 text-sm text-gray-800">{ringkasan}</p>

        {aksi === "tolak" && (
          <div className="mt-3">
            <label htmlFor="alasan-tolak" className="block text-sm font-medium text-gray-800">
              Alasan penolakan <span className="text-red-700">(wajib)</span>
            </label>
            <textarea
              id="alasan-tolak"
              rows={3}
              value={alasan}
              onChange={(e) => setAlasan(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              placeholder="Mis. target terlalu tinggi untuk kemampuan santri saat ini."
            />
            <p className="mt-1 text-xs text-gray-600">
              Target tidak dihapus: tetap tersimpan sebagai riwayat, dan pengaju boleh mengajukan ulang.
            </p>
          </div>
        )}

        {aksi === "batalkan" && (
          <p className="mt-2 rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-700">
            Pengajuan dibatalkan, bukan dihapus. Hanya pengaju dan hanya status <strong>diajukan</strong> yang
            dapat dibatalkan.
          </p>
        )}

        {perluKonfirmasi && (
          <div className="mt-3 space-y-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
            <p>
              Bulan berlaku target ini <strong>{lewat ? "sudah lewat" : "sudah dikunci"}</strong>.
            </p>
            {aksesPenuh ? (
              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={konfirmasi}
                  onChange={(e) => setKonfirmasi(e.target.checked)}
                />
                <span>Saya (Mudir/Admin) tetap ingin melanjutkan.</span>
              </label>
            ) : (
              <p className="text-xs">
                Hanya Mudir/Admin yang dapat memproses target pada bulan lewat/terkunci.
              </p>
            )}
          </div>
        )}

        <div className="mt-4 flex flex-wrap justify-end gap-2">
          <button
            type="button"
            onClick={onBatal}
            disabled={sedang}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={() => onJalankan({ alasan: alasan.trim(), konfirmasi })}
            disabled={sedang || tidakBoleh}
            className={
              "rounded-lg px-3 py-2 text-sm font-medium text-white disabled:opacity-50 " +
              (aksi === "tolak"
                ? "bg-red-600 hover:bg-red-700"
                : aksi === "batalkan"
                  ? "bg-gray-700 hover:bg-gray-800"
                  : "bg-kusafa hover:bg-kusafa/90")
            }
          >
            {sedang ? "Memproses..." : tombol}
          </button>
        </div>
      </div>
    </div>
  );
}
