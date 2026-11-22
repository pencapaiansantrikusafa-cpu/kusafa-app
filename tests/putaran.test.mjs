import { test } from "node:test";
import assert from "node:assert/strict";
import { bolehKhatam, putaranUntukSimpan } from "../src/lib/putaran.ts";

/**
 * Uji tertulis aturan putaran Tilawah Al Qur'an (docs/SPEC.md bagian 5.3).
 *
 * Posisi di database: posisi = value + value_offset + (putaran - 1) * cycle_length.
 * Tilawah Al Qur'an siklik dengan cycle_length 604 halaman; value = nomor halaman.
 * Uji ini hanya menghitung posisi dengan rumus yang sama seperti fungsi
 * `public.item_position` agar angka pada laporan bisa diperiksa tanpa database.
 */
const CYCLE = 604;
const posisi = (halaman, putaran) => halaman + (putaran - 1) * CYCLE;

test("khatam: 587 lalu 10 dengan putaran + 1 menghasilkan selisih +27", () => {
  const putaranLalu = 1;
  const putaranKini = putaranUntukSimpan({
    khatam: true,
    putaranBulanLalu: putaranLalu,
    putaranTersimpan: putaranLalu,
  });
  assert.equal(putaranKini, 2, "putaran bulan lalu + 1, bukan angka mutlak");
  assert.equal(posisi(10, putaranKini) - posisi(587, putaranLalu), 27);
});

test("tanpa khatam, pilihan Pengulangan: 587 lalu 10 menghasilkan selisih -577", () => {
  const putaranLalu = 1;
  const putaranKini = putaranUntukSimpan({
    khatam: false,
    putaranBulanLalu: putaranLalu,
    putaranTersimpan: putaranLalu,
  });
  assert.equal(putaranKini, putaranLalu, "pengulangan tidak menaikkan putaran");
  assert.equal(posisi(10, putaranKini) - posisi(587, putaranLalu), -577);
});

test("khatam memakai putaran bulan lalu terbaru, bukan angka tetap 2", () => {
  assert.equal(
    putaranUntukSimpan({ khatam: true, putaranBulanLalu: 3, putaranTersimpan: 3 }),
    4,
  );
});

test("khatam ditolak bila putaran bulan lalu tidak diketahui (jangan menebak)", () => {
  assert.throws(() =>
    putaranUntukSimpan({ khatam: true, putaranBulanLalu: null, putaranTersimpan: null }),
  );
});

test("pilihan khatam hanya untuk buku siklik dan bila putaran bulan lalu ada", () => {
  assert.equal(bolehKhatam(true, { pos: 587, putaran: 1 }), true);
  assert.equal(bolehKhatam(false, { pos: 12, putaran: 1 }), false);
  assert.equal(bolehKhatam(true, null), false);
  assert.equal(bolehKhatam(true, { pos: null, putaran: null }), false);
});

test("baris yang belum pernah diisi memakai putaran 1, bukan putaran bulan lalu", () => {
  assert.equal(
    putaranUntukSimpan({ khatam: false, putaranBulanLalu: null, putaranTersimpan: null }),
    1,
  );
});
