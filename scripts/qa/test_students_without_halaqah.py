#!/usr/bin/env python3
"""
Uji otomatis: notifikasi "santri belum punya halaqah" per domain.

Aturan yang diuji (docs/SPEC.md bagian 9):
  - Mudir/Admin melihat ketiga domain.
  - Masul Al Quran hanya Al Qur'an, Masul Wasilah hanya Ilmu Wasilah,
    Masul Ghayah hanya Ilmu Ghayah.
  - Musyrif/ah dan Mudarris/ah tidak melihat apa pun.
  - anon ditolak (tidak punya EXECUTE pada fungsi).
  - Baris hilang otomatis begitu santri diberi halaqah (diuji dalam transaksi
    lalu ROLLBACK; tidak ada data yang benar-benar diubah).

Implementasi: fungsi `students_without_halaqah()` (daftar) dan
`students_without_halaqah_count()` (ringkasan per domain), security definer,
memeriksa `can_manage(domain)` di dalam fungsi (migrasi 20261121000009).

Data dummy 24 Nov 2026 yang diharapkan:
  - Al Qur'an : 0 santri
  - Wasilah   : 1 santri (NIS ...024)
  - Ghayah    : 2 santri (NIS ...023 dan ...024)

Membaca .env.local; tidak mencetak rahasia.
Jalankan: python scripts/qa/test_students_without_halaqah.py
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "qa" / f"students_without_halaqah_{datetime.date.today().isoformat()}.json"

env: dict[str, str] = {}
for line in open(ROOT / ".env.local", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

results: list[dict] = []


def rec(name: str, ok: bool, detail: str, evidence: dict | None = None) -> None:
    results.append({"name": name, "ok": ok, "detail": detail, "evidence": evidence or {}})
    print(("PASS" if ok else "FAIL"), name, "-", detail)


conn = psycopg.connect(env["DATABASE_URL"], autocommit=True, connect_timeout=20)


def rows(sql: str, params: tuple = ()) -> list[tuple]:
    return conn.execute(sql, params).fetchall()


def satu(sql: str, params: tuple = ()):
    r = rows(sql, params)
    return r[0] if r else None


def profil(role: str):
    r = satu(
        "select id, full_name from public.profiles where role=%s and is_active order by full_name limit 1",
        (role,),
    )
    if not r:
        raise RuntimeError(f"Profil aktif dengan role {role} tidak ditemukan.")
    return str(r[0]), r[1]


def dengan_role(profile_id: str, fn):
    """Jalankan fn() sebagai pengguna authenticated, lalu ROLLBACK."""
    conn.execute("begin")
    try:
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (profile_id,))
        conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        return fn()
    finally:
        conn.rollback()


DETAIL = (
    "select domain::text, nis, full_name, level_label "
    "from public.students_without_halaqah() order by domain, full_name"
)


def baca_detail() -> list[tuple]:
    return rows(DETAIL)


def baca_count() -> list[tuple]:
    return rows(
        "select domain::text, jumlah from public.students_without_halaqah_count() order by domain"
    )


def per_domain_pdt(hasil) -> dict:
    d: dict[str, list] = {}
    for r in hasil:
        d.setdefault(r[0], []).append(r[1])
    return d


# ---------------------------------------------------------------- 0. konteks data lapangan (sebagai postgres)
try:
    semua = rows(
        "select domain::text, nis from public.students_without_halaqah() order by domain, nis"
    )
    per_domain: dict[str, list[str]] = {}
    for d, nis in semua:
        per_domain.setdefault(d, []).append(nis)
    rec(
        "data_dummy_alquran_0_wasilah_1_ghayah_2",
        per_domain.get("alquran", []) == []
        and per_domain.get("wasilah", []) == ["1447.dummy-nis.024"]
        and sorted(per_domain.get("ghayah", [])) == ["1447.dummy-nis.023", "1447.dummy-nis.024"],
        f"alquran={len(per_domain.get('alquran', []))}, wasilah={len(per_domain.get('wasilah', []))}, ghayah={len(per_domain.get('ghayah', []))}",
        {"per_domain": per_domain},
    )
except Exception as e:  # noqa: BLE001
    rec("data_dummy_alquran_0_wasilah_1_ghayah_2", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 1. Mudir dan Admin (daftar)
for role in ("mudir", "admin"):
    try:
        pid, nama = profil(role)
        hasil = dengan_role(pid, baca_detail)
        domain = sorted({r[0] for r in hasil})
        rec(
            f"{role}_melihat_semua_domain",
            sorted(per_domain_pdt(hasil)) == ["ghayah", "wasilah"]
            and {r[1] for r in hasil} >= {"1447.dummy-nis.023", "1447.dummy-nis.024"},
            f"{len(hasil)} baris di domain {domain} (Al Qur'an kosong karena 0 santri)",
            {"profil": nama[0], "baris": [list(r) for r in hasil]},
        )
    except Exception as e:  # noqa: BLE001
        rec(f"{role}_melihat_semua_domain", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 1b. Mudir dan Admin (ringkasan)
for role in ("mudir", "admin"):
    try:
        pid, nama = profil(role)
        hasil = dengan_role(pid, baca_count)
        peta = {r[0]: r[1] for r in hasil}
        rec(
            f"{role}_ringkasan_counts",
            sorted(peta) == ["alquran", "ghayah", "wasilah"]
            and peta["alquran"] == 0 and peta["wasilah"] == 1 and peta["ghayah"] == 2,
            f"ringkasan {peta}",
            {"profil": nama[0]},
        )
    except Exception as e:  # noqa: BLE001
        rec(f"{role}_ringkasan_counts", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 2. Masul per domain
harapan_masul = {
    "masul_alquran": ("alquran", set()),
    "masul_wasilah": ("wasilah", {"1447.dummy-nis.024"}),
    "masul_ghayah": ("ghayah", {"1447.dummy-nis.023", "1447.dummy-nis.024"}),
}
for role, (domain_harap, nis_harap) in harapan_masul.items():
    try:
        pid, nama = profil(role)
        hasil = dengan_role(pid, baca_detail)
        domain = {r[0] for r in hasil}
        nis = {r[1] for r in hasil}
        rec(
            f"{role}_hanya_domain_{domain_harap}",
            domain <= {domain_harap} and nis == nis_harap,
            f"{len(hasil)} baris; domain={sorted(domain) or []}; NIS={sorted(nis) or []}",
            {"profil": nama[0], "baris": [list(r) for r in hasil]},
        )
    except Exception as e:  # noqa: BLE001
        rec(f"{role}_hanya_domain_{domain_harap}", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 3. Musyrif / Mudarris tidak melihat
for role in ("musyrif", "mudarris"):
    try:
        pid, nama = profil(role)
        hasil_detail = dengan_role(pid, baca_detail)
        hasil_count = dengan_role(pid, baca_count)
        rec(
            f"{role}_tidak_melihat_notifikasi",
            hasil_detail == [] and hasil_count == [],
            f"detail={len(hasil_detail)} baris, count={len(hasil_count)} baris (harus 0)",
            {"profil": nama[0]},
        )
    except Exception as e:  # noqa: BLE001
        rec(f"{role}_tidak_melihat_notifikasi", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 4. Santri diberi halaqah -> hilang
try:
    s023 = satu("select id from public.students where nis='1447.dummy-nis.023'")
    tahun = satu("select id from public.academic_years where is_active order by hijri_year desc limit 1")
    halaqah_gh = satu(
        "select id from public.halaqahs where domain='ghayah' and is_active "
        "and academic_year_id=%s order by code limit 1",
        (tahun[0],),
    )
    if not (s023 and tahun and halaqah_gh):
        raise RuntimeError("Konteks santri/halaqah Ghayah tidak lengkap.")

    conn.execute("begin")
    try:
        conn.execute(
            "insert into public.halaqah_members (halaqah_id, student_id) values (%s, %s)",
            (halaqah_gh[0], s023[0]),
        )
        pid_mudir, nama_mudir = profil("mudir")
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claim.sub', %s, true)", (pid_mudir,))
        conn.execute("select set_config('request.jwt.claim.role', 'authenticated', true)")
        hasil = baca_detail()
        ghayah = [r for r in hasil if r[0] == "ghayah"]
        rec(
            "santri_diberi_halaqah_hilang_dari_notifikasi",
            len(ghayah) == 1 and ghayah[0][1] == "1447.dummy-nis.024",
            f"setelah 023 diberi halaqah Ghayah: {len(ghayah)} baris; NIS={[r[1] for r in ghayah]}",
            {"profil": nama_mudir[0], "baris": [list(r) for r in hasil]},
        )
    finally:
        conn.rollback()

    # Pastikan ROLLBACK benar-benar mengembalikan data.
    lagi = dengan_role(profil("mudir")[0], baca_detail)
    ghayah_lagi = sorted(r[1] for r in lagi if r[0] == "ghayah")
    rec(
        "rollback_mengembalikan_data_uji",
        ghayah_lagi == ["1447.dummy-nis.023", "1447.dummy-nis.024"],
        f"setelah ROLLBACK: Ghayah={ghayah_lagi}",
    )
except Exception as e:  # noqa: BLE001
    rec("santri_diberi_halaqah_hilang_dari_notifikasi", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- 5. anon ditolak
try:
    conn.execute("begin")
    try:
        conn.execute("set local role anon")
        conn.execute("select count(*) from public.students_without_halaqah()")
        rec("anon_ditolak", False, "SELECT BERHASIL; seharusnya ditolak.")
    except psycopg.errors.InsufficientPrivilege:
        rec("anon_ditolak", True, "Ditolak (InsufficientPrivilege / 42501).")
    except Exception as e:  # noqa: BLE001
        rec("anon_ditolak", False, f"Ditolak, tetapi bukan karena hak akses: {type(e).__name__}: {e}")
    finally:
        conn.rollback()
except Exception as e:  # noqa: BLE001
    rec("anon_ditolak", False, f"Error: {type(e).__name__}: {e}")

# ---------------------------------------------------------------- ringkasan
conn.close()
gagal = [r for r in results if not r["ok"]]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps(
        {"ran_at": datetime.datetime.now().isoformat(), "tests": results},
        indent=2,
        default=str,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"\n{len(results) - len(gagal)}/{len(results)} PASS. Laporan: {OUT}")
sys.exit(1 if gagal else 0)