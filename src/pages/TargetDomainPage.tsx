import { useEffect, useMemo, useState } from "react";
import PemilihTahunBulan, { type BulanData } from "../components/PemilihTahunBulan";
import PemilihHalaqah, {
  ambilGuru,
  ambilPengampu,
  halaqahDiampu,
  type HalaqahData,
} from "../components/PemilihHalaqah";
import DropdownCari from "../components/DropdownCari";
import FormTarget from "../components/FormTarget";
import DialogRiwayatTarget from "../components/DialogRiwayatTarget";
import DialogAksiTarget, { type JenisAksiTarget } from "../components/DialogAksiTarget";
import TabelTargetHalaqah, { type GrupHalaqah } from "../components/TabelTargetHalaqah";
import { supabase } from "../lib/supabase";
import { ambilSemua } from "../lib/ambil-semua";
import { angka } from "../lib/laporan";
import {
  adalahAksesPenuh,
  bolehSetujuiTarget,
  DOMAIN_LABEL,
  hanyaHalaqahDiampu,
  type Domain,
} from "../lib/roles";
import { useAuth } from "../lib/auth-context";
import {
  batalkanTarget,
  infoKonfirmasi,
  setujuiTarget,
  setujuiTargetHalaqah,
  STATUS_GAYA,
  STATUS_LABEL,
  tolakTarget,
  type BarisTarget,
  type TargetStatus,
} from "../lib/target";

interface Bidang {
  id: string;
  name: string;
}

/**
 * Baris target untuk tampilan. Nama sasaran, mapel, bulan, dan pelaku diambil
 * SEKALIGUS lewat embed PostgREST, supaya halaman tidak perlu mengunduh seluruh
 * daftar santri/profil hanya untuk menampilkan nama.
 */
type BarisTargetTampil = BarisTarget & {
  santri: { full_name: string } | null;
  halaqah: { code: string } | null;
  mapel: { name: string } | null;
  target_item: { label: string } | null;
  bulan: {
    name: string;
    month_no: number;
    academic_years: { hijri_year: number } | { hijri_year: number }[];
  } | null;
  pengaju: { full_name: string } | null;
  penyetuju: { full_name: string } | null;
  penolak: { full_name: string } | null;
};

const STATUS_URUT: TargetStatus[] = ["diajukan", "disetujui", "ditolak", "dibatalkan"];

/**
 * Halaman daftar target satu domain (T7 [2/2]); dibungkus `TargetPage` yang
 * menyediakan tab domain.
 *
 * Menampilkan target dari tabel `targets` (SELECT dibaca langsung, tulis lewat RPC).
 * Saringan: Tahun + Bulan berlaku (dua dropdown terpisah), halaqah, mata pelajaran,
 * status. Pengampu (Musyrif/ah, Mudarris/ah) hanya melihat halaqah yang diampu.
 *
 * Catatan bentuk target: target Al Qur'an disimpan per SANTRI (`halaqah_id` NULL),
 * target Wasilah/Ghayah per HALAQAH (`student_id` NULL). Karena itu saringan halaqah
 * untuk Al Qur'an memakai keanggotaan `halaqah_members`.
 */
export default function TargetDomainPage({ domain }: { domain: Domain }) {
  const { profile } = useAuth();
  const isAlquran = domain === "alquran";

  const [memuatAwal, setMemuatAwal] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);
  const [pesan, setPesan] = useState<string | null>(null);

  const [halaqahList, setHalaqahList] = useState<HalaqahData[]>([]);
  const [pengampu, setPengampu] = useState<Record<string, string>>({});
  const [bulanList, setBulanList] = useState<BulanData[]>([]);
  const [bidang, setBidang] = useState<Bidang[]>([]);
  const [halaqahPeta, setHalaqahPeta] = useState<Map<string, string>>(new Map());
  /** student_id -> kode halaqah pada domain ini (untuk menampilkan sasaran Al Qur'an). */
  const [siswaHalaqah, setSiswaHalaqah] = useState<Map<string, string[]>>(new Map());
  /** halaqah_id -> daftar student_id anggota aktif (saringan Al Qur'an). */
  const [anggotaHalaqah, setAnggotaHalaqah] = useState<Map<string, string[]>>(new Map());
  /** halaqah_id -> mapel aktif pada bulan matriks (Wasilah/Ghayah). */
  const [mapelHalaqah, setMapelHalaqah] = useState<Map<string, { id: string; name: string }[]>>(
    new Map(),
  );
  /** Bulan matriks target Wasilah/Ghayah (satu bulan, dipilih lewat saringan). */
  const [bulanMatriks, setBulanMatriks] = useState("");

  const [tahun, setTahun] = useState<number | "">("");
  const [bulanId, setBulanId] = useState("");
  const [halaqahId, setHalaqahId] = useState("");
  const [mapelId, setMapelId] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | TargetStatus>("");

  const [baris, setBaris] = useState<BarisTargetTampil[]>([]);
  const [memuat, setMemuat] = useState(true);
  const [muatUlangKe, setMuatUlangKe] = useState(0);

  const [form, setForm] = useState<null | { mode: "ajukan" | "ubah"; target?: BarisTargetTampil }>(null);
  const [riwayat, setRiwayat] = useState<null | {
    judul: string;
    subjectId: string;
    studentId: string | null;
    halaqahId: string | null;
  }>(null);
  const [aksi, setAksi] = useState<null | {
    jenis: JenisAksiTarget;
    target: BarisTargetTampil;
    perluKonfirmasi: boolean;
    lewat: boolean;
  }>(null);
  const [sedang, setSedang] = useState(false);

  const aksesPenuh = !!profile && adalahAksesPenuh(profile.role);
  const bolehSetujui = !!profile && bolehSetujuiTarget(profile.role, domain);
  const batasiAmanah = !!profile && hanyaHalaqahDiampu(profile.role);

  const labelHalaqah = isAlquran ? "Halaqah" : domain === "wasilah" ? "Level" : "Kelompok";

  // ---- Muat daftar pilihan (sekali per domain) ----
  useEffect(() => {
    if (!profile) return;
    let aktif = true;
    setMemuatAwal(true);
    setGalat(null);
    void (async () => {
      const [h, b, s, anggota, guru] = await Promise.all([
        supabase
          .from("halaqahs")
          .select("id, code, name")
          .eq("domain", domain)
          .eq("is_active", true)
          .order("code"),
        supabase
          .from("hijri_months")
          .select("id, month_no, name, academic_years!inner(hijri_year)")
          .order("month_no"),
        supabase.from("subjects").select("id, name").eq("domain", domain).order("sort_order"),
        ambilSemua<{ student_id: string; halaqah_id: string }>((awal, jumlah) =>
          supabase
            .from("halaqah_members")
            .select("student_id, halaqah_id, halaqahs!inner(domain)")
            .eq("halaqahs.domain", domain)
            .is("left_on", null)
            .order("id", { ascending: true })
            .range(awal, awal + jumlah - 1),
        ),
        ambilGuru(),
      ]);
      if (!aktif) return;

      const pesanGalat = h.error?.message ?? b.error?.message ?? s.error?.message ?? anggota.error?.message;
      if (pesanGalat) {
        setGalat(pesanGalat);
        setMemuatAwal(false);
        return;
      }

      const petaGuru = await ambilPengampu();
      if (!aktif) return;
      setPengampu(petaGuru);

      const halaqahData = (h.data ?? []) as HalaqahData[];
      const ampu = batasiAmanah ? halaqahDiampu(guru, profile.id) : null;
      const daftarHalaqah = halaqahData.filter((x) => !ampu || ampu.has(x.id));
      setHalaqahList(daftarHalaqah);
      setHalaqahPeta(new Map(halaqahData.map((x) => [x.id, x.code])));
      setHalaqahId((prev) => prev || (batasiAmanah ? daftarHalaqah[0]?.id ?? "" : ""));

      const semuaBulan = ((b.data ?? []) as unknown as Array<{
        id: string;
        month_no: number;
        name: string;
        academic_years: { hijri_year: number } | { hijri_year: number }[];
      }>).map((m) => {
        const ay = Array.isArray(m.academic_years) ? m.academic_years[0] : m.academic_years;
        return { id: m.id, month_no: m.month_no, name: m.name, hijri_year: ay?.hijri_year ?? 0 };
      });
      semuaBulan.sort((a, c) => a.hijri_year - c.hijri_year || a.month_no - c.month_no);
      setBulanList(semuaBulan);
      const tahunTerakhir = semuaBulan[semuaBulan.length - 1]?.hijri_year ?? "";
      setTahun((prev) => (prev !== "" ? prev : tahunTerakhir));
      // Bulan kosong = semua bulan pada tahun itu (target lama bisa berlaku mulai Data Awal).
      setBulanId("");

      setBidang((s.data ?? []) as Bidang[]);

      const anggotaMap = new Map<string, string[]>();
      const siswaMap = new Map<string, string[]>();
      for (const a of anggota.data ?? []) {
        const arr = anggotaMap.get(a.halaqah_id) ?? [];
        arr.push(a.student_id);
        anggotaMap.set(a.halaqah_id, arr);
        const kode = halaqahPetaBaru(halaqahData, a.halaqah_id);
        if (kode) {
          const daftar = siswaMap.get(a.student_id) ?? [];
          if (!daftar.includes(kode)) daftar.push(kode);
          siswaMap.set(a.student_id, daftar);
        }
      }
      setAnggotaHalaqah(anggotaMap);
      setSiswaHalaqah(siswaMap);
      setMemuatAwal(false);
    })().catch((e: unknown) => {
      setGalat(`Gagal memuat pilihan: ${e instanceof Error ? e.message : String(e)}`);
      setMemuatAwal(false);
    });
    return () => {
      aktif = false;
    };
  }, [domain, profile, batasiAmanah]);

  const bulanTahun = useMemo(
    () => bulanList.filter((b) => Number(b.hijri_year) === Number(tahun)),
    [bulanList, tahun],
  );
  const bulanPeta = useMemo(
    () => new Map(bulanList.map((b) => [b.id, b])),
    [bulanList],
  );
  const mapelPeta = useMemo(() => new Map(bidang.map((b) => [b.id, b.name])), [bidang]);

  // ---- Wasilah/Ghayah: mapel aktif tiap halaqah untuk matriks target ----
  useEffect(() => {
    if (isAlquran || memuatAwal || halaqahList.length === 0) {
      setMapelHalaqah(new Map());
      setBulanMatriks("");
      return;
    }
    let aktif = true;
    void (async () => {
      let bulan = bulanId;
      if (!bulan) {
        const { data } = await supabase.rpc("target_bulan_berjalan", { p_domain: domain });
        bulan = (data as unknown as string) ?? "";
      }
      if (!bulan) bulan = bulanTahun[bulanTahun.length - 1]?.id ?? "";
      if (!aktif) return;
      setBulanMatriks(bulan);
      if (!bulan) {
        setMapelHalaqah(new Map());
        return;
      }
      const hasil = await Promise.all(
        halaqahList.map(async (h) => {
          const { data, error } = await supabase.rpc("halaqah_mapel_aktif", {
            p_halaqah: h.id,
            p_bulan: bulan,
          });
          if (error) return [h.id, [] as { id: string; name: string }[]] as const;
          return [
            h.id,
            ((data ?? []) as Array<{ subject_id: string; name: string }>).map((x) => ({
              id: x.subject_id,
              name: x.name,
            })),
          ] as const;
        }),
      );
      if (aktif) setMapelHalaqah(new Map(hasil));
    })();
    return () => {
      aktif = false;
    };
  }, [domain, isAlquran, memuatAwal, halaqahList, bulanId, bulanTahun]);

  // ---- Matriks target: satu grup per halaqah ----
  const grup = useMemo<GrupHalaqah<BarisTargetTampil>[]>(
    () =>
      (halaqahId ? halaqahList.filter((h) => h.id === halaqahId) : halaqahList).map((h) => {
        const mapel = mapelHalaqah.get(h.id) ?? [];
        return {
          halaqahId: h.id,
          code: h.code,
          pengampu: pengampu[h.id] ?? "",
          mapel,
          tanpaMapel: mapel.length === 0,
          baris: baris.filter(
            (b) =>
              b.halaqah_id === h.id &&
              (!bulanMatriks || b.effective_month_id === bulanMatriks) &&
              (!mapelId || b.subject_id === mapelId),
          ),
        };
      }),
    [halaqahList, halaqahId, pengampu, mapelHalaqah, baris, bulanMatriks, mapelId],
  );
  const kolomMapel = useMemo(() => {
    const peta = new Map<string, { id: string; name: string }>();
    for (const g of grup) for (const m of g.mapel) peta.set(m.id, m);
    return [...peta.values()].sort((a, b) => a.name.localeCompare(b.name));
  }, [grup]);
  const namaBulanMatriks = useMemo(() => {
    const b = bulanPeta.get(bulanMatriks);
    return b ? `${b.name} ${b.hijri_year}` : "";
  }, [bulanPeta, bulanMatriks]);

  // ---- Muat daftar target sesuai saringan ----
  useEffect(() => {
    let aktif = true;
    if (memuatAwal) return;
    const bulanQuery = bulanId ? [bulanId] : bulanTahun.map((b) => b.id);
    if (bulanQuery.length === 0) {
      setBaris([]);
      setMemuat(false);
      return;
    }
    const siswaHalaqahTerpilih = halaqahId ? anggotaHalaqah.get(halaqahId) ?? [] : null;

    setMemuat(true);
    setGalat(null);
    void (async () => {
      if (halaqahId && isAlquran && (!siswaHalaqahTerpilih || siswaHalaqahTerpilih.length === 0)) {
        if (aktif) {
          setBaris([]);
          setMemuat(false);
        }
        return;
      }
      const { data, error } = await ambilSemua<BarisTargetTampil>((awal, jumlah) => {
        let q = supabase
          .from("targets")
          .select(
            "id, domain, subject_id, student_id, halaqah_id, effective_month_id, amount, amount_period, target_item_id, status, proposed_by, approved_by, approved_at, rejected_by, rejected_at, alasan_tolak, note, created_at, santri:students(full_name), halaqah:halaqahs(code), mapel:subjects(name), target_item:curriculum_items(label), bulan:hijri_months(name, month_no, academic_years(hijri_year)), pengaju:profiles!targets_proposed_by_fkey(full_name), penyetuju:profiles!targets_approved_by_fkey(full_name), penolak:profiles!targets_rejected_by_fkey(full_name)",
          )
          .eq("domain", domain)
          .in("effective_month_id", bulanQuery)
          .order("created_at", { ascending: false })
          .order("id", { ascending: false })
          .range(awal, awal + jumlah - 1);
        if (halaqahId && isAlquran) q = q.in("student_id", siswaHalaqahTerpilih ?? []);
        if (halaqahId && !isAlquran) q = q.eq("halaqah_id", halaqahId);
        if (mapelId) q = q.eq("subject_id", mapelId);
        if (statusFilter) q = q.eq("status", statusFilter);
        // Bentuk hasil sudah sesuai `select` di atas; supabase-js tidak dapat
        // menyimpulkan tipe embed dari string select, jadi disamakan di sini.
        return q as unknown as PromiseLike<{
          data: BarisTargetTampil[] | null;
          error: { message: string } | null;
        }>;
      });
      if (!aktif) return;
      if (error) {
        setGalat(error.message);
        setMemuat(false);
        return;
      }
      setBaris(data);
      setMemuat(false);
    })();
    return () => {
      aktif = false;
    };
  }, [
    domain,
    isAlquran,
    memuatAwal,
    bulanId,
    bulanTahun,
    halaqahId,
    anggotaHalaqah,
    mapelId,
    statusFilter,
    muatUlangKe,
  ]);

  function gantiTahun(t: number) {
    setTahun(t);
    if (bulanId && !bulanList.some((b) => b.id === bulanId && Number(b.hijri_year) === t)) {
      setBulanId("");
    }
  }

  async function muatUlang() {
    setMuatUlangKe((k) => k + 1);
  }

  function teksSasaran(t: BarisTargetTampil): string {
    if (t.student_id) {
      const nama = t.santri?.full_name ?? "—";
      // Kode halaqah santri tetap diambil dari keanggotaan (target Al Qur'an tidak
      // menyimpan halaqah_id, hanya student_id).
      const halaqah = siswaHalaqah.get(t.student_id)?.join(", ");
      return halaqah ? `${nama} (${halaqah})` : nama;
    }
    if (t.halaqah_id) return t.halaqah?.code ?? halaqahPeta.get(t.halaqah_id) ?? "—";
    return "—";
  }

  function teksBulan(t: BarisTargetTampil): string {
    const b = t.bulan;
    if (!b) {
      const peta = bulanPeta.get(t.effective_month_id);
      if (!peta) return "—";
      return peta.month_no === 0
        ? `${peta.name} ${peta.hijri_year} (Data Awal)`
        : `${peta.name} ${peta.hijri_year}`;
    }
    const ay = Array.isArray(b.academic_years) ? b.academic_years[0] : b.academic_years;
    const tahun = ay?.hijri_year ?? "";
    return b.month_no === 0 ? `${b.name} ${tahun} (Data Awal)` : `${b.name} ${tahun}`;
  }

  const jumlahMenunggu = useMemo(
    () => baris.filter((b) => b.status === "diajukan").length,
    [baris],
  );

  async function bukaAksi(jenis: JenisAksiTarget, target: BarisTargetTampil) {
    setPesan(null);
    let perluKonfirmasi = false;
    let lewat = false;
    try {
      const info = await infoKonfirmasi(domain, target.effective_month_id);
      perluKonfirmasi = !!info?.perlu_konfirmasi;
      lewat = !!info?.lewat;
    } catch {
      /* biarkan database menolak bila perlu */
    }
    setAksi({ jenis, target, perluKonfirmasi, lewat });
  }

  async function jalankanAksi(opsi: { alasan: string; konfirmasi: boolean }) {
    if (!aksi) return;
    setSedang(true);
    setPesan(null);
    try {
      if (aksi.jenis === "setujui") {
        await setujuiTarget(aksi.target.id, opsi.konfirmasi);
        setPesan("Target disetujui dan mulai dipakai laporan pada bulan berlakunya.");
      } else if (aksi.jenis === "tolak") {
        await tolakTarget(aksi.target.id, opsi.alasan, opsi.konfirmasi);
        setPesan("Target ditolak. Alasan tersimpan dan target tetap ada di riwayat.");
      } else {
        await batalkanTarget(aksi.target.id);
        setPesan("Pengajuan target dibatalkan (baris tetap tersimpan sebagai riwayat).");
      }
      setAksi(null);
      await muatUlang();
    } catch (e) {
      setPesan(`Gagal: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setSedang(false);
    }
  }

  /** Bulk "Setujui semua target halaqah ini" (Masul domain/Mudir/Admin). */
  async function setujuiSemua(halaqahSatu: string) {
    setPesan(null);
    try {
      const info = bulanMatriks ? await infoKonfirmasi(domain, bulanMatriks) : null;
      if (info?.perlu_konfirmasi) {
        if (!aksesPenuh) {
          setPesan("Gagal: bulan sudah lewat/terkunci. Hanya Mudir atau Admin yang dapat menyetujui.");
          return;
        }
        const lanjut = window.confirm(
          `${info.lewat ? "Bulan sudah lewat" : "Bulan sudah dikunci"}. Tetap setujui semua target halaqah ini?`,
        );
        if (!lanjut) return;
      }
      setSedang(true);
      const h = await setujuiTargetHalaqah({
        halaqahId: halaqahSatu,
        bulanId: bulanMatriks || null,
        konfirmasi: !!info?.perlu_konfirmasi,
      });
      setPesan(`${h.jumlah ?? 0} target disetujui${bulanMatriks ? ` untuk ${namaBulanMatriks}` : ""}.`);
      await muatUlang();
    } catch (e) {
      setPesan(`Gagal: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setSedang(false);
    }
  }

  /** Tombol aksi yang sama dipakai tabel desktop dan kartu HP. */
  function tombolAksi(t: BarisTargetTampil) {
    const bolehBatalkan = t.status === "diajukan" && t.proposed_by === profile?.id;
    const bolehUbah = t.status === "disetujui" || t.status === "diajukan";
    return (
      <div className="flex flex-wrap gap-1.5">
        {t.status === "diajukan" && bolehSetujui && (
          <>
            <button
              type="button"
              onClick={() => void bukaAksi("setujui", t)}
              className="rounded border border-emerald-300 bg-white px-2 py-1 text-xs font-medium text-emerald-800 hover:bg-emerald-50"
            >
              Setujui
            </button>
            <button
              type="button"
              onClick={() => void bukaAksi("tolak", t)}
              className="rounded border border-red-300 bg-white px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
            >
              Tolak
            </button>
          </>
        )}
        {bolehBatalkan && (
          <button
            type="button"
            onClick={() => void bukaAksi("batalkan", t)}
            className="rounded border border-gray-300 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
          >
            Batalkan
          </button>
        )}
        {bolehUbah && (
          <button
            type="button"
            onClick={() => {
              setPesan(null);
              setForm({ mode: "ubah", target: t });
            }}
            className="rounded border border-kusafa/40 bg-white px-2 py-1 text-xs font-medium text-kusafa hover:bg-kusafa-light"
          >
            Ubah
          </button>
        )}
        <button
          type="button"
          onClick={() =>
            setRiwayat({
              judul: `${teksSasaran(t)} · ${mapelPeta.get(t.subject_id) ?? ""}`,
              subjectId: t.subject_id,
              studentId: t.student_id,
              halaqahId: t.halaqah_id,
            })
          }
          className="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
        >
          Riwayat
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <PemilihHalaqah
            id={`target-filter-halaqah-${domain}`}
            label={labelHalaqah}
            halaqah={halaqahList}
            pengampu={pengampu}
            nilai={halaqahId}
            onChange={setHalaqahId}
            opsiKosong={batasiAmanah ? undefined : `Semua ${labelHalaqah.toLowerCase()}`}
            keterangan={
              batasiAmanah
                ? "Hanya halaqah yang Anda ampu."
                : pengampu[halaqahId]
                  ? `Pengampu: ${pengampu[halaqahId]}`
                  : undefined
            }
          />

          <PemilihTahunBulan
            bulan={bulanList}
            tahun={tahun}
            bulanId={bulanId}
            idAwalan={`target-filter-bulan-${domain}`}
            onTahun={gantiTahun}
            onBulan={setBulanId}
            domain={domain}
            catatan="Bulan kosong = semua bulan pada tahun itu."
          />

          <DropdownCari
            id={`target-filter-mapel-${domain}`}
            label="Mata pelajaran"
            opsi={bidang.map((b) => ({ nilai: b.id, label: b.name }))}
            nilai={mapelId}
            onChange={setMapelId}
            opsiKosong="Semua mata pelajaran"
            placeholderCari="Ketik mata pelajaran..."
          />

          <DropdownCari
            id={`target-filter-status-${domain}`}
            label="Status"
            opsi={STATUS_URUT.map((s) => ({ nilai: s, label: STATUS_LABEL[s] }))}
            nilai={statusFilter}
            onChange={(v) => setStatusFilter((v as TargetStatus) || "")}
            opsiKosong="Semua status"
            placeholderCari="Ketik status..."
          />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-black/5 pt-3">
          <button
            type="button"
            onClick={() => {
              setPesan(null);
              setForm({ mode: "ajukan" });
            }}
            className="rounded-lg bg-kusafa px-3 py-2 text-sm font-medium text-white hover:bg-kusafa/90"
          >
            Ajukan target
          </button>
          <p className="text-xs text-gray-600">
            {bolehSetujui
              ? "Anda boleh menyetujui/menolak target domain ini."
              : "Pengampu mengajukan target; persetujuan oleh Masul domain, Mudir, atau Admin."}
          </p>
        </div>
      </div>

      {galat && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          {galat}
        </p>
      )}
      {pesan && (
        <p role="status" className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
          {pesan}
        </p>
      )}

      <div className="rounded-xl bg-white ring-1 ring-black/5">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/5 px-4 py-3">
          <h2 className="text-base font-bold text-gray-900">
            Daftar target {DOMAIN_LABEL[domain]}
          </h2>
          <p className="text-xs text-gray-600">
            {memuat ? "memuat..." : `${baris.length} target`}
            {jumlahMenunggu > 0 ? ` · ${jumlahMenunggu} menunggu persetujuan` : ""}
          </p>
        </div>

        {memuatAwal ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">Memuat...</p>
        ) : batasiAmanah && halaqahList.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">
            Belum ada halaqah yang Anda ampu pada domain ini.
          </p>
        ) : !isAlquran ? (
          <div className="space-y-2">
            <p className="text-xs text-gray-600">
              Bulan berlaku: <strong>{namaBulanMatriks || "—"}</strong> · satu baris per {labelHalaqah.toLowerCase()},
              kolom = mapel aktif bulan itu (butir tujuan akhir + status).
            </p>
            {memuat && (
              <p className="px-4 py-2 text-center text-sm text-gray-600">Memuat target...</p>
            )}
            <TabelTargetHalaqah
              domain={domain}
              labelHalaqah={labelHalaqah}
              grup={grup}
              mapel={mapelId ? kolomMapel.filter((m) => m.id === mapelId) : kolomMapel}
              bolehSetujui={bolehSetujui}
              aksesPenuh={aksesPenuh}
              profileId={profile?.id}
              sedang={sedang}
              onSetujuiSemua={(id) => void setujuiSemua(id)}
              onAksi={(jenis, target) => void bukaAksi(jenis, target)}
              onUbah={(target) => {
                setPesan(null);
                setForm({ mode: "ubah", target });
              }}
              onRiwayat={(target) =>
                setRiwayat({
                  judul: `${target.halaqah?.code ?? teksSasaran(target)} · ${mapelPeta.get(target.subject_id) ?? ""}`,
                  subjectId: target.subject_id,
                  studentId: target.student_id,
                  halaqahId: target.halaqah_id,
                })
              }
            />
          </div>
        ) : baris.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">
            {memuat ? "Memuat target..." : "Belum ada target pada saringan ini."}
          </p>
        ) : (
          <>
            {/* HP 360 px: kartu ringkas, tanpa perlu menggeser tabel 820 px. */}
            <ul className="divide-y divide-black/5 lg:hidden">
              {baris.map((t) => (
                <li key={t.id} className="px-4 py-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-900">{teksSasaran(t)}</p>
                      <p className="mt-0.5 text-xs text-gray-700">
                        {mapelPeta.get(t.subject_id) ?? "—"} · target {angka(t.amount)}{" "}
                        {t.amount_period === "harian" ? "per hari" : "per bulan"}
                      </p>
                      <p className="text-xs text-gray-600">Mulai {teksBulan(t)}</p>
                      {t.note && <p className="mt-0.5 text-xs text-gray-500">{t.note}</p>}
                      {t.status === "ditolak" && t.alasan_tolak && (
                        <p className="mt-0.5 text-xs text-red-700">Alasan: {t.alasan_tolak}</p>
                      )}
                    </div>
                    <span
                      className={
                        "shrink-0 rounded px-1.5 py-0.5 text-xs font-medium " + STATUS_GAYA[t.status]
                      }
                    >
                      {STATUS_LABEL[t.status]}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-600">
                    Pengaju: {t.pengaju?.full_name ?? "—"}
                    {t.penyetuju?.full_name ? ` · Disetujui: ${t.penyetuju.full_name}` : ""}
                    {t.penolak?.full_name ? ` · Ditolak: ${t.penolak.full_name}` : ""}
                  </p>
                  <div className="mt-2">{tombolAksi(t)}</div>
                </li>
              ))}
            </ul>

            <div className="hidden w-full overflow-x-auto lg:block">
              <table className="w-full min-w-[820px] border-collapse text-sm">
              <thead>
                <tr className="bg-kusafa-light text-xs uppercase tracking-wide text-kusafa">
                  <th scope="col" className="px-3 py-2 text-left">
                    Sasaran
                  </th>
                  <th scope="col" className="px-3 py-2 text-left">
                    Mata pelajaran
                  </th>
                  <th scope="col" className="px-3 py-2 text-left">
                    Target
                  </th>
                  <th scope="col" className="px-3 py-2 text-left">
                    Berlaku mulai
                  </th>
                  <th scope="col" className="px-3 py-2 text-left">
                    Status
                  </th>
                  <th scope="col" className="px-3 py-2 text-left">
                    Pengaju / penyetuju
                  </th>
                  <th scope="col" className="px-3 py-2 text-left">
                    Aksi
                  </th>
                </tr>
              </thead>
              <tbody>
                {baris.map((t) => {
                  return (
                    <tr key={t.id} className="border-t border-black/5 align-top">
                      <th scope="row" className="px-3 py-3 text-left font-medium text-gray-900">
                        {teksSasaran(t)}
                        {t.note && (
                          <span className="mt-0.5 block text-xs font-normal text-gray-500">{t.note}</span>
                        )}
                      </th>
                      <td className="px-3 py-3 text-gray-800">
                        {mapelPeta.get(t.subject_id) ?? "—"}
                      </td>
                      <td className="whitespace-nowrap px-3 py-3">
                        <span className="font-semibold text-gray-900">{angka(t.amount)}</span>
                        <span className="block text-xs text-gray-500">
                          {t.amount_period === "harian" ? "per hari" : "per bulan"}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-gray-800">{teksBulan(t)}</td>
                      <td className="px-3 py-3">
                        <span
                          className={
                            "inline-block rounded px-1.5 py-0.5 text-xs font-medium " + STATUS_GAYA[t.status]
                          }
                        >
                          {STATUS_LABEL[t.status]}
                        </span>
                        {t.status === "ditolak" && t.alasan_tolak && (
                          <span className="mt-1 block text-xs text-red-700">
                            Alasan: {t.alasan_tolak}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-3 text-xs text-gray-700">
                        <span className="block">
                          <span className="text-gray-500">Pengaju: </span>
                          {t.pengaju?.full_name ?? "—"}
                        </span>
                        {t.penyetuju?.full_name && (
                          <span className="block">
                            <span className="text-gray-500">Disetujui: </span>
                            {t.penyetuju.full_name}
                          </span>
                        )}
                        {t.penolak?.full_name && (
                          <span className="block">
                            <span className="text-gray-500">Ditolak: </span>
                            {t.penolak.full_name}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-3">{tombolAksi(t)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </div>
          </>
        )}
      </div>

      <div className="rounded-lg bg-white px-4 py-3 text-xs text-gray-700 ring-1 ring-black/5">
        <p>
          Target <strong>disetujui</strong> dipakai laporan pada bulan berlakunya sampai diganti. Target
          <strong> diajukan</strong> belum dipakai. Target lama tidak dihapus; mengubah target membuat baris baru.
          Target Al Qur'an harian; target Ilmu Wasilah dan Ilmu Ghayah bulanan langsung (tidak dikali Hadir).
        </p>
      </div>

      {form && (
        <FormTarget
          domain={domain}
          mode={form.mode}
          target={form.target ?? null}
          halaqah={halaqahList}
          pengampu={pengampu}
          bulan={bulanList}
          bidang={bidang}
          halaqahAwal={halaqahId}
          sedang={sedang}
          onSedang={setSedang}
          onBatal={() => setForm(null)}
          onSelesai={(p) => {
            setForm(null);
            setPesan(p);
            void muatUlang();
          }}
        />
      )}

      {riwayat && (
        <DialogRiwayatTarget
          judul={riwayat.judul}
          subjectId={riwayat.subjectId}
          studentId={riwayat.studentId}
          halaqahId={riwayat.halaqahId}
          onTutup={() => setRiwayat(null)}
        />
      )}

      {aksi && (
        <DialogAksiTarget
          aksi={aksi.jenis}
          ringkasan={`${teksSasaran(aksi.target)} · ${mapelPeta.get(aksi.target.subject_id) ?? "—"} · target ${angka(
            aksi.target.amount,
          )} ${aksi.target.amount_period === "harian" ? "per hari" : "per bulan"} · mulai ${teksBulan(aksi.target)}`}
          perluKonfirmasi={aksi.perluKonfirmasi}
          lewat={aksi.lewat}
          aksesPenuh={aksesPenuh}
          sedang={sedang}
          onBatal={() => setAksi(null)}
          onJalankan={(opsi) => void jalankanAksi(opsi)}
        />
      )}
    </div>
  );
}

/** Kode halaqah dari daftar halaqah yang sudah dimuat. */
function halaqahPetaBaru(daftar: HalaqahData[], id: string): string | undefined {
  return daftar.find((h) => h.id === id)?.code;
}
