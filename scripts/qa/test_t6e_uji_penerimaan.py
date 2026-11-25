"""UJI PENERIMAAN T6e: Mudir menghapus 3 baris capaian percobaannya (Jumadal Ula) LEWAT FITUR.

Ini BUKAN uji yang memulihkan data: ketiga baris MEMANG dihapus permanen atas perintah
Mudir (T6e). Yang dibuktikan:
 1. Tombol "Hapus capaian" ada dan bisa dipakai Mudir di halaman Capaian.
 2. Tiap dialog menyebut santri, bidang, bulan, dan nilai.
 3. Setelah hapus, sel kembali "belum diisi" (teks), dan database tidak lagi memuat baris.
 4. Log mencatat 3 DELETE (progress_entries, aktor Mudir, nilai lama item_id).
 5. Sidik jari berubah TEPAT: progress_entries -3, change_log +3 (tidak ada lainnya).

Pakai:
  BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t6e_uji_penerimaan.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

import psycopg
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t6e_uji_penerimaan.json"))
FOTO = pathlib.Path("docs/qa/t6e")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
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


def sidik_jari() -> dict:
    subprocess.run([sys.executable, "scripts/qa/db_fingerprint.py", "--simpan", "/tmp/fp_terima.json"],
                   check=True, capture_output=True)
    return json.loads(pathlib.Path("/tmp/fp_terima.json").read_text(encoding="utf-8"))


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    sebelum = sidik_jari()
    log_awal = db.execute("select count(*) from public.change_log").fetchone()[0]

    # Tiga baris percobaan Mudir: santri "Santriwan fulan 16", bulan Jumadal Ula.
    target = db.execute("""
        select sj.name, ci.label
        from public.progress_entries pe
        join public.students st on st.id = pe.student_id
        join public.subjects sj on sj.id = pe.subject_id
        join public.hijri_months m on m.id = pe.month_id
        join public.curriculum_items ci on ci.id = pe.item_id
        where st.full_name = 'Santriwan fulan 16' and m.month_no = 8
        order by sj.name""").fetchall()
    catat("ada 3 baris percobaan Mudir (Tilawah/Tahfidz/Kitabah, Jumadal Ula)", len(target) == 3,
          target=[list(t) for t in target])

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            galat: list[str] = []
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun("mudir"))
            page.goto(f"{BASE}/capaian/alquran", wait_until="load")
            page.wait_for_timeout(2500)
            # Bulan Jumadal Ula + halaqah HLQ-PA-1
            page.click("#tahun-bulan-alquran-bulan")
            page.wait_for_selector('[role="option"]', timeout=20000)
            page.get_by_role("option", name="Jumadal Ula", exact=True).first.click()
            page.wait_for_timeout(2500)
            page.click("#halaqah-alquran")
            page.wait_for_selector('[role="option"]', timeout=20000)
            opsi = [o.inner_text().strip() for o in page.query_selector_all('[role="option"]')]
            target_hlq = next((o for o in opsi if o.startswith("HLQ-PA-1")), opsi[0])
            page.get_by_role("option", name=target_hlq, exact=True).first.click()
            page.wait_for_timeout(2500)

            for mapel, label in sorted(target):
                tombol = page.locator(
                    f'button[aria-label="Hapus capaian {mapel} Santriwan fulan 16"]')
                catat(f"tombol hapus {mapel} tersedia", tombol.count() > 0, jumlah=tombol.count())
                tombol.first.click()
                page.wait_for_selector('[role="dialog"]', timeout=20000)
                page.wait_for_timeout(600)
                teks = page.locator('[role="dialog"]').inner_text()
                catat(f"dialog {mapel} menyebut santri/bulan/nilai",
                      "Santriwan fulan 16" in teks and "Jumadal Ula" in teks and label in teks,
                      potongan=teks[:200])
                kandidat = [b for b in page.locator('[role="dialog"] button').all()
                            if "Hapus" in (b.inner_text() or "")]
                konfirmasi = kandidat[-1]
                # Centang konfirmasi bila dialog meminta (bulan terkunci / bulan sesudahnya terisi)
                kotak = page.locator('[role="dialog"] input[type="checkbox"]')
                for i in range(kotak.count()):
                    kotak.nth(i).click()
                page.wait_for_timeout(400)
                konfirmasi.click()
                page.wait_for_timeout(2500)
                sisa = db.execute("""
                    select count(*) from public.progress_entries pe
                    join public.students st on st.id = pe.student_id
                    join public.subjects sj on sj.id = pe.subject_id
                    join public.hijri_months m on m.id = pe.month_id
                    where st.full_name = 'Santriwan fulan 16' and m.month_no = 8 and sj.name = %s""",
                    (mapel,)).fetchone()[0]
                catat(f"{mapel}: baris database benar-benar terhapus", sisa == 0, sisa=sisa)
            page.screenshot(path=str(FOTO / "uji_penerimaan_sesudah.png"), full_page=True)
            # Tampilan kembali kosong: baris "belum diisi" untuk bidang yang dihapus
            teks_hal = page.inner_text("main")
            catat("setelah hapus, tampilan kembali 'belum diisi'",
                  "belum diisi" in teks_hal, potongan=teks_hal[:300])
            catat("konsol bersih", not galat, galat=galat[:5])
            browser.close()
    finally:
        sesudah = sidik_jari()
        baru_log = [r for r in db.execute("""
            select id, tabel, aksi, aktor_role, sumber, nilai_lama->>'item_id', nilai_lama->>'putaran'
            from public.change_log order by id desc limit 3""").fetchall()]
        catat("log mencatat 3 DELETE progress_entries oleh Mudir",
              len(baru_log) == 3 and all(r[1] == "progress_entries" and r[2] == "delete"
                                         and r[3] == "mudir" and r[4] == "aplikasi" for r in baru_log),
              log=[list(map(str, r)) for r in baru_log])
        catat("sidik jari berubah tepat -3 capaian",
              sesudah["progress_entries"]["baris"] == sebelum["progress_entries"]["baris"] - 3,
              sebelum=sebelum["progress_entries"]["baris"], sesudah=sesudah["progress_entries"]["baris"])
        catat("log bertambah (3 delete; tidak ada perubahan tabel lain)",
              sesudah["_log_change_log"]["baris"] == sebelum["_log_change_log"]["baris"] + 3
              and all(sesudah[t] == sebelum[t] for t in sebelum
                      if t not in ("progress_entries", "_log_change_log")),
              log_sebelum=sebelum["_log_change_log"]["baris"],
              log_sesudah=sesudah["_log_change_log"]["baris"])
        RINCIAN.append({"uji": "isi log 3 DELETE", "ok": True,
                        "log": [list(map(str, r)) for r in baru_log]})

    hasil = {
        "base": BASE,
        "lulus": LULUS,
        "gagal": GAGAL,
        "ringkasan": f"{LULUS} LULUS, {GAGAL}" if GAGAL else f"{LULUS} LULUS, 0 gagal",
        "rincian": RINCIAN,
        "catatan": "UJI PENERIMAAN: 3 baris dihapus permanen atas perintah Mudir, TIDAK dipulihkan.",
    }
    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(json.dumps(hasil, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for r in RINCIAN:
        print(("PASS " if r["ok"] else "GAGAL ") + r["uji"])
    print(hasil["ringkasan"], "| Laporan:", HASIL)
    return 0 if not GAGAL else 1


if __name__ == "__main__":
    sys.exit(main())
