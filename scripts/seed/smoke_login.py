#!/usr/bin/env python3
"""
Menguji login beberapa akun dummy ke Supabase Auth (bukan lewat browser).
Membaca kredensial dari scripts/seed/output/users.csv dan .env.local.
Kata sandi TIDAK pernah dicetak; hanya hasil berhasil/gagal dan role-nya.

    python scripts/seed/smoke_login.py
"""
import csv, json, os, sys, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def env():
    out = {}
    for line in open(os.path.join(ROOT, ".env.local"), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out

def post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

def get(url, token, apikey):
    req = urllib.request.Request(url, headers={"apikey": apikey, "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"[]")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"[]")

def main():
    e = env()
    base, anon = e["VITE_SUPABASE_URL"].rstrip("/"), e["VITE_SUPABASE_ANON_KEY"]
    rows = list(csv.DictReader(open(os.path.join(ROOT, "scripts/seed/output/users.csv"), encoding="utf-8")))
    # satu akun per role
    per_role = {}
    for r in rows:
        per_role.setdefault(r["role"], r)
    urut = ["mudir", "admin", "masul_alquran", "masul_wasilah", "masul_ghayah", "musyrif", "mudarris"]
    print(f"{'role':16s} {'login':8s} {'profil':8s} {'keterangan'}")
    gagal = 0
    for role in urut:
        r = per_role.get(role)
        if not r:
            continue
        st, body = post(f"{base}/auth/v1/token?grant_type=password",
                        {"email": r["email"], "password": r["password"]},
                        {"apikey": anon})
        if st != 200:
            print(f"{role:16s} {'GAGAL':8s} {'-':8s} status {st}: {body.get('error_description') or body.get('msg')}")
            gagal += 1
            continue
        token = body.get("access_token")
        st2, prof = get(f"{base}/rest/v1/profiles?select=full_name,role,is_active&id=eq.{body['user']['id']}", token, anon)
        if st2 == 200 and prof:
            print(f"{role:16s} {'OK':8s} {'OK':8s} profil role={prof[0]['role']} aktif={prof[0]['is_active']}")
        else:
            print(f"{role:16s} {'OK':8s} {'GAGAL':8s} status {st2}")
            gagal += 1
    print("\nSelesai." + ("" if gagal == 0 else f" {gagal} masalah."))
    sys.exit(1 if gagal else 0)

if __name__ == "__main__":
    main()