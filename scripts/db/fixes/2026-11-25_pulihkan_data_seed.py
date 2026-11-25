#!/usr/bin/env python3
"""Pulihkan baris seed yang hilang/berubah di database (T6d3).

Latar: berkas seed (`supabase/seed/02_school_data.sql`, tidak di-commit) adalah sumber
data dummy yang disetujui Mudir. Uji yang menulis di database yang SAMA dengan produksi
pernah menghapus/menimpa baris seed (mis. `test_input_dropdown_e2e.py` menghapus semua
baris dengan `entered_at >= mulai`). Skrip ini mengembalikan:

  1. baris `progress_entries` yang ada di seed tetapi TIDAK ada di database
     (id, halaqah, item, putaran, `entered_at` seed, `entered_by` NULL);
  2. baris `attendance` Al Qur'an yang ada di seed tetapi TIDAK ada di database;
  3. nilai `attendance` (izin/sakit/alpha/effective_days_override) yang berbeda dari seed;
  4. jejak (`entered_at`, `entered_by`, `updated_by`, `updated_at`) baris seed yang
     berubah (dikembalikan ke `entered_at` seed, NULL).
  5. capaian Wasilah/Ghayah (harus 0) TIDAK disentuh; kalau ada, skrip berhenti.

TIDAK menghapus baris yang tidak ada di seed: 3 baris Jumadal Ula (percobaan Mudir) tetap.

Cara pakai (dari akar repo):
    python scripts/db/fixes/2026-11-25_pulihkan_data_seed.py            # lihat rencana
    python scripts/db/fixes/2026-11-25_pulihkan_data_seed.py --jalankan  # kerjakan

Membaca `.env.local`; tidak mencetak rahasia. Hanya menyentuh baris SEED yang hilang/berbeda.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import psycopg

ROOT = pathlib.Path(__file__).resolve().parents[3]
SEED = ROOT / "supabase/seed/02_school_data.sql"
POLA_PROG = re.compile(
    r"\('([0-9a-f-]{36})', '([0-9a-f-]{36})', '([0-9a-f-]{36})', '([0-9a-f-]{36})', "
    r"'([0-9a-f-]{36})', '([0-9a-f-]{36})', (\d+)\)")
POLA_ATT = re.compile(
    r"\('([0-9a-f-]{36})', '([0-9a-f-]{36})', '(\w+)', (\d+), (\d+), (\d+), (null|\d+)\)")


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def baca_seed():
    txt = SEED.read_text(encoding="utf-8")
    prog, att = [], []
    for m in re.finditer(r"insert into public\.progress_entries", txt):
        blok = txt[m.start():txt.index(";", m.start()) + 1]
        prog += POLA_PROG.findall(blok)
    for m in re.finditer(r"insert into public\.attendance", txt):
        blok = txt[m.start():txt.index(";", m.start()) + 1]
        att += POLA_ATT.findall(blok)
    return prog, att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jalankan", action="store_true", help="benar-benar menulis (tanpa ini: rencana saja)")
    a = ap.parse_args()

    prog, att = baca_seed()
    print(f"seed: {len(prog)} capaian, {len(att)} kehadiran Al Qur'an")

    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    ts_seed = db.execute(
        "select min(entered_at) from public.progress_entries where entered_by is null").fetchone()[0]
    print(f"cap jam seed (entered_at acuan): {ts_seed}")

    # ---------- 1. capaian seed yang hilang ----------
    ada = {(r[0], r[1], r[2]) for r in db.execute(
        "select student_id::text, subject_id::text, month_id::text from public.progress_entries").fetchall()}
    hilang = [r for r in prog if (r[1], r[3], r[4]) not in ada]
    print(f"capaian seed hilang: {len(hilang)}")
    for h in hilang[:5]:
        info = db.execute("""select s.nis, sj.name, m.month_no, ci.label from public.students s,
            public.subjects sj, public.hijri_months m, public.curriculum_items ci
            where s.id=%s and sj.id=%s and m.id=%s and ci.id=%s""", (h[1], h[3], h[4], h[5])).fetchone()
        print("   ", info)

    # ---------- 2. kehadiran seed yang hilang ----------
    ada_att = {(str(r[0]), str(r[1]), r[2]) for r in db.execute(
        "select student_id, month_id, domain from public.attendance").fetchall()}
    hilang_att = [r for r in att if (r[0], r[1], r[2]) not in ada_att]
    print(f"kehadiran seed hilang: {len(hilang_att)}")

    # ---------- 3. nilai kehadiran yang berbeda ----------
    db_att = {(str(r[0]), str(r[1]), r[2]): (r[3], r[4], r[5], r[6], r[7], r[8])
              for r in db.execute("""select student_id, month_id, domain, izin, sakit, alpha,
                 effective_days_override, entered_at, entered_by from public.attendance""").fetchall()}
    beda_att, jejak_att = [], []
    for sid, mid, dom, iz, sk, al, ov in att:
        ov_val = None if ov == "null" else int(ov)
        key = (sid, mid, dom)
        if key not in db_att:
            continue
        nilai, ent_at, ent_by = db_att[key][:4], db_att[key][4], db_att[key][5]
        if nilai != (int(iz), int(sk), int(al), ov_val):
            beda_att.append((key, nilai, (int(iz), int(sk), int(al), ov_val)))
        elif ent_at != ts_seed or ent_by is not None:
            jejak_att.append(key)
    print(f"nilai kehadiran beda dari seed: {len(beda_att)}; jejak kehadiran berubah: {len(jejak_att)}")

    # ---------- 4. jejak capaian berubah ----------
    jejak_prog = [r for r in db.execute(
        """select id from public.progress_entries
           where entered_by is null and (entered_at <> %s or updated_by is not null)""", (ts_seed,)).fetchall()]
    print(f"jejak capaian seed berubah: {len(jejak_prog)}")

    # ---------- 5. capaian Wasilah/Ghayah harus 0 ----------
    lain = db.execute("""select count(*) from public.progress_entries pe join public.subjects s
                         on s.id=pe.subject_id where s.domain <> 'alquran'""").fetchone()[0]
    if lain:
        sys.exit(f"BERHENTI: ada {lain} capaian Wasilah/Ghayah (harus 0); periksa dulu.")

    if not any([hilang, hilang_att, beda_att, jejak_att, jejak_prog]):
        print("Tidak ada yang perlu dipulihkan.")
        return 0
    if not a.jalankan:
        print("Rencana saja. Jalankan ulang dengan --jalankan.")
        return 0

    for h in hilang:
        db.execute("""insert into public.progress_entries
            (id, student_id, halaqah_id, subject_id, month_id, item_id, putaran, entered_at, entered_by)
            values (%s,%s,%s,%s,%s,%s,%s,%s,null) on conflict (student_id,subject_id,month_id) do nothing""",
                   (h[0], h[1], h[2], h[3], h[4], h[5], int(h[6]), ts_seed))
    for sid, mid, dom, iz, sk, al, ov in hilang_att:
        ov_val = None if ov == "null" else int(ov)
        db.execute("""insert into public.attendance
            (student_id, month_id, domain, izin, sakit, alpha, effective_days_override, entered_at, entered_by)
            values (%s,%s,%s,%s,%s,%s,%s,%s,null) on conflict (student_id,month_id,domain) do nothing""",
                   (sid, mid, dom, int(iz), int(sk), int(al), ov_val, ts_seed))
    for key, _, baru in beda_att:
        db.execute("""update public.attendance set izin=%s, sakit=%s, alpha=%s,
                      effective_days_override=%s where student_id=%s and month_id=%s and domain=%s""",
                   baru + key)
    for key in jejak_att:
        db.execute("""update public.attendance set entered_at=%s, entered_by=null, updated_by=null,
                      updated_at=null where student_id=%s and month_id=%s and domain=%s""", (ts_seed,) + key)
    for (pid,) in jejak_prog:
        db.execute("""update public.progress_entries set entered_at=%s, updated_by=null, updated_at=null
                      where id=%s""", (ts_seed, pid))

    print("SELESAI. Verifikasi:")
    print("  capaian:", db.execute("select count(*) from public.progress_entries").fetchone()[0], "(harus 2039)")
    print("  kehadiran:", db.execute("select domain, count(*) from public.attendance group by 1 order by 1").fetchall(),
          "(harus alquran 606 / wasilah 756 / ghayah 749)")
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
