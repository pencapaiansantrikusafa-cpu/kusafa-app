import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { hanyaHalaqahDiampu, navItemsFor } from "../lib/roles";
import { supabase } from "../lib/supabase";
import FormInputAlQuran, { type BarisInput, type BidangInput, type InfoLalu } from "./FormInputAlQuran";
import KotakBelumLengkap from "../components/KotakBelumLengkap";
import PemilihTahunBulan from "../components/PemilihTahunBulan";
import PemilihHalaqah, {
  halaqahDiampu,
  petaPengampu,
  type GuruBaris,
} from "../components/PemilihHalaqah";
import type { CariDiServer } from "../components/DropdownCari";

interface Halaqah {
  id: string;
  code: string;
  /** Nama halaqah tidak dikirim server lagi (T5c-2); dropdown memakai kode + pengampu. */
  name: string;
}

interface Bulan {
  id: string;
  month_no: number;
  name: string;
  hijri_year: number;
}

export interface Item {
  id: string;
  subject_id: string;
  label: string;
  value: string | null;
  /** Buku siklik (Tilawah Al Qur'an) — hanya di sini pilihan khatam ditawarkan. */
  siklik: boolean;
}

const DOMAIN = "alquran" as const;

/** Paket pembukaan halaman Input dari RPC `input_alquran_boot` (T5c-2). */
interface DataBoot {
  boleh: boolean;
  guru: GuruBaris[];
  halaqah: Array<{ id: string; code: string }>;
  bulan: Array<{ id: string; month_no: number; name: string; hijri_year: number }>;
}

/** Paket data halaman Input dari RPC `input_alquran_data` (T5c-2, satu permintaan). */
interface DataInput {
  boleh: boolean;
  bidang: BidangInput[];
  hari_efektif: number | null;
  terkunci: boolean;
  santri: Array<{ id: string; full_name: string }>;
  capaian: Array<{ student_id: string; subject_id: string; item_id: string; putaran: number; label: string }>;
  item_terpilih: Item[];
  buku: Array<{ id: string; subject_id: string; is_cyclic: boolean; sort_order: number }>;
  presensi: Array<{
    student_id: string;
    month_id: string;
    izin: number;
    sakit: number;
    alpha: number;
    effective_days_override: number | null;
  }>;
  catatan: Array<{ student_id: string; month_id: string; note: string }>;
  lalu: Array<{
    student_id: string;
    subject_id: string;
    pos: number | null;
    putaran: number | null;
    item_label: string | null;
  }>;
  kini: Array<{
    student_id: string;
    subject_id: string;
    pos: number | null;
    putaran: number | null;
    item_label: string | null;
    prev_item_label: string | null;
    selisih: number | null;
  }>;
  setelah: Array<{ student_id: string; subject_id: string }>;
}

/** Halaman Input capaian. T5: hanya Al Qur'an (Wasilah/Ghayah di T6). */
export default function InputPage() {
  const { profile } = useAuth();
  const [halaqahList, setHalaqahList] = useState<Halaqah[]>([]);
  const [halaqahId, setHalaqahId] = useState("");
  const [bulanList, setBulanList] = useState<Bulan[]>([]);
  const [bulanId, setBulanId] = useState("");
  const [tahun, setTahun] = useState<number | "">("");
  const [bidang, setBidang] = useState<BidangInput[]>([]);
  const [pengampu, setPengampu] = useState<Record<string, string>>({});
  /** Data pengampu & halaqah lengkap, dipakai ulang oleh notifikasi (tanpa unduh ulang). */
  const [guruSemua, setGuruSemua] = useState<GuruBaris[]>([]);
  const [semuaHalaqah, setSemuaHalaqah] = useState<{ id: string; code: string }[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  // Item capaian yang sudah tersimpan tetapi belum ada di daftar aktif (mis. sudah dinonaktifkan).
  const [baris, setBaris] = useState<BarisInput[]>([]);
  /** Teks capaian bulan lalu per santri|bidang, dari view (bukan dihitung di sini). */
  const [infoLalu, setInfoLalu] = useState<Record<string, InfoLalu>>({});
  const [hariEfektif, setHariEfektif] = useState<number | null>(null);
  const [terkunci, setTerkunci] = useState(false);
  const [memuat, setMemuat] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);

  const bolehHeKhusus = profile?.role === "mudir" || profile?.role === "admin";
  const item = profile ? navItemsFor(profile.role).find((i) => i.key === "input") : undefined;

  // Daftar halaqah + bulan + pengampu.
  // T5c-2: satu RPC (`input_alquran_boot`) menggantikan tiga permintaan berurutan
  // (halaqah, bulan, pengampu). Aturan "hanya halaqah yang diampu" tetap dijalankan di sini;
  // database tetap penjaga terakhir (RLS).
  useEffect(() => {
    let aktif = true;
    async function muat() {
      const { data, error } = await supabase.rpc("input_alquran_boot");
      if (!aktif) return;
      if (error) {
        setGalat(error.message);
        setMemuat(false);
        return;
      }
      const paket = (data ?? {}) as unknown as DataBoot;
      if (!paket.boleh) {
        setGalat("Profil akun belum aktif atau tidak punya akses ke data ini.");
        setMemuat(false);
        return;
      }

      const guru: GuruBaris[] = paket.guru ?? [];
      setPengampu(petaPengampu(guru));
      setGuruSemua(guru);

      const semua = (paket.bulan ?? []).filter((m) => m.month_no > 0);
      setBulanList(semua);
      const bulanTerakhir = semua.length ? semua[semua.length - 1] : undefined;
      setBulanId((prev) => prev || bulanTerakhir?.id || "");
      setTahun((prev) => (prev !== "" ? prev : bulanTerakhir?.hijri_year ?? ""));

      // Musyrif/ah dan Mudarris/ah hanya boleh mengisi halaqah yang diampu.
      // Ini juga ditegakkan database (RLS), tetapi tampilan tidak boleh menawarkan
      // halaqah milik guru lain supaya tidak ada kesan boleh.
      // Nama halaqah tidak dikirim server (T5c-2); dropdown memakai kode + pengampu.
      const semuaHalaqahData: Halaqah[] = (paket.halaqah ?? []).map((h) => ({ ...h, name: "" }));
      let daftarHalaqah = semuaHalaqahData;
      if (profile && hanyaHalaqahDiampu(profile.role)) {
        const diampu = halaqahDiampu(guru, profile.id);
        daftarHalaqah = daftarHalaqah.filter((x) => diampu.has(x.id));
      }
      setHalaqahList(daftarHalaqah);
      setSemuaHalaqah(semuaHalaqahData);
      setHalaqahId((prev) =>
        daftarHalaqah.some((x) => x.id === prev) ? prev : (daftarHalaqah[0]?.id ?? ""),
      );
      setMemuat(false);
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, [profile]);

  // Muat isi form untuk halaqah + bulan terpilih.
  // T5c-2: SATU permintaan ke database (RPC `input_alquran_data`). Sebelumnya 20 permintaan
  // berurutan; latensi jaringan per permintaan (0,24-1,3 s) membuat halaman lambat.
  // Logika penyusunan baris tetap sama; angka tetap dari view (posisi/selisih/Hadir/target).
  const muatIsi = useCallback(async () => {
    if (!halaqahId || !bulanId) {
      setBaris([]);
      return;
    }
    setMemuat(true);
    setGalat(null);

    // Bulan sebelumnya menurut urutan kalender (pembanding otomatis).
    const idx = bulanList.findIndex((b) => b.id === bulanId);
    const bulanLaluId = idx > 0 ? bulanList[idx - 1].id : null;

    const { data, error } = await supabase.rpc("input_alquran_data", {
      p_halaqah: halaqahId,
      p_bulan: bulanId,
      p_bulan_lalu: bulanLaluId,
    });
    if (error) {
      setGalat(error.message);
      setMemuat(false);
      return;
    }
    const paket = (data ?? {}) as unknown as DataInput;
    if (!paket.boleh) {
      setGalat("Profil akun belum aktif atau tidak punya akses ke data ini.");
      setMemuat(false);
      return;
    }

    const bidangList = paket.bidang ?? [];
    setBidang(bidangList);
    setHariEfektif(paket.hari_efektif ?? null);
    setTerkunci(!!paket.terkunci);

    if ((paket.santri ?? []).length === 0) {
      setBaris([]);
      setMemuat(false);
      return;
    }

    // Item yang sudah tersimpan (label & siklik sudah berawalan nama bidang dari database).
    const daftarItem: Item[] = (paket.item_terpilih ?? []).map((it) => ({
      id: it.id,
      subject_id: it.subject_id,
      label: it.label,
      value: it.value,
      siklik: !!it.siklik,
    }));
    setItems(daftarItem);

    const barisCapaian = paket.capaian ?? [];
    const petaCapaian = new Map(barisCapaian.map((c) => [`${c.student_id}|${c.subject_id}`, c.item_id]));
    const petaPutaranTersimpan = new Map(
      barisCapaian.map((c) => [`${c.student_id}|${c.subject_id}`, c.putaran]),
    );
    const petaLalu = new Map(
      (paket.lalu ?? []).map((r) => [`${r.student_id}|${r.subject_id}`, r]),
    );
    const petaSetelah = new Set(
      (paket.setelah ?? []).map((r) => `${r.student_id}|${r.subject_id}`),
    );

    // Teks "bulan lalu" per santri|bidang: label item dari view (bukan angka posisi).
    const petaInfo: Record<string, InfoLalu> = {};
    for (const [kunci, r] of petaLalu) {
      petaInfo[kunci] = { teks: r.item_label ?? null, putaran: r.putaran ?? null, pos: r.pos ?? null };
    }
    setInfoLalu(petaInfo);

    // Isi tersimpan bulan ini menurut view (pos, selisih, teks) — untuk penanda "sudah mundur".
    const petaKini = new Map(
      (paket.kini ?? []).map((r) => [`${r.student_id}|${r.subject_id}`, r]),
    );

    const petaPresensi = new Map((paket.presensi ?? []).map((p) => [p.student_id, p]));
    const petaCatatan = new Map((paket.catatan ?? []).map((c) => [c.student_id, c.note]));

    setBaris(
      (paket.santri ?? []).map((s) => {
        const p = petaPresensi.get(s.id);
        const itemPerBidang: Record<string, string | null> = {};
        const khatamPerBidang: Record<string, boolean> = {};
        const putaranTersimpan: Record<string, number> = {};
        const posLalu: Record<string, number | null> = {};
        const putaranLalu: Record<string, number | null> = {};
        const adaBulanSetelah: Record<string, boolean> = {};
        const selisihTersimpan: Record<string, number | null> = {};
        for (const bd of bidangList) {
          const kunci = `${s.id}|${bd.id}`;
          itemPerBidang[bd.id] = petaCapaian.get(kunci) ?? null;
          khatamPerBidang[bd.id] = false;
          const tersimpan = petaPutaranTersimpan.get(kunci);
          if (tersimpan !== undefined) putaranTersimpan[bd.id] = tersimpan;
          const lalu = petaLalu.get(kunci);
          posLalu[bd.id] = lalu?.pos ?? null;
          putaranLalu[bd.id] = lalu?.putaran ?? null;
          adaBulanSetelah[bd.id] = petaSetelah.has(kunci);
          selisihTersimpan[bd.id] = petaKini.get(kunci)?.selisih ?? null;
        }
        return {
          santri_id: s.id,
          santri_nama: s.full_name,
          itemPerBidang,
          izin: String(p?.izin ?? ""),
          sakit: String(p?.sakit ?? ""),
          alpha: String(p?.alpha ?? ""),
          catatan: petaCatatan.get(s.id) ?? "",
          heOverride:
            p?.effective_days_override === null || p?.effective_days_override === undefined
              ? ""
              : String(p.effective_days_override),
          khatamPerBidang,
          putaranTersimpan,
          posLalu,
          putaranLalu,
          adaBulanSetelah,
          selisihTersimpan,
        };
      }),
    );

    setMemuat(false);
  }, [halaqahId, bulanId, bulanList]);

  useEffect(() => {
    void muatIsi();
  }, [muatIsi]);

  const namaHalaqah = useMemo(
    () => halaqahList.find((h) => h.id === halaqahId)?.code ?? "",
    [halaqahList, halaqahId],
  );
  const namaBulan = useMemo(() => {
    const b = bulanList.find((x) => x.id === bulanId);
    return b ? `${b.name} ${b.hijri_year} H` : "";
  }, [bulanList, bulanId]);

  /**
   * T5c: pencarian item di server. Halaman tidak lagi mengunduh seluruh item domain
   * (9.177 baris); tiap kotak dropdown mengambil 60 hasil pertama yang cocok dari
   * database saat pengguna mengetik. Rumus capaian tidak berubah.
   */
  const cariItemServer = useCallback(
    (subjectId: string): CariDiServer => ({
      awal: async () => {
        const { data, error } = await supabase.rpc("curriculum_items_search", {
          p_subject: subjectId,
          p_q: "",
          p_limit: 60,
        });
        if (error) throw new Error(error.message);
        return ((data ?? []) as Item[]).map((it) => ({
          nilai: it.id,
          label: it.label,
          siklik: it.siklik,
        }));
      },
      cari: async (kata: string) => {
        const { data, error } = await supabase.rpc("curriculum_items_search", {
          p_subject: subjectId,
          p_q: kata,
          p_limit: 60,
        });
        if (error) throw new Error(error.message);
        return ((data ?? []) as Item[]).map((it) => ({
          nilai: it.id,
          label: it.label,
          siklik: it.siklik,
        }));
      },
    }),
    [],
  );

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{item?.label ?? "Input"}</h1>
        <p className="mt-1 text-sm text-gray-700">
          Mengisi capaian, kehadiran, dan catatan bulanan. Saat ini Al Qur'an; input Ilmu Wasilah
          dan Ilmu Ghayah belum dibuat (T6).
        </p>
      </div>

      <div className="space-y-3 rounded-xl bg-white p-4 ring-1 ring-black/5">
        <PemilihHalaqah
          id="input-halaqah"
          label="Halaqah"
          halaqah={halaqahList}
          pengampu={pengampu}
          nilai={halaqahId}
          onChange={setHalaqahId}
          keterangan={
            pengampu[halaqahId] ? `Musyrif/ah: ${pengampu[halaqahId]}` : "Pengampu belum ditetapkan"
          }
        />
        <PemilihTahunBulan
          bulan={bulanList}
          tahun={tahun}
          bulanId={bulanId}
          idAwalan="input"
          tanpaDataAwal
          onTahun={(t) => {
            setTahun(t);
            const calon = bulanList.filter((b) => Number(b.hijri_year) === t && b.month_no > 0);
            if (!calon.some((b) => b.id === bulanId)) setBulanId(calon[calon.length - 1]?.id ?? "");
          }}
          onBulan={setBulanId}
        />
        {halaqahList.length === 0 && !memuat && (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Anda belum ditetapkan sebagai pengampu halaqah Al Qur'an mana pun. Hubungi Admin.
          </p>
        )}
      </div>

      {galat && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          Gagal memuat: {galat}
        </p>
      )}

      {bulanId && (
        <KotakBelumLengkap bulanId={bulanId} halaqahAwal={semuaHalaqah} guruAwal={guruSemua} />
      )}

      {memuat ? (
        <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">Memuat data...</p>
      ) : baris.length === 0 ? (
        <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">
          {halaqahId ? `Belum ada anggota di ${namaHalaqah}.` : "Pilih halaqah terlebih dahulu."}
        </p>
      ) : (
        <FormInputAlQuran
          bulanId={bulanId}
          bulanNama={`${namaHalaqah} · ${namaBulan}`}
          halaqahId={halaqahId}
          bidang={bidang}
          baris={baris}
          setBaris={setBaris}
          items={items}
          cariItemServer={cariItemServer}
          infoLalu={infoLalu}
          hariEfektif={hariEfektif}
          terkunci={terkunci}
          bolehHariEfektifKhusus={bolehHeKhusus}
          onSelesai={() => void muatIsi()}
        />
      )}
    </div>
  );
}
