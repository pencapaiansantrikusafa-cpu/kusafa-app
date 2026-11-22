import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { navItemsFor } from "../lib/roles";
import { supabase } from "../lib/supabase";
import FormInputAlQuran, { type BarisInput, type BidangInput } from "./FormInputAlQuran";
import PemilihTahunBulan from "../components/PemilihTahunBulan";
import PemilihHalaqah, { ambilPengampu } from "../components/PemilihHalaqah";

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

interface Item {
  id: string;
  subject_id: string;
  label: string;
  value: string | null;
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
  const [items, setItems] = useState<Item[]>([]);
  // Item capaian yang sudah tersimpan tetapi belum ada di daftar aktif (mis. sudah dinonaktifkan).
  const [itemTambahan, setItemTambahan] = useState<Item[]>([]);
  const [baris, setBaris] = useState<BarisInput[]>([]);
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
      if (!aktif) return;
      if (h.error || b.error) {
        setGalat(h.error?.message ?? b.error?.message ?? null);
        setMemuat(false);
        return;
      }
      setHalaqahList(h.data ?? []);
      setPengampu(await ambilPengampu());
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
      setHalaqahId((prev) => prev || h.data?.[0]?.id || "");
      const bulanTerakhir = semua.filter((m) => m.month_no > 0).slice(-1)[0];
      setBulanId((prev) => prev || bulanTerakhir?.id || "");
      setTahun((prev) => (prev !== "" ? prev : bulanTerakhir?.hijri_year ?? ""));
      setMemuat(false);
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, []);

  // Muat isi form untuk halaqah + bulan terpilih.
  const muatIsi = useCallback(async () => {
    if (!halaqahId || !bulanId) return;
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
    const [st, capaian, presensi, catatan, semuaItem] = await Promise.all([
      supabase.from("students").select("id, full_name").in("id", anggota).order("full_name"),
      supabase
        .from("progress_entries")
        .select("student_id, subject_id, item_id, curriculum_items(label)")
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
      // curriculum_items tidak punya subject_id langsung; bidang diambil lewat books.
      supabase
        .from("curriculum_items")
        .select("id, label, value, is_active, books!inner(subject_id)")
        .in("books.subject_id", subjectIds)
        .eq("is_active", true)
        .order("seq")
        .limit(20000),
    ]);
    const galat2 =
      st.error ?? capaian.error ?? presensi.error ?? catatan.error ?? semuaItem.error;
    if (galat2) {
      setGalat(galat2.message);
      setMemuat(false);
      return;
    }

    // Ratakan relasi books.subject_id menjadi subject_id agar mudah dipakai form.
    const daftarItem: Item[] = ((semuaItem.data ?? []) as unknown as Array<{
      id: string;
      label: string;
      value: string | null;
      books: { subject_id: string } | { subject_id: string }[];
    }>).map((it) => {
      const bk = Array.isArray(it.books) ? it.books[0] : it.books;
      return { id: it.id, subject_id: bk?.subject_id ?? "", label: it.label, value: it.value };
    });
    setItems(daftarItem);

    const barisCapaian = (capaian.data ?? []) as unknown as Array<{
      student_id: string;
      subject_id: string;
      item_id: string;
      curriculum_items: { label: string } | { label: string }[] | null;
    }>;
    const petaCapaian = new Map(barisCapaian.map((c) => [`${c.student_id}|${c.subject_id}`, c.item_id]));

    // Label item tersimpan (dipakai bila item tidak ada di daftar aktif).
    const tambahan: Item[] = [];
    for (const c of barisCapaian) {
      const ci = Array.isArray(c.curriculum_items) ? c.curriculum_items[0] : c.curriculum_items;
      if (ci?.label) tambahan.push({ id: c.item_id, subject_id: c.subject_id, label: ci.label, value: null });
    }
    setItemTambahan(tambahan);
    // Hanya baris pada bulan yang sedang dibuka (jaga-jaga bila ada baris lain).
    const barisPresensi = (presensi.data ?? []).filter((p) => p.month_id === bulanId);
    const petaPresensi = new Map(barisPresensi.map((p) => [p.student_id, p]));
    const barisCatatan = (catatan.data ?? []).filter((c) => c.month_id === bulanId);
    const petaCatatan = new Map(barisCatatan.map((c) => [c.student_id, c.note]));

    setBaris(
      (st.data ?? []).map((s) => {
        const p = petaPresensi.get(s.id);
        const itemPerBidang: Record<string, string | null> = {};
        for (const bd of bidangList) itemPerBidang[bd.id] = petaCapaian.get(`${s.id}|${bd.id}`) ?? null;
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
        };
      }),
    );
    setMemuat(false);
  }, [halaqahId, bulanId]);

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

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{item?.label ?? "Input"}</h1>
        <p className="mt-1 text-sm text-gray-700">
          Mengisi capaian, kehadiran, dan catatan bulanan. T5 hanya Al Qur'an; Wasilah dan Ghayah di T6.
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
      </div>

      {galat && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          Gagal memuat: {galat}
        </p>
      )}

      {memuat ? (
        <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">Memuat data...</p>
      ) : baris.length === 0 ? (
        <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">
          Belum ada anggota di {namaHalaqah}.
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
          hariEfektif={hariEfektif}
          terkunci={terkunci}
          bolehHariEfektifKhusus={bolehHeKhusus}
          onSelesai={() => void muatIsi()}
        />
      )}
    </div>
  );
}