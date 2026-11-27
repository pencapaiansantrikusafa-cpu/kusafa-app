"""E2E RINGKAS T7c [3/3] butir 1-2: form Input Wasilah/Ghayah (capaian + target bulan depan).

Satu pengampu dan satu Masul Wasilah menulis lewat TAMPILAN, memeriksa tampilan
(pesan sukses + nilai tersimpan tampil kembali), lalu data dipulihkan PERSIS
(pulihkan_data) dan dibandingkan sidik jarinya (db_fingerprint). Uji ini MENULIS
hanya baris miliknya sendiri pada SATU database (= produksi).

Yang diperiksa:
  1. Pengampu simpan gabungan -> pesan sukses tampil + capaian tersalin ke semua
     anggota + target bulan depan dibuat (status `diajukan`).
  2. Nilai target tersimpan tampil kembali setelah halaman dimuat ulang
     (keterangan "Sudah ada").
  3. Masul Wasilah simpan gabungan -> pesan sukses tampil + target langsung
     `disetujui`.
  4. Data dipulihkan PERSIS + sidik jari SAMA.

Pakai:
  npm run build
  python3 scripts/qa/serve_dist.py 4173 &
  BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t7c3_form_e2e.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time

import psycopg
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t7c3_form_e2e.json"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

sys_path = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(sys_path))
import db_fingerprint  # noqa: E402
import pulihkan_data  # noqa: E402

LULUS = 0
GAGAL: list[str] = []
RINCIAN: list[dict] = []


def catat(nama: str, ok: bool, **info) -> None:
    global LULUS
    RINCIAN.append({"uji": nama, "ok": bool(ok), **info})
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


USERS = list(csv.DictReader(pathlib.Path("scripts/seed/output/users.csv").open(encoding="utf-8")))


def akun_nama(nama: str) -> dict:
    for u in USERS:
        if u["full_name"] == nama:
            return u
    raise SystemExit(f"akun {nama} tidak ada di users.csv")


def akun_role(role: str) -> dict:
    for u in USERS:
        if u["role"] == role:
            return u
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
    page.wait_for_timeout(800)


def pilih(page, id_tombol: str, cari: str, nama_opsi: str | None = None) -> str:
    page.click(f"#{id_tombol}")
    page.wait_for_selector('input[type="search"]:visible', timeout=20000)
    kotak = page.locator('input[type="search"]:visible').first
    kotak.fill(cari)
    page.wait_for_timeout(900)
    if nama_opsi:
        opsi = page.get_by_role("option", name=re.compile(nama_opsi)).first
    else:
        opsi = page.get_by_role("option").first
    label = opsi.inner_text().strip().split("\n")[0]
    opsi.click()
    page.wait_for_timeout(400)
    return label


def alert_teks(page) -> list[str]:
    return [t.strip() for t in page.locator('[role="alert"]').all_inner_texts() if t.strip()]


def tunggu_sukses(page, batas_detik: int = 20) -> str:
    """Tunggu pesan sukses (`[role="status"]`) tampil lalu kembalikan teksnya."""
    akhir = time.time() + batas_detik
    teks = ""
    while time.time() < akhir:
        teks = " ".join(t.strip() for t in page.locator('[role="status"]').all_inner_texts() if t.strip())
        if "tersimpan" in teks.lower() or "tuntas" in teks.lower():
            return teks
        page.wait_for_timeout(200)
    return teks


def isi_halaman(page, nama6: str) -> None:
    """Pilih halaqah Level Dasar A + bulan `nama6` di halaman Input Wasilah."""
    page.goto(f"{BASE}/input/wasilah", wait_until="load")
    page.get_by_role("button", name="Simpan capaian & target").wait_for(timeout=60000)
    pilih(page, "input-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
    pilih(page, "input-wasilah-bulan", nama6, re.escape(nama6))
    page.wait_for_timeout(1200)


def main() -> int:  # noqa: C901
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    c = db.cursor()

    def satu(q: str, a: tuple = ()):
        c.execute(q, a)
        return c.fetchone()[0]

    def hitung(q: str, a: tuple = ()) -> int:
        c.execute(q, a)
        return int(c.fetchone()[0])

    hal_id = satu("select id from public.halaqahs where domain='wasilah' and code='Level Dasar A'")
    bulan6 = satu("select id from public.hijri_months where month_no=6")
    bulan7 = satu("select id from public.hijri_months where month_no=7")
    nama6 = satu("select name from public.hijri_months where id=%s", (bulan6,))
    c.execute("select subject_id, name from public.halaqah_mapel_aktif(%s,%s)", (hal_id, bulan6))
    mapel = c.fetchall()
    sid0, nama_mapel0 = mapel[0]
    sid1, nama_mapel1 = mapel[1]
    anggota = hitung(
        "select count(*) from public.halaqah_members where halaqah_id=%s and left_on is null",
        (hal_id,),
    )
    pengampu_nama = satu(
        """select p.full_name from public.halaqah_teachers ht
           join public.profiles p on p.id=ht.profile_id
           where ht.halaqah_id=%s group by p.full_name order by count(*) desc limit 1""",
        (hal_id,),
    )
    akun_pengampu = akun_nama(pengampu_nama)
    akun_masul = akun_role("masul_wasilah")

    def pe(subject: str) -> int:
        return hitung(
            "select count(*) from public.progress_entries where halaqah_id=%s and subject_id=%s and month_id=%s",
            (hal_id, subject, bulan6),
        )

    def target_live(subject: str) -> list[tuple]:
        c.execute(
            """select status, target_item_id from public.targets
               where halaqah_id=%s and subject_id=%s and effective_month_id=%s
               order by created_at, id""",
            (hal_id, subject, bulan7),
        )
        return c.fetchall()

    asli = pulihkan_data.rekam(db)
    fp_awal = db_fingerprint.rekam()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1280, "height": 1000})

            # ---------------- 1. PENGAMPU: simpan gabungan ----------------
            login(page, akun_pengampu)
            isi_halaman(page, nama6)
            jml_awal0 = pe(sid0)
            pilih(page, f"wasilah-{sid0}", "1")
            pilih(page, f"target-{sid0}", "2")
            page.get_by_role("button", name="Simpan capaian & target").click()
            teks = tunggu_sukses(page)
            batas = time.time() + 30
            while time.time() < batas and len(target_live(sid0)) == 0:
                page.wait_for_timeout(500)
            live0 = target_live(sid0)
            catat(
                "1. Pengampu simpan gabungan: pesan sukses tampil + capaian tersalin + target diajukan",
                "tersimpan" in teks.lower() and pe(sid0) == anggota
                and len(live0) == 1 and live0[0][0] == "diajukan",
                pesan=teks[:160], mapel=nama_mapel0, baris=pe(sid0), anggota=anggota, target=live0,
            )

            # ---------------- 2. Nilai tersimpan tampil kembali ----------------
            page.reload(wait_until="load")
            isi_halaman(page, nama6)
            page.wait_for_timeout(1500)
            tampil = page.get_by_text("Sudah ada", exact=False).count() > 0
            catat(
                "2. Target bulan depan tersimpan tampil kembali (keterangan 'Sudah ada')",
                tampil, mapel=nama_mapel0,
            )

            # ---------------- 3. MASUL: simpan gabungan ----------------
            login(page, akun_masul)
            isi_halaman(page, nama6)
            jml_awal1 = pe(sid1)
            pilih(page, f"wasilah-{sid1}", "1")
            pilih(page, f"target-{sid1}", "1")
            page.get_by_role("button", name="Simpan capaian & target").click()
            teks = tunggu_sukses(page)
            batas = time.time() + 30
            while time.time() < batas and len(target_live(sid1)) == 0:
                page.wait_for_timeout(500)
            live1 = target_live(sid1)
            catat(
                "3. Masul Wasilah simpan gabungan: pesan sukses tampil + target langsung disetujui",
                "tersimpan" in teks.lower() and pe(sid1) == anggota
                and len(live1) == 1 and live1[0][0] == "disetujui",
                pesan=teks[:160], mapel=nama_mapel1, baris=pe(sid1), target=live1,
            )
            browser.close()
    finally:
        pulihkan_data.pulihkan(db, asli)
        sama, beda = pulihkan_data.sama_dengan(db, asli)
        fp_akhir = db_fingerprint.rekam()
        log_lama = db_fingerprint.cek_log_sampai(fp_awal.get("_log_change_log", {}).get("maks_id", 0))
        log_utuh = log_lama == fp_awal.get("_log_change_log", {}).get("checksum")
        selisih = db_fingerprint.banding(fp_awal, fp_akhir, log_lama_utuh=log_utuh)
        catat("4. Data dipulihkan PERSIS + sidik jari SAMA", sama, beda=beda, log_tumbuh=selisih)

    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(
        json.dumps(
            {"marker": "UJI-T7C3-FORM-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"),
             "lulus": LULUS, "gagal": GAGAL, "rincian": RINCIAN},
            ensure_ascii=False, indent=2, default=str,
        ),
        encoding="utf-8",
    )
    print(f"{LULUS} LULUS, {len(GAGAL)} gagal | Laporan: {HASIL}")
    for g in GAGAL:
        print("GAGAL:", g)
    return 0 if not GAGAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
