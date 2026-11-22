#!/usr/bin/env python3
"""
Membuat akun dummy di Supabase Auth dari scripts/seed/output/users.csv (hasil build_seed.py).
Hanya memakai pustaka standar Python.

Pemakaian:
    isi SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY di .env.local (rahasia: JANGAN di-commit, JANGAN ada di frontend), lalu:
    python scripts/seed/create_auth_users.py

Akun asli sekolah dibuat manual lewat dashboard Supabase atau fitur kelola pengguna, bukan lewat skrip ini.
"""
import csv, json, os, sys, urllib.error, urllib.request

def load_env():
    """Baca .env.local di akar repo (tanpa mencetak nilainya) supaya tidak perlu 'export' manual."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", ".env.local")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

url = os.environ.get("SUPABASE_URL", "").rstrip("/")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
if not url or not key:
    sys.exit("Isi SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY dulu (lihat .env.example).")
path = os.path.join(os.path.dirname(__file__), "output", "users.csv")
if not os.path.exists(path):
    sys.exit("users.csv belum ada. Jalankan scripts/seed/build_seed.py dulu.")

made = skipped = 0
with open(path, newline="", encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        body = json.dumps({"email": row["email"], "password": row["password"], "email_confirm": True,
                           "user_metadata": {"full_name": row["full_name"]}}).encode()
        req = urllib.request.Request(url + "/auth/v1/admin/users", data=body, method="POST",
                                     headers={"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req)
            made += 1
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")
            if e.code in (409, 422) and ("already" in msg or "registered" in msg or "exists" in msg):
                skipped += 1
            else:
                sys.exit(f"Gagal membuat {row['email']}: HTTP {e.code} {msg[:200]}")
print(f"Selesai. Dibuat: {made}, sudah ada: {skipped}. Lanjut: jalankan supabase/seed/02_school_data.sql.")
