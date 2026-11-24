#!/usr/bin/env python3
"""
Uji otomatis: santri yang tidak punya halaqah di suatu domain.

Kasus uji nyata (keputusan Mudir 24 November 2026, dibiarkan apa adanya):
  - 1447.dummy-nis.023 : punya halaqah Al Qur'an + Ilmu Wasilah, TIDAK punya Ilmu Ghayah.
  - 1447.dummy-nis.024 : punya halaqah Al Qur'an saja (tidak punya Wasilah dan Ghayah).

Yang diuji:
  1. Keanggotaan halaqah per domain sesuai kenyataan (tidak menambah/mengarang baris).
  2. View v_monthly_report tidak error dan tidak menampilkan baris untuk domain yang tidak diikuti
     (santri tidak muncul, bukan tampil 0).
  3. Fungsi bantu mengembalikan false/NULL dengan aman (tidak error) untuk domain yang tidak diikuti.
  4. Staf pengampu tidak bisa menulis capaian domain yang tidak diikuti santri (RLS menolak);
     semua uji tulis di dalam transaksi lalu ROLLBACK.

Membaca .env.local; tidak mencetak rahasia.
Jalankan: python scripts/qa/test_no_halaqah.py
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "qa" / f"no_halaqah_{datetime.date.today().isoformat()}.json"

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

results: list[dict] = []


def rec(name: str, ok: bool, detail: str, evidence: dict | None = None) -> None:
    results.append({"name": name, "ok": ok, "detail": detail, "evidence": evidence or {}})
    print(("PASS" if ok else "FAIL"), name, "-", detail)


def fetch1(conn, q, params=None):
    return conn.execute(q, params or ()).fetchone()


def fetchall(conn, q, params=None):
    return conn.execute(q, params or ()).fetchall()


conn = psycopg.connect(env["DATABASE_URL"], autocommit=True, connect_timeout=20)

# ---------------------------------------------------------------- konteks
students = {}
for nis in ("1447.dummy-nis.023", "1447.dummy-nis.024"):
    row = fetch1(conn, "select id, full_name from public.students where nis=%s", (nis,))
    students[nis] = row

nilai_023 = students["1447.dummy-nis.023"]
nilai_024 = students["1447.dummy-nis.024"]

if not nilai_023 or not nilai_024:
    rec("konteks_santri_uji", False, "Santri 023/024 tidak ditemukan; uji tidak bisa dijalankan.")
    conn.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"tests": results}, indent=2, default=str), encoding="utf-8")
    sys.exit(1)

id_023 = nilai_023[0]
id_024 = nilai_024[0]

# ---------------------------------------------------------------- 1. keanggotaan
rows = fetchall(
    conn,
    """
    select s.nis, h.domain::text, count(*)
    from public.students s
    join public.halaqah_members hm on hm.student_id = s.id and hm.left_on is null
    join public.halaqahs h on h.id = hm.halaqah_id
    where s.nis in ('1447.dummy-nis.023','1447.dummy-nis.024')
    group by s.nis, h.domain
    """,
)
anggota = {(r[0], r[1]): r[2] for r in rows}
rec(
    "keanggotaan_023_alquran_dan_wasilah_tanpa_ghayah",
    anggota.get(("1447.dummy-nis.023", "alquran"), 0) == 1
    and anggota.get(("1447.dummy-nis.023", "wasilah"), 0) == 1
    and anggota.get(("1447.dummy-nis.023", "ghayah"), 0) == 0,
    "023: alquran=1, wasilah=1, ghayah=0",
    {"anggota": {f"{k[0]}|{k[1]}": v for k, v in anggota.items()}},
)
rec(
    "keanggotaan_024_hanya_alquran",
    anggota.get(("1447.dummy-nis.024", "alquran"), 0) == 1
    and anggota.get(("1447.dummy-nis.024", "wasilah"), 0) == 0
    and anggota.get(("1447.dummy-nis.024", "ghayah"), 0) == 0,
    "024: alquran=1, wasilah=0, ghayah=0",
)

# ---------------------------------------------------------------- 2. view laporan
try:
    n = fetch1(
        conn,
        "select count(*) from public.v_monthly_report where student_id=%s and domain='ghayah'",
        (id_023,),
    )[0]
    rec("v_monthly_report_023_ghayah_kosong_tanpa_error", n == 0, f"baris={n} (tidak ditampilkan)")
except Exception as e:  # noqa: BLE001
    rec("v_monthly_report_023_ghayah_kosong_tanpa_error", False, f"Error: {type(e).__name__}: {e}")

try:
    n = fetch1(
        conn,
        "select count(*) from public.v_monthly_report where student_id=%s and domain in ('wasilah','ghayah')",
        (id_024,),
    )[0]
    rec("v_monthly_report_024_wasilah_ghayah_kosong_tanpa_error", n == 0, f"baris={n} (tidak ditampilkan)")
except Exception as e:  # noqa: BLE001
    rec("v_monthly_report_024_wasilah_ghayah_kosong_tanpa_error", False, f"Error: {type(e).__name__}: {e}")

try:
    n = fetch1(
        conn,
        "select count(*) from public.v_monthly_report where student_id=%s and domain='alquran'",
        (id_024,),
    )[0]
    rec("v_monthly_report_024_alquran_ada", n > 0, f"baris={n} (domain yang diikuti tetap tampil)")
except Exception as e:  # noqa: BLE001
    rec("v_monthly_report_024_alquran_ada", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 3. fungsi bantu
try:
    r = fetch1(conn, "select public.student_in_taught_domain(%s,'ghayah'::public.domain_kind)", (id_023,))
    rec("fungsi_student_in_taught_domain_023_ghayah_false", r[0] is False, f"hasil={r[0]}")
except Exception as e:  # noqa: BLE001
    rec("fungsi_student_in_taught_domain_023_ghayah_false", False, f"Error: {type(e).__name__}: {e}")

sub_gh = fetch1(conn, "select id from public.subjects where domain='ghayah' limit 1")
if sub_gh:
    try:
        r = fetch1(conn, "select public.student_in_taught_halaqah(%s,%s)", (id_023, sub_gh[0]))
        rec("fungsi_student_in_taught_halaqah_023_ghayah_false", r[0] is False, f"hasil={r[0]}")
    except Exception as e:  # noqa: BLE001
        rec("fungsi_student_in_taught_halaqah_023_ghayah_false", False, f"Error: {type(e).__name__}: {e}")

try:
    r = fetch1(conn, "select public.can_manage(NULL::public.domain_kind)")
    rec("fungsi_can_manage_null_aman", r[0] is False or r[0] is None, f"hasil={r[0]}")
except Exception as e:  # noqa: BLE001
    rec("fungsi_can_manage_null_aman", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 4. RLS: pengampu tidak bisa menulis domain yang tidak diikuti
# Cari musyrif (staf non-admin) dan item Ghayah.
guru = fetch1(
    conn,
    "select p.id from public.profiles p where p.role='musyrif' and p.is_active order by p.full_name limit 1",
)
item_gh = fetch1(
    conn,
    """
    select ci.id from public.curriculum_items ci
    join public.books b on b.id=ci.book_id
    join public.subjects s on s.id=b.subject_id
    where s.domain='ghayah' and ci.is_active limit 1
    """,
)
bulan = fetch1(conn, "select id from public.hijri_months where month_no=6 limit 1")

if guru and item_gh and sub_gh and bulan:
    try:
        conn.autocommit = False
        conn.execute("begin")
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(guru[0]),))
        conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        try:
            conn.execute(
                """
                insert into public.progress_entries (student_id, month_id, subject_id, item_id, putaran)
                values (%s,%s,%s,%s,1)
                """,
                (id_023, bulan[0], sub_gh[0], item_gh[0]),
            )
            rec(
                "rls_pengampu_tidak_bisa_menulis_ghayah_santri_tanpa_halaqah",
                False,
                "INSERT BERHASIL; seharusnya ditolak RLS.",
            )
        except psycopg.errors.InsufficientPrivilege:
            rec(
                "rls_pengampu_tidak_bisa_menulis_ghayah_santri_tanpa_halaqah",
                True,
                "Ditolak RLS (InsufficientPrivilege), bukan error skema.",
            )
        except Exception as e:  # noqa: BLE001
            rec(
                "rls_pengampu_tidak_bisa_menulis_ghayah_santri_tanpa_halaqah",
                False,
                f"Ditolak, tetapi bukan oleh RLS: {type(e).__name__}: {e}",
            )
        finally:
            conn.rollback()
    finally:
        conn.autocommit = True
else:
    rec("rls_pengampu_tidak_bisa_menulis_ghayah_santri_tanpa_halaqah", False, "Konteks tidak cukup.")

# ---------------------------------------------------------------- ringkasan
conn.close()
gagal = [r for r in results if not r["ok"]]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps({"ran_at": datetime.datetime.now().isoformat(), "tests": results}, indent=2, default=str),
    encoding="utf-8",
)
print(f"\n{len(results) - len(gagal)}/{len(results)} PASS. Laporan: {OUT}")
sys.exit(1 if gagal else 0)
