"""Uji T7c [3/3]: kewajiban target baru (keputusan Mudir a) + form + notifikasi.

Diuji langsung di database (satu transaksi + ROLLBACK; savepoint; tidak ada data berubah):
  1. Target WAJIB hanya untuk mapel yang capaiannya dikirim.
  2. Ditolak bila mapel yang capaiannya dikirim belum punya target DAN belum ada target.
  3. Tidak wajib bila target bulan depan SUDAH ada (diajukan/disetujui).
  4. Koreksi capaian tanpa mengisi target: target lama tidak berubah/bertambah.
  5. Target sama yang dikirim ulang tidak membuat baris baru.
  6. Jalur simpan lama (wasilah_input_save) DITUTUP.
  7. wasilah_input_form memuat target bulan ini/depan, label+posisi, bulan depan, Level 6.
  8. Pengampu tidak boleh mengganti target yang sudah disetujui lewat simpan gabungan.
  9. Masul domain boleh mengganti target disetujui (baris lama -> dibatalkan, baru -> disetujui).
 10. target_belum_domain: hanya Masul domain/Mudir/Admin; Level 6 ditandai; tuntas & ada target.
 11. Mapel TUNTAS tidak diwajibkan target.

Pakai:
  python scripts/qa/test_t7c3_kewajiban_target.py
"""
from __future__ import annotations

import json
import pathlib

import psycopg

OUT = pathlib.Path("docs/qa/t7c3_kewajiban_target.json")
LULUS = 0
GAGAL: list[str] = []
RINCIAN: list[dict] = []


def catat(nama: str, ok: bool, **info) -> None:
    global LULUS
    RINCIAN.append({"uji": nama, "ok": ok, **info})
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


def main() -> int:  # noqa: C901 - uji berurutan
    conn = psycopg.connect(env_local()["DATABASE_URL"], autocommit=False, connect_timeout=30)
    c = conn.cursor()

    def satu(q: str, a: tuple = ()):
        c.execute(q, a)
        return c.fetchone()[0]

    P: dict[str, str] = {}
    for role, pid in c.execute(
        "select role, id from public.profiles where is_active order by full_name").fetchall():
        P.setdefault(role, pid)

    hal_w = satu("select id from public.halaqahs where domain='wasilah' and code='Level 1A'")
    hal6 = satu("select id from public.halaqahs where domain='wasilah' and code='Level 6'")
    bulan6 = satu("select id from public.hijri_months where month_no=6")
    bulan7 = satu("select id from public.hijri_months where month_no=7")
    assert satu("select bulan_berikutnya(%s)", (bulan6,)) == bulan7

    c.execute("select subject_id, name from public.halaqah_mapel_aktif(%s,%s)", (hal_w, bulan6))
    mw = c.fetchall()
    sid0, sid1 = mw[0][0], mw[1][0]

    def item(subject: str, arah: str = "first") -> str:
        o = "asc" if arah == "first" else "desc"
        return satu(
            f"""select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
                where b.subject_id=%s and ci.is_active and b.is_active
                order by b.sort_order {o}, b.stage_order {o}, ci.seq {o} limit 1""",
            (subject,),
        )

    def item2(subject: str) -> str:
        return satu(
            """select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
               where b.subject_id=%s and ci.is_active and b.is_active
               order by b.sort_order, b.stage_order, ci.seq offset 1 limit 1""",
            (subject,),
        )

    def simpan(args: tuple) -> object:
        c.execute(
            "select public.wasilah_simpan_gabungan(%s,%s,%s::jsonb,%s::jsonb,%s)",
            (args[0], args[1], json.dumps(args[2], default=str),
             json.dumps(args[3], default=str), args[4]),
        )
        return c.fetchone()[0]

    def jadi(role: str) -> None:
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P[role]),))
        c.execute("select set_config('request.jwt.claim.role','authenticated', true)")

    def reset() -> None:
        c.execute("reset role")
        c.execute("select set_config('request.jwt.claim.sub','',true)")

    def coba(role: str, args: tuple) -> tuple[str, object, str]:
        c.execute("savepoint coba")
        try:
            jadi(role)
            res = simpan(args)
            return "DITERIMA", res, ""
        except psycopg.errors.Error as e:  # noqa: PERF203
            return "DITOLAK", None, " ".join(str(e).split("\n")[0].split())[:300]
        finally:
            c.execute("rollback to savepoint coba")
            reset()

    def target_rows(subject: str, bulan: str = bulan7) -> list[tuple]:
        c.execute(
            """select status, target_item_id from public.targets
               where halaqah_id=%s and subject_id=%s and effective_month_id=%s
               order by created_at, id""",
            (hal_w, subject, bulan),
        )
        return c.fetchall()

    # ============================================================ 1. wajib hanya mapel yang dikirim
    st, res, pesan = coba("mudir", (hal_w, bulan6,
        [{"subject_id": sid0, "item_id": item(sid0)}],
        [{"subject_id": sid0, "target_item_id": item(sid0)}], False))
    catat("1. Mapel tanpa capaian TIDAK diminta target (hanya mapel yang dikirim)",
          st == "DITERIMA" and res and res["target"] == 1 and res["mapel"] == 1,
          res=res, pesan=pesan)

    # ============================================================ 2. ditolak (mapel dikirim tanpa target)
    st, _, pesan = coba("mudir", (hal_w, bulan6,
        [{"subject_id": sid0, "item_id": item(sid0)}], [], False))
    catat("2. Ditolak bila mapel yang capaiannya dikirim belum punya target",
          st == "DITOLAK" and "Target bulan depan belum diisi" in pesan, pesan=pesan)

    # ============================================================ 3-5. target sudah ada
    c.execute("savepoint s3")
    jadi("mudir")
    simpan((hal_w, bulan6, [], [{"subject_id": sid0, "target_item_id": item(sid0)}], False))
    reset()
    n_awal = len(target_rows(sid0))
    catat("3a. Target saja (tanpa capaian) boleh disimpan; jadi target hidup",
          n_awal == 1 and target_rows(sid0)[0][0] == "disetujui", rows=target_rows(sid0))

    st, res, pesan = coba("mudir", (hal_w, bulan6,
        [{"subject_id": sid0, "item_id": item2(sid0)}], [], False))
    catat("3b. Tidak wajib mengisi ulang target bila target bulan depan SUDAH ada",
          st == "DITERIMA" and res and res["target"] == 0, res=res, pesan=pesan)

    st, res, pesan = coba("mudir", (hal_w, bulan6,
        [{"subject_id": sid0, "item_id": item(sid0)}],
        [{"subject_id": sid0, "target_item_id": item(sid0)}], False))
    catat("4. Koreksi capaian + target SAMA: tidak membuat baris target baru",
          st == "DITERIMA" and res and res["target"] == 0 and len(target_rows(sid0)) == n_awal,
          res=res, rows=target_rows(sid0), pesan=pesan)

    # ============================================================ 5. jalur lama ditutup
    c.execute("savepoint s5")
    jadi("mudir")
    try:
        c.execute("select public.wasilah_input_save(%s,%s,%s::jsonb)",
                  (hal_w, bulan6, json.dumps([{"subject_id": str(sid0), "item_id": str(item(sid0))}])))
        st5, pesan5 = "DITERIMA", ""
    except psycopg.errors.Error as e:  # noqa: PERF203
        st5, pesan5 = "DITOLAK", " ".join(str(e).split("\n")[0].split())
    c.execute("rollback to savepoint s5")
    reset()
    catat("5. Jalur simpan lama (capaian saja) DITUTUP",
          st5 == "DITOLAK" and "ditutup" in pesan5, pesan=pesan5)

    # ============================================================ 6. bentuk form
    form = satu("select public.wasilah_input_form(%s,%s)", (hal_w, bulan6))
    mapel0 = next((m for m in form["mapel"] if str(m["id"]) == str(sid0)), None)
    depan0 = next((t for t in form["target_depan"] if str(t["subject_id"]) == str(sid0)), None)
    ini0 = next((t for t in form["target_ini"] if str(t["subject_id"]) == str(sid0)), None)
    catat("6a. Form memuat bulan_depan, target bulan ini, target bulan depan, tanpa_mapel",
          form.get("bulan_depan") is not None and isinstance(form.get("target_ini"), list)
          and isinstance(form.get("target_depan"), list) and form.get("tanpa_mapel") is False)
    catat("6b. Target depan berlabel + posisi; mapel punya penanda tuntas",
          bool(depan0 and depan0.get("item_label") and depan0.get("pos") is not None)
          and bool(mapel0 and "tuntas" in mapel0),
          depan=depan0)

    # ============================================================ 7. pengampu vs masul
    pengampu = satu(
        """select ht.profile_id from public.halaqah_teachers ht
           where ht.halaqah_id=%s and ht.subject_id=%s limit 1""", (hal_w, sid0))
    # Pengampu memakai uid, bukan nama role.
    c.execute("savepoint s7")
    c.execute("set local role authenticated")
    c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(pengampu),))
    c.execute("select set_config('request.jwt.claim.role','authenticated', true)")
    try:
        simpan((hal_w, bulan6,
                [{"subject_id": sid0, "item_id": item2(sid0)}],
                [{"subject_id": sid0, "target_item_id": item2(sid0)}], False))
        st7, pesan7 = "DITERIMA", ""
    except psycopg.errors.Error as e:  # noqa: PERF203
        st7, pesan7 = "DITOLAK", " ".join(str(e).split("\n")[0].split())[:300]
    c.execute("rollback to savepoint s7")
    reset()
    catat("7a. Pengampu TIDAK boleh mengganti target yang sudah disetujui lewat simpan gabungan",
          st7 == "DITOLAK" and "sudah disetujui" in pesan7, pesan=pesan7)

    c.execute("savepoint s8")
    jadi("masul_wasilah")
    try:
        simpan((hal_w, bulan6,
                [{"subject_id": sid0, "item_id": item2(sid0)}],
                [{"subject_id": sid0, "target_item_id": item2(sid0)}], False))
        st8, pesan8 = "DITERIMA", ""
    except psycopg.errors.Error as e:  # noqa: PERF203
        st8, pesan8 = "DITOLAK", " ".join(str(e).split("\n")[0].split())[:300]
    rows8 = target_rows(sid0)
    c.execute("rollback to savepoint s8")
    reset()
    catat("7b. Masul domain mengganti target disetujui: lama dibatalkan, baru disetujui",
          st8 == "DITERIMA"
          and sum(1 for s, _ in rows8 if s == "disetujui") == 1
          and any(s == "dibatalkan" for s, _ in rows8), st=st8, rows=rows8, pesan=pesan8)

    # ============================================================ 8. notifikasi
    c.execute("savepoint s9")
    jadi("masul_wasilah")
    c.execute("select halaqah_code, subject_name, tuntas, level6, ada_disetujui, ada_diajukan "
              "from public.target_belum_domain('wasilah', %s)", (bulan6,))
    rows_mw = c.fetchall()
    c.execute("reset role")
    jadi("masul_ghayah")
    c.execute("select count(*) from public.target_belum_domain('wasilah', %s)", (bulan6,))
    n_gh = c.fetchone()[0]
    c.execute("reset role")
    jadi("mudir")
    c.execute("select count(*) from public.target_belum_domain('wasilah', %s)", (bulan6,))
    n_md = c.fetchone()[0]
    c.execute("rollback to savepoint s9")
    reset()
    level6 = [r for r in rows_mw if r[3] is True]
    ada0 = [r for r in rows_mw if r[1] == mw[0][1] and r[4] is True]
    catat("8a. Notifikasi: Masul domain dapat baris, level 6 ditandai, target terdeteksi",
          len(rows_mw) > 0 and len(level6) == 1 and len(ada0) == 1,
          baris=len(rows_mw), level6=len(level6), ada=len(ada0))
    catat("8b. Notifikasi: Masul domain lain 0 baris, Mudir dapat baris", n_gh == 0 and n_md > 0,
          masul_ghayah=n_gh, mudir=n_md)

    # ============================================================ 9. tuntas
    c.execute("savepoint s10")
    c.execute(
        """insert into public.progress_entries (student_id, halaqah_id, subject_id, month_id, item_id, putaran)
           select hm.student_id, %s, %s, %s, %s, 1 from public.halaqah_members hm
           where hm.halaqah_id=%s and hm.left_on is null
           on conflict (student_id, subject_id, month_id) do update set item_id=excluded.item_id""",
        (hal_w, sid1, bulan6, item(sid1, "last"), hal_w))
    reset()
    st, res, pesan = coba("mudir", (hal_w, bulan6,
        [{"subject_id": sid1, "item_id": item(sid1, "last")}], [], False))
    catat("9. Mapel TUNTAS tidak diwajibkan target", st == "DITERIMA", res=res, pesan=pesan)
    c.execute("rollback to savepoint s10")

    conn.rollback()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"lulus": LULUS, "gagal": GAGAL, "rincian": RINCIAN}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    print(f"{LULUS} LULUS, {len(GAGAL)} gagal | Laporan: {OUT}")
    if GAGAL:
        for g in GAGAL:
            print("GAGAL:", g)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
