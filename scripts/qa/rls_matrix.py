#!/usr/bin/env python3
"""
Matriks RLS KUSAFA: role x tabel x operasi (pola docs/SPEC.md bagian 8).

Tiap probe membuat transaksi sendiri, memasang identitas pengguna
(`set local role authenticated` + JWT untuk pengguna aplikasi, atau `anon`),
menjalankan SATU operasi, lalu ROLLBACK — tidak ada data yang benar-benar
diubah. Karena `set local role` berlaku per transaksi, setiap probe diisolasi;
hasil bertambah sebagai baris:
    role | tabel | operasi | diharapkan | aktual | status

Cakupan mengikuti aturan tertulis docs/SPEC.md bagian 8:
  - semua staf membaca semua halaqah & santri; anon tidak;
  - Musyrif/ah menulis hanya halaqah Al Qur'an yang diampu; ditolak di halaqah lain;
  - Masul Al Quran menulis halaqah domainnya; Admin/Mudir menulis di mana pun;
  - pengampu ditolak menulis pada bulan terkunci; Admin/Mudir diterima;
  - penyetujuan target: Masul domain / Mudir; pengampu tidak;
  - Hari Efektif (month_domain_settings) hanya Admin/Mudir (policy is_full_access);
  - profil (role/aktif) hanya Admin/Mudir (policy is_full_access);
  - anon ditolak (tidak punya kebijakan mana pun; RLS menyembunyikan semua baris).

Catatan RLS di Supabase: tidak ada kebijakan SELECT untuk anon => baris disembunyikan
bukan galat 42501. Untuk SELECT, DITERIMA = baris yang diuji terbaca; DITOLAK = disebunyikan.

Jalankan: python scripts/qa/rls_matrix.py
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "qa" / f"rls_matrix_{datetime.date.today().isoformat()}.json"

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

baris: list[dict] = []
gagal = 0


def rec(role, tabel, operasi, diharapkan, aktual, note="") -> None:
    global gagal
    status = "OK" if diharapkan == aktual else "GAGAL"
    if aktual.startswith("SKIP"):
        status = "SKIP"
    if diharapkan != aktual and status != "SKIP":
        gagal += 1
    baris.append({"role": role, "tabel": tabel, "operasi": operasi,
                  "diharapkan": diharapkan, "aktual": aktual,
                  "status": status, "catatan": note})
    mark = "PASS" if status == "OK" else ("SKIP" if status == "SKIP" else "FAIL")
    print(f"[{mark}] {role:16} | {tabel:24} | {operasi:26} | exp={diharapkan:14} | got={aktual}")


conn = psycopg.connect(env["DATABASE_URL"], autocommit=True, connect_timeout=20)


def satu(q, params=()):
    r = conn.execute(q, params).fetchone()
    return r[0] if r else None


def probe(role, pid, sql, params=(), is_select=False):
    """Satu probe dalam transaksi terisolasi. Kembalikan status aktual."""
    conn.execute("begin")
    try:
        if role == "anon":
            conn.execute("set local role anon")
        else:
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (pid,))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        if is_select:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            return "DITERIMA" if row is not None else "DITOLAK(RLS)"
        cur = conn.execute(sql, params)
        n = cur.rowcount if cur.rowcount is not None else 0
        # UPDATE/DELETE yang disembunyikan RLS (USING false) DIAKUI BERHASIL tapi
        # memengaruhi 0 baris. 0 baris = baris sasaran tidak terlihat walasan => ditolak RLS
        # (tidak dianggap akses DITERIMA). INSERT yang di-izin-kan selalu >0 baris.
        return "DITERIMA" if n > 0 else "DITOLAK(RLS)"
    except psycopg.errors.InsufficientPrivilege:
        return "DITOLAK(RLS)"
    except Exception as e:  # noqa: BLE001
        return f"DITOLAK({type(e).__name__})"
    finally:
        conn.rollback()


ROLES = ("mudir", "admin", "masul_alquran", "masul_wasilah",
         "masul_ghayah", "musyrif", "mudarris", "wali")
PID = {}
for r in ROLES:
    has = satu("select 1 from public.profiles where role=%s and is_active limit 1", (r,))
    PID[r] = str(satu("select id from public.profiles where role=%s and is_active "
                      "order by full_name limit 1", (r,))) if has else None
PID["anon"] = None  # anon tidak ada profil; identitas = peran database `anon`

# ------------------------------------------------------------------ konteks (sebagai postgres)
hlq_ampu = satu("select h.id from public.halaqah_teachers ht join public.halaqahs h on h.id=ht.halaqah_id "
                "where h.domain='alquran' and ht.profile_id=%s limit 1", (PID["musyrif"],))
hlq_lain = satu("select id from public.halaqahs where domain='alquran' and is_active and id<>%s "
                "order by code limit 1", (hlq_ampu,))
st_ampu = satu("select student_id from public.halaqah_members where halaqah_id=%s and left_on is null "
               "limit 1", (hlq_ampu,))
st_lain = satu("select student_id from public.halaqah_members where halaqah_id=%s and left_on is null "
               "limit 1", (hlq_lain,))
bulan_syawal = satu("select id from public.hijri_months where month_no=1 limit 1")
sub_alquran = satu("select id from public.subjects where domain='alquran' order by sort_order limit 1")
item_alquran = satu(
    "select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
    "where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (sub_alquran,))
sub_gh = satu("select id from public.subjects where domain='ghayah' order by sort_order limit 1")
target_gh = satu("select id from public.targets where subject_id=%s and status='diajukan' "
                 "order by id limit 1", (sub_gh,))

# ---------------------------------------------------------------- 1. BACA baris konkret
READ_PROBE = {
    "students": f"select full_name from public.students where id='{st_ampu}'",
    "halaqahs": f"select code from public.halaqahs where id='{hlq_ampu}'",
    "progress_entries": f"select 1 from public.progress_entries where student_id='{st_ampu}' limit 1",
}
ROLE_READ_OK = ("mudir", "admin", "masul_alquran", "masul_wasilah",
                "masul_ghayah", "musyrif", "mudarris")
for role in (*ROLE_READ_OK, "wali", "anon"):
    exp = "DITERIMA" if role in ROLE_READ_OK else "DITOLAK(RLS)"
    if PID[role] is None and role != "anon":
        for tbl in READ_PROBE:
            rec(role, tbl, "select", exp, "SKIP(no profil)")
        continue
    for tbl, sql in READ_PROBE.items():
        rec(role, tbl, "select", exp, probe(role, PID[role], sql, is_select=True))

# ---------------------------------------------------------------- 2. WRITE progress_entries
INS_PROG = ("insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran) "
            "values (%s,%s,%s,%s,1)")
rec("musyrif", "progress_entries", "insert(halaqah sendiri)", "DITERIMA",
    probe("musyrif", PID["musyrif"], INS_PROG, (st_ampu, bulan_syawal, sub_alquran, item_alquran)))
rec("musyrif", "progress_entries", "insert(halaqah lain)", "DITOLAK(RLS)",
    probe("musyrif", PID["musyrif"], INS_PROG, (st_lain, bulan_syawal, sub_alquran, item_alquran)))
for role, exp in (("mudir", "DITERIMA"), ("admin", "DITERIMA")):
    rec(role, "progress_entries", "insert", exp,
        probe(role, PID[role], INS_PROG, (st_lain, bulan_syawal, sub_alquran, item_alquran)))
# Masul Al Quran (T6d2, keputusan Mudir 25 Nov 2026): boleh input di SEMUA halaqah Al Qur'an,
# termasuk halaqah yang tidak dicatat sebagai ampuannya. Domain lain tetap ditolak (diuji di atas).
rec("masul_alquran", "progress_entries", "insert(halaqah tak diampu oleh profil uji)", "DITERIMA",
    probe("masul_alquran", PID["masul_alquran"], INS_PROG, (st_lain, bulan_syawal, sub_alquran, item_alquran)))

# Masul Wasilah/Masul Ghayah = penanggung jawab domain (keputusan Mudir 25 Nov 2026, T6b).
# Mereka boleh menulis capaian di domainnya walau bukan pengampu mapel itu; domain lain ditolak.
sub_was = satu("select id from public.subjects where domain='wasilah' order by sort_order limit 1")
item_was = satu(
    "select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
    "where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (sub_was,))
sub_gh2 = satu("select id from public.subjects where domain='ghayah' order by sort_order limit 1")
item_gh = satu(
    "select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
    "where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (sub_gh2,))
# T6d2 (keputusan Mudir 25 Nov 2026): KETIGA Masul boleh input di SEMUA halaqah domainnya.
for role, sub, item, exp in (
    ("masul_wasilah", sub_was, item_was, "DITERIMA"),
    ("masul_wasilah", sub_gh2, item_gh, "DITOLAK(RLS)"),
    ("masul_ghayah", sub_gh2, item_gh, "DITERIMA"),
    ("masul_ghayah", sub_was, item_was, "DITOLAK(RLS)"),
    ("masul_alquran", sub_alquran, item_alquran, "DITERIMA"),
    ("masul_alquran", sub_was, item_was, "DITOLAK(RLS)"),
    ("musyrif", sub_was, item_was, "DITOLAK(RLS)"),
):
    nama_domain = ("alquran" if sub == sub_alquran else "wasilah" if sub == sub_was else "ghayah")
    rec(role, "progress_entries", f"insert(domain {nama_domain})", exp,
        probe(role, PID[role], INS_PROG, (st_lain, bulan_syawal, sub, item)))

# Kehadiran & catatan: Masul domainnya DITERIMA di halaqah yang bukan ampuannya;
# domain lain DITOLAK; pengampu (musyrif) tetap DITOLAK di halaqah lain.
INS_ATT_W = ("insert into public.attendance (student_id,month_id,domain,izin,sakit,alpha) "
             "values (%s,%s,%s,0,0,0) on conflict (student_id,month_id,domain) do update set izin=0")
INS_NOTE_W = ("insert into public.monthly_notes (student_id,month_id,domain,note) "
              "values (%s,%s,%s,'uji rls') on conflict (student_id,month_id,domain) do update set note='uji rls'")
for role, dom, exp in (
    ("masul_alquran", "alquran", "DITERIMA"),
    ("masul_alquran", "wasilah", "DITOLAK(RLS)"),
    ("masul_wasilah", "wasilah", "DITERIMA"),
    ("masul_wasilah", "ghayah", "DITOLAK(RLS)"),
    ("masul_ghayah", "ghayah", "DITERIMA"),
    ("masul_ghayah", "alquran", "DITOLAK(RLS)"),
    ("musyrif", "wasilah", "DITOLAK(RLS)"),
):
    rec(role, "attendance", f"insert(domain {dom})", exp,
        probe(role, PID[role], INS_ATT_W, (st_lain, bulan_syawal, dom)))
    rec(role, "monthly_notes", f"insert(domain {dom})", exp,
        probe(role, PID[role], INS_NOTE_W, (st_lain, bulan_syawal, dom)))

# Hapus: hanya Mudir/Admin. Masul & pengampu ditolak.
#
# Baris sasaran dibuat DI DALAM transaksi probe (sebelum SET ROLE) lalu ikut di-ROLLBACK,
# supaya uji ini tidak meninggalkan baris capaian/kehadiran di database. Sebelumnya baris
# sasaran di-COMMIT lebih dulu, dan 1 baris capaian Wasilah tertinggal di data produksi.
INS_PROG_W = ("insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran) "
              "values (%s,%s,%s,%s,1) on conflict (student_id,subject_id,month_id) do update set putaran=excluded.putaran")


def probe_hapus(role, pid, siapkan_sql, siapkan_params, sql, params):
    """Siapkan baris sasaran sebagai postgres, lalu coba HAPUS sebagai role. Selalu ROLLBACK."""
    conn.execute("begin")
    try:
        conn.execute(siapkan_sql, siapkan_params)
        if role == "anon":
            conn.execute("set local role anon")
        else:
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (pid,))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        cur = conn.execute(sql, params)
        n = cur.rowcount if cur.rowcount is not None else 0
        return "DITERIMA" if n > 0 else "DITOLAK(RLS)"
    except psycopg.errors.InsufficientPrivilege:
        return "DITOLAK(RLS)"
    except Exception as e:  # noqa: BLE001
        return f"DITOLAK({type(e).__name__})"
    finally:
        conn.rollback()


for role, exp in (("masul_wasilah", "DITOLAK(RLS)"), ("masul_alquran", "DITOLAK(RLS)"),
                  ("musyrif", "DITOLAK(RLS)"), ("mudir", "DITERIMA")):
    rec(role, "progress_entries", "delete", exp,
        probe_hapus(role, PID[role], INS_PROG_W, (st_lain, bulan_syawal, sub_was, item_was),
                    "delete from public.progress_entries where student_id=%s and month_id=%s "
                    "and subject_id=%s", (st_lain, bulan_syawal, sub_was)))
    rec(role, "attendance", "delete", exp,
        probe_hapus(role, PID[role], INS_ATT_W, (st_lain, bulan_syawal, "wasilah"),
                    "delete from public.attendance where student_id=%s and month_id=%s and domain='wasilah'",
                    (st_lain, bulan_syawal)))

# ---------------------------------------------------------------- 3. attendance pada bulan terkunci
INS_ATT = ("insert into public.attendance (student_id,month_id,domain,izin,sakit,alpha) "
           "values (%s,%s,'alquran',0,0,0)")
# kunci bulan Syawwal domain alquran sekali (transaksi terpisah, sebagai postgres)
conn.execute("begin")
conn.execute("update public.month_domain_settings set is_locked=true where month_id=%s and domain='alquran'",
             (bulan_syawal,))
conn.commit()
for role, exp in (("musyrif", "DITOLAK(RLS)"), ("masul_alquran", "DITOLAK(RLS)"),
                  ("admin", "DITERIMA")):
    rec(role, "attendance", "insert(bulan terkunci)", exp,
        probe(role, PID[role], INS_ATT, (st_ampu, bulan_syawal)))
# kembalikan (biar tidak mengotori DB nyata)
conn.execute("update public.month_domain_settings set is_locked=false where month_id=%s and domain='alquran'",
             (bulan_syawal,))
conn.commit()

# ---------------------------------------------------------------- 4. Hari Efektif (month_domain_settings)
for role, exp in (("musyrif", "DITOLAK(RLS)"), ("masul_alquran", "DITOLAK(RLS)"),
                  ("admin", "DITERIMA"), ("mudir", "DITERIMA")):
    rec(role, "month_domain_settings", "update(Hari Efektif)", exp,
        probe(role, PID[role], "update public.month_domain_settings set effective_days=19 "
              "where month_id=%s and domain=%s", (bulan_syawal, "alquran")))

# ---------------------------------------------------------------- 5. targets (setujui)
for role, exp in (
    ("musyrif", "DITOLAK(RLS)"),
    ("masul_wasilah", "DITOLAK(RLS)"),    # domain salah utk target ghayah
    ("masul_alquran", "DITOLAK(RLS)"),    # domain salah
    ("masul_ghayah", "DITERIMA"),
    ("mudir", "DITERIMA"),
):
    if not target_gh:
        rec(role, "targets", "update(status disetujui)", exp, "SKIP(no target diajukan)")
        continue
    rec(role, "targets", "update(status disetujui)", exp,
        probe(role, PID[role], "update public.targets set status='disetujui' where id=%s", (target_gh,)))

# ---------------------------------------------------------------- 6. profiles (role/aktif)
other = satu("select id from public.profiles where role<>'admin' and is_active limit 1")
rec("musyrif", "profiles", "update(role user lain)", "DITOLAK(RLS)",
    probe("musyrif", PID["musyrif"], "update public.profiles set is_active=true where id=%s", (other,)))
rec("admin", "profiles", "update(role user lain)", "DITERIMA",
    probe("admin", PID["admin"], "update public.profiles set is_active=true where id=%s", (other,)))

# ---------------------------------------------------------------- ringkasan
conn.close()
ok = sum(1 for b in baris if b["status"] == "OK")
skip = sum(1 for b in baris if b["status"] == "SKIP")
ska = sum(1 for b in baris if b["status"] == "GAGAL")
ringkasan = {"total": len(baris), "ok": ok, "skip": skip, "gagal": ska,
             "ran_at": datetime.datetime.now().isoformat()}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"ringkasan": ringkasan, "baris": baris}, indent=2, default=str,
                          ensure_ascii=False), encoding="utf-8")
print(f"\n=== RINGKASAN: {ok}/{len(baris)} OK, {skip} SKIP, {ska} GAGAL. Laporan: {OUT}")
sys.exit(1 if ska else 0)