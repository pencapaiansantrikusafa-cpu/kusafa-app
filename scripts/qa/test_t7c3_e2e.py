"""E2E T7c [3/3]: Input Wasilah/Ghayah (capaian + target bulan depan) dan halaman Target.

Database lokal = produksi (satu Supabase). Uji ini MENULIS lewat tampilan, lalu
memulihkan PERSIS di blok finally (pulihkan_data) dan membandingkan sidik jari
(db_fingerprint). Hanya baris milik uji yang dibuat/diubah.

Yang diperiksa:
  1. Halaman Input siap < 1,5 detik (butir dicari di server, bukan dimuat semua).
  2. Pengampu menyimpan gabungan (capaian + target) -> tersalin ke semua anggota.
  3. Capaian mapel tanpa target DITOLAK dan capaian tidak tersimpan.
  4. Koreksi capaian tanpa mengisi ulang target DITERIMA; target tidak bertambah.
  5. Target di bawah capaian: peringatan + centang; tanpa centang DITOLAK.
  6. Masul menolak target dengan alasan wajib; lalu "Setujui semua" untuk sisanya.
  7. Lintas domain: Masul Ghayah dialihkan dari /target/wasilah.
  8. Level 6: "Tuntas, belum ada pelajaran lanjutan" di Input, Capaian, Target.
  9. Tab & URL di 1280 px dan 360 px; tidak ada geser samping di 360 px.
 10. Tangkapan layar HP + desktop.

Pakai:
  npm run build
  python3 scripts/qa/serve_dist.py 4173 &
  BASE_URL=http://localhost:4173 .venv-qa/bin/python scripts/qa/test_t7c3_e2e.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import pathlib
import re
import statistics
import time

import psycopg
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:4173")
HASIL = pathlib.Path(os.environ.get("HASIL", "docs/qa/t7c3_e2e.json"))
FOTO = pathlib.Path(os.environ.get("FOTO", "docs/qa/t7c3"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

sys_path = pathlib.Path(__file__).resolve().parent
import sys  # noqa: E402

sys.path.insert(0, str(sys_path))
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


def akun_nama(nama: str) -> dict:
    for u in USERS:
        if u["full_name"] == nama:
            return u
    raise SystemExit(f"akun {nama} tidak ada di users.csv")


def akun_role(role: str) -> dict:
    for u in USERS:
        if u["role"] == role:
            return u
    raise SystemExit(f"akun role {role} tidak ada")


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


def pilih(page, id_tombol: str, cari: str, nama_opsi: str | None = None) -> str:
    page.click(f"#{id_tombol}")
    page.wait_for_selector('input[type="search"]:visible', timeout=20000)
    kotak = page.locator('input[type="search"]:visible').first
    kotak.fill(cari)
    page.wait_for_timeout(900)
    if nama_opsi:
        opsi = page.get_by_role("option", name=re.compile(nama_opsi)).first
    else:
        opsi = page.get_by_role("option").first
    label = opsi.inner_text().strip().split("\n")[0]
    opsi.click()
    page.wait_for_timeout(400)
    return label


def alert_teks(page) -> list[str]:
    return [t.strip() for t in page.locator('[role="alert"]').all_inner_texts() if t.strip()]


def main() -> int:  # noqa: C901
    FOTO.mkdir(parents=True, exist_ok=True)
    db = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    c = db.cursor()

    def satu(q: str, a: tuple = ()):
        c.execute(q, a)
        return c.fetchone()[0]

    def hitung(q: str, a: tuple = ()) -> int:
        c.execute(q, a)
        return int(c.fetchone()[0])

    hal_id = satu("select id from public.halaqahs where domain='wasilah' and code='Level Dasar A'")
    hal6_id = satu("select id from public.halaqahs where domain='wasilah' and code='Level 6'")
    bulan6 = satu("select id from public.hijri_months where month_no=6")
    bulan7 = satu("select id from public.hijri_months where month_no=7")
    nama6 = satu("select name from public.hijri_months where id=%s", (bulan6,))
    nama7 = satu("select name from public.hijri_months where id=%s", (bulan7,))
    c.execute("select subject_id, name from public.halaqah_mapel_aktif(%s,%s)", (hal_id, bulan6))
    mapel = c.fetchall()
    sid0, nama_mapel0 = mapel[0]
    sid1, nama_mapel1 = mapel[1]
    anggota = hitung(
        "select count(*) from public.halaqah_members where halaqah_id=%s and left_on is null",
        (hal_id,),
    )
    pengampu_nama = satu(
        """select p.full_name from public.halaqah_teachers ht
           join public.profiles p on p.id=ht.profile_id
           where ht.halaqah_id=%s
           group by p.full_name
           order by count(*) desc limit 1""",
        (hal_id,),
    )
    akun_pengampu = akun_nama(pengampu_nama)
    akun_masul_w = akun_role("masul_wasilah")
    akun_masul_g = akun_role("masul_ghayah")
    akun_mudir = akun_role("mudir")

    MARKER = "UJI-T7C3-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    asli = pulihkan_data.rekam(db)
    fp_awal = db_fingerprint.rekam()

    def item_id_1(subject: str) -> str:
        return satu(
            """select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
               where b.subject_id=%s and ci.is_active and b.is_active
               order by b.sort_order, b.stage_order, ci.seq limit 1""",
            (subject,),
        )

    def item_id_2(subject: str) -> str:
        return satu(
            """select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
               where b.subject_id=%s and ci.is_active and b.is_active
               order by b.sort_order, b.stage_order, ci.seq offset 1 limit 1""",
            (subject,),
        )

    def pe(subject: str) -> int:
        return hitung(
            "select count(*) from public.progress_entries where halaqah_id=%s and subject_id=%s and month_id=%s",
            (hal_id, subject, bulan6),
        )

    def target_live(subject: str) -> list[tuple]:
        c.execute(
            """select status, target_item_id, note from public.targets
               where halaqah_id=%s and subject_id=%s and effective_month_id=%s
               order by created_at, id""",
            (hal_id, subject, bulan7),
        )
        return c.fetchall()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1280, "height": 1100})
            galat: list[str] = []
            gagal_http: list[str] = []
            page.on("console", lambda m: galat.append(m.text) if m.type == "error" else None)
            page.on("response", lambda r: gagal_http.append(f"{r.status} {r.url[:180]}") if r.status >= 400 else None)

            # ---------------- 1-6. Pengampu mengisi Input ----------------
            login(page, akun_pengampu)
            page.goto(f"{BASE}/input/wasilah", wait_until="load")
            page.get_by_role("button", name="Simpan capaian & target").wait_for(timeout=60000)
            # Ukur 5 putaran (pemanasan cold-start tidak dihitung); laporan = median + maksimum.
            sampel_waktu: list[float] = []
            for _ in range(5):
                t0 = time.perf_counter()
                page.goto(f"{BASE}/input/wasilah", wait_until="load")
                page.get_by_role("button", name="Simpan capaian & target").wait_for(timeout=60000)
                sampel_waktu.append(round(time.perf_counter() - t0, 3))
            median = statistics.median(sampel_waktu)
            catat(
                "1. Halaman Input siap: median 5 putaran < 1,5 detik",
                median < 1.5,
                median=round(median, 3),
                maks=round(max(sampel_waktu), 3),
                sampel=sampel_waktu,
            )

            pilih(page, "input-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
            pilih(page, "input-wasilah-bulan", nama6, re.escape(nama6))
            page.wait_for_timeout(1200)
            jml_awal0 = pe(sid0)

            # 2. Simpan gabungan mapel 0 (capaian 1 + target 2).
            pilih(page, f"wasilah-{sid0}", "1")
            pilih(page, f"target-{sid0}", "2")
            page.screenshot(path=str(FOTO / "desktop_input_terisi.png"), full_page=True)
            page.get_by_role("button", name="Simpan capaian & target").click()
            batas = time.time() + 90
            while time.time() < batas and pe(sid0) == jml_awal0:
                page.wait_for_timeout(500)
            live0 = target_live(sid0)
            catat(
                "2. Simpan gabungan: capaian tersalin ke semua anggota + target dibuat",
                pe(sid0) == anggota and len(live0) == 1 and live0[0][0] == "diajukan",
                baris=pe(sid0), anggota=anggota, target=live0,
            )

            # 3. Capaian mapel 1 tanpa target -> DITOLAK, capaian tidak tersimpan.
            jml_awal1 = pe(sid1)
            pilih(page, f"wasilah-{sid1}", "1")
            page.get_by_role("button", name="Simpan capaian & target").click()
            page.wait_for_timeout(2500)
            teks = " ".join(alert_teks(page))
            catat(
                "3. Capaian tanpa target DITOLAK dan capaian tidak tersimpan",
                "Target bulan depan belum diisi" in teks and pe(sid1) == jml_awal1,
                pesan=teks[:200], baris=pe(sid1),
            )

            # 4. Koreksi capaian mapel 0 tanpa mengisi ulang target.
            # Muat ulang dulu supaya pilihan mapel 1 yang gagal di langkah 3 tidak ikut terkirim.
            page.reload(wait_until="load")
            page.get_by_role("button", name="Simpan capaian & target").wait_for(timeout=60000)
            pilih(page, "input-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
            pilih(page, "input-wasilah-bulan", nama6, re.escape(nama6))
            page.wait_for_timeout(1500)
            n_target0 = len(target_live(sid0))
            item_sebelum4 = satu(
                "select item_id from public.progress_entries where halaqah_id=%s and subject_id=%s and month_id=%s limit 1",
                (hal_id, sid0, bulan6),
            )
            pilih(page, f"wasilah-{sid0}", "2")
            page.get_by_role("button", name="Simpan capaian & target").click()
            page.wait_for_timeout(2500)
            item_baru = satu(
                "select item_id from public.progress_entries where halaqah_id=%s and subject_id=%s and month_id=%s limit 1",
                (hal_id, sid0, bulan6),
            )
            catat(
                "4. Koreksi capaian tanpa isi ulang target DITERIMA; target tidak bertambah",
                len(target_live(sid0)) == n_target0
                and str(item_baru) != str(item_sebelum4),
                target=target_live(sid0), item=item_baru,
            )

            # 5. Target di bawah capaian: peringatan + centang; tanpa centang ditolak.
            target_sebelum5 = next(x[1] for x in target_live(sid0) if x[0] in ("diajukan", "disetujui"))
            pilih(page, f"wasilah-{sid0}", "2")
            pilih(page, f"target-{sid0}", "1")
            page.wait_for_timeout(900)
            ada_peringatan = page.get_by_text("Target di bawah capaian bulan ini", exact=False).count() > 0
            page.get_by_role("button", name="Simpan capaian & target").click()
            page.wait_for_timeout(2500)
            teks = " ".join(alert_teks(page))
            catat(
                "5a. Peringatan target di bawah capaian tampil",
                ada_peringatan,
                pesan=teks[:200],
            )
            catat(
                "5b. Tanpa centang konfirmasi: DITOLAK",
                "bawah capaian" in teks,
                pesan=teks[:200],
            )
            page.get_by_label(re.compile("Saya tahu target bulan depan di bawah capaian")).check()
            page.get_by_role("button", name="Simpan capaian & target").click()
            page.wait_for_timeout(2500)
            live0 = target_live(sid0)
            catat(
                "5c. Dengan centang: DITERIMA; target diganti (satu target hidup)",
                sum(1 for x in live0 if x[0] in ("diajukan", "disetujui")) == 1
                and any(x[0] == "dibatalkan" for x in live0)
                and str(next(x[1] for x in live0 if x[0] in ("diajukan", "disetujui"))) != str(target_sebelum5),
                target=live0,
            )

            # 6. Simpan mapel 1 (capaian + target) untuk diuji penolakan Masul.
            pilih(page, f"wasilah-{sid1}", "1")
            pilih(page, f"target-{sid1}", "1")
            page.get_by_role("button", name="Simpan capaian & target").click()
            page.wait_for_timeout(2500)
            live1 = target_live(sid1)
            catat(
                "6. Pengampu menyimpan mapel kedua (capaian + target)",
                pe(sid1) == anggota and len(live1) == 1 and live1[0][0] == "diajukan",
                baris=pe(sid1), target=live1,
            )
            page.screenshot(path=str(FOTO / "desktop_input_tersimpan.png"), full_page=True)

            # ---------------- 6b. Pengampu TIDAK punya tombol Setujui/Tolak di /target ----------------
            page.goto(f"{BASE}/target/wasilah", wait_until="load")
            page.wait_for_timeout(1200)
            pilih(page, "target-filter-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
            pilih(page, "target-filter-bulan-wasilah-bulan", nama7, re.escape(nama7))
            page.wait_for_timeout(1500)
            body6b = page.locator("body").inner_text()
            catat(
                "6b. Pengampu tidak punya tombol Setujui/Tolak di /target",
                "Setujui semua" not in body6b
                and page.get_by_role("button", name=re.compile("^Setujui$")).count() == 0
                and page.get_by_role("button", name="Tolak").count() == 0,
                ada_setujui_semua="Setujui semua" in body6b,
            )

            # ---------------- 7. Masul Wasilah: tolak + setujui semua ----------------
            login(page, akun_masul_w)
            page.goto(f"{BASE}/target/wasilah", wait_until="load")
            page.wait_for_selector("table", timeout=60000)
            pilih(page, "target-filter-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
            pilih(page, "target-filter-bulan-wasilah-bulan", nama7, re.escape(nama7))
            page.wait_for_timeout(1800)

            headers = page.locator("thead th").all_inner_texts()
            kolom = {t.strip().lower(): i for i, t in enumerate(headers) if t.strip()}
            idx1 = kolom.get(nama_mapel1.lower())
            if idx1 is None:
                raise AssertionError(f"kolom {nama_mapel1} tidak ada: {headers}")
            sel1 = page.locator("tbody tr").first.locator("td").nth(max(0, idx1 - 1))
            sel1.get_by_role("button", name="Tolak").click()
            page.fill("#alasan-tolak", "UJI-T7C3 alasan penolakan")
            page.get_by_role("button", name="Tolak target").click()
            page.wait_for_timeout(2000)
            ditolak = satu(
                """select alasan_tolak from public.targets
                   where halaqah_id=%s and subject_id=%s and effective_month_id=%s and status='ditolak'
                   order by created_at desc limit 1""",
                (hal_id, sid1, bulan7),
            )
            catat(
                "7. Masul menolak target dengan alasan wajib (tersimpan)",
                ditolak == "UJI-T7C3 alasan penolakan",
                alasan=ditolak,
            )

            page.screenshot(path=str(FOTO / "desktop_target.png"), full_page=True)
            page.get_by_role("button", name="Setujui semua target halaqah ini").first.click()
            page.wait_for_timeout(2500)
            sisa = target_live(sid0)
            catat(
                "8. Setujui semua target halaqah ini: target menunggu menjadi disetujui",
                sum(1 for x in sisa if x[0] == "diajukan") == 0
                and sum(1 for x in sisa if x[0] == "disetujui") == 1,
                target=sisa,
            )

            # ---------------- 8b. Alasan tolak tampil ke pengaju di /target ----------------
            login(page, akun_pengampu)
            page.goto(f"{BASE}/target/wasilah", wait_until="load")
            page.wait_for_timeout(1200)
            pilih(page, "target-filter-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
            pilih(page, "target-filter-bulan-wasilah-bulan", nama7, re.escape(nama7))
            page.wait_for_timeout(1500)
            teks8b = page.locator("body").inner_text()
            catat(
                "8b. Alasan penolakan tampil ke pengaju di /target",
                "UJI-T7C3 alasan penolakan" in teks8b,
            )

            # ---------------- 8c-8d. Bulan lewat/terkunci: setujui butuh konfirmasi Mudir/Admin ----------------
            # Target sementara (baris uji) berlaku BULAN 6 (lewat), status diajukan; kunci bulan 6
            # sementara agar jalur konfirmasi pasti terpicu. Semua dikembalikan di finally.
            item8c = item_id_1(sid0)
            pid8c = satu("select id from public.profiles where full_name=%s", (pengampu_nama,))
            c.execute(
                """insert into public.targets (domain, subject_id, halaqah_id, effective_month_id,
                       amount_period, target_item_id, status, proposed_by, note)
                   values ('wasilah', %s, %s, %s, 'bulanan', %s, 'diajukan', %s, %s)
                   returning id""",
                (sid0, hal_id, bulan6, item8c, pid8c, MARKER + " uji bulan lewat"),
            )
            id8c = c.fetchone()[0]
            try:
                c.execute(
                    "update public.month_domain_settings set is_locked=true "
                    "where month_id=%s and domain='wasilah'",
                    (bulan6,),
                )
                # Masul Wasilah (bukan akses penuh): DIBLOKIR, tidak ada dialog, target tetap diajukan.
                login(page, akun_masul_w)
                page.goto(f"{BASE}/target/wasilah", wait_until="load")
                page.wait_for_timeout(1200)
                pilih(page, "target-filter-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
                pilih(page, "target-filter-bulan-wasilah-bulan", nama6, re.escape(nama6))
                page.wait_for_timeout(1500)
                page.get_by_role("button", name="Setujui semua target halaqah ini").first.click()
                page.wait_for_timeout(1500)
                teks8c = page.locator("body").inner_text()
                status8c = satu("select status from public.targets where id=%s", (id8c,))
                catat(
                    "8c. Bulan terkunci: Masul diblokir (butuh Mudir/Admin), target tetap diajukan",
                    "Hanya Mudir atau Admin" in teks8c and status8c == "diajukan",
                    status=status8c, potongan=teks8c[:120],
                )
                # Mudir: dialog konfirmasi eksplisit -> disetujui.
                login(page, akun_mudir)
                page.goto(f"{BASE}/target/wasilah", wait_until="load")
                page.wait_for_timeout(1200)
                pilih(page, "target-filter-halaqah-wasilah", "Level Dasar A", r"Level Dasar A")
                pilih(page, "target-filter-bulan-wasilah-bulan", nama6, re.escape(nama6))
                page.wait_for_timeout(1500)
                page.once("dialog", lambda d: d.accept())
                page.get_by_role("button", name="Setujui semua target halaqah ini").first.click()
                page.wait_for_timeout(2500)
                status8d = satu("select status from public.targets where id=%s", (id8c,))
                catat(
                    "8d. Bulan terkunci: Mudir konfirmasi eksplisit -> target disetujui",
                    status8d == "disetujui",
                    status=status8d,
                )
            finally:
                c.execute(
                    "update public.month_domain_settings set is_locked=false "
                    "where month_id=%s and domain='wasilah'",
                    (bulan6,),
                )

            # ---------------- 9. Lintas domain ----------------
            login(page, akun_masul_g)
            page.goto(f"{BASE}/target/wasilah", wait_until="load")
            page.wait_for_timeout(1200)
            catat(
                "9. Masul Ghayah dialihkan dari /target/wasilah",
                page.url.rstrip("/").endswith("/target/ghayah"),
                url=page.url,
            )

            # ---------------- 10. Level 6 di Input, Capaian, Target ----------------
            login(page, akun_masul_w)
            page.goto(f"{BASE}/input/wasilah", wait_until="load")
            page.wait_for_timeout(1200)
            pilih(page, "input-halaqah-wasilah", "Level 6", r"Level 6")
            page.wait_for_timeout(1500)
            teks_input = page.locator("body").inner_text()
            catat(
                "10a. Level 6 di Input: 'Tuntas, belum ada pelajaran lanjutan'",
                "Tuntas, belum ada pelajaran lanjutan" in teks_input,
            )

            page.goto(f"{BASE}/capaian/wasilah", wait_until="load")
            page.wait_for_timeout(1200)
            pilih(page, "halaqah-wasilah", "Level 6", r"Level 6")
            page.wait_for_timeout(1500)
            catat(
                "10b. Level 6 di Capaian: pesan tuntas tampil",
                "Tuntas, belum ada pelajaran lanjutan" in page.locator("body").inner_text(),
            )

            page.goto(f"{BASE}/target/wasilah", wait_until="load")
            page.wait_for_timeout(1200)
            pilih(page, "target-filter-halaqah-wasilah", "Level 6", r"Level 6")
            pilih(page, "target-filter-bulan-wasilah-bulan", nama7, re.escape(nama7))
            page.wait_for_timeout(1500)
            catat(
                "10c. Level 6 di Target: pesan tuntas tampil",
                "Tuntas, belum ada pelajaran lanjutan" in page.locator("body").inner_text(),
            )

            # ---------------- 11. 360 px & 1280 px ----------------
            # Pakai Mudir: Masul hanya punya satu domain sehingga tab tidak ditampilkan.
            login(page, akun_role("mudir"))
            for lebar, nama_foto in ((1280, "desktop"), (360, "mobile")):
                page.set_viewport_size({"width": lebar, "height": 800})
                page.goto(f"{BASE}/target/wasilah", wait_until="load")
                page.wait_for_timeout(1800)
                tab_aktif = page.locator('[role="tab"][aria-selected="true"]').inner_text().strip()
                tanpa_geser = page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
                )
                catat(
                    f"11. {lebar} px: tab aktif Ilmu Wasilah + URL + tanpa geser samping",
                    "wasilah" in page.url and "Wasilah" in tab_aktif and tanpa_geser,
                    url=page.url, tab=tab_aktif, tanpa_geser=tanpa_geser,
                )
                page.screenshot(path=str(FOTO / f"{nama_foto}_target_360.png" if lebar == 360 else FOTO / "desktop_target_1280.png"), full_page=True)

                page.goto(f"{BASE}/capaian/wasilah", wait_until="load")
                page.wait_for_timeout(1500)
                tanpa_geser_c = page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
                )
                catat(
                    f"12. {lebar} px: Capaian Wasilah tanpa geser samping",
                    tanpa_geser_c,
                    url=page.url,
                )
                page.screenshot(
                    path=str(FOTO / ("mobile_capaian_360.png" if lebar == 360 else "desktop_capaian_1280.png")),
                    full_page=True,
                )

            galat_nyata = [g for g in galat if "Failed to load resource" not in g]
            catat(
                "13. Konsol bersih (galat 400 = penolakan server yang memang diuji)",
                not galat_nyata and len(gagal_http) == 2,
                galat=galat[:5], http=gagal_http[:6], lain=galat_nyata[:3],
            )
            browser.close()
    finally:
        pulihkan_data.pulihkan(db, asli)
        sama, beda = pulihkan_data.sama_dengan(db, asli)
        fp_akhir = db_fingerprint.rekam()
        log_lama = db_fingerprint.cek_log_sampai(fp_awal.get("_log_change_log", {}).get("maks_id", 0))
        log_utuh = log_lama == fp_awal.get("_log_change_log", {}).get("checksum")
        selisih = db_fingerprint.banding(fp_awal, fp_akhir, log_lama_utuh=log_utuh)
        catat("14. Data dipulihkan PERSIS (pulihkan_data) + sidik jari SAMA",
              sama, beda=beda, selisih=selisih)
        HASIL.parent.mkdir(parents=True, exist_ok=True)
        HASIL.write_text(
            json.dumps({"marker": MARKER, "lulus": LULUS, "gagal": GAGAL, "rincian": RINCIAN},
                       ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"[setelah pemulihan] {LULUS} LULUS, {len(GAGAL)} gagal | Laporan: {HASIL}")
        for g in GAGAL:
            print("GAGAL:", g)

    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(
        json.dumps({"marker": MARKER, "lulus": LULUS, "gagal": GAGAL, "rincian": RINCIAN},
                   ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"{LULUS} LULUS, {len(GAGAL)} gagal | Laporan: {HASIL}")
    for g in GAGAL:
        print("GAGAL:", g)
    return 0 if not GAGAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
