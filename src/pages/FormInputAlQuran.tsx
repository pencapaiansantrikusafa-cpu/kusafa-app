import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { angka } from "../lib/laporan";
import { bolehKhatam, putaranUntukSimpan } from "../lib/putaran";
import { posisiItem } from "../lib/posisi";
import DropdownCari from "../components/DropdownCari";
import KonfirmasiPutaran, { type KasusTurun } from "../components/KonfirmasiPutaran";

export interface InfoLalu {
  /** Teks capaian bulan lalu (label item dari view), bukan angka posisi. */
  teks: string | null;
  putaran: number | null;
  pos: number | null;
}

export interface BarisInput {
  santri_id: string;
  santri_nama: string;
  /** per bidang: nilai item (id item) atau null = belum diisi */
  itemPerBidang: Record<string, string | null>;
  izin: string;
  sakit: string;
  alpha: string;
  catatan: string;
  /** Hari Efektif khusus santri (hanya boleh diubah Mudir/Admin). */
  heOverride: string;
  /** Centang "khatam, mulai putaran baru" per bidang (hanya buku siklik). */
  khatamPerBidang: Record<string, boolean>;
  /** Putaran yang sudah tersimpan di bulan ini. */
  putaranTersimpan: Record<string, number>;
  /** Posisi capaian bulan lalu per bidang (dari v_monthly_report). */
  posLalu: Record<string, number | null>;
  /** Putaran bulan lalu per bidang; null = bulan lalu belum diisi. */
  putaranLalu: Record<string, number | null>;
  /** Bulan-bulan setelah bulan ini sudah terisi untuk bidang ini. */
  adaBulanSetelah: Record<string, boolean>;
}

export interface BidangInput {
  id: string;
  name: string;
}

export interface Item {
  id: string;
  subject_id: string;
  label: string;
  value: string | null;
  /** Buku siklik (Tilawah Al Qur'an). */
  siklik: boolean;
}

interface Props {
  bulanId: string;
  bulanNama: string;
  halaqahId: string;
  bidang: BidangInput[];
  baris: BarisInput[];
  setBaris: (b: BarisInput[]) => void;
  items: Item[];
  /** Teks capaian bulan lalu per `santri_id|bidang_id` (label dari view, bukan angka posisi). */
  infoLalu: Record<string, InfoLalu>;
  hariEfektif: number | null;
  terkunci: boolean;
  bolehHariEfektifKhusus: boolean;
  onSelesai: () => void;
}

/**
 * Form input capaian Al Qur'an untuk satu halaqah dan satu bulan.
 * Semua penjagaan hak akses tetap di database (RLS); form hanya menampilkan pesan galatnya.
 * Putaran tidak pernah ditebak: khatam hanya lewat centang atau konfirmasi eksplisit.
 */
export default function FormInputAlQuran({
  bulanId,
  bulanNama,
  halaqahId,
  bidang,
  baris,
  setBaris,
  items,
  infoLalu,
  hariEfektif,
  terkunci,
  bolehHariEfektifKhusus,
  onSelesai,
}: Props) {
  const [menyimpan, setMenyimpan] = useState(false);
  const [pesan, setPesan] = useState<{ jenis: "ok" | "galat"; teks: string } | null>(null);
  const [terbuka, setTerbuka] = useState<string | null>(baris[0]?.santri_id ?? null);
  // "belum" = hanya santri yang belum lengkap (fokus mengisi), "semua" = termasuk yang sudah ada data.
  const [saring, setSaring] = useState<"semua" | "belum" | "sudah">("semua");
  /** Pertanyaan yang belum dijawab: pengulangan atau khatam. */
  const [kasus, setKasus] = useState<KasusTurun[] | null>(null);
  const [jawaban, setJawaban] = useState<Record<string, "ulang" | "khatam">>({});
  /** Ada isian yang diubah pada kunjungan ini (dipakai peringatan bulan lampau). */
  const [berubah, setBerubah] = useState(false);

  // Memo ini harus murni (tidak memodifikasi state `items`). React Mode Ketat
  // memanggilnya dua kali; bila array state ikut diubah, item terduplikasi
  // dan React memperingatkan kunci ganda.
  const itemPerBidang = useMemo(() => {
    const p: Record<string, Item[]> = {};
    for (const it of items) {
      const daftar = p[it.subject_id];
      if (daftar) daftar.push(it);
      else p[it.subject_id] = [it];
    }
    return p;
  }, [items]);

  const petaItem = useMemo(() => {
    const p = new Map<string, Item>();
    for (const it of items) p.set(it.id, it);
    return p;
  }, [items]);

  /** Lengkap = semua bidang terisi dan kehadiran (izin+sakit+alpha) masuk akal. */
  function statusSantri(b: BarisInput) {
    const terisi = bidang.filter((bd) => b.itemPerBidang[bd.id]).length;
    return { terisi, total: bidang.length, sudah: terisi === bidang.length };
  }

  const jumlahSudah = baris.filter((b) => statusSantri(b).sudah).length;
  const jumlahBelum = baris.length - jumlahSudah;

  const barisTampil = baris.filter((b) => {
    const sudah = statusSantri(b).sudah;
    return saring === "semua" || (saring === "belum" ? !sudah : sudah);
  });

  /** Santri/bidang yang bulan berikutnya sudah terisi (untuk peringatan). */
  const perluTinjau = useMemo(() => {
    // Peringatan hanya muncul bila ada perubahan nyata pada kunjungan ini.
    if (!berubah) return [];
    const daftar: string[] = [];
    for (const b of baris) {
      for (const bd of bidang) {
        // Peringatan berlaku untuk isian yang akan tersimpan — baik yang baru dipilih
        // maupun yang sudah ada di bulan ini — asalkan bulan sesudahnya sudah terisi.
        const akanTersimpan = !!b.itemPerBidang[bd.id] || b.putaranTersimpan[bd.id] !== undefined;
        if (akanTersimpan && b.adaBulanSetelah[bd.id]) {
          daftar.push(`${b.santri_nama} · ${bd.name}`);
        }
      }
    }
    return daftar;
  }, [baris, bidang, berubah]);

  function ubah(santriId: string, patch: Partial<BarisInput>) {
    setBerubah(true);
    setBaris(baris.map((b) => (b.santri_id === santriId ? { ...b, ...patch } : b)));
  }

  function ubahBidang(santriId: string, bidangId: string, itemId: string) {
    const b = baris.find((x) => x.santri_id === santriId);
    if (!b) return;
    ubah(santriId, {
      itemPerBidang: { ...b.itemPerBidang, [bidangId]: itemId || null },
      // Ganti item = pilihan khatam lama tidak berlaku lagi.
      khatamPerBidang: { ...b.khatamPerBidang, [bidangId]: false },
    });
  }

  function ubahKhatam(santriId: string, bidangId: string, nilai: boolean) {
    const b = baris.find((x) => x.santri_id === santriId);
    if (!b) return;
    ubah(santriId, { khatamPerBidang: { ...b.khatamPerBidang, [bidangId]: nilai } });
  }

  /** Putaran yang akan disimpan untuk satu bidang, mengikuti jawaban konfirmasi. */
  function putaranEfektif(b: BarisInput, bidangId: string): number {
    const kunci = `${b.santri_id}|${bidangId}`;
    const khatam = !!b.khatamPerBidang[bidangId] || jawaban[kunci] === "khatam";
    return putaranUntukSimpan({
      khatam,
      putaranBulanLalu: b.putaranLalu[bidangId] ?? null,
      putaranTersimpan: b.putaranTersimpan[bidangId] ?? null,
    });
  }

  async function simpan() {
    if (menyimpan) return;
    setMenyimpan(true);
    setPesan(null);
    try {
      // 1. Periksa capaian yang lebih kecil dari bulan lalu sebelum menulis apa pun.
      //    Posisi dihitung database lewat RPC item_position; panggilan dikumpulkan dulu
      //    agar bisa berjalan bersamaan, bukan satu per satu.
      const kandidat: Array<{
        kunci: string;
        santriNama: string;
        bidangNama: string;
        posLalu: number;
        itemId: string;
        putaran: number;
        siklik: boolean;
      }> = [];
      for (const b of baris) {
        for (const bd of bidang) {
          const itemId = b.itemPerBidang[bd.id];
          if (!itemId) continue;
          const kunci = `${b.santri_id}|${bd.id}`;
          const posLalu = b.posLalu[bd.id] ?? null;
          if (posLalu === null || jawaban[kunci]) continue;
          kandidat.push({
            kunci,
            santriNama: b.santri_nama,
            bidangNama: bd.name,
            posLalu,
            itemId,
            putaran: putaranEfektif(b, bd.id),
            siklik: !!petaItem.get(itemId)?.siklik,
          });
        }
      }
      const posKiniSemua = await Promise.all(
        kandidat.map((k) => posisiItem(k.itemId, k.putaran)),
      );
      const perluKonfirmasi: KasusTurun[] = kandidat.flatMap((k, i) => {
        const posKini = posKiniSemua[i];
        if (posKini === null || posKini >= k.posLalu) return [];
        return [
          {
            kunci: k.kunci,
            santriNama: k.santriNama,
            bidangNama: k.bidangNama,
            posLalu: k.posLalu,
            posKini,
            siklik: k.siklik,
          },
        ];
      });
      if (perluKonfirmasi.length > 0) {
        setKasus(perluKonfirmasi);
        setMenyimpan(false);
        return;
      }

      // 2. Kehadiran (izin/sakit/alpha) dan catatan per santri.
      for (const b of baris) {
        const att = {
          student_id: b.santri_id,
          month_id: bulanId,
          domain: "alquran",
          izin: Number(b.izin || 0),
          sakit: Number(b.sakit || 0),
          alpha: Number(b.alpha || 0),
          ...(bolehHariEfektifKhusus && b.heOverride !== ""
            ? { effective_days_override: Number(b.heOverride) }
            : {}),
        };
        const { error: e1 } = await supabase
          .from("attendance")
          .upsert(att, { onConflict: "student_id,month_id,domain" });
        if (e1) throw new Error(`Kehadiran ${b.santri_nama}: ${e1.message}`);

        if (b.catatan.trim()) {
          const { error: e2 } = await supabase
            .from("monthly_notes")
            .upsert(
              {
                student_id: b.santri_id,
                month_id: bulanId,
                domain: "alquran",
                note: b.catatan.trim(),
              },
              { onConflict: "student_id,month_id,domain" },
            );
          if (e2) throw new Error(`Catatan ${b.santri_nama}: ${e2.message}`);
        }

        // 3. Capaian per bidang yang dipilih, termasuk putaran.
        for (const bd of bidang) {
          const itemId = b.itemPerBidang[bd.id];
          if (!itemId) continue;
          const { error: e3 } = await supabase.from("progress_entries").upsert(
            {
              student_id: b.santri_id,
              halaqah_id: halaqahId,
              subject_id: bd.id,
              month_id: bulanId,
              item_id: itemId,
              putaran: putaranEfektif(b, bd.id),
            },
            { onConflict: "student_id,subject_id,month_id" },
          );
          if (e3) throw new Error(`Capaian ${bd.name} ${b.santri_nama}: ${e3.message}`);
        }
      }
      setKasus(null);
      setJawaban({});
      setBerubah(false);
      setPesan({ jenis: "ok", teks: "Data tersimpan." });
      onSelesai();
    } catch (e) {
      setPesan({
        jenis: "galat",
        teks: e instanceof Error ? e.message : String(e),
      });
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
              Hari Efektif domain: <strong>{angka(hariEfektif)}</strong>
              {terkunci && <span className="ml-2 rounded bg-gray-200 px-1.5 py-0.5">bulan terkunci</span>}
            </p>
          </div>
          <button
            onClick={() => void simpan()}
            disabled={menyimpan || terkunci}
            className="rounded-lg bg-kusafa px-4 py-2 text-sm font-medium text-white hover:bg-kusafa/90 disabled:opacity-50"
          >
            {menyimpan ? "Menyimpan..." : "Simpan"}
          </button>
        </div>
        {terkunci && (
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

      {perluTinjau.length > 0 && (
        <p role="status" className="rounded-xl bg-amber-50 px-4 py-3 text-xs text-amber-900 ring-1 ring-amber-200">
          Bulan setelah bulan ini sudah terisi untuk {perluTinjau.length} santri/bidang (
          {perluTinjau.slice(0, 3).join(", ")}
          {perluTinjau.length > 3 ? ", dan lainnya" : ""}). Bila capaian atau putaran bulan ini diubah,
          putaran bulan-bulan berikutnya perlu ditinjau.
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 rounded-xl bg-white px-3 py-2 ring-1 ring-black/5">
        <span className="text-sm font-medium text-gray-800">Tampilkan</span>
        {(
          [
            ["semua", `Semua (${baris.length})`],
            ["belum", `Belum lengkap (${jumlahBelum})`],
            ["sudah", `Sudah ada data (${jumlahSudah})`],
          ] as ["semua" | "belum" | "sudah", string][]
        ).map(([nilai, label]) => (
          <button
            key={nilai}
            onClick={() => setSaring(nilai)}
            aria-pressed={saring === nilai}
            className={
              "rounded-lg px-3 py-1.5 text-sm " +
              (saring === nilai
                ? "bg-kusafa text-white"
                : "border border-gray-300 text-gray-700 hover:bg-gray-50")
            }
          >
            {label}
          </button>
        ))}
        <span className="ml-auto flex items-center gap-3 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full bg-pink-400" /> belum lengkap
          </span>
          <span className="flex items-center gap-1">
            <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" /> sudah terisi
          </span>
        </span>
      </div>

      <ul className="space-y-2">
        {barisTampil.map((b) => {
          const buka = terbuka === b.santri_id;
          const st = statusSantri(b);
          return (
            <li
              key={b.santri_id}
              className={
                "rounded-xl border-l-4 bg-white ring-1 ring-black/5 " +
                (st.sudah ? "border-l-emerald-500" : "border-l-pink-400")
              }
            >
              <button
                onClick={() => setTerbuka(buka ? null : b.santri_id)}
                aria-expanded={buka}
                className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
              >
                <span className="min-w-0">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="truncate text-sm font-medium text-gray-900">{b.santri_nama}</span>
                    <span
                      className={
                        "rounded px-1.5 py-0.5 text-[11px] font-medium " +
                        (st.sudah
                          ? "bg-emerald-50 text-emerald-800"
                          : "bg-pink-50 text-pink-900")
                      }
                    >
                      {st.sudah ? "✓ sudah terisi" : "belum lengkap"}
                    </span>
                  </span>
                  <span className="text-xs text-gray-600">
                    {st.terisi}/{st.total} bidang terisi · izin {b.izin || "—"}, sakit {b.sakit || "—"}, alpha {b.alpha || "—"}
                  </span>
                </span>
                <span aria-hidden className="text-gray-400">{buka ? "▴" : "▾"}</span>
              </button>

              {buka && (
                <div className="space-y-3 border-t border-black/5 px-4 py-3">
                  <div className="grid gap-3 sm:grid-cols-3">
                    {bidang.map((bd) => {
                      const itemId = b.itemPerBidang[bd.id];
                      const item = itemId ? petaItem.get(itemId) : undefined;
                      const pLalu = b.putaranLalu[bd.id] ?? null;
                      const bisaKhatam = bolehKhatam(!!item?.siklik, {
                        pos: b.posLalu[bd.id] ?? null,
                        putaran: pLalu,
                      });
                      const khatam = !!b.khatamPerBidang[bd.id];
                      return (
                        <div key={bd.id}>
                          <DropdownCari
                            id={`item-${b.santri_id}-${bd.id}`}
                            label={bd.name}
                            opsi={(itemPerBidang[bd.id] ?? []).map((it) => ({
                              nilai: it.id,
                              label: it.label,
                            }))}
                            nilai={itemId ?? ""}
                            onChange={(v) => ubahBidang(b.santri_id, bd.id, v)}
                            opsiKosong="— belum diisi —"
                            placeholderCari={`Cari ${bd.name} (mis. "qura")...`}
                          />
                          {item && (
                            <p className="mt-1 text-[11px] text-gray-600">
                              {(() => {
                                const info = infoLalu[`${b.santri_id}|${bd.id}`];
                                if (info?.teks) {
                                  return (
                                    <>
                                      Bulan lalu: <span className="text-gray-800">{info.teks}</span>
                                      {pLalu !== null ? ` (putaran ${pLalu})` : ""}
                                    </>
                                  );
                                }
                                if (b.putaranLalu[bd.id] !== null || b.posLalu[bd.id] !== null) {
                                  return "Bulan lalu: teks capaian belum tersedia.";
                                }
                                return "Bulan lalu: belum diisi.";
                              })()}
                            </p>
                          )}
                          {bisaKhatam && (
                            <label
                              htmlFor={`khatam-${b.santri_id}-${bd.id}`}
                              className="mt-1 flex items-start gap-2 text-xs text-gray-800"
                            >
                              <input
                                id={`khatam-${b.santri_id}-${bd.id}`}
                                type="checkbox"
                                checked={khatam}
                                onChange={(e) => ubahKhatam(b.santri_id, bd.id, e.target.checked)}
                                className="mt-0.5"
                              />
                              <span>
                                khatam, mulai putaran baru
                                <span className="block text-[11px] text-gray-600">
                                  putaran menjadi {(pLalu ?? 0) + 1}
                                </span>
                              </span>
                            </label>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {(
                      [
                        ["izin", "Izin"],
                        ["sakit", "Sakit"],
                        ["alpha", "Alpha"],
                      ] as ["izin" | "sakit" | "alpha", string][]
                    ).map(([k, label]) => (
                      <div key={k}>
                        <label htmlFor={`${k}-${b.santri_id}`} className="block text-xs font-medium text-gray-800">
                          {label}
                        </label>
                        <input
                          id={`${k}-${b.santri_id}`}
                          type="number"
                          min={0}
                          step={1}
                          inputMode="numeric"
                          value={b[k]}
                          onChange={(e) => ubah(b.santri_id, { [k]: e.target.value } as Partial<BarisInput>)}
                          className="mt-1 w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                        />
                      </div>
                    ))}
                  </div>

                  {bolehHariEfektifKhusus && (
                    <div>
                      <label
                        htmlFor={`he-${b.santri_id}`}
                        className="block text-xs font-medium text-gray-800"
                      >
                        Hari Efektif khusus santri (kosongkan bila sama dengan domain)
                      </label>
                      <input
                        id={`he-${b.santri_id}`}
                        type="number"
                        min={0}
                        step={1}
                        value={b.heOverride}
                        onChange={(e) => ubah(b.santri_id, { heOverride: e.target.value })}
                        className="mt-1 w-32 rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                      />
                    </div>
                  )}

                  <div>
                    <label htmlFor={`catatan-${b.santri_id}`} className="block text-xs font-medium text-gray-800">
                      Catatan
                    </label>
                    <textarea
                      id={`catatan-${b.santri_id}`}
                      rows={2}
                      value={b.catatan}
                      onChange={(e) => ubah(b.santri_id, { catatan: e.target.value })}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                      placeholder="Catatan bulanan (boleh kosong)"
                    />
                  </div>

                  <Link
                    to={`/santri/${b.santri_id}?domain=alquran`}
                    className="inline-block text-xs font-medium text-kusafa underline underline-offset-2"
                  >
                    Lihat capaian santri ini
                  </Link>
                </div>
              )}
            </li>
          );
        })}
      </ul>

      {kasus && (
        <KonfirmasiPutaran
          kasus={kasus}
          dijawab={jawaban}
          onJawab={(kunci, nilai) => setJawaban((prev) => ({ ...prev, [kunci]: nilai }))}
          onTutup={() => {
            setKasus(null);
            setJawaban({});
          }}
          onSimpan={() => {
            setKasus(null);
            void simpan();
          }}
        />
      )}
    </div>
  );
}
