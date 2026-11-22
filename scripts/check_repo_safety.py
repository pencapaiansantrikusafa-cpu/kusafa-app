#!/usr/bin/env python3
"""
Pemeriksaan keamanan repo. Repo ini boleh PUBLIK hanya selama berisi data dummy dan tanpa rahasia.

    python scripts/check_repo_safety.py            # periksa semua berkas yang dilacak git
    python scripts/check_repo_safety.py --staged   # periksa hanya yang akan di-commit (dipakai hook pre-commit)

Gagal (kode 1) bila menemukan: berkas terlarang (.env, .xlsx, .zip, seed SQL, users.csv, berkas token, dll.),
kunci service_role / secret Supabase, token akses (JWT) apa pun, refresh token, atau URL database berisi kata sandi.
Isi rahasia TIDAK dicetak, hanya nama berkas dan nomor baris.
"""
import base64, fnmatch, json, re, subprocess, sys

FORBIDDEN = [".env", ".env.*", "*.xlsx", "*.xls", "*.csv", "*.zip", "supabase/seed/*.sql", "scripts/seed/output/*", "data/source/*", "*smoke-tokens*"]
ALLOWED = [".env.example", "data/source/.gitkeep", "supabase/seed/.gitkeep"]
# JWT apa pun (access token) dianggap rahasia, bukan hanya yang ber-role service_role.
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.([A-Za-z0-9_-]{10,})\.[A-Za-z0-9_-]{10,}")
REFRESH_TOKEN = re.compile(r"[\"']?refresh_token[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_-]{8,}[\"']")
SECRET_KEY = re.compile(r"sb_secret_[A-Za-z0-9_-]{10,}")
DB_URL = re.compile(r"postgres(?:ql)?://[^\s:@/]+:(?!PASSWORD\b|xxxx\b|password\b)[^\s@/]{4,}@")

def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout

def main():
    staged = "--staged" in sys.argv
    names = git("diff", "--cached", "--name-only", "--diff-filter=ACM").split("\n") if staged else git("ls-files").split("\n")
    problems = []
    for name in filter(None, names):
        if name not in ALLOWED and any(fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(name.split("/")[-1], pat) for pat in FORBIDDEN):
            problems.append(f"{name}: berkas terlarang (data santri atau rahasia) tidak boleh ada di repo.")
            continue
        try:
            raw = subprocess.run(["git", "show", (":" + name) if staged else ("HEAD:" + name)], capture_output=True, check=True).stdout
        except subprocess.CalledProcessError:
            try: raw = open(name, "rb").read()
            except OSError: continue
        if len(raw) > 2_000_000 or b"\0" in raw[:2000]: continue
        for no, line in enumerate(raw.decode("utf-8", "ignore").splitlines(), 1):
            for m in JWT.finditer(line):
                try:
                    payload = json.loads(base64.urlsafe_b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4)))
                except Exception:
                    payload = {}
                if payload.get("role") == "service_role":
                    problems.append(f"{name}:{no}: kunci service_role Supabase.")
                else:
                    problems.append(f"{name}:{no}: token akses (JWT) tidak boleh ada di repo.")
            if REFRESH_TOKEN.search(line): problems.append(f"{name}:{no}: refresh token tidak boleh ada di repo.")
            if SECRET_KEY.search(line): problems.append(f"{name}:{no}: kunci secret Supabase (sb_secret_...).")
            if DB_URL.search(line): problems.append(f"{name}:{no}: URL database berisi kata sandi.")
    if problems:
        print("PEMERIKSAAN KEAMANAN GAGAL:")
        for p in problems: print(" -", p)
        print("Jangan commit/push. Hapus berkas atau nilai itu; jika sudah pernah ter-push, putar (rotate) kuncinya di Supabase.")
        sys.exit(1)
    print("Pemeriksaan keamanan lolos.")

if __name__ == "__main__":
    main()
