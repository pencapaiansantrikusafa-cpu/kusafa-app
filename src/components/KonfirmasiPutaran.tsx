import { angka } from "../lib/laporan";

/** Satu kasus capaian yang lebih kecil dari bulan lalu. */
export interface KasusTurun {
  /** Kunci unik `${santri_id}|${bidang_id}`. */
  kunci: string;
  santriNama: string;
  /** Nama mata pelajaran (Tilawah/Tahfidz/Kitabah) agar tidak tertukar dengan bidang lain. */
  mataPelajaran: string;
  posLalu: number;
  posKini: number;
  /** Teks pilihan bulan lalu (label dropdown), bukan angka posisi. */
  teksLalu: string | null;
  /** Teks pilihan yang baru dipilih (label dropdown), bukan angka posisi. */
  teksKini: string | null;
  /** Buku siklik (Tilawah Al Qur'an): pilihan Khatam menaikkan putaran. */
  siklik: boolean;
}

interface Props {
  kasus: KasusTurun[];
  /** Kunci yang sudah dijawab pada percobaan simpan ini. */
  dijawab: Record<string, "ulang" | "khatam">;
  onJawab: (kunci: string, jawaban: "ulang" | "khatam") => void;
  onTutup: () => void;
  onSimpan: () => void;
}

/**
 * Konfirmasi sebelum simpan bila capaian lebih kecil dari bulan lalu.
 * Aplikasi tidak menebak: pengulangan dan khatam memberi hasil yang berbeda.
 */
export default function KonfirmasiPutaran({ kasus, dijawab, onJawab, onTutup, onSimpan }: Props) {
  const belum = kasus.filter((k) => !dijawab[k.kunci]);
  const adaSiklik = kasus.some((k) => k.siklik);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end bg-black/40 sm:items-center sm:justify-center"
      onClick={onTutup}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="judul-konfirmasi-putaran"
        className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:max-w-lg sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="judul-konfirmasi-putaran" className="text-base font-bold text-gray-900">
          Capaian lebih kecil dari bulan lalu. Pengulangan atau khatam?
        </h2>
        <p className="mt-1 text-xs text-gray-700">
          Pengulangan: putaran tetap, selisih menjadi negatif. Khatam: putaran menjadi putaran bulan
          lalu + 1. Pilih satu untuk setiap santri di bawah.
        </p>

        <ul className="mt-3 space-y-3">
          {kasus.map((k) => {
            const jawab = dijawab[k.kunci];
            return (
              <li key={k.kunci} className="rounded-lg bg-gray-50 p-3">
                <p className="text-sm font-medium text-gray-900">
                  {k.santriNama} · {k.mataPelajaran}
                </p>
                <p className="mt-0.5 text-xs text-gray-700">
                  Bulan lalu {k.teksLalu ?? "—"} → dipilih {k.teksKini ?? "—"} (selisih{" "}
                  {k.posKini - k.posLalu > 0 ? "+" : ""}
                  {angka(k.posKini - k.posLalu)})
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    onClick={() => onJawab(k.kunci, "ulang")}
                    aria-pressed={jawab === "ulang"}
                    className={
                      "rounded-lg px-3 py-1.5 text-sm " +
                      (jawab === "ulang"
                        ? "bg-kusafa text-white"
                        : "border border-gray-300 text-gray-700 hover:bg-gray-100")
                    }
                  >
                    Pengulangan
                  </button>
                  <button
                    onClick={() => onJawab(k.kunci, "khatam")}
                    disabled={!k.siklik}
                    aria-pressed={jawab === "khatam"}
                    title={
                      k.siklik
                        ? undefined
                        : "Khatam hanya untuk buku siklik (Tilawah Al Qur'an)."
                    }
                    className={
                      "rounded-lg px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:opacity-50 " +
                      (jawab === "khatam"
                        ? "bg-kusafa text-white"
                        : "border border-gray-300 text-gray-700 hover:bg-gray-100")
                    }
                  >
                    Khatam
                  </button>
                  {!k.siklik && (
                    <span className="self-center text-xs text-gray-600">
                      Buku ini bukan buku siklik, jadi hanya pengulangan.
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ul>

        {adaSiklik && (
          <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Bila memilih Khatam pada bulan yang sudah lewat, putaran bulan-bulan berikutnya perlu
            ditinjau.
          </p>
        )}

        <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
          <button
            onClick={onTutup}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Batal
          </button>
          <button
            onClick={onSimpan}
            disabled={belum.length > 0}
            className="rounded-lg bg-kusafa px-4 py-2 text-sm font-medium text-white hover:bg-kusafa/90 disabled:opacity-50"
          >
            {belum.length > 0
              ? `Jawab dulu ${belum.length} santri`
              : "Simpan dengan pilihan ini"}
          </button>
        </div>
      </div>
    </div>
  );
}
