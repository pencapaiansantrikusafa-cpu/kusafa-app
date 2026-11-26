#!/usr/bin/env python3
"""Uji T7c [1/3]: target Wasilah/Ghayah = TUJUAN AKHIR (butir kurikulum).

Semua perubahan berjalan di transaksi yang SELALU di-ROLLBACK; tidak ada data nyata
yang berubah. Tidak mencetak nama santri atau nilai data nyata.

Yang dibuktikan:
  A. Bentuk: Al Qur'an (lama 9 argumen) tetap jalan; Wasilah/Ghayah dengan amount
     ditolak jelas; butir wajib milik buku mapel itu & aktif; constraint tabel.
  B. Satu target menunggu per (halaqah, mapel, bulan); pengajuan baru menggantikan.
  C. Hak per role dan lintas domain (pengampu, 3 Masul, Mudir, Admin, anon).
  D. Bulk `setujui_target_halaqah` (per halaqah x bulan, konfirmasi bulan lewat/terkunci).
  E. `ubah_target` baris baru; panggilan lama Al Qur'an tetap jalan; pembatalan.
  F. v_monthly_report Al Qur'an identik sebelum/sesudah; rumus Al Qur'an tidak berubah.
  G. DUMMY bentuk baru ada (25 Wasilah + 11 Ghayah), bentuk lama 0.
  H. Tidak ada overload fungsi target (penyebab HTTP 300 PGRST203 di produksi).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
ENV: dict[str, str] = {}
for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip().strip('"').strip("'")

c = psycopg.connect(ENV["DATABASE_URL"], autocommit=True, connect_timeout=30)
results: list[dict] = []
UUID_RE = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


def record(name: str, ok: bool, detail: str = "") -> None:
    safe = re.sub(UUID_RE, "<id>", detail)[:300]
    results.append({"uji": name, "ok": bool(ok), "detail": safe})
    print(("LULUS" if ok else "GAGAL") + " | " + name + (" | " + safe if safe else ""))


def one(sql: str, args=()):
    r = c.execute(sql, args).fetchone()
    return r[0] if r else None


def rows(sql: str, args=()):
    return c.execute(sql, args).fetchall()


P = {role: str(pid) for role, pid in rows(
    "select distinct on (role) role::text, id from public.profiles "
    "where is_active order by role, full_name")}


def begin_as(role: str) -> None:
    c.execute("begin")
    switch(role)


def switch(role: str) -> None:
    c.execute("reset role")
    if role == "anon":
        c.execute("set local role anon")
    else:
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P[role],))
        c.execute("select set_config('request.jwt.claim.role','authenticated',true)")


def rollback() -> None:
    c.execute("rollback")


def call(role: str, sql: str, args=()):
    """Jalankan satu panggilan sebagai role; SELALU rollback. -> (ok, nilai, galat)."""
    begin_as(role)
    try:
        cur = c.execute(sql, args)
        return True, (cur.fetchone() if cur.description else cur.rowcount), ""
    except Exception as e:  # noqa: BLE001
        return False, None, str(e).splitlines()[0][:300]
    finally:
        rollback()


def harus_gagal(role: str, sql: str, args=(), bagian: str | None = None):
    """Panggil sebagai role; harus GAGAL. -> (ok, None, galat)."""
    ok, _, err = call(role, sql, args)
    if ok:
        return False, None, "DITERIMA (seharusnya ditolak)"
    if bagian and bagian.lower() not in err.lower():
        return False, None, "pesan tidak sesuai: " + err
    return True, None, err


roles_perlu = ("mudir", "admin", "masul_alquran", "masul_wasilah", "masul_ghayah",
               "musyrif", "mudarris")
hilang = [r for r in roles_perlu if r not in P]
if hilang:
    print("GAGAL | konteks peran | profil tidak tersedia: " + ", ".join(hilang))
    sys.exit(1)

month0 = one("select id from public.hijri_months where month_no=0 order by id limit 1")
month6 = one("select id from public.hijri_months where month_no=6 order by id limit 1")
month7 = one("select id from public.hijri_months where month_no=7 order by id limit 1")
month8 = one("select id from public.hijri_months where month_no=8 order by id limit 1")
bulan_berjalan = one("select month_no from public.hijri_months where id = public.target_bulan_berjalan('wasilah')")

subject_a = one("select id from public.subjects where domain='alquran' order by sort_order limit 1")
subject_g = one("select id from public.subjects where domain='ghayah' order by sort_order limit 1")
item_a = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
             "where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (subject_a,))
item_g = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
             "where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (subject_g,))
halaqah_g = one("select h.id from public.halaqahs h join public.halaqah_subjects hs on hs.halaqah_id=h.id "
                "where h.domain='ghayah' and hs.subject_id=%s order by h.code limit 1", (subject_g,))

# Halaqah Wasilah dengan mapel TERBANYAK (Level Dasar A, 3 mapel) untuk uji bulk.
halaqah_w = one("""select hs.halaqah_id from public.halaqah_subjects hs
  join public.halaqahs h on h.id=hs.halaqah_id
  where h.domain='wasilah' group by hs.halaqah_id
  order by count(*) desc, hs.halaqah_id limit 1""")
mapel_w = [r[0] for r in rows(
    "select subject_id from public.halaqah_subjects where halaqah_id=%s order by subject_id",
    (halaqah_w,))]
subject_w1, subject_w2 = mapel_w[0], mapel_w[1]
item_w1 = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
              "where b.subject_id=%s and ci.is_active order by b.sort_order, ci.seq limit 1", (subject_w1,))
item_w2 = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
              "where b.subject_id=%s and ci.is_active order by b.sort_order, ci.seq limit 1", (subject_w2,))
item_w1b = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
               "where b.subject_id=%s and ci.is_active and ci.id<>%s order by b.sort_order, ci.seq limit 1",
               (subject_w1, item_w1))
# Mapel Wasilah yang TIDAK ditetapkan untuk halaqah itu, beserta butirnya.
subject_w_luar = one("""select s.id from public.subjects s where s.domain='wasilah'
  and not exists (select 1 from public.halaqah_subjects hs
                  where hs.halaqah_id=%s and hs.subject_id=s.id)
  order by s.sort_order limit 1""", (halaqah_w,))
item_w_luar = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
                  "where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (subject_w_luar,))
# Halaqah Wasilah lain (bukan halaqah_w) untuk uji "bukan halaqah ampuanku".
halaqah_w2 = one("select distinct hs.halaqah_id from public.halaqah_subjects hs "
                 "join public.halaqahs h on h.id=hs.halaqah_id "
                 "where h.domain='wasilah' and hs.halaqah_id<>%s order by 1 limit 1", (halaqah_w,))
subject_w2b = one("select subject_id from public.halaqah_subjects where halaqah_id=%s limit 1", (halaqah_w2,))
item_w2b = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id "
               "where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (subject_w2b,))

# Al Qur'an: halaqah & santri ampuanku (Musyrif/ah).
ampu_h = one("select h.id from public.halaqah_teachers ht join public.halaqahs h on h.id=ht.halaqah_id "
             "where ht.profile_id=%s and h.domain='alquran' order by h.code limit 1", (P["musyrif"],))
ampu_st = one("select student_id from public.halaqah_members where halaqah_id=%s "
              "and left_on is null order by student_id limit 1", (ampu_h,))

wajib = {
    "month0": month0, "month6": month6, "month7": month7, "month8": month8,
    "subject_a": subject_a, "subject_g": subject_g, "item_a": item_a, "item_g": item_g,
    "halaqah_g": halaqah_g, "halaqah_w": halaqah_w, "mapel_w2": subject_w2,
    "item_w1": item_w1, "item_w1b": item_w1b, "item_w2": item_w2, "item_w_luar": item_w_luar,
    "halaqah_w2": halaqah_w2, "item_w2b": item_w2b, "ampu_h": ampu_h, "ampu_st": ampu_st,
}
kosong = [k for k, v in wajib.items() if v is None]
if kosong or bulan_berjalan != 7:
    print("GAGAL | konteks database | kosong: " + ", ".join(kosong) +
          f"; bulan berjalan Wasilah={bulan_berjalan} (harus 7)")
    sys.exit(1)

AJUKAN_A = ("select public.ajukan_target('alquran',%s,%s,null,%s,%s::numeric,"
            "'harian'::target_period,%s,false,%s)")
# Panggilan 9 argumen (bentuk produksi lama). Lewat PostgREST namanya dicocokkan
# sehingga parameter 10 (butir) memakai nilai bawaannya; lewat SQL langsung butuh
# tipe eksplisit karena psycopg mengirim double precision untuk angka.
AJUKAN_A_LAMA = ("select public.ajukan_target('alquran',%s,%s,null,%s,%s::numeric,"
                 "'harian'::target_period,%s,false)")
AJUKAN_W = "select public.ajukan_target('wasilah',%s,null,%s,%s,null::numeric,'bulanan',%s,false,%s)"
AJUKAN_W_LAMA = ("select public.ajukan_target('wasilah',%s,null,%s,%s,"
                 "%s::numeric,'bulanan',%s,false)")
AJUKAN_G = "select public.ajukan_target('ghayah',%s,null,%s,%s,null::numeric,'bulanan',%s,false,%s)"


# ---------------------------------------------------------------- A. BENTUK
ok, val, err = call("musyrif", AJUKAN_A_LAMA, (subject_a, ampu_st, month7, 0.75, "uji t7c"))
record("A1 panggilan LAMA Al Qur'an (9 argumen, tanpa butir) tetap berhasil",
       ok and val and val[0]["status"] == "diajukan" and val[0]["target_item_id"] is None,
       err or f"status={val[0]['status'] if val else None}")

ok, val, err = harus_gagal("mudir", AJUKAN_A, (subject_a, ampu_st, month7, 2, "uji t7c", item_a),
                           "bukan butir")
record("A2 Al Qur'an dengan butir kurikulum ditolak", ok, err)

ok, val, err = harus_gagal("mudir", AJUKAN_A, (subject_a, ampu_st, month7, None, "uji t7c", None),
                           "wajib diisi")
record("A3 Al Qur'an tanpa jumlah ditolak", ok, err)

ok, val, err = harus_gagal("mudir", AJUKAN_W_LAMA,
                           (subject_w1, halaqah_w, month7, 1, "uji t7c"), "butir kurikulum")
record("A4 Wasilah bentuk LAMA (amount, tanpa butir) ditolak dengan pesan jelas", ok, err)

ok, val, err = harus_gagal("mudir",
                           "select public.ajukan_target('wasilah',%s,null,%s,%s,%s,'bulanan',%s,false,%s)",
                           (subject_w1, halaqah_w, month7, 1, "uji t7c", item_w1), "bukan jumlah")
record("A5 Wasilah dengan amount DAN butir ditolak", ok, err)

ok, val, err = harus_gagal("mudir", AJUKAN_W, (subject_w1, halaqah_w, month7, "uji t7c", item_w_luar),
                           "milik buku mata pelajaran")
record("A6 Butir milik mapel LAIN ditolak", ok, err)

# Butir nonaktif: dinonaktifkan hanya di transaksi.
c.execute("begin")
try:
    c.execute("update public.curriculum_items set is_active=false where id=%s", (item_w1,))
    switch("mudir")
    try:
        c.execute(AJUKAN_W, (subject_w1, halaqah_w, month7, "uji t7c", item_w1))
        record("A7 Butir NONAKTIF ditolak", False, "DITERIMA (seharusnya ditolak)")
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        record("A7 Butir NONAKTIF ditolak", "milik buku mata pelajaran ini dan aktif" in msg,
               msg.splitlines()[0][:180])
finally:
    rollback()

ok, val, err = harus_gagal("mudir",
                           "select public.ajukan_target('wasilah',%s,%s,%s,%s,null,'bulanan',%s,false,%s)",
                           (subject_w1, ampu_st, halaqah_w, month7, "uji t7c", item_w1), "per halaqah")
record("A8 Wasilah per SANTRI ditolak", ok, err)

ok, val, err = harus_gagal("mudir", AJUKAN_W,
                           (subject_w_luar, halaqah_w, month7, "uji t7c", item_w_luar),
                           "tidak ditetapkan untuk halaqah")
record("A9 Mapel yang tidak ditetapkan halaqah ditolak", ok, err)

c.execute("begin")
try:
    switch("mudir")
    ok, val, err = ("ok", c.execute(AJUKAN_W, (subject_w1, halaqah_w, month7, "uji t7c", item_w1)).fetchone()[0], "")
    record("A10 Wasilah bentuk baru (butir, tanpa amount) diterima & otomatis disetujui",
           val["status"] == "disetujui" and val["target_item_id"] == str(item_w1),
           f"status={val['status']}")
    row = c.execute("select amount, target_item_id = %s from public.targets where id=%s",
                    (item_w1, val["id"],)).fetchone()
    record("A11 Baris Wasilah tersimpan: amount KOSONG, butir terisi",
           row is not None and row[0] is None and row[1] is True, str(row))
finally:
    rollback()

ok, val, err = call("mudir", AJUKAN_G, (subject_g, halaqah_g, month7, "uji t7c", item_g))
record("A12 Ghayah bentuk baru diterima", ok and val and val[0]["status"] == "disetujui", err)

c.execute("begin")
try:
    c.execute("savepoint a13")
    try:
        c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,"
                  "amount,amount_period,status) values ('wasilah',%s,%s,%s,1,'bulanan','disetujui')",
                  (subject_w1, halaqah_w, month7))
        record("A13 Constraint menolak INSERT langsung bentuk lama (amount=1)", False, "DITERIMA")
        c.execute("rollback to savepoint a13")
    except psycopg.errors.CheckViolation:
        record("A13 Constraint menolak INSERT langsung bentuk lama (amount=1)", True,
               "targets_bentuk_check")
        c.execute("rollback to savepoint a13")
    c.execute("savepoint a14")
    try:
        c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,"
                  "amount,amount_period,status,target_item_id) values "
                  "('wasilah',%s,%s,%s,2,'bulanan','disetujui',%s)",
                  (subject_w1, halaqah_w, month7, item_w1))
        record("A14 Constraint menolak amount DAN butir sekaligus", False, "DITERIMA")
    except psycopg.errors.CheckViolation:
        record("A14 Constraint menolak amount DAN butir sekaligus", True, "targets_bentuk_check")
finally:
    rollback()

# ------------------------------------------------- B. SATU TARGET MENUNGGU
c.execute("begin")
try:
    c.execute("insert into public.halaqah_teachers(halaqah_id,profile_id) values (%s,%s)",
              (halaqah_w, P["mudarris"]))
    switch("mudarris")
    r1 = c.execute(AJUKAN_W, (subject_w1, halaqah_w, month7, "uji t7c", item_w1)).fetchone()[0]
    r2 = c.execute(AJUKAN_W, (subject_w1, halaqah_w, month7, "uji ganti", item_w1b)).fetchone()[0]
    lama = c.execute("select status from public.targets where id=%s", (r1["id"],)).fetchone()[0]
    tunggu = one("select count(*) from public.targets where halaqah_id=%s and subject_id=%s "
                 "and effective_month_id=%s and status='diajukan'",
                 (halaqah_w, subject_w1, month7))
    baru_beda = c.execute("select target_item_id from public.targets where id=%s", (r2["id"],)).fetchone()[0]
    record("B1 Pengajuan baru MENGGANTIKAN yang masih diajukan (lama dibatalkan)",
           r2["digantikan"] == 1 and lama == "dibatalkan" and tunggu == 1 and str(baru_beda) == str(item_w1b),
           f"digantikan={r2['digantikan']}, lama={lama}, diajukan={tunggu}")
finally:
    rollback()

c.execute("begin")
try:
    c.execute("delete from public.targets where halaqah_id=%s and subject_id=%s "
              "and effective_month_id=%s and status='diajukan'", (halaqah_w, subject_w1, month7))
    c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,status,"
              "amount_period,target_item_id) values "
              "('wasilah',%s,%s,%s,'diajukan','bulanan',%s)", (subject_w1, halaqah_w, month7, item_w1))
    try:
        c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,status,"
                  "amount_period,target_item_id) values "
                  "('wasilah',%s,%s,%s,'diajukan','bulanan',%s)",
                  (subject_w1, halaqah_w, month7, item_w1b))
        record("B2 Unique index: dua target diajukan untuk kunci sama ditolak", False, "DITERIMA")
    except psycopg.errors.UniqueViolation:
        record("B2 Unique index: dua target diajukan untuk kunci sama ditolak", True,
               "targets_satu_diajukan_uk")
finally:
    rollback()

# ------------------------------------------------- C. HAK PER ROLE
def ajukan_sebagai_pengampu():
    """Pengampu (Mudarris/ah) mengajukan Wasilah; kembalikan id target 'diajukan'."""
    c.execute("insert into public.halaqah_teachers(halaqah_id,profile_id) values (%s,%s)",
              (halaqah_w, P["mudarris"]))
    switch("mudarris")
    return c.execute(AJUKAN_W, (subject_w1, halaqah_w, month7, "uji t7c", item_w1)).fetchone()[0]


c.execute("begin")
try:
    r = ajukan_sebagai_pengampu()
    try:
        c.execute("select public.setujui_target(%s,false)", (r["id"],))
        record("C1 Pengampu mengajukan (diajukan) dan TIDAK dapat menyetujui", False,
               "persetujuan diterima")
    except Exception as e:  # noqa: BLE001
        record("C1 Pengampu mengajukan (diajukan) dan TIDAK dapat menyetujui",
               r["status"] == "diajukan" and "Masul" in str(e), f"status={r['status']}")
finally:
    rollback()

for role, harus in (("masul_wasilah", True), ("masul_ghayah", False), ("masul_alquran", False)):
    c.execute("begin")
    try:
        r = ajukan_sebagai_pengampu()
        switch(role)
        try:
            st = c.execute("select public.setujui_target(%s,false)->>'status'", (r["id"],)).fetchone()[0]
            diterima = st == "disetujui"
        except Exception:  # noqa: BLE001
            diterima = False
        record(f"C2 {role} menyetujui target Wasilah", diterima == harus,
               "diterima" if diterima else "ditolak")
    finally:
        rollback()

ok, val, err = call("masul_wasilah", AJUKAN_W, (subject_w2, halaqah_w, month7, "uji t7c", item_w2))
record("C3 Masul Wasilah mengajukan sendiri -> otomatis disetujui",
       ok and val and val[0]["status"] == "disetujui", err)

ok, val, err = harus_gagal("masul_ghayah", AJUKAN_W,
                           (subject_w1, halaqah_w, month7, "uji t7c", item_w1), "tidak berhak")
record("C4 Masul Ghayah ditolak mengajukan target Wasilah", ok, err)

for role in ("mudir", "admin"):
    ok, val, err = call(role, AJUKAN_W, (subject_w1, halaqah_w, month7, "uji t7c", item_w1))
    record(f"C5 {role} mengajukan Wasilah -> otomatis disetujui",
           ok and val and val[0]["status"] == "disetujui", err)

ok, val, err = harus_gagal("masul_wasilah", AJUKAN_G,
                           (subject_g, halaqah_g, month7, "uji t7c", item_g), "tidak berhak")
record("C6 Masul Wasilah ditolak mengajukan target Ghayah", ok, err)

c.execute("begin")
try:
    c.execute("insert into public.halaqah_teachers(halaqah_id,profile_id) values (%s,%s)",
              (halaqah_w, P["mudarris"]))
    switch("mudarris")
    try:
        c.execute(AJUKAN_W, (subject_w2b, halaqah_w2, month7, "uji t7c", item_w2b))
        record("C7 Pengampu ditolak mengajukan untuk halaqah BUKAN ampuannya", False, "DITERIMA")
    except Exception as e:  # noqa: BLE001
        record("C7 Pengampu ditolak mengajukan untuk halaqah BUKAN ampuannya",
               "tidak berhak" in str(e), str(e)[:180])
finally:
    rollback()

ok, _, err = call("anon", AJUKAN_W, (subject_w1, halaqah_w, month7, "uji t7c", item_w1))
record("C8 Anon TIDAK dapat memanggil RPC target", not ok, err)

fungsi = rows("""select p.oid::regprocedure::text from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and (left(p.proname,7)='target_' or p.proname in
   ('ajukan_target','ubah_target','setujui_target','tolak_target','batalkan_target',
    'riwayat_target','setujui_target_halaqah','ajukan_target_massal_alquran'))""")
terbuka = [s for (s,) in fungsi if one("select has_function_privilege('anon',%s,'EXECUTE')", (s,))]
record("C9 Semua fungsi target tanpa EXECUTE untuk anon", terbuka == [],
       f"{len(fungsi)} fungsi; terbuka={len(terbuka)}")
publik = rows("""select p.oid::regprocedure::text from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and (left(p.proname,7)='target_' or p.proname in
   ('ajukan_target','ubah_target','setujui_target','tolak_target','batalkan_target',
    'riwayat_target','setujui_target_halaqah','ajukan_target_massal_alquran'))
    and exists (select 1 from aclexplode(coalesce(p.proacl, acldefault('f',p.proowner))) x
                where x.grantee=0 and x.privilege_type='EXECUTE')""")
record("C10 Semua fungsi target tanpa EXECUTE untuk PUBLIC", publik == [],
       f"terbuka ke PUBLIC={len(publik)}")

# ------------------------------------------------------------ D. BULK
def siapkan_dua_pengajuan():
    c.execute("insert into public.halaqah_teachers(halaqah_id,profile_id) values (%s,%s)",
              (halaqah_w, P["mudarris"]))
    switch("mudarris")
    a = c.execute(AJUKAN_W, (subject_w1, halaqah_w, month7, "uji bulk", item_w1)).fetchone()[0]
    b = c.execute(AJUKAN_W, (subject_w2, halaqah_w, month7, "uji bulk", item_w2)).fetchone()[0]
    return a["id"], b["id"]


c.execute("begin")
try:
    id1, id2 = siapkan_dua_pengajuan()
    switch("masul_wasilah")
    res = c.execute("select public.setujui_target_halaqah(%s,%s,false)",
                    (halaqah_w, month7)).fetchone()[0]
    semua = c.execute("select count(*) from public.targets where id = any(%s) and status='disetujui'",
                      ([id1, id2],)).fetchone()[0]
    record("D1 Setujui SEMUA target halaqah ini (bulk) menyetujui kedua pengajuan",
           res["jumlah"] == 2 and semua == 2, f"jumlah={res['jumlah']}")
finally:
    rollback()

c.execute("begin")
try:
    siapkan_dua_pengajuan()
    switch("masul_ghayah")
    try:
        c.execute("select public.setujui_target_halaqah(%s,%s,false)", (halaqah_w, month7))
        record("D2 Masul domain LAIN ditolak bulk", False, "DITERIMA")
    except Exception as e:  # noqa: BLE001
        record("D2 Masul domain LAIN ditolak bulk", "Masul" in str(e), str(e)[:150])
finally:
    rollback()

c.execute("begin")
try:
    siapkan_dua_pengajuan()  # dua target bulan 7
    switch("mudarris")
    c.execute(AJUKAN_W, (subject_w1, halaqah_w, month8, "uji bulk", item_w1))  # satu target bulan 8
    switch("masul_wasilah")
    res = c.execute("select public.setujui_target_halaqah(%s,%s,false)",
                    (halaqah_w, month7)).fetchone()[0]
    sisa8 = one("select count(*) from public.targets where halaqah_id=%s and effective_month_id=%s "
                "and status='diajukan'", (halaqah_w, month8))
    record("D3 Bulk per halaqah x BULAN: bulan lain tidak ikut disetujui",
           res["jumlah"] == 2 and sisa8 == 1, f"jumlah={res['jumlah']}, sisa_bulan8={sisa8}")
finally:
    rollback()

def target_menunggu_terkunci() -> None:
    c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,status,"
              "amount_period,target_item_id,proposed_by) values "
              "('wasilah',%s,%s,%s,'diajukan','bulanan',%s,%s)",
              (subject_w1, halaqah_w, month7, item_w1, P["mudarris"]))
    c.execute("insert into public.month_domain_settings(month_id,domain,effective_days,is_locked) "
              "values (%s,'wasilah',10,true) on conflict (month_id,domain) do update set is_locked=true",
              (month7,))

c.execute("begin")
try:
    target_menunggu_terkunci()
    switch("masul_wasilah")
    try:
        c.execute("select public.setujui_target_halaqah(%s,%s,false)", (halaqah_w, month7))
        record("D4 Bulan TERKUNCI: Masul ditolak tanpa konfirmasi", False, "DITERIMA")
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        record("D4 Bulan TERKUNCI: Masul ditolak tanpa konfirmasi",
               "konfirmasi" in msg.lower() or "terkunci" in msg.lower(), msg.splitlines()[0][:150])
finally:
    rollback()

c.execute("begin")
try:
    target_menunggu_terkunci()
    switch("mudir")
    res = c.execute("select public.setujui_target_halaqah(%s,%s,true)",
                    (halaqah_w, month7)).fetchone()[0]
    record("D5 Bulan TERKUNCI: Mudir dengan konfirmasi diterima", res["jumlah"] >= 1,
           f"jumlah={res['jumlah']}")
finally:
    rollback()

c.execute("begin")
try:
    siapkan_dua_pengajuan()
    switch("mudarris")
    try:
        c.execute("select public.setujui_target_halaqah(%s,%s,false)", (halaqah_w, month7))
        record("D6 Pengampu ditolak memakai bulk", False, "DITERIMA")
    except Exception as e:  # noqa: BLE001
        record("D6 Pengampu ditolak memakai bulk", "Masul" in str(e), str(e)[:150])
finally:
    rollback()

# ------------------------------------------- E. UBAH / BATALKAN (bentuk baru)
c.execute("begin")
try:
    lama = c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,status,"
                     "amount_period,target_item_id,proposed_by,approved_by,approved_at) values "
                     "('wasilah',%s,%s,%s,'disetujui','bulanan',%s,%s,%s,now()) returning id",
                     (subject_w1, halaqah_w, month6, item_w1, P["masul_wasilah"],
                      P["masul_wasilah"])).fetchone()[0]
    switch("masul_wasilah")
    try:
        c.execute("select public.ubah_target(%s,null::numeric,%s,'uji ubah',true,null::uuid)",
                  (lama, month7))
        record("E1 ubah_target Wasilah TANPA butir ditolak", False, "DITERIMA")
    except Exception as e:  # noqa: BLE001
        record("E1 ubah_target Wasilah TANPA butir ditolak", "butir" in str(e).lower(), str(e)[:150])
finally:
    rollback()

c.execute("begin")
try:
    lama = c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,status,"
                     "amount_period,target_item_id,proposed_by,approved_by,approved_at) values "
                     "('wasilah',%s,%s,%s,'disetujui','bulanan',%s,%s,%s,now()) returning id",
                     (subject_w1, halaqah_w, month6, item_w1, P["masul_wasilah"],
                      P["masul_wasilah"])).fetchone()[0]
    switch("masul_wasilah")
    baru = c.execute("select public.ubah_target(%s,null::numeric,%s,'uji ubah',true,%s)->>'id'",
                     (lama, month7, item_w1b)).fetchone()[0]
    asal = c.execute("select target_item_id, amount from public.targets where id=%s",
                     (lama,)).fetchone()
    baru_row = c.execute("select target_item_id, amount, status, effective_month_id "
                         "from public.targets where id=%s", (baru,)).fetchone()
    record("E2 ubah_target Wasilah membuat baris BARU (butir baru, amount kosong), lama utuh",
           str(baru) != str(lama) and asal == (item_w1, None)
           and baru_row == (item_w1b, None, "disetujui", month7),
           f"baru={baru_row}")
finally:
    rollback()

ok, val, err = call("masul_alquran",
                    "select public.ubah_target(%s,0.875::numeric,%s,'uji ubah'::text,false)",
                    (one("select id from public.targets where domain='alquran' limit 1"), month7))
record("E3 Panggilan LAMA ubah_target Al Qur'an (5 argumen) tetap berhasil", ok, err)

c.execute("begin")
try:
    r = ajukan_sebagai_pengampu()
    switch("masul_wasilah")
    try:
        c.execute("select public.batalkan_target(%s)", (r["id"],))
        record("E4 Hanya pengaju yang dapat membatalkan", False, "DITERIMA")
    except Exception as e:  # noqa: BLE001
        record("E4 Hanya pengaju yang dapat membatalkan", "pengaju" in str(e).lower(),
               str(e).splitlines()[0][:150])
finally:
    rollback()

c.execute("begin")
try:
    r = ajukan_sebagai_pengampu()
    st = c.execute("select public.batalkan_target(%s)->>'status'", (r["id"],)).fetchone()[0]
    record("E5 Pengaju membatalkan pengajuannya sendiri", st == "dibatalkan", st)
finally:
    rollback()

# ------------------------------------ F. v_monthly_report AL QUR'AN IDENTIK
CEK_A = ("select coalesce(md5(string_agg(t::text,'' order by entry_id)),'') "
         "from public.v_monthly_report t where domain='alquran'")
awal = one(CEK_A)
c.execute("begin")
try:
    switch("mudir")
    c.execute(AJUKAN_W, (subject_w1, halaqah_w, month7, "uji laporan", item_w1))
    switch("masul_wasilah")
    c.execute("select public.setujui_target_halaqah(%s,%s,false)", (halaqah_w, month7))
    dalam_txn = one(CEK_A)
finally:
    rollback()
sesudah = one(CEK_A)
record("F1 v_monthly_report Al Qur'an IDENTIK sebelum/sesudah perubahan Wasilah",
       awal == dalam_txn == sesudah, "checksum sama")

c.execute("begin")
try:
    switch("musyrif")
    p = c.execute("select public.ajukan_target('alquran',%s,%s,null,%s,2.5::numeric,"
                  "'harian'::target_period,'uji t7c',false)->>'id'",
                  (subject_a, ampu_st, month7)).fetchone()[0]
    switch("masul_alquran")
    c.execute("select public.setujui_target(%s,false)", (p,))
    row = c.execute("select target_amount, target_monthly, hadir, target_period "
                    "from public.v_monthly_report where student_id=%s and subject_id=%s "
                    "and month_id=%s", (ampu_st, subject_a, month7)).fetchone()
    record("F2 Al Qur'an: target_amount = jumlah, target_monthly = jumlah x Hadir",
           row is not None and float(row[0]) == 2.5 and row[3] == "harian"
           and (row[2] is None or abs(float(row[1]) - 2.5 * float(row[2])) < 1e-9),
           f"amount={row and row[0]}, monthly={row and row[1]}, hadir={row and row[2]}")
finally:
    rollback()

# Data capaian Wasilah/Ghayah memang kosong di seed (lihat STATUS/DATA-NOTES), jadi
# baris laporan Wasilah dibuat di dalam transaksi uji lalu di-rollback.
anggota_w = one("select student_id from public.halaqah_members where halaqah_id=%s and left_on is null "
                "order by student_id limit 1", (halaqah_w,))
c.execute("begin")
try:
    c.execute("insert into public.month_domain_settings(month_id,domain,effective_days,is_locked) "
              "values (%s,'wasilah',10,false) on conflict (month_id,domain) do update set is_locked=false",
              (month7,))
    c.execute("insert into public.attendance(student_id,month_id,domain,izin,sakit,alpha) "
              "values (%s,%s,'wasilah',0,0,0) on conflict (student_id,month_id,domain) "
              "do update set izin=0, sakit=0, alpha=0", (anggota_w, month7))
    c.execute("insert into public.progress_entries(student_id,halaqah_id,subject_id,item_id,month_id,putaran) "
              "values (%s,%s,%s,%s,%s,1)", (anggota_w, halaqah_w, subject_w1, item_w1, month7))
    row = c.execute("select r.target_id, r.target_amount, r.target_monthly from public.v_monthly_report r "
                    "where r.student_id=%s and r.subject_id=%s and r.month_id=%s",
                    (anggota_w, subject_w1, month7)).fetchone()
    record("F3 Wasilah: laporan melihat target tujuan akhir (target_id ada) tanpa angka (NULL, bukan 0)",
           row is not None and row[0] is not None and row[1] is None and row[2] is None,
           f"baris={row}")
finally:
    rollback()

# ------------------------------------------------------- G. DUMMY BENTUK BARU
dummy = rows("""select domain, count(*) from public.targets
  where note like 'DUMMY - target sementara Wasilah/Ghayah (tujuan akhir)%%'
    and domain in ('wasilah','ghayah') and target_item_id is not null and amount is null
  group by 1 order by 1""")
d = dict(dummy)
record("G1 DUMMY bentuk baru: 25 Wasilah + 11 Ghayah", d == {"wasilah": 25, "ghayah": 11}, str(d))

lama_dummy = one("select count(*) from public.targets where domain in ('wasilah','ghayah') "
                 "and amount is not null")
record("G2 DUMMY bentuk LAMA (amount terisi) tidak ada lagi", lama_dummy == 0,
       f"baris amount terisi={lama_dummy}")

salah = one("""select count(*) from public.targets t
  join public.curriculum_items ci on ci.id=t.target_item_id
  join public.books b on b.id=ci.book_id
  where t.domain in ('wasilah','ghayah') and t.target_item_id is not null
    and (b.subject_id<>t.subject_id or not ci.is_active or not b.is_active)""")
record("G3 Semua butir target Wasilah/Ghayah milik buku mapelnya & aktif", salah == 0,
       f"baris salah={salah}")

# -------------------------------------------------------- H. TANPA OVERLOAD
overload = rows("""select proname, count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and proname in ('ajukan_target','ubah_target','setujui_target',
   'tolak_target','batalkan_target','riwayat_target','setujui_target_halaqah',
   'ajukan_target_massal_alquran') group by 1 having count(*)>1""")
record("H1 Satu signature per RPC target (tidak ada overload)", overload == [], str(overload))

ok, val, err = call("masul_wasilah", "select public.riwayat_target(%s,null,%s)",
                    (subject_w1, halaqah_w))
ada_butir = ok and val and any(r.get("butir") for r in val[0])
record("H2 riwayat_target menyertakan butir tujuan akhir", bool(ada_butir), err or "butir ada")

out = ROOT / "docs" / "qa" / "test_t7c_target_tujuan.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"lulus": sum(x["ok"] for x in results),
                           "gagal": sum(not x["ok"] for x in results),
                           "hasil": results}, indent=2, ensure_ascii=False), encoding="utf-8")
gagal = [x["uji"] for x in results if not x["ok"]]
print(f"\nRingkasan: {len(results) - len(gagal)}/{len(results)} lulus; hasil di {out.relative_to(ROOT)}")
c.close()
sys.exit(1 if gagal else 0)