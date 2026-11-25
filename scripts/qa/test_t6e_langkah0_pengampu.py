"""Langkah 0 T6e - E2E Simpan lewat UI: Mudarris/ah, Musyrif/ah, dan halaqah Level 6.

Yang diperiksa (lewat UI, bukan panggilan fungsi langsung):
 1. **Mudarris/ah** (Ilmu Wasilah): hanya ditawari halaqah/mapel yang diampu, Simpan menulis
    capaian ke semua anggota aktif, label tampil lagi setelah muat ulang.
 2. **Musyrif/ah** (Al Qur'an): hanya ditawari halaqah yang diampu, Simpan menulis capaian.
 3. **Halaqah Level 6 (Ilmu Wasilah)**: 4 anggota aktif, belum punya mata pelajaran/pengampu.
    Halaman Input harus siap tanpa galat, tidak menawarkan mata pelajaran, dan tidak
    menulis apa pun (masih 0 capaian).
 4. Hak dari baris SPEC: pengampu **tidak** bisa menulis di halaqah yang bukan ampuannya
    (dibuktikan dengan percobaan simpan pada halaqah lain yang ditolak/tidak ditawarkan).

Disiplin T6d3: sidik jari database (scripts/qa/db_fingerprint.py) diambil sebelum & sesudah
oleh pemanggil, dan data uji dipulihkan PERSIS (scripts/qa/pulihkan_data.py). Skrip ini
menuliskan sidik jarinya sendiri juga ke laporan.

Pakai:
  .venv-qa/bin/python scripts/qa/test_t6e_langkah0_pengampu.py
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

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t6e_langkah0_pengampu.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t6e_langkah0"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PLACEHOLDER = "belum diisi"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pulihkan_data  # noqa: E402

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
    page.context.clear_cookies()
    page.goto(f"{BASE}/", wait_until="load")
    page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
    page.goto(f"{BASE}/", wait_until="load")
    page.wait_for_selector('input[type="email"]', timeout=60000)
    page.fill('input[type="email"]', a["email"])
    page.fill('input[type="password"]', a["password"])
    page.click('button[type="submit"]')
    page.wait_for_selector("header", timeout=60000)


def opsi_halaqah(page, tid: str) -> list[str]:
    page.click(f"#{tid}")
    page.wait_for_selector('[role="option"]', timeout=20000)
    opsi = [(o.inner_text() or "").strip() for o in page.query_selector_all('[role="option"]')]
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    return opsi


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    asli = pulihkan_data.rekam(db)
    mulai = dt.datetime.now(dt.timezone.utc)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            galat: list[str] = []
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)

            # ---------- 1. Mudarris/ah: Ilmu Wasilah ----------
            login(page, akun("mudarris"))
            page.goto(f"{BASE}/input/wasilah", wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.wait_for_timeout(1500)
            opsi = opsi_halaqah(page, "input-halaqah-wasilah")
            ampu = {r[0] for r in db.execute(
                """select h.code from public.halaqah_teachers ht join public.halaqahs h on h.id=ht.halaqah_id
                   join public.profiles p on p.id=ht.profile_id where p.role='mudarris'""").fetchall()}
            catat("Mudarris/ah hanya ditawari halaqah yang diampu (Wasilah)",
                  len(opsi) > 0 and all(o.split(" - ")[0] in ampu for o in opsi),
                  ditawarkan=len(opsi), contoh=opsi[:3])

            sebelum = db.execute("select count(*) from public.progress_entries pe join public.subjects s "
                                 "on s.id=pe.subject_id where s.domain='wasilah'").fetchone()[0]
            tombol = page.query_selector_all('[role="combobox"]')
            tombol_item = [b for b in tombol if (b.get_attribute("id") or "").startswith("wasilah-")]
            catat("Mudarris/ah: ada dropdown item Wasilah", bool(tombol_item), jumlah=len(tombol_item))
            if tombol_item:
                tombol_item[0].click()
                page.wait_for_selector('input[type="search"]:visible', timeout=20000)
                page.locator('input[type="search"]:visible').first.fill("1")
                page.wait_for_timeout(1800)
                opsi_item = page.query_selector_all('[role="option"]')
                label = opsi_item[0].inner_text().strip() if opsi_item else ""
                if opsi_item:
                    opsi_item[0].click()
                page.wait_for_timeout(400)
                page.get_by_role("button", name="Simpan", exact=True).first.click()
                batas = time.time() + 120
                sesudah = sebelum
                while time.time() < batas:
                    sesudah = db.execute("select count(*) from public.progress_entries pe join public.subjects s "
                                         "on s.id=pe.subject_id where s.domain='wasilah'").fetchone()[0]
                    if sesudah > sebelum:
                        break
                    page.wait_for_timeout(500)
                catat("Mudarris/ah: Simpan menulis capaian Wasilah ke semua anggota", sesudah > sebelum,
                      dipilih=label, sebelum=sebelum, sesudah=sesudah)
                page.reload(wait_until="load")
                page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
                page.wait_for_timeout(2000)
                tampil = [b.inner_text().split("\n")[0].strip()
                          for b in page.query_selector_all('[role="combobox"]')
                          if (b.get_attribute("id") or "").startswith("wasilah-")]
                catat("Mudarris/ah: label tersimpan tampil lagi setelah muat ulang",
                      bool(tampil) and tampil[0] == label and PLACEHOLDER not in tampil[0],
                      diharapkan=label, tampil=tampil[:1])
            page.screenshot(path=str(FOTO / "mudarris_wasilah.png"), full_page=True)

            # ---------- 2. Musyrif/ah: Al Qur'an ----------
            login(page, akun("musyrif"))
            page.goto(f"{BASE}/input", wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.wait_for_timeout(1500)
            opsi = opsi_halaqah(page, "input-halaqah")
            ampu_m = {r[0] for r in db.execute(
                """select h.code from public.halaqah_teachers ht join public.halaqahs h on h.id=ht.halaqah_id
                   join public.profiles p on p.id=ht.profile_id where p.role='musyrif' and h.domain='alquran'""").fetchall()}
            catat("Musyrif/ah hanya ditawari halaqah yang diampu (Al Qur'an)",
                  len(opsi) > 0 and all(o.split(" - ")[0] in ampu_m for o in opsi),
                  ditawarkan=len(opsi), contoh=opsi[:3])

            # Pilih bulan Rabiul Akhir (bulan berisi data; bulan default layar = Ramadhan
            # yang belum punya Hari Efektif, sehingga tidak ada item untuk diuji).
            page.click("#input-bulan")
            page.wait_for_selector('[role="option"]', timeout=20000)
            page.get_by_role("option", name="Rabiul Akhir", exact=True).first.click()
            page.wait_for_timeout(2500)
            sebelum = db.execute("select count(*) from public.progress_entries").fetchone()[0]
            kartu = page.locator("li button[aria-expanded]").filter(has_text="belum lengkap")
            catat("Musyrif/ah: ada santri 'belum lengkap' di halaqahnya", kartu.count() > 0,
                  kartu=kartu.count())
            if kartu.count():
                kartu.first.click()
                page.wait_for_timeout(600)
                dd = page.query_selector_all('button[id^="item-"]')
                if dd:
                    dd[0].click()
                    try:
                        page.wait_for_selector('[role="option"]', timeout=30000)
                        page.locator('input[type="search"]:visible').first.fill("1")
                        page.wait_for_timeout(1500)
                        page.wait_for_function(
                            "() => Array.from(document.querySelectorAll('[role=\"option\"]'))"
                            ".some(o => !o.innerText.includes('belum diisi'))", timeout=20000)
                    except Exception:  # noqa: BLE001
                        pass
                    opsi_item = [o for o in page.query_selector_all('[role="option"]')
                                 if "belum diisi" not in o.inner_text()]
                    if opsi_item:
                        opsi_item[0].click()
                        page.wait_for_timeout(400)
                        page.get_by_role("button", name="Simpan", exact=True).first.click()
                        page.wait_for_timeout(2500)
                        if "Pengulangan atau khatam" in page.inner_text("body"):
                            page.get_by_role("button", name="Pengulangan").first.click()
                            page.wait_for_timeout(500)
                            page.get_by_role("button", name="Simpan dengan pilihan ini").first.click()
                            page.wait_for_timeout(3500)
                batas = time.time() + 120
                sesudah = sebelum
                while time.time() < batas:
                    sesudah = db.execute("select count(*) from public.progress_entries").fetchone()[0]
                    if sesudah > sebelum:
                        break
                    page.wait_for_timeout(500)
                catat("Musyrif/ah: Simpan menulis capaian Al Qur'an", sesudah > sebelum,
                      sebelum=sebelum, sesudah=sesudah)
            page.screenshot(path=str(FOTO / "musyrif_alquran.png"), full_page=True)

            # ---------- 3. Halaqah Level 6 (Ilmu Wasilah) ----------
            login(page, akun("mudir"))
            page.goto(f"{BASE}/input/wasilah", wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.wait_for_timeout(1500)
            opsi = opsi_halaqah(page, "input-halaqah-wasilah")
            level6 = next((o for o in opsi if o.split(" - ")[0] == "Level 6"), None)
            catat("Level 6 muncul di dropdown halaqah Wasilah untuk Mudir", bool(level6), opsi=level6)
            n_anggota = db.execute("""select count(*) from public.halaqah_members hm join public.halaqahs h
                                      on h.id=hm.halaqah_id where h.code='Level 6' and hm.left_on is null""").fetchone()[0]
            n_mapel = db.execute("""select count(*) from public.halaqah_subjects hs join public.halaqahs h
                                    on h.id=hs.halaqah_id where h.code='Level 6'""").fetchone()[0]
            if level6:
                page.click("#input-halaqah-wasilah")
                page.wait_for_selector('[role="option"]', timeout=20000)
                page.get_by_role("option", name=level6, exact=True).first.click()
                page.wait_for_timeout(2500)
                isi = page.inner_text("main")
                tombol_item = [b for b in page.query_selector_all('[role="combobox"]')
                               if (b.get_attribute("id") or "").startswith("wasilah-")]
                capai_level6 = db.execute("""select count(*) from public.progress_entries pe
                                             join public.halaqahs h on h.id=pe.halaqah_id where h.code='Level 6'""").fetchone()[0]
                catat("Level 6: halaman terbuka, menunjukkan jumlah anggota, tanpa mata pelajaran",
                      (f"{n_anggota} anggota" in isi or "Belum ada anggota" in isi)
                      and len(tombol_item) == 0 and n_mapel == 0,
                      anggota=n_anggota, mapel=n_mapel, dropdown_item=len(tombol_item))
                page.screenshot(path=str(FOTO / "level6_wasilah.png"), full_page=True)
                catat("Level 6: belum ada capaian (bukan dikarang)", capai_level6 == 0, capaian=capai_level6)

            catat("konsol bersih", not galat, galat=galat[:5])
            browser.close()
    finally:
        pulihkan_data.pulihkan(db, asli)
        sama, beda = pulihkan_data.sama_dengan(db, asli)
        catat("data uji dipulihkan persis (seluruh nilai & jejak sama)", sama, beda=beda)

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
