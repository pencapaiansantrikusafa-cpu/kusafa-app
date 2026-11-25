import { useEffect, useMemo, useState } from "react";
import DropdownCari from "./DropdownCari";
import { supabase } from "../lib/supabase";
import { useAuth } from "../lib/auth-context";
import { isPeninjau, type Domain } from "../lib/roles";

export interface BulanData {
  id: string;
  month_no: number;
  name: string;
  hijri_year: number;
}

interface Props {
  /** Semua bulan lintas tahun ajaran. */
  bulan: BulanData[];
  tahun: number | "";
  bulanId: string;
  onTahun: (t: number) => void;
  onBulan: (id: string) => void;
  /** Awalan id elemen agar unik bila dipakai beberapa kali di satu halaman. */
  idAwalan: string;
  /** Sembunyikan bulan "Data Awal" (month_no 0) untuk form input. */
  tanpaDataAwal?: boolean;
  catatan?: string;
  /**
   * Domain yang diperiksa notifikasi "data belum lengkap". Sebelumnya selalu
   * Al Qur'an sehingga halaman Ilmu Wasilah/Ilmu Ghayah menulis "capaian Al Qur'an".
   */
  domain?: Domain;
}

/**
 * DUA dropdown terpisah: Tahun Hijriyah dan Bulan.
 * Aturan proyek: jangan pernah menggabungkan bulan dan tahun dalam satu dropdown,
 * supaya jumlah pilihan tidak bertambah saat tahun ajaran berganti.
 */
export default function PemilihTahunBulan({
  bulan,
  tahun,
  bulanId,
  onTahun,
  onBulan,
  idAwalan,
  tanpaDataAwal = false,
  catatan,
  domain = "alquran",
}: Props) {
  const daftarTahun = useMemo(
    () => [...new Set(bulan.map((b) => Number(b.hijri_year)))].sort((a, b) => a - b),
    [bulan],
  );

  const bulanTahunIni = useMemo(
    () =>
      bulan
        .filter((b) => Number(b.hijri_year) === Number(tahun))
        .filter((b) => (tanpaDataAwal ? b.month_no > 0 : true))
        .sort((a, b) => a.month_no - b.month_no),
    [bulan, tahun, tanpaDataAwal],
  );

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <DropdownCari
        id={`${idAwalan}-tahun`}
        label="Tahun Hijriyah"
        opsi={daftarTahun.map((t) => ({ nilai: String(t), label: `${t} H` }))}
        nilai={String(tahun)}
        onChange={(v) => onTahun(Number(v))}
        placeholderCari="Ketik tahun..."
      />
      <div>
        <DropdownCari
          id={`${idAwalan}-bulan`}
          label="Bulan"
          opsi={bulanTahunIni.map((b) => ({ nilai: b.id, label: b.name }))}
          nilai={bulanId}
          onChange={onBulan}
          placeholderCari="Ketik bulan..."
        />
        {catatan && <p className="mt-1 text-xs text-gray-500">{catatan}</p>}
        {Number(tahun) && <PenandaBelumLengkap bulanId={bulanId} domain={domain} />}
      </div>
    </div>
  );
}

interface BarisLengkap {
  student_id: string;
  subject_id: string;
  month_id: string;
}

const NAMA_DOMAIN: Record<Domain, string> = {
  alquran: "Al Qur'an",
  wasilah: "Ilmu Wasilah",
  ghayah: "Ilmu Ghayah",
};

/**
 * Pemberitahuan "data belum lengkap" per bulan untuk laman Capaian.
 * Hanya untuk Mudir/Admin/Masul (guru lain hanya melihat halaqahnya di halaman Input).
 * Bulan dikosongkan = belum diisi, bukan 0 (docs/SPEC.md).
 *
 * Diperiksa per domain: yang dihitung hanya santri yang punya halaqah aktif di domain
 * itu (santri tanpa halaqah dilaporkan kotak notifikasi tersendiri), dan hanya mata
 * pelajaran yang ditetapkan untuk halaqahnya. Definisi "lengkap" mengikuti perilaku
 * yang sudah dipakai untuk Al Qur'an: sedikitnya satu mata pelajaran sudah terisi.
 */
function PenandaBelumLengkap({ bulanId, domain }: { bulanId: string; domain: Domain }) {
  const { profile } = useAuth();
  const [jumlah, setJumlah] = useState<{ belum: number; total: number } | null>(null);
  const boleh = !!profile && isPeninjau(profile.role);

  useEffect(() => {
    let aktif = true;
    if (!boleh || !bulanId) {
      setJumlah(null);
      return;
    }
    void (async () => {
      // Halaqah aktif domain ini + anggotanya.
      const { data: halaqah } = await supabase
        .from("halaqahs")
        .select("id")
        .eq("domain", domain)
        .eq("is_active", true);
      const idHalaqah = (halaqah ?? []).map((h) => h.id);
      if (!aktif) return;
      if (idHalaqah.length === 0) {
        setJumlah({ belum: 0, total: 0 });
        return;
      }
      const [{ data: anggota }, { data: mapel }, { data: entri }] = await Promise.all([
        supabase
          .from("halaqah_members")
          .select("student_id, halaqah_id")
          .in("halaqah_id", idHalaqah)
          .is("left_on", null),
        supabase.from("halaqah_subjects").select("halaqah_id, subject_id").in("halaqah_id", idHalaqah),
        supabase.from("progress_entries").select("student_id, subject_id").eq("month_id", bulanId),
      ]);
      if (!aktif) return;

      const terisi = new Set(
        ((entri ?? []) as BarisLengkap[]).map((r) => `${r.student_id}|${r.subject_id}`),
      );
      // Mapel yang ditetapkan per halaqah. Bila halaqah belum punya penetapan,
      // dipakai semua bidang aktif domain itu (perilaku lama untuk Al Qur'an).
      const mapelHalaqah = new Map<string, Set<string>>();
      for (const r of (mapel ?? []) as Array<{ halaqah_id: string; subject_id: string }>) {
        const set = mapelHalaqah.get(r.halaqah_id) ?? new Set<string>();
        set.add(r.subject_id);
        mapelHalaqah.set(r.halaqah_id, set);
      }
      const { data: bidang } = await supabase
        .from("subjects")
        .select("id")
        .eq("domain", domain)
        .eq("is_active", true);
      if (!aktif) return;
      const semuaMapel = (bidang ?? []).map((b) => b.id);

      const kosongSantri = new Set<string>();
      const dilihat = new Set<string>();
      for (const a of (anggota ?? []) as Array<{ student_id: string; halaqah_id: string }>) {
        dilihat.add(a.student_id);
        const perlu = [...(mapelHalaqah.get(a.halaqah_id) ?? new Set(semuaMapel))];
        if (perlu.length === 0) continue;
        const ada = perlu.some((id) => terisi.has(`${a.student_id}|${id}`));
        if (!ada) kosongSantri.add(a.student_id);
      }
      setJumlah({ belum: kosongSantri.size, total: dilihat.size });
    })();
    return () => {
      aktif = false;
    };
  }, [bulanId, boleh, domain]);

  if (!jumlah || jumlah.total === 0) return null;
  return (
    <p
      className={
        "mt-1 text-xs " + (jumlah.belum > 0 ? "text-amber-800" : "text-emerald-800")
      }
    >
      {jumlah.belum > 0
        ? `Data belum lengkap: ${jumlah.belum} dari ${jumlah.total} santri belum punya capaian ${NAMA_DOMAIN[domain]} bulan ini.`
        : `Semua santri sudah punya capaian ${NAMA_DOMAIN[domain]} bulan ini.`}
    </p>
  );
}
