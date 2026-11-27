"""Uji T7c [2/3] BACKEND: simpan gabungan capaian + target bulan depan (Wasilah/Ghayah).

Diuji langsung di database (satu transaksi besar + ROLLBACK; savepoint bernama unik;
tidak ada data yang berubah).
  1. Simpan gabungan berhasil: capaian disalin ke semua anggota + target bulan depan dibuat.
  2. Ditolak bila ada mapel aktif (yang boleh ditulis) tanpa target; capaian tidak tersimpan.
  3. Mapel yang sudah TUNTAS (butir terakhir buku terakhir) dikecualikan dari kewajiban target.
  4. Bulan tanpa bulan berikutnya: target tidak diminta; mengirim target ditolak jelas.
  5. Hak per role: pengampu -> 'diajukan'; Masul domain/Mudir/Admin -> 'disetujui';
     Masul domain lain & Masul Al Quran -> ditolak; anon ditolak.
  6. Target di bawah capaian diterima, dilaporkan di `di_bawah_capaian`.
  7. Level 6 (tanpa mapel) -> "Tuntas, belum ada pelajaran lanjutan", tidak menulis.
  8. `v_monthly_report` Al Qur'an SEBELUM vs SESUDAH simpan gabungan IDENTIK.

Pakai:
  python scripts/qa/test_t7c_simpan_gabungan.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import psycopg

OUT = pathlib.Path("docs/qa/t7c_simpan_gabungan.json")
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
    bulan6 = satu("select id from public.hijri_months where month_no=6")
    bulan7 = satu("select id from public.hijri_months where month_no=7")
    bulan12 = satu("select id from public.hijri_months where month_no=12")
    assert satu("select bulan_berikutnya(%s)", (bulan6,)) == bulan7
    assert satu("select bulan_berikutnya(%s)", (bulan12,)) is None
    hal6 = satu("select id from public.halaqahs where domain='wasilah' and code='Level 6'")

    c.execute("select subject_id, name from public.halaqah_mapel_aktif(%s,%s)", (hal_w, bulan6))
    mw = c.fetchall()  # [(subject_id, name), ...]

    def item(subject: str, arah: str = "first") -> str:
        o = "asc" if arah == "first" else "desc"
        return satu(f"""select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
                        where b.subject_id=%s order by b.sort_order {o}, b.stage_order {o}, ci.seq {o} limit 1""",
                    (subject,))

    def anggota(halaqah: str) -> int:
        return satu("select count(*) from public.halaqah_members where halaqah_id=%s and left_on is null", (halaqah,))

    def jadi(role: str) -> None:
        if role == "anon":
            c.execute("set local role anon")
        else:
            c.execute("set local role authenticated")
            c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P[role]),))
            c.execute("select set_config('request.jwt.claim.role','authenticated', true)")

    def set_role_uid(uid: str) -> None:
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(uid),))
        c.execute("select set_config('request.jwt.claim.role','authenticated', true)")

    def panggil(args: tuple) -> object:
        c.execute("select public.wasilah_simpan_gabungan(%s,%s,%s::jsonb,%s::jsonb,%s)",
                  (args[0], args[1], json.dumps(args[2], default=str),
                   json.dumps(args[3], default=str), args[4]))
        return c.fetchone()[0]

    def coba(role: str, args: tuple) -> tuple[str, object, str]:
        """Jalankan, lalu SELALU rollback ke savepoint. Cocok untuk uji tolak/terima saja."""
        c.execute("savepoint coba")
        try:
            jadi(role)
            res = panggil(args)
            return "DITERIMA", res, ""
        except psycopg.errors.Error as e:  # noqa: PERF203
            return "DITOLAK", None, " ".join(str(e).split("\n")[0].split())[:300]
        finally:
            c.execute("rollback to savepoint coba")

    def capaian_semua(arah: str = "first") -> list[dict]:
        return [{"subject_id": sid, "item_id": item(sid, arah)} for sid, _ in mw]

    def target_semua(arah: str = "first") -> list[dict]:
        return [{"subject_id": sid, "target_item_id": item(sid, arah)} for sid, _ in mw]

    n = anggota(hal_w)

    # ============================================================ 1. Mudir berhasil (inspeksi)
    c.execute("savepoint s1")
    jadi("mudir")
    try:
        res = panggil((hal_w, bulan6, capaian_semua(), target_semua(), False))
        st, pesan = "DITERIMA", ""
    except psycopg.errors.Error as e:  # noqa: PERF203
        res, st, pesan = None, "DITOLAK", str(e).split("\n")[0]
    n_target = satu("""select count(*) from public.targets
                       where halaqah_id=%s and effective_month_id=%s and status='disetujui'""",
                    (hal_w, bulan7))
    n_pe = satu("""select count(*) from public.progress_entries
                   where halaqah_id=%s and month_id=%s""", (hal_w, bulan6))
    c.execute("rollback to savepoint s1")
    catat("1a. Mudir: simpan gabungan berhasil (capaian + target bulan depan)",
          st == "DITERIMA" and res and res["bulan_depan"] == str(bulan7)
          and res["baris"] == len(mw) * n and res["target"] == len(mw), res=res, pesan=pesan)
    catat("1b. Capaian tersalin ke semua anggota + target 'disetujui' untuk tiap mapel",
          n_pe == len(mw) * n and n_target == len(mw), n_pe=n_pe, n_target=n_target, anggota=n)

    # ============================================================ 2. ditolak tanpa target
    awal_pe = satu("""select count(*) from public.progress_entries
                      where halaqah_id=%s and month_id=%s""", (hal_w, bulan6))
    st, _, pesan = coba("mudir", (hal_w, bulan6, capaian_semua(),
                                  [{"subject_id": mw[0][0], "target_item_id": item(mw[0][0])}], False))
    akhir_pe = satu("""select count(*) from public.progress_entries
                       where halaqah_id=%s and month_id=%s""", (hal_w, bulan6))
    catat("2. Ditolak bila mapel aktif belum punya target",
          st == "DITOLAK" and "Target bulan depan belum diisi" in (pesan or ""), pesan=pesan)
    catat("2b. Capaian tidak tersimpan saat simpan gabungan ditolak", awal_pe == akhir_pe,
          awal=awal_pe, akhir=akhir_pe)

    # ============================================================ 3. tuntas dikecualikan
    c.execute("savepoint s3")
    sid0 = mw[0][0]
    c.execute("""insert into public.progress_entries (student_id, halaqah_id, subject_id, month_id, item_id, putaran)
                 select hm.student_id, %s, %s, %s, %s, 1
                 from public.halaqah_members hm where hm.halaqah_id=%s and hm.left_on is null
                 on conflict (student_id, subject_id, month_id) do update set item_id=excluded.item_id""",
              (hal_w, sid0, bulan6, item(sid0, "last"), hal_w))
    res3 = None
    try:
        jadi("mudir")
        res3 = panggil((hal_w, bulan6, [], [{"subject_id": mw[1][0], "target_item_id": item(mw[1][0])}], False))
        st3, pesan3 = "DITERIMA", ""
    except psycopg.errors.Error as e:  # noqa: PERF203
        st3, pesan3 = "DITOLAK", str(e).split("\n")[0]
    c.execute("rollback to savepoint s3")
    catat("3. Mapel TUNTAS dikecualikan dari kewajiban target",
          st3 == "DITERIMA" and res3 and res3["target"] == 1, res=res3, pesan=pesan3)

    # ============================================================ 4. bulan tanpa bulan berikutnya
    st, res, pesan = coba("mudir", (hal_w, bulan12, capaian_semua(), [], False))
    catat("4a. Bulan terakhir: target TIDAK diminta (simpan capaian saja)", st == "DITERIMA", res=res, pesan=pesan)
    st, _, pesan = coba("mudir", (hal_w, bulan12, [], [{"subject_id": mw[0][0], "target_item_id": item(mw[0][0])}], False))
    catat("4b. Bulan terakhir: mengirim target ditolak jelas",
          st == "DITOLAK" and "Tidak ada bulan berikutnya" in (pesan or ""), pesan=pesan)

    # ============================================================ 5. hak per role
    pengampu = satu("""select ht.profile_id from public.halaqah_teachers ht
                       where ht.halaqah_id=%s and ht.subject_id=%s limit 1""", (hal_w, mw[0][0]))
    c.execute("savepoint s5")
    try:
        set_role_uid(pengampu)
        panggil((hal_w, bulan6,
                 [{"subject_id": mw[0][0], "item_id": item(mw[0][0])}],
                 [{"subject_id": mw[0][0], "target_item_id": item(mw[0][0])}], False))
        status_p = satu("""select status from public.targets where halaqah_id=%s and subject_id=%s
                           and effective_month_id=%s order by created_at desc limit 1""", (hal_w, mw[0][0], bulan7))
        catat("5a. Pengampu mapelnya sendiri: target 'diajukan'", status_p == "diajukan", status=status_p)
    except psycopg.errors.Error as e:  # noqa: PERF203
        catat("5a. Pengampu mapelnya sendiri: target 'diajukan'", False, pesan=str(e).split("\n")[0])
    c.execute("rollback to savepoint s5")

    st, res, pesan = coba("masul_wasilah", (hal_w, bulan6, capaian_semua(), target_semua(), False))
    catat("5b. Masul Wasilah: tersimpan, target 'disetujui'",
          st == "DITERIMA" and res and res["target"] == len(mw), res=res, pesan=pesan)

    st, _, pesan = coba("masul_ghayah", (hal_w, bulan6, capaian_semua(), target_semua(), False))
    catat("5c. Masul Ghayah di halaqah Wasilah: DITOLAK", st == "DITOLAK", pesan=pesan)

    st, _, pesan = coba("masul_alquran", (hal_w, bulan6, capaian_semua(), target_semua(), False))
    catat("5d. Masul Al Quran di halaqah Wasilah: DITOLAK", st == "DITOLAK", pesan=pesan)

    st, _, pesan = coba("anon", (hal_w, bulan6, capaian_semua(), target_semua(), False))
    catat("5e. anon: DITOLAK (tanpa EXECUTE)", st == "DITOLAK", pesan=pesan)

    # ============================================================ 6. target di bawah capaian
    c.execute("savepoint s6")
    sid0 = mw[0][0]
    item_bawah = item(sid0, "first")
    item_atas = satu("""select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
                        where b.subject_id=%s order by b.sort_order, b.stage_order, ci.seq offset 2 limit 1""", (sid0,))
    try:
        jadi("mudir")
        res6 = panggil((hal_w, bulan6,
                        [{"subject_id": sid0, "item_id": item_atas}],
                        [{"subject_id": sid0, "target_item_id": item_bawah},
                         {"subject_id": mw[1][0], "target_item_id": item(mw[1][0])}], False))
        ada_bawah = bool(res6 and any(str(x["subject_id"]) == str(sid0) for x in res6.get("di_bawah_capaian", [])))
        catat("6. Target di bawah capaian DITERIMA + dilaporkan di di_bawah_capaian", ada_bawah, res=res6)
    except psycopg.errors.Error as e:  # noqa: PERF203
        catat("6. Target di bawah capaian DITERIMA + dilaporkan di di_bawah_capaian", False, pesan=str(e).split("\n")[0])
    c.execute("rollback to savepoint s6")

    # ============================================================ 7. Level 6
    st, res, pesan = coba("mudir", (hal6, bulan6, [], [], False))
    catat("7. Level 6 (tanpa mapel): 'Tuntas, belum ada pelajaran lanjutan', tidak menulis",
          st == "DITERIMA" and res and res.get("tanpa_mapel") is True
          and "Tuntas" in (res.get("pesan") or ""), res=res, pesan=pesan)

    # ============================================================ 8. Al Qur'an identik
    def hash_alquran() -> str:
        return satu("""select md5(coalesce(jsonb_agg(to_jsonb(x) order by x.entry_id)::text,'[]'))
                       from public.v_monthly_report x where x.domain='alquran'""")

    c.execute("savepoint s8")
    h_sebelum = hash_alquran()
    res8 = None
    try:
        jadi("mudir")
        res8 = panggil((hal_w, bulan6, capaian_semua(), target_semua(), False))
        st8 = "DITERIMA"
    except psycopg.errors.Error as e:  # noqa: PERF203
        st8, res8 = "DITOLAK", str(e).split("\n")[0]
    h_sesudah = hash_alquran()
    c.execute("rollback to savepoint s8")
    catat("8. v_monthly_report Al Qur'an SEBELUM vs SESUDAH simpan gabungan identik",
          st8 == "DITERIMA" and h_sebelum == h_sesudah, sebelum=h_sebelum[:12], sesudah=h_sesudah[:12])

    conn.rollback()
    conn.close()

    hasil = {
        "lulus": LULUS,
        "gagal": GAGAL,
        "ringkasan": f"{LULUS} LULUS, {GAGAL}" if GAGAL else f"{LULUS} LULUS, 0 gagal",
        "rincian": RINCIAN,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(hasil, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for r in RINCIAN:
        print(("PASS " if r["ok"] else "GAGAL ") + r["uji"])
    print(hasil["ringkasan"], "| Laporan:", OUT)
    return 0 if not GAGAL else 1


if __name__ == "__main__":
    sys.exit(main())
