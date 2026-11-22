#!/usr/bin/env python3
"""
Membangun file seed SQL dari 5 file Excel di data/source/.

Pemakaian (dari akar repo):
    pip install -r scripts/seed/requirements.txt
    python scripts/seed/build_seed.py

Hasil:
    supabase/seed/01_curriculum.sql     kurikulum (bidang, buku, item dropdown)
    supabase/seed/02_school_data.sql    tahun ajaran, santri, halaqah, pengampu, target, capaian, presensi
    scripts/seed/output/users.csv       akun dummy untuk create_auth_users.py (JANGAN di-commit)
    scripts/seed/output/seed-report.md  daftar temuan, peringatan, dan galat

Aturan: skrip ini tidak menebak. Jika ada data yang tidak dikenali, skrip berhenti dan
menulis alasannya di seed-report.md. Satu-satunya aturan yang dipakai saat seed adalah yang
tertulis di docs/DATA-NOTES.md.
"""
import argparse, csv, glob, os, re, secrets, sys, uuid
from collections import Counter, OrderedDict, defaultdict
from openpyxl import load_workbook

# ---------------------------------------------------------------- konfigurasi
ACADEMIC_HIJRI_YEAR = 1447            # tahun Hijriyah saat Syawwal dimulai (ubah jika perlu)
ACADEMIC_NAME = "1447/1448 H"
EMAIL_DOMAIN = "kusafa.test"          # akun dummy saja; akun asli dibuat manual
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "data", "source")
OUT_SQL = os.path.join(ROOT, "supabase", "seed")
OUT_REP = os.path.join(ROOT, "scripts", "seed", "output")

MONTHS = ["Data Awal", "Syawwal", "Dzul Qa'dah", "Dzul Hijjah", "Muharram", "Shafar",
          "Rabiul Awwal", "Rabiul Akhir", "Jumadal Ula", "Jumadal Akhir", "Rajab", "Sya'ban", "Ramadhan"]
ROLE_MAP = {"Mudir": "mudir", "Admin": "admin", "Masul Al Quran": "masul_alquran",
            "Masul Wasilah": "masul_wasilah", "Masul Ghayah": "masul_ghayah",
            "Musyrif/ah": "musyrif", "Mudarris/ah": "mudarris"}
# Materi/bidang di file halaqah -> nama bidang di dropdown (huruf besar-kecil diabaikan)
MATERI_ALIAS = {"iman dan adab": "Adab dan Iman"}
KNOWN_BAD = ["BerHisab", "diHisab", "PengHisab", "Hisab Selisih"]   # sisa Find & Replace "Hitung" -> "Hisab"

NS = uuid.UUID("6f1c0a4e-5b7d-4c1e-9a52-0d1f3c9b7a10")
errors, warnings, infos = [], [], []

def uid(*p):
    return str(uuid.uuid5(NS, "|".join(str(x) for x in p)))

def lit(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, int): return str(v)
    if isinstance(v, float): return str(int(v)) if v.is_integer() else repr(v)
    return "'" + str(v).replace("'", "''") + "'"

LABEL_RE = re.compile(r"^(Halaman \d+|.+ : \d+)$")

def row_shift(r):
    """Cari pergeseran kolom (0-2) tempat label capaian paling banyak cocok dengan tata letak sheet."""
    best = (-1, 0)
    for sh in (0, 1, 2):
        score = 0
        for idx in range(13):
            for off in (5, 7, 9):
                c = 11 + 11 * idx + off + sh
                if c < len(r) and isinstance(r[c], str) and LABEL_RE.match(r[c].strip()): score += 1
        if score > best[0]: best = (score, sh)
    return best[1]

def txt(v):
    if v is None: return None
    if isinstance(v, float) and v.is_integer(): v = int(v)
    s = str(v).strip()
    return s or None

def num(v):
    if v is None or v == "": return None
    if isinstance(v, (int, float)): return float(v)
    try: return float(str(v).strip().replace(",", "."))
    except ValueError: return None

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s

def find_file(prefix):
    hits = [p for p in glob.glob(os.path.join(SRC, prefix + "*.xlsx")) if not os.path.basename(p).startswith("~$")]
    if not hits: errors.append(f"File berawalan '{prefix}' tidak ada di data/source/."); return None
    if len(hits) > 1: errors.append(f"Ada lebih dari satu file berawalan '{prefix}': {[os.path.basename(h) for h in hits]}. Sisakan satu.")
    return sorted(hits)[0]

def rows(path, sheet=None, min_row=1):
    wb = load_workbook(path, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    return [list(r) for r in ws.iter_rows(min_row=min_row, values_only=True)]

def norm_level(s):
    s = txt(s)
    if s is None: return None
    s = re.sub(r"(?i)^level", "Level", s)
    s = s.replace("Al-Qur'an", "Al Qur'an")
    return s

def gender_of_name(name, role):
    if role in ("mudir", "admin"): return None
    return "P" if re.match(r"(?i)^usth", name) else "L"

# ---------------------------------------------------------------- baca dropdown
def read_dropdown(path):
    """return subjects (OrderedDict), books (OrderedDict), items (list)"""
    wb = load_workbook(path, data_only=True)
    subjects, books, items = OrderedDict(), OrderedDict(), []
    for sheet, domain in (("Al Quran", "alquran"), ("Ilmu Wasilah", "wasilah"), ("Ilmu Ghayah", "ghayah")):
        if sheet not in wb.sheetnames:
            errors.append(f"Sheet '{sheet}' tidak ada di file dropdown."); continue
        for r in wb[sheet].iter_rows(min_row=2, values_only=True):
            if r[0] is None and r[2] is None: continue
            no, _kel, bidang, buku, detail, satuan = r[0], r[1], txt(r[2]), txt(r[3]), txt(r[4]), txt(r[5])
            value = num(r[6]) if domain == "alquran" and len(r) > 6 else None
            if not (bidang and buku and detail):
                errors.append(f"[{sheet}] baris No={no} tidak lengkap (bidang/buku/detail kosong)."); continue
            if domain == "alquran" and value is None:
                errors.append(f"[{sheet}] {buku} / {detail}: kolom Value kosong."); continue
            if bidang not in subjects:
                subjects[bidang] = {"domain": domain, "units": Counter(), "order": len(subjects)}
            subjects[bidang]["units"][satuan or ""] += 1
            key = (bidang, buku)
            if key not in books:
                books[key] = {"subject": bidang, "name": buku, "order": sum(1 for k in books if k[0] == bidang), "n": 0}
            books[key]["n"] += 1
            items.append({"no": no, "domain": domain, "subject": bidang, "book": buku, "detail": detail,
                          "value": value, "seq": books[key]["n"]})
    # sisa Find & Replace
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            for c in r:
                if isinstance(c, str) and any(b in c for b in KNOWN_BAD):
                    errors.append(f"Sisa penggantian 'Hitung'->'Hisab' di sheet '{ws.title}': {c[:70]!r}. "
                                  "Hanya nama bidang yang boleh 'Hisab'; kata lain (Berhitung, dihitung, Hitung Selisih) harus kembali.")
                    return subjects, books, items
    return subjects, books, items

def finish_books(subjects, books, items):
    """stage_order, value_offset, is_cyclic, cycle_length per buku."""
    by_book = defaultdict(list)
    for it in items: by_book[(it["subject"], it["book"])].append(it)
    for key, b in books.items():
        its = by_book[key]; dom = subjects[b["subject"]]["domain"]
        b["domain"] = dom; b["stage_order"] = b["order"] + 1; b["is_cyclic"] = False; b["cycle_length"] = None; b["offset"] = 0.0
        if dom == "alquran":
            vals = [i["value"] for i in its]
            b["first"], b["last"] = min(vals), max(vals)
            if b["subject"] == "Tilawah" and b["name"] == "Al Qur'an":
                b["is_cyclic"] = True; b["cycle_length"] = int(b["last"] - b["first"] + 1)
    # Iqro' = jalur alternatif Karima: posisi akhir Iqro' disejajarkan dengan akhir Karima
    if ("Tilawah", "Karima") in books:
        iq = [b for k, b in books.items() if k[0] == "Tilawah" and b["name"].startswith("Iqro'")]
        if iq:
            iq_last = max(b["last"] for b in iq); kar_last = books[("Tilawah", "Karima")]["last"]
            for b in iq: b["offset"] = float(kar_last - iq_last); b["stage_order"] = books[("Tilawah", "Karima")]["stage_order"]
            infos.append(f"Iqro' dijajarkan ke Karima: value_offset = {kar_last - iq_last:g} (akhir Iqro' {iq_last:g} -> akhir Karima {kar_last:g}).")
    # Wasilah/Ghayah: value = nomor urut baris dalam buku; offset = jumlah item buku-buku sebelumnya di bidang yang sama
    for sname, s in subjects.items():
        if s["domain"] == "alquran": continue
        run = 0
        for key, b in books.items():
            if key[0] != sname: continue
            b["offset"] = float(run); run += b["n"]
    for it in items:
        if it["domain"] != "alquran": it["value"] = float(it["seq"])
    # validasi kontinuitas dan urutan
    for sname, s in subjects.items():
        if s["domain"] != "alquran": continue
        bl = [b for k, b in books.items() if k[0] == sname and not b["name"].startswith("Iqro'")]
        prev = None
        for b in bl:
            if prev is not None and b["first"] != prev["last"] + 1 and sname != "Tahfidz":
                warnings.append(f"Nilai {sname}: {prev['name']} berakhir di {prev['last']:g}, {b['name']} mulai di {b['first']:g} (tidak kontinu).")
            prev = b
    th = [i["value"] for i in items if i["subject"] == "Tahfidz"]
    drops = sum(1 for a, b in zip(th, th[1:]) if b < a)
    if drops: errors.append(f"Nilai Tahfidz turun di {drops} tempat (harus naik terus).")

# ---------------------------------------------------------------- baca data sekolah
def read_users(path):
    users = []
    for r in rows(path, min_row=2):
        if not r[0]: continue
        name, role = txt(r[0]), txt(r[1])
        if role not in ROLE_MAP: errors.append(f"Role tidak dikenal untuk '{name}': {role!r}"); continue
        users.append({"name": name, "role": ROLE_MAP[role], "email": f"{slug(name)}@{EMAIL_DOMAIN}"})
    return users

def read_quran(path):
    ws = load_workbook(path, data_only=True).worksheets[0]
    data = []
    for r in ws.iter_rows(min_row=5, values_only=True):
        if not r[1]: continue
        data.append(list(r))
    return data

def read_wasilah(path):
    wb = load_workbook(path, data_only=True)
    members = [(txt(r[0]), txt(r[1]), norm_level(r[2])) for r in wb["Halaqah Ilmu Wasilah"].iter_rows(min_row=4, values_only=True) if r[0]]
    sched = []
    for r in wb["Jadwal Ilmu Wasilah"].iter_rows(min_row=4, values_only=True):
        if r[0] and r[2] and r[3]:
            sched.append({"days": txt(r[0]), "kbm": int(re.sub(r"\D", "", txt(r[1]))), "materi": txt(r[2]),
                          "level": norm_level(r[3]), "teacher": txt(r[4])})
    return members, sched

def read_ghayah(path):
    out = []
    for r in rows(path, min_row=4):
        if not r[6]: continue
        out.append({"kelompok": txt(r[1]), "kategori": txt(r[2]), "muallim": txt(r[3]), "pendamping": txt(r[4]),
                    "materi": txt(r[5]), "nis": txt(r[6]), "nama": txt(r[7])})
    return out

# ---------------------------------------------------------------- pembangunan
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto-align-columns", action="store_true",
                    help="geser otomatis baris santri yang kolom capaiannya bergeser 1-2 kolom (lihat docs/DATA-NOTES.md); semua baris yang digeser dicatat di laporan")
    ap.add_argument("--allow-known-issues", action="store_true",
                    help="hanya untuk uji coba: abaikan galat sisa penggantian 'Hisab' (jangan dipakai untuk seed sungguhan)")
    args = ap.parse_args()
    os.makedirs(OUT_SQL, exist_ok=True); os.makedirs(OUT_REP, exist_ok=True)

    f_user, f_dd, f_q, f_w, f_g = (find_file(p) for p in ("1-", "2-", "3-", "4-", "5-"))
    if errors: return finish(args, None)
    subjects, books, items = read_dropdown(f_dd)
    if args.allow_known_issues:
        errors[:] = [e for e in errors if "Sisa penggantian" not in e]
    finish_books(subjects, books, items)
    users = read_users(f_user); user_names = {u["name"]: u for u in users}
    quran = read_quran(f_q); w_members, w_sched = read_wasilah(f_w); g_rows = read_ghayah(f_g)

    # ---- tahun ajaran & bulan
    ay = uid("ay", ACADEMIC_HIJRI_YEAR)
    month_id = {i: uid("month", ACADEMIC_HIJRI_YEAR, i) for i in range(13)}

    # ---- santri
    students = OrderedDict()
    def add_student(nis, nama, gender=None, angkatan=None):
        s = students.setdefault(nis, {"nis": nis, "nama": nama, "gender": None, "angkatan": None})
        if gender and not s["gender"]: s["gender"] = gender
        if angkatan and not s["angkatan"]: s["angkatan"] = int(angkatan)
        if s["nama"] != nama: warnings.append(f"Nama beda untuk NIS {nis}: {s['nama']!r} vs {nama!r}")
    for r in quran: add_student(txt(r[1]), txt(r[3]), txt(r[4]), num(r[2]))
    for nis, nama, _lv in w_members: add_student(nis, nama)
    for g in g_rows: add_student(g["nis"], g["nama"], "L" if g["kategori"] == "Putra" else "P" if g["kategori"] == "Putri" else None)
    for s in students.values():
        if not s["gender"]: errors.append(f"Jenis kelamin santri {s['nis']} tidak diketahui.")
    qg = {txt(r[1]): txt(r[4]) for r in quran}
    for g in g_rows:
        exp = "L" if g["kategori"] == "Putra" else "P"
        if qg.get(g["nis"]) and qg[g["nis"]] != exp:
            warnings.append(f"Gender bertentangan untuk {g['nis']}: Al Quran {qg[g['nis']]} vs Ghayah {g['kategori']}.")
    sid = lambda nis: uid("student", nis)

    # ---- level santri & halaqah
    levels = []   # (nis, domain, label)
    for r in quran:
        lv = norm_level(r[7])
        if lv: levels.append((txt(r[1]), "alquran", lv))
    for nis, _n, lv in w_members:
        if lv: levels.append((nis, "wasilah", lv))
    halaqahs = OrderedDict(); h_sub, h_teach, h_mem = [], [], []
    def teacher_email(name, ctx):
        if name not in user_names: errors.append(f"Pengampu '{name}' ({ctx}) tidak ada di file User and Role."); return None
        return user_names[name]["email"]
    # Al Quran
    for r in quran:
        code = txt(r[5]); 
        if not code: continue
        if code not in halaqahs:
            cat = "Putra" if "-PA-" in code else "Putri" if "-PI-" in code else None
            halaqahs[code + "|alquran"] = {"id": uid("halaqah", "alquran", code), "domain": "alquran", "code": code, "name": code,
                                         "category": cat, "level": None}
            halaqahs[code] = halaqahs[code + "|alquran"]
            for sj in ("Tilawah", "Tahfidz", "Kitabah"):
                if sj in subjects: h_sub.append((halaqahs[code]["id"], sj))
            m = txt(r[6]); e = teacher_email(m, f"musyrif {code}") if m else None
            if e: h_teach.append((halaqahs[code]["id"], e, None, None, None, "utama"))
        h_mem.append((halaqahs[code]["id"], txt(r[1])))
    # Wasilah (satu halaqah = satu Level)
    w_levels = sorted({lv for _n, _m, lv in w_members if lv} | {s["level"] for s in w_sched})
    for lv in w_levels:
        hid = uid("halaqah", "wasilah", lv)
        halaqahs[lv + "|wasilah"] = {"id": hid, "domain": "wasilah", "code": lv, "name": lv, "category": None, "level": lv}
    seen = set()
    for s in w_sched:
        hid = halaqahs[s["level"] + "|wasilah"]["id"]
        for mat in [m.strip() for m in s["materi"].split(",")]:
            mat_n = MATERI_ALIAS.get(mat.lower(), mat)
            match = [k for k in subjects if k.lower() == mat_n.lower() and subjects[k]["domain"] == "wasilah"]
            if not match: errors.append(f"Materi jadwal '{mat}' (Level {s['level']}) tidak ada di dropdown Wasilah."); continue
            if (hid, match[0]) not in seen: h_sub.append((hid, match[0])); seen.add((hid, match[0]))
            e = teacher_email(s["teacher"], f"jadwal {s['level']} {mat}")
            if e: h_teach.append((hid, e, match[0], s["days"], s["kbm"], "utama"))
    for nis, _n, lv in w_members:
        if lv: h_mem.append((halaqahs[lv + "|wasilah"]["id"], nis))
    no_sched = [lv for lv in w_levels if not any(s["level"] == lv for s in w_sched)]
    if no_sched: infos.append(f"Halaqah Wasilah tanpa jadwal/pengampu (sesuai keterangan Mudir): {', '.join(no_sched)}.")
    # Ghayah
    gk = OrderedDict()
    for g in g_rows: gk.setdefault((g["kelompok"], g["kategori"]), []).append(g)
    multi = Counter(k[0] for k in gk)
    for (kel, kat), mem in gk.items():
        code = f"{kel} {kat}" if multi[kel] > 1 else kel
        hid = uid("halaqah", "ghayah", code)
        halaqahs[code + "|ghayah"] = {"id": hid, "domain": "ghayah", "code": code, "name": code, "category": kat, "level": None}
        materi = {m["materi"] for m in mem}
        if len(materi) != 1: errors.append(f"{code}: materi tidak tunggal: {sorted(map(str, materi))}")
        mat = next(iter(materi)); mat_n = MATERI_ALIAS.get((mat or "").lower(), mat)
        match = [k for k in subjects if k.lower() == (mat_n or "").lower() and subjects[k]["domain"] == "ghayah"]
        if not match: errors.append(f"{code}: materi '{mat}' tidak ada di dropdown Ghayah ({[k for k in subjects if subjects[k]['domain']=='ghayah']}).")
        else: h_sub.append((hid, match[0]))
        for fld, role in (("muallim", "utama"), ("pendamping", "pendamping")):
            nm = mem[0][fld]
            if nm:
                e = teacher_email(nm, code)
                if e: h_teach.append((hid, e, match[0] if match else None, None, None, role))
        for m in mem: h_mem.append((hid, m["nis"]))

    # ---- item dropdown per bidang
    item_id = lambda it: uid("item", it["domain"], it["subject"], it["book"], it["seq"])
    by_subject_book_detail, by_subject_detail = {}, defaultdict(list)
    for it in items:
        by_subject_book_detail[(it["subject"], it["book"], it["detail"])] = it
        by_subject_detail[(it["subject"], it["detail"])].append(it)

    def map_label(subject, label):
        label = txt(label)
        if label is None: return None
        if subject == "Tilawah":
            m = re.match(r"^Halaman (\d+)$", label)
            if m: return by_subject_book_detail.get(("Tilawah", "Al Qur'an", m.group(1)))
        m = re.match(r"^(.*?)\s*:\s*(\d+)$", label)
        if m:
            hit = by_subject_book_detail.get((subject, m.group(1), m.group(2)))
            if hit: return hit
        hits = by_subject_detail.get((subject, label), [])
        return hits[0] if len(hits) == 1 else None

    # ---- capaian, presensi, target Al Quran
    progress, attendance, targets, flags, unmapped, shifted = [], [], [], [], [], []
    h_ignored = 0
    he_by_month = defaultdict(Counter)
    col = {"Tilawah": 5, "Tahfidz": 7, "Kitabah": 9}   # offset label dari kolom awal periode
    for r in quran:
        nis = txt(r[1]); hlq = txt(r[5]); hid = halaqahs[hlq]["id"]
        for sj, ci in (("Tilawah", 8), ("Tahfidz", 9), ("Kitabah", 10)):
            amt = num(r[ci])
            if amt is None:
                if r[ci] is not None: warnings.append(f"Target {sj} {nis} tidak terbaca: {r[ci]!r}")
                continue
            if amt == 0: flags.append(f"Target {sj} bernilai 0 untuk {nis}.")
            targets.append((uid("target", nis, sj), sj, sid(nis), amt))
        putaran = 1; last_page = None
        sh = row_shift(r)
        if sh:
            shifted.append((nis, sh))
        for idx in range(13):
            start = 11 + 11 * idx + (sh if args.auto_align_columns else 0)          # indeks 0-based: kolom 12 = indeks 11
            if start + 10 >= len(r): break
            he, h, s_, i_, a_ = (num(r[start + k]) for k in range(5))
            if he is not None:
                he_by_month[idx][he] += 1
                attendance.append((sid(nis), month_id[idx], "alquran", int(i_ or 0), int(s_ or 0), int(a_ or 0), int(he), idx, nis))
                if h is not None and he - (int(i_ or 0) + int(s_ or 0) + int(a_ or 0)) != h:
                    h_ignored += 1   # kolom H diabaikan (keputusan Mudir); Hadir dihitung dari HE - (S+I+A)
            for sj, off in col.items():
                label = r[start + off]
                if label is None: continue
                it = map_label(sj, label)
                if not it:
                    unmapped.append((nis, MONTHS[idx], sj, txt(label))); continue
                put = 1
                if sj == "Tilawah" and books[(it["subject"], it["book"])]["is_cyclic"]:
                    page = int(it["detail"])
                    if last_page is not None and page < last_page:
                        if last_page >= 450 and page <= 150:
                            putaran += 1; flags.append(f"Khatam terdeteksi (putaran {putaran}): {nis}, {MONTHS[idx]}, halaman {last_page} -> {page}.")
                        else:
                            flags.append(f"Tilawah mundur (dianggap pengulangan): {nis}, {MONTHS[idx]}, halaman {last_page} -> {page}.")
                    last_page = page; put = putaran
                progress.append((uid("pe", nis, sj, idx), sid(nis), hid, sj, month_id[idx], item_id(it), put))
    if shifted:
        if args.auto_align_columns:
            warnings.append(f"{len(shifted)} baris santri digeser otomatis (--auto-align-columns): " + ", ".join(f"{n} (+{k})" for n, k in shifted))
        else:
            errors.append(f"{len(shifted)} baris santri di sheet Al Quran memiliki kolom Data Awal/capaian/presensi bergeser 1-2 kolom "
                          "dari tata letak (HE, H, S, I, A, lalu pasangan label-nilai). Perbaiki di Excel, atau jalankan dengan --auto-align-columns. "
                          "Baris: " + ", ".join(f"{n} (+{k})" for n, k in shifted))
            unmapped.clear()
    if unmapped:
        for u in unmapped[:40]: errors.append(f"Label capaian tidak dikenali: santri {u[0]}, {u[1]}, {u[2]}: {u[3]!r}")
        if len(unmapped) > 40: errors.append(f"... dan {len(unmapped) - 40} label lain tidak dikenali.")
    eff = {}
    for idx, c in he_by_month.items():
        eff[idx] = int(c.most_common(1)[0][0])
    # Hari Efektif per domain = angka yang paling sering. Santri dengan angka lain (misalnya masuk terlambat)
    # dicatat sebagai override per santri (attendance.effective_days_override), hanya boleh diubah Mudir/Admin.
    ov = Counter()
    att_final = []
    for (st, mo, dom, iz, sk, al, he, idx, nis) in attendance:
        o = he if he != eff.get(idx) else None
        if o is not None: ov[(MONTHS[idx], he)] += 1
        att_final.append((st, mo, dom, iz, sk, al, o))
    attendance = att_final
    for (mname, he), n in sorted(ov.items()):
        infos.append(f"Hari Efektif khusus santri: {n} santri memakai {he} hari pada {mname} (angka domain: {eff[[i for i, m in enumerate(MONTHS) if m == mname][0]]}).")

    # ---- keluarkan SQL
    if errors: return finish(args, None)
    def batches(seq, n=400):
        for i in range(0, len(seq), n): yield seq[i:i + n]
    L1 = ["-- Dibuat oleh scripts/seed/build_seed.py. JANGAN diubah manual; ubah file Excel lalu jalankan ulang.",
          "begin;"]
    L1.append("truncate public.curriculum_items, public.books, public.subjects cascade;")
    for sname, s in subjects.items():
        unit = (s["units"].most_common(1)[0][0] or "unit").lower()
        L1.append("insert into public.subjects (id, domain, code, name, unit, sort_order) values "
                  f"({lit(uid('subject', sname))}, {lit(s['domain'])}, {lit(slug(sname).replace('-', '_'))}, {lit(sname)}, {lit(unit)}, {s['order']});")
    brow = []
    for (sname, bname), b in books.items():
        brow.append(f"({lit(uid('book', sname, bname))}, {lit(uid('subject', sname))}, {lit(bname)}, {b['stage_order']}, {lit(b['is_cyclic'])}, "
                    f"{lit(b['cycle_length'])}, {lit(b['offset'])}, {b['order']})")
    L1.append("insert into public.books (id, subject_id, name, stage_order, is_cyclic, cycle_length, value_offset, sort_order) values\n" + ",\n".join(brow) + ";")
    for chunk in batches(items):
        vals = [f"({lit(item_id(i))}, {lit(uid('book', i['subject'], i['book']))}, {lit(i['book'] + ' - ' + i['detail'])}, {lit(i['detail'])}, "
                f"{lit(i['value'])}, {i['seq']}, {lit(int(i['no']) if isinstance(i['no'], (int, float)) else None)})" for i in chunk]
        L1.append("insert into public.curriculum_items (id, book_id, label, detail, value, seq, legacy_id) values\n" + ",\n".join(vals) + ";")
    L1.append("commit;")

    L2 = ["-- Dibuat oleh scripts/seed/build_seed.py. Jalankan SETELAH 01_curriculum.sql dan create_auth_users.py.", "begin;"]
    L2.append("do $$ begin if (select count(*) from auth.users where email like '%@" + EMAIL_DOMAIN + "') < " + str(len(users)) +
              " then raise exception 'Akun dummy belum dibuat. Jalankan scripts/seed/create_auth_users.py dulu.'; end if; end $$;")
    L2.append("truncate public.progress_entries, public.attendance, public.monthly_notes, public.targets, public.halaqah_members, "
              "public.halaqah_teachers, public.halaqah_subjects, public.halaqahs, public.student_levels, public.students, "
              "public.month_domain_settings, public.hijri_months, public.academic_years cascade;")
    L2.append(f"insert into public.academic_years (id, hijri_year, name, is_active) values ({lit(ay)}, {ACADEMIC_HIJRI_YEAR}, {lit(ACADEMIC_NAME)}, true);")
    L2.append("insert into public.hijri_months (id, academic_year_id, month_no, name, semester) values\n" + ",\n".join(
        f"({lit(month_id[i])}, {lit(ay)}, {i}, {lit(MONTHS[i])}, {'null' if i == 0 else (1 if i <= 6 else 2)})" for i in range(13)) + ";")
    if eff:
        L2.append("insert into public.month_domain_settings (month_id, domain, effective_days) values\n" + ",\n".join(
            f"({lit(month_id[i])}, 'alquran', {d})" for i, d in sorted(eff.items())) + ";")
    L2.append("insert into public.profiles (id, full_name, role, gender)\nselect u.id, v.full_name, v.role::public.app_role, v.gender::public.gender_kind\n"
              "from auth.users u join (values\n" + ",\n".join(
                  f"({lit(x['email'])}, {lit(x['name'])}, {lit(x['role'])}, {lit(gender_of_name(x['name'], x['role']))})" for x in users) +
              "\n) as v(email, full_name, role, gender) on u.email = v.email\non conflict (id) do update set full_name = excluded.full_name, role = excluded.role, gender = excluded.gender;")
    for chunk in batches(list(students.values())):
        L2.append("insert into public.students (id, nis, full_name, gender, angkatan) values\n" + ",\n".join(
            f"({lit(sid(s['nis']))}, {lit(s['nis'])}, {lit(s['nama'])}, {lit(s['gender'])}, {lit(s['angkatan'])})" for s in chunk) + ";")
    L2.append("insert into public.student_levels (student_id, academic_year_id, domain, level_label) values\n" + ",\n".join(
        f"({lit(sid(n))}, {lit(ay)}, {lit(d)}, {lit(lv)})" for n, d, lv in levels) + ";")
    hl = [h for k, h in halaqahs.items() if "|" in k]
    L2.append("insert into public.halaqahs (id, academic_year_id, domain, code, name, category, level_label) values\n" + ",\n".join(
        f"({lit(h['id'])}, {lit(ay)}, {lit(h['domain'])}, {lit(h['code'])}, {lit(h['name'])}, {lit(h['category'])}, {lit(h['level'])})" for h in hl) + ";")
    L2.append("insert into public.halaqah_subjects (halaqah_id, subject_id) values\n" + ",\n".join(
        f"({lit(h)}, {lit(uid('subject', s))})" for h, s in sorted(set(h_sub))) + ";")
    L2.append("insert into public.halaqah_teachers (halaqah_id, profile_id, subject_id, schedule_days, kbm_session, teacher_role)\n"
              "select v.hid::uuid, u.id, v.sid::uuid, v.days, v.kbm::smallint, v.trole::public.teacher_role\nfrom (values\n" + ",\n".join(
                  f"({lit(h)}, {lit(e)}, {lit(uid('subject', s) if s else None)}, {lit(d)}, {lit(k)}, {lit(t)})" for h, e, s, d, k, t in h_teach) +
              "\n) as v(hid, email, sid, days, kbm, trole) join auth.users u on u.email = v.email;")
    L2.append("insert into public.halaqah_members (halaqah_id, student_id) values\n" + ",\n".join(
        f"({lit(h)}, {lit(sid(n))})" for h, n in sorted(set(h_mem))) + ";")
    if targets:
        for chunk in batches(targets):
            L2.append("insert into public.targets (id, domain, subject_id, student_id, effective_month_id, amount, amount_period, status) values\n" + ",\n".join(
                f"({lit(t[0])}, 'alquran', {lit(uid('subject', t[1]))}, {lit(t[2])}, {lit(month_id[0])}, {lit(t[3])}, 'harian', 'disetujui')" for t in chunk) + ";")
    for chunk in batches(progress):
        L2.append("insert into public.progress_entries (id, student_id, halaqah_id, subject_id, month_id, item_id, putaran) values\n" + ",\n".join(
            f"({lit(p[0])}, {lit(p[1])}, {lit(p[2])}, {lit(uid('subject', p[3]))}, {lit(p[4])}, {lit(p[5])}, {p[6]})" for p in chunk) + ";")
    for chunk in batches(attendance):
        L2.append("insert into public.attendance (student_id, month_id, domain, izin, sakit, alpha, effective_days_override) values\n" + ",\n".join(
            f"({lit(a[0])}, {lit(a[1])}, {lit(a[2])}, {a[3]}, {a[4]}, {a[5]}, {lit(a[6])})" for a in chunk) + ";")
    L2.append("commit;")

    open(os.path.join(OUT_SQL, "01_curriculum.sql"), "w", encoding="utf-8").write("\n".join(L1) + "\n")
    open(os.path.join(OUT_SQL, "02_school_data.sql"), "w", encoding="utf-8").write("\n".join(L2) + "\n")
    with open(os.path.join(OUT_REP, "users.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["email", "full_name", "role", "password"])
        for u in users: w.writerow([u["email"], u["name"], u["role"], secrets.token_urlsafe(9)])
    infos.append(f"Kolom H (hadir) di sheet diabaikan sesuai keputusan Mudir; aplikasi menghitung Hadir dari Hari Efektif dikurangi izin, sakit, alpha. {h_ignored} sel H tidak sama dengan hasil hitungan.")
    infos.append(f"Subjects {len(subjects)}, buku {len(books)}, item {len(items)}, santri {len(students)}, halaqah {len(hl)}, "
                 f"anggota {len(set(h_mem))}, pengampu {len(h_teach)}, target {len(targets)}, capaian {len(progress)}, presensi {len(attendance)}.")
    for fl in flags: warnings.append(fl)
    finish(args, True)

def finish(args, ok):
    os.makedirs(OUT_REP, exist_ok=True)
    with open(os.path.join(OUT_REP, "seed-report.md"), "w", encoding="utf-8") as fh:
        fh.write("# Laporan seed\n\n")
        fh.write(f"Status: {'BERHASIL' if ok and not errors else 'GAGAL (lihat galat)'}\n\n")
        for title, lst in (("Galat (harus diperbaiki)", errors), ("Peringatan dan temuan data (untuk dicek Mudir)", warnings), ("Informasi", infos)):
            fh.write(f"## {title} ({len(lst)})\n\n")
            for x in lst: fh.write(f"- {x}\n")
            fh.write("\n")
    print(f"Status: {'BERHASIL' if ok and not errors else 'GAGAL'}; galat={len(errors)}, peringatan={len(warnings)}")
    for e in errors[:15]: print("  GALAT:", e)
    print("Laporan lengkap: scripts/seed/output/seed-report.md")
    sys.exit(0 if ok and not errors else 1)

if __name__ == "__main__":
    main()
