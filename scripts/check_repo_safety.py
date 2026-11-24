#!/usr/bin/env python3
"""
Pemeriksaan keamanan repo. Repo ini boleh PUBLIK hanya selama berisi data dummy dan tanpa rahasia.

    python scripts/check_repo_safety.py            # periksa semua berkas yang dilacak git
    python scripts/check_repo_safety.py --staged   # periksa hanya yang akan di-commit (dipakai hook pre-commit)

Gagal (kode 1) bila menemukan: berkas terlarang (.env, .xlsx, .zip, seed SQL, users.csv, berkas token, dll.),
JWT apa pun (termasuk kunci service_role Supabase dan token OIDC Vercel/VERCEL_OIDC_TOKEN), refresh token,
sekret Supabase baru (sb_secret_...), sekret mentah service_role, atau URL database berisi kata sandi.
Isi rahasia TIDAK dicetak, hanya nama berkas dan nomor baris.
"""
import base64
import fnmatch
import json
import re
import subprocess
import sys

FORBIDDEN = [".env", ".env.*", "*.xlsx", "*.xls", "*.csv", "*.zip",
             "supabase/seed/*.sql", "scripts/seed/output/*", "data/source/*"]
ALLOWED = [".env.example", "data/source/.gitkeep", "supabase/seed/.gitkeep"]

# JWT apa pun (access token) dianggap rahasia. 3 ruas base64url dipisah titik.
_JWT_SEG = r"[A-Za-z0-9_-]+"
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\." + _JWT_SEG + r"\." + _JWT_SEG)

# Token OIDC Vercel: penugasan env VERCEL_OIDC_TOKEN (bukan sekadar menyebut namanya)
# atau penanda issuer di payload token. Nilai OIDC sejatinya JWT; JWT irisan bawah
# (scan_text) juga menangkapnya lewat `iss` Vercel.
VERCEL_OIDC = re.compile(r"(?i)VERCEL_OIDC_TOKEN\s*=\s*['\"]?[^\s'\"#]+|https://oidc[._-]vercel\.com")

# Sekret Supabase gaya baru dan sekilas sekret service_role mentah (bukan JWT).
SB_SECRET = re.compile(r"sb_secret_[A-Za-z0-9]{8,}")
SERVICE_ROLE_RAW = re.compile(r"service_role[^\n]{0,16}?(?:[A-Za-z0-9_-]{20,})")

# Refresh token Supabase: nilai panjang tak bertitik di dekat kata kunci `refresh_token`.
REFRESH = re.compile(r"(?i)refresh_token[^\n]{0,8}[=:\s]['\"]?(?:[A-Za-z0-9_-]{80,})")

# URL database postgres yang memuat kata sandi (bukan placeholder).
DB_URL = re.compile(r"postgres(?:ql)?://[^\s:@/]+:(?!PASSWORD\b|xxxx\b|password\b|redacted\b)[^\s@/]{4,}@")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def scan_text(name, text):
    """Kembalikan daftar (baris, pesan) untuk teks yang di-scan."""
    found = []
    for no, line in enumerate(text.splitlines(), 1):
        # Eksplisit: tidak boleh ada placeholder berbahaya (jaga bila terjadi).
        if VERCEL_OIDC.search(line):
            found.append((no, "token OIDC Vercel (VERCEL_OIDC_TOKEN) tidak boleh ada di repo."))
        if SB_SECRET.search(line):
            found.append((no, "kunci secret Supabase (sb_secret_...) tidak boleh ada di repo."))
        if SERVICE_ROLE_RAW.search(line):
            found.append((no, "kunci service_role Supabase (mentah) tidak boleh ada di repo."))
        if DB_URL.search(line):
            found.append((no, "URL database berisi kata sandi."))
        if REFRESH.search(line):
            found.append((no, "refresh token tidak boleh ada di repo."))
        for m in JWT.finditer(line):
            token = m.group(0)
            # Blokir false-positive untuk contoh di dokumentasi (mis. "eyJ<isi>").
            if any(s in line for s in ("eyJ<", "eyJPAYLOAD", "<JWT>", "contoh")):
                continue
            payload = {}
            try:
                seg = token.split(".")[1]
                payload = json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))
            except Exception:
                payload = {}
            if payload.get("role") == "service_role":
                found.append((no, "kunci service_role Supabase (JWT)."))
            elif (payload.get("iss") or "").find("vercel") >= 0:
                found.append((no, "token OIDC Vercel (VERCEL_OIDC_TOKEN)."))
            else:
                found.append((no, "token akses (JWT) tidak boleh ada di repo."))
    return found


def main():
    staged = "--staged" in sys.argv
    if staged:
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACM").split("\n")
    else:
        names = git("ls-files").split("\n")
    problems = []
    for name in filter(None, names):
        if name not in ALLOWED and any(
            fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(name.split("/")[-1], pat)
            for pat in FORBIDDEN
        ):
            problems.append(f"{name}: berkas terlarang (data santri atau rahasia) tidak boleh ada di repo.")
            continue
        try:
            raw = subprocess.run(
                ["git", "show", (":" + name) if staged else ("HEAD:" + name)],
                capture_output=True, check=True,
            ).stdout
        except subprocess.CalledProcessError:
            try:
                raw = open(name, "rb").read()
            except OSError:
                continue
        if len(raw) > 2_000_000 or b"\0" in raw[:2000]:
            continue
        text = raw.decode("utf-8", "ignore")
        for no, msg in scan_text(name, text):
            problems.append(f"{name}:{no}: {msg}")
    if problems:
        print("PEMERIKSAAN KEAMANAN GAGAL:")
        for p in problems:
            print(" -", p)
        print("Jangan commit/push. Hapus berkas/nilai itu; bila sudah ter-push, putar (rotate) kuncinya di Supabase.")
        sys.exit(1)
    print("Pemeriksaan keamanan lolos.")


if __name__ == "__main__":
    main()