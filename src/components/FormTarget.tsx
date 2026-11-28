import { useEffect, useMemo, useState } from "react";
import DropdownCari, { type OpsiCari } from "./DropdownCari";
import PemilihHalaqah, { type HalaqahData } from "./PemilihHalaqah";
import PemilihTahunBulan, { type BulanData } from "./PemilihTahunBulan";
import { supabase } from "../lib/supabase";
import {
  ajukanTarget,
  ajukanTargetMassalAlquran,
  infoKonfirmasi,
  ubahTarget,
  type BarisTarget,
} from "../lib/target";
import { adalahAksesPenuh, DOMAIN_LABEL, type Domain } from "../lib/roles";
import { useAuth } from "../lib/auth-context";

interface Bidang {
  id: string;
  name: string;
}

interface Props {
  domain: Domain;
  /** `ajukan` = target baru; `ubah` = baris baru menggantikan target lama. */
  mode: "ajukan" | "ubah";
  /** Target yang diubah (wajib bila mode `ubah`). */
  target?: (BarisTarget & { target_item?: { label: string } | null }) | null;
  halaqah: HalaqahData[];
  pengampu: Record<string, string>;
  bulan: BulanData[];
  bidang: Bidang[];
  /** Halaqah yang sudah dipilih di halaman, menjadi nilai awal form. */
  halaqahAwal?: string;
  sedang: boolean;
  onSedang: (v: boolean) => void;
  onBatal: () => void;
  /** Dipanggil bila target tersimpan; `pesan` ditampilkan halaman. */
  onSelesai: (pesan: string) => void;
}

/**
 * Formulir mengajukan / mengubah target (T7).
 *
 * Bentuk target mengikuti domain (keputusan T7 3.2c):
 * - Al Qur'an: per **santri**, per bidang (Tilawah/Tahfidz/Kitabah), **harian**;
 *   tersedia pula pengajuan massal untuk seluruh anggota halaqah.
 * - Ilmu Wasilah / Ilmu Ghayah: per **halaqah**, per mata pelajaran, **bulanan langsung**.
 *
 * Bulan berlaku dipilih saat mengajukan (default bulan berjalan). Bulan lewat/terkunci
 * hanya boleh dilanjutkan Mudir/Admin dengan centang konfirmasi (RPC menolak yang lain).
 */
export default function FormTarget({
  domain,
  mode,
  target,
  halaqah,
  pengampu,
  bulan,
  bidang,
  halaqahAwal,
  sedang,
  onSedang,
  onBatal,
  onSelesai,
}: Props) {
  const { profile } = useAuth();
  const aksesPenuh = !!profile && adalahAksesPenuh(profile.role);
  const isAlquran = domain === "alquran";
  const modeUbah = mode === "ubah" && !!target;

  const [halaqahId, setHalaqahId] = useState(target?.halaqah_id ?? halaqahAwal ?? "");
  const [santriId, setSantriId] = useState("");
  const [mapelId, setMapelId] = useState("");
  const [butir, setButir] = useState<OpsiCari | null>(() =>
    target?.target_item_id
      ? { nilai: target.target_item_id, label: target.target_item?.label ?? "butir terpilih" }
      : null,
  );
  const [nilai, setNilai] = useState(
    modeUbah && target?.amount !== null && target?.amount !== undefined
      ? String(target.amount)
      : "",
  );
  const [tahun, setTahun] = useState<number | "">("");
  const [bulanId, setBulanId] = useState("");
  const [catatan, setCatatan] = useState(target?.note ?? "");
  const [massal, setMassal] = useState(false);
  const [galat, setGalat] = useState<string | null>(null);

  const [anggota, setAnggota] = useState<Array<{ id: string; full_name: string }>>([]);
  const [mapelTersedia, setMapelTersedia] = useState<Bidang[]>([]);
  const [konfirmasi, setKonfirmasi] = useState(false);
  const [peringatan, setPeringatan] = useState<string | null>(null);
  /** Nama sasaran & mapel target lama (mode ubah, tampilan baca saja). */
  const [namaSasaran, setNamaSasaran] = useState<string>("");

  // Nama sasaran target lama (mode ubah, tampilan baca saja).
  useEffect(() => {
    if (!modeUbah || !target?.student_id) return;
    let aktif = true;
    void (async () => {
      const { data } = await supabase
        .from("students")
        .select("full_name")
        .eq("id", target.student_id)
        .maybeSingle();
      if (aktif && data) setNamaSasaran(data.full_name);
    })();
    return () => {
      aktif = false;
    };
  }, [modeUbah, target]);

  // Bulan default: bulan berjalan domain ini (fungsi database `target_bulan_berjalan`).
  useEffect(() => {
    let aktif = true;
    void (async () => {
      try {
        const { data } = await supabase.rpc("target_bulan_berjalan", { p_domain: domain });
        if (!aktif) return;
        const id = (data as unknown as string) ?? "";
        const dipilih = bulan.find((b) => b.id === id) ?? bulan[bulan.length - 1];
        if (dipilih) {
          setBulanId((prev) => prev || dipilih.id);
          setTahun((prev) => (prev !== "" ? prev : Number(dipilih.hijri_year)));
        }
      } catch {
        /* biarkan pengguna memilih manual bila gagal */
      }
    })();
    return () => {
      aktif = false;
    };
  }, [domain, bulan]);

  // Anggota halaqah (Al Qur'an: target per santri) dan mata pelajaran halaqah.
  useEffect(() => {
    let aktif = true;
    setAnggota([]);
    setMapelTersedia([]);
    if (!halaqahId) return;
    void (async () => {
      if (isAlquran) {
        const { data } = await supabase
          .from("halaqah_members")
          .select("student_id, students!inner(full_name)")
          .eq("halaqah_id", halaqahId)
          .is("left_on", null);
        if (!aktif) return;
        const daftar = ((data ?? []) as unknown as Array<{
          student_id: string;
          students: { full_name: string } | { full_name: string }[];
        }>).map((r) => {
          const s = Array.isArray(r.students) ? r.students[0] : r.students;
          return { id: r.student_id, full_name: s?.full_name ?? "" };
        });
        daftar.sort((a, b) => a.full_name.localeCompare(b.full_name));
        setAnggota(daftar);
        setMapelTersedia(bidang);
      } else {
        const { data } = await supabase
          .from("halaqah_subjects")
          .select("subject_id, subjects!inner(name, is_active)")
          .eq("halaqah_id", halaqahId);
        if (!aktif) return;
        const daftar = ((data ?? []) as unknown as Array<{
          subject_id: string;
          subjects: { name: string; is_active: boolean } | { name: string; is_active: boolean }[];
        }>)
          .map((r) => {
            const s = Array.isArray(r.subjects) ? r.subjects[0] : r.subjects;
            return { id: r.subject_id, name: s?.name ?? "", is_active: s?.is_active ?? true };
          })
          .filter((s) => s.is_active);
        setMapelTersedia(daftar);
      }
    })();
    return () => {
      aktif = false;
    };
  }, [halaqahId, isAlquran, bidang]);

  // Periksa bulan lewat/terkunci setiap kali bulan berlaku berubah.
  useEffect(() => {
    let aktif = true;
    setPeringatan(null);
    setKonfirmasi(false);
    if (!bulanId) return;
    void (async () => {
      try {
        const info = await infoKonfirmasi(domain, bulanId);
        if (!aktif || !info) return;
        if (info.perlu_konfirmasi) {
          setPeringatan(
            info.lewat
              ? "Bulan target yang dipilih SUDAH LEWAT. Mengubah target bulan lewat hanya untuk keperluan koreksi."
              : "Bulan target yang dipilih SUDAH DIKUNCI.",
          );
        }
      } catch {
        if (aktif) setPeringatan(null);
      }
    })();
    return () => {
      aktif = false;
    };
  }, [bulanId, domain]);

  /** Pencarian butir tujuan akhir di server (hanya mapel yang dipilih). */
  async function cariButirServer(subject: string, kata: string): Promise<OpsiCari[]> {
    const { data, error } = await supabase.rpc("curriculum_items_search", {
      p_subject: subject,
      p_q: kata,
      p_limit: 60,
    });
    if (error) throw new Error(error.message);
    return ((data ?? []) as Array<{ id: string; label: string }>).map((it) => ({
      nilai: it.id,
      label: it.label,
    }));
  }

  const bisaSimpan = useMemo(() => {
    if (!halaqahId) return false;
    if (modeUbah) {
      // sasaran & mapel mengikuti target lama, tidak diubah
    } else {
      if (isAlquran && !massal && !santriId) return false;
      if (!mapelId) return false;
    }
    if (isAlquran) {
      const n = Number(nilai);
      if (nilai === "" || !Number.isFinite(n) || n <= 0) return false;
    } else if (!butir) {
      return false;
    }
    if (!bulanId) return false;
    if (peringatan && aksesPenuh && !konfirmasi) return false;
    if (peringatan && !aksesPenuh) return false;
    return true;
  }, [modeUbah, halaqahId, isAlquran, massal, santriId, mapelId, butir, nilai, bulanId, peringatan, aksesPenuh, konfirmasi]);

  async function simpan() {
    setGalat(null);
    const jumlah = Number(nilai);
    const perluKonfirmasi = !!peringatan && aksesPenuh && konfirmasi;
    onSedang(true);
    try {
      let pesan: string;
      if (modeUbah && target) {
        const h = await ubahTarget({
          targetLamaId: target.id,
          amount: isAlquran ? jumlah : null,
          bulanId,
          targetItemId: isAlquran ? null : butir?.nilai ?? target.target_item_id,
          note: catatan,
          konfirmasi: perluKonfirmasi,
        });
        pesan =
          h.status === "disetujui"
            ? "Target baru tersimpan dan langsung disetujui, berlaku mulai bulan terpilih. Target lama tetap berlaku untuk bulan sebelumnya."
            : "Target baru diajukan dan menunggu persetujuan. Target lama tetap berlaku untuk bulan sebelumnya.";
      } else if (isAlquran && massal) {
        const h = await ajukanTargetMassalAlquran({
          halaqahId,
          subjectId: mapelId,
          bulanId,
          amount: jumlah,
          note: catatan,
          konfirmasi: perluKonfirmasi,
        });
        pesan =
          h.status === "disetujui"
            ? `Target massal disetujui untuk ${h.jumlah_santri ?? 0} santri (berlaku mulai bulan terpilih).`
            : `Target massal diajukan untuk ${h.jumlah_santri ?? 0} santri dan menunggu persetujuan.`;
      } else {
        const h = await ajukanTarget({
          domain,
          subjectId: mapelId,
          studentId: isAlquran ? santriId : null,
          // Constraint database: tepat satu dari student_id/halaqah_id. Target Al Qur'an
          // adalah per santri, jadi halaqah_id dikirim NULL.
          halaqahId: isAlquran ? null : halaqahId,
          bulanId,
          amount: isAlquran ? jumlah : null,
          periode: isAlquran ? "harian" : "bulanan",
          targetItemId: isAlquran ? null : butir?.nilai ?? null,
          note: catatan,
          konfirmasi: perluKonfirmasi,
        });
        pesan =
          h.status === "disetujui"
            ? "Target tersimpan dan langsung disetujui (berlaku mulai bulan terpilih)."
            : "Target diajukan dan menunggu persetujuan Masul domain / Mudir / Admin.";
      }
      onSelesai(pesan);
    } catch (e) {
      setGalat(e instanceof Error ? e.message : String(e));
    } finally {
      onSedang(false);
    }
  }

  const labelHalaqah = isAlquran ? "Halaqah" : domain === "wasilah" ? "Level" : "Kelompok";

  return (
    <div className="fixed inset-0 z-50 flex items-end bg-black/40 sm:items-center sm:justify-center" role="presentation">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="judul-form-target"
        className="max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl sm:max-w-xl sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="judul-form-target" className="text-base font-bold text-gray-900">
          {modeUbah ? "Ubah target" : "Ajukan target"} {DOMAIN_LABEL[domain]}
        </h2>
        <p className="mt-1 text-xs text-gray-600">
          {isAlquran
            ? "Target Al Qur'an per santri per bidang, dihitung harian (target bulanan = target harian × Hadir)."
            : "Target Ilmu Wasilah/Ilmu Ghayah per halaqah per mata pelajaran = satu butir tujuan akhir (bukan jumlah), bulanan langsung."}
        </p>

        <div className="mt-4 space-y-3">
          {modeUbah && target ? (
            <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
              <p>
                <span className="text-gray-500">Sasaran: </span>
                <strong className="text-gray-900">{namaSasaran || "—"}</strong>
              </p>
              {!isAlquran && (
                <p className="mt-0.5">
                  <span className="text-gray-500">Halaqah: </span>
                  {halaqahId ? (halaqah.find((h) => h.id === halaqahId)?.code ?? "—") : "—"}
                </p>
              )}
              <p className="mt-0.5">
                <span className="text-gray-500">Mata pelajaran: </span>
                {bidang.find((b) => b.id === target.subject_id)?.name ?? "—"}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Mengubah target membuat baris baru; target lama tetap utuh sebagai riwayat.
              </p>
            </div>
          ) : (
            <>
              <PemilihHalaqah
                id={`target-halaqah-${domain}`}
                label={labelHalaqah}
                halaqah={halaqah}
                pengampu={pengampu}
                nilai={halaqahId}
                onChange={(id) => {
                  setHalaqahId(id);
                  setSantriId("");
                  setMapelId("");
                }}
                keterangan={
                  pengampu[halaqahId] ? `Pengampu: ${pengampu[halaqahId]}` : "Pengampu belum ditetapkan"
                }
              />

              {isAlquran && (
                <div>
                  <DropdownCari
                    id="target-santri"
                    label="Santri"
                    opsi={anggota.map((s) => ({ nilai: s.id, label: s.full_name }))}
                    nilai={santriId}
                    onChange={setSantriId}
                    opsiKosong={massal ? "— target massal (semua anggota) —" : "— pilih santri —"}
                    disabled={massal}
                    placeholderCari="Ketik nama santri..."
                  />
                  <label className="mt-2 flex items-center gap-2 text-xs text-gray-700">
                    <input
                      type="checkbox"
                      checked={massal}
                      onChange={(e) => {
                        setMassal(e.target.checked);
                        setSantriId("");
                      }}
                    />
                    Ajukan sekaligus untuk seluruh anggota halaqah (satu nilai, bisa disesuaikan per santri kemudian)
                  </label>
                </div>
              )}

              <DropdownCari
                id="target-mapel"
                label="Mata pelajaran"
                opsi={mapelTersedia.map((b) => ({ nilai: b.id, label: b.name }))}
                nilai={mapelId}
                onChange={setMapelId}
                placeholderCari="Ketik mata pelajaran..."
                keterangan={
                  mapelTersedia.length === 0 ? "Mata pelajaran halaqah ini belum ditetapkan." : undefined
                }
              />
            </>
          )}

          {!isAlquran && (
            <DropdownCari
              id="target-butir"
              label="Butir tujuan akhir"
              opsi={butir ? [butir] : []}
              diServer={mapelId ? { awal: () => cariButirServer(mapelId, ""), cari: (kata) => cariButirServer(mapelId, kata) } : undefined}
              nilai={butir?.nilai ?? ""}
              onChange={(_, o) => setButir(o ?? null)}
              opsiKosong="— pilih butir tujuan akhir —"
              disabled={!mapelId}
              placeholderCari={mapelId ? 'Cari butir (mis. "1" atau "Quraisy")...' : "Pilih mata pelajaran dulu"}
              keterangan={mapelId ? undefined : "Pilih mata pelajaran terlebih dahulu."}
            />
          )}

          {isAlquran && (
            <div>
              <label htmlFor="target-nilai" className="block text-sm font-medium text-gray-800">
                Target harian
              </label>
              <input
                id="target-nilai"
                type="number"
                min="0"
                step="0.1"
                inputMode="decimal"
                value={nilai}
                onChange={(e) => setNilai(e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base"
                placeholder="mis. 1 (halaman per hari)"
              />
              <p className="mt-1 text-xs text-gray-500">Boleh pecahan. Tidak boleh negatif.</p>
            </div>
          )}

          <PemilihTahunBulan
            bulan={bulan}
            tahun={tahun}
            bulanId={bulanId}
            idAwalan="target-bulan-berlaku"
            onTahun={setTahun}
            onBulan={setBulanId}
            tanpaDataAwal
            domain={domain}
            catatan="Target berlaku penuh sebulan ini dan bulan-bulan berikutnya sampai diganti."
          />

          <div>
            <label htmlFor="target-catatan" className="block text-sm font-medium text-gray-800">
              Catatan (opsional)
            </label>
            <textarea
              id="target-catatan"
              rows={2}
              value={catatan}
              onChange={(e) => setCatatan(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              placeholder="Alasan penyesuaian target, mis. santri sedang mengulang."
            />
          </div>

          {peringatan && (
            <div className="space-y-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
              <p>{peringatan}</p>
              {aksesPenuh ? (
                <label className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={konfirmasi}
                    onChange={(e) => setKonfirmasi(e.target.checked)}
                  />
                  <span>Saya (Mudir/Admin) tetap ingin melanjutkan.</span>
                </label>
              ) : (
                <p className="text-xs">
                  Hanya Mudir/Admin yang dapat melanjutkan. Pilih bulan berjalan, atau minta Mudir/Admin.
                </p>
              )}
            </div>
          )}

          {galat && (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
              {galat}
            </p>
          )}
        </div>

        <div className="mt-4 flex flex-wrap justify-end gap-2">
          <button
            type="button"
            onClick={onBatal}
            disabled={sedang}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={() => void simpan()}
            disabled={sedang || !bisaSimpan}
            className="rounded-lg bg-kusafa px-3 py-2 text-sm font-medium text-white hover:bg-kusafa/90 disabled:opacity-50"
          >
            {sedang ? "Menyimpan..." : modeUbah ? "Simpan perubahan target" : "Ajukan target"}
          </button>
        </div>
      </div>
    </div>
  );
}
