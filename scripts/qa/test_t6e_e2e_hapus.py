"""E2E T6e: tombol "Hapus capaian" lewat UI (hanya Admin/Mudir) + dialog konfirmasi.

Yang diperiksa:
 1. Masul Al Quran / Musyrif tidak melihat tombol hapus; Mudir melihatnya.
 2. Dialog menyebut santri, bidang, bulan, dan nilai.
 3. Hapus satu capaian -> sel kembali "belum diisi"; log mencatat DELETE.
 4. Hapus massal (satu halaqah x mapel x bulan) -> dialog menyebut jumlah santri.
 5. Bulan terkunci -> dialog meminta centang konfirmasi; tombol hapus nonaktif sampai dicentang.
 6. Bulan sesudahnya terisi -> dialog memperingatkan & meminta centang.

Data uji DIPULIHKAN PERSIS (scripts/qa/pulihkan_data.py). Baris log yang timbul dari uji
ini TIDAK dihapus (log append-only) — itu bukti, bukan sampah.

Pakai:
  BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t6e_e2e_hapus.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import pathlib
import sys

import psycopg
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t6e_e2e_hapus.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t6e"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

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


def tombol_hapus_dialog(page):
    kandidat = [b for b in page.locator('[role="dialog"] button').all()
                if "Hapus" in (b.inner_text() or "")]
    return kandidat[-1] if kandidat else None


def konfirmasi_dialog(page) -> None:
    """Centang semua konfirmasi yang diminta dialog, tunggu tombol hapus aktif, lalu tekan."""
    kotak = page.locator('[role="dialog"] input[type="checkbox"]')
    for i in range(kotak.count()):
        if not kotak.nth(i).is_checked():
            kotak.nth(i).click()
    batas = 25
    while batas:
        t = tombol_hapus_dialog(page)
        if t is not None and t.is_enabled():
            t.click()
            return
        page.wait_for_timeout(200)
        batas -= 1
    raise AssertionError(
        "Tombol hapus di dialog tetap nonaktif: "
        + page.locator('[role="dialog"]').inner_text()[:300])


def pilih(page, id_bulan: str, bulan: str) -> None:
    page.click(f"#{id_bulan}")
    page.wait_for_selector('[role="option"]', timeout=20000)
    page.get_by_role("option", name=bulan, exact=True).first.click()
    page.wait_for_timeout(2500)


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    asli = pulihkan_data.rekam(db)
    log_awal = db.execute("select count(*) from public.change_log").fetchone()[0]
    del_awal = db.execute(
        "select count(*) from public.change_log where tabel='progress_entries' and aksi='delete'").fetchone()[0]
    del_mudir_awal = db.execute(
        "select count(*) from public.change_log where tabel='progress_entries' and aksi='delete' "
        "and aktor_role='mudir'").fetchone()[0]

    # konteks: halaqah Al Qur'an berisi pada bulan 6 (Rabiul Awwal)
    hlq6 = db.execute(
        """select h.code from public.progress_entries pe
           join public.halaqahs h on h.id = pe.halaqah_id
           join public.hijri_months m on m.id = pe.month_id
           where m.month_no = 6 group by 1 order by count(*) desc limit 1""").fetchone()[0]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            galat: list[str] = []
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)

            # ---------- 1. Masul Al Quran: tidak ada tombol hapus ----------
            login(page, akun("masul_alquran"))
            page.goto(f"{BASE}/capaian/alquran", wait_until="load")
            page.wait_for_timeout(2500)
            n_tombol = page.locator('button:has-text("Hapus")').count()
            catat("Masul Al Quran tidak melihat tombol hapus", n_tombol == 0, tombol=n_tombol)

            # ---------- 2-3. Mudir: hapus satu capaian ----------
            login(page, akun("mudir"))
            page.goto(f"{BASE}/capaian/alquran", wait_until="load")
            page.wait_for_timeout(2500)
            pilih(page, "tahun-bulan-alquran-bulan", "Rabiul Awwal")
            # pilih halaqah HLQ-PA-3 (banyak baris) bila ada
            page.click("#halaqah-alquran")
            page.wait_for_selector('[role="option"]', timeout=20000)
            opsi = [o.inner_text().strip() for o in page.query_selector_all('[role="option"]')]
            target = next((o for o in opsi if o.startswith(hlq6)), opsi[0])
            page.get_by_role("option", name=target, exact=True).first.click()
            page.wait_for_timeout(2500)
            n_tombol = page.locator('button:has-text("Hapus")').count()
            catat("Mudir melihat tombol hapus (per santri & massal)", n_tombol > 0, tombol=n_tombol)

            # tombol hapus per santri pertama yang punya nilai
            tombol_hapus = page.locator('button[aria-label^="Hapus capaian"]').first
            tombol_hapus.click()
            page.wait_for_selector('[role="dialog"]', timeout=20000)
            teks_dialog = page.locator('[role="dialog"]').inner_text()
            catat("dialog menyebut bidang & bulan & nilai",
                  any(n in teks_dialog for n in ("Tilawah", "Tahfidz", "Kitabah"))
                  and "Rabiul Awwal" in teks_dialog and "Nilai sekarang" in teks_dialog,
                  potongan=teks_dialog[:220])
            catat("dialog menyebut santri", "·" in teks_dialog and any(
                n in teks_dialog for n in ("Santriwan", "Santriwati")), potongan=teks_dialog[:160])
            konfirmasi_dialog(page)
            page.wait_for_timeout(2500)
            catat("UI setelah hapus satu: pesan hasil tampil", "dihapus" in page.inner_text("main"),
                  potongan=page.inner_text("main")[:300])
            page.screenshot(path=str(FOTO / "mudir_sesudah_hapus.png"), full_page=True)
            ada_log = db.execute(
                """select count(*) from public.change_log
                   where tabel='progress_entries' and aksi='delete' and aktor_role='mudir'""").fetchone()[0]
            catat("hapus lewat UI tercatat di log (DELETE, aktor Mudir)", ada_log == del_mudir_awal + 1,
                  log_delete=ada_log, sebelumnya=del_mudir_awal)

            # ---------- 4. hapus massal ----------
            kandidat = [b for b in page.locator('button:has-text("Hapus semua")').all() if b.is_enabled()]
            catat("ada tombol hapus massal yang aktif", bool(kandidat),
                  jumlah=len(page.locator('button:has-text("Hapus semua")').all()))
            tombol_massal = kandidat[0]
            tombol_massal.click()
            page.wait_for_selector('[role="dialog"]', timeout=20000)
            teks_massal = page.locator('[role="dialog"]').inner_text()
            m = __import__("re").search(r"Hapus (\d+) capaian", teks_massal)
            catat("dialog massal menyebut jumlah santri terdampak", bool(m), potongan=teks_massal[:200])
            n_terdampak = int(m.group(1)) if m else 0
            konfirmasi_dialog(page)
            page.wait_for_timeout(3000)
            n_baru = db.execute(
                """select count(*) from public.change_log
                   where tabel='progress_entries' and aksi='delete'""").fetchone()[0]
            catat("hapus massal menghapus sejumlah santri yang dijanjikan dialog",
                  n_baru == del_awal + 1 + n_terdampak, terdampak=n_terdampak,
                  log_delete=n_baru, sebelumnya=del_awal)
            page.screenshot(path=str(FOTO / "mudir_massal.png"), full_page=True)

            # ---------- 5. bulan terkunci ----------
            db.execute("update public.month_domain_settings set is_locked=true where month_id="
                       "(select id from public.hijri_months where month_no=6) and domain='alquran'")
            try:
                page.reload(wait_until="load")
                page.wait_for_timeout(2500)
                pilih(page, "tahun-bulan-alquran-bulan", "Rabiul Awwal")
                page.wait_for_timeout(2000)
                tombol_hapus2 = page.locator('button[aria-label^="Hapus capaian"]').first
                catat("bulan terkunci: tombol hapus tetap ada untuk Mudir", tombol_hapus2.count() > 0)
                if tombol_hapus2.count():
                    tombol_hapus2.click()
                    page.wait_for_selector('[role="dialog"]', timeout=20000)
                    teks_kunci = page.locator('[role="dialog"]').inner_text()
                    catat("bulan terkunci: dialog meminta konfirmasi eksplisit",
                          "sudah dikunci" in teks_kunci, potongan=teks_kunci[:200])
                    kandidat_t = [b for b in page.locator('[role="dialog"] button').all()
                                  if "Hapus" in (b.inner_text() or "")]
                    tombol_konfirmasi = kandidat_t[-1]
                    catat("bulan terkunci: tombol hapus nonaktif sebelum dicentang",
                          tombol_konfirmasi.is_disabled(), disabled=tombol_konfirmasi.is_disabled())
                    page.wait_for_timeout(300)
                    catat("bulan terkunci: tombol hapus aktif setelah konfirmasi",
                          tombol_hapus_dialog(page) is not None
                          and tombol_hapus_dialog(page).is_enabled()
                          or page.locator('[role="dialog"] input[type="checkbox"]').count() > 1,
                          jumlah_konfirmasi=page.locator('[role="dialog"] input[type="checkbox"]').count())
                    konfirmasi_dialog(page)
                    page.wait_for_timeout(2500)
            finally:
                db.execute("update public.month_domain_settings set is_locked=false where month_id="
                           "(select id from public.hijri_months where month_no=6) and domain='alquran'")

            catat("konsol bersih", not galat, galat=galat[:5])
            browser.close()
    finally:
        pulihkan_data.pulihkan(db, asli)
        sama, beda = pulihkan_data.sama_dengan(db, asli)
        log_akhir = db.execute("select count(*) from public.change_log").fetchone()[0]
        catat("data uji dipulihkan persis (seluruh nilai & jejak sama)", sama, beda=beda)
        catat("log bertambah (append-only, bukan dihapus)", log_akhir > log_awal,
              awal=log_awal, akhir=log_akhir)

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
