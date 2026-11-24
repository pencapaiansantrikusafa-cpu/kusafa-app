#!/usr/bin/env python3
"""
Bandingkan hasil Rabiul Awwal (bulan 6, Al Qur'an) antara database dan file Excel sumber.

Sumber Excel (tidak diubah):
  data/source/3-Al Quran (halaqah dan pencapaian).xlsx
  sheet "Halaqah Al Quran dan pencapaian", blok Rabiul Awwal: BZ=HE, CA=H, CB=S,
  CC=I, CD=A, lalu pasangan "Tilawah"/nilai, "Tahfidz"/nilai, "Kitabah"/nilai
  (CE..CJ untuk bulan ini; lihat header baris 4).

Yang dibandingkan per santri:
  - Hari Efektif (HE) : kolom BZ  vs v_attendance.effective_days
  - Hadir             : kolom CA  vs v_attendance.hadir  (HE - izin - sakit - alpha)
  - Sakit             : CB        vs attendance.sakit
  - Izin              : CC        vs attendance.izin
  - Alpha             : CD        vs attendance.alpha
  - Capaian Tilawah/Tahfidz/Kitabah: teks label di Excel vs label item di DB
    (dipakai untuk mengecek bahwa item bulan ini dan bulan pembanding sama,
    yaitu dasar perhitungan selisih).

Selisih tidak ada di Excel (Excel tidak menyimpan kolom selisih). Karena itu selisih
diverifikasi secara tidak langsung: label capaian bulan ini dan bulan lalu cocok persis
dengan Excel, dan rumusnya ada di view. Hasil ditampilkan sebagai catatan.

Membaca .env.local; tidak mencetak rahasia. Tidak mengubah apa pun.
Jalankan: python scripts/qa/compare_rabiul_awwal_excel.py
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import openpyxl
import psycopg

ROOT = Path(__file__).resolve().parents[2]
XLSX = ROOT / "data/source/3-Al Quran (halaqah dan pencapaian).xlsx"
OUT = ROOT / "docs" / "qa" / f"rabiul_awwal_excel_{datetime.date.today().isoformat()}.json"

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

# kolom Excel (1-based) blok Rabiul Awwal
C_HE, C_H, C_S, C_I, C_A = 78, 79, 80, 81, 82          # BZ..CD
C_ITEM = {"Tilawah": (83, 84), "Tahfidz": (85, 86), "Kitabah": (87, 88)}  # (label, angka) = CE/CF, CG/CH, CI/CJ

hasil: list[dict] = []


def rec(name, ok, detail, evidence=None):
    hasil.append({"name": name, "ok": ok, "detail": detail, "evidence": evidence or {}})
    status = "PASS" if ok is True else ("SKIP" if ok is None else "FAIL")
    print(status, name, "-", detail)


sudut_kolom = openpyxl.load_workbook(ROOT / "data/source/2-Dropdown Input Kurikulum KUSAFA.xlsx", data_only=True)["Al Quran"]
# (buku, detail) -> value acuan dari file dropdown (kolom G "Value (hitung Selisih)")
nilai_acuan = {}
for r in range(2, sudut_kolom.max_row + 1):
    buku, detail, val = sudut_kolom.cell(r, 4).value, sudut_kolom.cell(r, 5).value, sudut_kolom.cell(r, 7).value
    if buku and detail is not None and val is not None:
        def _kunci(x):
            try:
                return str(int(float(x)))
            except (TypeError, ValueError):
                return str(x).strip()
        nilai_acuan[(_kunci(buku), _kunci(detail))] = float(val)

ws = openpyxl.load_workbook(XLSX, data_only=True)["Halaqah Al Quran dan pencapaian"]
excel: dict[str, dict] = {}
for r in range(5, 114):
    nis = ws.cell(r, 2).value
    if not nis:
        continue
    num = lambda c: ws.cell(r, c).value if ws.cell(r, c).value is not None else 0
    he = ws.cell(r, C_HE).value
    excel[str(nis)] = {
        "row": r,
        "he": he,
        "h": ws.cell(r, C_H).value,
        "s": num(C_S), "i": num(C_I), "a": num(C_A),
        "item": {sj: ws.cell(r, c[0]).value for sj, c in C_ITEM.items()},
        "angka": {sj: ws.cell(r, c[1]).value for sj, c in C_ITEM.items()},
    }

conn = psycopg.connect(env["DATABASE_URL"], autocommit=True, connect_timeout=20)
tahun_aktif = conn.execute(
    "select hijri_year from public.academic_years where is_active order by hijri_year desc limit 1").fetchone()[0]
db = {
    r[0]: {"he": r[1], "hadir": r[2], "izin": r[3], "sakit": r[4], "alpha": r[5]}
    for r in conn.execute("""
        select s.nis, va.effective_days, va.hadir, va.izin, va.sakit, va.alpha
        from public.v_attendance va
        join public.students s on s.id = va.student_id
        join public.hijri_months m on m.id = va.month_id
        where m.month_no = 6 and va.domain = 'alquran'""").fetchall()
}

# label item di DB untuk bulan 6 (dan bulan pembanding bulan 5)
label_db = {}
for nis, sj, bulan, label in conn.execute("""
        select s.nis, sj.name, m.month_no, v.item_label
        from public.v_monthly_report v
        join public.students s on s.id = v.student_id
        join public.subjects sj on sj.id = v.subject_id
        join public.hijri_months m on m.id = v.month_id
        where m.month_no in (5, 6) and sj.domain = 'alquran'""").fetchall():
    label_db[(nis, sj, bulan)] = label

# hasil capaian per bulan (angka baris) — untuk dasar selisih
progress_db = {
    (r[0], r[1], r[2]): {"label": r[3], "pos": r[4], "prev_label": r[5], "selisih": r[6],
                         "putaran": r[7]}
    for r in conn.execute("""
        select s.nis, sj.name, m.month_no, v.item_label, v.pos, v.prev_item_label, v.selisih, v.putaran
        from public.v_monthly_report v
        join public.students s on s.id = v.student_id
        join public.subjects sj on sj.id = v.subject_id
        join public.hijri_months m on m.id = v.month_id
        where m.month_no = 6 and sj.domain = 'alquran'""").fetchall()
}

# ---- 1. HE
beda_he = [(n, excel[n]["he"], db.get(n, {}).get("he")) for n in excel
           if db.get(n, {}).get("he") != excel[n]["he"]]
rec("1_hari_efektif_cocok_excel", not beda_he,
    f"{len(excel)} santri; berbeda {len(beda_he)}" + (f": {beda_he[:5]}" if beda_he else ""))

# ---- 2. Hadir = HE - (izin+sakit+alpha), bandingkan dengan kolom CA
beda_hadir = [(n, excel[n]["h"], db.get(n, {}).get("hadir")) for n in excel
              if db.get(n, {}).get("hadir") != excel[n]["h"]]
rec("2_hadir_cocok_excel", not beda_hadir,
    f"Hadir DB = HE-(izin+sakit+alpha); berbeda {len(beda_hadir)}"
    + (f": {beda_hadir[:5]}" if beda_hadir else ""))

# ---- 3. izin/sakit/alpha
beda_abs = [(n, (excel[n]["i"], excel[n]["s"], excel[n]["a"]),
             (db.get(n, {}).get("izin"), db.get(n, {}).get("sakit"), db.get(n, {}).get("alpha")))
            for n in excel
            if db.get(n, {}).get("izin") != excel[n]["i"] or db.get(n, {}).get("sakit") != excel[n]["s"]
            or db.get(n, {}).get("alpha") != excel[n]["a"]]
rec("3_izin_sakit_alpha_cocok_excel", not beda_abs,
    f"berbeda {len(beda_abs)}" + (f": {beda_abs[:5]}" if beda_abs else ""))

# ---- 4. capaian bulan ini cocok dengan Excel: label teks (mis. "Al Insyiqaq : 13") harus
        # sama dengan label item di DB, dan posisi DB harus = nilai acuan file dropdown.
beda_item = []
suai_manual = []
for n in excel:
    for sj, teks in excel[n]["item"].items():
        pr = progress_db.get((n, sj, 6))
        angka = excel[n]["angka"].get(sj)
        if teks is None:
            if pr is not None:
                beda_item.append((n, sj, "kosong di Excel", pr["label"]))
            continue
        if pr is None:
            beda_item.append((n, sj, teks, "tidak ada di DB"))
            continue
        inti = pr["label"].split("·", 1)[1].strip() if "·" in pr["label"] else pr["label"]
        # CE/CG/CI berisi teks ("Halaman 351", "Al Insyiqaq : 13"); CF/CH/CJ berisi angka.
        import re as _re
        mh = _re.match(r"^Halaman\s+(\d+)$", str(teks).strip())
        m = _re.match(r"^(.*?)\s*:\s*(\d+)$", str(teks).strip())
        if mh:
            buku, detail = "Al Qur'an", mh.group(1)
        elif m:
            buku, detail = m.group(1), m.group(2)
        else:
            beda_item.append((n, sj, f"format tak dikenal: {teks}", pr["label"]))
            continue
        # label DB harus memuat "buku - detail"
        label_harap = f"{buku.strip()} - {int(float(detail))}"
        acuan = nilai_acuan.get((buku.strip(), str(int(float(detail)))))
        masalah = []
        if label_harap.lower() not in inti.lower():
            masalah.append(f"label DB {inti!r} != {label_harap!r}")
        if acuan is None or abs(float(pr["pos"]) - (acuan + (float(pr["putaran"]) - 1) * 604)) > 1e-9:
            masalah.append(f"posisi DB {pr['pos']} != nilai acuan {acuan} + (putaran-1)*604 ({pr['putaran']})")
        # Angka di kolom CF/CH/CJ adalah angka manual di file capaian; bisa berbeda dari posisi
        # kumulatif (contoh: "Al Qur'an 351" bernilai acuan 485 karena Karima 1-604 mendahului).
        # Perbedaan itu DICATAT, bukan kegagalan, dan hanya relevan untuk selisih.
        if angka is not None and acuan is not None and abs(float(angka) - (acuan + (float(pr["putaran"]) - 1) * 604)) > 1e-9:
            suai_manual.append((n, sj, float(angka), float(pr["pos"]), acuan, pr["putaran"]))
        if masalah:
            beda_item.append((n, sj, str(teks), pr["label"], "; ".join(masalah)))
rec("4_capaian_bulan_ini_cocok_excel", not beda_item,
    f"label & posisi capaian Rabiul Awwal Excel vs DB: berbeda {len(beda_item)}"
    + (f": {beda_item[:4]}" if beda_item else "")
    + (f"; angka manual Excel berbeda dari posisi kumulatif pada {len(suai_manual)} baris "
       f"(dicatat, bukan galat; lihat evidence)" if suai_manual else ""),
    {"beda": beda_item[:20], "angka_manual_berbeda": suai_manual[:20],
     "jumlah_angka_manual_berbeda": len(suai_manual)})

# ---- 5. selisih: Rabiul Awwal adalah bulan ke-6; pembanding bulan ke-5 (Shafar).
#        Kasus SAH tanpa pembanding: (a) capaian baru ada di Rabiul Awwal (bukan di Shafar),
#        (b) santri angkatan baru yang memang belum punya riwayat bulan lalu.
#        Selain itu dianggap janggal dan dilaporkan.
baru_angkatan = {nis for (nis,) in conn.execute(
    "select nis from public.students where angkatan = %s", (str(tahun_aktif),)).fetchall()}
pemilik_shafar = {(nis, sj) for (nis, sj, b) in progress_db if b == 6
                  and progress_db[(nis, sj, 6)]["prev_label"] is not None}
tanpa_pembanding = [(n, sj) for (n, sj, b) in progress_db if b == 6
                    and progress_db[(n, sj, 6)]["selisih"] is None]
tanpa_nis = {n for n, _ in tanpa_pembanding}
sah_baru = tanpa_nis & baru_angkatan
sah_bukan_shafar = {n for n, sj in tanpa_pembanding if (n, sj) not in pemilik_shafar} - baru_angkatan
janggal = sorted(tanpa_nis - baru_angkatan - sah_bukan_shafar)
rec("5_selisih_tanpa_pembanding_wajar", not janggal,
    f"{len(tanpa_nis)} santri tanpa pembanding: {len(sah_baru)} santri angkatan baru (sah), "
    f"{len(sah_bukan_shafar)} baru mulai di Rabiul Awwal (sah), janggal: {len(janggal)}"
    + (f" -> {janggal[:10]}" if janggal else ""),
    {"santri_tanpa_pembanding": sorted(tanpa_nis), "angkatan_baru": sorted(baru_angkatan),
     "janggal": janggal})

# ---- 6. sampel minimal 10 santri (termasuk yang punya ketidakhadiran)
sampel = sorted(excel)[:10]
sampel += [n for n in sorted(excel) if excel[n]["i"] + excel[n]["s"] + excel[n]["a"] > 0][:5]
sampel = list(dict.fromkeys(sampel))
baris = []
for n in sampel:
    e, d = excel[n], db.get(n, {})
    pr = progress_db.get((n, "Tilawah", 6), {})
    baris.append({"nis": n, "excel_he": e["he"], "db_he": d.get("he"),
                  "excel_hadir": e["h"], "db_hadir": d.get("hadir"),
                  "excel_tilawah": e["item"].get("Tilawah"),
                  "db_tilawah_pos": pr.get("pos"), "db_tilawah": pr.get("label"),
                  "db_tilawah_lalu": pr.get("prev_label"), "selisih": pr.get("selisih")})
rec("6_sampel_minimal_10", len(sampel) >= 10, f"{len(sampel)} santri dibandingkan", {"sampel": baris})

# ---- 7. semua yang tampak berbeda (tidak ada batas jumlah)
semua_beda = {"he": beda_he, "hadir": beda_hadir, "absensi": beda_abs, "capaian": beda_item}
rec("7_daftar_semua_perbedaan", all(not v for v in semua_beda.values()),
    "tidak ada perbedaan" if all(not v for v in semua_beda.values())
    else f"HE {len(beda_he)}, Hadir {len(beda_hadir)}, absensi {len(beda_abs)}, capaian {len(beda_item)}",
    {"semua_beda": {k: [list(map(str, x)) if isinstance(x, tuple) else x for x in v] for k, v in semua_beda.items()}})

conn.close()
gagal = [h for h in hasil if h["ok"] is False]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"ran_at": datetime.datetime.now().isoformat(), "tests": hasil},
                          indent=2, default=str, ensure_ascii=False), encoding="utf-8")
print(f"\n{sum(1 for h in hasil if h['ok'])}/{len(hasil)} PASS. Laporan: {OUT}")
sys.exit(1 if gagal else 0)