import { useEffect, useId, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

/**
 * Lapisan tertinggi aplikasi untuk semua dropdown.
 *
 * Dipakai agar daftar pilihan SELALU melayang di atas bagian lain, tidak peduli
 * berada di dalam kartu/tabel/bingkai bergulir mana pun. Bila angka lapisan ini
 * diubah, ubah juga di `AGENTS.md` (aturan tampilan) supaya halaman baru mengikuti.
 */
export const LAPISAN_DROPDOWN = 60;

/**
 * Nomor di ujung label: "Menyalin - 88" -> 88, "Quraisy : 12" -> 12, "An Naba' - 40" -> 40.
 * Dipakai agar guru cukup mengetik nomor untuk menemukan item.
 */
function nomorAkhir(label: string): number | null {
  const m = label.match(/-\s*(\d+)\s*$/) ?? label.match(/:\s*(\d+)\s*$/);
  return m ? Number(m[1]) : null;
}

export interface OpsiCari {
  nilai: string;
  label: string;
  /** Teks tambahan untuk pencocokan (mis. nama pengampu), tidak wajib ditampilkan. */
  cariJuga?: string;
  /**
   * Buku siklik (dipakai halaman Input untuk menentukan boleh/tidaknya "khatam").
   * Diisi hanya oleh pemanggil yang membutuhkannya; komponen ini tidak mengolahnya.
   */
  siklik?: boolean;
}

/**
 * Mode "cari di server": daftar pilihan diambil dari database saat pengguna mengetik,
 * jadi halaman tidak perlu mengunduh seluruh daftar. Dipakai halaman Input (T5c).
 * `cari` mengembalikan hasil untuk satu kata kunci (sudah dibatasi di server).
 */
export interface CariDiServer {
  cari: (kata: string) => Promise<OpsiCari[]>;
  /** Teks saat kotak dibuka sebelum mengetik (mis. item pertama pada urutan buku). */
  awal?: () => Promise<OpsiCari[]>;
}

interface Props {
  /** id elemen tombol; label memakai `${id}-label`. */
  id: string;
  label: string;
  opsi: OpsiCari[];
  nilai: string;
  /**
   * `opsi` berisi objek pilihan yang diklik (bila ada), sehingga pemanggil bisa
   * menyimpan label/siklik item baru yang belum ada di daftar `opsi` — penting pada
   * mode `diServer`, karena daftar hanya memuat item yang sudah tersimpan.
   */
  onChange: (nilai: string, opsi?: OpsiCari) => void;
  /** Teks pilihan kosong (mis. "— belum diisi —"). Bila diisi, muncul sebagai pilihan pertama. */
  opsiKosong?: string;
  keterangan?: string;
  disabled?: boolean;
  /** Jumlah baris yang ditampilkan sekaligus. */
  batasTampil?: number;
  placeholderCari?: string;
  /** Bila diisi, pencarian dilakukan di server (daftar lokal `opsi` tidak dipakai untuk mencari). */
  diServer?: CariDiServer;
}

/**
 * Dropdown dengan kotak pencarian. Pengguna cukup mengetik sebagian teks
 * (mis. "qura") dan pilihan yang tampil hanya yang mengandung teks itu.
 * Dipakai untuk semua dropdown yang daftarnya bisa panjang.
 */
export default function DropdownCari({
  id,
  label,
  opsi,
  nilai,
  onChange,
  opsiKosong,
  keterangan,
  disabled,
  batasTampil = 60,
  placeholderCari = "Ketik untuk mencari...",
  diServer,
}: Props) {
  const [terbuka, setTerbuka] = useState(false);
  const [cari, setCari] = useState("");
  const [sorot, setSorot] = useState(0);
  const kotakRef = useRef<HTMLDivElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const idLab = `${id}-label`;
  const idDaftar = useId();
  /** Hasil pencarian server (hanya dipakai bila `diServer` diisi). */
  const [hasilServer, setHasilServer] = useState<OpsiCari[]>([]);
  const [memuatServer, setMemuatServer] = useState(false);
  /** Posisi panel (diukur dari tombol), karena panel dilayangkan ke <body> lewat portal. */
  const [posisi, setPosisi] = useState({ top: 0, left: 0, lebar: 0, keAtas: false });
  /**
   * Pilihan yang pernah diklik, disimpan beserta labelnya.
   *
   * Diperlukan karena `opsi` pada mode `diServer` hanya berisi item yang sudah tersimpan:
   * begitu pengguna memilih item dari hasil pencarian, item itu tidak ada di `opsi`, sehingga
   * tanpa simpanan ini tombol jatuh ke teks kosong ("— belum diisi —") walau nilainya terpilih.
   */
  const [pilihan, setPilihan] = useState<Record<string, OpsiCari>>({});

  /**
   * Pencarian di server, ditunda 200 ms agar tidak memanggil database setiap ketukan.
   * Permintaan lama diabaikan bila pengguna sudah mengetik lagi (urutan hasil tetap).
   */
  useEffect(() => {
    if (!diServer || !terbuka) return;
    let aktif = true;
    const jeda = setTimeout(() => {
      setMemuatServer(true);
      const janji = cari.trim() === "" ? (diServer.awal ? diServer.awal() : Promise.resolve([])) : diServer.cari(cari);
      janji
        .then((r) => {
          if (aktif) setHasilServer(r);
        })
        .catch(() => {
          if (aktif) setHasilServer([]);
        })
        .finally(() => {
          if (aktif) setMemuatServer(false);
        });
    }, 200);
    return () => {
      aktif = false;
      clearTimeout(jeda);
    };
  }, [diServer, terbuka, cari]);

  /** Ukur ulang posisi panel terhadap tombol; dipanggil saat dibuka, digulir, dan diubah ukuran layar. */
  useEffect(() => {
    if (!terbuka) return;
    function ukur() {
      const kotak = kotakRef.current;
      if (!kotak) return;
      const r = kotak.getBoundingClientRect();
      // Panel butuh tinggi; bila ruang di bawah sempit tetapi di atas lapang,
      // panel dibuka ke atas supaya tetap tampil lengkap (tidak terpotong layar).
      const PERKIRAAN_TINGGI = 320;
      const ruangBawah = window.innerHeight - r.bottom;
      const ruangAtas = r.top;
      const keAtas = ruangBawah < PERKIRAAN_TINGGI && ruangAtas > ruangBawah;
      setPosisi({
        top: keAtas ? r.top - 4 : r.bottom + 4,
        left: r.left,
        lebar: r.width,
        keAtas,
      });
    }
    ukur();
    window.addEventListener("scroll", ukur, true);
    window.addEventListener("resize", ukur);
    return () => {
      window.removeEventListener("scroll", ukur, true);
      window.removeEventListener("resize", ukur);
    };
  }, [terbuka]);

  const terpilih =
    nilai === ""
      ? undefined
      : opsi.find((o) => o.nilai === nilai) ?? pilihan[nilai];

  const tersaring = useMemo(() => {
    // Mode server: hasil sudah disaring & diurutkan database (60 per permintaan).
    if (diServer) return { daftar: hasilServer.slice(0, batasTampil), jumlah: hasilServer.length };

    const k = cari.trim().toLowerCase();
    if (!k) return { daftar: opsi.slice(0, batasTampil), jumlah: opsi.length };

    // Kata kunci boleh lebih dari satu, mis. "menyalin 88" atau "naba 40".
    // Semua kata harus cocok (DAN), sehingga hasilnya menyempit dengan cepat.
    const kata = k.split(/\s+/).filter(Boolean);
    const angkaTerakhir = /^\d+$/.test(kata[kata.length - 1] ?? "")
      ? Number(kata[kata.length - 1])
      : null;

    const skor = (o: OpsiCari): number => {
      const teks = `${o.label} ${o.cariJuga ?? ""}`.toLowerCase();
      const nomor = nomorAkhir(o.label);
      // Semua kata harus ada di label; bila tidak, tapi nomornya persis, tetap ditawarkan.
      const semuaCocok = kata.every((w) => teks.includes(w));
      if (!semuaCocok) {
        return angkaTerakhir !== null && kata.length === 1 && nomor === angkaTerakhir ? 1 : -1;
      }
      if (angkaTerakhir !== null && nomor === angkaTerakhir) return 0; // nomor persis
      if (teks.startsWith(k)) return 2; // diawali seluruh kata kunci
      const batasKata = new RegExp(`(^|[\\s'\\-:·])${k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`);
      if (batasKata.test(teks)) return 3; // awal kata
      return 4; // mengandung
    };

    const cocok: Array<{ o: OpsiCari; s: number; i: number }> = [];
    opsi.forEach((o, i) => {
      const s = skor(o);
      if (s >= 0) cocok.push({ o, s, i });
    });
    // Urutan: skor, lalu urutan asli (buku) agar stabil.
    cocok.sort((a, b) => a.s - b.s || a.i - b.i);
    return { daftar: cocok.slice(0, batasTampil).map((x) => x.o), jumlah: cocok.length };
  }, [opsi, cari, batasTampil, diServer, hasilServer]);
  const jumlahCocok = tersaring.jumlah;
  const daftarTampil = tersaring.daftar;

  // Tutup bila mengetuk di luar.
  useEffect(() => {
    if (!terbuka) return;
    function onTutup(e: MouseEvent) {
      const t = e.target as Node;
      if (kotakRef.current?.contains(t) || panelRef.current?.contains(t)) return;
      setTerbuka(false);
    }
    document.addEventListener("mousedown", onTutup);
    return () => document.removeEventListener("mousedown", onTutup);
  }, [terbuka]);

  useEffect(() => {
    if (terbuka) inputRef.current?.focus();
  }, [terbuka]);

  function pilih(o: OpsiCari) {
    if (o.nilai) {
      setPilihan((p) => ({ ...p, [o.nilai]: o }));
    }
    onChange(o.nilai, o.nilai ? o : undefined);
    setTerbuka(false);
    setCari("");
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSorot((s) => Math.min(s + 1, daftarTampil.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSorot((s) => Math.max(s - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const pilihOpsi = daftarTampil[sorot];
      if (pilihOpsi) pilih(pilihOpsi);
    } else if (e.key === "Escape") {
      setTerbuka(false);
      setCari("");
    }
  }

  return (
    <div ref={kotakRef} className="relative">
      <span id={idLab} className="block text-sm font-medium text-gray-800">
        {label}
      </span>
      <button
        id={id}
        type="button"
        role="combobox"
        aria-expanded={terbuka}
        aria-haspopup="listbox"
        aria-controls={idDaftar}
        aria-labelledby={idLab}
        disabled={disabled}
        onClick={() => {
          setTerbuka((t) => !t);
          setCari("");
          setSorot(0);
        }}
        className="mt-1 flex w-full items-center justify-between gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-left text-base disabled:opacity-50"
      >
        <span className={terpilih ? "truncate text-gray-900" : "truncate text-gray-500"}>
          {terpilih?.label ?? opsiKosong ?? "— pilih —"}
        </span>
        <span aria-hidden className="shrink-0 text-gray-400">
          ▾
        </span>
      </button>

      {terbuka &&
        createPortal(
          <div
            className="fixed rounded-lg border border-gray-200 bg-white shadow-lg"
            style={{
              zIndex: LAPISAN_DROPDOWN,
              top: posisi.top,
              left: posisi.left,
              width: posisi.lebar,
              transform: posisi.keAtas ? "translateY(-100%)" : undefined,
            }}
            ref={panelRef}
          >
            <div className="border-b border-gray-100 p-2">
              <input
                ref={inputRef}
                type="search"
                value={cari}
                onChange={(e) => {
                  setCari(e.target.value);
                  setSorot(0);
                }}
                onKeyDown={onKeyDown}
                placeholder={placeholderCari}
                aria-label={`Cari ${label}`}
                aria-controls={idDaftar}
                className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
              />
            </div>
            <ul id={idDaftar} role="listbox" aria-labelledby={idLab} className="max-h-64 overflow-y-auto py-1">
              {opsiKosong && !cari && (
                <li role="option" aria-selected={nilai === ""}>
                  <button
                    type="button"
                    onClick={() => pilih({ nilai: "", label: opsiKosong })}
                    className={
                      "block w-full px-3 py-1.5 text-left text-sm " +
                      (nilai === "" ? "bg-kusafa-light font-medium text-kusafa" : "text-gray-600 hover:bg-gray-50")
                    }
                  >
                    {opsiKosong}
                  </button>
                </li>
              )}
              {memuatServer && (
                <li className="px-3 py-2 text-sm text-gray-500">Mencari...</li>
              )}
              {!memuatServer && daftarTampil.length === 0 && (
                <li className="px-3 py-2 text-sm text-gray-500">
                  {cari || !diServer
                    ? "Tidak ada yang cocok. Coba nomor atau sebagian nama."
                    : "Tidak ada pilihan."}
                </li>
              )}
              {daftarTampil.map((o, i) => (
                <li key={o.nilai} role="option" aria-selected={o.nilai === nilai}>
                  <button
                    type="button"
                    onClick={() => pilih(o)}
                    onMouseEnter={() => setSorot(i)}
                    className={
                      "block w-full px-3 py-1.5 text-left text-sm " +
                      (o.nilai === nilai
                        ? "bg-kusafa-light font-medium text-kusafa"
                        : i === sorot
                          ? "bg-gray-100 text-gray-900"
                          : "text-gray-800 hover:bg-gray-50")
                    }
                  >
                    {o.label}
                  </button>
                </li>
              ))}
            </ul>
            {jumlahCocok > daftarTampil.length && (
              <p className="border-t border-gray-100 px-3 py-1.5 text-xs text-gray-600">
                Menampilkan {daftarTampil.length} dari {jumlahCocok}. Ketik nomor atau nama untuk mempersempit.
              </p>
            )}
          </div>,
          document.body,
        )}

      {keterangan && <p className="mt-1 truncate text-xs text-gray-600">{keterangan}</p>}
    </div>
  );
}
