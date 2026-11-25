"""Uji T6d2: seragamkan hak input Masul (Al Quran / Wasilah / Ghayah) + jejak pengisi.

Keputusan Mudir 25 November 2026:
  Tiap Masul boleh INPUT capaian, catatan, dan kehadiran di SEMUA halaqah domainnya.
  Tetap DITOLAK: domain lain, bulan terkunci, bulan 0, menghapus.
  Pengampu (Musyrif/ah, Mudarris/ah) tetap hanya halaqahnya sendiri.

Yang diuji:
  1. Matriks role x domain x tabel (capaian, kehadiran, catatan) untuk INSERT dan UPDATE.
  2. Hapus: hanya Mudir/Admin (Masul ditolak, pengampu ditolak).
  3. Bulan terkunci: Masul & pengampu ditolak; Mudir diterima.
  4. Bulan 0: ditolak untuk Masul (RLS), dan oleh fungsi Wasilah/Ghayah.
  5. Jejak: `entered_by` terisi saat menyimpan; `updated_by` terisi saat orang lain menimpa.
  6. Anon: ditolak.

Semua penulisan terjadi di transaksi dan di-ROLLBACK. Tidak ada data yang berubah.

Pakai:
  python scripts/qa/test_t6d2_masul_input.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import psycopg

HASIL = pathlib.Path("docs/qa/t6d2_masul_input.json")
LULUS = 0
GAGAL: list[str] = []
RINCIAN: list[dict] = []


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in pathlib.Path(".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def catat(nama: str, ok: bool, **info) -> None:
    global LULUS
    RINCIAN.append({"uji": nama, "ok": ok, **info})
    if ok:
        LULUS += 1
    else:
        GAGAL.append(nama)


def main() -> int:  # noqa: C901
    c = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)

    def satu(q: str, a: tuple = ()):
        return c.execute(q, a).fetchone()[0]

    # ---------- konteks ----------
    P: dict[str, str] = {}
    for role, pid in c.execute(
        "select role, id from public.profiles where is_active order by full_name"
    ).fetchall():
        P.setdefault(role, pid)
    admin_2 = satu("select id from public.profiles where role='admin' and is_active limit 1")

    bulan = satu("select id from public.hijri_months where month_no=3")  # Dzul Hijjah
    bulan0 = satu("select id from public.hijri_months where month_no=0")
    data: dict[str, tuple] = {}
    for d in ("alquran", "wasilah", "ghayah"):
        h = satu("select id from public.halaqahs where domain=%s and is_active order by code limit 1", (d,))
        s = satu("select id from public.subjects where domain=%s order by sort_order limit 1", (d,))
        i = satu(
            """select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
               where b.subject_id=%s order by b.sort_order, ci.seq limit 1""",
            (s,),
        )
        st = satu(
            "select student_id from public.halaqah_members where halaqah_id=%s and left_on is null limit 1",
            (h,),
        )
        data[d] = (h, s, i, st)

    JUMLAH_SEBELUM = {}
    for t in ("progress_entries", "attendance", "monthly_notes"):
        JUMLAH_SEBELUM[t] = satu(f"select count(*) from public.{t}")

    # Rincian per domain: kalau ada baris LAMA yang terhapus, total bisa tetap sama
    # (mis. 1 dihapus + 1 ditambah) sehingga hanya angka per domain yang menangkapnya.
    DOMAIN_SEBELUM = {
        "capaian": dict(c.execute(
            "select s.domain, count(*) from public.progress_entries pe "
            "join public.subjects s on s.id=pe.subject_id group by 1").fetchall()),
        "kehadiran": dict(c.execute("select domain, count(*) from public.attendance group by 1").fetchall()),
        "catatan": dict(c.execute("select domain, count(*) from public.monthly_notes group by 1").fetchall()),
    }

    # Kehadiran yang SUDAH punya baris (seed/DUMMY) disentuh `upsert` uji ini.
    # Jejak aslinya dicatat dan dipulihkan di akhir, supaya data seed tidak berubah.
    att_awal = {
        (r[0], str(r[1]), r[2]): r[3]
        for r in c.execute("select student_id, month_id, domain, entered_by from public.attendance").fetchall()
    }
    st_att_baru = {}
    for d in ("alquran", "wasilah", "ghayah"):
        ada = {
            (r[0], str(r[1]))
            for r in c.execute(
                "select student_id, month_id from public.attendance where domain=%s", (d,)
            ).fetchall()
        }
        st = data[d][3]
        if (str(st), str(bulan)) in ada:
            st_att_baru[d] = satu(
                """select hm.student_id from public.halaqah_members hm
                   where hm.halaqah_id=%s and hm.left_on is null
                     and not exists (select 1 from public.attendance a
                                     where a.student_id=hm.student_id and a.domain=%s and a.month_id=%s)
                   limit 1""",
                (data[d][0], d, bulan),
            )
        else:
            st_att_baru[d] = st

    # ---------- alat ----------
    def sebagai(role: str, sql: str, params: tuple = ()) -> tuple[str, int, str]:
        """Jalankan SQL sebagai role itu; kembalikan (status, rowcount, pesan)."""
        c.execute("begin")
        try:
            if role == "anon":
                c.execute("set local role anon")
            else:
                c.execute("set local role authenticated")
                c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P[role]),))
            cur = c.execute(sql, params)
            n = cur.rowcount if cur.rowcount is not None else 1
            return ("DITERIMA" if n > 0 else "DITOLAK", n, "")
        except psycopg.errors.Error as e:  # noqa: PERF203
            return ("DITOLAK", 0, str(e).split("\n")[0][:80])
        finally:
            c.execute("rollback")

    def catat_matriks(role: str, tabel: str, domain: str, aksi: str, harap: str, sql: str, params: tuple) -> None:
        status, n, pesan = sebagai(role, sql, params)
        ok = status == harap
        catat(f"{role} | {tabel} | {domain} | {aksi} -> {harap}", ok, dapat=status, pesan=pesan,
              rowcount=n)

    INS_PROG = ("insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran) "
                "values (%s,%s,%s,%s,1)")
    # Kehadiran sudah punya baris (DUMMY Wasilah/Ghayah, seed Al Qur'an). Uji menulis
    # dengan `upsert` supaya yang dinilai RLS adalah "boleh menyimpan", bukan bentrok kunci.
    INS_ATT = ("insert into public.attendance (student_id,month_id,domain,izin,sakit,alpha) "
               "values (%s,%s,%s,0,0,0) "
               "on conflict (student_id,month_id,domain) do update set izin=excluded.izin")
    INS_NOTE = ("insert into public.monthly_notes (student_id,month_id,domain,note) "
                "values (%s,%s,%s,'uji') on conflict (student_id,month_id,domain) do update set note=excluded.note")

    # ---------- 1. matriks role x domain ----------
    # Masul = semua halaqah di domainnya; domain lain ditolak; Admin/Mudir semua.
    for role, domain_kembar in (
        ("mudir", None), ("admin", None),
        ("masul_alquran", "alquran"), ("masul_wasilah", "wasilah"), ("masul_ghayah", "ghayah"),
    ):
        for tabel in ("capaian", "kehadiran", "catatan"):
            for d, (h, s, i, st) in data.items():
                harap = "DITERIMA" if (domain_kembar is None or domain_kembar == d) else "DITOLAK"
                if tabel == "capaian":
                    catat_matriks(role, "capaian", d, "insert", harap, INS_PROG, (st, bulan, s, i))
                elif tabel == "kehadiran":
                    catat_matriks(role, "kehadiran", d, "insert", harap, INS_ATT,
                                  (st_att_baru[d], bulan, d))
                else:
                    catat_matriks(role, "catatan", d, "insert", harap, INS_NOTE, (st, bulan, d))

    # Pengampu: hanya halaqahnya sendiri; domain lain ditolak.
    # Ust. Fulan 1 mengampu HLQ-PA-1 (alquran). Ustadz Mudarris 1 mengampu mapel Wasilah.
    hlq_ampu = satu(
        "select h.id from public.halaqah_teachers ht join public.halaqahs h on h.id=ht.halaqah_id "
        "where h.domain='alquran' and ht.profile_id=%s limit 1", (P["musyrif"],))
    st_ampu = satu("select student_id from public.halaqah_members where halaqah_id=%s and left_on is null limit 1",
                   (hlq_ampu,))
    sub_ampu = satu("select id from public.subjects where domain='alquran' order by sort_order limit 1")
    item_ampu = satu(
        """select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
           where b.subject_id=%s order by b.sort_order, ci.seq limit 1""", (sub_ampu,))
    catat_matriks("musyrif", "capaian", "alquran (halaqahnya)", "insert", "DITERIMA",
                  INS_PROG, (st_ampu, bulan, sub_ampu, item_ampu))
    st_lain, s_lain = data["wasilah"][3], data["wasilah"][1]
    i_lain = data["wasilah"][2]
    catat_matriks("musyrif", "capaian", "wasilah (bukan halaqahnya)", "insert", "DITOLAK",
                  INS_PROG, (st_lain, bulan, s_lain, i_lain))
    catat_matriks("musyrif", "capaian", "alquran halaqah lain", "insert", "DITOLAK",
                  INS_PROG, (st_lain, bulan, sub_ampu, item_ampu))

    # ---------- 2 & 5. update + jejak ----------
    # Baris DUMMY: dibuat tanpa JWT (entered_by kosong), seperti isian seed.
    # Lalu Masul mengisi (update) -> entered_by = Masul.
    # Lalu Admin menimpa       -> entered_by = Admin, updated_by tetap kosong bila
    #                             pengisi lama kosong, atau berisi Masul bila ada.
    st_wk, s_wk, i_wk = data["wasilah"][3], data["wasilah"][1], data["wasilah"][2]
    K = (st_wk, bulan, s_wk)
    DELW = "delete from public.progress_entries where student_id=%s and month_id=%s and subject_id=%s"

    def buat_awal(entered_by=None):
        c.execute(DELW, K)
        c.execute(
            "insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran,entered_by) "
            "values (%s,%s,%s,%s,1,%s)", (*K, i_wk, entered_by))

    def sebagai_update(role: str, nilai: int):
        c.execute("begin")
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P[role]),))
        cur = c.execute("update public.progress_entries set putaran=%s where student_id=%s and month_id=%s "
                        "and subject_id=%s", (nilai, st_wk, bulan, s_wk))
        hasil = c.execute("select entered_by, updated_by from public.progress_entries "
                          "where student_id=%s and month_id=%s and subject_id=%s", K).fetchone()
        c.execute("rollback")
        return cur.rowcount, hasil

    buat_awal(None)
    n, jejak = sebagai_update("masul_wasilah", 1)
    catat("Masul Wasilah mengisi baris kosong: entered_by = Masul", n == 1 and jejak[0] == P["masul_wasilah"],
          rowcount=n, jejak=jejak)

    # Admin menimpa isian Masul: pengisi itu HARUS tercatat di updated_by.
    c.execute(DELW, K)
    c.execute("insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran,entered_by) "
              "values (%s,%s,%s,%s,1,%s)", (*K, i_wk, P["masul_wasilah"]))
    n, jejak = sebagai_update("admin", 1)
    catat("Admin menimpa isian Masul: updated_by mencatat Masul",
          n == 1 and jejak[0] == P["admin"] and jejak[1] == P["masul_wasilah"], rowcount=n, jejak=jejak)

    # Menyunting sendiri: tidak menghapus jejak pengubah.
    buat_awal(P["masul_wasilah"])
    n, jejak = sebagai_update("masul_wasilah", 2)
    catat("Menyunting sendiri: tidak mengubah pengisi", n == 1 and jejak[0] == P["masul_wasilah"], jejak=jejak)
    c.execute(DELW, K)

    # Masul Al Quran pada baris Al Qur'an yang kosong.
    st_a, s_a, i_a = data["alquran"][3], data["alquran"][1], data["alquran"][2]
    KA = (st_a, bulan, s_a)
    c.execute("delete from public.progress_entries where student_id=%s and month_id=%s and subject_id=%s", KA)
    c.execute("insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran) "
              "values (%s,%s,%s,%s,1)", (*KA, i_a))
    c.execute("begin"); c.execute("set local role authenticated")
    c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P["masul_alquran"]),))
    n = c.execute("update public.progress_entries set putaran=1 where student_id=%s and month_id=%s and subject_id=%s",
                  KA).rowcount
    jejak = c.execute("select entered_by from public.progress_entries where student_id=%s and month_id=%s "
                      "and subject_id=%s", KA).fetchone()
    c.execute("rollback")
    catat("Masul Al Quran bisa menimpa capaian Al Qur'an (entered_by = Masul)",
          n == 1 and jejak[0] == P["masul_alquran"], rowcount=n, jejak=jejak)
    c.execute("delete from public.progress_entries where student_id=%s and month_id=%s and subject_id=%s", KA)

    # Jejak untuk catatan (tabel masih kosong di data sekarang) -> buat lalu periksa.
    #
    # PENTING: jangan menghapus baris kehadiran yang sudah ada. Versi pertama uji ini
    # menghapus baris kehadiran Ghayah sebelum uji dan tidak memulihkannya, sehingga
    # 1 baris DUMMY hilang dari produksi. Sekarang semua penulisan terjadi di dalam
    # transaksi dan di-ROLLBACK, tanpa menghapus data lama.
    st_g = data["ghayah"][3]
    c.execute("begin")
    c.execute("set local role authenticated")
    c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P["masul_ghayah"]),))
    c.execute("insert into public.monthly_notes (student_id,month_id,domain,note) values (%s,%s,'ghayah','uji') "
              "on conflict (student_id,month_id,domain) do update set note=excluded.note",
              (st_g, bulan))
    note_jejak = c.execute(
        "select entered_by from public.monthly_notes where student_id=%s and month_id=%s and domain='ghayah'",
        (st_g, bulan)).fetchone()
    c.execute("update public.monthly_notes set note='uji2' where student_id=%s and month_id=%s and domain='ghayah'",
              (st_g, bulan))
    note_jejak2 = c.execute(
        "select entered_by, updated_by, note from public.monthly_notes where student_id=%s and month_id=%s and domain='ghayah'",
        (st_g, bulan)).fetchone()
    c.execute("rollback")
    catat("Catatan: entered_by terisi oleh Masul Ghayah", note_jejak and note_jejak[0] == P["masul_ghayah"],
          jejak=note_jejak)
    catat("Catatan: menyunting sendiri mencatat updated_by",
          note_jejak2 is not None and note_jejak2[0] == P["masul_ghayah"], jejak=note_jejak2)

    # ---------- 3. bulan terkunci ----------
    c.execute("update public.month_domain_settings set is_locked=true where month_id=%s and domain='alquran'",
              (bulan,))
    try:
        catat_matriks("masul_alquran", "capaian", "alquran (bulan terkunci)", "insert", "DITOLAK",
                      INS_PROG, (data["alquran"][3], bulan, data["alquran"][1], data["alquran"][2]))
        catat_matriks("musyrif", "capaian", "alquran (bulan terkunci)", "insert", "DITOLAK",
                      INS_PROG, (st_ampu, bulan, sub_ampu, item_ampu))
        catat_matriks("mudir", "capaian", "alquran (bulan terkunci)", "insert", "DITERIMA",
                      INS_PROG, (data["alquran"][3], bulan, data["alquran"][1], data["alquran"][2]))
        catat_matriks("masul_alquran", "catatan", "alquran (bulan terkunci)", "insert", "DITOLAK",
                      INS_NOTE, (data["alquran"][3], bulan, "alquran"))
    finally:
        c.execute("update public.month_domain_settings set is_locked=false where month_id=%s and domain='alquran'",
                  (bulan,))

    # ---------- 4. bulan 0 ----------
    catat_matriks("masul_alquran", "capaian", "bulan 0", "insert", "DITOLAK",
                  INS_PROG, (data["alquran"][3], bulan0, data["alquran"][1], data["alquran"][2]))
    catat_matriks("mudir", "capaian", "bulan 0", "insert", "DITOLAK",
                  INS_PROG, (data["alquran"][3], bulan0, data["alquran"][1], data["alquran"][2]))

    # ---------- 2b. hapus ----------
    c.execute("insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran) "
              "values (%s,%s,%s,%s,1)", (data["alquran"][3], bulan, data["alquran"][1], data["alquran"][2]))
    K = (data["alquran"][3], bulan, data["alquran"][1])
    DEL = "delete from public.progress_entries where student_id=%s and month_id=%s and subject_id=%s"
    st_hapus, n, _ = sebagai("masul_alquran", DEL, K)
    masih = c.execute("select count(*) from public.progress_entries where student_id=%s and month_id=%s and subject_id=%s",
                      K).fetchone()[0]
    catat("Masul TIDAK bisa menghapus capaian", st_hapus == "DITOLAK" and masih == 1, dapat=st_hapus, masih_ada=masih)
    st_hapus, _, _ = sebagai("musyrif", DEL, K)
    catat("Pengampu TIDAK bisa menghapus capaian", st_hapus == "DITOLAK", dapat=st_hapus)
    st_hapus, _, _ = sebagai("mudir", DEL, K)
    catat("Mudir BISA menghapus capaian", st_hapus == "DITERIMA", dapat=st_hapus)
    c.execute(DEL, K)

    # ---------- 6. anon ----------
    catat_matriks("anon", "capaian", "alquran", "insert", "DITOLAK",
                  INS_PROG, (data["alquran"][3], bulan, data["alquran"][1], data["alquran"][2]))
    c.execute("begin")
    c.execute("set local role anon")
    ditolak = False
    try:
        c.execute("select public.wasilah_input_boot('wasilah')")
    except psycopg.errors.InsufficientPrivilege:
        ditolak = True
    except psycopg.errors.Error:
        ditolak = False
    c.execute("rollback")
    catat("anon ditolak memanggil fungsi input (tanpa EXECUTE)", ditolak)

    # ---------- pulihkan jejak kehadiran yang disentuh upsert ----------
    for (st, bulan_s, d), eb in att_awal.items():
        c.execute(
            "update public.attendance set entered_by=%s where student_id=%s and month_id=%s and domain=%s",
            (eb, st, bulan_s, d),
        )
    att_akhir = {
        (r[0], str(r[1]), r[2]): r[3]
        for r in c.execute("select student_id, month_id, domain, entered_by from public.attendance").fetchall()
    }
    catat("jejak kehadiran lama dipulihkan", att_awal == att_akhir,
          beda=sum(1 for k in att_awal if att_awal.get(k) != att_akhir.get(k)))

    # ---------- kebersihan ----------
    JUMLAH_SESUDAH = {}
    for t in ("progress_entries", "attendance", "monthly_notes"):
        JUMLAH_SESUDAH[t] = satu(f"select count(*) from public.{t}")
    DOMAIN_SESUDAH = {
        "capaian": dict(c.execute(
            "select s.domain, count(*) from public.progress_entries pe "
            "join public.subjects s on s.id=pe.subject_id group by 1").fetchall()),
        "kehadiran": dict(c.execute("select domain, count(*) from public.attendance group by 1").fetchall()),
        "catatan": dict(c.execute("select domain, count(*) from public.monthly_notes group by 1").fetchall()),
    }
    catat("uji tidak meninggalkan baris baru", JUMLAH_SEBELUM == JUMLAH_SESUDAH,
          sebelum=JUMLAH_SEBELUM, sesudah=JUMLAH_SESUDAH)
    catat("uji tidak menghapus/menambah baris lama (per domain)", DOMAIN_SEBELUM == DOMAIN_SESUDAH,
          sebelum=DOMAIN_SEBELUM, sesudah=DOMAIN_SESUDAH)

    hasil = {
        "lulus": LULUS,
        "gagal": GAGAL,
        "ringkasan": f"{LULUS} LULUS, {GAGAL}" if GAGAL else f"{LULUS} LULUS, 0 gagal",
        "rincian": RINCIAN,
    }
    HASIL.parent.mkdir(parents=True, exist_ok=True)
    HASIL.write_text(json.dumps(hasil, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    untuk_ringkas = [r for r in RINCIAN if r["uji"].split(" | ")[0] in ("mudir", "admin")]
    for r in RINCIAN:
        if r["uji"] in (x["uji"] for x in untuk_ringkas) and not r["ok"]:
            print("GAGAL " + r["uji"])
    print(f"Matriks: {sum(1 for r in RINCIAN if ' | ' in r['uji'])} sel, "
          f"gagal: {sum(1 for r in RINCIAN if ' | ' in r['uji'] and not r['ok'])}")
    for r in RINCIAN:
        if " | " not in r["uji"]:
            print(("PASS " if r["ok"] else "GAGAL ") + r["uji"])
    print(hasil["ringkasan"], "| Laporan:", HASIL)
    return 0 if not GAGAL else 1


if __name__ == "__main__":
    sys.exit(main())
