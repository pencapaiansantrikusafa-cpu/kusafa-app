"""Uji E2E halaman Input: label item terpilih HARUS tampil (bukan "-- belum diisi --").

Celah smoke lama: hanya memeriksa halaman termuat & simpan berhasil, tidak memeriksa
teks tombol dropdown setelah memilih. Uji ini menutup celah itu:

  a. buka santri yang sudah punya nilai  -> label tampil
  b. pilih item dari daftar                -> label tampil
  c. pilih item lewat pencarian ("quraisy")-> label tampil
  d. pilih buku siklik                     -> centang "khatam" muncul, bisa dicentang/dibatalkan
  e. simpan -> muat ulang                  -> label pilihan baru tetap tampil; isi database cocok

Data uji dipulihkan: baris progress_entries yang diubah dikembalikan ke nilai semula
(item_id, putaran, entered_by, entered_at) di blok finally.

Pakai:
  .venv-qa/bin/python scripts/qa/test_input_dropdown_e2e.py
  BASE_URL=https://kusafa-app.vercel.app .venv-qa/bin/python scripts/qa/test_input_dropdown_e2e.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import pathlib
import sys
import time

import psycopg
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pulihkan_data  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pulihkan_data  # noqa: E402

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/e2e_input_dropdown.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/bug_dropdown"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PLACEHOLDER = "belum diisi"
BULAN = "Rabiul Awwal"


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in pathlib.Path(".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def akun(role: str) -> dict:
    for r in csv.DictReader(pathlib.Path("scripts/seed/output/users.csv").open(encoding="utf-8")):
        if r["role"] == role:
            return r
    raise SystemExit(f"akun role {role} tidak ada")


def login(page, a: dict) -> None:
    page.goto(f"{BASE}/", wait_until="load")
    page.wait_for_selector('input[type="email"]', timeout=60000)
    page.fill('input[type="email"]', a["email"])
    page.fill('input[type="password"]', a["password"])
    page.click('button[type="submit"]')
    page.wait_for_selector("header", timeout=60000)


def buka_input_bulan(page) -> None:
    page.goto(f"{BASE}/input", wait_until="load")
    page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
    page.click("#input-bulan")
    page.wait_for_selector('[role="option"]', timeout=20000)
    page.get_by_role("option", name=BULAN, exact=True).first.click()
    page.wait_for_timeout(2500)


def teks_item(page) -> list[str]:
    return [b.inner_text().split("\n")[0].strip() for b in page.query_selector_all('button[id^="item-"]')]


def pilih_lewat_cari(page, indeks: int, kata: str) -> str:
    page.query_selector_all('button[id^="item-"]')[indeks].click()
    page.wait_for_selector('input[type="search"]:visible', timeout=20000)
    page.locator('input[type="search"]:visible').first.fill(kata)
    page.wait_for_timeout(1800)
    opsi = page.query_selector_all('[role="option"]')
    if not opsi:
        raise AssertionError(f"pencarian {kata!r} tidak menghasilkan pilihan")
    label = opsi[0].inner_text().strip()
    opsi[0].click()
    page.wait_for_timeout(500)
    return label


def main() -> int:
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    hasil: dict = {"base": BASE, "langkah": [], "lulus": 0, "gagal": []}
    mulai = dt.datetime.now(dt.timezone.utc)
    asli_semua = pulihkan_data.rekam(db)

    # Baris acuan: santri pertama (urut nama) di HLQ-PA-1, bulan 6, bidang Tilawah.
    kode_hal, bulan_no = "HLQ-PA-1", 6
    subjek_tilawah = db.execute("select id from public.subjects where name='Tilawah'").fetchone()[0]
    asal = db.execute(
        """select pe.id, pe.student_id, pe.item_id, pe.putaran, pe.entered_by, pe.entered_at
           from public.progress_entries pe
           join public.halaqahs h on h.id = pe.halaqah_id
           join public.hijri_months m on m.id = pe.month_id
           join public.students s on s.id = pe.student_id
           where h.code=%s and m.month_no=%s and pe.subject_id=%s
           order by s.full_name limit 1""",
        (kode_hal, bulan_no, subjek_tilawah),
    ).fetchone()
    if not asal:
        raise SystemExit("Data acuan tidak ditemukan (HLQ-PA-1 bulan 6 Tilawah).")
    jml_awal = db.execute("select count(*) from public.progress_entries").fetchone()[0]

    def catat(nama: str, ok: bool, **info) -> None:
        hasil["langkah"].append({"langkah": nama, "ok": ok, **info})
        if ok:
            hasil["lulus"] += 1
        else:
            hasil["gagal"].append(nama)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            galat_konsol: list[str] = []
            page.on("console", lambda m: galat_konsol.append(m.text) if m.type == "error" else None)
            login(page, akun("mudir"))
            buka_input_bulan(page)

            # a. nilai tersimpan tampil
            awal = teks_item(page)
            catat("a. nilai tersimpan tampil saat dibuka", all(PLACEHOLDER not in t for t in awal), teks=awal[:3])
            page.screenshot(path=str(FOTO / "e2e_01_terbuka.png"), full_page=True)

            # a2. "Bulan lalu" harus tampil SEJAK AWAL, walau item bulan ini belum dipilih.
            #     Dipakai bulan Jumadal Akhir: belum ada capaian, bulan sebelumnya terisi.
            page.click("#input-bulan")
            page.wait_for_selector('[role="option"]', timeout=20000)
            page.get_by_role("option", name="Jumadal Akhir", exact=True).first.click()
            page.wait_for_timeout(3000)
            isi = page.inner_text("main")
            kosong = [
                b for b in page.query_selector_all('button[id^="item-"]')
                if PLACEHOLDER in b.inner_text()
            ]
            baris_lalu = [l for l in isi.split("\n") if "Bulan lalu" in l]
            catat(
                "a2. 'Bulan lalu' tampil sejak awal (dropdown belum dipilih)",
                bool(kosong) and len(baris_lalu) >= len(kosong)
                and not all("belum diisi" in l for l in baris_lalu),
                dropdown_kosong=len(kosong),
                baris_bulan_lalu=[l.strip()[:70] for l in baris_lalu],
            )
            page.screenshot(path=str(FOTO / "e2e_00_bulan_lalu_sejak_awal.png"), full_page=True)

            # Kembali ke bulan uji semula untuk langkah berikutnya.
            page.click("#input-bulan")
            page.wait_for_selector('[role="option"]', timeout=20000)
            page.get_by_role("option", name=BULAN, exact=True).first.click()
            page.wait_for_timeout(2800)

            # b. pilih dari daftar
            page.query_selector_all('button[id^="item-"]')[0].click()
            page.wait_for_selector('[role="option"]', timeout=20000)
            page.wait_for_timeout(1800)
            opsi = [o for o in page.query_selector_all('[role="option"]') if PLACEHOLDER not in (o.inner_text() or "")]
            label_b = opsi[0].inner_text().strip()
            opsi[0].click()
            page.wait_for_timeout(400)
            tampil_b = teks_item(page)[0]
            catat("b. pilih dari daftar -> label tampil", tampil_b == label_b, dipilih=label_b, tampil=tampil_b)

            # d. buku siklik: centang khatam muncul dan bisa dibatalkan
            label_d = pilih_lewat_cari(page, 0, "351")
            centang = page.query_selector_all('input[type="checkbox"]')
            ok_d = len(centang) == 1
            if ok_d:
                centang[0].check()
                ok_d = centang[0].is_checked()
                centang[0].uncheck()
                ok_d = ok_d and not centang[0].is_checked()
            catat("d. centang/batalkan 'khatam' pada buku siklik", ok_d, item=label_d, jumlah_checkbox=len(centang))
            page.screenshot(path=str(FOTO / "e2e_02_khatam.png"), full_page=True)

            # c. pilih lewat pencarian (Tahfidz), lalu simpan: yang disimpan = Tilawah (indeks 0)
            label_c = pilih_lewat_cari(page, 1, "quraisy")
            tampil_c = teks_item(page)[1]
            catat("c. pilih lewat pencarian 'quraisy' -> label tampil", tampil_c == label_c, dipilih=label_c, tampil=tampil_c)

            # Kembalikan form ke isi database dulu (pilihan b/c/d tidak disimpan),
            # supaya saat menyimpan hanya SATU baris (Tilawah santri pertama) yang berubah.
            page.reload(wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.click("#input-bulan")
            page.wait_for_selector('[role="option"]', timeout=20000)
            page.get_by_role("option", name=BULAN, exact=True).first.click()
            page.wait_for_timeout(2500)

            # c2. pilih Tilawah lewat pencarian, lalu simpan.
            label_simpan = pilih_lewat_cari(page, 0, "351")
            tampil_simpan = teks_item(page)[0]
            catat("c2. pilih Tilawah lewat pencarian -> label tampil", tampil_simpan == label_simpan, dipilih=label_simpan, tampil=tampil_simpan)
            # Id item tujuan (untuk memastikan yang tersimpan benar-benar item ini).
            mentah = label_simpan.split(" · ", 1)[-1]
            target = db.execute(
                """select ci.id from public.curriculum_items ci
                   join public.books b on b.id = ci.book_id
                   where b.subject_id=%s and ci.label=%s""",
                (subjek_tilawah, mentah),
            ).fetchone()
            if not target or target[0] == asal[2]:
                raise AssertionError("Item uji harus berbeda dari nilai semula.")
            target_id = target[0]

            # e. simpan
            page.get_by_role("button", name="Simpan", exact=True).first.click()
            page.wait_for_timeout(1500)
            # Bila capaian lebih kecil dari bulan lalu, form meminta konfirmasi lebih dulu.
            if page.get_by_role("dialog").count():
                page.get_by_role("button", name="Pengulangan", exact=True).first.click()
                page.get_by_role("button", name="Simpan dengan pilihan ini", exact=True).click()
            # Pesan "Data tersimpan." hilang saat form dimuat ulang, jadi tunggu lewat
            # bukti database: baris acuan berubah dari item_id semula.
            batas = time.time() + 240
            kini = None
            while time.time() < batas:
                kini = db.execute("select item_id from public.progress_entries where id=%s", (asal[0],)).fetchone()
                if kini and kini[0] == target_id:
                    break
                page.wait_for_timeout(500)
            catat("e0. penyimpanan menulis item yang dipilih ke database", bool(kini) and kini[0] == target_id,
                  diharapkan=str(target_id), tersimpan=str(kini[0]) if kini else None)
            # Pastikan tombol simpan sudah selesai (bukan masih berjalan) sebelum pemulihan.
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(state="visible", timeout=120000)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(FOTO / "e2e_03_tersimpan.png"), full_page=True)

            # Isi database harus sama dengan yang dipilih.
            baris = db.execute(
                """select s.name || ' · ' || ci.label, pe.item_id
                   from public.progress_entries pe
                   join public.subjects s on s.id = pe.subject_id
                   join public.curriculum_items ci on ci.id = pe.item_id
                   where pe.id=%s""",
                (asal[0],),
            ).fetchone()
            catat("e1. database berisi item yang dipilih", baris is not None and baris[0] == label_simpan,
                  dipilih=label_simpan, tersimpan=baris[0] if baris else None)

            # e. muat ulang -> label tetap tampil
            page.reload(wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.click("#input-bulan")
            page.wait_for_selector('[role="option"]', timeout=20000)
            page.get_by_role("option", name=BULAN, exact=True).first.click()
            page.wait_for_timeout(2500)
            ulang = teks_item(page)
            catat("e2. setelah simpan + muat ulang label tetap tampil", ulang[0] == label_simpan and PLACEHOLDER not in ulang[0],
                  diharapkan=label_simpan, tampil=ulang[0])
            page.screenshot(path=str(FOTO / "e2e_04_setelah_muat_ulang.png"), full_page=True)

            catat("konsol bersih", not galat_konsol, galat=galat_konsol[:5])
            browser.close()
    finally:
        # T6d3: pulihkan PERSIS seluruh tiga tabel uji (bukan hanya satu baris).
        # Sebelumnya baris `delete ... where entered_at >= mulai` menghapus 20 baris seed
        # yang disentuh app saat uji (jejaknya ikut bergeser) - lihat STATUS T6d3.
        pulihkan_data.pulihkan(db, asli_semua)
        sama, beda = pulihkan_data.sama_dengan(db, asli_semua)
        jml_akhir = db.execute("select count(*) from public.progress_entries").fetchone()[0]
        hasil["pemulihan"] = {"jumlah_awal": jml_awal, "jumlah_akhir": jml_akhir,
                              "cocok": sama and jml_akhir == jml_awal, "beda": beda}

    hasil["ringkasan"] = f"{hasil['lulus']} LULUS, {hasil['gagal']}"
    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(json.dumps(hasil, ensure_ascii=False, indent=2), encoding="utf-8")
    for l in hasil["langkah"]:
        print(("PASS " if l["ok"] else "GAGAL ") + l["langkah"])
    print(hasil["ringkasan"])
    print("Pemulihan data:", hasil["pemulihan"])
    print("Laporan:", HASIL)
    return 0 if not hasil["gagal"] and hasil["pemulihan"].get("cocok") else 1


if __name__ == "__main__":
    sys.exit(main())
