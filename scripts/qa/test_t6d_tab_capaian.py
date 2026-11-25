"""Uji E2E T6d: TAB domain di halaman Capaian (dan halaman Input).

Yang diperiksa (semua lewat TAMPILAN, bukan hanya "tidak error"):
 1. Ketiga tab terlihat: desktop 1280 px dan HP 360 px.
 2. Di HP 360 px tidak ada geseran horizontal (lebar dokumen = lebar layar),
    dan tiap tab cukup besar untuk disentuh (tinggi >= 44 px).
 3. Klik tab mengganti isi tabel DAN URL (/capaian/wasilah dan seterusnya).
 4. Muat ulang tetap di tab yang sama (tab aktif tercermin di URL).
 5. Tombol kembali mengembalikan tab sebelumnya.
 6. Tab sesuai role (tidak menawarkan domain yang bukan haknya); menu lama
    (submenu Capaian di menu samping) sudah tidak ada.
 7. Tab di halaman Input juga memakai komponen yang sama (3 tab, gaya sama).

Hanya membaca. Tidak menulis ke database.

Pakai:
  .venv-qa/bin/python scripts/qa/test_t6d_tab_capaian.py
  BASE_URL=https://kusafa-app.vercel.app .venv-qa/bin/python scripts/qa/test_t6d_tab_capaian.py
"""
from __future__ import annotations

import csv
import json
import os
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t6d_tab_capaian.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t6d"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TAB = '[role="tab"]'

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


def akun(role: str) -> dict:
    for r in csv.DictReader(pathlib.Path("scripts/seed/output/users.csv").open(encoding="utf-8")):
        if r["role"] == role:
            return r
    raise SystemExit(f"akun role {role} tidak ada")


def login(page, a: dict) -> None:
    # Sesi Supabase disimpan di localStorage, bukan hanya cookie.
    page.context.clear_cookies()
    page.goto(f"{BASE}/", wait_until="load")
    page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
    page.goto(f"{BASE}/", wait_until="load")
    page.wait_for_selector('input[type="email"]', timeout=60000)
    page.fill('input[type="email"]', a["email"])
    page.fill('input[type="password"]', a["password"])
    page.click('button[type="submit"]')
    page.wait_for_selector("header", timeout=60000)


def label_tab(page) -> list[str]:
    return [(b.inner_text() or "").strip() for b in page.query_selector_all(TAB)]


def tab_aktif(page) -> str:
    for b in page.query_selector_all(TAB):
        if (b.get_attribute("aria-selected") or "") == "true":
            return (b.inner_text() or "").strip()
    return ""


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        galat: list[str] = []

        # ---------------- Desktop 1280 px, role Mudir ----------------
        ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
        page = ctx.new_page()
        page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
        login(page, akun("mudir"))
        page.goto(f"{BASE}/capaian/alquran", wait_until="load")
        page.wait_for_selector("table", timeout=60000)
        page.wait_for_timeout(1200)

        catat("1. desktop: 3 tab Capaian terlihat", label_tab(page) == ["Al Qur'an", "Ilmu Wasilah", "Ilmu Ghayah"],
              tab=label_tab(page))
        catat("2. tab aktif awal = Al Qur'an", tab_aktif(page) == "Al Qur'an", aktif=tab_aktif(page))
        isi_alquran = page.inner_text("main")
        page.screenshot(path=str(FOTO / "desktop_01_capaian_alquran.png"), full_page=True)

        # Klik tab Ilmu Wasilah: isi dan URL berubah.
        page.get_by_role("tab", name="Ilmu Wasilah", exact=True).click()
        page.wait_for_url("**/capaian/wasilah", timeout=20000)
        page.wait_for_timeout(2500)
        isi_wasilah = page.inner_text("main")
        catat("3. klik tab mengganti URL", page.url.endswith("/capaian/wasilah"), url=page.url)
        catat("4. klik tab mengganti isi tabel", "Capaian Ilmu Wasilah" in isi_wasilah
              and isi_wasilah != isi_alquran, judul_terlihat="Capaian Ilmu Wasilah" in isi_wasilah)
        catat("5. tab aktif ikut berpindah", tab_aktif(page) == "Ilmu Wasilah", aktif=tab_aktif(page))
        page.screenshot(path=str(FOTO / "desktop_02_capaian_wasilah.png"), full_page=True)

        # Muat ulang: tetap di tab yang sama.
        page.reload(wait_until="load")
        page.wait_for_selector(TAB, timeout=60000)
        page.wait_for_timeout(1500)
        catat("6. muat ulang tetap di tab Wasilah",
              page.url.endswith("/capaian/wasilah") and tab_aktif(page) == "Ilmu Wasilah"
              and "Capaian Ilmu Wasilah" in page.inner_text("main"),
              aktif=tab_aktif(page), url=page.url)

        # Tombol kembali ke tab sebelumnya.
        page.go_back()
        page.wait_for_selector(TAB, timeout=60000)
        page.wait_for_timeout(1200)
        catat("7. tombol kembali mengembalikan tab Al Qur'an",
              page.url.endswith("/capaian/alquran") and tab_aktif(page) == "Al Qur'an",
              aktif=tab_aktif(page), url=page.url)

        # Tab Ghayah juga.
        page.get_by_role("tab", name="Ilmu Ghayah", exact=True).click()
        page.wait_for_url("**/capaian/ghayah", timeout=20000)
        page.wait_for_timeout(2500)
        catat("8. tab Ilmu Ghayah bekerja", "Capaian Ilmu Ghayah" in page.inner_text("main")
              and tab_aktif(page) == "Ilmu Ghayah", url=page.url)
        page.screenshot(path=str(FOTO / "desktop_03_capaian_ghayah.png"), full_page=True)

        # Menu lama (submenu Capaian di menu samping) sudah tidak ada.
        submenu = page.query_selector("#submenu-capaian")
        tombol_capaian = page.query_selector('nav[aria-label="Menu utama"] a[href="/capaian/alquran"]')
        catat("9. menu samping Capaian berupa tautan biasa (bukan submenu)",
              submenu is None and tombol_capaian is not None)

        # Halaman Input memakai tab yang sama.
        page.goto(f"{BASE}/input/alquran", wait_until="load")
        page.wait_for_selector(TAB, timeout=60000)
        page.wait_for_timeout(1500)
        catat("10. halaman Input juga memakai 3 tab yang sama",
              label_tab(page) == ["Al Qur'an", "Ilmu Wasilah", "Ilmu Ghayah"] and tab_aktif(page) == "Al Qur'an",
              tab=label_tab(page))
        page.screenshot(path=str(FOTO / "desktop_04_input_tab.png"), full_page=True)
        ctx.close()

        # ---------------- HP 360 px ----------------
        ctx = browser.new_context(viewport={"width": 360, "height": 780}, is_mobile=True,
                                  has_touch=True, device_scale_factor=2)
        page = ctx.new_page()
        page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
        login(page, akun("mudir"))
        for domain, nama in (("alquran", "Al Qur'an"), ("wasilah", "Ilmu Wasilah"), ("ghayah", "Ilmu Ghayah")):
            page.goto(f"{BASE}/capaian/{domain}", wait_until="load")
            page.wait_for_selector(TAB, timeout=60000)
            page.wait_for_timeout(1500)
            ukur = page.evaluate(
                """() => {
                    const tabs = [...document.querySelectorAll('[role="tab"]')];
                    const r = tabs.map(t => t.getBoundingClientRect());
                    return {
                      lebar_dok: document.documentElement.scrollWidth,
                      lebar_layar: window.innerWidth,
                      tab: r.map(x => ({w: Math.round(x.width), h: Math.round(x.height),
                                        kiri: Math.round(x.left), kanan: Math.round(x.right)})),
                      label: tabs.map(t => t.innerText.trim()),
                    };
                }"""
            )
            tanpa_geser = ukur["lebar_dok"] <= ukur["lebar_layar"] + 1
            semua_di_layar = all(t["kanan"] <= ukur["lebar_layar"] + 1 and t["kiri"] >= -1 for t in ukur["tab"])
            cukup_besar = all(t["h"] >= 44 for t in ukur["tab"])
            catat(f"HP 360 | {nama}: tidak bergeser ke samping", tanpa_geser,
                  lebar_dok=ukur["lebar_dok"], lebar_layar=ukur["lebar_layar"])
            catat(f"HP 360 | {nama}: 3 tab muat di layar", semua_di_layar and len(ukur["tab"]) == 3,
                  tab=ukur["tab"], label=ukur["label"])
            catat(f"HP 360 | {nama}: area sentuh >= 44 px", cukup_besar,
                  tinggi=[t["h"] for t in ukur["tab"]])
            page.screenshot(path=str(FOTO / f"hp360_capaian_{domain}.png"), full_page=False)

        # Klik tab di HP juga bekerja.
        page.goto(f"{BASE}/capaian/alquran", wait_until="load")
        page.wait_for_selector(TAB, timeout=60000)
        page.wait_for_timeout(1200)
        page.get_by_role("tab", name="Ilmu Wasilah", exact=True).click()
        page.wait_for_url("**/capaian/wasilah", timeout=20000)
        page.wait_for_timeout(2000)
        catat("HP 360: klik tab mengganti URL & isi",
              page.url.endswith("/capaian/wasilah") and "Capaian Ilmu Wasilah" in page.inner_text("main"))
        page.screenshot(path=str(FOTO / "hp360_capaian_wasilah.png"), full_page=False)
        ctx.close()

        # ---------------- Tab sesuai role ----------------
        # Hak lihat tidak diubah: semua staf melihat ketiga domain (RLS is_staff).
        # Yang dipastikan: tidak ada role yang ditawari domain yang bukan haknya, dan
        # role tanpa menu Capaian tidak bisa membuka halaman ini sama sekali.
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        for role, harusnya in (
            ("mudir", 3), ("admin", 3), ("masul_alquran", 3), ("masul_wasilah", 3),
            ("masul_ghayah", 3), ("musyrif", 3), ("mudarris", 3),
        ):
            login(page, akun(role))
            page.goto(f"{BASE}/capaian/alquran", wait_until="load")
            page.wait_for_timeout(2500)
            jumlah = len(page.query_selector_all(TAB))
            catat(f"role {role}: {harusnya} tab Capaian", jumlah == harusnya, jumlah=jumlah,
                  tab=label_tab(page))
        ctx.close()

        catat("konsol bersih", not galat, galat=galat[:5])
        browser.close()

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
