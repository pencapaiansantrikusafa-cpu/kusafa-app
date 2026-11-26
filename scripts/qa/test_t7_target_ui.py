"""Uji E2E T7 [2/2]: halaman Target (daftar, saringan, aksi, riwayat).

Semua lewat TAMPILAN dan HANYA MEMBACA (tidak menulis ke database).

Yang diperiksa:
  1. Mudir: rute `/target` dialihkan ke `/target/alquran`; ada tab ketiga domain.
  2. Daftar target tampil dari tabel `targets` (ada baris, ada kolom Sasaran/Target/Status).
  3. Klik tab mengganti URL dan judul (`/target/wasilah` -> "Target Ilmu Wasilah").
  4. Muat ulang tetap di tab yang sama.
  5. Riwayat target terbuka dari tombol "Riwayat" dan menampilkan isi.
  6. Saringan status "Diajukan" -> keadaan kosong yang benar (bukan 0 palsu).
  7. Tombol "Ajukan target" membuka form (dropdown, nilai, bulan berlaku) lalu ditutup.
  8. Musyrif (pengampu): hanya halaqah yang diampu, tidak ada tombol Setujui/Tolak,
     ada tombol Ubah; tidak ada pilihan "Semua halaqah".
  9. Masul Al Quran: `/target/wasilah` dialihkan ke `/target/alquran` (satu domain).
 10. HP 360 px: tidak bergeser ke samping; 3 tab muat.
 11. Konsol bersih.

Pakai:
  npm run build
  python3 scripts/qa/serve_dist.py 4173 &
  BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t7_target_ui.py
"""
from __future__ import annotations

import csv
import json
import os
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t7_target_ui.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t7"))
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


def tunggu_tabel(page) -> None:
    page.wait_for_selector("table", timeout=60000)
    page.wait_for_timeout(1200)


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        galat: list[str] = []

        # ---------------- Desktop, role Mudir ----------------
        ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
        page = ctx.new_page()
        page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
        login(page, akun("mudir"))

        page.goto(f"{BASE}/target", wait_until="load")
        page.wait_for_selector(TAB, timeout=60000)
        tunggu_tabel(page)
        catat("1. /target dialihkan ke /target/alquran", page.url.endswith("/target/alquran"), url=page.url)
        catat("2. 3 tab domain terlihat",
              label_tab(page) == ["Al Qur'an", "Ilmu Wasilah", "Ilmu Ghayah"], tab=label_tab(page))
        teks_main = page.inner_text("main")
        catat("3. judul 'Target Al Qur'an' tampil", "Target Al Qur'an" in teks_main)
        catat("4. daftar target punya baris data", len(page.query_selector_all("tbody tr")) > 0,
              baris=len(page.query_selector_all("tbody tr")))
        kepala = page.inner_text("thead").lower()
        for kolom in ("sasaran", "mata pelajaran", "target", "berlaku mulai", "status", "aksi"):
            catat(f"5. kepala kolom '{kolom}' ada", kolom in kepala)
        ada_setuju = page.get_by_role("button", name="Setujui", exact=True).count() > 0
        catat("6. Mudir melihat tombol aksi (Ubah/Riwayat)", ada_setuju or page.get_by_role("button", name="Ubah", exact=True).count() > 0)
        page.screenshot(path=str(FOTO / "desktop_01_target_alquran.png"), full_page=True)

        # Waktu siap halaman: dari buka rute sampai tabel target tampil (< 1,5 detik).
        page.goto(f"{BASE}/target/wasilah", wait_until="commit")
        t0 = time.perf_counter()
        page.wait_for_selector("tbody tr", timeout=60000)
        siap_ms = int((time.perf_counter() - t0) * 1000)
        catat("6b. halaman target siap < 1,5 detik", siap_ms < 1500, ms=siap_ms)
        page.goto(f"{BASE}/target/alquran", wait_until="load")
        tunggu_tabel(page)

        # Notifikasi target di kotak "Data belum lengkap" (halaman Input).
        page.goto(f"{BASE}/input/alquran", wait_until="load")
        page.wait_for_timeout(4000)
        teks_input = page.inner_text("main")
        catat("6c. kotak notifikasi memuat bagian Target Al Qur'an",
              "Target Al Qur'an" in teks_input and "menunggu persetujuan" in teks_input)
        catat("6d. notifikasi menandai target DUMMY dan sasaran tanpa target",
              "target DUMMY" in teks_input and "belum punya target" in teks_input)
        page.screenshot(path=str(FOTO / "desktop_08_notifikasi_target.png"), full_page=True)
        page.goto(f"{BASE}/target/alquran", wait_until="load")
        tunggu_tabel(page)

        # Tab Wasilah: URL + judul berubah.
        page.get_by_role("tab", name="Ilmu Wasilah", exact=True).click()
        page.wait_for_url("**/target/wasilah", timeout=20000)
        tunggu_tabel(page)
        catat("7. klik tab mengganti URL ke /target/wasilah", page.url.endswith("/target/wasilah"))
        catat("8. judul berubah 'Target Ilmu Wasilah'", "Target Ilmu Wasilah" in page.inner_text("main"))
        page.screenshot(path=str(FOTO / "desktop_02_target_wasilah.png"), full_page=True)

        # Muat ulang tetap di tab yang sama.
        page.reload(wait_until="load")
        page.wait_for_selector(TAB, timeout=60000)
        tunggu_tabel(page)
        catat("9. muat ulang tetap di tab Wasilah",
              page.url.endswith("/target/wasilah") and tab_aktif(page) == "Ilmu Wasilah",
              aktif=tab_aktif(page), url=page.url)

        # Riwayat target.
        page.get_by_role("button", name="Riwayat", exact=True).first.click()
        page.wait_for_selector('[aria-labelledby="judul-riwayat-target"]', timeout=20000)
        page.wait_for_timeout(1200)
        teks_dialog = page.inner_text('[aria-labelledby="judul-riwayat-target"]')
        catat("10. dialog riwayat tampil berisi target", "Riwayat target" in teks_dialog
              and ("Disetujui" in teks_dialog or "Berlaku mulai" in teks_dialog),
              cuplikan=teks_dialog[:80])
        page.screenshot(path=str(FOTO / "desktop_03_riwayat.png"), full_page=False)
        page.get_by_role("button", name="Tutup", exact=True).click()
        page.wait_for_timeout(500)

        # Form ajukan target terbuka lalu ditutup (tidak menyimpan apa pun).
        page.get_by_role("button", name="Ajukan target", exact=True).click()
        page.wait_for_selector('[aria-labelledby="judul-form-target"]', timeout=20000)
        teks_form = page.inner_text('[aria-labelledby="judul-form-target"]')
        catat("11. form ajukan target memuat label wajib",
              all(k in teks_form for k in ("Mata pelajaran", "Target", "Bulan", "Tahun Hijriyah")),
              cuplikan=teks_form[:80])
        # Bulan default berasal dari RPC `target_bulan_berjalan` (bukti panggilan RPC bernama berhasil).
        bulan_terpilih = (page.inner_text("#target-bulan-berlaku-bulan") or "").strip()
        tahun_terpilih = (page.inner_text("#target-bulan-berlaku-tahun") or "").strip()
        catat("11b. bulan berjalan terisi otomatis dari database",
              bulan_terpilih not in ("", "— pilih —") and tahun_terpilih not in ("", "— pilih —"),
              bulan=bulan_terpilih, tahun=tahun_terpilih)
        catat("11c. form Ilmu Wasilah: target bulanan, tanpa pilihan santri",
              "Target bulanan" in teks_form and "Santri" not in teks_form)
        page.screenshot(path=str(FOTO / "desktop_04_form_ajukan.png"), full_page=False)
        page.get_by_role("button", name="Batal", exact=True).click()
        page.wait_for_timeout(500)

        # Form ajukan target Al Qur'an: ada santri + pilihan massal, bulan default dari database.
        page.goto(f"{BASE}/target/alquran", wait_until="load")
        tunggu_tabel(page)
        page.get_by_role("button", name="Ajukan target", exact=True).click()
        page.wait_for_selector('[aria-labelledby="judul-form-target"]', timeout=20000)
        teks_alquran = page.inner_text('[aria-labelledby="judul-form-target"]')
        catat("11d. form Al Qur'an: pilih santri + target massal per halaqah",
              "Santri" in teks_alquran and "seluruh anggota halaqah" in teks_alquran
              and "Target harian" in teks_alquran)
        catat("11e. form Al Qur'an: bulan berjalan terisi otomatis",
              (page.inner_text("#target-bulan-berlaku-bulan") or "").strip() not in ("", "— pilih —"),
              bulan=(page.inner_text("#target-bulan-berlaku-bulan") or "").strip())
        page.screenshot(path=str(FOTO / "desktop_07_form_alquran.png"), full_page=False)
        page.get_by_role("button", name="Batal", exact=True).click()
        page.wait_for_timeout(500)

        # Saringan status: "Diajukan" pada data dummy = keadaan kosong yang benar.
        tunggu_tabel(page)
        page.click("#target-filter-status-alquran")
        page.fill('input[aria-label="Cari Status"]', "Diajukan")
        page.wait_for_timeout(400)
        page.get_by_role("option").first.click()
        page.wait_for_timeout(1500)
        teks = page.inner_text("main")
        catat("12. saringan status 'Diajukan' menampilkan keadaan kosong",
              "Belum ada target pada saringan ini" in teks, cuplikan=teks[-120:])
        page.screenshot(path=str(FOTO / "desktop_05_filter_diajukan.png"), full_page=True)
        ctx.close()

        # ---------------- Pengampu (Musyrif) ----------------
        ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
        page = ctx.new_page()
        page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
        login(page, akun("musyrif"))
        page.goto(f"{BASE}/target/alquran", wait_until="load")
        tunggu_tabel(page)
        teks_saringan = page.inner_text("main")
        catat("13. Musyrif dibatasi halaqah amanah (tanpa 'Semua halaqah')",
              "Semua halaqah" not in teks_saringan and "Hanya halaqah yang Anda ampu" in teks_saringan)
        page.goto(f"{BASE}/input/alquran", wait_until="load")
        page.wait_for_timeout(4000)
        catat("13b. pengampu tidak melihat bagian persetujuan target di notifikasi",
              "Buka halaman Target" not in page.inner_text("main"))
        # Kembali ke halaman Target sebelum memeriksa tombolnya.
        page.goto(f"{BASE}/target/alquran", wait_until="load")
        tunggu_tabel(page)
        catat("14. Musyrif tidak melihat tombol Setujui",
              page.get_by_role("button", name="Setujui", exact=True).count() == 0)
        catat("15. Musyrif melihat tombol Ubah",
              page.get_by_role("button", name="Ubah", exact=True).count() > 0)
        page.screenshot(path=str(FOTO / "desktop_06_musyrif.png"), full_page=True)
        ctx.close()

        # ---------------- Masul Al Quran: satu domain saja ----------------
        ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
        page = ctx.new_page()
        page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
        login(page, akun("masul_alquran"))
        page.goto(f"{BASE}/target/wasilah", wait_until="load")
        page.wait_for_timeout(2000)
        catat("16. Masul Al Quran dialihkan dari /target/wasilah ke /target/alquran",
              page.url.endswith("/target/alquran") and "Target Al Qur'an" in page.inner_text("main"),
              url=page.url)
        ctx.close()

        # ---------------- HP 360 px ----------------
        ctx = browser.new_context(viewport={"width": 360, "height": 780}, is_mobile=True,
                                  has_touch=True, device_scale_factor=2)
        page = ctx.new_page()
        page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
        login(page, akun("mudir"))
        for domain, nama in (("alquran", "Al Qur'an"), ("wasilah", "Ilmu Wasilah"), ("ghayah", "Ilmu Ghayah")):
            page.goto(f"{BASE}/target/{domain}", wait_until="load")
            page.wait_for_timeout(1800)
            ukur = page.evaluate(
                """() => {
                    const tabs = [...document.querySelectorAll('[role="tab"]')];
                    const r = tabs.map(t => t.getBoundingClientRect());
                    return {
                      lebar_dok: document.documentElement.scrollWidth,
                      lebar_layar: window.innerWidth,
                      tab: r.map(x => ({w: Math.round(x.width), h: Math.round(x.height)})),
                    };
                }"""
            )
            tanpa_geser = ukur["lebar_dok"] <= ukur["lebar_layar"] + 1
            cukup_besar = all(t["h"] >= 44 for t in ukur["tab"])
            catat(f"HP 360 | {nama}: tidak bergeser ke samping", tanpa_geser,
                  lebar_dok=ukur["lebar_dok"], lebar_layar=ukur["lebar_layar"])
            catat(f"HP 360 | {nama}: 3 tab muat & sentuh >= 44 px",
                  len(ukur["tab"]) == 3 and cukup_besar, tab=ukur["tab"])
            page.screenshot(path=str(FOTO / f"hp360_target_{domain}.png"), full_page=False)
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
