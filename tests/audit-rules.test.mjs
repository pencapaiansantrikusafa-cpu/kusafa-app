import { test } from "node:test";
import assert from "node:assert/strict";

/**
 * Uji otomatis pra-T6 [5/5] item 2: cermin rumus yang didokumentasikan di
 * docs/SPEC.md bagian 5 (perhitungan sebenarnya tetap di database:
 * - posisi = `public.item_position` = value + value_offset + (putaran-1)*cycle_length;
 * - selisih & target bulanan dibaca dari `v_monthly_report` / `v_attendance`;
 * - `month_is_open` adalah fungsi database).
 *
 * Uji di berkas ini MENIRU rumus tertulis agar angka bisa diperiksa cepat tanpa
 * database. Ini pola yang sama dengan tests/putaran.test.mjs. Bukan penghitung
 * di aplikasi.
 */

// ---------------------------------------------------------------- rumus posisi (item_position)
const CYCLE_ALQURAN = 604; // Tilawah Al Qur'an bersiklus 604 halaman

/** posisi = value + value_offset + (putaran - 1) * cycle_length (docs/SPEC §5.1) */
function posisi(item, putaran = 1) {
  return item.value + item.value_offset + (putaran - 1) * (item.cycle_length ?? CYCLE_ALQURAN);
}

// ---------------------------------------------------------------- selisih lintas buku
test("selisih lintas buku memakai posisi kumulatif (value + value_offset)", () => {
  // Item di buku terakhir suatu bidang punya value_offset = jumlah item buku-buku
  // sebelumnya, jadi posisinya berlanjut (bukan reset per buku).
  const bukuAkhir = { value: 3, value_offset: 604 }; // mis. halaman 607
  const bukuAwal = { value: 597, value_offset: 0 }; // halaman 597
  assert.equal(posisi(bukuAwal, 1), 597);
  assert.equal(posisi(bukuAkhir, 1), 607);
  const selisih = posisi(bukuAkhir, 1) - posisi(bukuAwal, 1);
  assert.equal(selisih, 10);
});

test("selisih lintas buku pada putaran berikutnya memperhitungkan cycle_length", () => {
  const bukuAkhir = { value: 3, value_offset: 604 };
  const posPutaran2 = posisi(bukuAkhir, 2); // 607 + 604
  assert.equal(posPutaran2, 1211);
});

// ---------------------------------------------------------------- capaian mundur (pengulangan)
test("capaian mundur karena pengulangan TETAP selisih negatif (bukan 0, bukan galat)", () => {
  const lalu = posisi({ value: 587, value_offset: 0 }, 1);
  const kini = posisi({ value: 10, value_offset: 0 }, 1); // pengulangan, putaran tidak naik
  const selisih = kini - lalu;
  assert.equal(selisih, -577, "docs/SPEC §5.2: selisih negatif ditampilkan apa adanya");
  assert.ok(selisih < 0);
});

// ---------------------------------------------------------------- khatam, mulai putaran baru
test("khatam menaikkan putaran (bulan lalu + 1) sehingga selisih melintasi akhir buku positif", () => {
  // bulan lalu: halaman 587 putaran 1 (akhir buku); kini: halaman 10, putaran berbaru 2
  const lalu = posisi({ value: 587, value_offset: 0 }, 1);
  const kini = posisi({ value: 10, value_offset: 0 }, 2); // + cycle karena putaran baru
  assert.equal(kini - lalu, 27, "contoh di tests/putaran.test.mjs; khatam = putaran+1");
  assert.ok(kini - lalu > 0, "khatam tidak menghasilkan selisih mundur");
});

// ---------------------------------------------------------------- target harian x Hadir
test("target bulanan = target harian x Hadir (boleh pecahan)", () => {
  const harian = 2; // halaman/hari
  const hadir = 19;
  const targetBulanan = harian * hadir;
  assert.equal(targetBulanan, 38);

  const harianPecahan = 0.5;
  assert.equal(harianPecahan * hadir, 9.5, "target bulanan boleh pecahan");
});

// ---------------------------------------------------------------- bulan terkunci (month_is_open)
/** Cermin public.month_is_open: bulan 0 (Data Awal) dan bulan terkunci = tutup. */
function monthIsOpen(monthNo, locked) {
  if (!Number.isInteger(monthNo) || monthNo < 0) return false;
  if (monthNo === 0) return false; // Data Awal bukan bulan input staf
  return !locked;
}

test("bulan 0 (Data Awal) tidak bisa diinput staf (month_is_open=false)", () => {
  assert.equal(monthIsOpen(0, false), false);
});

test("bulan efektif terbuka bila tidak dikunci, tertutup bila dikunci", () => {
  assert.equal(monthIsOpen(1, false), true, "Syawwal belum dikunci -> terbuka");
  assert.equal(monthIsOpen(6, true), false, "bulan dikunci -> tutup untuk staf");
  assert.equal(monthIsOpen(12, false), true, "Ramadhan belum dikunci -> terbuka");
});

test("hanya Admin/Mudir yang boleh menulis bulan terkunci (is_full_access)", () => {
  const penulisanDitolak = (role, monthNo, locked) => {
    // Staf biasa dibatasi month_is_open; Admin/Mudir tidak (full access).
    const isFullAccess = role === "mudir" || role === "admin";
    return !isFullAccess && !monthIsOpen(monthNo, locked);
  };
  assert.equal(penulisanDitolak("musyrif", 6, true), true, "Musyrif/ah tertahan pada bulan terkunci");
  assert.equal(penulisanDitolak("masul_alquran", 6, true), true, "Masul tertahan pada bulan terkunci");
  assert.equal(penulisanDitolak("admin", 6, true), false, "Admin dilewati per aturan is_full_access");
  assert.equal(penulisanDitolak("mudir", 6, true), false, "Mudir dilewati per aturan is_full_access");
});