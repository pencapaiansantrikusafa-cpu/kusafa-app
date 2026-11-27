import { useMemo, useState } from "react";
import { supabase } from "../lib/supabase";
import { angka } from "../lib/laporan";
import DropdownCari, { type CariDiServer, type OpsiCari } from "../components/DropdownCari";
import type { Domain } from "../lib/roles";

/** Satu mata pelajaran yang ditetapkan untuk halaqah ini. */
export interface MapelInput {
  id: string;
  name: string;
  /** Capaian bulan ini sudah mencapai butir terakhir mapel. */
  tuntas: boolean;
  /** Pemanggil boleh menulis capaian mapel ini di halaqah ini (dinilai database). */
  boleh_tulis: boolean;
}

export interface SantriInput {
  id: string;
  full_name: string;
}

export interface PresensiInput {
  student_id: string;
  izin: number;
  sakit: number;
  alpha: number;
  /** Hadir & Hari Efektif dari view `v_attendance` (dihitung database). */
  hadir: number | null;
  effective_days: number | null;
  effective_days_override: number | null;
}

export interface ItemWasilah {
  id: string;
  subject_id: string;
  label: string;
  value: string | null;
  siklik: boolean;
}

/** Target hidup (diajukan/disetujui) untuk satu mapel pada satu bulan. */
export interface TargetHidup {
  subject_id: string;
  target_item_id: string;
  status: "diajukan" | "disetujui" | "ditolak" | "dibatalkan";
  item_label: string;
  pos: number | null;
}

/** Paket isi form dari RPC `wasilah_input_form`. */
export interface DataFormWasilah {
  boleh: boolean;
  domain: Domain;
  hari_efektif: number | null;
  terkunci: boolean;
  mapel: MapelInput[];
  boleh_tulis: Record<string, boolean>;
  santri: SantriInput[];
  capaian: Array<{
    subject_id: string;
    item_id: string;
    pos: number | null;
    jumlah: number;
    variasi: number;
  }>;
  item_terpilih: ItemWasilah[];
  presensi: PresensiInput[];
  catatan: Array<{ student_id: string; note: string }>;
  lalu: Array<{ subject_id: string; item_label: string | null; pos: number | null; putaran: number | null }>;
  /** Target untuk bulan yang sedang dipilih (dibuat saat input bulan lalu). */
  target_ini: TargetHidup[];
  /** Target untuk bulan berikutnya (sudah ada; boleh diubah). */
  target_depan: TargetHidup[];
  /** Bulan berikutnya; null bila tidak ada (bulan terakhir). */
  bulan_depan: { id: string; name: string; hijri_year: number } | null;
  /** Halaqah Level 6: tidak punya mata pelajaran. */
  tanpa_mapel: boolean;
}

interface Props {
  halaqahId: string;
  bulanId: string;
  bulanNama: string;
  data: DataFormWasilah;
  /** Pencarian item di server per mata pelajaran (pola T5c). */
  cariItemServer: (subjectId: string) => CariDiServer;
  /** Dipanggil setelah simpan berhasil. `pesanSukses` ditampilkan induk agar tidak hilang saat form dimuat ulang. */
  onSelesai: (pesanSukses: string) => void;
}

type PilihanTarget = { opsi: OpsiCari; pos: number | null };

/**
 * Form input capaian + target bulan depan Ilmu Wasilah / Ilmu Ghayah.
 *
 * Aturan (keputusan Mudir 27 November 2026):
 * - Capaian dipilih sekali per halaqah x mapel, lalu disalin database ke semua anggota.
 * - Target bulan depan = TUJUAN AKHIR (butir kurikulum), wajib untuk tiap mapel yang
 *   capaiannya sedang diisi; tidak wajib bila mapel sudah tuntas atau sudah punya
 *   target (diajukan/disetujui). Koreksi capaian tidak memaksa mengisi ulang target.
 * - Semua disimpan satu transaksi lewat `wasilah_simpan_gabungan`.
 * Posisi butir dibaca dari fungsi database (`item_position`), bukan dihitung React.
 */
export default function FormInputWasilah({
  halaqahId,
  bulanId,
  bulanNama,
  data,
  cariItemServer,
  onSelesai,
}: Props) {
  const [pilihan, setPilihan] = useState<Record<string, OpsiCari>>(() => {
    const awal: Record<string, OpsiCari> = {};
    for (const c of data.capaian) {
      const it = data.item_terpilih.find((x) => x.id === c.item_id);
      if (it) awal[c.subject_id] = { nilai: it.id, label: it.label };
    }
    return awal;
  });
  const [posCapaian, setPosCapaian] = useState<Record<string, number | null>>(() => {
    const awal: Record<string, number | null> = {};
    for (const c of data.capaian) awal[c.subject_id] = c.pos;
    return awal;
  });
  const [target, setTarget] = useState<Record<string, PilihanTarget>>(() => {
    const awal: Record<string, PilihanTarget> = {};
    for (const t of data.target_depan) {
      if (t.target_item_id) {
        awal[t.subject_id] = {
          opsi: { nilai: t.target_item_id, label: t.item_label },
          pos: t.pos,
        };
      }
    }
    return awal;
  });
  const [konfirmasiBawah, setKonfirmasiBawah] = useState(false);
  const [menyimpan, setMenyimpan] = useState(false);
  const [pesan, setPesan] = useState<{ jenis: "ok" | "galat"; teks: string } | null>(null);

  const petaCapaian = useMemo(() => {
    const p = new Map<string, DataFormWasilah["capaian"][number]>();
    for (const c of data.capaian) p.set(c.subject_id, c);
    return p;
  }, [data.capaian]);
  const petaPresensi = useMemo(() => {
    const p = new Map<string, PresensiInput>();
    for (const a of data.presensi) p.set(a.student_id, a);
    return p;
  }, [data.presensi]);
  const itemTersimpan = useMemo(() => {
    const p = new Map<string, ItemWasilah>();
    for (const it of data.item_terpilih) p.set(it.id, it);
    return p;
  }, [data.item_terpilih]);
  const petaTargetIni = useMemo(
    () => new Map(data.target_ini.map((t) => [t.subject_id, t])),
    [data.target_ini],
  );
  const petaTargetDepan = useMemo(
    () => new Map(data.target_depan.map((t) => [t.subject_id, t])),
    [data.target_depan],
  );

  const bolehSimpan =
    !data.terkunci && data.santri.length > 0 && data.mapel.some((m) => m.boleh_tulis);

  /** Mapel yang capaiannya BERUBAH (atau baru) pada kunjungan ini. */
  const capaianBerubah = useMemo(() => {
    return data.mapel.filter((m) => {
      const pilih = pilihan[m.id]?.nilai ?? "";
      const simpan = petaCapaian.get(m.id)?.item_id ?? "";
      return !!pilih && pilih !== simpan;
    });
  }, [data.mapel, pilihan, petaCapaian]);

  /** Peringatan target di bawah capaian: posisi target < posisi capaian. */
  const diBawah = useMemo(() => {
    const hasil: Array<{ id: string; name: string }> = [];
    for (const m of data.mapel) {
      const t = target[m.id];
      const posC = posCapaian[m.id];
      if (t?.pos !== null && t?.pos !== undefined && posC !== null && posC !== undefined) {
        if (t.pos < posC) hasil.push({ id: m.id, name: m.name });
      }
    }
    return hasil;
  }, [data.mapel, target, posCapaian]);

  async function posisiButir(itemId: string): Promise<number | null> {
    const { data: p, error } = await supabase.rpc("item_position", {
      p_item: itemId,
      p_putaran: 1,
    });
    if (error) return null;
    return (p as unknown as number) ?? null;
  }

  async function simpan() {
    if (menyimpan) return;
    setMenyimpan(true);
    setPesan(null);
    try {
      // Hanya capaian yang benar-benar diisi/diubah yang dikirim. Mapel yang tidak
      // disentuh tidak diminta target (keputusan Mudir).
      const items = capaianBerubah.map((m) => ({
        subject_id: m.id,
        item_id: pilihan[m.id].nilai,
      }));
      // Target dikirim bila dipilih dan berbeda dari target yang sudah ada.
      const targets = data.mapel
        .filter((m) => {
          const t = target[m.id];
          if (!t?.opsi?.nilai) return false;
          return t.opsi.nilai !== (petaTargetDepan.get(m.id)?.target_item_id ?? "");
        })
        .map((m) => ({ subject_id: m.id, target_item_id: target[m.id].opsi.nilai }));

      if (items.length === 0 && targets.length === 0) {
        setPesan({ jenis: "galat", teks: "Belum ada capaian atau target yang diubah untuk disimpan." });
        return;
      }

      const { data: hasil, error } = await supabase.rpc("wasilah_simpan_gabungan", {
        p_halaqah: halaqahId,
        p_bulan: bulanId,
        p_capaian: items,
        p_target: targets,
        p_konfirmasi: konfirmasiBawah,
      });
      if (error) throw new Error(error.message);
      const h = hasil as unknown as {
        mapel?: number;
        anggota?: number;
        baris?: number;
        target?: number;
        tanpa_mapel?: boolean;
        pesan?: string;
      } | null;
      const teksSukses = h?.tanpa_mapel
        ? (h.pesan ?? "Tuntas, belum ada pelajaran lanjutan.")
        : `Data tersimpan: ${h?.mapel ?? 0} capaian (disalin ke ${h?.anggota ?? 0} anggota) ` +
          `dan ${h?.target ?? 0} target bulan depan.`;
      onSelesai(teksSukses);
    } catch (e) {
      setPesan({ jenis: "galat", teks: e instanceof Error ? e.message : String(e) });
    } finally {
      setMenyimpan(false);
    }
  }

  if (data.tanpa_mapel || data.mapel.length === 0) {
    return (
      <div className="rounded-xl bg-emerald-50 p-4 ring-1 ring-emerald-200">
        <p className="text-sm font-semibold text-emerald-900">
          Tuntas, belum ada pelajaran lanjutan
        </p>
        <p className="mt-1 text-xs text-emerald-800">
          Halaqah ini tidak punya mata pelajaran aktif. Tidak ada capaian atau target yang perlu
          diisi; keputusan lanjutan menunggu Masul.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-gray-900">Input capaian &amp; target — {bulanNama}</h2>
            <p className="text-xs text-gray-600">
              Hari Efektif domain: <strong>{angka(data.hari_efektif)}</strong>
              {data.terkunci && (
                <span className="ml-2 rounded bg-gray-200 px-1.5 py-0.5">bulan terkunci</span>
              )}
            </p>
            <p className="mt-1 text-xs text-gray-600">
              Capaian dipilih <strong>sekali</strong> per mapel lalu disalin ke {data.santri.length}{" "}
              anggota. Target bulan depan wajib untuk mapel yang capaiannya diisi, kecuali tuntas
              atau sudah punya target.
            </p>
          </div>
          <button
            onClick={() => void simpan()}
            disabled={menyimpan || !bolehSimpan}
            className="rounded-lg bg-kusafa px-4 py-2 text-sm font-medium text-white hover:bg-kusafa/90 disabled:opacity-50"
          >
            {menyimpan ? "Menyimpan..." : "Simpan capaian & target"}
          </button>
        </div>
        {data.terkunci && (
          <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Bulan ini sudah dikunci. Hanya Mudir atau Admin yang dapat mengubahnya.
          </p>
        )}
        {pesan && (
          <p
            role="alert"
            className={
              "mt-2 rounded-lg px-3 py-2 text-sm " +
              (pesan.jenis === "ok" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800")
            }
          >
            {pesan.teks}
          </p>
        )}
      </div>

      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.mapel.map((m) => {
            const tersimpan = petaCapaian.get(m.id);
            const opsiTerpilih = pilihan[m.id];
            const labelTersimpan = tersimpan
              ? itemTersimpan.get(tersimpan.item_id)?.label ?? null
              : null;
            const lalu = data.lalu.find((l) => l.subject_id === m.id);
            const tIni = petaTargetIni.get(m.id);
            const tDepan = petaTargetDepan.get(m.id);
            const tPilih = target[m.id];
            const bolehTulis = m.boleh_tulis && !data.terkunci;
            const bawah =
              tPilih?.pos !== null && tPilih?.pos !== undefined &&
              posCapaian[m.id] !== null && posCapaian[m.id] !== undefined &&
              tPilih.pos < (posCapaian[m.id] as number);
            return (
              <li key={m.id} className="rounded-lg bg-gray-50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-gray-900">{m.name}</p>
                  {m.tuntas && (
                    <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-medium text-emerald-800">
                      Tuntas
                    </span>
                  )}
                </div>
                <div className="mt-2">
                  <DropdownCari
                    id={`wasilah-${m.id}`}
                    label="Capaian bulan ini"
                    opsi={
                      tersimpan && labelTersimpan
                        ? [{ nilai: tersimpan.item_id, label: labelTersimpan }]
                        : []
                    }
                    diServer={bolehTulis ? cariItemServer(m.id) : undefined}
                    nilai={opsiTerpilih?.nilai ?? tersimpan?.item_id ?? ""}
                    onChange={(_, o) => {
                      if (!o) return;
                      setPilihan((p) => ({ ...p, [m.id]: o }));
                      void posisiButir(o.nilai).then((pos) =>
                        setPosCapaian((p) => ({ ...p, [m.id]: pos })),
                      );
                    }}
                    opsiKosong="— belum diisi —"
                    disabled={!bolehTulis}
                    placeholderCari={`Cari ${m.name} (mis. "1")...`}
                  />
                </div>

                <p className="mt-1 text-[11px] text-gray-600">
                  {lalu?.item_label ? (
                    <>
                      Bulan lalu: <span className="text-gray-800">{lalu.item_label}</span>
                    </>
                  ) : (
                    "Bulan lalu: belum diisi."
                  )}
                </p>
                <p className="text-[11px] text-gray-600">
                  Target bulan ini:{" "}
                  {tIni?.item_label ? (
                    <span className="text-gray-800">
                      {tIni.item_label}{" "}
                      <span className="text-gray-500">
                        ({tIni.status === "disetujui" ? "disetujui" : "menunggu persetujuan"})
                      </span>
                    </span>
                  ) : (
                    <span className="text-gray-500">belum ada.</span>
                  )}
                </p>

                <div className="mt-2 border-t border-black/5 pt-2">
                  <DropdownCari
                    id={`target-${m.id}`}
                    label="Target bulan depan"
                    opsi={tPilih ? [tPilih.opsi] : []}
                    diServer={bolehTulis ? cariItemServer(m.id) : undefined}
                    nilai={tPilih?.opsi.nilai ?? ""}
                    onChange={(_, o) => {
                      if (!o) return;
                      setTarget((p) => ({ ...p, [m.id]: { opsi: o, pos: null } }));
                      void posisiButir(o.nilai).then((pos) =>
                        setTarget((p) =>
                          p[m.id]?.opsi.nilai === o.nilai
                            ? { ...p, [m.id]: { ...p[m.id], pos } }
                            : p,
                        ),
                      );
                    }}
                    opsiKosong={tDepan ? "— tetap target yang ada —" : "— pilih butir tujuan akhir —"}
                    disabled={!bolehTulis}
                    placeholderCari={`Cari butir ${m.name} (mis. "1")...`}
                    keterangan={
                      tDepan
                        ? `Sudah ada: ${tDepan.item_label} (${tDepan.status === "disetujui" ? "disetujui" : "menunggu"}). Boleh diubah.`
                        : data.bulan_depan
                          ? `Tujuan akhir ${data.bulan_depan.name} ${data.bulan_depan.hijri_year} H.`
                          : "Bulan terakhir: target tidak diminta."
                    }
                  />
                  {m.tuntas ? (
                    <p className="mt-1 rounded bg-emerald-50 px-2 py-1 text-[11px] text-emerald-900">
                      Tuntas, target tidak wajib; menunggu keputusan Masul.
                    </p>
                  ) : (
                    <p className="mt-1 text-[11px] text-gray-500">
                      Pilih butir tujuan akhir untuk bulan depan. Butir yang sama tidak membuat
                      baris baru.
                    </p>
                  )}
                  {bawah && (
                    <p className="mt-1 rounded bg-amber-50 px-2 py-1 text-[11px] text-amber-900">
                      ⚠ Target di bawah capaian bulan ini (pengulangan). Centang konfirmasi di
                      bawah untuk melanjutkan.
                    </p>
                  )}
                </div>

                {tersimpan && tersimpan.variasi > 1 && (
                  <p className="mt-1 rounded bg-amber-50 px-2 py-1 text-[11px] text-amber-900">
                    Data tersimpan berbeda antar anggota ({tersimpan.variasi} nilai). Menyimpan
                    sekarang akan menyamakan semuanya.
                  </p>
                )}
                {!m.boleh_tulis && (
                  <p className="mt-1 text-[11px] text-gray-500">
                    Anda tidak mengampu mata pelajaran ini di halaqah ini.
                  </p>
                )}
              </li>
            );
          })}
        </ul>

        {diBawah.length > 0 && (
          <label className="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900 ring-1 ring-amber-200">
            <input
              type="checkbox"
              className="mt-0.5"
              checked={konfirmasiBawah}
              onChange={(e) => setKonfirmasiBawah(e.target.checked)}
            />
            <span>
              Saya tahu target bulan depan di bawah capaian (pengulangan) untuk:{" "}
              <strong>{diBawah.map((x) => x.name).join(", ")}</strong>. Lanjutkan.
            </span>
          </label>
        )}
      </div>

      {/* Anggota + kehadiran (angka dari database, bukan hitungan React). */}
      <div className="rounded-xl bg-white ring-1 ring-black/5">
        <div className="border-b border-black/5 px-4 py-3">
          <h3 className="text-sm font-bold text-gray-900">Anggota halaqah</h3>
          <p className="text-xs text-gray-600">
            Kehadiran dibaca dari database (Hadir = Hari Efektif − izin − sakit − alpha).
          </p>
        </div>
        <div className="w-full overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-kusafa-light text-xs uppercase tracking-wide text-kusafa">
                <th scope="col" className="px-3 py-2 text-left">Nama Santri</th>
                <th scope="col" className="px-3 py-2 text-left">Hadir/HE</th>
                <th scope="col" className="px-3 py-2 text-left">Izin</th>
                <th scope="col" className="px-3 py-2 text-left">Sakit</th>
                <th scope="col" className="px-3 py-2 text-left">Alpha</th>
                <th scope="col" className="px-3 py-2 text-left">Catatan</th>
              </tr>
            </thead>
            <tbody>
              {data.santri.map((s) => {
                const p = petaPresensi.get(s.id);
                const catatan = data.catatan.find((c) => c.student_id === s.id)?.note ?? "";
                const hadir = p?.hadir ?? null;
                const he = p?.effective_days ?? null;
                return (
                  <tr key={s.id} className="border-t border-black/5">
                    <th scope="row" className="px-3 py-2 text-left font-medium text-gray-900">
                      {s.full_name}
                    </th>
                    <td className="px-3 py-2 text-gray-800">
                      {hadir === null ? (
                        <span className="text-xs text-gray-500">belum diisi</span>
                      ) : (
                        `${angka(hadir)}/${angka(he)}`
                      )}
                    </td>
                    {[p?.izin, p?.sakit, p?.alpha].map((v, i) => (
                      <td key={i} className="px-3 py-2 text-gray-800">
                        {v === null || v === undefined ? <span className="text-xs text-gray-500">–</span> : angka(v)}
                      </td>
                    ))}
                    <td className="px-3 py-2 text-xs text-gray-700">
                      {catatan || <span className="text-gray-400">–</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      {!bolehSimpan && !data.terkunci && data.santri.length > 0 && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Anda belum ditetapkan sebagai pengampu mata pelajaran mana pun di halaqah ini.
          Penyimpanan hanya untuk pengampu atau Admin/Mudir.
        </p>
      )}
    </div>
  );
}
