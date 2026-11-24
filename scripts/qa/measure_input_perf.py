#!/usr/bin/env python3
"""
Ukur kinerja halaman Input Al Qur'an (T5c).

Per role (default: mudir): login -> buka /input -> tunggu tombol "Simpan" muncul,
lalu catat:
  - waktu sampai form siap (detik, dari navigasi sampai "Simpan" tampil)
  - jumlah permintaan HTTP dan total byte respons
  - jumlah permintaan ke tabel curriculum_items + total byte-nya
  - waktu muat dokumen (domContentLoaded / load)

Kata sandi dibaca dari scripts/seed/output/users.csv; tidak pernah dicetak.
Opsi: VIEWPORT=360 (lebar HP), ROLES=mudir, BASE_URL=..., HASIL=<berkas json>.

Jalankan:
  .venv-qa/bin/python scripts/qa/measure_input_perf.py
  VIEWPORT=360 .venv-qa/bin/python scripts/qa/measure_input_perf.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://localhost:5173").rstrip("/")
VIEWPORT = int(os.environ.get("VIEWPORT", "1440"))
ROLES = [r for r in os.environ.get("ROLES", "mudir").split(",") if r]
HASIL = os.environ.get("HASIL", "")
ULANG = int(os.environ.get("ULANG", "1"))

rows = list(csv.DictReader(open(ROOT / "scripts/seed/output/users.csv", encoding="utf-8")))
per_role: dict[str, dict] = {}
for r in rows:
    per_role.setdefault(r["role"], r)

hasil: list[dict] = []


def ukur(role: str, akun: dict) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        ctx = browser.new_context(viewport={"width": VIEWPORT, "height": 900})
        page = ctx.new_page()

        catatan = {"total": 0, "bytes": 0, "items": 0, "items_bytes": 0, "rpc": 0, "urls": []}

        def on_response(resp):
            try:
                body = resp.body()
            except Exception:  # noqa: BLE001
                body = b""
            catatan["total"] += 1
            catatan["bytes"] += len(body)
            if "curriculum_items" in resp.url:
                catatan["items"] += 1
                catatan["items_bytes"] += len(body)
            if "/rpc/" in resp.url:
                catatan["rpc"] += 1
            if any(k in resp.url for k in ("curriculum_items", "/rpc/")):
                catatan["urls"].append({"url": resp.url.split("?")[0], "bytes": len(body), "status": resp.status})

        page.on("response", on_response)

        # login
        page.goto(BASE + "/", wait_until="load")
        page.wait_for_selector('input[type="email"]', timeout=30000)
        page.fill('input[type="email"]', akun["email"])
        page.fill('input[type="password"]', akun["password"])
        page.click('button[type="submit"]')
        page.wait_for_selector("header", timeout=30000)

        # ukur halaman input
        t0 = time.perf_counter()
        page.goto(BASE + "/input", wait_until="commit")
        page.wait_for_function("() => !document.body.innerText.includes('Memuat data...')", timeout=120000)
        page.get_by_role("button", name="Simpan", exact=True).first.wait_for(timeout=120000)
        t_siap = time.perf_counter() - t0

        nav = page.evaluate(
            "() => { const n = performance.getEntriesByType('navigation')[0];"
            " return n ? {dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd,"
            " transfer: n.transferSize} : {}; }"
        )
        # lebar & kemungkinan geser horizontal (nyaman di HP)
        lebar = page.evaluate(
            "() => ({inner: window.innerWidth, doc: document.documentElement.scrollWidth})"
        )
        browser.close()
    return {
        "role": role,
        "viewport": VIEWPORT,
        "siap_detik": round(t_siap, 2),
        "permintaan": catatan["total"],
        "total_kb": round(catatan["bytes"] / 1024, 1),
        "permintaan_items": catatan["items"],
        "items_kb": round(catatan["items_bytes"] / 1024, 1),
        "permintaan_rpc": catatan["rpc"],
        "nav": {"dcl_ms": round(nav.get("dcl", 0), 1), "load_ms": round(nav.get("load", 0), 1)},
        "lebar": lebar,
        "urls": catatan["urls"][:12],
    }


for role in ROLES:
    akun = per_role.get(role)
    if not akun:
        print("SKIP", role, "(tidak ada akun)")
        continue
    for putaran in range(ULANG):
        h = ukur(role, akun)
        h["putaran"] = putaran + 1
        hasil.append(h)
        print(
            f"{role} #{putaran + 1}: siap {h['siap_detik']}s | permintaan {h['permintaan']} "
            f"({h['total_kb']} KB) | curriculum_items {h['permintaan_items']} ({h['items_kb']} KB) "
            f"| rpc {h['permintaan_rpc']} | lebar {h['lebar']}"
        )

if HASIL:
    out = ROOT / HASIL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(hasil, indent=2, default=str), encoding="utf-8")
    print("Laporan:", out)
sys.exit(0)