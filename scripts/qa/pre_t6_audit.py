#!/usr/bin/env python3
"""
Audit pra-T6 KUSAFA. Membaca .env.local, tidak mencetak rahasia.
Menulis laporan ke docs/qa/pre-t6-audit-YYYY-MM-DD.md dan ringkasan JSON.
Uji tulis DB dibungkus transaksi dan ROLLBACK.
"""
from __future__ import annotations
import os, re, json, subprocess, sys, datetime, hashlib, base64, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_DATE = datetime.date.today().isoformat()
REPORT_MD = ROOT / "docs" / "qa" / f"pre-t6-audit-{REPORT_DATE}.md"
REPORT_JSON = ROOT / "docs" / "qa" / f"pre-t6-audit-{REPORT_DATE}.json"

SENSITIVE_PATTERNS = {
    "JWT(eyJ...)": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "service_role": re.compile(r"service_role", re.I),
    "postgres://|postgresql://": re.compile(r"postgres(?:ql)?://", re.I),
    "DATABASE_URL": re.compile(r"\bDATABASE_URL\b"),
    "SUPABASE_SERVICE_ROLE_KEY": re.compile(r"\bSUPABASE_SERVICE_ROLE_KEY\b"),
    "sb_secret_": re.compile(r"sb_secret_", re.I),
    "password=": re.compile(r"password\s*[:=]", re.I),
    ".env.local": re.compile(r"\.env\.local"),
    "users.csv": re.compile(r"users\.csv", re.I),
}
SECRET_VALUE_PATTERNS = {
    "JWT_VALUE": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "DB_URL_WITH_CREDS": re.compile(r"postgres(?:ql)?://[^\s'\"<>]+:[^\s'\"<>]+@[^\s'\"<>]+", re.I),
    "SERVICE_ROLE_KEY_ASSIGN": re.compile(r"SUPABASE_SERVICE_ROLE_KEY\s*=\s*[^\s'\"#]{20,}"),
    "SB_SECRET_VALUE": re.compile(r"sb_secret_[A-Za-z0-9_-]{10,}"),
}

results = []

def add(section, item, status, detail, risk="", evidence=""):
    results.append({
        "section": section, "item": item, "status": status,
        "detail": detail, "risk": risk, "evidence": evidence,
    })

def load_env():
    env = {}
    p = ROOT / ".env.local"
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def git(*args, check=False):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, errors="ignore", check=check)

def redact(s: str) -> str:
    s = re.sub(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "eyJ[REDACTED_JWT]", s)
    s = re.sub(r"postgres(?:ql)?://[^\s'\"<>]+", "postgres://[REDACTED]", s, flags=re.I)
    s = re.sub(r"sb_secret_[A-Za-z0-9_-]+", "sb_secret_[REDACTED]", s)
    s = re.sub(r"(SUPABASE_SERVICE_ROLE_KEY\s*=\s*)[^\s'\"#]+", r"\1[REDACTED]", s)
    s = re.sub(r"(DATABASE_URL\s*=\s*)[^\s'\"#]+", r"\1[REDACTED]", s)
    s = re.sub(r"(password\s*[:=]\s*)[^\s'\",]+", r"\1[REDACTED]", s, flags=re.I)
    s = re.sub(r"(VERCEL_OIDC_TOKEN\s*=\s*)[^\s'\"#]+", r"\1[REDACTED]", s)
    return s

def scan_git_history():
    commits = git("rev-list", "--all").stdout.strip().splitlines()
    findings = {k: set() for k in SENSITIVE_PATTERNS}
    value_findings = []
    for c in commits:
        show = git("show", "--unified=0", "--no-color", "--format=%H|%ad|%s", "--date=short", c).stdout
        header = show.splitlines()[0] if show else c
        for k, pat in SENSITIVE_PATTERNS.items():
            if pat.search(show):
                findings[k].add(c[:12])
        for k, pat in SECRET_VALUE_PATTERNS.items():
            m = pat.search(show)
            if not m:
                continue
            extra = ""
            if k == "JWT_VALUE":
                tok = m.group(0)
                try:
                    payload = json.loads(base64.urlsafe_b64decode(tok.split(".")[1] + "=="))
                    extra = f"role={payload.get('role')} ref={payload.get('ref')}"
                except Exception:
                    extra = "role=unparseable"
            # identify file
            fname = "?"
            for line in show.splitlines():
                if line.startswith("+++ b/"):
                    fname = line[6:]
                if pat.search(line):
                    fname = fname
                    break
            value_findings.append({"commit": c[:12], "header": header[:120], "type": k, "file": fname, "extra": extra})
    # de-dup value findings
    uniq = []
    seen = set()
    for v in value_findings:
        key = (v["commit"], v["type"], v["file"], v["extra"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(v)
    return len(commits), findings, uniq

def scan_dist():
    dist = ROOT / "dist"
    if not dist.exists():
        return None, []
    issues = []
    for p in dist.rglob("*"):
        if not p.is_file():
            continue
        data = p.read_bytes()
        if b"\x00" in data[:2048]:
            continue
        text = data.decode("utf-8", "ignore")
        for name, pat in {
            "service_role": re.compile(r"service_role", re.I),
            "DATABASE_URL": re.compile(r"DATABASE_URL"),
            "SUPABASE_SERVICE_ROLE_KEY": re.compile(r"SUPABASE_SERVICE_ROLE_KEY"),
            "postgres://": re.compile(r"postgres(?:ql)?://", re.I),
            "sb_secret_": re.compile(r"sb_secret_"),
        }.items():
            if pat.search(text):
                issues.append({"file": str(p.relative_to(ROOT)), "pattern": name})
        for m in re.finditer(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", text):
            tok = m.group(0)
            try:
                payload = json.loads(base64.urlsafe_b64decode(tok.split(".")[1] + "=="))
                role = payload.get("role")
            except Exception:
                role = "unparseable"
            issues.append({"file": str(p.relative_to(ROOT)), "pattern": f"JWT(role={role})"})
    # de-dup
    uniq = []
    seen=set()
    for i in issues:
        k=(i['file'],i['pattern'])
        if k not in seen: seen.add(k); uniq.append(i)
    return True, uniq

def db_connect(env):
    import psycopg
    url = env.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL tidak tersedia.")
    return psycopg.connect(url, autocommit=True, connect_timeout=20)

def check_views_functions(env):
    conn = db_connect(env)
    views = conn.execute("""
      select c.relname, pg_get_userbyid(c.relowner), coalesce((select option_value from pg_options_to_table(c.reloptions) where option_name='security_invoker'),'unset')
      from pg_class c join pg_namespace n on n.oid=c.relnamespace
      where n.nspname='public' and c.relkind='v' order by c.relname
    """).fetchall()
    funcs = conn.execute("""
      select p.proname, case when p.prosecdef then 'DEFINER' else 'INVOKER' end, pg_get_function_identity_arguments(p.oid)
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public' order by p.proname
    """).fetchall()
    # execute grants
    grant_rows = conn.execute("""
      select p.proname, pg_get_function_identity_arguments(p.oid), r.rolname, has_function_privilege(r.oid, p.oid, 'EXECUTE')
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      cross join pg_roles r
      where n.nspname='public' and r.rolname in ('anon','authenticated','public','service_role','postgres')
    """).fetchall()
    conn.close()
    grants_by_fn = {}
    for fn, args, role, can in grant_rows:
        grants_by_fn.setdefault(f"{fn}({args})", {})[role] = bool(can)
    return views, funcs, grants_by_fn

def anon_rest(env, path, method="GET", body=None, token=None):
    import json, urllib.request, urllib.error
    url = env["VITE_SUPABASE_URL"]
    anon = env["VITE_SUPABASE_ANON_KEY"]
    headers = {"apikey": anon, "Authorization": f"Bearer {token or anon}", "Content-Type": "application/json", "Prefer": "count=exact"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url + path, data=data, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode("utf-8", "ignore"), r.headers.get("content-range")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore"), e.headers.get("content-range")

def anon_access_test(env):
    tables = ["profiles","academic_years","hijri_months","month_domain_settings","students","guardians","student_levels","subjects","books","curriculum_items","halaqahs","halaqah_members","halaqah_teachers","halaqah_subjects","targets","progress_entries","attendance","monthly_notes"]
    views = ["v_monthly_report","v_monthly_report_base","v_attendance","v_months_ordered"]
    funcs = ["item_position","can_manage","create_academic_year","current_app_role","domain_of_book","domain_of_halaqah","domain_of_subject","is_any_masul","is_full_access","is_masul_of","is_staff","month_is_open","reorder_items","resequence_subject","student_in_taught_domain","student_in_taught_halaqah","teaches_halaqah_subject"]
    out = {"tables":{}, "views":{}, "rpc":{}}
    for t in tables:
        st, b, cr = anon_rest(env, f"/rest/v1/{t}?select=*&limit=1")
        out["tables"][t] = {"status": st, "content_range": cr}
    for v in views:
        st, b, cr = anon_rest(env, f"/rest/v1/{v}?select=*&limit=1")
        out["views"][v] = {"status": st, "content_range": cr}
    for f in funcs:
        st, b, cr = anon_rest(env, f"/rest/v1/rpc/{f}", method="POST", body={})
        out["rpc"][f] = {"status": st, "body_head": b[:80]}
    return out

def auth_signup_test(env):
    import json, urllib.request, urllib.error, time
    url = env["VITE_SUPABASE_URL"]
    anon = env["VITE_SUPABASE_ANON_KEY"]
    sr = env["SUPABASE_SERVICE_ROLE_KEY"]
    email = f"qa.signup.test.{int(time.time())}@gmail.com"
    pw = "QaTest!12345"
    body = json.dumps({"email": email, "password": pw}).encode()
    req = urllib.request.Request(url + "/auth/v1/signup", data=body, headers={"apikey": anon, "Authorization": f"Bearer {anon}", "Content-Type": "application/json"})
    status = None; resp = {}
    try:
        r = urllib.request.urlopen(req, timeout=20); status = r.status; resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        status = e.code
        try: resp = json.loads(e.read().decode())
        except Exception: resp = {"raw": "..."}
    uid = resp.get("id") or (resp.get("user") or {}).get("id")
    userobj = resp.get("user") or resp
    email_confirmed = userobj.get("email_confirmed_at")
    has_session = bool(resp.get("access_token") or (resp.get("session") or {}).get("access_token"))
    new_user_data_visible = None
    if uid:
        # try login (may fail if email confirmation required)
        body2 = json.dumps({"email": email, "password": pw}).encode()
        req3 = urllib.request.Request(url + "/auth/v1/token?grant_type=password", data=body2, headers={"apikey": anon, "Authorization": f"Bearer {anon}", "Content-Type": "application/json"})
        tok = None
        try:
            r3 = urllib.request.urlopen(req3, timeout=20); d3 = json.loads(r3.read()); tok = d3.get("access_token")
        except urllib.error.HTTPError:
            tok = None
        if tok:
            visible = {}
            for tbl in ["students", "progress_entries", "halaqahs", "v_monthly_report"]:
                st, b, cr = anon_rest(env, f"/rest/v1/{tbl}?select=*&limit=1", token=tok)
                visible[tbl] = {"status": st, "content_range": cr, "body_head": b[:60]}
            new_user_data_visible = visible
        # delete
        reqd = urllib.request.Request(url + f"/auth/v1/admin/users/{uid}", method="DELETE", headers={"apikey": sr, "Authorization": f"Bearer {sr}"})
        deleted = None
        try:
            rd = urllib.request.urlopen(reqd, timeout=20); deleted = rd.status
        except urllib.error.HTTPError as e:
            deleted = f"ERR {e.code}"
    return {"status": status, "user_id": uid, "email_confirmed_at": email_confirmed, "has_session": has_session,
            "error": resp.get("error_description") or resp.get("msg") or resp.get("error"),
            "new_user_data_visible": new_user_data_visible, "deleted": deleted}

def get_policies(env):
    conn = db_connect(env)
    rows = conn.execute("""
      select schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
      from pg_policies where schemaname='public' order by tablename, policyname
    """).fetchall()
    conn.close()
    return rows

def get_triggers(env):
    conn = db_connect(env)
    rows = conn.execute("""
      select tgname, relname, pg_get_triggerdef(t.oid, true)
      from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
      where n.nspname='public' and not t.tgisinternal
      order by relname, tgname
    """).fetchall()
    conn.close()
    return rows

def get_constraints(env):
    conn = db_connect(env)
    rows = conn.execute("""
      select c.conname, rel.relname, c.contype, pg_get_constraintdef(c.oid, true)
      from pg_constraint c join pg_class rel on rel.oid=c.conrelid join pg_namespace n on n.oid=rel.relnamespace
      where n.nspname='public' order by rel.relname, c.contype, c.conname
    """).fetchall()
    conn.close()
    return rows

def hijri_months_info(env):
    conn = db_connect(env)
    rows = conn.execute("""
      select m.month_no, m.name, ay.hijri_year, m.id
      from public.hijri_months m join public.academic_years ay on ay.id=m.academic_year_id
      order by ay.hijri_year, m.month_no
    """).fetchall()
    conn.close()
    return rows

def hari_efektif_info(env):
    conn = db_connect(env)
    rows = conn.execute("""
      select ay.hijri_year, m.name, m.month_no, s.code, mds.effective_days
      from public.month_domain_settings mds
      join public.hijri_months m on m.id=mds.hijri_month_id
      join public.academic_years ay on ay.id=m.academic_year_id
      join public.subjects s on s.id=mds.subject_id
      where m.name ilike '%rabi%' and m.name ilike '%awwal%'
      order by ay.hijri_year, s.code
    """).fetchall()
    conn.close()
    return rows

def dummy_nis_search():
    # search in data/source files for 1447.dummy-nis.023 and .024
    targets = ["1447.dummy-nis.023","1447.dummy-nis.024"]
    base = ROOT / "data" / "source"
    found = []
    if not base.exists():
        return found
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        try:
            if p.suffix.lower() in {".xlsx",".xls"}:
                # use openpyxl if available
                try:
                    import openpyxl
                    wb=openpyxl.load_workbook(p, read_only=True, data_only=True)
                    for ws in wb.worksheets:
                        for row in ws.iter_rows():
                            for cell in row:
                                v=str(cell.value) if cell.value is not None else ""
                                for t in targets:
                                    if t in v:
                                        found.append({"file": str(p.relative_to(ROOT)), "sheet": ws.title, "cell": cell.coordinate, "target": t})
                    wb.close()
                except Exception as e:
                    found.append({"file": str(p.relative_to(ROOT)), "error": str(e)[:120]})
            else:
                data=p.read_text(encoding='utf-8',errors='ignore')
                for t in targets:
                    if t in data:
                        found.append({"file": str(p.relative_to(ROOT)), "target": t, "kind": "text"})
        except Exception as e:
            found.append({"file": str(p.relative_to(ROOT)), "error": str(e)[:120]})
    return found
