import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PemilihTahunBulan from "../components/PemilihTahunBulan";
import PemilihHalaqah, { ambilPengampu } from "../components/PemilihHalaqah";
import { DOMAIN_LABEL, type Domain } from "../lib/roles";
import { supabase } from "../lib/supabase";
import { ambilSemua } from "../lib/ambil-semua";
import { angka, type BarisLaporan } from "../lib/laporan";
import TabelAlQuran from "./TabelAlQuran";
import TabelWasilah, { type BarisHadir } from "./TabelWasilah";
import DialogHapusCapaian, { type InfoHapus, type InfoHapusMassal } from "../components/DialogHapusCapaian";
import { useAuth } from "../lib/auth-context";

interface Halaqah {
  id: string;
  code: string;
  name: string;
  category: string | null;
}

interface Bulan {
  id: string;
  month_no: number;
  name: string;
  hijri_year: number;
}

interface Santri {
  id: string;
  full_name: string;
}

interface Bidang {
  id: string;
  name: string;
}

export default function TabelCapaian({ domain }: { domain: Domain }) {
  const [halaqahList, setHalaqahList] = useState<Halaqah[]>([]);
  const [pengampu, setPengampu] = useState<Record<string, string>>({});
  const [bulanList, setBulanList] = useState<Bulan[]>([]);
  const [tahun, setTahun] = useState<number | "">("");
  const [halaqahId, setHalaqahId] = useState("");
  const [bulanId, setBulanId] = useState("");
  const [baris, setBaris] = useState<BarisLaporan[]>([]);
  const [santri, setSantri] = useState<Santri[]>([]);
  const [bidang, setBidang] = useState<Bidang[]>([]);
  /** Mata pelajaran yang ditetapkan untuk halaqah terpilih (`halaqah_subjects`). */
  const [bidangHalaqah, setBidangHalaqah] = useState<Bidang[]>([]);
  /** Kehadiran + catatan (Wasilah/Ghayah): keduanya dari tabel/view, bukan hitungan React. */
  const [hadir, setHadir] = useState<BarisHadir[]>([]);
  const [catatan, setCatatan] = useState<Record<string, string>>({});
  const [memuat, setMemuat] = useState(true);
  const [galat, setGalat] = useState<string | null>(null);
  const [detail, setDetail] = useState<Santri | null>(null);
  /** Admin/Mudir: dialog hapus sedang terbuka (satu capaian atau massal). */
  const [hapus, setHapus] = useState<
    | { jenis: "satu"; info: InfoHapus; siswa: string; mapel: string }
    | { jenis: "massal"; info: InfoHapusMassal; mapel: string }
    | null
  >(null);
  const [hapusSedang, setHapusSedang] = useState(false);
  const [hapusPesan, setHapusPesan] = useState<string | null>(null);

  // Daftar halaqah + pengampu, bulan, dan bidang.
  useEffect(() => {
    let aktif = true;
    async function muat() {
      setMemuat(true);
      setGalat(null);
      const [h, b, s] = await Promise.all([
        supabase
          .from("halaqahs")
          .select("id, code, name, category")
          .eq("domain", domain)
          .eq("is_active", true)
          .order("code"),
        supabase
          .from("hijri_months")
          .select("id, month_no, name, academic_years!inner(hijri_year)")
          .order("month_no"),
        supabase.from("subjects").select("id, name").eq("domain", domain).order("sort_order"),
        ]);

      setPengampu(await ambilPengampu());
      setHalaqahList(h.data ?? []);
      setBidang((s.data ?? []) as Bidang[]);
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
      setBulanList(semua);
      const halaqahAwal = h.data?.[0]?.id || "";
      setHalaqahId((prev) => prev || halaqahAwal);

      // Bulan default: bulan terakhir yang punya capaian pada domain ini.
      // Supabase mengembalikan maksimal 1.000 baris per permintaan, jadi `.limit(2000)`
      // dulu terpotong diam-diam begitu data bertambah. Sekarang memakai `ambilSemua`
      // dan disaring ke domain ini supaya angkanya tidak tercampur domain lain.
      const { data: adaData } = await ambilSemua<{ month_id: string }>((awal, jumlah) =>
        supabase
          .from("progress_entries")
          .select("month_id, subjects!inner(domain)")
          .eq("subjects.domain", domain)
          .in("month_id", semua.map((x) => x.id))
          .order("id", { ascending: true })
          .range(awal, awal + jumlah - 1),
      );
      if (!aktif) return;
      const punyaData = new Set((adaData ?? []).map((x) => x.month_id));
      const terakhir = [...semua].reverse().find((x) => punyaData.has(x.id));
      const dipilih = terakhir ?? semua[semua.length - 1];
      setTahun((prev) => (prev !== "" ? prev : dipilih?.hijri_year ?? ""));
      // Hanya terapkan pada pemuatan pertama; domain berikutnya punya state sendiri.
      setBulanId((prev) => prev || dipilih?.id || "");
      setMemuat(false);
    }
    void muat().catch((e: unknown) => {
      setGalat(`Gagal memuat: ${e instanceof Error ? e.message : String(e)}`);
      setMemuat(false);
    });
    return () => {
      aktif = false;
    };
  }, [domain]);

  // Isi tabel ketika pilihan berubah.
  const [muatUlangKe, setMuatUlangKe] = useState(0);
  async function muatUlang() {
    setMuatUlangKe((k) => k + 1);
  }
  useEffect(() => {
    let aktif = true;
    if (!halaqahId || !bulanId) return;
    setMemuat(true);
    setGalat(null);
    async function muat() {
      // Anggota diambil dari keanggotaan aktif halaqah ini saja. Santri yang tidak ikut
      // halaqah pada domain ini (mis. 1447.dummy-nis.023 di Ghayah) tidak pernah masuk.
      const [r, m, hs] = await Promise.all([
        supabase
          .from("v_monthly_report")
          .select(
            "halaqah_id, student_id, subject_id, month_id, pos, selisih, hadir, effective_days, target_monthly, below_target, attendance_short, item_label, prev_item_label",
          )
          .eq("halaqah_id", halaqahId)
          .eq("month_id", bulanId)
          .eq("domain", domain),
        supabase
          .from("halaqah_members")
          .select("student_id")
          .eq("halaqah_id", halaqahId)
          .is("left_on", null),
        supabase.from("halaqah_subjects").select("subject_id").eq("halaqah_id", halaqahId),
      ]);
      if (!aktif) return;
      if (r.error || m.error || hs.error) {
        setGalat(r.error?.message ?? m.error?.message ?? hs.error?.message ?? null);
        setMemuat(false);
        return;
      }
      const anggota = (m.data ?? []).map((x) => x.student_id);
      const mapelHalaqah = new Set((hs.data ?? []).map((x) => x.subject_id));

      const [st, att, notes] = await Promise.all([
        anggota.length
          ? supabase.from("students").select("id, full_name").in("id", anggota).order("full_name")
          : Promise.resolve({ data: [], error: null }),
        anggota.length
          ? supabase
              .from("v_attendance")
              .select("student_id, effective_days, izin, sakit, alpha, hadir")
              .eq("month_id", bulanId)
              .eq("domain", domain)
              .in("student_id", anggota)
          : Promise.resolve({ data: [], error: null }),
        anggota.length
          ? supabase
              .from("monthly_notes")
              .select("student_id, note")
              .eq("month_id", bulanId)
              .eq("domain", domain)
              .in("student_id", anggota)
          : Promise.resolve({ data: [], error: null }),
      ]);
      if (!aktif) return;
      if (st.error || att.error || notes.error) {
        setGalat(st.error?.message ?? att.error?.message ?? notes.error?.message ?? null);
        setMemuat(false);
        return;
      }
      setBaris((r.data ?? []) as unknown as BarisLaporan[]);
      setSantri((st.data ?? []) as Santri[]);
      setHadir((att.data ?? []) as unknown as BarisHadir[]);
      setCatatan(
        Object.fromEntries(
          ((notes.data ?? []) as Array<{ student_id: string; note: string }>).map((n) => [
            n.student_id,
            n.note,
          ]),
        ),
      );
      // Wasilah/Ghayah: hanya mata pelajaran yang ditetapkan halaqah ini (urutan `subjects`).
      setBidangHalaqah(bidang.filter((bd) => mapelHalaqah.has(bd.id)));
      setMemuat(false);
    }
    void muat();
    return () => {
      aktif = false;
    };
  }, [halaqahId, bulanId, domain, bidang, muatUlangKe]);

  function gantiTahun(t: number) {
    setTahun(t);
    const calon = bulanList.filter((b) => Number(b.hijri_year) === t);
    if (!calon.some((b) => b.id === bulanId)) {
      setBulanId(calon[calon.length - 1]?.id ?? "");
    }
  }

  // Ringkasan singkat untuk HP: santri mana yang belum sesuai target, bidang apa.
  const ringkasanHp = useMemo(() => {
    const peta = new Map<string, BarisLaporan>();
    for (const b of baris) peta.set(`${b.student_id}|${b.subject_id}`, b);
    const daftarBidang = domain === "alquran" ? bidang : bidangHalaqah;
    return santri.map((s) => {
      const masalah: string[] = [];
      const kosong: string[] = [];
      for (const bd of daftarBidang) {
        const r = peta.get(`${s.id}|${bd.id}`);
        if (!r || r.pos === null || r.target_monthly === null) kosong.push(bd.name);
        else if (r.below_target) masalah.push(bd.name);
      }
      return { santri: s, masalah, kosong };
    });
  }, [santri, bidang, bidangHalaqah, domain, baris]);

  const pengampuTerpilih = pengampu[halaqahId] ?? "";

  // ---- Hapus capaian (T6e): hanya Mudir/Admin. Cek role juga di dalam RPC (penjaga akhir). ----
  const { profile } = useAuth();
  const bolehHapus = profile?.role === "mudir" || profile?.role === "admin";

  async function bukaHapusSatu(siswa: string, mapel: string) {
    setHapusPesan(null);
    const { data, error } = await supabase.rpc("hapus_capaian_info", {
      p_siswa: siswa,
      p_mapel: mapel,
      p_bulan: bulanId,
    });
    if (error) {
      setHapusPesan(`Gagal memuat pratinjau: ${error.message}`);
      return;
    }
    const info = data as unknown as InfoHapus;
    if (!info?.ada) {
      setHapusPesan("Capaian itu sudah tidak ada (mungkin baru saja dihapus).");
      return;
    }
    setHapus({ jenis: "satu", info, siswa, mapel });
  }

  async function bukaHapusMassal(mapel: string) {
    setHapusPesan(null);
    const { data, error } = await supabase.rpc("hapus_capaian_massal_info", {
      p_halaqah: halaqahId,
      p_mapel: mapel,
      p_bulan: bulanId,
    });
    if (error) {
      setHapusPesan(`Gagal memuat pratinjau: ${error.message}`);
      return;
    }
    const info = data as unknown as InfoHapusMassal;
    if (!info?.ada) {
      setHapusPesan("Tidak ada capaian untuk halaqah, mata pelajaran, dan bulan itu.");
      return;
    }
    setHapus({ jenis: "massal", info, mapel });
  }

  async function jalankanHapus(opsi: { setujuTerkunci: boolean; setujuLanjutan: boolean }) {
    if (!hapus) return;
    setHapusSedang(true);
    setHapusPesan(null);
    try {
      if (hapus.jenis === "satu") {
        const { data, error } = await supabase.rpc("hapus_capaian", {
          p_siswa: hapus.siswa,
          p_mapel: hapus.mapel,
          p_bulan: bulanId,
          p_setuju_terkunci: opsi.setujuTerkunci,
          p_setuju_lanjutan: opsi.setujuLanjutan,
        });
        if (error) throw new Error(error.message);
        const h = data as unknown as { baris: number; santri: string; label: string | null };
        setHapusPesan(
          `${h.santri}: "${h.label ?? "—"}" dihapus (${h.baris} baris). Tampilan kembali "belum diisi".`,
        );
      } else {
        const { data, error } = await supabase.rpc("hapus_capaian_massal", {
          p_halaqah: halaqahId,
          p_mapel: hapus.mapel,
          p_bulan: bulanId,
          p_setuju_terkunci: opsi.setujuTerkunci,
          p_setuju_lanjutan: opsi.setujuLanjutan,
        });
        if (error) throw new Error(error.message);
        const h = data as unknown as { baris: number; mapel: string; bulan: string };
        setHapusPesan(`Dihapus ${h.baris} capaian ${h.mapel} bulan ${h.bulan}.`);
      }
      setHapus(null);
      // Muat ulang supaya tabel menampilkan "belum diisi" (kosong, bukan 0).
      setBulanId((b) => b);
      await muatUlang();
    } catch (e) {
      setHapusPesan(`Gagal menghapus: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setHapusSedang(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white p-4 ring-1 ring-black/5">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <PemilihHalaqah
              id={`halaqah-${domain}`}
              label={domain === "wasilah" ? "Level" : domain === "ghayah" ? "Kelompok" : "Halaqah"}
              halaqah={halaqahList}
              pengampu={pengampu}
              nilai={halaqahId}
              onChange={setHalaqahId}
              keterangan={pengampu[halaqahId] ? `Pengampu: ${pengampu[halaqahId]}` : "Pengampu belum ditetapkan"}
            />
          </div>

          <PemilihTahunBulan
            bulan={bulanList}
            tahun={tahun}
            bulanId={bulanId}
            idAwalan={`tahun-bulan-${domain}`}
            onTahun={gantiTahun}
            onBulan={setBulanId}
            domain={domain}
            catatan="Pembanding otomatis bulan sebelumnya."
          />
        </div>
      </div>

      {galat && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          Gagal memuat data: {galat}
        </p>
      )}

      {hapusPesan && (
        <p
          role="alert"
          className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900"
        >
          {hapusPesan}
        </p>
      )}

      <div className="rounded-xl bg-white ring-1 ring-black/5">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/5 px-4 py-3">
          <h2 className="text-base font-bold text-gray-900">Capaian {DOMAIN_LABEL[domain]}</h2>
          <p className="text-xs text-gray-600">
            {santri.length} santri · {memuat ? "memuat..." : `${baris.filter((b) => b.below_target).length} di bawah target`}
          </p>
        </div>

        {bolehHapus && (domain === "alquran" ? bidang : bidangHalaqah).length > 0 && (
          <div className="flex flex-wrap items-center gap-2 border-b border-black/5 px-4 py-2">
            <span className="text-xs font-medium text-gray-600">Hapus capaian massal (Mudir/Admin):</span>
            {(domain === "alquran" ? bidang : bidangHalaqah).map((bd) => {
              const ada = baris.some(
                (b) => b.subject_id === bd.id && b.pos !== null && b.pos !== undefined,
              );
              return (
                <button
                  key={bd.id}
                  type="button"
                  onClick={() => void bukaHapusMassal(bd.id)}
                  disabled={!ada}
                  className="rounded-lg border border-red-300 bg-white px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-40"
                >
                  Hapus semua {bd.name}
                </button>
              );
            })}
          </div>
        )}

        {memuat && santri.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">Memuat data...</p>
        ) : santri.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-600">Belum ada anggota di halaqah ini.</p>
        ) : (
          <>
            {/* HP: ringkasan singkat, detail lewat pop-up. */}
            <ul className="divide-y divide-black/5 lg:hidden">
              {ringkasanHp.map(({ santri: s, masalah, kosong }) => (
                <li key={s.id}>
                  <button
                    onClick={() => setDetail(s)}
                    className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left hover:bg-gray-50"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium text-gray-900">{s.full_name}</span>
                      <span className="mt-0.5 block text-xs">
                        {masalah.length > 0 ? (
                          <span className="text-pink-900">
                            di bawah target: {masalah.join(", ")}
                          </span>
                        ) : (
                          <span className="text-emerald-800">sesuai target</span>
                        )}
                        {kosong.length > 0 && (
                          <span className="text-amber-800"> · belum diisi: {kosong.join(", ")}</span>
                        )}
                      </span>
                    </span>
                    <span aria-hidden className="shrink-0 text-gray-400">
                      ›
                    </span>
                  </button>
                </li>
              ))}
            </ul>

            {/* Desktop: tabel lengkap. */}
            <div className="hidden lg:block">
              {domain === "alquran" ? (
                <TabelAlQuran
                  santri={santri}
                  baris={baris}
                  bidang={bidang}
                  memuat={memuat}
                  onHapus={bolehHapus ? (s, m) => void bukaHapusSatu(s, m) : undefined}
                />
              ) : (
                <TabelWasilah
                  santri={santri}
                  baris={baris}
                  bidang={bidangHalaqah}
                  hadir={hadir}
                  catatan={catatan}
                  domain={domain}
                  memuat={memuat}
                  onHapus={bolehHapus ? (s, m) => void bukaHapusSatu(s, m) : undefined}
                />
              )}
            </div>
          </>
        )}
      </div>

      <div className="rounded-lg bg-white px-4 py-3 text-xs text-gray-700 ring-1 ring-black/5">
        <p>
          <span className="mr-1 inline-block rounded bg-pink-100 px-1.5 py-0.5 font-medium text-pink-900">
            di bawah target
          </span>
          selisih kurang dari target bulanan.
          <span className="mx-1">·</span>
          <span className="mr-1 inline-block rounded bg-amber-100 px-1.5 py-0.5 font-medium text-amber-900">
            belum diisi
          </span>
          data belum ada di Excel/database, bukan nol.
        </p>
      </div>

      {hapus && (
        <DialogHapusCapaian
          info={hapus.info}
          massal={hapus.jenis === "massal"}
          sedang={hapusSedang}
          onBatal={() => setHapus(null)}
          onHapus={(opsi) => void jalankanHapus(opsi)}
        />
      )}

      {detail && (
        <DialogDetail
          santri={detail}
          bidang={domain === "alquran" ? bidang : bidangHalaqah}
          baris={baris}
          domain={domain}
          namaHalaqah={halaqahList.find((h) => h.id === halaqahId)?.code ?? ""}
          bolehHapus={bolehHapus}
          onHapus={(mapel) => {
            setDetail(null);
            void bukaHapusSatu(detail.id, mapel);
          }}
          hadirTeks={(() => {
            const hd = baris.find((b) => b.student_id === detail.id && b.hadir !== null);
            return hd
              ? `${angka(hd.hadir)}/${angka(hd.effective_days)}${hd.attendance_short ? " — kurang" : ""}`
              : "belum diisi";
          })()}
          onTutup={() => setDetail(null)}
        />
      )}
    </div>
  );
}

/** Pop-up detail capaian satu santri (dipakai di HP). */
function DialogDetail({
  santri,
  bidang,
  baris,
  domain,
  namaHalaqah,
  hadirTeks,
  bolehHapus,
  onHapus,
  onTutup,
}: {
  santri: Santri;
  bidang: Bidang[];
  baris: BarisLaporan[];
  domain: Domain;
  namaHalaqah: string;
  /** Hadir/HE cukup ditampilkan sekali di kepala pop-up. */
  hadirTeks: string;
  /** T6e: hanya Admin/Mudir yang boleh menghapus capaian. */
  bolehHapus: boolean;
  onHapus: (mapelId: string) => void;
  onTutup: () => void;
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onTutup();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onTutup]);

  return (
    <div
      className="fixed inset-0 z-40 flex items-end bg-black/40 sm:items-center sm:justify-center"
      onClick={onTutup}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Detail capaian ${santri.full_name}`}
        className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:max-w-md sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-gray-900">{santri.full_name}</h3>
            <p className="text-xs text-gray-600">
              {namaHalaqah} · Hadir/HE: <strong className="text-gray-800">{hadirTeks}</strong>
            </p>
          </div>
          <button
            onClick={onTutup}
            className="rounded-lg border border-gray-300 px-2.5 py-1 text-sm text-gray-700"
          >
            Tutup
          </button>
        </div>

        <Link
          to={`/santri/${santri.id}?domain=${domain}&dari=capaian`}
          className="mt-3 block rounded-lg bg-kusafa px-3 py-2 text-center text-sm font-medium text-white hover:bg-kusafa/90"
        >
          Buka halaman santri (grafik & riwayat)
        </Link>

        <div className="mt-3 space-y-3">
          {bidang.map((b) => {
            const r = baris.find((x) => x.student_id === santri.id && x.subject_id === b.id);
            return (
              <div key={b.id} className="rounded-lg bg-gray-50 p-3">
                <p className="text-sm font-semibold text-kusafa">{b.name}</p>
                {!r || r.pos === null ? (
                  <p className="mt-1 text-xs text-amber-800">Belum diisi</p>
                ) : (
                  <dl className="mt-1 space-y-0.5 text-xs">
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Capaian lalu</dt>
                      <dd className="text-gray-800">{r.prev_item_label ?? "–"}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Capaian kini</dt>
                      <dd className="font-medium text-gray-900">{r.item_label ?? "–"}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Selisih</dt>
                      <dd
                        className={
                          r.selisih !== null && r.selisih < 0
                            ? "font-semibold text-red-700"
                            : "font-semibold text-kusafa"
                        }
                      >
                        {r.selisih === null ? "–" : (r.selisih > 0 ? "+" : "") + angka(r.selisih)}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-gray-600">Target bulanan</dt>
                      <dd className="text-gray-800">
                        {r.target_monthly === null ? "–" : angka(r.target_monthly)}
                      </dd>
                    </div>
                    <div className="pt-1">
                      {r.target_monthly === null ? (
                        <span
                          className="rounded bg-amber-100 px-1.5 py-0.5 font-medium text-amber-900"
                          title="Belum ada target disetujui untuk bulan ini (kosong, bukan 0)"
                        >
                          target: –
                        </span>
                      ) : r.below_target ? (
                        <span className="rounded bg-pink-100 px-1.5 py-0.5 font-medium text-pink-900">
                          di bawah target
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-50 px-1.5 py-0.5 font-medium text-emerald-800">
                          sesuai target
                        </span>
                      )}
                    </div>
                  </dl>
                )}
                {bolehHapus && r && r.pos !== null && r.pos !== undefined && (
                  <button
                    type="button"
                    onClick={() => onHapus(b.id)}
                    className="mt-2 w-full rounded-lg border border-red-300 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
                    aria-label={`Hapus capaian ${b.name} ${santri.full_name}`}
                  >
                    Hapus capaian {b.name}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}