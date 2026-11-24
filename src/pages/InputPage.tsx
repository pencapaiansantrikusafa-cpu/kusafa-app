import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { hanyaHalaqahDiampu, navItemsFor } from "../lib/roles";
import { supabase } from "../lib/supabase";
import FormInputAlQuran, { type BarisInput, type BidangInput, type InfoLalu } from "./FormInputAlQuran";
import KotakBelumLengkap from "../components/KotakBelumLengkap";
import { ambilSemua } from "../lib/ambil-semua";
import PemilihTahunBulan from "../components/PemilihTahunBulan";
import PemilihHalaqah, {
  ambilGuru,
  halaqahDiampu,
  petaPengampu,
  type GuruBaris,
} from "../components/PemilihHalaqah";
import type { CariDiServer } from "../components/DropdownCari";

interface Halaqah {
  id: string;
  code: string;
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
  const [itemTambahan, setItemTambahan] = useState<Item[]>([]);
  const [baris, setBaris] = useState<BarisInput[]>([]);
  /** Teks capaian bulan lalu per santri|bidang, dari view (bukan dihitung di sini). */
  const [infoLalu, setInfoLalu] = useState<Record<string, InfoLalu>>({});
  const [hariEfektif, setHariEfektif] = useState<number | null>(null);
  const [terkunci, setTerkunci] = useState(false);
  const [memuat, setMemuat] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);

  const bolehHeKhusus = profile?.role === "mudir" || profile?.role === "admin";
  const item = profile ? navItemsFor(profile.role).find((i) => i.key === "input") : undefined;

  // Daftar halaqah + bulan.
  useEffect(() => {
    let aktif = true;
    async function muat() {
      const [h, b] = await Promise.all([
        supabase.from("halaqahs").select("id, code, name").eq("domain", DOMAIN).eq("is_active", true).order("code"),
        supabase
          .from("hijri_months")
          .select("id, month_no, name, academic_years!inner(hijri_year)")
          .order("month_no"),
      ]);
      // T5c: pengampu diambil SEKALI di sini (dipakai pemilih halaqah & notifikasi),
      // tidak diunduh ulang oleh komponen lain.
      const guru = await ambilGuru();
      if (!aktif) return;
      if (h.error || b.error) {
        setGalat(h.error?.message ?? b.error?.message ?? null);
        setMemuat(false);
        return;
      }
      const semua = ((b.data ?? []) as unknown as Array<{
        id: string;
        month_no: number;
        name: string;
        academic_years: { hijri_year: number } | { hijri_year: number }[];
      }>).map((m) => {
        const ay = Array.isArray(m.academic_years) ? m.academic_years[0] : m.academic_years;
        return { id: m.id, month_no: m.month_no, name: m.name, hijri_year: ay?.hijri_year ?? 0 };
      });
      semua.sort((a, c) => a.hijri_year - c.hijri_year || a.month_no - c.month_no);
      setBulanList(semua.filter((m) => m.month_no > 0));
      const bulanTerakhir = semua.filter((m) => m.month_no > 0).slice(-1)[0];
      setBulanId((prev) => prev || bulanTerakhir?.id || "");
      setTahun((prev) => (prev !== "" ? prev : bulanTerakhir?.hijri_year ?? ""));

      setPengampu(petaPengampu(guru));

      // Musyrif/ah dan Mudarris/ah hanya boleh mengisi halaqah yang diampu.
      // Ini juga ditegakkan database (RLS), tetapi tampilan tidak boleh menawarkan
      // halaqah milik guru lain supaya tidak ada kesan boleh.
      let daftarHalaqah = h.data ?? [];
      if (profile && hanyaHalaqahDiampu(profile.role)) {
        const diampu = halaqahDiampu(guru, profile.id);
        daftarHalaqah = daftarHalaqah.filter((x) => diampu.has(x.id));
      }
      setHalaqahList(daftarHalaqah);
      setGuruSemua(guru);
      setSemuaHalaqah(h.data ?? []);
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
  const muatIsi = useCallback(async () => {
    if (!halaqahId || !bulanId) {
      setBaris([]);
      return;
    }
    setMemuat(true);
    setGalat(null);

    const [mem, sub, set] = await Promise.all([
      supabase.from("halaqah_members").select("student_id").eq("halaqah_id", halaqahId),
      supabase.from("subjects").select("id, name").eq("domain", DOMAIN).order("sort_order"),
      supabase
        .from("month_domain_settings")
        .select("effective_days, is_locked")
        .eq("month_id", bulanId)
        .eq("domain", DOMAIN)
        .maybeSingle(),
    ]);
    if (mem.error || sub.error || set.error) {
      setGalat(mem.error?.message ?? sub.error?.message ?? set.error?.message ?? null);
      setMemuat(false);
      return;
    }
    const bidangList = (sub.data ?? []) as BidangInput[];
    setBidang(bidangList);
    setHariEfektif(set.data?.effective_days ?? null);
    setTerkunci(!!set.data?.is_locked);

    const anggota = (mem.data ?? []).map((x) => x.student_id);
    if (anggota.length === 0) {
      setBaris([]);
      setMemuat(false);
      return;
    }

    const subjectIds = bidangList.map((b) => b.id);
    // T5c: daftar buku untuk item diambil paralel dengan query form (tidak berurutan).
    const janjiBuku = supabase
      .from("books")
      .select("id, subject_id, is_cyclic, sort_order")
      .in("subject_id", subjectIds)
      .eq("is_active", true)
      .order("stage_order", { ascending: true })
      .order("sort_order", { ascending: true });
    // Bulan sebelumnya dan bulan-bulan sesudahnya, menurut urutan kalender.
    const idx = bulanList.findIndex((b) => b.id === bulanId);
    const bulanLaluId = idx > 0 ? bulanList[idx - 1].id : null;
    const bulanLaluNama = idx > 0 ? bulanList[idx - 1].name : "";
    const bulanSetelahIds = idx >= 0 ? bulanList.slice(idx + 1).map((b) => b.id) : [];

    const [st, capaian, presensi, catatan, laporanLalu, laporanKini, setelah, bukuRes] = await Promise.all([
      supabase.from("students").select("id, full_name").in("id", anggota).order("full_name"),
      supabase
        .from("progress_entries")
        .select("student_id, subject_id, item_id, putaran, curriculum_items(label)")
        .eq("month_id", bulanId)
        .eq("halaqah_id", halaqahId),
      // Tentukan bulan secara tegas di kedua sisi (sisi klien dan kunci peta).
      supabase
        .from("attendance")
        .select("student_id, month_id, izin, sakit, alpha, effective_days_override")
        .eq("month_id", bulanId)
        .eq("domain", DOMAIN)
        .in("student_id", anggota)
        .neq("month_id", "00000000-0000-0000-0000-000000000000"),
      supabase
        .from("monthly_notes")
        .select("student_id, month_id, note")
        .eq("month_id", bulanId)
        .eq("domain", DOMAIN)
        .in("student_id", anggota),
      // Posisi, putaran, dan teks capaian bulan lalu (pembanding otomatis).
      bulanLaluId
        ? supabase
            .from("v_monthly_report")
            .select("student_id, subject_id, pos, putaran, item_label")
            .eq("halaqah_id", halaqahId)
            .eq("month_id", bulanLaluId)
            .eq("domain", DOMAIN)
        : Promise.resolve({ data: [], error: null }),
      // Isi tersimpan bulan ini menurut database (pos, selisih, teks). Dipakai untuk
      // menandai bidang yang sudah mundur tetapi tidak diubah — tanpa menghitung di React.
      supabase
        .from("v_monthly_report")
        .select("student_id, subject_id, pos, putaran, item_label, prev_item_label, selisih")
        .eq("halaqah_id", halaqahId)
        .eq("month_id", bulanId)
        .eq("domain", DOMAIN),
      // Apakah bulan sesudahnya sudah terisi (untuk peringatan peninjauan putaran).
      bulanSetelahIds.length > 0 && anggota.length > 0
        ? ambilSemua<{ student_id: string; subject_id: string }>((awal, jumlah) =>
            supabase
              .from("progress_entries")
              .select("student_id, subject_id")
              .in("month_id", bulanSetelahIds)
              .in("student_id", anggota)
              .in("subject_id", subjectIds)
              .order("id", { ascending: true })
              .range(awal, awal + jumlah - 1),
          )
        : Promise.resolve({ data: [], error: null }),
      janjiBuku,
    ]);
    const galat2 =
      st.error ??
      capaian.error ??
      presensi.error ??
      catatan.error ??
      bukuRes.error ??
      laporanLalu.error ??
      laporanKini.error ??
      setelah.error;
    if (galat2) {
      setGalat(typeof galat2 === "string" ? galat2 : galat2.message);
      setMemuat(false);
      return;
    }

    // T5c: hanya item yang SUDAH terpilih bulan ini yang diambil detailnya (lewat RPC),
    // agar nilai tersimpan tetap tampil walau item itu tidak muncul di hasil cari.
    if (!Array.isArray(bukuRes.data)) {
      setGalat("Daftar buku tidak terbaca.");
      setMemuat(false);
      return;
    }
    const barisCapaianAwal = (capaian.data ?? []) as unknown as Array<{
      student_id: string;
      subject_id: string;
      item_id: string;
      putaran: number;
      curriculum_items: { label: string } | { label: string }[] | null;
    }>;
    const idTerpilih = [...new Set(barisCapaianAwal.map((c) => c.item_id))];
    const { data: dataTerpilih, error: eTerpilih } = await supabase.rpc("curriculum_items_by_ids", {
      p_ids: idTerpilih,
    });
    if (eTerpilih) {
      setGalat(eTerpilih.message);
      setMemuat(false);
      return;
    }

    // Gabungkan item per buku menjadi satu daftar sesuai urutan buku.
    // Label diberi nama mata pelajaran di depan ("Tahfidz · An Naba' - 40"): beberapa
    // buku dipakai lebih dari satu mata pelajaran (mis. Juz 'Amma di Tilawah dan
    // Kitabah), sehingga label mentah bisa sama dan membingungkan.
    const namaBidang = new Map(bidangList.map((b) => [b.id, b.name]));
    const berlabel = (subjectId: string, label: string) => {
      const nama = namaBidang.get(subjectId);
      return nama ? `${nama} · ${label}` : label;
    };
    const daftarItem: Item[] = [];
    if (Array.isArray(dataTerpilih)) {
      for (const it of dataTerpilih as Item[]) {
        daftarItem.push({
          id: it.id,
          subject_id: it.subject_id,
          label: it.label,
          value: it.value,
          siklik: !!it.siklik,
        });
      }
    }
    setItems(daftarItem);

    const barisCapaian = barisCapaianAwal;
    const petaCapaian = new Map(barisCapaian.map((c) => [`${c.student_id}|${c.subject_id}`, c.item_id]));
    const petaPutaranTersimpan = new Map(
      barisCapaian.map((c) => [`${c.student_id}|${c.subject_id}`, c.putaran]),
    );
    const petaLalu = new Map(
      ((laporanLalu.data ?? []) as unknown as Array<{
        student_id: string;
        subject_id: string;
        pos: number | null;
        putaran: number | null;
        item_label: string | null;
      }>).map((r) => [`${r.student_id}|${r.subject_id}`, r]),
    );
    const petaSetelah = new Set(
      ((setelah.data ?? []) as unknown as Array<{ student_id: string; subject_id: string }>).map(
        (r) => `${r.student_id}|${r.subject_id}`,
      ),
    );

    // Label item tersimpan (dipakai bila item tidak ada di daftar aktif).
    const petaTerpilih = new Map(
      ((Array.isArray(dataTerpilih) ? (dataTerpilih as Item[]) : []) as Item[]).map((it) => [it.id, it]),
    );
    const tambahan: Item[] = [];
    for (const c of barisCapaian) {
      const ci = Array.isArray(c.curriculum_items) ? c.curriculum_items[0] : c.curriculum_items;
      const dariRpc = petaTerpilih.get(c.item_id);
      if (dariRpc) {
        tambahan.push(dariRpc);
        continue;
      }
      if (ci?.label)
        tambahan.push({
          id: c.item_id,
          subject_id: c.subject_id,
          label: berlabel(c.subject_id, ci.label),
          value: null,
          siklik: false,
        });
    }
    setItemTambahan(tambahan);

    // Teks "bulan lalu" per santri|bidang: label item dari view (bukan angka posisi).
    const petaInfo: Record<string, InfoLalu> = {};
    for (const [kunci, r] of petaLalu) {
      petaInfo[kunci] = { teks: r.item_label ?? null, putaran: r.putaran ?? null, pos: r.pos ?? null };
    }
    setInfoLalu(petaInfo);

    // Isi tersimpan bulan ini menurut view (pos, selisih, teks) — untuk penanda "sudah mundur".
    const petaKini = new Map(
      ((laporanKini.data ?? []) as unknown as Array<{
        student_id: string;
        subject_id: string;
        pos: number | null;
        putaran: number | null;
        item_label: string | null;
        prev_item_label: string | null;
        selisih: number | null;
      }>).map((r) => [`${r.student_id}|${r.subject_id}`, r]),
    );

    // Hanya baris pada bulan yang sedang dibuka (jaga-jaga bila ada baris lain).
    const barisPresensi = (presensi.data ?? []).filter((p) => p.month_id === bulanId);
    const petaPresensi = new Map(barisPresensi.map((p) => [p.student_id, p]));
    const barisCatatan = (catatan.data ?? []).filter((c) => c.month_id === bulanId);
    const petaCatatan = new Map(barisCatatan.map((c) => [c.student_id, c.note]));

    setBaris(
      (st.data ?? []).map((s) => {
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

    // Nama bulan lalu untuk keterangan di form.
    void bulanLaluNama;
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
        return ((data ?? []) as Item[]).map((it) => ({ nilai: it.id, label: it.label }));
      },
      cari: async (kata: string) => {
        const { data, error } = await supabase.rpc("curriculum_items_search", {
          p_subject: subjectId,
          p_q: kata,
          p_limit: 60,
        });
        if (error) throw new Error(error.message);
        return ((data ?? []) as Item[]).map((it) => ({ nilai: it.id, label: it.label }));
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
          items={[...items, ...itemTambahan]}
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
