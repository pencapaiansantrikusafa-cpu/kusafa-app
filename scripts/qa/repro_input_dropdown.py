"""Reproduksi bug: label item terpilih jatuh ke "-- belum diisi --" di halaman Input.

Dijalankan terhadap build lokal (default http://localhost:4173) SEBELUM perbaikan.
Mencatat teks tombol dropdown pada tiap langkah + tangkapan layar.

Pakai:
  .venv-qa/bin/python scripts/qa/repro_input_dropdown.py
  BASE_URL=https://kusafa-app.vercel.app .venv-qa/bin/python scripts/qa/repro_input_dropdown.py
"""
from __future__ import annotations

import csv
import json
import os
import pathlib
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/repro_input_dropdown.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/bug_dropdown"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
AKUN = pathlib.Path("scripts/seed/output/users.csv")

PLACEHOLDER = "belum diisi"


def akun(role: str) -> dict:
    for r in csv.DictReader(AKUN.open(encoding="utf-8")):
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


def buka_input(page) -> None:
    page.goto(f"{BASE}/input", wait_until="load")
    page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)


def pilih_bulan(page, nama: str) -> None:
    page.click("#input-bulan")
    page.wait_for_selector('[role="option"]', timeout=20000)
    page.get_by_role("option", name=nama, exact=True).first.click()
    # Tunggu data form selesai dimuat ulang.
    page.wait_for_timeout(2500)


def teks_item(page) -> list[str]:
    return [b.inner_text().split("\n")[0].strip() for b in page.query_selector_all('button[id^="item-"]')]


def ganti_tahun_bila_perlu(page, tahun: str) -> None:
    tombol = page.query_selector("#input-tahun")
    if tombol and tahun not in (tombol.inner_text() or ""):
        tombol.click()
        page.get_by_role("option", name=f"{tahun} H", exact=True).first.click()
        page.wait_for_timeout(500)


def main() -> None:
    FOTO.mkdir(parents=True, exist_ok=True)
    hasil: dict = {"base": BASE, "langkah": [], "roles": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        galat_konsol: list[str] = []
        page.on("console", lambda m: galat_konsol.append(m.text) if m.type == "error" else None)

        # ---------- Skenario Mudir ----------
        login(page, akun("mudir"))
        buka_input(page)
        ganti_tahun_bila_perlu(page, "1447")
        pilih_bulan(page, "Rabiul Awwal")
        page.screenshot(path=str(FOTO / "01_terbuka_bulan_rabiul_awwal.png"), full_page=True)
        awal = teks_item(page)
        hasil["langkah"].append({"langkah": "a. buka santri yang sudah punya nilai", "teks": awal[:6], "gagal": sum(PLACEHOLDER in t for t in awal)})

        # b. pilih item baru dari daftar (tanpa mengetik)
        tombol = page.query_selector_all('button[id^="item-"]')
        tombol[0].click()
        page.wait_for_selector('[role="option"]', timeout=20000)
        page.wait_for_timeout(1800)  # hasil pencarian server (jeda 200 ms + jaringan)
        opsi = [o for o in page.query_selector_all('[role="option"]') if PLACEHOLDER not in (o.inner_text() or "")]
        pilihan_b = opsi[0].inner_text().strip()
        opsi[0].click()
        page.wait_for_timeout(400)
        sesudah_b = teks_item(page)[0]
        page.screenshot(path=str(FOTO / "02_setelah_pilih_dari_daftar.png"), full_page=True)
        hasil["langkah"].append({"langkah": "b. pilih item dari daftar", "dipilih": pilihan_b, "tampil": sesudah_b, "gagal": PLACEHOLDER in sesudah_b})

        # c. pilih lewat kotak ketik (server search)
        tombol = page.query_selector_all('button[id^="item-"]')
        tombol[1].click()
        page.wait_for_selector('input[type="search"]:visible', timeout=20000)
        kotak = page.locator('input[type="search"]:visible').first
        kotak.fill("quraisy")
        page.wait_for_timeout(1500)
        opsi = page.query_selector_all('[role="option"]')
        pilihan_c = opsi[0].inner_text().strip()
        opsi[0].click()
        page.wait_for_timeout(400)
        sesudah_c = teks_item(page)[1]
        page.screenshot(path=str(FOTO / "03_setelah_cari_quraisy.png"), full_page=True)
        hasil["langkah"].append({"langkah": "c. pilih lewat pencarian 'quraisy'", "dipilih": pilihan_c, "tampil": sesudah_c, "gagal": PLACEHOLDER in sesudah_c})

        # d. centang / batalkan "khatam, mulai putaran baru"
        #    Pilih dulu item buku siklik (Tilawah Al Qur'an) lewat pencarian nomor.
        tombol = page.query_selector_all('button[id^="item-"]')
        tombol[0].click()
        page.wait_for_selector('input[type="search"]:visible', timeout=20000)
        page.locator('input[type="search"]:visible').first.fill("351")
        page.wait_for_timeout(1800)
        opsi = page.query_selector_all('[role="option"]')
        siklik_terpilih = opsi[0].inner_text().strip() if opsi else ""
        if opsi:
            opsi[0].click()
        page.wait_for_timeout(500)
        tampil_d = teks_item(page)[0]
        centang = page.query_selector_all('input[type="checkbox"]')
        langkah_d = {
            "langkah": "d. centang / batalkan 'khatam, mulai putaran baru'",
            "item_siklik": siklik_terpilih,
            "tampil": tampil_d,
            "placeholder": PLACEHOLDER in tampil_d,
            "jumlah_checkbox": len(centang),
        }
        if centang:
            centang[0].check()
            page.wait_for_timeout(300)
            page.screenshot(path=str(FOTO / "04_khatam_dicentang.png"), full_page=True)
            dicentang = centang[0].is_checked()
            centang[0].uncheck()
            langkah_d.update({"bisa_dicentang": True, "dicentang": dicentang, "dibatalkan": not centang[0].is_checked()})
        else:
            langkah_d.update({"bisa_dicentang": False, "catatan": "checkbox tidak muncul"})
        hasil["langkah"].append(langkah_d)

        # e. buka ulang setelah simpan: di sini belum menyimpan (menghindari data uji),
        #    cukup muat ulang untuk melihat nilai tersimpan database.
        page.reload(wait_until="load")
        page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
        ganti_tahun_bila_perlu(page, "1447")
        pilih_bulan(page, "Rabiul Awwal")
        ulang = teks_item(page)
        page.screenshot(path=str(FOTO / "05_setelah_muat_ulang.png"), full_page=True)
        hasil["langkah"].append({"langkah": "e. muat ulang halaman (tanpa simpan)", "teks": ulang[:6], "gagal": sum(PLACEHOLDER in t for t in ulang)})

        # ---------- Sapuan semua dropdown untuk tiap role ----------
        for role in ("mudir", "admin", "masul_alquran", "masul_wasilah", "masul_ghayah", "musyrif", "mudarris"):
            try:
                page.context.clear_cookies()
                page.goto(BASE, wait_until="load")
                page.evaluate("localStorage.clear()")
                login(page, akun(role))
                buka_input(page)
                ganti_tahun_bila_perlu(page, "1447")
                pilih_bulan(page, "Rabiul Awwal")
                semua = page.query_selector_all('[role="combobox"]')
                rincian = []
                for b in semua:
                    teks = (b.inner_text() or "").strip().replace("\n", " ")
                    rincian.append({"id": b.get_attribute("id"), "teks": teks, "placeholder": PLACEHOLDER in teks})
                hasil["roles"][role] = {
                    "jumlah_combobox": len(semua),
                    "item_dropdown": len(page.query_selector_all('button[id^="item-"]')),
                    "placeholder_pada_item": sum(1 for r in rincian if r["id"] and r["id"].startswith("item-") and r["placeholder"]),
                    "rincian": rincian[:12],
                }
                page.screenshot(path=str(FOTO / f"role_{role}.png"), full_page=False)
            except Exception as e:  # noqa: BLE001
                hasil["roles"][role] = {"galat": str(e)}

        hasil["galat_konsol"] = galat_konsol[:10]
        browser.close()

    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(json.dumps(hasil, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(hasil, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
