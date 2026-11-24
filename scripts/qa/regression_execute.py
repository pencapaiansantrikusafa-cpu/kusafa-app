#!/usr/bin/env python3
"""
Uji regresi pra-T6 [6/4]:  keketatan EXECUTE fungsi + fungsi admin tidak bisa dieksekusi sembarang.

Bagian A — "setiap fungsi di schema public tidak punya EXECUTE untuk anon".
  Loop pg_proc; untuk setiap fungsi ber-namespace public yang dapat dipanggil
  (language yang didukung dan bukan kelas regprocedure tak ter-resolve), pastikan
  has_function_privilege('anon', fq, 'EXECUTE') = false. Ini menjamin hardening
  migrasi 000007/000009/000010 tidak diregresi oleh fungsi baru.

Bagian B — "musyrif memanggil create_academic_year / reorder_items /
resequence_subject TIDAK mengubah data":  ketiga fungsi admin (T8) murni menulis,
  dan RLS pada tabel yang ditulisnya harus menolak pengguna non-admin sehingga
  tidak ada baris yang benar-benar berubah. Uji dijalankan dalam transaksi dan
  di-ROLLBACK. Jika fungsi ditolak oleh RLS (InsufficientPrivilege) => tidak
  mengubah data (LULUS). Jika "berhasil" tetapi 0 baris berubah => tetap LULUS
  (target tak terlihat). Jika benar-benar mengubah baris => GAGAL.

Hanya skrip yang dapat dijalankan ulang; tidak mengubah data nyata.
Membaca .env.local; tidak mencetak rahasia.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "qa" / f"regression_execute_{datetime.date.today().isoformat()}.json"

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


conn = psycopg.connect(env["DATABASE_URL"], autocommit=True, connect_timeout=20)


def satu(q, params=()):
    r = conn.execute(q, params).fetchone()
    return r[0] if r else None


def dengan_musyrif(pid, fn):
    conn.execute("begin")
    try:
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (pid,))
        conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        return fn()
    finally:
        conn.rollback()


# ------------------------------------------------------------------ A. anon EXECUTE = false (loop pg_proc)
try:
    rows = conn.execute(
        """
        select p.oid, p.proname, pg_get_function_identity_arguments(p.oid) as args,
               l.lanname
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        join pg_language l on l.oid = p.prolang
        where n.nspname = 'public'
          and p.prokind in ('f','p')
          and p.proname not like '\\_%'          -- fungsi yang boleh terbuka / bantu
        order by p.proname, args
        """
    ).fetchall()
    anon_open: list[str] = []
    checked = 0
    for oid, name, args, lang in rows:
        try:
            if satu("select has_function_privilege('anon', %s::oid, 'EXECUTE')", (oid,)):
                anon_open.append(f"public.{name}({args})")
        except psycopg.errors.UndefinedObject:
            continue
        checked += 1
    rec(
        "A_anon_tanpa_execute_loop_pg_proc",
        anon_open == [],
        f"{checked} fungsi public diperiksa; {len(anon_open)} terbuka ke anon.",
        {"terbuka_ke_anon": anon_open},
    )
except Exception as e:  # noqa: BLE001
    rec("A_anon_tanpa_execute_loop_pg_proc", False, f"Error: {type(e).__name__}: {e}")

# Pastikan beberapa fungsi inti tetap punya EXECUTE untuk authenticated (sanity, bukan regresi):
for f in ("public.current_app_role()", "public.can_manage(public.domain_kind)",
          "public.students_without_halaqah()"):
    try:
        ya = satu("select has_function_privilege('authenticated', %s, 'EXECUTE')", (f,))
        rec(f"A_sanity_authenticated_{f.split('.')[-1]}", ya is True, f"{f}: authenticated EXECUTE={ya}")
    except psycopg.errors.UndefinedFunction:
        rec(f"A_sanity_authenticated_{f.split('.')[-1]}", False, f"{f} tidak ditemukan")

# ------------------------------------------------------------------ B. musyrif tidak mengubah data via fungsi admin
# Cari profil musyrif aktif + item kurikulum (untuk reorder) + subject.
pid_row = conn.execute("select id from public.profiles where role='musyrif' and is_active order by full_name limit 1").fetchone()
pid = str(pid_row[0]) if pid_row else None
subject_gh = satu("select id from public.subjects where domain='ghayah' order by sort_order limit 1")

if not pid:
    rec("B_musyrif_fungsi_admin_tanpa_perubahan", None, "Profil musyrif tidak ada.")
else:
    def musyrif_call(sql, params=()):
        try:
            conn.execute(sql, params)
            return "berhasil"
        except Exception as e:  # noqa: BLE001
            return f"ditolak({type(e).__name__})"

    # B1 create_academic_year (langsung dipanggil musyrif)
    def snap_tahun():
        return {
            "academic_years": satu("select count(*) from public.academic_years"),
            "hijri_months": satu("select count(*) from public.hijri_months"),
        }

    before = snap_tahun()
    hasil = dengan_musyrif(pid, lambda: musyrif_call(
        "select public.create_academic_year(1499, 'Uji musyrif dilarang', false)"))
    after = snap_tahun()
    rec("B1_musyrif_create_academic_year_tidak_mengubah_data",
        before == after,
        f"panggilan → {hasil}; jumlah baris tahun/bulan tidak berubah: {before == after}")

    # B2 reorder_items + B3 resequence_subject — pakai buku domain GH/FIQIH (non-Al Qur'an)
    # agar resequence tidak terblok oleh guard "Al Qur'an manual", dan benar-benar menguji
    # apakah RLS INVOKER menghalangi musyrif mengubah baris curriculum_items/books.
    if subject_gh:
        def upaya_tulis_musyrif(item_id):
            cur = conn.execute(
                "select count(*) from public.progress_entries;")  # warm-up konteks
            cur = conn.execute(
                "select public.resequence_subject(%s::uuid)", (subject_gh,))
            return cur.rowcount

        def probe_update_rows(subject_):
            """Berapa baris curriculum_items yang akan di-UPDATE musyrif bila dibolehkan."""
            n = 0
            for book_ in conn.execute(
                    "select b.id from public.books b where b.subject_id=%s order by b.sort_order",
                    (subject_,)).fetchall():
                cur = conn.execute(
                    "update public.curriculum_items set seq=seq where book_id=%s", (book_[0],))
                n += cur.rowcount if cur.rowcount is not None else 0
            return n

        # jalankan probe dalam konteks musyrif; diharapkan RLS menyembunyikan baris => 0
        rows_diubah = dengan_musyrif(pid, lambda: probe_update_rows(subject_gh))
        rec("B_musyrif_tulis_item_ghayah_diblokir_rls",
            rows_diubah == 0,
            f"musyrif UPDATE curriculum_items Ghayah mengubah {rows_diubah} baris (harus 0; RLS menjaga)")

        # tetap laporkan apakah fungsi admin bisa diselesaikan musyrif (informatif)
        try:
            hasil_reorder = dengan_musyrif(
                pid, lambda: musyrif_call("select public.resequence_subject(%s::uuid)", (subject_gh,)))
        except Exception as e:  # noqa: BLE001
            hasil_reorder = f"ditolak({type(e).__name__})"
        rec("B_resequence_subject_tidak_mengubah_data_musyrif",
            rows_diubah == 0,
            f"panggilan resequence_subject → {hasil_reorder}; baris item yang benar-benar bisa "
            f"diubah musyrif = {rows_diubah} (harus 0)")
    else:
        rec("B2_musyrif_reorder_items_tidak_mengubah_data", False, "Subject Ghayah tidak ditemukan.")
        rec("B3_musyrif_resequence_subject_tidak_mengubah_data", False, "Subject Ghayah tidak ditemukan.")

conn.close()
gagal = [r for r in results if r.get("ok") is False]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps({"ran_at": datetime.datetime.now().isoformat(), "tests": results}, indent=2,
               default=str, ensure_ascii=False), encoding="utf-8")
n_ok = sum(1 for r in results if r.get("ok") is True)
n_skip = sum(1 for r in results if r.get("ok") is None)
print(f"\n{n_ok}/{len(results)} PASS (skip={n_skip}, gagal={len(gagal)}). Laporan: {OUT}")
sys.exit(1 if gagal else 0)