import { useEffect, useMemo, useState } from "react";
import { supabase } from "../lib/supabase";
import { useAuth } from "../lib/auth-context";
import { ambilSemua } from "../lib/ambil-semua";
import { batasiPemberitahuan, hanyaHalaqahDiampu } from "../lib/roles";
import { ambilGuru, halaqahDiampu } from "./PemilihHalaqah";
import DropdownCari from "./DropdownCari";

interface Baris {
  student_id: string;
  subject_id: string;
  month_id: string;
  halaqah_id: string | null;
}

interface Halaqah {
  id: string;
  code: string;
}

interface Bidang {
  id: string;
  name: string;
  domain: string;
}

/**
 * Pemberitahuan "data belum lengkap" dari awal tahun sampai bulan ini.
 * Menampilkan halaqah dan santri yang belum punya capaian pada bulan-bulan
 * yang seharusnya sudah diisi. Bulan kosong = belum diisi, bukan 0.
 *
 * Sumber: `progress_entries` dan `v_months_ordered` (urutan bulan lintas tahun).
 * Tidak ada perhitungan selisih di sini.
 */
export default function KotakBelumLengkap({
  bulanId,
  domain = "alquran",
}: {
  /** Bulan batas atas (bulan yang sedang dipilih). */
  bulanId: string;
  domain?: string;
}) {
  const { profile } = useAuth();
  const [buka, setBuka] = useState(true);
  const [memuat, setMemuat] = useState(false);
  const [galat, setGalat] = useState<string | null>(null);
  const [daftar, setDaftar] = useState<{
    bulan: { id: string; nama: string }[];
    santri: { id: string; nama: string; halaqah: string; kosong: string[] }[];
  } | null>(null);

  // Hanya untuk peninjau (Mudir/Admin/Masul) dan pengampu yang dibatasi amanah.
  const boleh = !!profile;
  const batasiSemua = profile ? hanyaHalaqahDiampu(profile.role) : false;
  const batasiPemberitahuanGuru = profile ? batasiPemberitahuan(profile.role) : false;

  useEffect(() => {
    let aktif = true;
    if (!boleh || !bulanId) {
      setDaftar(null);
      return;
    }
    void (async () => {
      setMemuat(true);
      setGalat(null);
      try {
        // Semua bulan (termasuk Data Awal bulan_no 0) sampai bulan terpilih.
        const { data: urutan, error: e1 } = await supabase
          .from("v_months_ordered")
          .select("id, month_no, name, hijri_year, ord, prev_month_id");
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
        // Bulan yang harus sudah diisi: bulan_no > 0 sampai batas (Data Awal manual tidak dihitung).
        const bulanWajib = semua
          .filter((m) => m.month_no > 0 && m.ord <= batas.ord)
          .sort((a, b) => a.ord - b.ord);

        const { data: bidang, error: e2 } = await supabase
          .from("subjects")
          .select("id, name, domain")
          .eq("domain", domain)
          .eq("is_active", true)
          .order("sort_order");
        if (e2) throw new Error(e2.message);

        const { data: halaqah, error: e3 } = await supabase
          .from("halaqahs")
          .select("id, code")
          .eq("domain", domain)
          .eq("is_active", true)
          .order("code");
        if (e3) throw new Error(e3.message);

        // Anggota aktif hanya dari halaqah domain ini.
        const idHalaqah = (halaqah ?? []).map((h) => h.id);
        if (idHalaqah.length === 0) {
          if (aktif) setDaftar({ bulan: bulanWajib.map((b) => ({ id: b.id, nama: b.name })), santri: [] });
          return;
        }
        const { data: anggota, error: e4 } = await supabase
          .from("halaqah_members")
          .select("student_id, halaqah_id")
          .is("left_on", null)
          .in("halaqah_id", idHalaqah)
          .order("student_id", { ascending: true })
          .range(0, 9999);
        if (e4) throw new Error(e4.message);
        let daftarAnggota = (anggota ?? []) as Array<{ student_id: string; halaqah_id: string }>;
        // Semua role pengampu (termasuk Masul) hanya membaca pemberitahuan halaqahnya.
        if (batasiSemua && profile) {
          const diampu = halaqahDiampu(await ambilGuru(), profile.id);
          daftarAnggota = daftarAnggota.filter((x) => diampu.has(x.halaqah_id));
        }

        // Capaian yang sudah ada pada bulan-bulan itu (diambil bertahap: batas server 1.000 baris).
        const bulanIds = bulanWajib.map((b) => b.id);
        const { data: capaian, error: e5 } = bulanIds.length
          ? await ambilSemua<Baris>((awal, jumlah) =>
              supabase
                .from("progress_entries")
                .select("student_id, subject_id, month_id, halaqah_id")
                .in("month_id", bulanIds)
                .order("id", { ascending: true })
                .range(awal, awal + jumlah - 1),
            )
          : { data: [], error: null };
        if (e5) throw new Error(e5.message);
        const ada = new Set(
          ((capaian ?? []) as Baris[]).map((c) => `${c.student_id}|${c.subject_id}|${c.month_id}`),
        );

        // Capaian yang diisi boleh hanya salah satu bidang; yang dianggap lengkap
        // harus punya capaian di setiap bidang aktif pada bulan itu (sesuai form input).
        const bidangDomain = (bidang ?? []) as Bidang[];
        const daftarSantri = daftarAnggota.map((a) => {
          const h = (halaqah ?? []).find((x) => x.id === a.halaqah_id);
          return { ...a, kode: h?.code ?? "" };
        });

        const { data: siswa, error: e6 } = await supabase
          .from("students")
          .select("id, full_name, is_active")
          .eq("is_active", true)
          .in("id", daftarSantri.map((a) => a.student_id))
          .order("full_name", { ascending: true })
          .range(0, 9999);
        if (e6) throw new Error(e6.message);
        const petaNama = new Map((siswa ?? []).map((s) => [s.id, s.full_name]));

        const keluaran = daftarSantri
          .map((a) => {
            const bulanKosong = bulanWajib.filter((b) => {
              // Bulan dianggap belum lengkap bila ada bidang yang belum terisi.
              return bidangDomain.some((bd) => !ada.has(`${a.student_id}|${bd.id}|${b.id}`));
            });
            return {
              id: a.student_id,
              nama: petaNama.get(a.student_id) ?? a.student_id,
              halaqah: a.kode,
              kosong: bulanKosong.map((b) => b.name),
              jumlahBulan: bulanKosong.length,
            };
          })
          .filter((x) => x.jumlahBulan > 0)
          .sort((a, b) => b.jumlahBulan - a.jumlahBulan || a.nama.localeCompare(b.nama));

        if (!aktif) return;
        setDaftar({ bulan: bulanWajib.map((b) => ({ id: b.id, nama: b.name })), santri: keluaran });
      } catch (e) {
        if (aktif) setGalat(e instanceof Error ? e.message : String(e));
      } finally {
        if (aktif) setMemuat(false);
      }
    })();
    return () => {
      aktif = false;
    };
  }, [bulanId, domain, boleh, batasiSemua, profile]);

  const ringkas = useMemo(() => {
    if (!daftar) return null;
    const total = daftar.santri.length;
    const halaqahKena = new Set(daftar.santri.map((s) => s.halaqah));
    return { total, halaqah: halaqahKena.size };
  }, [daftar]);

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
            Data belum lengkap — awal tahun sampai bulan ini
          </span>
          <span className="block text-xs text-gray-600">
            {memuat
              ? "Memeriksa..."
              : galat
                ? "Gagal memeriksa."
                : ringkas
                  ? `${ringkas.total} santri di ${ringkas.halaqah} halaqah belum lengkap.`
                  : "Tidak ada data."}
          </span>
        </span>
        <span aria-hidden className="text-gray-400">
          {buka ? "▴" : "▾"}
        </span>
      </button>

      {buka && (
        <div className="border-t border-black/5 px-4 py-3">
          {galat && (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
              {galat}
            </p>
          )}
          {!galat && daftar && daftar.santri.length === 0 && (
            <p className="text-sm text-emerald-800">Semua santri lengkap sampai bulan ini.</p>
          )}
          {!galat && daftar && daftar.santri.length > 0 && (
            <>
              <p className="mb-2 text-xs text-gray-700">
                Kosong berarti belum diisi, bukan 0. Hubungi pengampu halaqah terkait, atau isi
                sendiri bila Anda berhak.
              </p>
              <div className="max-h-80 overflow-y-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="bg-kusafa-light text-left text-xs uppercase tracking-wide text-kusafa">
                      <th scope="col" className="px-2 py-2">Santri</th>
                      <th scope="col" className="px-2 py-2">Halaqah</th>
                      <th scope="col" className="px-2 py-2">Bulan belum lengkap</th>
                    </tr>
                  </thead>
                  <tbody>
                    {daftar.santri.slice(0, 200).map((s) => (
                      <tr key={s.id} className="border-t border-black/5 align-top">
                        <th scope="row" className="px-2 py-2 text-left font-medium text-gray-900">
                          {s.nama}
                        </th>
                        <td className="px-2 py-2 text-gray-700">{s.halaqah}</td>
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
              {daftar.santri.length > 200 && (
                <p className="mt-2 text-xs text-gray-600">
                  Ditampilkan 200 pertama dari {daftar.santri.length} santri.
                </p>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}
