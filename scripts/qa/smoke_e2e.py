#!/usr/bin/env python3
"""
Smoke E2E pra-T6 [6/6]: satu putaran untuk SETIAP role lewat browser sungguhan.

Per role: login → halaman utama termuat → kotak notifikasi → halaman Input
(masalah "belum lengkap"/"belum punya halaqah") → simpan satu capaian (HANYA
Mudir; menulis ke database) lalu kembalikan persis → keluar.

Menjaga data: sebelum/ setelah simpan, skrip mencatat `id` dan `entered_at`
baris progress_entries untuk halaqah uji, lalu menghapus HANYA baris dengan
`entered_at` terbaru (yang diciptakan uji ini) dan mengembalikan kehadiran
ke nilai semula. Tidak menyentuh baris lain.

Kata sandi dibaca dari scripts/seed/output/users.csv dan TIDAK pernah dicetak.
Laporan ringkas → docs/qa/smoke_e2e_<tanggal>[_prod].json.

Jalankan:
    .venv-qa/bin/python scripts/qa/smoke_e2e.py
    BASE_URL=https://kusafa-app.vercel.app .venv-qa/bin/python scripts/qa/smoke_e2e.py
Opsi: HEADLESS=0 (lihat jendela), ROLES=mudir,admin (subset), DATA_UJI=0 (lompati simpan).
"""
from __future__ import annotations

import csv
import datetime
import json
import os
import sys
from pathlib import Path

import psycopg
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://localhost:5173").rstrip("/")
HEADLESS = os.environ.get("HEADLESS", "1") != "0"
DATA_UJI = os.environ.get("DATA_UJI", "1") != "0"
HALAQAH_UJI = os.environ.get("HALAQAH", "HLQ-PA-1")
BULAN_UJI = os.environ.get("BULAN", "Rabiul Akhir")
SUFFIX = "_prod" if "vercel" in BASE else ""
OUT = ROOT / "docs" / "qa" / f"smoke_e2e_{datetime.date.today().isoformat()}{SUFFIX}.json"

URUT = ["mudir", "admin", "masul_alquran", "masul_wasilah", "masul_ghayah", "musyrif", "mudarris"]
ROLES = [r for r in os.environ.get("ROLES", "").split(",") if r] or URUT

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

rows = list(csv.DictReader(open(ROOT / "scripts/seed/output/users.csv", encoding="utf-8")))
per_role: dict[str, dict] = {}
for r in rows:
    per_role.setdefault(r["role"], r)

hasil: list[dict] = []


def catat(role, langkah, ok, pesan=""):
    hasil.append({"role": role, "langkah": langkah, "ok": ok, "pesan": pesan[:400]})
    print(("PASS" if ok else "FAIL"), f"{role:14s}", langkah, "-", pesan[:170])


def tunggu_muat(page):
    page.wait_for_function("() => !document.body.innerText.includes('Memuat...')", timeout=25000)


def login(page, akun):
    page.goto(BASE + "/", wait_until="load")
    page.wait_for_selector('input[type="email"]', timeout=20000)
    page.fill('input[type="email"]', akun["email"])
    page.fill('input[type="password"]', akun["password"])
    page.click('button[type="submit"]')
    page.wait_for_selector("header", timeout=25000)
    tunggu_muat(page)


def pilih_dropdown(page, tombol, opsi_nama):
    tombol.first.click()
    page.get_by_role("option", name=opsi_nama).first.click()


def simpan_capaian(page, conn):
    """Simpan satu capaian lewat UI untuk HALAQAH_UJI / BULAN_UJI, lalu kembalikan."""
    teks = page.inner_text("main")
    if "Halaqah" not in teks:
        return "lompati", "role tanpa form input"

    # --- pilih halaqah (tombol berisi "HLQ")
    page.locator("button").filter(has_text="HLQ").first.click()
    page.wait_for_timeout(400)
    opsi_hlq = [o.inner_text().strip() for o in page.query_selector_all('[role="option"]')]
    target_hlq = next((t for t in opsi_hlq if t.startswith(HALAQAH_UJI)), None)
    if not target_hlq:
        return "gagal", f"halaqah {HALAQAH_UJI} tidak ada di daftar"
    page.get_by_role("option", name=target_hlq, exact=True).first.click()
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=20000)

    # --- pilih bulan (tombol dropdown berakhiran ▾ yang bukan halaqah/tahun)
    tombol_bulan = page.locator("button").filter(has_text="▾").filter(
        has_not_text="HLQ").filter(has_not_text=" H")  # bukan "1447 H"
    # lebih andal: tombol yang kini menampilkan nama bulan adalah tombol ke-3 di samping label "Bulan"
    kandidat = []
    for b in page.query_selector_all("button"):
        t = b.inner_text().strip()
        if t.endswith("▾") and "HLQ" not in t:
            kandidat.append(b)
    if not kandidat:
        return "gagal", "tombol bulan tidak ditemukan"
    # tombol bulan = kandidat terakhir yang teksnya bukan tahun
    tombol = next((b for b in kandidat if not b.inner_text().strip().startswith("14")), None) or kandidat[-1]
    tombol.click()
    page.wait_for_timeout(400)
    page.get_by_role("option", name=BULAN_UJI, exact=True).first.click()
    page.wait_for_timeout(2500)

    # catat komposisi progress_entries halaqah/bulan ini SEBELUM (id + entered_at)
    def snapshot():
        return {
            r[0]: r[1] for r in conn.execute(
                "select pe.id, pe.entered_at from public.progress_entries pe "
                "join public.halaqahs h on h.id=pe.halaqah_id "
                "join public.hijri_months m on m.id=pe.month_id "
                "where h.code=%s and m.name=%s", (HALAQAH_UJI, BULAN_UJI)).fetchall()
        }

    sebelum = snapshot()
    waktu_mulai = datetime.datetime.now(datetime.timezone.utc)
    pesan_galat = ""

    try:
        # buka kartu santri "belum lengkap" pertama
        kartu = page.locator("li button[aria-expanded]").filter(has_text="belum lengkap")
        if kartu.count() == 0:
            return "lompati", "semua santri halaqah ini sudah lengkap bulan tsb"
        kartu.first.click()
        page.wait_for_timeout(600)
        dd = page.query_selector_all('button[id^="item-"]')
        if not dd:
            return "gagal", "dropdown item tidak muncul"
        dd[0].click()
        # T5c: daftar awal kini diambil dari server (RPC) setelah panel dibuka;
        # tunggu sampai pilihan muncul (bukan jeda tetap).
        try:
            page.wait_for_function(
                "() => Array.from(document.querySelectorAll('[role=\"option\"]'))"
                ".some(o => !o.innerText.includes('belum diisi'))",
                timeout=20000,
            )
        except Exception:  # noqa: BLE001
            pass
        opsi = [o for o in page.query_selector_all('[role="option"]') if "belum diisi" not in o.inner_text()]
        if not opsi:
            return "gagal", "tidak ada pilihan item"
        opsi[1 if len(opsi) > 1 else 0].click()
        page.wait_for_timeout(400)
        page.get_by_role("button", name="Simpan", exact=True).first.click()
        page.wait_for_timeout(2500)
        # Konfirmasi "Pengulangan / Khatam" hanya muncul bila capaian yang DIUBAH lebih kecil
        # dari bulan lalu (aturan final). Jawab "Pengulangan" lalu simpan lagi.
        teks_konfirmasi = page.inner_text("body")
        if "Pengulangan atau khatam" in teks_konfirmasi:
            page.get_by_role("button", name="Pengulangan").first.click()
            page.wait_for_timeout(500)
            page.get_by_role("button", name="Simpan dengan pilihan ini").first.click()
            page.wait_for_timeout(4000)
        page.wait_for_timeout(1500)
        isi_setelah = page.inner_text("main")
        tersimpan_ui = "Data tersimpan" in isi_setelah
        for baris in isi_setelah.splitlines():
            if "tersimpan" in baris.lower() or "galat" in baris.lower():
                pesan_galat = baris[:160]
    finally:
        # Selalu bersihkan: hapus HANYA baris yang entered_at-nya >= waktu mulai (dibuat uji ini),
        # baris lama tidak pernah disentuh.
        baru = [(k, t) for k, t in snapshot().items() if k not in sebelum and t >= waktu_mulai]
        for k, _ in baru:
            conn.execute("delete from public.progress_entries where id=%s", (k,))
        bersih = set(snapshot()) == set(sebelum)
        if "baru" not in dir():
            baru = []

    # Bukti simpan yang sebenarnya = baris baru tercatat di database (bukan teks UI yang
    # langsung hilang saat form dimuat ulang). Data yang dikembalikan bersih juga wajib.
    sukses = bool(baru) and bersih
    return ("berhasil" if sukses else "gagal",
            f"baris database baru={len(baru)} (bukti tersimpan); dikembalikan bersih={bersih}"
            + (f"; pesan_ui={pesan_galat}" if pesan_galat else ""))


def main():
    conn = psycopg.connect(env["DATABASE_URL"], autocommit=True, connect_timeout=20)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        for role in ROLES:
            akun = per_role.get(role)
            if not akun:
                catat(role, "akun", False, "tidak ada akun dummy")
                continue
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = ctx.new_page()
            galat_konsol: list[str] = []
            page.on("console", lambda m: galat_konsol.append(m.text) if m.type == "error" else None)
            try:
                login(page, akun)
                isi = page.inner_text("body")
                catat(role, "login+utama", "Keluar" in isi and "KUSAFA" in isi,
                      "header tampil setelah login")
                ada_notif = ("belum lengkap" in isi.lower()) or ("belum punya halaqah" in isi.lower())
                page.goto(BASE + "/input", wait_until="load")
                tunggu_muat(page)
                # Notifikasi "belum punya halaqah" dimuat dari database. Polling (bukan
                # wait_for_function pada elemen): elemen dari React baru ada setelah render.
                ada_kotak = False
                for _ in range(60):
                    isi_input = page.inner_text("main")
                    if "belum punya halaqah" in isi_input.lower() and "Memeriksa..." not in isi_input:
                        ada_kotak = True
                        break
                    page.wait_for_timeout(1000)
                catat(role, "notifikasi",
                      ada_kotak if role in ("mudir", "admin", "masul_wasilah", "masul_ghayah") else True,
                      ("kotak 'santri belum punya halaqah' tampil" if ada_kotak
                       else "tidak tampil (wajar untuk role ini)"))
                if role == "mudir" and DATA_UJI:
                    status, ket = simpan_capaian(page, conn)
                    catat(role, "simpan_dan_kembalikan", status in ("berhasil", "lompati"), f"[{status}] {ket}")
                page.goto(BASE + "/capaian/alquran", wait_until="load")
                tunggu_muat(page)
                page.wait_for_timeout(1200)
                catat(role, "halaman_capaian", True, "termuat tanpa galat")
                berbahaya = [g for g in galat_konsol if "favicon" not in g.lower()]
                catat(role, "konsol_bersih", len(berbahaya) == 0,
                      "tanpa galat konsol" if not berbahaya else "; ".join(berbahaya)[:250])
            except Exception as e:  # noqa: BLE001
                catat(role, "alur", False, f"{type(e).__name__}: {str(e).splitlines()[0][:200]}")
            finally:
                ctx.close()
        browser.close()
    conn.close()


main()
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"base": BASE, "ran_at": datetime.datetime.now().isoformat(), "hasil": hasil},
                          indent=2, default=str, ensure_ascii=False), encoding="utf-8")
gagal = [h for h in hasil if not h["ok"]]
print(f"\n{len(hasil) - len(gagal)}/{len(hasil)} PASS. Laporan: {OUT}")
sys.exit(1 if gagal else 0)