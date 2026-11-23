import { useEffect, useMemo, useState } from "react";
import DropdownCari from "./DropdownCari";
import { supabase } from "../lib/supabase";
import { useAuth } from "../lib/auth-context";
import { isPeninjau } from "../lib/roles";

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
        {Number(tahun) && <PenandaBelumLengkap bulanId={bulanId} />}
      </div>
    </div>
  );
}

interface BarisLengkap {
  student_id: string;
  subject_id: string;
  month_id: string;
}

/**
 * Pemberitahuan "data belum lengkap" per bulan untuk laman Capaian.
 * Hanya untuk Mudir/Admin/Masul (guru lain hanya melihat halaqahnya di halaman Input).
 * Bulan dikosongkan = belum diisi, bukan 0 (docs/SPEC.md).
 */
function PenandaBelumLengkap({ bulanId }: { bulanId: string }) {
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
      const { data, error } = await supabase
        .from("progress_entries")
        .select("student_id, subject_id, month_id")
        .eq("month_id", bulanId);
      if (!aktif || error) return;
      const terisi = new Set(
        ((data ?? []) as BarisLengkap[]).map((r) => `${r.student_id}|${r.subject_id}`),
      );
      const { data: santri } = await supabase.from("students").select("id").eq("is_active", true);
      const { data: bidang } = await supabase
        .from("subjects")
        .select("id")
        .eq("domain", "alquran")
        .eq("is_active", true);
      if (!aktif) return;
      const n = (santri ?? []).length;
      const kosongSantri = new Set<string>();
      for (const s of santri ?? []) {
        const ada = (bidang ?? []).some((bd) => terisi.has(`${s.id}|${bd.id}`));
        if (!ada) kosongSantri.add(s.id);
      }
      setJumlah({ belum: kosongSantri.size, total: n });
    })();
    return () => {
      aktif = false;
    };
  }, [bulanId, boleh]);

  if (!jumlah || jumlah.total === 0) return null;
  return (
    <p
      className={
        "mt-1 text-xs " + (jumlah.belum > 0 ? "text-amber-800" : "text-emerald-800")
      }
    >
      {jumlah.belum > 0
        ? `Data belum lengkap: ${jumlah.belum} dari ${jumlah.total} santri belum punya capaian Al Qur'an bulan ini.`
        : "Semua santri sudah punya capaian Al Qur'an bulan ini."}
    </p>
  );
}
