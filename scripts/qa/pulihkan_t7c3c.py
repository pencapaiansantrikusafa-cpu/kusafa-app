"""Pulihkan sisa E2E T7c [3c] yang menggantung (tanpa snapshot `finally`).

Uji `test_t7c3_e2e.py` menggantung saat menunggu kotak notifikasi; blok `finally`
(restore) tidak sempat jalan. Baris sisa teridentifikasi dari `change_log` + waktu
baseline sidik jari:
  - progress_entries: 20 baris baru, halaqah 'Level Dasar A' (wasilah), bulan 6.
  - targets: 5 baris baru (marker UJI-T7C3-20261128-164856 + hasil simpan UI).

Skrip ini membangun snapshot `asli` = keadaan sekarang dikurangi baris sisa itu,
lalu memakai `pulihkan_data.pulihkan` (jalur uji yang sudah teruji) untuk
menghapusnya, dan memeriksa `sama_dengan`. Hanya MENGHAPUS baris yang dibuat uji.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import psycopg  # noqa: E402
import pulihkan_data  # noqa: E402

HAL = "24f4a4de-e603-5624-a70c-b7e13c79268c"  # Level Dasar A (wasilah)
# Baseline sidik jari sebelum rangkaian uji T7c[3c] (waktu simpan berkas).
BASELINE = "2026-11-28T09:12:52+00"


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in pathlib.Path(".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main() -> int:
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    c = db.cursor()
    # Baris sisa = dibuat uji ini: semua progress_entries halaqah uji (baseline 0 di sana),
    # dan targets halaqah uji yang dibuat setelah baseline atau ber-marker UJI-T7C3.
    c.execute("select id from public.targets where halaqah_id=%s and "
              "(created_at > %s or note like 'UJI-T7C3-%%')", (HAL, BASELINE))
    target_sisa = {str(r[0]) for r in c.fetchall()}
    c.execute("select id from public.progress_entries where halaqah_id=%s", (HAL,))
    pe_ids = {str(r[0]) for r in c.fetchall()}
    asli = pulihkan_data.rekam(db)
    pe = asli["progress_entries"]
    sisa_pe = [k for k in pe if k[0] in pe_ids]
    for k in sisa_pe:
        pe.pop(k)
    tg = asli["targets"]
    sisa_tg = [k for k in tg if k[0] in target_sisa]
    for k in sisa_tg:
        tg.pop(k)
    print(f"akan dihapus: progress_entries={len(sisa_pe)}, targets={len(sisa_tg)}")
    pulihkan_data.pulihkan(db, asli)
    sama, beda = pulihkan_data.sama_dengan(db, asli)
    print("pulih:", "SAMA" if sama else beda)
    db.close()
    return 0 if sama else 1


if __name__ == "__main__":
    raise SystemExit(main())
