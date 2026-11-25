"""Uji penjaga data setelah seed: keadaan data yang disetujui Mudir tidak boleh hidup lagi.

Latar (T6d3): 7 baris kehadiran Ramadhan yang dihapus Mudir 23 Nov 2026 muncul lagi
karena seed dijalankan ulang (seed membuka dengan `truncate`). Uji ini gagal bila:
  1. ada baris kehadiran Ramadhan tanpa capaian;
  2. izin/sakit/alpha tidak sama dengan sumber (dicek oleh uji banding Excel penuh);
  3. capaian Wasilah/Ghayah bocor dari seed (harus 0 sebelum diisi staf).

HANYA MEMBACA. Jalankan sesudah seed atau sebelum push:
  python scripts/qa/test_seed_bersih.py
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

import psycopg

OUT = pathlib.Path("docs/qa") / f"seed_bersih_{datetime.date.today().isoformat()}.json"
hasil: list[dict] = []


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in pathlib.Path(".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def rec(nama: str, ok: bool, detail: str, **ev) -> None:
    hasil.append({"uji": nama, "ok": ok, "detail": detail, **ev})
    print(("PASS " if ok else "FAIL ") + nama + " - " + detail)


def main() -> int:
    c = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)

    # 1. Capaian harus sama dengan seed + baris uji Mudir (2.036 + 3 = 2.039).
    #    2.036 = jumlah baris `progress_entries` di berkas seed (diverifikasi terpisah
    #    oleh uji banding Excel penuh). 3 baris bulan Jumadal Ula adalah percobaan Mudir.
    n_prog = c.execute("select count(*) from public.progress_entries").fetchone()[0]
    rec("1a_jumlah_capaian_2039", n_prog == 2039,
        f"progress_entries: {n_prog} (harus 2.039 = 2.036 seed + 3 baris uji Mudir)")

    # 2. Ramadhan tanpa capaian (keputusan Mudir 23 Nov 2026 + T6d3)
    n = c.execute("""
        select count(*) from public.attendance a
        join public.hijri_months m on m.id = a.month_id
        where m.month_no = 12
          and not exists (select 1 from public.progress_entries pe
                          where pe.student_id = a.student_id and pe.month_id = a.month_id)
    """).fetchone()[0]
    rec("1_ramadhan_tanpa_capaian_0", n == 0,
        f"baris kehadiran Ramadhan tanpa capaian: {n} (harus 0). "
        "Bila > 0, seed dijalankan ulang: jalankan scripts/db/fixes/2026-11-25_hapus_kehadiran_ramadhan.sql")

    # 3. Kehadiran harus sama dengan jumlah yang disetujui
    per = dict(c.execute("select domain, count(*) from public.attendance group by 1").fetchall())
    rec("2_jumlah_kehadiran", per.get("alquran", 0) == 606 and per.get("wasilah", 0) == 756
        and per.get("ghayah", 0) == 749,
        f"kehadiran Al Qur'an {per.get('alquran')} (606), Wasilah {per.get('wasilah')} (756), "
        f"Ghayah {per.get('ghayah')} (749)", jumlah=per)

    # 4. Capaian Wasilah/Ghayah belum dikarang (harus 0)
    bocor = dict(c.execute("""
        select s.domain, count(*) from public.progress_entries pe
        join public.subjects s on s.id = pe.subject_id
        where s.domain <> 'alquran' group by 1""").fetchall())
    rec("3_capaian_wasilah_ghayah_0", not bocor,
        "tidak ada capaian Wasilah/Ghayah" if not bocor else f"ADA capaian karangan: {bocor}", jumlah=bocor)

    # 5. Catatan bulanan belum ada (data uji)
    n_note = c.execute("select count(*) from public.monthly_notes").fetchone()[0]
    rec("4_catatan_bulanan_0", n_note == 0, f"monthly_notes: {n_note} (harus 0)")

    c.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"tests": hasil}, indent=2, ensure_ascii=False), encoding="utf-8")
    gagal = [h for h in hasil if not h["ok"]]
    print(f"\n{len(hasil) - len(gagal)}/{len(hasil)} PASS. Laporan: {OUT}")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
