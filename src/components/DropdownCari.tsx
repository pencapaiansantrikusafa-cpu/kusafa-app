import { useEffect, useId, useMemo, useRef, useState } from "react";

export interface OpsiCari {
  nilai: string;
  label: string;
  /** Teks tambahan untuk pencocokan (mis. nama pengampu), tidak wajib ditampilkan. */
  cariJuga?: string;
}

interface Props {
  /** id elemen tombol; label memakai `${id}-label`. */
  id: string;
  label: string;
  opsi: OpsiCari[];
  nilai: string;
  onChange: (nilai: string) => void;
  /** Teks pilihan kosong (mis. "— belum diisi —"). Bila diisi, muncul sebagai pilihan pertama. */
  opsiKosong?: string;
  keterangan?: string;
  disabled?: boolean;
  /** Jumlah baris yang ditampilkan sekaligus. */
  batasTampil?: number;
  placeholderCari?: string;
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
}: Props) {
  const [terbuka, setTerbuka] = useState(false);
  const [cari, setCari] = useState("");
  const [sorot, setSorot] = useState(0);
  const kotakRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const idLab = `${id}-label`;
  const idDaftar = useId();

  const terpilih = opsi.find((o) => o.nilai === nilai);

  const tersaring = useMemo(() => {
    const k = cari.trim().toLowerCase();
    const dasar = k
      ? opsi.filter((o) => `${o.label} ${o.cariJuga ?? ""}`.toLowerCase().includes(k))
      : opsi;
    return dasar.slice(0, batasTampil);
  }, [opsi, cari, batasTampil]);

  // Tutup bila mengetuk di luar.
  useEffect(() => {
    if (!terbuka) return;
    function onTutup(e: MouseEvent) {
      if (kotakRef.current && !kotakRef.current.contains(e.target as Node)) setTerbuka(false);
    }
    document.addEventListener("mousedown", onTutup);
    return () => document.removeEventListener("mousedown", onTutup);
  }, [terbuka]);

  useEffect(() => {
    if (terbuka) inputRef.current?.focus();
  }, [terbuka]);

  function pilih(n: string) {
    onChange(n);
    setTerbuka(false);
    setCari("");
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSorot((s) => Math.min(s + 1, tersaring.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSorot((s) => Math.max(s - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const pilihOpsi = tersaring[sorot];
      if (pilihOpsi) pilih(pilihOpsi.nilai);
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

      {terbuka && (
        <div className="absolute z-30 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg">
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
                  onClick={() => pilih("")}
                  className={
                    "block w-full px-3 py-1.5 text-left text-sm " +
                    (nilai === "" ? "bg-kusafa-light font-medium text-kusafa" : "text-gray-600 hover:bg-gray-50")
                  }
                >
                  {opsiKosong}
                </button>
              </li>
            )}
            {!cari && tersaring.length === 0 && (
              <li className="px-3 py-2 text-sm text-gray-500">Tidak ada pilihan yang cocok.</li>
            )}
            {tersaring.map((o, i) => (
              <li key={o.nilai} role="option" aria-selected={o.nilai === nilai}>
                <button
                  type="button"
                  onClick={() => pilih(o.nilai)}
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
            {!cari && opsi.length > tersaring.length && (
              <li className="px-3 py-1.5 text-xs text-gray-500">
                Menampilkan {tersaring.length} dari {opsi.length}. Ketik untuk mempersempit.
              </li>
            )}
          </ul>
        </div>
      )}

      {keterangan && <p className="mt-1 truncate text-xs text-gray-600">{keterangan}</p>}
    </div>
  );
}
