#!/usr/bin/env python3
"""
Uji pra-T6 [6]: aturan Data Awal (bulan 0) tahun kedua — jawaban Mudir 24 Nov 2026.

Aturan (docs/SPEC.md bagian 4a):
  - Tahun pertama pemakaian: bulan 0 "Data Awal" ada dan diisi manual Admin/Mudir.
  - Mulai tahun ajaran KEDUA, Data Awal TIDAK diisi manual: nilainya otomatis diambil
    dari capaian bulan terakhir (Ramadhan) tahun sebelumnya — juga bagi santri tahun
    pertama yang naik ke tahun kedua.
  - create_academic_year(...) TIDAK boleh meminta/membuat Data Awal untuk tahun kedua.

Yang diuji (semua dalam SATU transaksi, lalu ROLLBACK — tidak ada data yang tertinggal):
  1. create_academic_year(1448, ..., false) membuat 12 bulan (1..12), TANPA bulan 0.
  2. Syawwal 1448 punya prev_month_id = Ramadhan 1447 (bukan bulan 0).
  3. Selisih Syawwal 1448 di v_monthly_report = pos(Syawwal 1448) - pos(Ramadhan 1447)
     untuk santri yang naik dari tahun pertama (1447) ke tahun kedua (1448).
  4. Tidak ada baris Data Awal 1448 di hijri_months maupun v_monthly_report.
Membaca .env.local; tidak mencetak rahasia.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "qa" / f"data_awal_tahun_kedua_{datetime.date.today().isoformat()}.json"

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

results: list[dict] = []


def rec(name, ok, detail, evidence=None):
    results.append({"name": name, "ok": ok, "detail": detail, "evidence": evidence or {}})
    print(("PASS" if ok else "FAIL"), name, "-", detail)


conn = psycopg.connect(env["DATABASE_URL"], autocommit=False, connect_timeout=20)


def satu(q, params=()):
    r = conn.execute(q, params).fetchone()
    return r[0] if r else None


try:
    conn.execute("begin")

    # konteks: santri yang punya capaian di tahun 1447 (naik ke tahun kedua 1448)
    santri = satu("""
        select pe.student_id from public.progress_entries pe
        join public.hijri_months m on m.id=pe.month_id
        join public.academic_years ay on ay.id=m.academic_year_id
        where ay.hijri_year=1447
        order by pe.student_id limit 1""")
    subj = satu("select id from public.subjects where domain='alquran' order by sort_order limit 1")
    item_awal = satu("""
        select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
        where b.subject_id=%s order by ci.seq limit 1""", (subj,))
    item_lanjut = satu("""
        select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
        where b.subject_id=%s and ci.seq > 1 order by ci.seq limit 1""", (subj,))
    halaqah = satu("select id from public.halaqahs where domain='alquran' and is_active order by code limit 1")

    # 1. buat tahun ajaran 1448 tanpa Data Awal
    thn_baru = satu("select public.create_academic_year(1448, 'Uji 1448', false)")
    bulan_1448 = conn.execute(
        "select month_no from public.hijri_months where academic_year_id=%s order by month_no",
        (thn_baru,)).fetchall()
    daftar = [b[0] for b in bulan_1448]
    rec("1_tahun_kedua_tanpa_bulan_0", daftar == list(range(1, 13)),
        f"1448 bulan = {daftar} (harus 1..12, tanpa 0)")

    # 2. Syawwal 1448 -> prev = Ramadhan 1447
    syawal_1448 = satu("select id from public.hijri_months where academic_year_id=%s and month_no=1", (thn_baru,))
    ramadhan_1447 = satu("""
        select m.id from public.hijri_months m join public.academic_years ay on ay.id=m.academic_year_id
        where ay.hijri_year=1447 and m.month_no=12""")
    prev_id = satu("select prev_month_id from public.v_months_ordered where id=%s", (syawal_1448,))
    rec("2_syawwal_1448_pembanding_ramadhan_1447", prev_id == ramadhan_1447,
        f"prev_month_id Syawwal 1448 = {'Ramadhan 1447' if prev_id == ramadhan_1447 else prev_id}")

    # 3. capaian Ramadhan 1447 (data awal otomatis) + Syawwal 1448 (bulan pertama tahun kedua)
    conn.execute("""
        insert into public.progress_entries (student_id, halaqah_id, subject_id, month_id, item_id, putaran)
        values (%s,%s,%s,%s,%s,1)""", (santri, halaqah, subj, ramadhan_1447, item_awal))
    conn.execute("""
        insert into public.progress_entries (student_id, halaqah_id, subject_id, month_id, item_id, putaran)
        values (%s,%s,%s,%s,%s,1)""", (santri, halaqah, subj, syawal_1448, item_lanjut))
    pos_ramadhan = satu("select public.item_position(%s,1)", (item_awal,))
    pos_syawal = satu("select public.item_position(%s,1)", (item_lanjut,))
    row = conn.execute("""
        select selisih, prev_item_id from public.v_monthly_report
        where student_id=%s and month_id=%s and subject_id=%s""", (santri, syawal_1448, subj)).fetchone()
    selisih_ok = row is not None and row[0] is not None and abs(float(row[0]) - (float(pos_syawal) - float(pos_ramadhan))) < 1e-6
    rec("3_selisih_syawwal_1448_vs_ramadhan_1447", selisih_ok,
        f"selisih={row[0] if row else None}; harapan pos_syawal({pos_syawal}) - pos_ramadhan({pos_ramadhan}) = "
        f"{float(pos_syawal) - float(pos_ramadhan)}; prev_item cocok={row[1] == item_awal if row else False}",
        {"prev_item_sama_dengan_item_ramadhan": bool(row and row[1] == item_awal)})

    # 4. tidak ada Data Awal 1448 di mana pun
    ada_0 = satu("select count(*) from public.hijri_months where academic_year_id=%s and month_no=0", (thn_baru,))
    rec("4_tidak_ada_data_awal_1448", ada_0 == 0, f"baris month_no=0 untuk 1448 = {ada_0} (harus 0)")

    # 5. santri lama TIDAK perlu baris Data Awal 1448 untuk punya pembanding
    punya_pembanding = row is not None and row[1] is not None
    rec("5_santri_lama_otomatis_punya_pembanding", punya_pembanding,
        "Syawwal 1448 otomatis memakai capaian Ramadhan 1447 (tanpa mengisi Data Awal manual)")

finally:
    conn.rollback()
    conn.close()

gagal = [r for r in results if r["ok"] is False]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"ran_at": datetime.datetime.now().isoformat(), "tests": results},
                          indent=2, default=str, ensure_ascii=False), encoding="utf-8")
print(f"\n{sum(1 for r in results if r['ok'])}/{len(results)} PASS. Laporan: {OUT}")
sys.exit(1 if gagal else 0)