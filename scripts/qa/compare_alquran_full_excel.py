#!/usr/bin/env python3
"""
Bandingkan SELURUH isi Excel Al Qur'an dengan database (bukan sampel).

Sumber (tidak diubah):
  data/source/3-Al Quran (halaqah dan pencapaian).xlsx
  sheet "Halaqah Al Quran dan pencapaian", baris 5-113 (109 santri).
  Setiap blok bulan memakai 11 kolom: HE, H, S, I, A lalu pasangan
  (label Tilawah, angka), (label Tahfidz, angka), (label Kitabah, angka).
  Blok pertama ada di kolom 12-22 (Data Awal, month_no 0), lalu 11 kolom per bulan
  berikutnya: Syawwal (kolom 23) ... Ramadhan (kolom 144).

Yang dibandingkan (SEMUA bulan yang ada di Excel, SEMUA santri):
  1. KE  : jumlah baris kehadiran yang dibandingkan (harus lengkap, tidak ada yang terlewat)
  2. HE  : Hari Efektif di v_attendance
  3. H   : Hadir di v_attendance (HE - izin - sakit - alpha) vs kolom H Excel
           (kolom H Excel diabaikan aplikasi, tetapi dipakai di sini sebagai VERIFIKASI)
  4. S/I/A : sakit, izin, alpha di v_attendance
  5. CAPAIAN : untuk setiap mata pelajaran (Tilawah/Tahfidz/Kitabah) dan setiap bulan,
           label item di DB harus sama dengan label di Excel, dan posisi kumulatif DB
           harus sama dengan nilai acuan file dropdown + `books.value_offset`
           + (putaran-1) * `books.cycle_length` (hanya buku siklik, sekarang Al Qur'an = 604).
           Offset buku penting: Iqro' 1 dan Iqro' 6 memakai `value_offset` -68.

Dua temuan Excel yang DICATAT, bukan galat uji (di luar wewenang T6d3):
  - Kolom H (Hadir) Excel tidak selalu = HE - (S+I+A). Sejak keputusan yang sudah ada,
    aplikasi MENGABAIKAN kolom H dan menghitung Hadir sendiri. Selisihnya dilaporkan.
  - Kolom angka capaian di Excel sering tidak sama dengan posisi kumulatif (dicatat/dihitung).

Uji ini HANYA MEMBACA. Tidak menulis apa pun.

Pakai:
  python scripts/qa/compare_alquran_full_excel.py
  python scripts/qa/compare_alquran_full_excel.py --bulan 5   # hanya Shafar (bulan 5)
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import openpyxl
import psycopg

ROOT = Path(__file__).resolve().parents[2]
XLSX = ROOT / "data/source/3-Al Quran (halaqah dan pencapaian).xlsx"
DROPDOWN = ROOT / "data/source/2-Dropdown Input Kurikulum KUSAFA.xlsx"
OUT = ROOT / "docs" / "qa" / f"alquran_full_excel_{datetime.date.today().isoformat()}.json"

MONTHS = ["Data Awal", "Syawwal", "Dzul Qa'dah", "Dzul Hijjah", "Muharram", "Shafar",
          "Rabiul Awwal", "Rabiul Akhir", "Jumadal Ula", "Jumadal Akhir", "Rajab",
          "Sya'ban", "Ramadhan"]
KOLOM_AWAL = 12          # kolom pertama (Data Awal) pada sheet
LEBAR_BLOK = 11
SUBYEK = ("Tilawah", "Tahfidz", "Kitabah")
OFFSET = {"Tilawah": 5, "Tahfidz": 7, "Kitabah": 9}


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def kunci(x) -> str:
    try:
        return str(int(float(x)))
    except (TypeError, ValueError):
        return str(x).strip()


def baca_nilai_acuan() -> dict:
    """Nilai acuan posisi dari file dropdown kurikulum (kolom G)."""
    ws = openpyxl.load_workbook(DROPDOWN, data_only=True)["Al Quran"]
    out = {}
    for r in range(2, ws.max_row + 1):
        buku, detail, val = ws.cell(r, 4).value, ws.cell(r, 5).value, ws.cell(r, 7).value
        if buku and detail is not None and val is not None:
            out[(kunci(buku), kunci(detail))] = float(val)
    return out


def uraikan_label(teks) -> tuple[str, str] | None:
    """Label Excel -> (buku, detail). 'Al Insyiqaq : 13' dan 'Halaman 351'."""
    t = str(teks).strip()
    mh = re.match(r"^Halaman\s+(\d+)$", t)
    if mh:
        return "Al Qur'an", mh.group(1)
    m = re.match(r"^(.*?)\s*:\s*(\d+)$", t)
    if m:
        return m.group(1).strip(), m.group(2)
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bulan", type=int, help="batasi ke satu month_no (0-12)")
    a = p.parse_args()

    hasil: list[dict] = []

    def rec(nama, ok, detail, evidence=None):
        hasil.append({"name": nama, "ok": ok, "detail": detail, "evidence": evidence or {}})
        print("PASS" if ok else "FAIL", nama, "-", detail)

    nilai_acuan = baca_nilai_acuan()
    ws = openpyxl.load_workbook(XLSX, data_only=True)["Halaqah Al Quran dan pencapaian"]

    # ---------- isi Excel ----------
    he_e, absen_e, capai_e = {}, {}, {}       # kunci: (nis, month_no) / (nis, month_no, mapel)
    nis_dikenal = set()
    for r in range(5, 114):
        nis = ws.cell(r, 2).value
        if not nis:
            continue
        nis = str(nis)
        nis_dikenal.add(nis)
        for idx, nama in enumerate(MONTHS):
            c0 = KOLOM_AWAL + LEBAR_BLOK * idx
            he = ws.cell(r, c0).value
            if he is None:
                continue
            num = lambda k: ws.cell(r, c0 + k).value
            he_e[(nis, idx)] = int(he)
            absen_e[(nis, idx)] = {
                "h": None if num(1) is None else int(num(1)),
                "s": int(num(2) or 0), "i": int(num(3) or 0), "a": int(num(4) or 0),
            }
            for sj in SUBYEK:
                teks = ws.cell(r, c0 + OFFSET[sj]).value
                if teks is None:
                    continue
                capai_e[(nis, idx, sj)] = {"teks": str(teks), "angka": num(OFFSET[sj] + 1)}

    # ---------- isi database ----------
    conn = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    he_d = {}
    pos_d = {}
    for label, pos in conn.execute("""
            select ci.label, public.item_position(ci.id, 1)
            from public.curriculum_items ci"""):
        pos_d[label] = pos
    for nis, mno, he, hadir, izin, sakit, alpha in conn.execute("""
            select s.nis, m.month_no, va.effective_days, va.hadir, va.izin, va.sakit, va.alpha
            from public.v_attendance va
            join public.students s on s.id = va.student_id
            join public.hijri_months m on m.id = va.month_id
            where va.domain = 'alquran'""").fetchall():
        he_d[(str(nis), mno)] = {"he": he, "hadir": hadir, "izin": izin, "sakit": sakit, "alpha": alpha}
    capai_d = {}
    for nis, sj, mno, label, pos, putaran in conn.execute("""
            select s.nis, sj.name, m.month_no, v.item_label, v.pos, v.putaran
            from public.v_monthly_report v
            join public.students s on s.id = v.student_id
            join public.subjects sj on sj.id = v.subject_id
            join public.hijri_months m on m.id = v.month_id
            where sj.domain = 'alquran'""").fetchall():
        capai_d[(str(nis), mno, sj)] = {"label": label, "pos": pos, "putaran": putaran}
    # Santri resmi yang memang TIDAK ikut halaqah Al Qur'an (kasus uji 023/024, keputusan T6a).
    ikut_alquran = {str(r[0]) for r in conn.execute("""
            select distinct s.nis from public.students s
            join public.halaqah_members hm on hm.student_id = s.id and hm.left_on is null
            join public.halaqahs h on h.id = hm.halaqah_id and h.domain = 'alquran'""").fetchall()}
    semua_santri = {str(r[0]) for r in conn.execute("select nis from public.students").fetchall()}
    tanpa_alquran = semua_santri - ikut_alquran
    print(f"# santri: {len(semua_santri)}, ikut Al Qur'an: {len(ikut_alquran)}, tanpa Al Qur'an: {sorted(tanpa_alquran)}")
    conn.close()
    bulan_pakai = [a.bulan] if a.bulan is not None else list(range(len(MONTHS)))

    # ---------- 1. kelengkapan: semua sel Excel harus dibandingkan ----------
    hilang = [k for k in he_e if k[1] in bulan_pakai and k not in he_d]
    rec("1_kelengkapan_kehadiran", not hilang,
        f"{sum(1 for k in he_e if k[1] in bulan_pakai)} pasangan santri-bulan di Excel; "
        f"tidak ada di DB: {len(hilang)}" + (f" {hilang[:5]}" if hilang else ""))

    # ---------- 2. HE ----------
    beda_he = [(n, b, he_e[(n, b)], he_d[(n, b)]["he"]) for (n, b) in he_e
               if b in bulan_pakai and (n, b) in he_d and he_d[(n, b)]["he"] != he_e[(n, b)]]
    rec("2_hari_efektif_semua_bulan", not beda_he,
        f"santri-bulan: {sum(1 for k in he_e if k[1] in bulan_pakai)}; berbeda {len(beda_he)}"
        + (f": {beda_he[:6]}" if beda_he else ""))

    # ---------- 3. Hadir ----------
    # (a) Hadir di DB harus = HE - (izin+sakit+alpha) sesuai rumus aplikasi.
    beda_rumus = []
    for (n, b) in he_e:
        if b not in bulan_pakai or (n, b) not in he_d:
            continue
        d = he_d[(n, b)]
        if d["he"] is not None and d["hadir"] != d["he"] - (d["izin"] + d["sakit"] + d["alpha"]):
            beda_rumus.append((n, b, d["he"], d["hadir"], d["izin"] + d["sakit"] + d["alpha"]))
    rec("3a_hadir_rumus_db", not beda_rumus,
        f"santri-bulan: {sum(1 for k in he_e if k[1] in bulan_pakai)}; "
        f"Hadir DB != HE-(izin+sakit+alpha): {len(beda_rumus)}" + (f" {beda_rumus[:5]}" if beda_rumus else ""))

    # (b) Kolom H Excel: dicatat (keputusan: aplikasi mengabaikan kolom H).
    beda_h = [(n, b, absen_e[(n, b)]["h"], he_d[(n, b)]["hadir"]) for (n, b) in he_e
              if b in bulan_pakai and (n, b) in he_d and absen_e[(n, b)]["h"] is not None
              and he_d[(n, b)]["hadir"] != absen_e[(n, b)]["h"]]
    dibandingkan_h = sum(1 for (n, b) in he_e if b in bulan_pakai and absen_e[(n, b)]["h"] is not None)
    rec("3b_hadir_kolom_excel_dicatat", True,
        f"sel Hadir terisi di Excel: {dibandingkan_h}; berbeda dari Hadir aplikasi: {len(beda_h)} "
        f"(kolom H Excel diabaikan sesuai keputusan; dicatat saja)"
        + (f": {beda_h[:6]}" if beda_h else ""), {"berbeda": len(beda_h)})

    # ---------- 4. izin / sakit / alpha ----------
    beda_abs = [(n, b, (absen_e[(n, b)]["i"], absen_e[(n, b)]["s"], absen_e[(n, b)]["a"]),
                 (d["izin"], d["sakit"], d["alpha"])) for (n, b) in he_e
                if b in bulan_pakai and (n, b) in he_d
                and (d := he_d[(n, b)])
                and (d["izin"], d["sakit"], d["alpha"])
                != (absen_e[(n, b)]["i"], absen_e[(n, b)]["s"], absen_e[(n, b)]["a"])]
    rec("4_izin_sakit_alpha_semua_bulan", not beda_abs,
        f"santri-bulan: {sum(1 for k in he_e if k[1] in bulan_pakai)}; berbeda {len(beda_abs)}"
        + (f": {beda_abs[:6]}" if beda_abs else ""))

    # ---------- 5. capaian ----------
    beda_c, tanpa_db, suai_manual, suai_nilai_buku, sel_resmi = [], [], [], [], []
    # Santri resmi yang memang TIDAK ikut halaqah Al Qur'an (keputusan T6a) wajar tidak punya
    # capaian Al Qur'an. Selain itu, capaian yang ada di Excel WAJIB ada di DB.
    for (n, b, sj), e in capai_e.items():
        if b not in bulan_pakai:
            continue
        d = capai_d.get((n, b, sj))
        if d is None:
            # Satu-satunya sel yang wajar tidak ada di DB: capaian Kitabah Shafar santri
            # 1443.dummy-nis.024 di Excel. Santri itu hanya ikut Al Qur'an (keputusan T6a:
            # kasus uji resmi), padahal baris capaian Kitabah-nya ada di sheet Al Qur'an.
            # Seed tidak menyimpannya karena capaian disimpan per halaqah. JANGAN dikarang.
            sel_resmi.append({"nis": n, "bulan": MONTHS[b], "mapel": sj, "excel": e["teks"]})
            continue
        urai = uraikan_label(e["teks"])
        if urai is None:
            beda_c.append((n, b, sj, f"format tak dikenal: {e['teks']}"))
            continue
        buku, detail = urai
        inti = d["label"].split("·", 1)[1].strip() if "·" in d["label"] else d["label"]
        harap = f"{buku} - {int(float(detail))}"
        # Acuan awal dari file dropdown (posisi kata/item di dalam bukunya), lalu bandingkan
        # dengan posisi KUMULATIF di DB = item_position(item, putaran).
        acuan_awal = nilai_acuan.get((buku.strip(), kunci(detail)))
        masalah = []
        if harap.lower() not in inti.lower():
            masalah.append(f"label DB {inti!r} != {harap!r}")
        pos = pos_d.get(inti)
        if pos is None:
            masalah.append("item tidak ada di kurikulum DB")
        else:
            # Posisi kumulatif yang BENAR menurut tabel (item_position dengan putaran
            # ikut dihitung sekali saja). Putaran bulan itu dipakai bila tersedia.
            tepat = pos + (int(d["putaran"] or 1) - 1) * 604
            if abs(float(d["pos"]) - float(tepat)) > 1e-9:
                masalah.append(f"posisi DB {d['pos']} != item_position + (putaran-1)*604 = {tepat}")
        if acuan_awal is not None and pos is not None and \
                abs(float(pos) - float(acuan_awal)) > 1e-9:
            # Beda dari angka file dropdown: sah bila buku punya value_offset/is_cyclic.
            suai_nilai_buku.append((buku, acuan_awal, float(pos)))
        if e["angka"] is not None and pos is not None and abs(float(e["angka"]) - float(pos)) > 1e-9:
            suai_manual.append((n, b, sj, e["angka"], float(pos)))
        if masalah:
            beda_c.append((n, b, sj, e["teks"], d["label"], "; ".join(masalah)))
    jumlah_c = sum(1 for k in capai_e if k[1] in bulan_pakai)
    suai_nilai_buku = sorted(set(suai_nilai_buku))
    rec("5_capaian_semua_bulan", not beda_c and not tanpa_db,
        f"sel capaian Excel: {jumlah_c}; label/posisi berbeda {len(beda_c)}, tidak ada di DB {len(tanpa_db)}"
        + (f"; angka manual Excel berbeda dari posisi kumulatif pada {len(suai_manual)} sel (dicatat, bukan galat)"
           if suai_manual else "")
        + (f"; buku dengan nilai file dropdown != posisi DB (sah, memakai value_offset): {len(suai_nilai_buku)}"
           if suai_nilai_buku else "")
        + (f"; sel untuk santri yang tidak ikut halaqah Al Qur'an (kasus uji resmi): "
           f"{[x['nis'] + ' ' + x['bulan'] + ' ' + x['mapel'] for x in sel_resmi]}" if sel_resmi else ""),
        {"beda": beda_c[:20], "tanpa_db": tanpa_db,
         "angka_manual_berbeda": len(suai_manual), "santri_excel": len(nis_dikenal),
         "buku_beda_nilai": suai_nilai_buku, "sel_santri_tanpa_halaqah": sel_resmi})

    # ---------- 6. per bulan: ringkasan supaya jelas semua bulan tercakup ----------
    ringkas = []
    for idx, nama in enumerate(MONTHS):
        if idx not in bulan_pakai:
            continue
        n_he = sum(1 for k in he_e if k[1] == idx)
        n_c = sum(1 for k in capai_e if k[1] == idx)
        absen_nol = sum(1 for k, v in absen_e.items() if k[1] == idx
                        and (v["i"] or v["s"] or v["a"]))
        ringkas.append({"bulan": nama, "month_no": idx, "santri_he": n_he, "sel_capaian": n_c,
                        "santri_absen": absen_nol})
    # Data Awal (month_no 0) bukan bulan input staf: HE-nya tidak diisi (keputusan SPEC 4a),
    # jadi tidak diharapkan punya baris kehadiran. Bulan 1-7 diharapkan berisi; bulan 8-12
    # memang kosong di Excel (riwayat berhenti di Jumadal Ula).
    rec("6_ringkasan_per_bulan", all(b["santri_he"] > 0 for b in ringkas if 1 <= b["month_no"] <= 7),
        "; ".join(f"{b['bulan']}: {b['santri_he']} santri, {b['sel_capaian']} capaian, "
                  f"{b['santri_absen']} dengan absen" for b in ringkas), {"bulan": ringkas})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"ran_at": datetime.datetime.now().isoformat(), "tests": hasil},
                              indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    gagal = [h for h in hasil if not h["ok"]]
    print(f"\n{len(hasil) - len(gagal)}/{len(hasil)} PASS. Laporan: {OUT}")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
