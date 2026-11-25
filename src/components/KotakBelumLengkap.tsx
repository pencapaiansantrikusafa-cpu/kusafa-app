import { useEffect, useMemo, useState } from "react";
import { supabase } from "../lib/supabase";
import { useAuth } from "../lib/auth-context";
import { ambilSemua } from "../lib/ambil-semua";
import { hanyaHalaqahDiampu, isPeninjau, DOMAIN_LABEL, type Domain } from "../lib/roles";
import { ambilGuru, halaqahDiampu, type GuruBaris } from "./PemilihHalaqah";
import DropdownCari from "./DropdownCari";

interface Baris {
  student_id: string;
  subject_id: string;
  month_id: string;
}

interface Bidang {
  id: string;
  name: string;
}

/** Baris penetapan mata pelajaran per halaqah. */
interface Grant {
  halaqah_id: string;
  subject_id: string;
}

/** Ringkasan "x/y terisi" untuk satu bulan, per halaqah. */
interface RingkasBulan {
  monthId: string;
  nama: string;
  total: number;
  terisi: number;
}

interface SantriKurang {
  id: string;
  nama: string;
  halaqahId: string;
  halaqah: string;
  musyrif: string;
  kosong: string[];
  jumlahBulan: number;
}

/** Baris dari fungsi RPC `students_without_halaqah()` (santri aktif tanpa halaqah di satu domain). */
interface SantriTanpaHalaqah {
  domain: Domain;
  academic_year_id: string;
  hijri_year: number;
  student_id: string;
  nis: string;
  full_name: string;
  level_label: string | null;
}

/** Domain yang notifikasinya boleh dilihat role ini (cermin aturan database). */
function domainNotifikasi(role: string): Domain[] {
  if (role === "mudir" || role === "admin") return ["alquran", "wasilah", "ghayah"];
  if (role === "masul_alquran") return ["alquran"];
  if (role === "masul_wasilah") return ["wasilah"];
  if (role === "masul_ghayah") return ["ghayah"];
  return [];
}

/** Label baku halaqah: "HLQ-PA-4 - Ust. Fulan 3" (nama pengampu selalu ikut). */
function labelHalaqahNotif(code: string, musyrif: string, domain: Domain = "alquran"): string {
  const sebutan = domain === "alquran" ? "musyrif/ah" : "pengampu";
  return musyrif ? `${code} - ${musyrif}` : `${code} - ${sebutan} belum ditetapkan`;
}

/**
 * Pemberitahuan "data belum lengkap" dari awal tahun sampai bulan berjalan.
 *
 * Sumber data (semuanya dari database, tidak ada perhitungan di luar):
 * - `v_months_ordered` : urutan bulan lintas tahun ajaran;
 * - `month_domain_settings` : Hari Efektif tiap bulan per domain, dipakai sebagai
 *   penanda "bulan ini sudah berjalan" (opsi B yang dipilih Mudir 23 Nov 2026).
 *   Bulan yang belum punya Hari Efektif tidak dihitung, jadi bulan yang belum
 *   dimulai tidak membuat santri terlihat lalai.
 * - `progress_entries` : capaian yang sudah ada;
 * - `halaqah_members`, `halaqahs`, `halaqah_teachers`, `profiles` : santri, halaqah, musyrif.
 *
 * Hak lihat: Mudir/Admin/Masul Al Quran melihat semua halaqah dan boleh menyaring
 * per halaqah; musyrif/ah hanya halaqahnya sendiri (jumlah santri yang diampu).
 */
export default function KotakBelumLengkap({
  bulanId,
  halaqahAwal,
  guruAwal,
  tunda = false,
  domain = "alquran",
}: {
  bulanId: string;
  /** Domain yang diperiksa (T6b: halaman Input Ilmu Wasilah/Ghayah). */
  domain?: Domain;
  /** Halaqah yang boleh dilihat (dari halaman induk; tidak diunduh ulang). */
  halaqahAwal?: { id: string; code: string }[];
  /** Pengampu tiap halaqah (dari halaman induk; tidak diunduh ulang). */
  guruAwal?: GuruBaris[];
  /**
   * T5c-2: tunggu sampai `tunda` menjadi false sebelum memeriksa. Dipakai halaman Input
   * agar kotak notifikasi tidak menahan/menyaingi pemuatan form utama (form lebih penting).
   */
  tunda?: boolean;
}) {
  const { profile } = useAuth();
  const [buka, setBuka] = useState(true);
  const [memuat, setMemuat] = useState(false);
  const [galat, setGalat] = useState<string | null>(null);
  /** Saringan halaqah; "" = semua halaqah. */
  const [saringHalaqah, setSaringHalaqah] = useState("");
  const [data, setData] = useState<{
    bulan: RingkasBulan[];
    santri: SantriKurang[];
    halaqah: { id: string; code: string }[];
    /** Peta halaqah -> nama musyrif/ah (untuk label dropdown). */
    musyrif: Record<string, string[]>;
  } | null>(null);
  /** Notifikasi santri tanpa halaqah per domain (view v_students_without_halaqah). */
  const [tanpaHalaqah, setTanpaHalaqah] = useState<{
    memuat: boolean;
    galat: string | null;
    baris: SantriTanpaHalaqah[];
  }>({ memuat: false, galat: null, baris: [] });

  const boleh = !!profile;
  const semuaHalaqah = profile ? isPeninjau(profile.role) : false;
  const batasiAmanah = profile ? hanyaHalaqahDiampu(profile.role) : false;

  useEffect(() => {
    let aktif = true;
    if (!boleh || !bulanId || tunda) {
      setData(null);
      return;
    }
    void (async () => {
      setMemuat(true);
      setGalat(null);
      // T5c: bila halaman induk sudah mengirim data halaqah & pengampu, tunggu sampai
      // siap — supaya tidak ada unduhan dobel dan notifikasi tidak menunggu dua kali.
      if (halaqahAwal !== undefined && halaqahAwal.length === 0) return;
      if (guruAwal !== undefined && guruAwal.length === 0) return;
      try {
        const DOMAIN = domain;
        // 1. Urutan bulan lintas tahun.
        const { data: urutan, error: e1 } = await supabase
          .from("v_months_ordered")
          .select("id, month_no, name, hijri_year, ord");
        if (e1) throw new Error(e1.message);
        const semua = (urutan ?? []) as Array<{
          id: string;
          month_no: number;
          name: string;
          hijri_year: number;
          ord: number;
        }>;
        const batas = semua.find((m) => m.id === bulanId);
        if (!batas) throw new Error("Bulan tidak ditemukan.");

        // 2. Bulan yang sudah berjalan: punya Hari Efektif di domain ini.
        //    (Opsi B: bulan yang belum dimulai tidak dihitung sebagai kekurangan.)
        const { data: setelan, error: e2 } = await supabase
          .from("month_domain_settings")
          .select("month_id, effective_days")
          .eq("domain", DOMAIN);
        if (e2) throw new Error(e2.message);
        const berjalan = new Set(
          (setelan ?? []).filter((s) => s.effective_days !== null).map((s) => s.month_id as string),
        );
        const bulanDiperiksa = semua
          .filter((m) => m.month_no > 0 && m.ord <= batas.ord && berjalan.has(m.id))
          .sort((a, b) => a.ord - b.ord);

        // 3. Bidang, halaqah, dan santri.
        //    T5c: halaqah & pengampu memakai data dari halaman induk bila tersedia,
        //    supaya tidak ada permintaan ganda yang memperlambat halaman Input.
        const [bidangRes, halaqahRes] = await Promise.all([
          supabase.from("subjects").select("id, name").eq("domain", DOMAIN).eq("is_active", true).order("sort_order"),
          halaqahAwal && halaqahAwal.length
            ? Promise.resolve({ data: halaqahAwal, error: null })
            : supabase.from("halaqahs").select("id, code").eq("domain", DOMAIN).eq("is_active", true).order("code"),
        ]);
        if (bidangRes.error) throw new Error(bidangRes.error.message);
        if (halaqahRes.error) throw new Error(halaqahRes.error.message);
        const bidang = (bidangRes.data ?? []) as Bidang[];
        let halaqah = (halaqahRes.data ?? []) as { id: string; code: string }[];

        // 4. Musyrif/ah tiap halaqah (kolom pengampu).
        const guru = guruAwal ?? (await ambilGuru());
        const musyrifPeta = new Map<string, string[]>();
        for (const g of guru) {
          const arr = musyrifPeta.get(g.halaqah_id) ?? [];
          if (g.full_name && !arr.includes(g.full_name)) arr.push(g.full_name);
          musyrifPeta.set(g.halaqah_id, arr);
        }

        // 5. Hak lihat.
        if (batasiAmanah && profile) {
          const diampu = halaqahDiampu(guru, profile.id);
          halaqah = halaqah.filter((h) => diampu.has(h.id));
        }
        const idHalaqah = halaqah.map((h) => h.id);
        if (idHalaqah.length === 0 || bidang.length === 0) {
          if (aktif) setData({ bulan: [], santri: [], halaqah: [], musyrif: {} });
          return;
        }

        // 4b. Mata pelajaran yang ditetapkan per halaqah. Untuk Al Qur'an, semua bidang
        //     domain dipakai (perilaku lama). Untuk Wasilah/Ghayah, hanya mapel halaqah itu:
        //     halaqah boleh hanya punya satu mata pelajaran (mis. Kelompok 1 = Aqidah dan Fiqih).
        const { data: penetapan, error: e6 } = await supabase
          .from("halaqah_subjects")
          .select("halaqah_id, subject_id")
          .in("halaqah_id", idHalaqah);
        if (e6) throw new Error(e6.message);
        const mapelHalaqah = new Map<string, Set<string>>();
        for (const r of (penetapan ?? []) as unknown as Grant[]) {
          const set = mapelHalaqah.get(r.halaqah_id) ?? new Set<string>();
          set.add(r.subject_id);
          mapelHalaqah.set(r.halaqah_id, set);
        }
        /** Bidang yang wajib terisi untuk satu halaqah. */
        const bidangHalaqah = (halaqahId: string): Bidang[] => {
          if (domain === "alquran") return bidang;
          const ids = mapelHalaqah.get(halaqahId);
          if (!ids || ids.size === 0) return [];
          return bidang.filter((bd) => ids.has(bd.id));
        };

        const { data: anggota, error: e3 } = await supabase
          .from("halaqah_members")
          .select("student_id, halaqah_id")
          .is("left_on", null)
          .in("halaqah_id", idHalaqah)
          .order("student_id", { ascending: true })
          .range(0, 9999);
        if (e3) throw new Error(e3.message);
        const daftarAnggota = (anggota ?? []) as Array<{ student_id: string; halaqah_id: string }>;

        // 6. Capaian yang sudah ada pada bulan-bulan yang diperiksa.
        const bulanIds = bulanDiperiksa.map((b) => b.id);
        const { data: capaian, error: e4 } = bulanIds.length
          ? await ambilSemua<Baris>((awal, jumlah) =>
              supabase
                .from("progress_entries")
                .select("student_id, subject_id, month_id")
                .in("month_id", bulanIds)
                .order("id", { ascending: true })
                .range(awal, awal + jumlah - 1),
            )
          : { data: [], error: null };
        if (e4) throw new Error(e4.message);
        const ada = new Set(
          ((capaian ?? []) as Baris[]).map((c) => `${c.student_id}|${c.subject_id}|${c.month_id}`),
        );
        /**
         * Santri lengkap bila punya capaian di semua bidang yang berlaku untuk halaqahnya
         * pada bulan itu. Halaqah tanpa penetapan mapel (mis. Level 6) tidak dinilai.
         */
        const lengkap = (studentId: string, halaqahId: string, monthId: string) => {
          const perlu = bidangHalaqah(halaqahId);
          if (perlu.length === 0) return true;
          return perlu.every((bd) => ada.has(`${studentId}|${bd.id}|${monthId}`));
        };

        const { data: siswa, error: e5 } = await supabase
          .from("students")
          .select("id, full_name, is_active")
          .eq("is_active", true)
          .in("id", daftarAnggota.map((a) => a.student_id))
          .order("full_name", { ascending: true })
          .range(0, 9999);
        if (e5) throw new Error(e5.message);
        const petaNama = new Map((siswa ?? []).map((s) => [s.id, s.full_name]));
        const petaHalaqah = new Map(halaqah.map((h) => [h.id, h.code]));

        // 7. Daftar santri yang belum lengkap.
        const santri: SantriKurang[] = daftarAnggota
          .map((a) => {
            const kosong = bulanDiperiksa.filter((b) => !lengkap(a.student_id, a.halaqah_id, b.id));
            return {
              id: a.student_id,
              nama: petaNama.get(a.student_id) ?? a.student_id,
              halaqahId: a.halaqah_id,
              halaqah: petaHalaqah.get(a.halaqah_id) ?? "",
              musyrif: (musyrifPeta.get(a.halaqah_id) ?? []).join(", "),
              kosong: kosong.map((b) => b.name),
              jumlahBulan: kosong.length,
            };
          })
          .filter((x) => x.jumlahBulan > 0)
          .sort((a, b) => b.jumlahBulan - a.jumlahBulan || a.nama.localeCompare(b.nama));

        // 8. Ringkasan "x/y terisi" per bulan.
        const ringkas: RingkasBulan[] = bulanDiperiksa.map((b) => {
          const terisi = daftarAnggota.filter((a) => lengkap(a.student_id, a.halaqah_id, b.id)).length;
          return { monthId: b.id, nama: b.name, total: daftarAnggota.length, terisi };
        });

        if (!aktif) return;
        setData({ bulan: ringkas, santri, halaqah, musyrif: Object.fromEntries(musyrifPeta) });
      } catch (e) {
        if (aktif) setGalat(e instanceof Error ? e.message : String(e));
      } finally {
        if (aktif) setMemuat(false);
      }
    })();
    return () => {
      aktif = false;
    };
  }, [bulanId, boleh, batasiAmanah, profile, halaqahAwal, guruAwal, tunda, domain]);

  // Notifikasi turunan: santri aktif yang belum punya halaqah di domain yang
  // boleh dilihat role ini. Hak lihat ditegakkan database (fungsi security
  // definer `students_without_halaqah`, yang memeriksa `can_manage(domain)` di
  // dalam fungsi). Di sini hanya menyembunyikan bagian untuk musyrif/mudarris/wali
  // dan menyusun lencana jumlah per domain.
  useEffect(() => {
    let aktif = true;
    if (!profile || !isPeninjau(profile.role)) {
      setTanpaHalaqah({ memuat: false, galat: null, baris: [] });
      return;
    }
    void (async () => {
      setTanpaHalaqah({ memuat: true, galat: null, baris: [] });
      try {
        const { data: hasil, error } = await supabase.rpc("students_without_halaqah");
        if (error) throw new Error(error.message);
        if (aktif) setTanpaHalaqah({ memuat: false, galat: null, baris: (hasil ?? []) as SantriTanpaHalaqah[] });
      } catch (e) {
        if (aktif)
          setTanpaHalaqah({
            memuat: false,
            galat: e instanceof Error ? e.message : String(e),
            baris: [],
          });
      }
    })();
    return () => {
      aktif = false;
    };
  }, [profile]);

  // Halaqah yang boleh dipilih di saringan.
  const musyrifMap = data?.musyrif ?? {};

  const santriTampil = useMemo(() => {
    if (!data) return [];
    return saringHalaqah ? data.santri.filter((s) => s.halaqahId === saringHalaqah) : data.santri;
  }, [data, saringHalaqah]);

  const domainTampil = profile ? domainNotifikasi(profile.role) : [];
  const barisTanpa = tanpaHalaqah.baris.filter((b) => domainTampil.includes(b.domain));

  if (!boleh) return null;

  return (
    <section className="rounded-xl bg-white ring-1 ring-black/5">
      <button
        type="button"
        onClick={() => setBuka((b) => !b)}
        aria-expanded={buka}
        className="flex w-full flex-wrap items-center justify-between gap-2 px-4 py-3 text-left"
      >
        <span>
          <span className="block text-sm font-bold text-gray-900">
            Data belum lengkap — awal tahun sampai bulan berjalan
          </span>
          <span className="block text-xs text-gray-600">
            {memuat
              ? "Memeriksa..."
              : galat
                ? "Gagal memeriksa."
                : data
                  ? semuaHalaqah
                    ? `${data.santri.length} santri di ${new Set(data.santri.map((s) => s.halaqahId)).size} halaqah belum lengkap.`
                    : `${data.santri.length} santri yang Anda ampu belum lengkap.`
                  : "Tidak ada data."}
          </span>
        </span>
        <span aria-hidden className="text-gray-400">
          {buka ? "▴" : "▾"}
        </span>
      </button>

      {buka && (
        <div className="border-t border-black/5 px-4 py-3">
          {/* Santri belum punya halaqah: perluasan notifikasi yang sama, bukan sistem paralel.
              Hanya untuk Mudir/Admin/Masul sesuai domain; musyrif/mudarris tidak melihat. */}
          {profile && isPeninjau(profile.role) && (
            <div className="mb-4 rounded-lg bg-amber-50 px-3 py-3 ring-1 ring-amber-200">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-sm font-bold text-gray-900">Santri belum punya halaqah</p>
                <p className="text-xs text-gray-600">
                  Santri aktif di tahun ajaran aktif yang belum punya halaqah pada domain tersebut.
                </p>
              </div>

              {tanpaHalaqah.memuat ? (
                <p className="mt-2 text-xs text-gray-600">Memeriksa...</p>
              ) : tanpaHalaqah.galat ? (
                <p role="alert" className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
                  Gagal memeriksa: {tanpaHalaqah.galat}
                </p>
              ) : (
                <>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {domainTampil.map((d) => {
                      const jumlah = barisTanpa.filter((b) => b.domain === d).length;
                      return (
                        <span
                          key={d}
                          className={
                            "rounded px-2 py-1 text-xs ring-1 " +
                            (jumlah === 0
                              ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
                              : "bg-amber-100 text-amber-900 ring-amber-300")
                          }
                        >
                          <strong className="font-semibold">{DOMAIN_LABEL[d]}</strong>{" "}
                          {jumlah === 0 ? "0 santri" : `${jumlah} santri`}
                        </span>
                      );
                    })}
                  </div>

                  {barisTanpa.length === 0 ? (
                    <p className="mt-2 text-sm text-emerald-800">
                      Semua santri aktif sudah punya halaqah di domain ini.
                    </p>
                  ) : (
                    <div className="mt-3 max-h-60 overflow-auto rounded-lg bg-white ring-1 ring-black/5">
                      <table className="w-full min-w-[520px] border-collapse text-sm">
                        <thead className="sticky top-0 z-30 bg-kusafa-light text-left text-xs uppercase tracking-wide text-kusafa">
                          <tr>
                            <th scope="col" className="px-2 py-2">Domain</th>
                            <th scope="col" className="px-2 py-2">NIS</th>
                            <th scope="col" className="px-2 py-2">Nama</th>
                            <th scope="col" className="px-2 py-2">Level</th>
                          </tr>
                        </thead>
                        <tbody>
                          {barisTanpa.slice(0, 200).map((b) => (
                            <tr key={`${b.domain}|${b.student_id}`} className="border-t border-black/5">
                              <td className="whitespace-nowrap px-2 py-2 text-gray-700">
                                {DOMAIN_LABEL[b.domain]}
                              </td>
                              <td className="whitespace-nowrap px-2 py-2 font-mono text-xs text-gray-700">
                                {b.nis}
                              </td>
                              <th scope="row" className="px-2 py-2 text-left font-medium text-gray-900">
                                {b.full_name}
                              </th>
                              <td className="px-2 py-2 text-gray-700">
                                {b.level_label || <span className="text-gray-500">—</span>}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  {barisTanpa.length > 200 && (
                    <p className="mt-2 text-xs text-gray-600">
                      Ditampilkan 200 pertama dari {barisTanpa.length} santri.
                    </p>
                  )}
                  <p className="mt-2 text-xs text-gray-600">
                    Penugasan halaqah dilakukan di menu Halaqah (T8). Daftar ini hilang otomatis
                    begitu santri dimasukkan ke halaqah.
                  </p>
                </>
              )}
            </div>
          )}
          {galat && (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
              {galat}
            </p>
          )}

          {/* Saringan halaqah: hanya untuk Mudir/Admin/Masul Al Quran. */}
          {!galat && data && semuaHalaqah && data.halaqah.length > 1 && (
            <div className="mb-3 max-w-md">
              <DropdownCari
                id="belum-lengkap-halaqah"
                label="Lihat per halaqah"
                opsi={data.halaqah.map((h) => ({
                  nilai: h.id,
                  label: labelHalaqahNotif(
                    h.code,
                    (musyrifMap[h.id] ?? []).join(", "),
                    domain,
                  ),
                  cariJuga: (musyrifMap[h.id] ?? []).join(", "),
                }))}
                nilai={saringHalaqah}
                onChange={setSaringHalaqah}
                opsiKosong="Semua halaqah"
                placeholderCari="Ketik kode halaqah atau nama musyrif/ah..."
              />
            </div>
          )}

          {/* Ringkasan x/y terisi per bulan. */}
          {!galat && data && data.bulan.length > 0 && (
            <div className="mb-3 overflow-x-auto rounded-lg bg-gray-50 p-2 ring-1 ring-black/5">
              <p className="mb-1 text-xs font-medium text-gray-800">
                Jumlah santri terisi per bulan{" "}
                <span className="font-normal text-gray-600">
                  ({semuaHalaqah ? "seluruh halaqah" : "halaqah yang Anda ampu"}; lengkap = semua
                  bidang terisi)
                </span>
              </p>
              <div className="flex flex-wrap gap-1.5">
                {data.bulan.map((b) => {
                  const persen = b.total === 0 ? 0 : Math.round((b.terisi / b.total) * 100);
                  const tuntas = b.terisi === b.total;
                  return (
                    <span
                      key={b.monthId}
                      title={`${b.nama}: ${b.terisi} dari ${b.total} santri lengkap (${persen}%)`}
                      className={
                        "rounded px-2 py-1 text-xs " +
                        (tuntas
                          ? "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200"
                          : "bg-amber-50 text-amber-900 ring-1 ring-amber-200")
                      }
                    >
                      <strong className="font-semibold">{b.nama}</strong> {b.terisi}/{b.total}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {!galat && data && santriTampil.length === 0 && (
            <p className="text-sm text-emerald-800">Semua santri lengkap sampai bulan berjalan.</p>
          )}

          {!galat && data && santriTampil.length > 0 && (
            <>
              <p className="mb-2 text-xs text-gray-700">
                Kosong berarti belum diisi, bukan 0. Hubungi musyrif/ah terkait, atau isi sendiri bila
                Anda berhak. Total {santriTampil.length} santri belum lengkap.
              </p>
              {/* Kepala tabel tetap terlihat saat daftar digulir; kolom Santri
                  dibekukan di kiri agar tetap terbaca di HP sempit.
                  Struktur: bingkai bergulir > tabel > dua kepala:
                  (1) "thead-kepala" yang menempel di atas bingkai tanpa ikut tergulir
                      (bukan sekadar sticky, karena sticky masih bisa ikut naik bila
                      bingkai gulirnya ikut tergulir bersama halaman);
                  (2) "thead-santri" berisi sudut "Santri" yang dibekukan (kiri atas)
                      dan sengaja tidak terlihat (h-0, border-0, sr-only) sehingga
                      tidak menambah tinggi tabel. */}
              <div className="max-h-80 overflow-auto rounded-lg ring-1 ring-black/5">
                <table className="w-full min-w-[640px] border-collapse text-sm">
                  <thead className="sticky top-0 z-30">
                    <tr className="bg-kusafa-light text-left text-xs uppercase tracking-wide text-kusafa">
                      <th scope="col" className="w-[34%] min-w-[9rem] px-2 py-2">Santri</th>
                      <th scope="col" className="px-2 py-2">Halaqah</th>
                      <th scope="col" className="px-2 py-2">Musyrif/ah</th>
                      <th scope="col" className="px-2 py-2">Bulan belum lengkap</th>
                    </tr>
                  </thead>
                  <thead className="sticky top-0 z-40 h-0">
                    <tr className="h-0">
                      <th
                        scope="col"
                        aria-label="Santri"
                        className="sticky left-0 z-40 h-0 border-0 bg-kusafa-light p-0 shadow-[1px_0_0_0_rgba(0,0,0,0.08)]"
                      >
                        <span className="sr-only">Santri</span>
                      </th>
                      <th className="sr-only" colSpan={3}>
                        kolom lainnya
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {santriTampil.slice(0, 200).map((s) => (
                      <tr key={s.id} className="border-t border-black/5 align-top">
                        <th
                          scope="row"
                          className="sticky left-0 z-10 whitespace-nowrap bg-white px-2 py-2 text-left font-medium text-gray-900 shadow-[1px_0_0_0_rgba(0,0,0,0.08)]"
                        >
                          {s.nama}
                        </th>
                        <td className="whitespace-nowrap px-2 py-2 text-gray-700">{s.halaqah}</td>
                        <td className="px-2 py-2 text-gray-700">
                          {s.musyrif || <span className="text-gray-500">belum ditetapkan</span>}
                        </td>
                        <td className="px-2 py-2 text-xs">
                          <span className="rounded bg-amber-100 px-1.5 py-0.5 font-medium text-amber-900">
                            {s.kosong.length} bulan
                          </span>{" "}
                          <span className="text-gray-600">{s.kosong.slice(-4).join(", ")}</span>
                          {s.kosong.length > 4 && <span className="text-gray-500">, …</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {santriTampil.length > 200 && (
                <p className="mt-2 text-xs text-gray-600">
                  Ditampilkan 200 pertama dari {santriTampil.length} santri.
                </p>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}
