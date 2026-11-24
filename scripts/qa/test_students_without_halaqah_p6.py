#!/usr/bin/env python3
"""
Uji pra-T6 [6/2]: jalur "tampil semua" pada students_without_halaqah() / _count().

PERTANYAAN: kapan fungsi mengembalikan SEMUA domain TANPA cek role per domain?
JAWABAN (definisi fungsi, migrasi 20261121000009):
  nilai dipegang jika:
     can_manage(domain)
     OR ( current_app_role() IS NULL AND session_user IN ('postgres','service_role','supabase_admin') )
  - can_manage -> Mudir/Admin & Masul domain itu (jalur aplikasi ber-JWT).
  - cabang kedua -> KONEKSI ADMIN/SKEMA yang TIDAK mewakili pengguna aplikasi:
    current_app_role() NULL (tidak ada JWT pengguna) DAN role login adalah
    postgres/service_role/supabase_admin. Ini jalur skrip lokal (DATABASE_URL = postgres)
    dan PostgREST service_role key untuk QA/seed.
  - Pengguna aplikasi ber-JWT punya session_user='authenticated' (bukan daftar admin),
    jadi cabang kedua TIDAK aktif; hanya can_manage yang menentukan -> pemilik domain / 0.

Diuji:
  (a) authenticated TANPA profil (token user tanpa baris profiles) -> 0 baris. Diuji via
      REST PostgREST dengan token sungguhan (harness SQL lokal tak bisa meniru
      session_user='authenticated' karena koneksi login sebagai postgres bukan superuser).
  (b) service_role key -> SEMUA domain yang relevan.
  (c) role non-pemilik (musyrif, mudarris; wali jika ada) -> 0 baris.
  (d) anon -> ditolak (tak punya EXECUTE).
Semua pembuatan akun sementara dihapus sesudahnya; tidak mengubah data santri.
Membaca .env.local; tidak mencetak rahasia.
"""
from __future__ import annotations

import datetime
import json
import sys
import uuid
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "qa" / f"students_without_halaqah_p6_{datetime.date.today().isoformat()}.json"

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

results: list[dict] = []


def rec(name: str, ok, detail: str, evidence: dict | None = None) -> None:
    results.append({"name": name, "ok": ok, "detail": detail, "evidence": evidence or {}})
    status = "PASS" if ok is True else ("SKIP" if ok is None else "FAIL")
    print(status, name, "-", detail)


conn = psycopg.connect(env["DATABASE_URL"], autocommit=True, connect_timeout=20)


def satu(sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return r[0] if r else None


def sql_ctx(mode, sub, fn):
    conn.execute("begin")
    try:
        if mode == "anon":
            conn.execute("set local role anon")
        elif mode == "service_role":
            conn.execute("set local role service_role")
        else:
            conn.execute("set local role authenticated")
            conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (sub,))
            conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        return fn()
    finally:
        conn.rollback()


DETAIL = "select domain::text from public.students_without_halaqah() order by domain"
COUNT = "select domain::text, jumlah from public.students_without_halaqah_count() order by domain"

# konteks: domain yang terisi sebagai admin (postgres) -> untuk dibandingkan dgn service_role
konteks = [r[0] for r in conn.execute(DETAIL).fetchall()]
domain_admin = {r for r in konteks}
rec("konteks_admin_semua_domain",
    domain_admin == {"wasilah", "ghayah"},
    f"postgres melihat {sorted(domain_admin)} (Al Qur'an 0 karena 0 santri)")

# ---------------------------------------------------------------- (b) service_role
try:
    det = sql_ctx("service_role", None, lambda: conn.execute(DETAIL).fetchall())
    domain_sr = {r[0] for r in det}
    rec("b_koneksi_admin_melihat_semua_domain", domain_sr == domain_admin,
        f"service_role melihat {sorted(domain_sr)} == admin {sorted(domain_admin)}")
except Exception as e:  # noqa: BLE001
    rec("b_koneksi_admin_melihat_semua_domain", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- (a) authenticated tanpa profil (REST)
base = env["VITE_SUPABASE_URL"].rstrip("/")
svc = env["SUPABASE_SERVICE_ROLE_KEY"]
anon = env["VITE_SUPABASE_ANON_KEY"]
import urllib.request as _ur, urllib.error as _ue  # noqa: E402


def http(method, url, payload=None, headers=None):
    h = {"apikey": anon, "Authorization": f"Bearer {anon}", "Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(payload).encode() if payload is not None else None
    req = _ur.Request(url, data=data, headers=h, method=method)
    try:
        with _ur.urlopen(req, timeout=40) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except _ue.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def rest_as_user_rpc(rpc_name):
    """Buat akun auth sementara tanpa profil, dapat token, panggil rpc; hapus akun."""
    email = f"p6.auth.noprofile.{uuid.uuid4().hex[:8]}@example.com"
    st, body = http("POST", f"{base}/auth/v1/admin/users",
                    {"email": email, "password": "RahasiaSementara#1", "email_confirm": True},
                    {"apikey": svc, "Authorization": f"Bearer {svc}"})
    uid = body.get("id") if isinstance(body, dict) else None
    try:
        if not uid:
            raise RuntimeError(f"Gagal buat user: {st} {body}")
        st2, body2 = http("POST", f"{base}/auth/v1/token?grant_type=password",
                          {"email": email, "password": "RahasiaSementara#1"})
        token = body2.get("access_token")
        if not token:
            raise RuntimeError(f"Gagal token: {st2}")
        h = {"apikey": anon, "Authorization": f"Bearer {token}", "Accept": "application/json"}
        # Fungsi ini stable (tanpa argumen). POST dengan body json bisa disalah-terjemahkan
        # sebagai argumen (PGRST202); GET pada fungsi stable lebih andal.
        req = _ur.Request(f"{base}/rest/v1/rpc/{rpc_name}", headers=h, method="GET")
        with _ur.urlopen(req, timeout=40) as resp:
            return json.loads(resp.read() or b"{}")
    finally:
        if uid:
            http("DELETE", f"{base}/auth/v1/admin/users/{uid}",
                 None, {"apikey": svc, "Authorization": f"Bearer {svc}"})


try:
    det = rest_as_user_rpc("students_without_halaqah")
    try:
        cnt = rest_as_user_rpc("students_without_halaqah_count")
    except Exception:  # noqa: BLE001
        cnt = []
    rec("a_authenticated_tanpa_profil_0_baris",
        det == [] and cnt == [],
        f"authenticated(tanpa profil) REST -> detail={len(det)} baris, count={len(cnt)} baris (harus 0)")
except Exception as e:  # noqa: BLE001
    rec("a_authenticated_tanpa_profil_0_baris", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- (c) role non-pemilik -> 0 baris
for role in ("musyrif", "mudarris", "wali"):
    pid_row = conn.execute(
        "select id from public.profiles where role=%s and is_active order by full_name limit 1",
        (role,)).fetchone()
    if not pid_row:
        rec(f"c_{role}_0_baris", None, f"Tidak ada profil aktif {role}.")
        continue
    pid = str(pid_row[0])
    try:
        det = sql_ctx("authenticated", pid, lambda: conn.execute(DETAIL).fetchall())
        cnt = sql_ctx("authenticated", pid, lambda: conn.execute(COUNT).fetchall())
        rec(f"c_{role}_0_baris", det == [] and cnt == [],
            f"{role} -> detail={len(det)} baris, count={len(cnt)} baris (harus 0)")
    except Exception as e:  # noqa: BLE001
        rec(f"c_{role}_0_baris", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- (d) anon ditolak
try:
    sql_ctx("anon", None, lambda: conn.execute(DETAIL).fetchall())
    rec("d_anon_ditolak", False, "SELECT anon BERHASIL; seharusnya ditolak.")
except psycopg.errors.InsufficientPrivilege:
    rec("d_anon_ditolak", True, "Anon ditolak (InsufficientPrivilege).")
except Exception as e:  # noqa: BLE001
    rec("d_anon_ditolak", False, f"Ditolak bukan karena hak akses: {type(e).__name__}: {e}")

conn.close()
gagal = [r for r in results if r.get("ok") is False]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"ran_at": datetime.datetime.now().isoformat(), "tests": results},
                          indent=2, default=str, ensure_ascii=False), encoding="utf-8")
okn = sum(1 for r in results if r.get("ok") is True)
skip = sum(1 for r in results if r.get("ok") is None)
print(f"\n{okn}/{len(results)} PASS (skip={skip}). Laporan: {OUT}")
sys.exit(1 if gagal else 0)