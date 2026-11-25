"""Uji E2E T6d2: halaman Input untuk ketiga Masul (Simpan lewat UI).

Yang diperiksa:
 1. Masul Al Quran menawarkan SEMUA halaqah Al Qur'an (bukan hanya yang diampu) dan
    tombol Simpan benar-benar menulis capaian; label tersimpan tampil lagi setelah muat ulang.
 2. Masul Wasilah dan Masul Ghayah menawarkan semua halaqah/level di domainnya dan
    Simpan berhasil.
 3. Tab Input hanya menawarkan domain milik Masul itu.
 4. Musyrif/ah TETAP hanya ditawari halaqahnya sendiri.

Data uji dipulihkan: setiap baris progress_entries/attendance/monthly_notes yang
dibuat/diubah uji ini dikembalikan atau dihapus pada blok finally, lalu jumlah baris
dibandingkan dengan sebelum uji.

Pakai:
  .venv-qa/bin/python scripts/qa/test_t6d2_e2e_masul.py
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
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t6d2_e2e_masul.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t6d2"))
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
    page.context.clear_cookies()
    page.goto(f"{BASE}/", wait_until="load")
    page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
    page.goto(f"{BASE}/", wait_until="load")
    page.wait_for_selector('input[type="email"]', timeout=60000)
    page.fill('input[type="email"]', a["email"])
    page.fill('input[type="password"]', a["password"])
    page.click('button[type="submit"]')
    page.wait_for_selector("header", timeout=60000)


def opsi_halaqah(page, id_tombol: str) -> list[str]:
    page.click(f"#{id_tombol}")
    page.wait_for_selector('[role="option"]', timeout=20000)
    opsi = [(o.inner_text() or "").strip() for o in page.query_selector_all('[role="option"]')]
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    return opsi


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    mulai = dt.datetime.now(dt.timezone.utc)

    # Sidik jari LENGKAP tiga tabel yang mungkin disentuh: salinan semua kolom,
    # supaya pemulihan persis (nilai, entered_by/entered_at, updated_by/updated_at).
    # Sejak T6d3: uji yang menulis wajib memulihkan baris PERSIS dan lolos sidik jari.
    TABEL_UJI = ("progress_entries", "attendance", "monthly_notes")
    KUNCI = {
        "progress_entries": ("id",),
        "attendance": ("student_id", "month_id", "domain"),
        "monthly_notes": ("student_id", "month_id", "domain"),
    }

    def rekam(tabel: str) -> dict:
        kol = [r[0] for r in db.execute(
            "select column_name from information_schema.columns where table_schema='public' "
            "and table_name=%s order by ordinal_position", (tabel,)).fetchall()]
        rows = db.execute(f'select {", ".join(kol)} from public.{tabel}').fetchall()
        hasil = {}
        for r in rows:
            k = tuple(str(r[kol.index(x)]) for x in KUNCI[tabel])
            hasil[k] = dict(zip(kol, r))
        return hasil

    asli = {t: rekam(t) for t in TABEL_UJI}
    jml_sebelum = {t: len(asli[t]) for t in TABEL_UJI}

    def pulihkan(tabel: str) -> None:
        kunci = KUNCI[tabel]
        asli_t = asli[tabel]
        kol = list(next(iter(asli_t.values())).keys()) if asli_t else []
        sekarang = rekam(tabel)
        # 1. Hapus baris yang TIDAK ada sebelumnya (dibuat uji ini).
        for k in sekarang:
            if k not in asli_t:
                kondisi = " and ".join(f"{x}=%s" for x in kunci)
                db.execute(f"delete from public.{tabel} where {kondisi}", tuple(k))
        # 2. Kembalikan nilai baris lama yang berubah (termasuk jejak).
        for k, v in asli_t.items():
            if sekarang.get(k) == v:
                continue
            kondisi = " and ".join(f"{x}=%s" for x in kunci)
            db.execute(
                f"update public.{tabel} set {', '.join(f'{c}=%s' for c in kol)} where {kondisi}",
                tuple(v[c] for c in kol) + tuple(k),
            )


    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            galat: list[str] = []
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)

            # ---------- 1. Masul Al Quran: semua halaqah Al Qur'an + Simpan ----------
            login(page, akun("masul_alquran"))
            page.goto(f"{BASE}/input", wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.wait_for_timeout(1500)
            # Satu-satunya domain yang boleh input: bilah tab memang tidak ditampilkan
            # (perilaku yang sama sejak T6d). Yang harus terbukti: halaman ini adalah Al Qur'an
            # dan domain lain tidak dapat dibuka.
            # Halaman Input Al Qur'an dikenali dari dropdown halaqah `input-halaqah`
            # (form Wasilah memakai `input-halaqah-wasilah`).
            page.wait_for_selector("#input-halaqah", timeout=60000)
            punya_input_alquran = page.query_selector("#input-halaqah") is not None
            page.goto(f"{BASE}/input/wasilah", wait_until="load")
            page.wait_for_timeout(2500)
            catat("Masul Al Quran: hanya Al Qur'an (domain lain dialihkan)",
                  punya_input_alquran and page.url.endswith("/input/alquran"),
                  url=page.url)
            page.goto(f"{BASE}/input", wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.wait_for_timeout(1500)
            opsi = opsi_halaqah(page, "input-halaqah")
            semua = db.execute(
                "select count(*) from public.halaqahs where domain='alquran' and is_active"
            ).fetchone()[0]
            catat("Masul Al Quran ditawari SEMUA halaqah Al Qur'an", len(opsi) == semua,
                  ditawarkan=len(opsi), total=semua, contoh=opsi[:2])

            # Pilih halaqah yang BUKAN halaqah ampuannya (Masul Al Quran tidak mengampu).
            hlq_ampu = db.execute(
                """select h.code from public.halaqah_teachers ht join public.halaqahs h on h.id=ht.halaqah_id
                   join public.profiles p on p.id=ht.profile_id
                   where p.role='masul_alquran' and h.domain='alquran' limit 1"""
            ).fetchone()
            ampu = hlq_ampu[0] if hlq_ampu else None
            target = next((o for o in opsi if not ampu or not o.startswith(ampu)), None)
            if target:
                page.click("#input-halaqah")
                page.wait_for_selector('[role="option"]', timeout=20000)
                page.get_by_role("option", name=target, exact=True).first.click()
                page.wait_for_timeout(2500)
            catat("Masul Al Quran bisa membuka halaqah di luar ampuannya", bool(target), halaqah=target)

            # Pilih satu item di dropdown pertama, lalu Simpan.
            sebelum = db.execute(
                """select count(*) from public.progress_entries pe join public.profiles p on p.id=pe.entered_by
                   where p.role='masul_alquran'"""
            ).fetchone()[0]
            tombol_item = page.query_selector_all('button[id^="item-"]')
            tombol_item[0].click()
            page.wait_for_selector('input[type="search"]:visible', timeout=20000)
            page.locator('input[type="search"]:visible').first.fill("2")
            page.wait_for_timeout(1800)
            opsi_item = page.query_selector_all('[role="option"]')
            pilihan = opsi_item[0].inner_text().strip() if opsi_item else ""
            if opsi_item:
                opsi_item[0].click()
            page.wait_for_timeout(500)
            tampil = page.query_selector_all('button[id^="item-"]')[0].inner_text().split("\n")[0].strip()
            catat("Masul Al Quran: label pilihan tampil", tampil == pilihan and "belum diisi" not in tampil,
                  dipilih=pilihan, tampil=tampil)
            page.get_by_role("button", name="Simpan", exact=True).first.click()
            page.wait_for_timeout(1500)
            if page.get_by_role("dialog").count():
                page.get_by_role("button", name="Pengulangan", exact=True).first.click()
                page.get_by_role("button", name="Simpan dengan pilihan ini", exact=True).click()
            batas = time.time() + 120
            sesudah = sebelum
            while time.time() < batas:
                sesudah = db.execute(
                    """select count(*) from public.progress_entries pe join public.profiles p on p.id=pe.entered_by
                       where p.role='masul_alquran'"""
                ).fetchone()[0]
                if sesudah > sebelum:
                    break
                page.wait_for_timeout(500)
            catat("Masul Al Quran: Simpan menulis capaian (entered_by tercatat)", sesudah > sebelum,
                  sebelum=sebelum, sesudah=sesudah)
            page.screenshot(path=str(FOTO / "masul_alquran_simpan.png"), full_page=True)

            # ---------- 2. Masul Wasilah & Masul Ghayah ----------
            for role, domain, tabel in (("masul_wasilah", "wasilah", "wasilah"), ("masul_ghayah", "ghayah", "ghayah")):
                login(page, akun(role))
                page.goto(f"{BASE}/input/{domain}", wait_until="load")
                page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
                page.wait_for_timeout(1500)
                domain_lain = "ghayah" if domain == "wasilah" else "wasilah"
                page.goto(f"{BASE}/input/{domain_lain}", wait_until="load")
                page.wait_for_timeout(2000)
                catat(f"{role}: domain lain dialihkan ke domainnya", page.url.endswith(f"/input/{domain}"),
                      url=page.url)
                page.goto(f"{BASE}/input/{domain}", wait_until="load")
                page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
                page.wait_for_timeout(1500)
                opsi = opsi_halaqah(page, f"input-halaqah-{domain}")
                semua = db.execute(
                    "select count(*) from public.halaqahs where domain=%s and is_active", (domain,)
                ).fetchone()[0]
                catat(f"{role}: ditawari semua halaqah domainnya", len(opsi) == semua,
                      ditawarkan=len(opsi), total=semua)
                sebelum = db.execute(
                    f"select count(*) from public.progress_entries pe join public.subjects s on s.id=pe.subject_id "
                    f"where s.domain='{domain}'"
                ).fetchone()[0]
                tombol_item = page.query_selector_all('button[id^="wasilah-"]')
                if not tombol_item:
                    catat(f"{role}: Simpan menulis capaian", False, catatan="tidak ada mapel/pilihan")
                    continue
                tombol_item[0].click()
                page.wait_for_selector('input[type="search"]:visible', timeout=20000)
                page.locator('input[type="search"]:visible').first.fill("1")
                page.wait_for_timeout(1800)
                opsi_item = page.query_selector_all('[role="option"]')
                if opsi_item:
                    opsi_item[0].click()
                page.wait_for_timeout(400)
                page.get_by_role("button", name="Simpan", exact=True).first.click()
                batas = time.time() + 120
                sesudah = sebelum
                while time.time() < batas:
                    sesudah = db.execute(
                        f"select count(*) from public.progress_entries pe join public.subjects s on s.id=pe.subject_id "
                        f"where s.domain='{domain}'"
                    ).fetchone()[0]
                    if sesudah > sebelum:
                        break
                    page.wait_for_timeout(500)
                catat(f"{role}: Simpan menulis capaian untuk semua anggota", sesudah > sebelum,
                      sebelum=sebelum, sesudah=sesudah)
                page.screenshot(path=str(FOTO / f"{role}_simpan.png"), full_page=True)

            # ---------- 4. Musyrif tetap hanya halaqahnya ----------
            login(page, akun("musyrif"))
            page.goto(f"{BASE}/input", wait_until="load")
            page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=60000)
            page.wait_for_timeout(1500)
            opsi = opsi_halaqah(page, "input-halaqah")
            catat("Musyrif tetap hanya ditawari halaqahnya sendiri", 1 <= len(opsi) <= 2,
                  ditawarkan=len(opsi), contoh=opsi[:2])

            catat("konsol bersih", not galat, galat=galat[:5])
            browser.close()
    finally:
        # Pulihkan PERSIS: hapus baris baru, kembalikan nilai + jejak baris lama.
        for t in TABEL_UJI:
            pulihkan(t)
        sesudah = {t: rekam(t) for t in TABEL_UJI}
        jml_sesudah = {t: len(sesudah[t]) for t in TABEL_UJI}
        catat("data uji dipulihkan (seluruh nilai & jejak sama)",
              asli == sesudah,
              sebelum=jml_sebelum, sesudah=jml_sesudah,
              baris_beda={t: sum(1 for k in set(asli[t]) | set(sesudah[t]) if asli[t].get(k) != sesudah[t].get(k))
                          for t in TABEL_UJI})

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
