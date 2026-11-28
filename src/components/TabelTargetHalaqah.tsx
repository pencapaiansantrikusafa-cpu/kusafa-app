import type { Domain } from "../lib/roles";
import {
  STATUS_GAYA,
  STATUS_LABEL,
  type BarisTarget,
  type TargetStatus,
} from "../lib/target";

/** Kolom tampilan yang wajib ada pada baris target halaqah. */
export type BarisTargetHalaqah = BarisTarget & {
  halaqah: { code: string } | null;
  mapel: { name: string } | null;
  target_item?: { label: string } | null;
  pengaju: { full_name: string } | null;
  penyetuju: { full_name: string } | null;
  penolak: { full_name: string } | null;
};

/** Satu halaqah + target-target mapelnya pada bulan yang dipilih. */
export interface GrupHalaqah<R extends BarisTargetHalaqah = BarisTargetHalaqah> {
  halaqahId: string;
  code: string;
  pengampu: string;
  /** Mapel aktif halaqah ini pada bulan terpilih (urutan database). */
  mapel: { id: string; name: string }[];
  /** Halaqah tanpa mapel (Level 6). */
  tanpaMapel: boolean;
  baris: R[];
}

/** Urutan status untuk memilih target yang ditampilkan di sel. */
const PRIORITAS: Record<TargetStatus, number> = {
  diajukan: 0,
  disetujui: 1,
  ditolak: 2,
  dibatalkan: 3,
};

interface Props<R extends BarisTargetHalaqah> {
  domain: Domain;
  labelHalaqah: string;
  grup: GrupHalaqah<R>[];
  mapel: { id: string; name: string }[];
  bolehSetujui: boolean;
  aksesPenuh: boolean;
  /** Profil pemakai (untuk tombol Batalkan hanya pengaju). */
  profileId?: string | null;
  sedang: boolean;
  onSetujuiSemua: (halaqahId: string) => void;
  onAksi: (jenis: "setujui" | "tolak" | "batalkan", target: R) => void;
  onUbah: (target: R) => void;
  onRiwayat: (target: R) => void;
}

/** Target terbaru satu (halaqah, mapel): pengajuan didahulukan, lalu terbaru. */
function terbaru<R extends BarisTarget>(baris: R[], mapelId: string): R | null {
  const kandidat = baris.filter((b) => b.subject_id === mapelId);
  if (kandidat.length === 0) return null;
  return [...kandidat].sort(
    (a, b) =>
      PRIORITAS[a.status] - PRIORITAS[b.status] ||
      b.created_at.localeCompare(a.created_at),
  )[0];
}

/**
 * Daftar target Ilmu Wasilah / Ilmu Ghayah: SATU baris per halaqah, kolom = mapel
 * aktif bulan itu berisi butir tujuan akhir + status. HP menampilkan kartu per
 * halaqah (tanpa tabel lebar). Target Al Qur'an memakai tampilan lain.
 */
export default function TabelTargetHalaqah<R extends BarisTargetHalaqah>({
  labelHalaqah,
  grup,
  mapel,
  bolehSetujui,
  profileId,
  sedang,
  onSetujuiSemua,
  onAksi,
  onUbah,
  onRiwayat,
}: Props<R>) {
  // Halaqah tanpa mapel (Level 6) tetap punya kolom catatan agar pesannya terlihat.
  const pakaiKeterangan = mapel.length === 0;

  function tombol(b: R) {
    const bolehBatalkan = b.status === "diajukan" && b.proposed_by === profileId;
    return (
      <div className="mt-1 flex flex-wrap gap-1">
        {b.status === "diajukan" && bolehSetujui && (
          <>
            <button
              type="button"
              onClick={() => onAksi("setujui", b)}
              className="rounded border border-emerald-300 bg-white px-1.5 py-0.5 text-[11px] font-medium text-emerald-800 hover:bg-emerald-50"
            >
              Setujui
            </button>
            <button
              type="button"
              onClick={() => onAksi("tolak", b)}
              className="rounded border border-red-300 bg-white px-1.5 py-0.5 text-[11px] font-medium text-red-700 hover:bg-red-50"
            >
              Tolak
            </button>
          </>
        )}
        {bolehBatalkan && (
          <button
            type="button"
            onClick={() => onAksi("batalkan", b)}
            className="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[11px] text-gray-700 hover:bg-gray-50"
          >
            Batalkan
          </button>
        )}
        <button
          type="button"
          onClick={() => onUbah(b)}
          className="rounded border border-kusafa/40 bg-white px-1.5 py-0.5 text-[11px] font-medium text-kusafa hover:bg-kusafa-light"
        >
          Ubah
        </button>
        <button
          type="button"
          onClick={() => onRiwayat(b)}
          className="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[11px] text-gray-700 hover:bg-gray-50"
        >
          Riwayat
        </button>
      </div>
    );
  }

  function labelButir(b: R | null) {
    if (!b) return <span className="text-xs text-gray-400">— belum ada target —</span>;
    return <span className="text-xs text-gray-800">{b.target_item?.label ?? "—"}</span>;
  }

  function sel(b: R | null) {
    if (!b) return <>{labelButir(b)}</>;
    return (
      <div className="space-y-0.5">
        {labelButir(b)}
        <span
          className={
            "inline-block rounded px-1.5 py-0.5 text-[10px] font-medium " + STATUS_GAYA[b.status]
          }
        >
          {STATUS_LABEL[b.status]}
        </span>
        {b.status === "ditolak" && b.alasan_tolak && (
          <p className="text-[10px] text-red-700">Alasan: {b.alasan_tolak}</p>
        )}
        <p className="text-[10px] text-gray-500">
          Pengaju: {b.pengaju?.full_name ?? "—"}
          {b.penyetuju?.full_name ? ` · Penyetuju: ${b.penyetuju.full_name}` : ""}
          {b.penolak?.full_name ? ` · Penolak: ${b.penolak.full_name}` : ""}
        </p>
        {tombol(b)}
      </div>
    );
  }

  return (
    <>
      {/* HP: kartu per halaqah, tanpa tabel lebar. */}
      <ul className="space-y-3 lg:hidden">
        {grup.map((g) => (
          <li key={g.halaqahId} className="rounded-lg bg-white p-3 ring-1 ring-black/5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-gray-900">{g.code}</p>
                <p className="text-[11px] text-gray-600">Pengampu: {g.pengampu || "—"}</p>
              </div>
              {bolehSetujui && !g.tanpaMapel && (
                <button
                  type="button"
                  disabled={sedang}
                  onClick={() => onSetujuiSemua(g.halaqahId)}
                  className="rounded border border-emerald-300 px-2 py-1 text-[11px] font-medium text-emerald-800 hover:bg-emerald-50"
                >
                  Setujui semua
                </button>
              )}
            </div>
            {g.tanpaMapel ? (
              <p className="mt-2 text-xs text-emerald-800">
                Tuntas, belum ada pelajaran lanjutan.
              </p>
            ) : (
              <ul className="mt-2 space-y-2">
                {g.mapel.map((m) => (
                  <li key={m.id} className="border-t border-black/5 pt-2">
                    <p className="text-xs font-medium text-gray-700">{m.name}</p>
                    {sel(terbaru(g.baris, m.id))}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>

      {/* Desktop: satu baris per halaqah, kolom = mapel aktif. */}
      <div className="hidden w-full overflow-x-auto lg:block">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr className="bg-kusafa-light text-xs uppercase tracking-wide text-kusafa">
              <th scope="col" className="px-3 py-2 text-left">{labelHalaqah}</th>
              {mapel.map((m) => (
                <th key={m.id} scope="col" className="px-3 py-2 text-left">{m.name}</th>
              ))}
              {pakaiKeterangan && (
                <th scope="col" className="px-3 py-2 text-left">Catatan</th>
              )}
              <th scope="col" className="px-3 py-2 text-left">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {grup.map((g) => (
              <tr key={g.halaqahId} className="border-t border-black/5 align-top">
                <th scope="row" className="px-3 py-3 text-left font-medium text-gray-900">
                  {g.code}
                  <span className="block text-[11px] font-normal text-gray-600">
                    Pengampu: {g.pengampu || "—"}
                  </span>
                </th>
                {mapel.map((m) => (
                  <td key={m.id} className="px-3 py-3">
                    {g.tanpaMapel ? (
                      <span className="text-xs text-emerald-800">
                        Tuntas, belum ada pelajaran lanjutan.
                      </span>
                    ) : (
                      sel(terbaru(g.baris, m.id))
                    )}
                  </td>
                ))}
                {pakaiKeterangan && (
                  <td className="px-3 py-3 text-xs text-emerald-800">
                    Tuntas, belum ada pelajaran lanjutan.
                  </td>
                )}
                <td className="px-3 py-3">
                  {bolehSetujui && !g.tanpaMapel && (
                    <button
                      type="button"
                      disabled={sedang}
                      onClick={() => onSetujuiSemua(g.halaqahId)}
                      className="rounded border border-emerald-300 px-2 py-1 text-[11px] font-medium text-emerald-800 hover:bg-emerald-50"
                    >
                      Setujui semua target halaqah ini
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
