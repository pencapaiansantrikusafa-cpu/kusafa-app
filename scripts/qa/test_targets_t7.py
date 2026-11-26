#!/usr/bin/env python3
"""Uji T7 target dinamis. Semua perubahan berjalan di transaksi yang selalu ROLLBACK.
Tidak mencetak identitas/nama santri atau data target nyata.
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
import sys

import psycopg

ROOT = Path(__file__).resolve().parents[2]
ENV = {}
for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip().strip('"').strip("'")

c = psycopg.connect(ENV["DATABASE_URL"], autocommit=True, connect_timeout=30)
results: list[dict] = []

def record(name: str, ok: bool, detail: str = "") -> None:
    # Hasil tidak boleh memuat UUID/data santri; ganti id dengan penanda.
    safe = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "<id>", detail)
    results.append({"uji": name, "ok": bool(ok), "detail": safe[:300]})
    print(("LULUS" if ok else "GAGAL") + " | " + name + (" | " + safe[:180] if safe else ""))

def one(sql: str, args=()):
    r = c.execute(sql, args).fetchone()
    return r[0] if r else None

def rows(sql: str, args=()):
    return c.execute(sql, args).fetchall()

P = {role: str(pid) for role, pid in rows(
    "select distinct on (role) role::text,id from public.profiles where is_active order by role,full_name")}

def begin_as(role: str):
    c.execute("begin")
    if role == "anon":
        c.execute("set local role anon")
    else:
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P[role],))
        c.execute("select set_config('request.jwt.claim.role','authenticated',true)")

def rollback():
    c.execute("rollback")

def call(role: str, sql: str, args=()):
    begin_as(role)
    try:
        cur = c.execute(sql, args)
        return True, cur.fetchone() if cur.description else cur.rowcount, ""
    except Exception as e:
        return False, None, str(e).splitlines()[0][:300]
    finally:
        rollback()

def txn(role: str, fn):
    begin_as(role)
    try:
        return fn()
    finally:
        rollback()

# Seed context only; no sensitive values are printed.
roles_needed = ("mudir", "admin", "masul_alquran", "masul_wasilah", "masul_ghayah", "musyrif", "mudarris")
missing = [r for r in roles_needed if r not in P]
if missing:
    print("GAGAL | konteks peran lengkap | profil tidak tersedia: " + ", ".join(missing))
    sys.exit(1)

month0 = one("select id from public.hijri_months where month_no=0 order by id limit 1")
month1 = one("select id from public.hijri_months where month_no=1 order by id limit 1")
month6 = one("select id from public.hijri_months where month_no=6 order by id limit 1")
month7 = one("select id from public.hijri_months where month_no=7 order by id limit 1")
subject_a = one("select id from public.subjects where domain='alquran' order by sort_order limit 1")
subject_w = one("select id from public.subjects where domain='wasilah' order by sort_order limit 1")
subject_g = one("select id from public.subjects where domain='ghayah' order by sort_order limit 1")

ampu_h = one("select h.id from public.halaqah_teachers ht join public.halaqahs h on h.id=ht.halaqah_id where ht.profile_id=%s and h.domain='alquran' order by h.code limit 1", (P["musyrif"],))
ampu_st = one("select student_id from public.halaqah_members where halaqah_id=%s and left_on is null order by student_id limit 1", (ampu_h,))
item_a = one("select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id where b.subject_id=%s and ci.is_active order by ci.seq limit 1", (subject_a,))

if not all((month0, month1, month6, month7, subject_a, subject_w, subject_g, ampu_h, ampu_st, item_a)):
    print("GAGAL | konteks database lengkap | data rujukan tidak tersedia")
    sys.exit(1)

# 1) Pengampu dapat mengajukan dan tidak dapat menyetujui.
def test_pengampu():
    begin_as("musyrif")
    try:
        r = c.execute("select public.ajukan_target('alquran',%s,%s,null,%s,0.75,'harian','uji rollback',false)", (subject_a, ampu_st, month7)).fetchone()[0]
        tid = r["id"]
        try:
            c.execute("select public.setujui_target(%s,false)", (tid,))
            return False, "RPC setujui_target diterima untuk Musyrif/ah"
        except Exception:
            return r["status"] == "diajukan", "ajukan=diajukan; persetujuan ditolak"
    finally:
        rollback()
ok, detail = test_pengampu(); record("Musyrif/ah mengajukan; tidak dapat menyetujui", ok, detail)

# 2) Masul domain sendiri boleh menyetujui; Masul domain lain ditolak.
def test_masul_domain():
    begin_as("musyrif")
    try:
        t = c.execute("select public.ajukan_target('alquran',%s,%s,null,%s,0.75,'harian','uji rollback',false)", (subject_a, ampu_st, month7)).fetchone()[0]["id"]
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P["masul_alquran"],))
        accepted = c.execute("select public.setujui_target(%s,false)", (t,)).fetchone()[0]["status"] == "disetujui"
        return accepted, "Masul Al Quran domain sendiri menyetujui"
    finally:
        rollback()
ok, detail = test_masul_domain(); record("Masul Al Quran menyetujui target domainnya", ok, detail)

# Cross-domain attempt: staged pending row via postgres, then invoke as Masul Al Quran.
def test_lintas_domain():
    c.execute("begin")
    try:
        tid = c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,amount,amount_period,status,proposed_by,target_item_id) values ('wasilah',%s,%s,%s,null,'bulanan','diajukan',%s,(select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id where b.subject_id=%s and ci.is_active order by ci.seq limit 1)) returning id", (subject_w, one("select id from public.halaqahs where domain='wasilah' order by code limit 1"), month7, P["mudarris"], subject_w)).fetchone()[0]
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P["masul_alquran"],))
        c.execute("select set_config('request.jwt.claim.role','authenticated',true)")
        try:
            c.execute("select public.setujui_target(%s,false)", (tid,))
            return False, "Masul Al Quran lintas domain diterima"
        except Exception as e:
            return True, str(e).splitlines()[0][:180]
    finally:
        rollback()
ok, detail = test_lintas_domain(); record("Masul Al Quran ditolak menyetujui Wasilah", ok, detail)

# 3) Mudir/Admin menyetujui.
def test_full(role):
    begin_as("musyrif")
    try:
        tid = c.execute("select (public.ajukan_target('alquran',%s,%s,null,%s,0.75,'harian','uji rollback',false)->>'id')::uuid", (subject_a, ampu_st, month7)).fetchone()[0]
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P[role],))
        status = c.execute("select public.setujui_target(%s,false)->>'status'", (tid,)).fetchone()[0]
        return status == "disetujui", status
    finally:
        rollback()
for r in ("mudir", "admin"):
    ok, detail = test_full(r); record(f"{r} menyetujui target", ok, detail)

# 4) Anon RPC access denied; direct table writes denied for any API role.
for r in ("anon", "authenticated"):
    if r == "anon":
        ok, _, detail = call("anon", "select public.ajukan_target('alquran',%s,%s,null,%s,1,'harian',null,false)", (subject_a, ampu_st, month7))
        record("anon tidak dapat menjalankan RPC target", not ok, detail)
    begin_as("anon" if r == "anon" else "musyrif")
    try:
        try:
            c.execute("insert into public.targets(domain,subject_id,student_id,effective_month_id,amount,amount_period,status) values ('alquran',%s,%s,%s,1,'harian','diajukan')", (subject_a, ampu_st, month7))
            direct_ok = True
        except Exception:
            direct_ok = False
    finally:
        rollback()
    record(f"{r} direct INSERT targets ditolak", not direct_ok)

# 5) Pending target tidak digunakan di laporan.
def test_pending_not_report():
    begin_as("musyrif")
    try:
        r = c.execute("select public.ajukan_target('alquran',%s,%s,null,%s,99,'harian','uji rollback',false)", (subject_a, ampu_st, month7)).fetchone()[0]
        report = c.execute("select target_amount from public.v_monthly_report where student_id=%s and subject_id=%s and month_id=%s", (ampu_st, subject_a, month7)).fetchone()
        return r["status"] == "diajukan" and report and report[0] != 99, "pending tidak mengganti target laporan"
    finally:
        rollback()
ok, detail = test_pending_not_report(); record("Target diajukan tidak dipakai laporan", ok, detail)

# 6) Penolakan wajib alasan dan status/riwayat tidak terhapus.
def test_reject():
    begin_as("musyrif")
    try:
        tid = c.execute("select (public.ajukan_target('alquran',%s,%s,null,%s,0.75,'harian','uji rollback',false)->>'id')::uuid", (subject_a, ampu_st, month7)).fetchone()[0]
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P["masul_alquran"],))
        try:
            c.execute("select public.tolak_target(%s,'  ',false)", (tid,))
            return False, "alasan kosong diterima"
        except Exception:
            rollback()
            begin_as("musyrif")
            tid = c.execute("select (public.ajukan_target('alquran',%s,%s,null,%s,0.75,'harian','uji rollback',false)->>'id')::uuid", (subject_a, ampu_st, month7)).fetchone()[0]
            c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P["masul_alquran"],))
        rejected = c.execute("select public.tolak_target(%s,'Alasan uji',false)->>'status'", (tid,)).fetchone()[0]
        exists = c.execute("select count(*) from public.targets where id=%s", (tid,)).fetchone()[0] == 1
        return rejected == "ditolak" and exists, "ditolak tersimpan sebagai riwayat"
    finally:
        rollback()
ok, detail = test_reject(); record("Tolak wajib alasan; target tidak dihapus", ok, detail)

# 7) ubah_target menambah baris baru dan mempertahankan target asal.
def test_change():
    begin_as("musyrif")
    try:
        old = c.execute("select id,amount from public.targets where domain='alquran' and student_id=%s and subject_id=%s order by created_at limit 1", (ampu_st, subject_a)).fetchone()
        if not old: return False, "target asal tidak ditemukan"
        new = c.execute("select (public.ubah_target(%s,0.875,%s,'uji rollback',false)->>'id')::uuid", (old[0], month7)).fetchone()[0]
        keep = c.execute("select amount from public.targets where id=%s", (old[0],)).fetchone()[0] == old[1]
        return bool(new != old[0] and keep), "baris baru; lama utuh"
    finally:
        rollback()
ok, detail = test_change(); record("ubah_target membuat baris baru, target lama tetap", ok, detail)

# 8) Massal Al Qur'an menghasilkan baris per santri, seluruh transaksi rollback.
def test_mass():
    ok, val, err = call("musyrif", "select public.ajukan_target_massal_alquran(%s,%s,%s,0.25,'uji rollback',false)", (ampu_h, subject_a, month7))
    if not ok: return False, err
    obj = val[0]
    return obj["jumlah_santri"] > 0 and obj["status"] == "diajukan", json.dumps(obj)
ok, detail = test_mass(); record("Massal Al Qur'an membuat target per santri", ok, detail)

# 9) Riwayat mengembalikan array tanpa mengubah target.
def test_history():
    ok, val, err = call("mudir", "select public.riwayat_target(%s,%s,null)", (subject_a, ampu_st))
    return ok and val and isinstance(val[0], list) and len(val[0]) > 0, err or "riwayat terbaca"
ok, detail = test_history(); record("Riwayat target terbaca", ok, detail)

# 10) Bulan 0 ditolak oleh RPC.
ok, _, detail = call("musyrif", "select public.ajukan_target('alquran',%s,%s,null,%s,1,'harian',null,false)", (subject_a, ampu_st, month0))
record("Bulan 0 ditolak sebagai bulan berlaku target", not ok, detail)

# 11) Target lewat hanya Mudir/Admin, dengan konfirmasi eksplisit.
for role in ("masul_alquran", "mudir", "admin"):
    ok, _, detail = call(role, "select public.ajukan_target('alquran',%s,%s,null,%s,0.5,'harian',null,false)", (subject_a, ampu_st, month6))
    record(f"Bulan lewat: {role} tanpa konfirmasi ditolak", not ok, detail)
for role in ("mudir", "admin"):
    ok, val, detail = call(role, "select public.ajukan_target('alquran',%s,%s,null,%s,0.5,'harian',null,true)", (subject_a, ampu_st, month6))
    record(f"Bulan lewat: {role} dengan konfirmasi diterima", ok, detail)

# 12) Pembatalan hanya pemilik pengajuan yang masih diajukan.
def test_cancel():
    begin_as("musyrif")
    try:
        tid = c.execute("select (public.ajukan_target('alquran',%s,%s,null,%s,0.75,'harian','uji rollback',false)->>'id')::uuid", (subject_a, ampu_st, month7)).fetchone()[0]
        st = c.execute("select public.batalkan_target(%s)->>'status'", (tid,)).fetchone()[0]
        return st == "dibatalkan", st
    finally:
        rollback()
ok, detail = test_cancel(); record("Pengaju dapat membatalkan status diajukan", ok, detail)

# 13) Bulan terkunci: semua API-role ditolak; Mudir/Admin perlu konfirmasi.
def test_locked(role, confirmation):
    c.execute("begin")
    try:
        c.execute("update public.month_domain_settings set is_locked=true where month_id=%s and domain='alquran'", (month7,))
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P[role],))
        c.execute("select set_config('request.jwt.claim.role','authenticated',true)")
        c.execute("select public.ajukan_target('alquran',%s,%s,null,%s,0.5,'harian',null,%s)", (subject_a, ampu_st, month7, confirmation))
        return True, "RPC diterima"
    except Exception as e:
        return False, str(e).splitlines()[0][:180]
    finally:
        rollback()
for role in ("musyrif", "masul_alquran"):
    ok, detail = test_locked(role, True); record(f"Bulan terkunci hanya Mudir/Admin ({role})", not ok, detail)
for role in ("mudir", "admin"):
    ok, detail = test_locked(role, False); record(f"Bulan terkunci {role} tanpa konfirmasi ditolak", not ok, detail)
    ok, detail = test_locked(role, True); record(f"Bulan terkunci {role} dengan konfirmasi diterima", ok, detail)

# 14) Kasus (f), uji di transaksi: tidak ada target/Hari Efektif => NULL; hadir 0 => 0;
#     bulan 0 tetap NULL. Gunakan santri+baris uji sendiri; semua perubahan rollback.
def test_f_semantics():
    c.execute("begin")
    try:
        candidate = c.execute("""select e.student_id,e.month_id,e.subject_id,e.item_id,e.halaqah_id
            from public.progress_entries e join public.subjects s on s.id=e.subject_id
            join public.hijri_months m on m.id=e.month_id
            join public.hijri_months m0 on m0.month_no=0
            join public.progress_entries e0 on e0.student_id=e.student_id and e0.subject_id=e.subject_id and e0.month_id=m0.id
            where s.domain='alquran' and m.month_no>0
            order by e.month_id,e.student_id limit 1""").fetchone()
        sid, mid, sub, item, hlq = candidate
        # Bulan target yang baru dibuat sendiri di transaksi akan menggantikan target lama hanya di sana.
        tid = c.execute("insert into public.targets(domain,subject_id,student_id,effective_month_id,amount,amount_period,status) values ('alquran',%s,%s,%s,2,'harian','disetujui') returning id", (sub,sid,mid)).fetchone()[0]
        # Tanpa kehadiran (hari efektif NULL) -> NULL.
        c.execute("delete from public.attendance where student_id=%s and month_id=%s and domain='alquran'", (sid,mid))
        val_null = c.execute("select target_monthly from public.v_monthly_report where student_id=%s and month_id=%s and subject_id=%s", (sid,mid,sub)).fetchone()[0]
        # Masukkan attendance+setting untuk case hadir=0. Settings disetel ke 0 hanya di transaksi.
        c.execute("insert into public.month_domain_settings(month_id,domain,effective_days,is_locked) values (%s,'alquran',0,false) on conflict(month_id,domain) do update set effective_days=0", (mid,))
        c.execute("insert into public.attendance(student_id,month_id,domain,izin,sakit,alpha) values (%s,%s,'alquran',0,0,0) on conflict(student_id,month_id,domain) do update set izin=0,sakit=0,alpha=0", (sid,mid))
        val_zero = c.execute("select target_monthly from public.v_monthly_report where student_id=%s and month_id=%s and subject_id=%s", (sid,mid,sub)).fetchone()[0]
        # Bulan 0: report tetap NULL meski target tersedia.
        c.execute("insert into public.targets(domain,subject_id,student_id,effective_month_id,amount,amount_period,status) values ('alquran',%s,%s,%s,2,'harian','disetujui')", (sub,sid,month0))
        val_zero_month = c.execute("select target_monthly from public.v_monthly_report where student_id=%s and month_id=%s and subject_id=%s", (sid,month0,sub)).fetchone()[0]
        return val_null is None and val_zero == 0 and val_zero_month is None, f"null={val_null}, hadir0={val_zero}, bulan0={val_zero_month}"
    finally:
        rollback()
ok, detail = test_f_semantics(); record("Kasus (f): kosong vs 0 vs bulan 0 NULL", ok, detail)

# 14b) Individu didahulukan dari halaqah; dua target seord diputus created_at/id;
#      target halaqah Wasilah/Ghayah bulanan tidak dikali Hadir. Semua di transaksi rollback.
def test_prioritas_dan_bulanan():
    c.execute("begin")
    try:
        h = c.execute("select id from public.halaqahs where domain='alquran' order by code limit 1").fetchone()[0]
        sid = c.execute("select student_id from public.halaqah_members where halaqah_id=%s and left_on is null order by student_id limit 1", (h,)).fetchone()[0]
        e = c.execute("""select pe.month_id,pe.subject_id from public.progress_entries pe
            join public.hijri_months m on m.id=pe.month_id and m.month_no=7
            where pe.student_id=%s and pe.halaqah_id=%s limit 1""",(sid,h)).fetchone()
        if not e: return False, "baris laporan uji tidak ditemukan"
        mid, sub = e
        c.execute("insert into public.month_domain_settings(month_id,domain,effective_days,is_locked) values (%s,'alquran',10,false) on conflict(month_id,domain) do update set effective_days=10",(mid,))
        c.execute("insert into public.attendance(student_id,month_id,domain,izin,sakit,alpha) values (%s,%s,'alquran',2,0,0) on conflict(student_id,month_id,domain) do update set izin=2,sakit=0,alpha=0",(sid,mid))
        # target halaqah: 3/hari, target individu: 7/hari. Hadir=8 => individu 56, halaqah 24.
        c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,amount,amount_period,status,created_at) values ('alquran',%s,%s,%s,3,'harian','disetujui',now()-interval '1 day')",(sub,h,mid))
        ti = c.execute("insert into public.targets(domain,subject_id,student_id,effective_month_id,amount,amount_period,status,created_at) values ('alquran',%s,%s,%s,7,'harian','disetujui',now()) returning id",(sub,sid,mid)).fetchone()[0]
        got = c.execute("select target_id,target_monthly from public.v_monthly_report where student_id=%s and subject_id=%s and month_id=%s",(sid,sub,mid)).fetchone()
        prioritas = got[0] == ti and float(got[1]) == 56
        # Tiebreak: satu lagi target individu seord, lebih baru => menang (amount 9 -> 72)
        tj = c.execute("insert into public.targets(domain,subject_id,student_id,effective_month_id,amount,amount_period,status,created_at) values ('alquran',%s,%s,%s,9,'harian','disetujui',now()+interval '1 second') returning id",(sub,sid,mid)).fetchone()[0]
        got2 = c.execute("select target_id,target_monthly from public.v_monthly_report where student_id=%s and subject_id=%s and month_id=%s",(sid,sub,mid)).fetchone()
        tie = got2[0] == tj and float(got2[1]) == 72
        # Wasilah/Ghayah: bentuk TUJUAN AKHIR (butir, tanpa amount) -> laporan mengenal
        # targetnya tetapi tidak punya angka (NULL, bukan 0) dan tidak dikali Hadir.
        hw = c.execute("select h.id, s.id from public.halaqahs h join public.halaqah_subjects hs on hs.halaqah_id=h.id join public.subjects s on s.id=hs.subject_id where s.domain='wasilah' order by h.code limit 1").fetchone()
        sidw = c.execute("select student_id from public.halaqah_members where halaqah_id=%s and left_on is null limit 1",(hw[0],)).fetchone()[0]
        itemw = c.execute("select ci.id from curriculum_items ci join books b on b.id=ci.book_id where b.subject_id=%s and ci.is_active order by ci.seq limit 1",(hw[1],)).fetchone()[0]
        c.execute("insert into public.month_domain_settings(month_id,domain,effective_days,is_locked) values (%s,'wasilah',10,false) on conflict(month_id,domain) do update set effective_days=10",(mid,))
        c.execute("insert into public.attendance(student_id,month_id,domain,izin,sakit,alpha) values (%s,%s,'wasilah',9,0,0) on conflict(student_id,month_id,domain) do update set izin=9,sakit=0,alpha=0",(sidw,mid))
        c.execute("insert into public.progress_entries(student_id,halaqah_id,subject_id,month_id,item_id,putaran) values (%s,%s,%s,%s,%s,1)",(sidw,hw[0],hw[1],mid,itemw))
        tw = c.execute("insert into public.targets(domain,subject_id,halaqah_id,effective_month_id,amount,amount_period,status,target_item_id) values ('wasilah',%s,%s,%s,null,'bulanan','disetujui',%s) returning id",(hw[1],hw[0],mid,itemw)).fetchone()[0]
        bw = c.execute("select target_id,target_amount,target_monthly from public.v_monthly_report where student_id=%s and subject_id=%s and month_id=%s",(sidw,hw[1],mid)).fetchone()
        return prioritas and tie and bw[0] == tw and bw[1] is None and bw[2] is None, f"individu={got}, tie={got2}, wasilah={bw}"
    finally:
        rollback()
ok, detail = test_prioritas_dan_bulanan(); record("Individu diutamakan, tiebreak deterministik, tujuan akhir tanpa angka di laporan", ok, detail)

# 14c) Log perubahan targets: UPDATE dan DELETE tercatat (nilai lama + baru, aktor).
def test_log_target():
    c.execute("begin")
    try:
        c.execute("reset role")
        c.execute("select set_config('request.jwt.claim.sub',%s,true)", (P["mudir"],))
        sid, mid, sub = c.execute("""select pe.student_id,pe.month_id,pe.subject_id from public.progress_entries pe
            join public.subjects s on s.id=pe.subject_id join public.hijri_months m on m.id=pe.month_id
            where s.domain='alquran' and m.month_no=7 limit 1""").fetchone()
        tid = c.execute("insert into public.targets(domain,subject_id,student_id,effective_month_id,amount,amount_period,status,note) values ('alquran',%s,%s,%s,1,'harian','disetujui','uji log T7') returning id",(sub,sid,mid)).fetchone()[0]
        c.execute("update public.targets set amount=2 where id=%s",(tid,))
        upd = c.execute("select aksi,nilai_lama->>'amount',nilai_baru->>'amount',aktor from public.change_log where tabel='targets' order by id desc limit 1").fetchone()
        audit = c.execute("select updated_by is not null, entered_by is null from public.targets where id=%s",(tid,)).fetchone()
        c.execute("delete from public.targets where id=%s",(tid,))
        dele = c.execute("select aksi,nilai_lama->>'amount',nilai_baru,aktor from public.change_log where tabel='targets' order by id desc limit 1").fetchone()
        return upd == ("update","1","2",uuid.UUID(P["mudir"])) and dele == ("delete","2",None,uuid.UUID(P["mudir"])) and audit == (True,False), f"update={upd}, delete={dele}, audit={audit}"
    finally:
        rollback()
ok, detail = test_log_target(); record("Log targets: UPDATE dan DELETE tercatat", ok, detail)

# 15) Pending dan ditolak tidak dipakai laporan.
def test_status_laporan():
    c.execute("begin")
    try:
        sid, mid, sub = c.execute("""select pe.student_id,pe.month_id,pe.subject_id from public.progress_entries pe
            join public.subjects s on s.id=pe.subject_id join public.hijri_months m on m.id=pe.month_id
            where s.domain='alquran' and m.month_no=7 limit 1""").fetchone()
        base = c.execute("select target_monthly from public.v_monthly_report where student_id=%s and month_id=%s and subject_id=%s",(sid,mid,sub)).fetchone()[0]
        c.execute("insert into public.targets(domain,subject_id,student_id,effective_month_id,amount,amount_period,status,created_at) values ('alquran',%s,%s,%s,999,'harian','diajukan',now()+interval '2 hour')",(sub,sid,mid))
        p = c.execute("select target_monthly from public.v_monthly_report where student_id=%s and month_id=%s and subject_id=%s",(sid,mid,sub)).fetchone()[0]
        c.execute("update public.targets set status='ditolak',alasan_tolak='uji' where domain='alquran' and student_id=%s and subject_id=%s and effective_month_id=%s and amount=999",(sid,sub,mid))
        d = c.execute("select target_monthly from public.v_monthly_report where student_id=%s and month_id=%s and subject_id=%s",(sid,mid,sub)).fetchone()[0]
        return p == base and d == base, f"base={base}, pending={p}, ditolak={d}"
    finally:
        rollback()
ok, detail = test_status_laporan(); record("Diajukan dan ditolak tidak mengubah laporan", ok, detail)

# 15) Direct UPDATE/DELETE must fail for API role; SELECT stays available.
for op, sql in (("UPDATE", "update public.targets set amount=amount where id=(select id from public.targets limit 1)"),
                ("DELETE", "delete from public.targets where id=(select id from public.targets limit 1)")):
    ok, _, detail = call("musyrif", sql)
    record(f"Tulis langsung targets {op} ditolak", not ok, detail)
ok, val, detail = call("musyrif", "select id from public.targets limit 1")
record("SELECT targets tetap tersedia bagi staf", ok and bool(val), detail)

# 16) Validasi privilege anon atas seluruh RPC target (termasuk helper) ditolak.
funcs = rows("""select p.oid::regprocedure::text from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname like '%%target%%' order by p.proname""")
all_anon_denied = True
for (sig,) in funcs:
    allowed = one("select has_function_privilege('anon',%s,'EXECUTE')", (sig,))
    if allowed:
        all_anon_denied = False
        record("Anon EXECUTE ditolak: " + sig, False, "EXECUTE masih diberikan")
if all_anon_denied:
    record("Semua fungsi bernama target tidak dapat di-EXECUTE anon", True, f"{len(funcs)} fungsi")

# Simpan hasil yang tidak mengandung data murid.
out = ROOT / "docs/qa/test_targets_t7.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"lulus": sum(x["ok"] for x in results), "gagal": sum(not x["ok"] for x in results), "hasil": results}, indent=2, ensure_ascii=False), encoding="utf-8")
failed = [x["uji"] for x in results if not x["ok"]]
print(f"Ringkasan: {len(results)-len(failed)}/{len(results)} lulus; hasil di {out.relative_to(ROOT)}")
c.close()
sys.exit(1 if failed else 0)
