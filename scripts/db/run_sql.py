#!/usr/bin/env python3
"""
Menjalankan file SQL (atau satu query) ke database Supabase tanpa perlu psql. Berjalan di Windows, macOS, dan Linux.
Membaca DATABASE_URL dari .env.local (atau dari variabel lingkungan). Nilainya tidak pernah dicetak.

Contoh:
    python scripts/db/run_sql.py supabase/seed/01_curriculum.sql
    python scripts/db/run_sql.py --query "select count(*) from public.students"
(Di Windows, jika 'python' tidak dikenali, coba 'py'.)
"""
import argparse, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def load_env():
    path = os.path.join(ROOT, ".env.local")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="file .sql yang dijalankan berurutan")
    ap.add_argument("--query", help="satu query; hasilnya ditampilkan")
    a = ap.parse_args()
    if not a.files and not a.query:
        ap.error("beri minimal satu file .sql atau --query")
    load_env()
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        sys.exit("DATABASE_URL belum diisi di .env.local.")
    try:
        import psycopg
    except ImportError:
        sys.exit("Pasang dulu: pip install -r scripts/seed/requirements.txt")
    try:
        with psycopg.connect(url, autocommit=True, connect_timeout=20) as conn:
            for f in a.files:
                conn.execute(open(f, encoding="utf-8").read())
                print("OK:", f)
            if a.query:
                cur = conn.execute(a.query)
                if cur.description:
                    print(" | ".join(c.name for c in cur.description))
                    for row in cur.fetchall():
                        print(" | ".join("" if v is None else str(v) for v in row))
                else:
                    print("OK")
    except Exception as e:   # tidak mencetak URL atau kata sandi
        sys.exit(f"Gagal: {type(e).__name__}: {str(e)[:600]}")

if __name__ == "__main__":
    main()
