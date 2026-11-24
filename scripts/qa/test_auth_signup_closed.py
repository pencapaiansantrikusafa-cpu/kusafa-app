#!/usr/bin/env python3
"""
Uji pra-T6 [6/1]: signup publik tertutup, login akun dummy tiap role berhasil.

  A. GET /auth/v1/settings -> disable_signup = true.
  B. POST /auth/v1/signup dengan anon key -> DITOLAK (4xx, error_code signup_disabled).
     (Sebelumnya tertutup hanya karena provider email dimatikan; itu ikut mematikan
     login. Kini disable_signup=true sehingga login password tetap jalan.)
  C. Login password akun dummy satu per role -> 200 + profil terbaca.

Membaca .env.local + scripts/seed/output/users.csv; TIDAK mencetak kata sandi/token.
Jalankan: python scripts/qa/test_auth_signup_closed.py
"""
from __future__ import annotations

import csv
import datetime
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "qa" / f"auth_signup_closed_{datetime.date.today().isoformat()}.json"

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

base = env["VITE_SUPABASE_URL"].rstrip("/")
anon = env["VITE_SUPABASE_ANON_KEY"]
results: list[dict] = []


def rec(name, ok, detail, evidence=None):
    results.append({"name": name, "ok": ok, "detail": detail, "evidence": evidence or {}})
    print(("PASS" if ok else "FAIL"), name, "-", detail)


def http(method, url, payload=None, headers=None):
    h = {"apikey": anon, "Content-Type": "application/json", "Authorization": f"Bearer {anon}"}
    if headers:
        h.update(headers)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read() or b"{}")
        except Exception:  # noqa: BLE001
            body = {}
        return e.code, body


# ---------------------------------------------------------------- A. settings
st, body = http("GET", f"{base}/auth/v1/settings")
rec("A_disable_signup_true",
    st == 200 and body.get("disable_signup") is True,
    f"GET settings status={st}, disable_signup={body.get('disable_signup')}")

# ---------------------------------------------------------------- B. signup ditolak
st, body = http("POST", f"{base}/auth/v1/signup",
                {"email": f"p6.signup.probe+{uuid.uuid4().hex[:10]}@mailinator.com",
                 "password": "RahasiaSementara#1"})
ditutup = st >= 400 and body.get("error_code") == "signup_disabled"
rec("B_signup_ditolak", ditutup,
    f"POST signup status={st}, error_code={body.get('error_code') or body.get('msg')}",
    {"status": st})
if st < 400:
    # jangan tinggalkan akun uji: akun tak seharusnya tercipta, tapi bersihkan bila ada.
    rec("B_peringatan_akun_tercipta", False, "Signup DITERIMA padahal seharusnya ditutup.")

# ---------------------------------------------------------------- C. login tiap role
rows = list(csv.DictReader(open(ROOT / "scripts/seed/output/users.csv", encoding="utf-8")))
per_role = {}
for r in rows:
    per_role.setdefault(r["role"], r)
urut = ["mudir", "admin", "masul_alquran", "masul_wasilah", "masul_ghayah", "musyrif", "mudarris"]
for role in urut:
    r = per_role.get(role)
    if not r:
        rec(f"C_login_{role}", None, "Tidak ada akun dummy untuk role ini.")
        continue
    st, body = http("POST", f"{base}/auth/v1/token?grant_type=password",
                    {"email": r["email"], "password": r["password"]})
    if st != 200:
        rec(f"C_login_{role}", False, f"Login GAGAL status={st} ({body.get('error_description') or body.get('msg')})")
        continue
    token = body.get("access_token")
    st2, prof = http("GET", f"{base}/rest/v1/profiles?select=full_name,role,is_active&id=eq.{body['user']['id']}",
                     None, {"Authorization": f"Bearer {token}"})
    ok = st2 == 200 and isinstance(prof, list) and prof and prof[0].get("role") == role and prof[0].get("is_active")
    rec(f"C_login_{role}", bool(ok),
        f"login OK; profil role={(prof[0].get('role') if isinstance(prof, list) and prof else None)} aktif={(prof[0].get('is_active') if isinstance(prof, list) and prof else None)}")

gagal = [r for r in results if r["ok"] is False]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"ran_at": datetime.datetime.now().isoformat(), "tests": results},
                          indent=2, default=str, ensure_ascii=False), encoding="utf-8")
okn = sum(1 for r in results if r["ok"] is True)
skip = sum(1 for r in results if r["ok"] is None)
print(f"\n{okn}/{len(results)} PASS (skip={skip}). Laporan: {OUT}")
sys.exit(1 if gagal else 0)