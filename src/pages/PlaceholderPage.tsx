import type { NavItem } from "../lib/roles";

interface Props {
  item: NavItem;
  roleLabel: string;
  children?: React.ReactNode;
}

/**
 * Bingkai halaman berisi menu yang akan diisi pada tugas berikutnya (T3-T10).
 * Ditulis apa adanya supaya Mudir tahu bagian mana yang masih menunggu.
 */
export default function PlaceholderPage({ item, roleLabel, children }: Props) {
  return (
    <div className="rounded-xl bg-white p-6 ring-1 ring-black/5">
      <h1 className="text-xl font-bold text-gray-900">{item.label}</h1>
      <p className="mt-2 text-sm text-gray-700">{item.description}</p>

      <div className="mt-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900 ring-1 ring-amber-200">
        Halaman ini belum diisi. Fitur {item.label.toLowerCase()} dikerjakan pada tugas berikutnya.
      </div>

      <p className="mt-4 text-xs text-gray-500">
        Anda masuk sebagai {roleLabel}. Semua data dijaga oleh aturan akses di database,
        jadi walaupun menu disembunyikan, data tetap tidak bisa dibuka tanpa hak.
      </p>

      {children}
    </div>
  );
}