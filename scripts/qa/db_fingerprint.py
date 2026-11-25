"""Sidik jari database: jumlah baris + checksum per tabel.

Tujuan (T6d3): database lokal dan produksi adalah SATU Supabase. Setiap rangkaian uji
yang MENULIS (E2E, smoke, uji DB) wajib memulihkan baris PERSIS. Alat ini merekam
keadaan seluruh tabel `public` sebelum dan sesudah uji; bila berbeda, uji dianggap
GAGAL dan selisihnya dilaporkan.

Yang direkam per tabel:
  - jumlah baris (count);
  - checksum isi: md5 dari semua baris (kolom diurutkan nama) yang diserialkan dengan
    `row_to_json(...::text)`, diurutkan menurut primary key (atau seluruh kolom bila
    tabel tidak punya PK), sehingga checksum berubah bila ADA satu nilai berubah
    (termasuk `entered_by`/`entered_at`/`updated_by`).

Sengaja memakai query COUNT/checksum di sisi server, bukan mengambil semua baris:
`progress_entries` 2.000+ baris dan `curriculum_items` 10.000+ baris melebihi batas
1.000 baris Supabase.

Pakai:
  python scripts/qa/db_fingerprint.py                      # cetak sidik jari sekarang
  python scripts/qa/db_fingerprint.py --simpan docs/qa/x.json   # simpan untuk banding
  python scripts/qa/db_fingerprint.py --banding docs/qa/x.json  # banding dengan berkas
  # hasil: keluar 0 bila SAMA, 1 bila BERBEDA (daftar tabel yang berubah dicetak)

Catatan: hanya MEMBACA. Tidak pernah menulis ke database.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import psycopg

TABEL = [
    "academic_years", "hijri_months", "subjects", "books", "curriculum_items",
    "students", "guardians", "student_levels", "halaqahs", "halaqah_members",
    "halaqah_teachers", "halaqah_subjects", "targets", "progress_entries",
    "attendance", "monthly_notes", "month_domain_settings", "profiles",
]


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in pathlib.Path(".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def kolom(c, tabel: str) -> list[str]:
    return [r[0] for r in c.execute(
        "select column_name from information_schema.columns "
        "where table_schema='public' and table_name=%s order by ordinal_position", (tabel,)).fetchall()]


def urutan(c, tabel: str, semua: list[str]) -> str:
    """Urutan deterministik: primary key bila ada, selain itu seluruh kolom."""
    pk = [r[0] for r in c.execute(
        """select a.attname from pg_index i
           join pg_attribute a on a.attrelid = i.indrelid and a.attnum = any(i.indkey)
           where i.indrelid = ('public.' || %s)::regclass and i.indisprimary
           order by array_position(i.indkey, a.attnum)""", (tabel,)).fetchall()]
    pakai = pk or semua
    return ", ".join(f'"{k}"' for k in pakai)


def sidik(c, tabel: str) -> dict:
    semua = kolom(c, tabel)
    susunan = urutan(c, tabel, semua)
    sql = (
        f"select count(*), coalesce(md5(string_agg(t::text, '' order by {susunan})), '') "
        f'from public."{tabel}" t'
    )
    n, cek = c.execute(sql).fetchone()
    return {"baris": n, "checksum": cek}


def rekam() -> dict:
    conn = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    c = conn.cursor()
    hasil = {t: sidik(c, t) for t in TABEL}
    conn.close()
    return hasil


def banding(a: dict, b: dict) -> list[dict]:
    beda = []
    for t in sorted(set(a) | set(b)):
        x, y = a.get(t), b.get(t)
        if x != y:
            beda.append({
                "tabel": t,
                "sebelum": x,
                "sesudah": y,
                "selisih_baris": (y or {}).get("baris", 0) - (x or {}).get("baris", 0),
            })
    return beda


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--simpan", help="simpan sidik jari ke berkas JSON")
    p.add_argument("--banding", help="bandingkan sidik jari sekarang dengan berkas JSON")
    p.add_argument("--ringkas", action="store_true", help="cetak satu baris ringkas")
    a = p.parse_args()

    sekarang = rekam()
    total = sum(v["baris"] for v in sekarang.values())

    if a.simpan:
        pathlib.Path(a.simpan).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.simpan).write_text(json.dumps(sekarang, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
        print(f"sidik jari disimpan: {a.simpan} ({total} baris, {len(sekarang)} tabel)")
        return 0

    if a.banding:
        lama = json.loads(pathlib.Path(a.banding).read_text(encoding="utf-8"))
        beda = banding(lama, sekarang)
        if not beda:
            print(f"SAMA: {total} baris, {len(sekarang)} tabel (sidik jari identik)")
            return 0
        print("BERBEDA - sidik jari tidak identik:")
        for d in beda:
            print(f"  {d['tabel']}: baris {d['sebelum'] and d['sebelum']['baris']} -> "
                  f"{d['sesudah'] and d['sesudah']['baris']} (selisih {d['selisih_baris']}), "
                  f"checksum {'berubah' if (d['sebelum'] or {}).get('checksum') != (d['sesudah'] or {}).get('checksum') else 'tetap'}")
        return 1

    if a.ringkas:
        print(json.dumps({t: v["baris"] for t, v in sekarang.items()}, ensure_ascii=False))
        return 0

    print(f"sidik jari {len(sekarang)} tabel, total {total} baris")
    for t, v in sekarang.items():
        print(f"  {t:22} {v['baris']:>6}  {v['checksum']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
