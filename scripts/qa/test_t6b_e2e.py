"""Uji E2E T6b: input Ilmu Wasilah / Ilmu Ghayah dari sisi TAMPILAN.

Celah yang ditutup (pelajaran T5c-3): smoke lama hanya memeriksa halaman termuat.
Uji ini memeriksa TEKS tombol dropdown, isi database, dan tampilan setelah muat ulang.

Langkah:
  a. buka halaman Input Ilmu Wasilah sebagai Mudir
  b. buka dropdown item sebuah mata pelajaran -> pilih hasil pencarian
     -> label pilihan HARUS tampil (bukan "-- belum diisi --")
  c. simpan -> database berisi item yang sama untuk SEMUA anggota halaqah
  d. muat ulang -> label tetap tampil (nilai tersimpan dikenali)
  e. halaman Ilmu Ghayah: hal yang sama
  f. konsol bersih

Data uji dipulihkan: seluruh baris `progress_entries` domain wasilah/ghayah yang
dibuat uji ini dihapus kembali di blok finally, lalu jumlah baris diverifikasi
sama dengan sebelum uji.

Pakai:
  .venv-qa/bin/python scripts/qa/test_t6b_e2e.py
  BASE_URL=https://kusafa-app.vercel.app .venv-qa/bin/python scripts/qa/test_t6b_e2e.py
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
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t6b_e2e.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t6b_e2e"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PLACEHOLDER = "belum diisi"

LULUS = 0
GAGAL: list[str] = []
RINCIAN: list[dict] = []


def catat(nama: str, ok: bool, **info) -> None:
    global LULUS
    RINCIAN.append({"uji": nama, "ok": ok, **info})
    if ok:
        LULUS += 1
    else:
        GAGAL.append(nama)


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


def teks_dropdown_item(page) -> list[str]:
    """Teks tombol dropdown item (yang punya kotak pencarian item)."""
    hasil = []
    for b in page.query_selector_all('[role="combobox"]'):
        bid = b.get_attribute("id") or ""
        if bid.startswith("wasilah-"):
            hasil.append(b.inner_text().split("\n")[0].strip())
    return hasil


def pilih_item(page, indeks: int, kata: str) -> str:
    tombol = [b for b in page.query_selector_all('[role="combobox"]') if (b.get_attribute("id") or "").startswith("wasilah-")]
    tombol[indeks].click()
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



def pilih_target(page, indeks: int, kata: str) -> str:
    """Pilih butir target bulan depan untuk mapel ke-`indeks` (T7c [3/3])."""
    tombol = [b for b in page.query_selector_all('[role="combobox"]') if (b.get_attribute("id") or "").startswith("target-")]
    tombol[indeks].click()
    page.wait_for_selector('input[type="search"]:visible', timeout=20000)
    page.locator('input[type="search"]:visible').first.fill(kata)
    page.wait_for_timeout(1800)
    opsi = page.query_selector_all('[role="option"]')
    if not opsi:
        raise AssertionError(f"pencarian target {kata!r} tidak menghasilkan pilihan")
    label = opsi[0].inner_text().strip()
    opsi[0].click()
    page.wait_for_timeout(500)
    return label


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    mulai = dt.datetime.now(dt.timezone.utc)
    asli = pulihkan_data.rekam(db)

    sebelum = db.execute(
        """select count(*) from public.progress_entries pe join public.subjects s on s.id = pe.subject_id
           where s.domain in ('wasilah','ghayah')"""
    ).fetchone()[0]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1440, "height": 1300})
            galat: list[str] = []
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun("mudir"))

            for domain, halaman in (("wasilah", "Ilmu Wasilah"), ("ghayah", "Ilmu Ghayah")):
                t0 = time.perf_counter()
                page.goto(f"{BASE}/input/{domain}", wait_until="load")
                page.get_by_role("button", name="Simpan capaian & target", exact=True).first.wait_for(timeout=60000)
                siap = time.perf_counter() - t0
                page.wait_for_timeout(1200)

                catat(f"{domain}: halaman siap < 1,5 s", siap < 1.5, detik=round(siap, 2))
                awal = teks_dropdown_item(page)
                catat(
                    f"{domain}: belum ada capaian -> placeholder wajar",
                    all(PLACEHOLDER in t for t in awal) if awal else False,
                    dropdown=awal,
                )
                page.screenshot(path=str(FOTO / f"{domain}_01_awal.png"), full_page=True)

                label = pilih_item(page, 0, "1")
                label_target = pilih_target(page, 0, "1")
                tampil = teks_dropdown_item(page)[0]
                catat(
                    f"{domain}: pilih dari pencarian -> label tampil",
                    tampil == label and PLACEHOLDER not in tampil,
                    dipilih=label,
                    tampil=tampil,
                )
                page.screenshot(path=str(FOTO / f"{domain}_02_dipilih.png"), full_page=True)

                # Simpan.
                page.get_by_role("button", name="Simpan capaian & target", exact=True).first.click()
                # Tunggu bukti database: baris muncul untuk domain ini.
                batas = time.time() + 120
                jml = 0
                while time.time() < batas:
                    jml = db.execute(
                        """select count(*) from public.progress_entries pe
                           join public.subjects s on s.id = pe.subject_id
                           where s.domain = %s""",
                        (domain,),
                    ).fetchone()[0]
                    if jml > 0:
                        break
                    page.wait_for_timeout(500)
                anggota = db.execute(
                    """select count(*) from public.halaqah_members hm
                       join public.halaqahs h on h.id = hm.halaqah_id
                       where h.domain=%s and h.code=%s and hm.left_on is null""",
                    (domain, "Level 1A" if domain == "wasilah" else "Kelompok 1"),
                ).fetchone()[0]
                catat(
                    f"{domain}: simpan menulis ke database untuk semua anggota",
                    jml == anggota and anggota > 0,
                    baris=jml,
                    anggota=anggota,
                )
                # Semua anggota menerima item yang SAMA.
                beda = db.execute(
                    """select count(distinct pe.item_id) from public.progress_entries pe
                       join public.subjects s on s.id = pe.subject_id where s.domain=%s""",
                    (domain,),
                ).fetchone()[0]
                catat(f"{domain}: semua anggota mendapat item yang sama", beda == 1, variasi=beda)
                page.get_by_role("button", name="Simpan capaian & target", exact=True).first.wait_for(state="visible", timeout=120000)
                page.wait_for_timeout(2500)
                page.screenshot(path=str(FOTO / f"{domain}_03_tersimpan.png"), full_page=True)

                # Muat ulang: label tersimpan harus tetap tampil.
                page.reload(wait_until="load")
                page.get_by_role("button", name="Simpan capaian & target", exact=True).first.wait_for(timeout=60000)
                page.wait_for_timeout(2500)
                ulang = teks_dropdown_item(page)
                catat(
                    f"{domain}: setelah muat ulang label tetap tampil",
                    bool(ulang) and ulang[0] == label and PLACEHOLDER not in ulang[0],
                    diharapkan=label,
                    tampil=ulang[0] if ulang else None,
                )
                page.screenshot(path=str(FOTO / f"{domain}_04_muat_ulang.png"), full_page=True)

            catat("konsol bersih", not galat, galat=galat[:5])
            browser.close()
    finally:
        # T6d3: pulihkan PERSIS (bukan hanya menghapus baris baru).
        pulihkan_data.pulihkan(db, asli)
        sama, beda = pulihkan_data.sama_dengan(db, asli)
        sesudah = db.execute(
            """select count(*) from public.progress_entries pe join public.subjects s on s.id = pe.subject_id
               where s.domain in ('wasilah','ghayah')"""
        ).fetchone()[0]
        catat("data uji dipulihkan persis (sidik jari sama)", sama and sesudah == sebelum,
              sebelum=sebelum, sesudah=sesudah, beda=beda)

    hasil = {
        "base": BASE,
        "lulus": LULUS,
        "gagal": GAGAL,
        "ringkasan": f"{LULUS} LULUS, {GAGAL}" if GAGAL else f"{LULUS} LULUS, 0 gagal",
        "rincian": RINCIAN,
    }
    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(json.dumps(hasil, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for r in RINCIAN:
        print(("PASS " if r["ok"] else "GAGAL ") + r["uji"])
    print(hasil["ringkasan"], "| Laporan:", HASIL)
    return 0 if not GAGAL else 1


if __name__ == "__main__":
    sys.exit(main())
