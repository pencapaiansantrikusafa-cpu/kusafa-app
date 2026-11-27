import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { DOMAIN_LABEL, bolehInputDomain, hanyaHalaqahDiampu, type Domain } from "../lib/roles";
import { supabase } from "../lib/supabase";
import KotakBelumLengkap from "../components/KotakBelumLengkap";
import PemilihTahunBulan from "../components/PemilihTahunBulan";
import PemilihHalaqah, { halaqahDiampu, petaPengampu, type GuruBaris } from "../components/PemilihHalaqah";
import type { CariDiServer } from "../components/DropdownCari";
import FormInputWasilah, { type DataFormWasilah, type ItemWasilah } from "./FormInputWasilah";

interface Halaqah {
  id: string;
  code: string;
  /** Nama tidak dikirim server; dropdown memakai kode + pengampu. */
  name: string;
}

interface Bulan {
  id: string;
  month_no: number;
  name: string;
  hijri_year: number;
}

interface GuruWasilah extends GuruBaris {
  subject_id: string | null;
}

interface DataBoot {
  boleh: boolean;
  domain: Domain;
  halaqah: Array<{ id: string; code: string }>;
  guru: GuruWasilah[];
  bulan: Bulan[];
  mapel: Array<{ halaqah_id: string; subject_id: string; name: string }>;
  setelan: Array<{ month_id: string; effective_days: number | null; terkunci: boolean }>;
}

/** Label dropdown: "Level 1A - Ustadzah Mudarrisah 1" (aturan tampilan AGENTS.md). */
function petaPengampuWasilah(guru: GuruWasilah[]): Record<string, string> {
  return petaPengampu(
    guru.map((g) => ({ halaqah_id: g.halaqah_id, profile_id: g.profile_id, full_name: g.full_name })),
  );
}

/**
 * Halaman Input capaian Ilmu Wasilah / Ilmu Ghayah.
 *
 * Pola sama dengan Al Qur'an (T5c-2): pembukaan halaman dan isi form masing-masing
 * SATU permintaan ke database (`wasilah_input_boot`, `wasilah_input_form`), dan
 * pencarian item dilakukan di server. Input disalin ke anggota oleh database.
 */
export default function InputWasilahPage({ domain }: { domain: Domain }) {
  const { profile } = useAuth();
  const [halaqah, setHalaqah] = useState<Halaqah[]>([]);
  const [semuaHalaqah, setSemuaHalaqah] = useState<{ id: string; code: string }[]>([]);
  const [guru, setGuru] = useState<GuruWasilah[]>([]);
  const [pengampu, setPengampu] = useState<Record<string, string>>({});
  const [halaqahId, setHalaqahId] = useState("");
  const [bulan, setBulan] = useState<Bulan[]>([]);
  const [bulanId, setBulanId] = useState("");
  const [tahun, setTahun] = useState<number | "">("");
  const [form, setForm] = useState<DataFormWasilah | null>(null);
  const [memuat, setMemuat] = useState(true);
  const [memuatForm, setMemuatForm] = useState(false);
  const [galat, setGalat] = useState<string | null>(null);
  const [sukses, setSukses] = useState<string | null>(null);

  // ---------- Pembukaan halaman: satu RPC ----------
  useEffect(() => {
    let aktif = true;
    setMemuat(true);
    setGalat(null);
    void (async () => {
      const { data, error } = await supabase.rpc("wasilah_input_boot", { p_domain: domain });
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
      const g = paket.guru ?? [];
      setGuru(g);
      setPengampu(petaPengampuWasilah(g));

      const semua = (paket.bulan ?? []).filter((m) => m.month_no > 0);
      setBulan(semua);
      // Bulan awal: bulan terakhir yang sudah punya Hari Efektif untuk domain ini.
      // Bulan yang belum punya Hari Efektif belum berjalan, jadi tidak dijadikan awal.
      const berjalan = new Set(
        (paket.setelan ?? [])
          .filter((x) => x.effective_days !== null)
          .map((x) => x.month_id),
      );
      const terakhir =
        [...semua].reverse().find((m) => berjalan.has(m.id)) ?? semua[semua.length - 1];
      setBulanId((prev) => prev || terakhir?.id || "");
      setTahun((prev) => (prev !== "" ? prev : terakhir?.hijri_year ?? ""));

      // Masul/pengampu hanya ditawari halaqah yang diampu (aturan sama dengan Al Qur'an).
      const semuaHal: Halaqah[] = (paket.halaqah ?? []).map((h) => ({ ...h, name: "" }));
      let daftar = semuaHal;
      // Masul domain ini melihat semua halaqah domainnya; pengampu hanya yang diampu.
      if (profile && hanyaHalaqahDiampu(profile.role) && !bolehInputDomain(profile.role, domain)) {
        const diampu = halaqahDiampu(
          g.map((x) => ({ halaqah_id: x.halaqah_id, profile_id: x.profile_id, full_name: x.full_name })),
          profile.id,
        );
        daftar = semuaHal.filter((h) => diampu.has(h.id));
      }
      setHalaqah(daftar);
      setSemuaHalaqah(paket.halaqah ?? []);
      setHalaqahId((prev) => (daftar.some((h) => h.id === prev) ? prev : (daftar[0]?.id ?? "")));
      setMemuat(false);
    })();
    return () => {
      aktif = false;
    };
  }, [domain, profile]);

  // ---------- Isi form: satu RPC ----------
  const muatForm = useCallback(async () => {
    if (!halaqahId || !bulanId) {
      setForm(null);
      return;
    }
    setMemuatForm(true);
    setGalat(null);
    const { data, error } = await supabase.rpc("wasilah_input_form", {
      p_halaqah: halaqahId,
      p_bulan: bulanId,
    });
    if (error) {
      setGalat(error.message);
      setMemuatForm(false);
      return;
    }
    const paket = (data ?? {}) as unknown as DataFormWasilah;
    if (!paket.boleh) {
      setGalat("Profil akun belum aktif atau tidak punya akses ke data ini.");
      setMemuatForm(false);
      return;
    }
    setForm(paket);
    setMemuatForm(false);
  }, [halaqahId, bulanId]);

  useEffect(() => {
    void muatForm();
  }, [muatForm]);

  // Pesan sukses hanya untuk halaqah/bulan yang baru disimpan; hilang saat berganti pilihan.
  useEffect(() => {
    setSukses(null);
  }, [halaqahId, bulanId]);

  /** Pencarian item di server per mata pelajaran (pola T5c; label berawalan nama mapel). */
  const cariItemServer = useCallback(
    (subjectId: string): CariDiServer => ({
      awal: async () => cari(subjectId, ""),
      cari: async (kata: string) => cari(subjectId, kata),
    }),
    [],
  );

  async function cari(subjectId: string, kata: string) {
    const { data, error } = await supabase.rpc("curriculum_items_search", {
      p_subject: subjectId,
      p_q: kata,
      p_limit: 60,
    });
    if (error) throw new Error(error.message);
    return ((data ?? []) as ItemWasilah[]).map((it) => ({
      nilai: it.id,
      label: it.label,
      siklik: it.siklik,
    }));
  }

  const namaHalaqah = useMemo(
    () => halaqah.find((h) => h.id === halaqahId)?.code ?? "",
    [halaqah, halaqahId],
  );
  const namaBulan = useMemo(() => {
    const b = bulan.find((x) => x.id === bulanId);
    return b ? `${b.name} ${b.hijri_year} H` : "";
  }, [bulan, bulanId]);

  const labelHalaqah =
    domain === "wasilah" ? "Level" : domain === "ghayah" ? "Kelompok" : "Halaqah";

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Input capaian {DOMAIN_LABEL[domain]}</h1>
        <p className="mt-1 text-sm text-gray-700">
          Nilai dipilih sekali per halaqah dan mata pelajaran, lalu disalin ke semua anggota.
        </p>
      </div>

      <div className="space-y-3 rounded-xl bg-white p-4 ring-1 ring-black/5">
        <PemilihHalaqah
          id={`input-halaqah-${domain}`}
          label={labelHalaqah}
          halaqah={halaqah}
          pengampu={pengampu}
          nilai={halaqahId}
          onChange={setHalaqahId}
          keterangan={
            pengampu[halaqahId]
              ? `Pengampu: ${pengampu[halaqahId]}`
              : "Pengampu belum ditetapkan"
          }
        />
        <PemilihTahunBulan
          bulan={bulan}
          tahun={tahun}
          bulanId={bulanId}
          idAwalan={`input-${domain}`}
          tanpaDataAwal
          domain={domain}
          onTahun={(t) => {
            setTahun(t);
            const calon = bulan.filter((b) => Number(b.hijri_year) === t && b.month_no > 0);
            if (!calon.some((b) => b.id === bulanId)) setBulanId(calon[calon.length - 1]?.id ?? "");
          }}
          onBulan={setBulanId}
        />
        {halaqah.length === 0 && !memuat && (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Anda belum ditetapkan sebagai pengampu halaqah {DOMAIN_LABEL[domain]} mana pun.
            Hubungi Admin.
          </p>
        )}
      </div>

      {galat && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
          Gagal memuat: {galat}
        </p>
      )}

      {sukses && (
        <p role="status" className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
          {sukses}
        </p>
      )}

      {bulanId && (
        <KotakBelumLengkap
          bulanId={bulanId}
          domain={domain}
          halaqahAwal={semuaHalaqah}
          guruAwal={guru}
          tunda={memuatForm}
        />
      )}

      {memuat || memuatForm ? (
        <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">
          Memuat data...
        </p>
      ) : !form ? (
        <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">
          {halaqqahKosong(namaHalaqah)}
        </p>
      ) : form.santri.length === 0 && !form.tanpa_mapel ? (
        <p className="rounded-xl bg-white p-6 text-sm text-gray-600 ring-1 ring-black/5">
          Belum ada anggota di {namaHalaqah || "halaqah ini"}.
        </p>
      ) : (
        <FormInputWasilah
          halaqahId={halaqahId}
          bulanId={bulanId}
          bulanNama={`${namaHalaqah} · ${namaBulan}`}
          data={form}
          cariItemServer={cariItemServer}
          onSelesai={(pesanSukses) => {
            setSukses(pesanSukses);
            void muatForm();
          }}
        />
      )}
    </div>
  );
}

function halaqqahKosong(nama: string): string {
  return nama ? `Belum ada data untuk ${nama}.` : "Pilih halaqah terlebih dahulu.";
}
