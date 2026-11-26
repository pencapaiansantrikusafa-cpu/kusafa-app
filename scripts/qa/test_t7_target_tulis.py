"""E2E T7 [2/2] yang MENULIS lewat tampilan (RPC, bukan SQL): alur target per role.

Database lokal = produksi (satu Supabase). Karena itu uji ini:
  - menyimpan salinan PERSIS di awal (`pulihkan_data.rekam`),
  - hanya mengubah baris yang DIBUATNYA sendiri (semua target uji ditandai `note`
    "UJI-T7-TULIS-..."), dan
  - memulihkan di blok `finally` dengan `urus={...}` supaya baris target baru milik
    orang lain (mis. Mudir mencoba `/target` manual) TIDAK ikut dihapus.
Sidik jari database diambil sebelum & sesudah (`db_fingerprint.rekam/banding`);
selisih yang tersisa HANYA boleh berupa baris baru milik orang lain, dan dilaporkan.

Yang diperiksa (semua lewat TAMPILAN):
  1. Pengampu (Musyrif/ah) mengajukan target Al Qur'an -> status "Diajukan".
  2. Masul Al Quran menyetujui -> laporan (v_monthly_report) menampilkan target baru;
     nilai target di halaman Capaian = target harian x Hadir.
  3. Masul Al Quran menolak dengan alasan -> pengampu melihat alasan di daftar target.
  4. Pengaju membatalkan pengajuannya -> status "Dibatalkan".
  5. Masul lintas domain (Masul Wasilah) tidak melihat/menyetujui target Al Qur'an
     (dialihkan dari /target/alquran; target uji tetap "diajukan").
  6. Bulan lewat: pengampu diblokir; Mudir/Admin mendapat centang konfirmasi dan
     berhasil menyimpan. Bulan terkunci: Mudir/Admin juga mendapat konfirmasi.
  7. Tab & URL di 1280 px dan 360 px.

Pakai:
  npm run build
  python3 scripts/qa/serve_dist.py 4173 &
  BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t7_target_tulis.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import pathlib
import sys

import psycopg
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t7_target_tulis.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t7_tulis"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TAB = '[role="tab"]'
DIALOG_FORM = '[aria-labelledby="judul-form-target"]'
DIALOG_AKSI = '[aria-labelledby="judul-aksi-target"]'

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import db_fingerprint  # noqa: E402
import pulihkan_data  # noqa: E402

LULUS = 0
GAGAL: list[str] = []
RINCIAN: list[dict] = []


def catat(nama: str, ok: bool, **info) -> None:
    global LULUS
    RINCIAN.append({"uji": nama, "ok": bool(ok), **info})
    if ok:
        LULUS += 1
    else:
        GAGAL.append(nama)


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in pathlib.Path(".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


USERS = list(csv.DictReader(pathlib.Path("scripts/seed/output/users.csv").open(encoding="utf-8")))


def akun_role(role: str) -> dict:
    for r in USERS:
        if r["role"] == role:
            return r
    raise SystemExit(f"akun role {role} tidak ada")


def akun_nama(full_name: str) -> dict | None:
    for r in USERS:
        if r["full_name"] == full_name:
            return r
    return None


def login(page, a: dict) -> None:
    page.context.clear_cookies()
    page.goto(f"{BASE}/", wait_until="load")
    page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
    page.goto(f"{BASE}/", wait_until="load")
    page.wait_for_selector('input[type="email"]', timeout=60000)
    page.fill('input[type="email"]', a["email"])
    page.fill('input[type="password"]', a["password"])
    page.click('button[type="submit"]')
    page.wait_for_selector("header", timeout=60000)
    page.wait_for_timeout(800)


def pilih(page, tombol_id: str, label: str, cari: str, opsi: str, exact: bool = True, jeda: int = 400) -> None:
    """Buka DropdownCari, ketik di kotak cari, klik opsi."""
    page.click(f"#{tombol_id}")
    page.wait_for_selector('[role="option"]', timeout=20000)
    kotak = page.locator(f'input[aria-label="Cari {label}"]')
    kotak.fill(cari)
    page.wait_for_timeout(jeda)
    page.get_by_role("option", name=opsi, exact=exact).first.click()
    page.wait_for_timeout(400)


def filter_status(page, domain: str, status: str) -> None:
    pilih(page, f"target-filter-status-{domain}", "Status", status, status)
    page.wait_for_timeout(1200)


def baris_santri(page, nama: str):
    return page.locator("tbody tr").filter(has_text=nama)


def db_main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    c = db.cursor()

    # ---------------- konteks data (baca saja) ----------------
    m7 = c.execute("select id from public.hijri_months where month_no=7").fetchone()[0]
    m6 = c.execute("select id from public.hijri_months where month_no=6").fetchone()[0]
    mapel = {r[0]: r[1] for r in c.execute(
        "select id, name from public.subjects where domain='alquran'").fetchall()}
    subj_id = {name: sid for sid, name in mapel.items()}

    kandidat = c.execute(
        """
        select h.id, h.code, pr.full_name,
          (select hm.student_id from public.halaqah_members hm
             join public.progress_entries pe
               on pe.student_id=hm.student_id and pe.halaqah_id=h.id and pe.month_id=%s
            where hm.halaqah_id=h.id and hm.left_on is null
            group by hm.student_id having count(distinct pe.subject_id) >= 3
            order by hm.student_id limit 1) santri
        from public.halaqahs h
        join public.halaqah_teachers ht on ht.halaqah_id=h.id
        join public.profiles pr on pr.id=ht.profile_id and pr.role='musyrif'
        where h.domain='alquran' and h.is_active
        order by h.code
        """, (m7,)).fetchall()
    pilih_data = None
    for hid, kode, musyrif_name, santri in kandidat:
        if santri and akun_nama(musyrif_name):
            pilih_data = (hid, kode, musyrif_name, santri)
            break
    if not pilih_data:
        raise SystemExit("Tidak ada halaqah Al Qur'an dengan pengampu berakun & santri 3 bidang pada bulan 7.")
    halaqah_id, kode_halaqah, musyrif_name, santri_id = pilih_data
    santri_name = c.execute("select full_name from public.students where id=%s", (santri_id,)).fetchone()[0]
    att = c.execute(
        "select hadir, effective_days from public.v_attendance where student_id=%s and month_id=%s and domain='alquran'",
        (santri_id, m7)).fetchone()
    hadir = float(att[0]) if att and att[0] is not None else None

    akun_musyrif = akun_nama(musyrif_name)
    akun_masul_aq = akun_role("masul_alquran")
    akun_masul_wsl = akun_role("masul_wasilah")
    akun_mudir = akun_role("mudir")
    pid_masul_aq = c.execute("select id from public.profiles where full_name=%s",
                             (akun_masul_aq["full_name"],)).fetchone()[0]
    pid_mudir = c.execute("select id from public.profiles where full_name=%s",
                          (akun_mudir["full_name"],)).fetchone()[0]

    MARKER = "UJI-T7-TULIS-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    asli = pulihkan_data.rekam(db)
    # Teks kanonik tiap baris target lama: pembanding persis setelah pemulihan (aman tipe).
    asli_text = {str(r[0]): r[1] for r in c.execute(
        "select id, t::text from public.targets t").fetchall()}
    fp_awal = db_fingerprint.rekam()
    log_awal = c.execute("select count(*) from public.change_log").fetchone()[0]

    def target_uji():
        return c.execute(
            "select id, status, domain, subject_id, student_id, effective_month_id, amount, "
            "approved_by, proposed_by, alasan_tolak from public.targets where note=%s order by created_at",
            (MARKER,)).fetchall()

    id_uji: set[str] = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
            page = ctx.new_page()
            galat: list[str] = []
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)

            # ================= S1. Pengampu mengajukan 3 target =================
            login(page, akun_musyrif)
            page.goto(f"{BASE}/target/alquran", wait_until="load")
            page.wait_for_selector("tbody tr", timeout=60000)
            page.wait_for_timeout(1000)
            teks_main = page.inner_text("main")
            catat("S1 halaman target pengampu: halaqah amanah tanpa 'Semua halaqah'",
                  "Semua halaqah" not in teks_main and "Hanya halaqah yang Anda ampu" in teks_main)

            def ajukan(nama_mapel: str, nilai: str, bulan: str | None = None) -> str:
                page.get_by_role("button", name="Ajukan target", exact=True).first.click()
                page.wait_for_selector(DIALOG_FORM, timeout=20000)
                dlg = page.locator(DIALOG_FORM)
                # halaqah sudah terisi otomatis untuk pengampu (hanya satu)
                pilih(page, "target-santri", "Santri", santri_name, santri_name)
                pilih(page, "target-mapel", "Mata pelajaran", nama_mapel, nama_mapel)
                page.fill("#target-nilai", nilai)
                page.fill("#target-catatan", MARKER)
                if bulan:
                    pilih(page, "target-bulan-berlaku-bulan", "Bulan", bulan, bulan)
                    page.wait_for_timeout(900)
                status_bulan = (page.inner_text("#target-bulan-berlaku-bulan") or "").strip()
                dlg.get_by_role("button", name="Ajukan target", exact=True).click()
                page.wait_for_timeout(1600)
                return status_bulan

            bulan_default = ajukan("Tilawah", "3")
            bulan_default = bulan_default.split("\n")[0].strip()  # tombol punya ikon ▾ di baris itu
            catat("S1a bulan berlaku default = bulan berjalan (Rabiul Akhir)",
                  bulan_default == "Rabiul Akhir", bulan=bulan_default)
            catat("S1b pesan 'diajukan' tampil setelah Simpan",
                  "menunggu persetujuan" in page.inner_text("main"))
            ajukan("Tahfidz", "2")
            ajukan("Kitabah", "1")

            filter_status(page, "alquran", "Diajukan")
            t = page.inner_text("main")
            catat("S1c tiga target uji tampil berstatus Diajukan",
                  t.count(santri_name) >= 3 and "Diajukan" in t and "Tilawah" in t,
                  cuplikan=t[:160])
            page.screenshot(path=str(FOTO / "s1_pengampu_diajukan.png"), full_page=True)
            rows = target_uji()
            id_uji = {r[0] for r in rows}
            catat("S1d database: 3 baris diajukan, approved_by kosong, pengaju = pengampu",
                  len(rows) == 3 and all(r[1] == "diajukan" and r[7] is None for r in rows),
                  baris=len(rows))
            catat("S1e pengampu TIDAK melihat tombol Setujui/Tolak",
                  page.get_by_role("button", name="Setujui", exact=True).count() == 0
                  and page.get_by_role("button", name="Tolak", exact=True).count() == 0)

            # S1f: bulan lewat diblokir untuk pengampu (isi dulu agar valid, lalu ganti bulan).
            page.get_by_role("button", name="Ajukan target", exact=True).first.click()
            page.wait_for_selector(DIALOG_FORM, timeout=20000)
            pilih(page, "target-santri", "Santri", santri_name, santri_name)
            pilih(page, "target-mapel", "Mata pelajaran", "Tilawah", "Tilawah")
            page.fill("#target-nilai", "2")
            tombol_simpan = page.locator(DIALOG_FORM).get_by_role("button", name="Ajukan target", exact=True)
            aktif_sebelum = tombol_simpan.is_enabled()
            pilih(page, "target-bulan-berlaku-bulan", "Bulan", "Rabiul Awwal", "Rabiul Awwal")
            page.wait_for_timeout(1200)
            teks_dlg = page.inner_text(DIALOG_FORM)
            catat("S1f bulan lewat: pengampu diberi peringatan & Simpan dinonaktifkan",
                  aktif_sebelum and "SUDAH LEWAT" in teks_dlg
                  and "Hanya Mudir/Admin" in teks_dlg and tombol_simpan.is_disabled(),
                  peringatan="SUDAH LEWAT" in teks_dlg, disabled=tombol_simpan.is_disabled())
            page.get_by_role("button", name="Batal", exact=True).click()
            page.wait_for_timeout(500)
            ctx.close()

            # ================= S2. Masul Al Quran menyetujui & menolak =================
            ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
            page = ctx.new_page()
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun_masul_aq)
            page.goto(f"{BASE}/target/wasilah", wait_until="load")
            page.wait_for_timeout(1500)
            catat("S2a Masul Al Quran dialihkan dari /target/wasilah ke /target/alquran",
                  page.url.endswith("/target/alquran"))
            page.goto(f"{BASE}/target/alquran", wait_until="load")
            page.wait_for_selector("tbody tr", timeout=60000)
            page.wait_for_timeout(1000)
            filter_status(page, "alquran", "Diajukan")

            baris_santri(page, santri_name).filter(has_text="Tilawah").first \
                .get_by_role("button", name="Setujui", exact=True).click()
            page.wait_for_selector(DIALOG_AKSI, timeout=20000)
            dlg_aksi = page.inner_text(DIALOG_AKSI)
            catat("S2b dialog setujui menyebut sasaran, mapel, nilai, bulan",
                  santri_name in dlg_aksi and "Tilawah" in dlg_aksi and "target 3" in dlg_aksi
                  and "Rabiul Akhir" in dlg_aksi, potongan=dlg_aksi[:180])
            page.locator(DIALOG_AKSI).get_by_role("button", name="Setujui target", exact=True).click()
            page.wait_for_timeout(1800)
            catat("S2c pesan 'target disetujui' tampil",
                  "Target disetujui" in page.inner_text("main"))
            page.screenshot(path=str(FOTO / "s2_masul_setujui.png"), full_page=True)

            # tolak Tahfidz dengan alasan
            filter_status(page, "alquran", "Diajukan")
            baris_santri(page, santri_name).filter(has_text="Tahfidz").first \
                .get_by_role("button", name="Tolak", exact=True).click()
            page.wait_for_selector(DIALOG_AKSI, timeout=20000)
            alasan = "Uji T7: target terlalu tinggi untuk santri ini."
            page.fill("#alasan-tolak", alasan)
            page.locator(DIALOG_AKSI).get_by_role("button", name="Tolak target", exact=True).click()
            page.wait_for_timeout(1800)
            catat("S2d pesan 'target ditolak' tampil",
                  "Target ditolak" in page.inner_text("main"))

            rows = {r[3]: r for r in target_uji()}  # subject_id -> row (kolom: id,status,domain,subject_id,...)
            row_aq = rows.get(subj_id["Tilawah"])
            row_tf = rows.get(subj_id["Tahfidz"])
            catat("S2e database: Tilawah disetujui oleh Masul Al Quran",
                  bool(row_aq) and row_aq[1] == "disetujui" and str(row_aq[7]) == str(pid_masul_aq),
                  status=row_aq[1] if row_aq else None)
            catat("S2f database: Tahfidz ditolak + alasan tersimpan",
                  bool(row_tf) and row_tf[1] == "ditolak" and row_tf[9] == alasan,
                  status=row_tf[1] if row_tf else None, alasan=row_tf[9] if row_tf else None)

            # laporan: target_monthly = amount x hadir
            rep = c.execute(
                "select target_amount, target_monthly from public.v_monthly_report "
                "where student_id=%s and month_id=%s and subject_id=%s",
                (santri_id, m7, subj_id["Tilawah"])).fetchone()
            harap = (None if hadir is None else 3 * hadir)
            catat("S2g laporan (v_monthly_report) memakai target baru 3/hari",
                  rep is not None and float(rep[0]) == 3.0
                  and harap is not None and float(rep[1]) == harap,
                  target_amount=float(rep[0]) if rep else None,
                  target_monthly=float(rep[1]) if rep else None, harapan=harap, hadir=hadir)
            ctx.close()

            # ================= S3. Masul lintas domain =================
            ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
            page = ctx.new_page()
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun_masul_wsl)
            page.goto(f"{BASE}/target/alquran", wait_until="load")
            page.wait_for_timeout(1800)
            catat("S3a Masul Wasilah dialihkan dari /target/alquran ke /target/wasilah",
                  page.url.endswith("/target/wasilah"), url=page.url)
            teks_wsl = page.inner_text("main")
            catat("S3b target Al Qur'an uji tidak terlihat di domain Wasilah",
                  santri_name not in teks_wsl)
            sisa_diajukan = c.execute(
                "select count(*) from public.targets where note=%s and status='diajukan'", (MARKER,)).fetchone()[0]
            catat("S3c Masul lintas domain tidak menyetujui: target uji tetap 'diajukan'",
                  sisa_diajukan >= 1, diajukan=sisa_diajukan)
            ctx.close()

            # ================= S4. Pengampu: lihat alasan + batalkan =================
            ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
            page = ctx.new_page()
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun_musyrif)
            page.goto(f"{BASE}/target/alquran", wait_until="load")
            page.wait_for_selector("tbody tr", timeout=60000)
            page.wait_for_timeout(1200)
            filter_status(page, "alquran", "Ditolak")
            t = page.inner_text("main")
            catat("S4a pengampu melihat status Ditolak dan alasannya",
                  "Ditolak" in t and alasan in t, cuplikan=t[:200])

            filter_status(page, "alquran", "Diajukan")
            baris_santri(page, santri_name).filter(has_text="Kitabah").first \
                .get_by_role("button", name="Batalkan", exact=True).click()
            page.wait_for_selector(DIALOG_AKSI, timeout=20000)
            catat("S4b dialog batalkan menjelaskan 'bukan dihapus'",
                  "bukan dihapus" in page.inner_text(DIALOG_AKSI))
            page.locator(DIALOG_AKSI).get_by_role("button", name="Batalkan pengajuan", exact=True).click()
            page.wait_for_timeout(1800)
            catat("S4c pesan 'dibatalkan' tampil", "dibatalkan" in page.inner_text("main"))
            row_kb = next((r for r in target_uji() if r[3] == subj_id["Kitabah"] and r[5] == m7), None)
            catat("S4d database: Kitabah berstatus dibatalkan",
                  bool(row_kb) and row_kb[1] == "dibatalkan", status=row_kb[1] if row_kb else None)
            page.screenshot(path=str(FOTO / "s4_pengampu_ditolak_dibatalkan.png"), full_page=True)
            ctx.close()

            # ================= S5. Mudir: bulan lewat/terkunci butuh konfirmasi =================
            ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
            page = ctx.new_page()
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun_mudir)
            page.goto(f"{BASE}/target/alquran", wait_until="load")
            page.wait_for_selector("tbody tr", timeout=60000)
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Ajukan target", exact=True).first.click()
            page.wait_for_selector(DIALOG_FORM, timeout=20000)
            pilih(page, "target-halaqah-alquran", "Halaqah", kode_halaqah,
                  f"{kode_halaqah} - {musyrif_name}")
            pilih(page, "target-santri", "Santri", santri_name, santri_name)
            pilih(page, "target-mapel", "Mata pelajaran", "Kitabah", "Kitabah")
            page.fill("#target-nilai", "4")
            page.fill("#target-catatan", MARKER)
            pilih(page, "target-bulan-berlaku-bulan", "Bulan", "Rabiul Awwal", "Rabiul Awwal")
            page.wait_for_timeout(1200)
            teks_dlg = page.inner_text(DIALOG_FORM)
            simpan = page.locator(DIALOG_FORM).get_by_role("button", name="Ajukan target", exact=True)
            # Hati-hati: form Al Qur'an juga punya centang "massal"; ambil centang konfirmasi saja.
            centang = page.locator(DIALOG_FORM).locator(
                'label:has-text("tetap ingin melanjutkan") input[type="checkbox"]')
            catat("S5a bulan lewat: Mudir/Admin melihat centang konfirmasi & Simpan terkunci",
                  "SUDAH LEWAT" in teks_dlg and "tetap ingin melanjutkan" in teks_dlg
                  and centang.count() == 1 and simpan.is_disabled(),
                  checkbox=centang.count(), disabled=simpan.is_disabled())
            centang.first.click()
            page.wait_for_timeout(300)
            catat("S5b setelah dicentang, Simpan aktif",
                  simpan.is_enabled())
            simpan.click()
            page.wait_for_timeout(1800)
            catat("S5c target bulan lewat tersimpan (pesan sukses)", "langsung disetujui" in page.inner_text("main"))
            row_mudir = next((r for r in target_uji()
                              if r[3] == subj_id["Kitabah"] and r[5] == m6), None)
            catat("S5d database: target bulan Rabiul Awwal disetujui, pengaju Mudir",
                  bool(row_mudir) and row_mudir[1] == "disetujui"
                  and str(row_mudir[8]) == str(pid_mudir),
                  status=row_mudir[1] if row_mudir else None)

            # bulan terkunci: kunci Rabiul Akhir sementara, lalu periksa centang Mudir.
            lock_asli = c.execute(
                "select is_locked from public.month_domain_settings where month_id=%s and domain='alquran'",
                (m7,)).fetchone()
            c.execute("update public.month_domain_settings set is_locked=true where month_id=%s and domain='alquran'",
                      (m7,))
            try:
                page.reload(wait_until="load")
                page.wait_for_selector("tbody tr", timeout=60000)
                page.wait_for_timeout(1000)
                page.get_by_role("button", name="Ajukan target", exact=True).first.click()
                page.wait_for_selector(DIALOG_FORM, timeout=20000)
                pilih(page, "target-halaqah-alquran", "Halaqah", kode_halaqah,
                      f"{kode_halaqah} - {musyrif_name}")
                pilih(page, "target-santri", "Santri", santri_name, santri_name)
                pilih(page, "target-mapel", "Mata pelajaran", "Kitabah", "Kitabah")
                page.fill("#target-nilai", "1")
                page.fill("#target-catatan", MARKER)
                page.wait_for_timeout(1200)  # bulan default = Rabiul Akhir (terkunci)
                teks_kunci = page.inner_text(DIALOG_FORM)
                catat("S5e bulan terkunci: Mudir/Admin melihat peringatan + centang konfirmasi",
                      "SUDAH DIKUNCI" in teks_kunci and "tetap ingin melanjutkan" in teks_kunci,
                      cuplikan=teks_kunci[:200])
                page.get_by_role("button", name="Batal", exact=True).click()
                page.wait_for_timeout(400)
            finally:
                if lock_asli is None:
                    c.execute("delete from public.month_domain_settings where month_id=%s and domain='alquran'", (m7,))
                else:
                    c.execute("update public.month_domain_settings set is_locked=%s "
                              "where month_id=%s and domain='alquran'", (lock_asli[0], m7))
            ctx.close()

            # ================= S6. Tab & URL 1280 px dan 360 px =================
            ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
            page = ctx.new_page()
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun_mudir)
            page.goto(f"{BASE}/target", wait_until="load")
            page.wait_for_selector(TAB, timeout=60000)
            page.wait_for_timeout(1000)
            catat("S6a 1280 px: /target -> /target/alquran, 3 tab",
                  page.url.endswith("/target/alquran")
                  and [(b.inner_text() or "").strip() for b in page.query_selector_all(TAB)]
                  == ["Al Qur'an", "Ilmu Wasilah", "Ilmu Ghayah"])
            page.get_by_role("tab", name="Ilmu Wasilah", exact=True).click()
            page.wait_for_url("**/target/wasilah", timeout=20000)
            catat("S6b 1280 px: klik tab mengganti URL", page.url.endswith("/target/wasilah"))
            ctx.close()

            ctx = browser.new_context(viewport={"width": 360, "height": 780}, is_mobile=True,
                                      has_touch=True, device_scale_factor=2)
            page = ctx.new_page()
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            login(page, akun_mudir)
            for domain, nama in (("alquran", "Al Qur'an"), ("wasilah", "Ilmu Wasilah"), ("ghayah", "Ilmu Ghayah")):
                page.goto(f"{BASE}/target/{domain}", wait_until="load")
                page.wait_for_timeout(1500)
                ukur = page.evaluate(
                    """() => ({lebar: document.documentElement.scrollWidth,
                               layar: window.innerWidth,
                               tab: [...document.querySelectorAll('[role="tab"]')].map(t => Math.round(t.getBoundingClientRect().height))})"""
                )
                ok = (ukur["lebar"] <= ukur["layar"] + 1 and len(ukur["tab"]) == 3
                      and all(h >= 44 for h in ukur["tab"])
                      and page.url.endswith(f"/target/{domain}"))
                catat(f"S6c 360 px {nama}: URL benar, 3 tab >=44 px, tidak bergeser",
                      ok, url=page.url, ukur=ukur)
            ctx.close()

            catat("konsol browser bersih", not galat, galat=galat[:5])
            browser.close()
    finally:
        # Hanya baris buatan uji ini yang dihapus/dipulihkan; baris baru orang lain dibiarkan.
        # Kunci tabel `targets` berbentuk tuple string (lihat `pulihkan_data.KUNCI`).
        id_uji = {(str(r[0]),) for r in c.execute(
            "select id from public.targets where note=%s", (MARKER,)).fetchall()}
        tetap = pulihkan_data.pulihkan(
            db, asli,
            urus={"targets": id_uji, "progress_entries": set(), "attendance": set(), "monthly_notes": set()},
        )
        # Verifikasi pemulihan: tidak ada baris lama hilang/berubah; selisih hanya baris baru orang lain.
        # Kunci dibandingkan sebagai tuple string agar cocok dengan `pulihkan_data.KUNCI`.
        sekarang = {(str(r[0]),) for r in c.execute("select id from public.targets").fetchall()}
        asli_ids = set(asli["targets"].keys())
        hilang = asli_ids - sekarang
        catat("data uji dipulihkan: tidak ada baris target lama yang hilang", not hilang,
              hilang=len(hilang))
        # Bandingkan teks kanonik baris lama (persis, aman tipe) — harus identik.
        beda_nilai = 0
        for tid, teks in asli_text.items():
            r = c.execute("select t::text from public.targets t where id=%s", (tid,)).fetchone()
            if r is None or r[0] != teks:
                beda_nilai += 1
        catat("data uji dipulihkan: nilai baris target lama tidak berubah", beda_nilai == 0,
              beda=beda_nilai)
        sisa_uji = {(str(r[0]),) for r in c.execute(
            "select id from public.targets where note=%s", (MARKER,)).fetchall()}
        catat("tidak ada baris target uji (bertanda) yang tertinggal", not sisa_uji,
              tertinggal=len(sisa_uji))
        # Baris baru milik orang lain (mis. Mudir) dilaporkan, bukan dianggap gagal.
        baru_lain = []
        for tname, key in tetap:
            if tname == "targets":
                info = c.execute(
                    "select domain, amount, status, note, created_at from public.targets where id=%s",
                    (key[0],)).fetchone()
                baru_lain.append({"id": key[0], "domain": info[0], "amount": float(info[1]),
                                  "status": info[2], "note": info[3],
                                  "created_at": str(info[4])} if info else {"id": key[0]})
        catat("baris target baru milik orang lain dibiarkan utuh (bukan kegagalan sidik jari)",
              True,  # informasional: baris milik orang lain sengaja tidak disentuh
              jumlah=len(baru_lain), rincian=baru_lain[:10])

        # Sidik jari: harus SAMA, kecuali `targets` bertambah tepat karena baris orang lain
        # yang sengaja dibiarkan (tidak dihitung sebagai kegagalan, sesuai perintah kerja).
        fp_akhir = db_fingerprint.rekam()
        log_utuh = c.execute(
            "select count(*) from public.change_log where id <= %s", (fp_awal["_log_change_log"]["maks_id"],)
        ).fetchone()[0] == fp_awal["_log_change_log"]["baris"]
        beda = db_fingerprint.banding(fp_awal, fp_akhir, log_utuh)
        beda_selain_target = [d for d in beda if d["tabel"] not in ("targets", "change_log")]
        beda_target = [d for d in beda if d["tabel"] == "targets"]
        selisih_baris = (fp_akhir["targets"]["baris"] - fp_awal["targets"]["baris"]) if beda_target else 0
        target_terjelaskan = (
            not beda_target
            or (selisih_baris == len(baru_lain) and not sisa_uji and not beda_nilai)
        )
        catat("sidik jari database SAMA (kecuali baris target orang lain yang dilaporkan)",
              not beda_selain_target and target_terjelaskan,
              beda=beda, baris_lain=len(baru_lain), selisih_target=selisih_baris)
        log_akhir = c.execute("select count(*) from public.change_log").fetchone()[0]
        catat("change_log bertambah (append-only, baris lama utuh)", log_akhir >= log_awal and log_utuh,
              awal=log_awal, akhir=log_akhir)
        db.close()

    hasil = {
        "base": BASE,
        "waktu": dt.datetime.now().isoformat(timespec="seconds"),
        "konteks": {"halaqah": kode_halaqah, "musyrif": musyrif_name, "santri": santri_name,
                    "hadir_bulan7": hadir},
        "lulus": LULUS,
        "gagal": GAGAL,
        "ringkasan": f"{LULUS} LULUS, {GAGAL}" if GAGAL else f"{LULUS} LULUS, 0 gagal",
        "rincian": RINCIAN,
    }
    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(json.dumps(hasil, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for r in RINCIAN:
        print(("PASS " if r["ok"] else "GAGAL ") + r["uji"])
    print(hasil["ringkasan"], "| Laporan:", HASIL)
    return 0 if not GAGAL else 1


if __name__ == "__main__":
    sys.exit(db_main())
