import { useEffect, useState } from "react";
import { ambilRiwayat, STATUS_GAYA, STATUS_LABEL, type RiwayatBaris } from "../lib/target";
import { angka } from "../lib/laporan";

interface Props {
  judul: string;
  subjectId: string;
  studentId?: string | null;
  halaqahId?: string | null;
  onTutup: () => void;
}

/**
 * Riwayat target satu sasaran (santri + bidang, atau halaqah + mapel).
 * Membaca RPC `riwayat_target`; target lama tidak pernah dihapus, hanya diganti
 * baris baru sehingga seluruh riwayat tetap terlihat.
 */
export default function DialogRiwayatTarget({ judul, subjectId, studentId, halaqahId, onTutup }: Props) {
  const [baris, setBaris] = useState<RiwayatBaris[] | null>(null);
  const [galat, setGalat] = useState<string | null>(null);

  useEffect(() => {
    let aktif = true;
    void (async () => {
      try {
        const hasil = await ambilRiwayat(subjectId, studentId, halaqahId);
        if (aktif) setBaris(hasil);
      } catch (e) {
        if (aktif) setGalat(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => {
      aktif = false;
    };
  }, [subjectId, studentId, halaqahId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onTutup();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onTutup]);

  return (
    <div className="fixed inset-0 z-50 flex items-end bg-black/40 sm:items-center sm:justify-center" role="presentation">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="judul-riwayat-target"
        className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:max-w-2xl sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <h2 id="judul-riwayat-target" className="text-base font-bold text-gray-900">
              Riwayat target
            </h2>
            <p className="text-xs text-gray-600">{judul}</p>
          </div>
          <button
            type="button"
            onClick={onTutup}
            className="rounded-lg border border-gray-300 px-2.5 py-1 text-sm text-gray-700"
          >
            Tutup
          </button>
        </div>

        {galat && (
          <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
            Gagal memuat riwayat: {galat}
          </p>
        )}

        {baris === null && !galat && <p className="mt-3 text-sm text-gray-600">Memuat riwayat...</p>}

        {baris !== null && baris.length === 0 && (
          <p className="mt-3 text-sm text-gray-600">Belum ada target untuk sasaran ini.</p>
        )}

        {baris !== null && baris.length > 0 && (
          <ol className="mt-3 space-y-2">
            {baris.map((r) => (
              <li key={r.id} className="rounded-lg bg-gray-50 p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium text-gray-900">
                    Berlaku mulai {r.bulan_berlaku} {r.hijri_year} H · target {angka(r.amount)}{" "}
                    {r.amount_period === "harian" ? "per hari" : "per bulan"}
                  </p>
                  <span
                    className={
                      "rounded px-1.5 py-0.5 text-xs font-medium " + STATUS_GAYA[r.status]
                    }
                  >
                    {STATUS_LABEL[r.status]}
                  </span>
                </div>
                <dl className="mt-1 space-y-0.5 text-xs text-gray-700">
                  <div className="flex flex-wrap gap-x-2">
                    <dt className="text-gray-500">Pengaju:</dt>
                    <dd>{r.pengaju ?? "—"}</dd>
                    {r.approved_at && (
                      <>
                        <dt className="ml-2 text-gray-500">Disetujui:</dt>
                        <dd>
                          {r.penyetuju ?? "—"} · {new Date(r.approved_at).toLocaleDateString("id-ID")}
                        </dd>
                      </>
                    )}
                    {r.rejected_at && (
                      <>
                        <dt className="ml-2 text-gray-500">Ditolak:</dt>
                        <dd>
                          {r.penolak ?? "—"} · {new Date(r.rejected_at).toLocaleDateString("id-ID")}
                        </dd>
                      </>
                    )}
                  </div>
                  {r.alasan_tolak && (
                    <div className="text-red-700">
                      <dt className="inline text-gray-500">Alasan ditolak: </dt>
                      <dd className="inline">{r.alasan_tolak}</dd>
                    </div>
                  )}
                  {r.note && (
                    <div>
                      <dt className="inline text-gray-500">Catatan: </dt>
                      <dd className="inline">{r.note}</dd>
                    </div>
                  )}
                  <div>
                    <dt className="inline text-gray-500">Dibuat: </dt>
                    <dd className="inline">{new Date(r.created_at).toLocaleString("id-ID")}</dd>
                  </div>
                </dl>
              </li>
            ))}
          </ol>
        )}

        <p className="mt-3 text-xs text-gray-600">
          Target lama tidak dihapus: mengubah target membuat baris baru, sehingga riwayat tetap utuh.
          Hanya target <strong>disetujui</strong> yang dipakai laporan.
        </p>
      </div>
    </div>
  );
}
