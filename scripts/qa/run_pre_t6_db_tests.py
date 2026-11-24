#!/usr/bin/env python3
"""
Uji DB pra-T6. Semua uji tulis dibungkus BEGIN...ROLLBACK.
Membaca .env.local. Tidak mencetak rahasia.
"""
import os, json, sys, datetime, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
env={}
for line in open(ROOT/'.env.local'):
    line=line.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k,v=line.split('=',1)
    env[k.strip()]=v.strip().strip('"').strip("'")

import psycopg
from psycopg.rows import dict_row

out = {"ran_at": datetime.datetime.now().isoformat(), "tests": []}

def rec(name, ok, detail, evidence=None):
    out["tests"].append({"name": name, "ok": ok, "detail": detail, "evidence": evidence or {}})
    print(("PASS" if ok else "FAIL"), name, "-", detail)

conn = psycopg.connect(env['DATABASE_URL'], autocommit=True, connect_timeout=20)

# helpers
def fetch1(q,*a):
    params = a[0] if len(a)==1 and isinstance(a[0], (tuple,list)) else a
    r=conn.execute(q,params).fetchone(); return r

def fetchall(q,*a):
    params = a[0] if len(a)==1 and isinstance(a[0], (tuple,list)) else a
    return conn.execute(q,params).fetchall()

# discover some ids
profiles = fetchall("select id, role::text, full_name from public.profiles where role in ('mudir','admin','masul_alquran','musyrif') order by role, full_name")
mudir = next((p for p in profiles if p[1]=='mudir'), None)
admin = next((p for p in profiles if p[1]=='admin'), None)
masul_q = next((p for p in profiles if p[1]=='masul_alquran'), None)
musyrif = next((p for p in profiles if p[1]=='musyrif'), None)

# pick a month/subject for alquran
alquran_subject = fetch1("select id, code, domain::text from public.subjects where domain='alquran' limit 1")
any_month = fetch1("select m.id, m.name, ay.hijri_year from public.hijri_months m join public.academic_years ay on ay.id=m.academic_year_id where m.month_no>0 order by m.month_no limit 1")
# find musyrif's halaqah and a student in it
musyrif_halaqah_row = fetch1("select halaqah_id from public.halaqah_teachers where profile_id=%s limit 1", (str(musyrif[0]),)) if musyrif else None
musyrif_halaqah = musyrif_halaqah_row[0] if musyrif_halaqah_row else None
student_in_h = None
if musyrif_halaqah:
    student_in_h = fetch1("select hm.student_id, s.full_name from public.halaqah_members hm join public.students s on s.id=hm.student_id where hm.halaqah_id=%s limit 1", musyrif_halaqah)
# another student not in musyrif halaqah (any)
student_out = fetch1("select s.id, s.full_name from public.students s where not exists (select 1 from public.halaqah_members hm where hm.student_id=s.id and hm.halaqah_id=%s) limit 1", musyrif_halaqah) if musyrif_halaqah else None

# item for alquran
item = fetch1("select ci.id, ci.label from public.curriculum_items ci join public.books b on b.id=ci.book_id join public.subjects s on s.id=b.subject_id where s.domain='alquran' order by ci.seq limit 1")

# find a locked month if any
locked = fetch1("select mds.month_id, mds.domain::text, m.name from public.month_domain_settings mds join public.hijri_months m on m.id=mds.month_id where mds.is_locked=true limit 1")
# find an unlocked
unlocked = fetch1("select mds.month_id, mds.domain::text, m.name from public.month_domain_settings mds join public.hijri_months m on m.id=mds.month_id where mds.is_locked=false and mds.domain='alquran' limit 1")

# for effective_days test, pick rabiul awwal alquran setting
ra = fetch1("select mds.month_id, mds.domain::text, mds.effective_days, m.name from public.month_domain_settings mds join public.hijri_months m on m.id=mds.month_id where m.name ilike '%%rabi%%awwal%%' and mds.domain='alquran' limit 1")

out['context'] = {
  'mudir': mudir[1] if mudir else None,
  'admin': admin[1] if admin else None,
  'masul_q': masul_q[1] if masul_q else None,
  'musyrif': {'role': musyrif[1], 'halaqah_id': str(musyrif_halaqah)} if musyrif else None,
  'student_in_h': str(student_in_h[0]) if student_in_h else None,
  'student_out': str(student_out[0]) if student_out else None,
  'subject': str(alquran_subject[0]) if alquran_subject else None,
  'month': str(any_month[0]) if any_month else None,
  'item': str(item[0]) if item else None,
  'locked': str(locked[0]) if locked else None,
  'unlocked': str(unlocked[0]) if unlocked else None,
  'ra_effective_days': ra[2] if ra else None,
}
print('CONTEXT', json.dumps(out['context']))

def set_auth(uid, role):
    conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(uid),))
    conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
    # Also set role via auth.uid() - supabase uses request.jwt.claim.sub; current_app_role reads profiles by auth.uid()
    # We need to ensure auth.uid() works. In SQL, auth.uid() reads request.jwt.claim.sub.
    # Also set_config with is_local true applies to current transaction; we'll use it inside transactions.

def reset_auth():
    conn.execute("select set_config('request.jwt.claim.sub', '', true)")
    conn.execute("select set_config('request.jwt.claim.role', '', true)")

# B2: Attendance override guard (trigger) - effective_days_override hanya Mudir/Admin
if musyrif and unlocked and student_in_h:
    try:
        conn.execute("BEGIN")
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(musyrif[0]),))
        conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        try:
            conn.execute("""
              insert into public.attendance (student_id, month_id, domain, izin, sakit, alpha, effective_days_override)
              values (%s,%s,%s::public.domain_kind,0,0,0,10)
            """, (str(student_in_h[0]), str(unlocked[0]), unlocked[1]))
            rec("B2_musyrif_override_ditolak", False, "INSERT effective_days_override oleh musyrif BERHASIL (seharusnya ditolak trigger).", {"role":"musyrif"})
        except Exception as e:
            rec("B2_musyrif_override_ditolak", True, f"Trigger menolak override musyrif: {type(e).__name__}", {"sqlstate": getattr(e,'sqlstate',None)})
        finally:
            conn.execute("ROLLBACK")
    except Exception as e:
        rec("B2_musyrif_override_ditolak", False, f"Error uji: {e}")
    if admin:
        try:
            conn.execute("BEGIN")
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(admin[0]),))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
            conn.execute("delete from public.attendance where student_id=%s and month_id=%s and domain=%s::public.domain_kind",
                         (str(student_in_h[0]), str(unlocked[0]), unlocked[1]))
            conn.execute("""
              insert into public.attendance (student_id, month_id, domain, izin, sakit, alpha, effective_days_override)
              values (%s,%s,%s::public.domain_kind,0,0,0,10)
            """, (str(student_in_h[0]), str(unlocked[0]), unlocked[1]))
            rec("B2_admin_override_diterima", True, "INSERT effective_days_override oleh admin diterima (akan di-ROLLBACK).")
            conn.execute("ROLLBACK")
        except Exception as e:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            rec("B2_admin_override_diterima", False, f"Admin override ditolak: {type(e).__name__}", {"sqlstate": getattr(e,'sqlstate',None)})
else:
    rec("B2_musyrif_override_ditolak", None, "Konteks tidak cukup untuk uji.")
    rec("B2_admin_override_diterima", None, "Konteks tidak cukup untuk uji.")

# B3: month_is_open / write lock
# test as musyrif: insert progress on locked month should fail; on unlocked should succeed
if musyrif and student_in_h and item and alquran_subject:
    if locked and locked[1]=='alquran':
        try:
            conn.execute("BEGIN")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(musyrif[0]),))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
            try:
                conn.execute("""
                  insert into public.progress_entries (student_id, month_id, subject_id, item_id, putaran)
                  values (%s,%s,%s,%s,1)
                """, (str(student_in_h[0]), str(locked[0]), str(alquran_subject[0]), str(item[0])))
                rec("B3_tulis_bulan_terkunci_ditolak", False, "INSERT progress di bulan terkunci BERHASIL (seharusnya ditolak RLS).", {"month": locked[2]})
            except Exception as e:
                rec("B3_tulis_bulan_terkunci_ditolak", True, f"Ditolak: {type(e).__name__}", {"sqlstate": getattr(e,'sqlstate',None)})
            finally:
                conn.execute("ROLLBACK")
        except Exception as e:
            rec("B3_tulis_bulan_terkunci_ditolak", False, f"Error uji: {e}")
    else:
        # no locked month in data; set one temporarily
        if unlocked:
            try:
                conn.execute("BEGIN")
                conn.execute("set local role postgres")
                conn.execute("update public.month_domain_settings set is_locked=true where month_id=%s and domain=%s", (str(unlocked[0]), unlocked[1]))
                conn.execute("set local role authenticated")
                conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(musyrif[0]),))
                conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
                try:
                    conn.execute("""
                      insert into public.progress_entries (student_id, month_id, subject_id, item_id, putaran)
                      values (%s,%s,%s,%s,1)
                    """, (str(student_in_h[0]), str(unlocked[0]), str(alquran_subject[0]), str(item[0])))
                    rec("B3_tulis_bulan_terkunci_ditolak", False, "INSERT progress di bulan terkunci (dikunci sementara dalam tx) BERHASIL.")
                except Exception as e:
                    rec("B3_tulis_bulan_terkunci_ditolak", True, f"Ditolak: {type(e).__name__}", {"sqlstate": getattr(e,'sqlstate',None)})
                finally:
                    conn.execute("ROLLBACK")
            except Exception as e:
                try: conn.execute("ROLLBACK")
                except Exception: pass
                rec("B3_tulis_bulan_terkunci_ditolak", False, f"Error uji: {e}")
        else:
            rec("B3_tulis_bulan_terkunci_ditolak", None, "Tidak ada bulan alquran untuk uji.")

    # admin can write locked? test
    if unlocked and admin:
        try:
            conn.execute("BEGIN")
            conn.execute("set local role postgres")
            conn.execute("update public.month_domain_settings set is_locked=true where month_id=%s and domain=%s", (str(unlocked[0]), unlocked[1]))
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(admin[0]),))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
            conn.execute("delete from public.progress_entries where student_id=%s and month_id=%s and subject_id=%s",
                         (str(student_in_h[0]), str(unlocked[0]), str(alquran_subject[0])))
            conn.execute("""
              insert into public.progress_entries (student_id, month_id, subject_id, item_id, putaran)
              values (%s,%s,%s,%s,1)
            """, (str(student_in_h[0]), str(unlocked[0]), str(alquran_subject[0]), str(item[0])))
            rec("B3_admin_tulis_bulan_terkunci_diterima", True, "Admin dapat menulis di bulan terkunci (ROLLBACK).")
            conn.execute("ROLLBACK")
        except Exception as e:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            rec("B3_admin_tulis_bulan_terkunci_diterima", False, f"Admin ditolak menulis bulan terkunci: {type(e).__name__}", {"sqlstate": getattr(e,'sqlstate',None)})
else:
    rec("B3_tulis_bulan_terkunci_ditolak", None, "Konteks tidak cukup.")
    rec("B3_admin_tulis_bulan_terkunci_diterima", None, "Konteks tidak cukup.")

# B4: cross-book achievement (posisi) - test item_position function via SQL
# Create test data in transaction: two items in different books? Actually test posisi calc
try:
    conn.execute("BEGIN")
    conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(admin[0]),))
    conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
    # test item_position with a sample
    if item:
        pos = fetch1("select public.item_position(%s::uuid, 1)", (str(item[0]),))
        rec("B4_item_position_basic", pos is not None, f"item_position(item,1) = {pos[0] if pos else None}", {"value": str(pos[0]) if pos else None})
    rec("B4_item_position_function_exists", True, "Fungsi item_position dapat dipanggil.")
    conn.execute("ROLLBACK")
except Exception as e:
    try: conn.execute("ROLLBACK")
    except Exception: pass
    rec("B4_item_position_basic", False, f"Error: {e}")

# B5: cross-halaqah RLS - musyrif cannot insert progress for student outside halaqah
if musyrif and student_out and item and alquran_subject and unlocked:
    try:
        conn.execute("BEGIN")
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(musyrif[0]),))
        conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        try:
            conn.execute("""
              insert into public.progress_entries (student_id, month_id, subject_id, item_id, putaran)
              values (%s,%s,%s,%s,1)
            """, (str(student_out[0]), str(unlocked[0]), str(alquran_subject[0]), str(item[0])))
            rec("B5_musyrif_luar_halaqah_ditolak", False, "INSERT progress santri di luar halaqah musyrif BERHASIL (seharusnya ditolak RLS).")
        except Exception as e:
            rec("B5_musyrif_luar_halaqah_ditolak", True, f"Ditolak: {type(e).__name__}", {"sqlstate": getattr(e,'sqlstate',None)})
        finally:
            conn.execute("ROLLBACK")
    except Exception as e:
        rec("B5_musyrif_luar_halaqah_ditolak", False, f"Error uji: {e}")
else:
    rec("B5_musyrif_luar_halaqah_ditolak", None, "Konteks tidak cukup.")

# B6: can_manage matrix for roles
# test as masul_alquran: can_manage('alquran') true, can_manage('wasilah') false
if masul_q:
    for domain, expected in [('alquran', True), ('wasilah', False), ('ghayah', False)]:
        try:
            conn.execute("BEGIN")
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(masul_q[0]),))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
            r = fetch1("select public.can_manage(%s::public.domain_kind)", (domain,))
            actual = bool(r[0]) if r else None
            rec(f"B6_masul_alquran_can_manage_{domain}", actual == expected, f"can_manage({domain})={actual}, expected {expected}")
            conn.execute("ROLLBACK")
        except Exception as e:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            rec(f"B6_masul_alquran_can_manage_{domain}", False, f"Error: {e}")
# mudir can manage all
if mudir:
    for domain in ['alquran','wasilah','ghayah']:
        try:
            conn.execute("BEGIN")
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(mudir[0]),))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
            r = fetch1("select public.can_manage(%s::public.domain_kind)", (domain,))
            actual = bool(r[0]) if r else None
            rec(f"B6_mudir_can_manage_{domain}", actual is True, f"can_manage({domain})={actual}")
            conn.execute("ROLLBACK")
        except Exception as e:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            rec(f"B6_mudir_can_manage_{domain}", False, f"Error: {e}")

# B7: effective_days Rabiul Awwal per domain — HARUS 19 (keputusan final Mudir 24 Nov 2026)
if ra:
    rec("E_hari_efektif_rabiul_awwal_19", ra[2] == 19,
        f"Rabiul Awwal alquran effective_days={ra[2]} (harus 19, bukan 3).",
        {"month_id": str(ra[0]), "effective_days": ra[2]})
else:
    rec("E_hari_efektif_rabiul_awwal_19", False, "Baris Rabiul Awwal alquran tidak ditemukan di month_domain_settings.")

# B7b: tidak ada Hari Efektif yang mustahil secara fisik (harus 1..31).
try:
    aneh = fetchall(
        "select m.name, mds.domain::text, mds.effective_days from public.month_domain_settings mds "
        "join public.hijri_months m on m.id=mds.month_id "
        "where m.month_no between 1 and 12 and (mds.effective_days < 1 or mds.effective_days > 31)"
    )
    rec("E_tidak_ada_hari_efektif_janggal", aneh == [],
        f"{len(aneh)} baris Hari Efektif di luar 1..31", {"baris": [list(r) for r in aneh]})
except Exception as e:  # noqa: BLE001
    rec("E_tidak_ada_hari_efektif_janggal", False, f"Error: {type(e).__name__}: {e}")

# B7c: laporkan nilai di luar kebiasaan (5..31) sebagai CATATAN, bukan kegagalan,
# karena boleh jadi bulan pembuka tahun ajaran yang tidak penuh (menunggu jawaban Mudir).
try:
    luar_kebiasaan = fetchall(
        "select m.month_no, m.name, mds.effective_days from public.month_domain_settings mds "
        "join public.hijri_months m on m.id=mds.month_id "
        "where m.month_no between 1 and 12 and mds.effective_days < 5 order by m.month_no"
    )
    if luar_kebiasaan:
        print("CATATAN Hari Efektif < 5 hari (perlu konfirmasi Mudir):", [list(r) for r in luar_kebiasaan])
except Exception as e:  # noqa: BLE001
    print("CATATAN gagal membaca:", e)

# B8: check month_is_open function
if any_month:
    try:
        conn.execute("BEGIN")
        if mudir:
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(mudir[0]),))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        r = fetch1("select public.month_is_open(%s::uuid, %s::public.domain_kind)", (str(any_month[0]), 'alquran'))
        rec("B8_month_is_open_callable", True, f"month_is_open({any_month[1]})={r[0] if r else None}")
        conn.execute("ROLLBACK")
    except Exception as e:
        try: conn.execute("ROLLBACK")
        except Exception: pass
        rec("B8_month_is_open_callable", False, f"Error: {e}")

conn.close()
outpath = ROOT/'docs'/'qa'/f'db_tests_{datetime.date.today().isoformat()}.json'
outpath.parent.mkdir(parents=True, exist_ok=True)
outpath.write_text(json.dumps(out, indent=2, default=str), encoding='utf-8')
print('WROTE', outpath)
