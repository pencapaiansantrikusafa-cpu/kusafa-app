import { useMemo, useState } from "react";
import { supabase } from "../lib/supabase";
import { angka } from "../lib/laporan";
import DropdownCari, { type CariDiServer, type OpsiCari } from "../components/DropdownCari";
import type { Domain } from "../lib/roles";

/** Satu mata pelajaran yang ditetapkan untuk halaqah ini. */
export interface MapelInput {
  id: string;
  name: string;
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

/** Paket isi form dari RPC `wasilah_input_form`. */
export interface DataFormWasilah {
  boleh: boolean;
  domain: Domain;
  hari_efektif: number | null;
  terkunci: boolean;
  mapel: MapelInput[];
  boleh_tulis: Record<string, boolean>;
  santri: SantriInput[];
  capaian: Array<{ subject_id: string; item_id: string; jumlah: number; variasi: number }>;
  item_terpilih: ItemWasilah[];
  presensi: PresensiInput[];
  catatan: Array<{ student_id: string; note: string }>;
  lalu: Array<{ subject_id: string; item_label: string | null; pos: number | null; putaran: number | null }>;
}

interface Props {
  halaqahId: string;
  bulanId: string;
  bulanNama: string;
  data: DataFormWasilah;
  /** Pencarian item di server per mata pelajaran (pola T5c). */
  cariItemServer: (subjectId: string) => CariDiServer;
  onSelesai: () => void;
}

/**
 * Form input capaian Ilmu Wasilah / Ilmu Ghayah.
 *
 * Aturan (docs/SPEC.md bagian 2 dan 5.6): nilai dipilih SEKALI untuk halaqah ini pada
 * satu mata pelajaran, lalu disalin ke semua anggota aktif oleh database
 * (`wasilah_input_save`), bukan oleh React. Karena itu form menampilkan satu dropdown
 * item per mata pelajaran, bukan satu dropdown per santri.
 *
 * Tidak ada perhitungan di sini: Hadir tampil dari `v_attendance`, dan kemungkinan
 * selisih dinilai database saat menyimpan.
 */
export default function FormInputWasilah({
  halaqahId,
  bulanId,
  bulanNama,
  data,
  cariItemServer,
  onSelesai,
}: Props) {
  /**
   * Pilihan tiap mata pelajaran. Nilai awalnya adalah item TERSIMPAN (dari database),
   * dan setiap pilihan baru menyimpan objek beserta labelnya — pelajaran bug T5c-3:
   * item baru tidak ada di daftar `opsi`, jadi labelnya harus ditahan di state.
   */
  const [pilihan, setPilihan] = useState<Record<string, OpsiCari>>(() => {
    const awal: Record<string, OpsiCari> = {};
    for (const c of data.capaian) {
      const it = data.item_terpilih.find((x) => x.id === c.item_id);
      if (it) awal[c.subject_id] = { nilai: it.id, label: it.label };
    }
    return awal;
  });
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

  /** Item tersimpan per mapel (label dari database, bukan hasil tebakan). */
  const itemTersimpan = useMemo(() => {
    const p = new Map<string, ItemWasilah>();
    for (const it of data.item_terpilih) p.set(it.id, it);
    return p;
  }, [data.item_terpilih]);

  const bolehSimpan =
    !data.terkunci && data.santri.length > 0 && data.mapel.some((m) => m.boleh_tulis);

  async function simpan() {
    if (menyimpan) return;
    setMenyimpan(true);
    setPesan(null);
    try {
      // Yang dikirim hanya mapel yang punya pilihan; penyimpanan menyalin ke semua anggota.
      const items = Object.entries(pilihan)
        .filter(([, o]) => !!o?.nilai)
        .map(([subjectId, o]) => ({ subject_id: subjectId, item_id: o.nilai }));

      const { data: hasil, error } = await supabase.rpc("wasilah_input_save", {
        p_halaqah: halaqahId,
        p_bulan: bulanId,
        p_items: items,
      });
      if (error) throw new Error(error.message);
      const h = hasil as unknown as { mapel: number; anggota: number; baris: number } | null;
      setPesan({
        jenis: "ok",
        teks: `Data tersimpan untuk ${h?.mapel ?? 0} mata pelajaran, disalin ke ${h?.anggota ?? 0} anggota (${h?.baris ?? 0} baris).`,
      });
      onSelesai();
    } catch (e) {
      setPesan({ jenis: "galat", teks: e instanceof Error ? e.message : String(e) });
    } finally {
      setMenyimpan(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-gray-900">Input capaian — {bulanNama}</h2>
            <p className="text-xs text-gray-600">
              Hari Efektif domain: <strong>{angka(data.hari_efektif)}</strong>
              {data.terkunci && (
                <span className="ml-2 rounded bg-gray-200 px-1.5 py-0.5">bulan terkunci</span>
              )}
            </p>
            <p className="mt-1 text-xs text-gray-600">
              Nilai dipilih <strong>sekali</strong> untuk halaqah ini, lalu disalin ke semua{" "}
              {data.santri.length} anggota aktif.
            </p>
          </div>
          <button
            onClick={() => void simpan()}
            disabled={menyimpan || !bolehSimpan}
            className="rounded-lg bg-kusafa px-4 py-2 text-sm font-medium text-white hover:bg-kusafa/90 disabled:opacity-50"
          >
            {menyimpan ? "Menyimpan..." : "Simpan"}
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

      {data.mapel.length === 0 ? (
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900 ring-1 ring-amber-200">
          Halaqah ini belum punya mata pelajaran yang ditetapkan. Penetapan mata pelajaran per
          halaqah dikerjakan pada T8; hubungi Admin atau Mudir.
        </p>
      ) : (
        <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.mapel.map((m) => {
              const tersimpan = petaCapaian.get(m.id);
              const opsiTerpilih = pilihan[m.id];
              const labelTersimpan = tersimpan
                ? itemTersimpan.get(tersimpan.item_id)?.label ?? null
                : null;
              const lalu = data.lalu.find((l) => l.subject_id === m.id);
              const bolehTulis = m.boleh_tulis && !data.terkunci;
              return (
                <li key={m.id} className="rounded-lg bg-gray-50 p-3">
                  <DropdownCari
                    id={`wasilah-${m.id}`}
                    label={m.name}
                    opsi={
                      tersimpan && labelTersimpan
                        ? [{ nilai: tersimpan.item_id, label: labelTersimpan }]
                        : []
                    }
                    diServer={bolehTulis ? cariItemServer(m.id) : undefined}
                    nilai={opsiTerpilih?.nilai ?? tersimpan?.item_id ?? ""}
                    onChange={(_, o) => {
                      if (!o) return;
                      // Simpan objek pilihan beserta labelnya (pelajaran bug T5c-3):
                      // item baru tidak ada di daftar `opsi` sehingga labelnya harus ditahan.
                      setPilihan((p) => ({ ...p, [m.id]: o }));
                    }}
                    opsiKosong="— belum diisi —"
                    disabled={!bolehTulis}
                    placeholderCari={`Cari ${m.name} (mis. "1")...`}
                  />
                  <p className="mt-1 text-[11px] text-gray-600">
                    {lalu?.item_label ? (
                      <>
                        Bulan lalu: <span className="text-gray-800">{lalu.item_label}</span>
                      </>
                    ) : (
                      "Bulan lalu: belum diisi."
                    )}
                  </p>
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
        </div>
      )}

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
                // Hadir & Hari Efektif dibaca dari database (v_attendance lewat RPC),
                // tidak dihitung di React.
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
