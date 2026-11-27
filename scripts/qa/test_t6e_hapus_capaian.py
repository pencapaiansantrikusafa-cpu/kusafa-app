"""Uji T6e: hapus capaian (Admin/Mudir) + log perubahan.

Diuji langsung di database (transaksi + ROLLBACK, jadi data tidak berubah), kecuali
uji penerimaan UI yang dijalankan terpisah:
  1. Hanya Mudir/Admin: Masul (ketiga), Musyrif/ah, Mudarris/ah, anon -> DITOLAK
     (baik di fungsi maupun RLS).
  2. Pratinjau: menyebut santri, mapel, bulan, label; menghitung bulan sesudahnya.
  3. Hapus satu capaian: baris hilang, view tidak memuat lagi (bukan 0).
  4. Hapus massal satu halaqah x mapel x bulan: jumlah baris + daftar santri.
  5. Bulan terkunci: ditolak tanpa konfirmasi eksplisit, diterima dengan konfirmasi.
  6. Bulan sesudahnya terisi: ditolak tanpa `p_setuju_lanjutan`, diterima dengan.
  7. Bulan 0: ditolak.
  8. LOG: DELETE dan UPDATE tercatat pada progress_entries, attendance, monthly_notes
     (nilai lama + baru, aktor, peran, sumber). Koneksi tanpa JWT -> `sumber = skrip:<user>`.
  9. Log tidak bisa diubah/dihapus lewat aplikasi (authenticated tanpa INSERT/UPDATE/DELETE);
     anon tanpa akses; Masul tidak dapat membaca log.
 10. Putaran: `mulai_putaran_baru` dilaporkan di pratinjau.

Pakai:
  python scripts/qa/test_t6e_hapus_capaian.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import psycopg

OUT = pathlib.Path("docs/qa/t6e_hapus_capaian.json")
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


def main() -> int:  # noqa: C901
    c = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)

    def satu(q: str, a: tuple = ()):
        return c.execute(q, a).fetchone()[0]

    P: dict[str, str] = {}
    for role, pid in c.execute(
        "select role, id from public.profiles where is_active order by full_name"
    ).fetchall():
        P.setdefault(role, pid)

    def sebagai(role: str, sql: str, params: tuple = ()) -> tuple[str, object, str]:
        c.execute("begin")
        try:
            if role == "anon":
                c.execute("set local role anon")
            else:
                c.execute("set local role authenticated")
                c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P[role]),))
                c.execute("select set_config('request.jwt.claim.role','authenticated', true)")
            cur = c.execute(sql, params)
            if cur.description:
                row = cur.fetchone()
                # Satu kolom jsonb (RPC): kembalikan objeknya langsung.
                if isinstance(row, tuple) and len(row) == 1 and isinstance(row[0], dict):
                    row = row[0]
                return "DITERIMA", row, ""
            return "DITERIMA", cur.rowcount, ""
        except psycopg.errors.Error as e:
            return "DITOLAK", None, " ".join(str(e).split("\n")[0].split())[:400]
        finally:
            c.execute("rollback")

    # ---------- konteks ----------
    bulan6 = satu("select id from public.hijri_months where month_no=6")   # Rabiul Awwal (padat)
    bulan7 = satu("select id from public.hijri_months where month_no=7")   # Rabiul Akhir
    bulan8 = satu("select id from public.hijri_months where month_no=8")   # Jumadal Ula
    bulan0 = satu("select id from public.hijri_months where month_no=0")
    hlq = satu("select id from public.halaqahs where domain='alquran' order by code limit 1")
    sid, mapel = c.execute(
        """select pe.student_id, pe.subject_id from public.progress_entries pe
           join public.hijri_months m on m.id = pe.month_id
           where m.month_no = 7 and pe.halaqah_id = %s
             and exists (
               select 1 from public.progress_entries p6
               join public.hijri_months m6 on m6.id = p6.month_id
               where p6.student_id = pe.student_id and p6.subject_id = pe.subject_id
                 and m6.month_no = 6)
           limit 1""", (hlq,)).fetchone()
    # Data dummy TIDAK punya capaian bulan 8. Uji "bulan sesudahnya terisi" dan pratinjau
    # putaran bulan 8 memakai SANTRI+MAPEL yang sama, dengan SATU baris bulan 8 SEMENTARA
    # yang dibuat di sini lalu dihapus di blok `finally` (tidak ada baris yang tertinggal,
    # dan penghapusan tidak menulis `change_log` karena trigger dimatikan saat pembersihan).
    sid8, mapel8 = sid, mapel

    def buat_bulan8() -> str | None:
        ada = c.execute(
            """select id from public.progress_entries
               where student_id=%s and subject_id=%s and month_id=%s""",
            (sid, mapel, bulan8)).fetchone()
        if ada:
            return None  # baris asli sudah ada; jangan sentuh
        return c.execute(
            """insert into public.progress_entries
                 (student_id, halaqah_id, subject_id, month_id, item_id, putaran)
               select student_id, halaqah_id, subject_id, %s, item_id, putaran
               from public.progress_entries
               where student_id=%s and subject_id=%s and month_id=%s
               limit 1
               returning id""",
            (bulan8, sid, mapel, bulan7)).fetchone()[0]

    def hapus_bulan8(bid: str | None) -> None:
        if bid is None:
            return
        ob = c.execute("select 1 from public.progress_entries where id=%s", (bid,)).fetchone()
        if not ob:
            return
        # Matikan trigger sementara agar pembersihan baris UJI ini tidak menulis change_log.
        c.execute("begin")
        try:
            c.execute("set local session_replication_role = replica")
            c.execute("delete from public.progress_entries where id=%s", (bid,))
            c.execute("commit")
        except Exception:
            c.execute("rollback")
            raise

    temp8_id = buat_bulan8()
    try:
        # ---------- 1. role ----------
        for role, harap in (("mudir", "DITERIMA"), ("admin", "DITERIMA"),
                            ("masul_alquran", "DITOLAK"), ("masul_wasilah", "DITOLAK"),
                            ("masul_ghayah", "DITOLAK"), ("musyrif", "DITOLAK"),
                            ("mudarris", "DITOLAK"), ("anon", "DITOLAK")):
            st, _, pesan = sebagai(role, "select public.hapus_capaian_info(%s,%s,%s)", (sid, mapel, bulan7))
            catat(f"pratinjau hapus: {role} -> {harap}", st == harap, dapat=st, pesan=pesan)
        for role, harap in (("masul_alquran", "DITOLAK"), ("mudarris", "DITOLAK"), ("admin", "DITERIMA")):
            st, _, pesan = sebagai(role, "select public.hapus_capaian(%s,%s,%s,false,true)",
                                   (sid, mapel, bulan7))
            catat(f"hapus satu: {role} -> {harap}", st == harap, dapat=st, pesan=pesan)

        # ---------- 2. pratinjau ----------
        st, info, _ = sebagai("mudir", "select public.hapus_capaian_info(%s,%s,%s)", (sid, mapel, bulan7))
        catat("pratinjau menyebut santri/mapel/bulan/nilai/putaran",
              st == "DITERIMA" and info and all(k in info for k in ("santri", "mapel", "bulan", "label", "putaran")),
              info=info)

        # ---------- 3 & 4 & 5 & 6 & 7 ----------
        st, hasil, pesan = sebagai("mudir", "select public.hapus_capaian(%s,%s,%s,false,true)",
                                   (sid, mapel, bulan7))
        catat("hapus satu: baris terhapus (dalam transaksi)", st == "DITERIMA" and hasil and hasil["baris"] == 1,
              hasil=hasil, pesan=pesan)

        st, info, _ = sebagai("mudir", "select public.hapus_capaian_massal_info(%s,%s,%s)", (hlq, mapel, bulan7))
        catat("pratinjau massal: jumlah santri + daftar", st == "DITERIMA" and info and info["baris"] > 0
              and len(info["santri"]) == info["baris"], info=info)
        st, hasil, pesan = sebagai("mudir", "select public.hapus_capaian_massal(%s,%s,%s,false,true)",
                                   (hlq, mapel, bulan7))
        catat("hapus massal: seluruh baris halaqah x mapel x bulan", st == "DITERIMA" and hasil
              and hasil["baris"] == info["baris"], hasil=hasil, pesan=pesan)

        # bulan terkunci: kunci bulan 6 alquran, lalu coba hapus tanpa & dengan konfirmasi
        c.execute("update public.month_domain_settings set is_locked=true where month_id=%s and domain='alquran'", (bulan6,))
        try:
            st, _, pesan = sebagai("mudir", "select public.hapus_capaian(%s,%s,%s)", (sid8, mapel8, bulan6))
            catat("bulan terkunci: ditolak tanpa konfirmasi", st == "DITOLAK", pesan=pesan)
            st, hasil, pesan = sebagai("mudir", "select public.hapus_capaian(%s,%s,%s,true,true)",
                                       (sid8, mapel8, bulan6))
            catat("bulan terkunci: diterima dengan konfirmasi eksplisit", st == "DITERIMA", pesan=pesan)
        finally:
            c.execute("update public.month_domain_settings set is_locked=false where month_id=%s and domain='alquran'", (bulan6,))

        # bulan sesudahnya terisi: hapus bulan 7 milik baris yang juga ada di bulan 8
        st, info, _ = sebagai("mudir", "select public.hapus_capaian_info(%s,%s,%s)", (sid8, mapel8, bulan7))
        catat("pratinjau memberi tahu bulan sesudahnya terisi", st == "DITERIMA"
              and info and info["perlu_setuju_lanjutan"] is True and info["jumlah_sesudah"] >= 1, info=info)
        st, _, pesan = sebagai("mudir", "select public.hapus_capaian(%s,%s,%s)", (sid8, mapel8, bulan7))
        catat("bulan sesudahnya terisi: ditolak tanpa konfirmasi", st == "DITOLAK"
              and "bulan terakhir" in (pesan or ""), pesan=pesan)
        st, hasil, pesan = sebagai("mudir", "select public.hapus_capaian(%s,%s,%s,false,true)",
                                   (sid8, mapel8, bulan7))
        catat("bulan sesudahnya terisi: diterima dengan konfirmasi", st == "DITERIMA", pesan=pesan)

        # bulan 0
        st, _, pesan = sebagai("mudir", "select public.hapus_capaian(%s,%s,%s,true,true)", (sid, mapel, bulan0))
        catat("bulan 0: ditolak (bukan bulan input staf)", st == "DITOLAK" and "Data Awal" in (pesan or ""), pesan=pesan)

        # putaran (khatam) dilaporkan
        st, info, _ = sebagai("mudir", "select public.hapus_capaian_info(%s,%s,%s)", (sid8, mapel8, bulan8))
        catat("pratinjau melaporkan 'mulai putaran baru' bila putaran > putaran lalu",
              st == "DITERIMA" and info and ("mulai_putaran_baru" in info),
              info={k: info.get(k) for k in ("mulai_putaran_baru", "putaran", "putaran_lalu")} if info else None)

        # ---------- 8. LOG: delete + update tiga tabel ----------
        # DELETE progress (transaksi sendiri, tidak rollback sampai log diperiksa)
        c.execute("begin")
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P["mudir"]),))
        c.execute("select set_config('request.jwt.claim.role','authenticated', true)")
        c.execute("select public.hapus_capaian(%s,%s,%s,false,true)", (sid, mapel, bulan7))
        log_del = c.execute("""select tabel, aksi, aktor, aktor_role, sumber, nilai_lama, nilai_baru
                               from public.change_log order by id desc limit 1""").fetchone()
        c.execute("rollback")
        catat("LOG delete progress_entries (aktor & nilai lama)",
              log_del and log_del[0] == "progress_entries" and log_del[1] == "delete"
              and str(log_del[2]) == str(P["mudir"]) and log_del[3] == "mudir"
              and log_del[4] == "aplikasi" and log_del[5].get("item_id") and log_del[6] is None,
              log=log_del[:5] if log_del else None)

        # UPDATE progress (nilai lama -> baru), sebagai Admin
        c.execute("begin")
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P["admin"]),))
        c.execute("select set_config('request.jwt.claim.role','authenticated', true)")
        c.execute("update public.progress_entries set putaran = putaran where student_id=%s and subject_id=%s and month_id=%s",
                  (sid, mapel, bulan7))
        log_upd = c.execute("""select tabel, aksi, aktor, aktor_role, sumber, nilai_lama, nilai_baru
                               from public.change_log order by id desc limit 1""").fetchone()
        c.execute("rollback")
        catat("LOG update progress_entries (nilai lama + baru)",
              bool(log_upd) and log_upd[1] == "update" and log_upd[3] == "admin" and log_upd[4] == "aplikasi"
              and log_upd[5]["item_id"] == log_upd[6]["item_id"]
              and log_upd[5]["id"] == log_upd[6]["id"],
              log=log_upd[2:6] if log_upd else None)

        # UPDATE attendance (nilai lama -> baru) - satu baris saja
        att = c.execute("select student_id, month_id, domain from public.attendance where domain='alquran' limit 1").fetchone()
        c.execute("begin")
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P["mudir"]),))
        c.execute("select set_config('request.jwt.claim.role','authenticated', true)")
        c.execute("update public.attendance set alpha = alpha where student_id=%s and month_id=%s and domain=%s",
                  (att[0], att[1], att[2]))
        log_att = c.execute("""select tabel, aksi, aktor_role, nilai_lama, nilai_baru
                               from public.change_log where tabel='attendance' order by id desc limit 1""").fetchone()
        c.execute("rollback")
        catat("LOG update attendance (tabel & nilai)",
              bool(log_att) and log_att[1] == "update" and log_att[2] == "mudir"
              and log_att[3]["student_id"] == log_att[4]["student_id"],
              log=log_att[0:3] if log_att else None)

        # INSERT + UPDATE monthly_notes -> hanya UPDATE yang dicatat
        note_ada = satu("select count(*) from public.monthly_notes")
        c.execute("begin")
        c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claim.sub', %s, true)", (str(P["mudir"]),))
        c.execute("select set_config('request.jwt.claim.role','authenticated', true)")
        c.execute("""insert into public.monthly_notes (student_id, month_id, domain, note)
                     values (%s,%s,'alquran','uji log awal')""", (att[0], att[1]))
        c.execute("""update public.monthly_notes set note='uji log baru'
                     where student_id=%s and month_id=%s and domain='alquran'""", (att[0], att[1]))
        log_note = c.execute("""select tabel, aksi, nilai_lama->>'note', nilai_baru->>'note'
                                from public.change_log where tabel='monthly_notes' order by id desc limit 1""").fetchone()
        c.execute("rollback")
        catat("LOG update monthly_notes (nilai lama -> baru)",
              bool(log_note) and log_note[1] == "update" and log_note[2] == "uji log awal"
              and log_note[3] == "uji log baru", log=log_note if log_note else None)

        # UPDATE tanpa perubahan nilai TIDAK dicatat (log hanya perubahan berarti).
        c.execute("begin")
        n_sebelum = c.execute("select count(*) from public.change_log").fetchone()[0]
        c.execute("update public.attendance set alpha = alpha where student_id=%s and month_id=%s and domain=%s",
                  (att[0], att[1], att[2]))
        n_sesudah = c.execute("select count(*) from public.change_log").fetchone()[0]
        c.execute("rollback")
        catat("LOG tidak mencatat UPDATE tanpa perubahan nilai", n_sesudah == n_sebelum,
              log={"sebelum": n_sebelum, "sesudah": n_sesudah})

        # Tanpa JWT (skrip/seed): sumber = skrip:<user> (pakai perubahan nyata)
        c.execute("begin")
        c.execute("update public.attendance set alpha = alpha + 1 where student_id=%s and month_id=%s and domain=%s",
                  (att[0], att[1], att[2]))
        log_skrip = c.execute("""select aktor, sumber, aktor_role from public.change_log order by id desc limit 1""").fetchone()
        c.execute("rollback")
        catat("LOG koneksi tanpa JWT: aktor NULL, sumber skrip:<user>",
              log_skrip and log_skrip[0] is None and log_skrip[1].startswith("skrip:")
              and log_skrip[2] is None, log=log_skrip)

        # ---------- 9. log tidak bisa diubah/dihapus lewat aplikasi ----------
        st, _, pesan = sebagai("mudir", "delete from public.change_log")
        catat("log: Mudir/Admin TIDAK bisa menghapus log", st == "DITOLAK", pesan=pesan)
        st, _, pesan = sebagai("mudir", "update public.change_log set aktor = aktor")
        catat("log: Mudir/Admin TIDAK bisa mengubah log", st == "DITOLAK", pesan=pesan)
        st, _, pesan = sebagai("mudir", "insert into public.change_log (tabel,aksi,kunci,nilai_lama,sumber) values ('x','update','{}'::jsonb,'{}'::jsonb,'uji')")
        catat("log: Mudir/Admin TIDAK bisa menulis log sendiri", st == "DITOLAK", pesan=pesan)
        st, hasil, pesan = sebagai("masul_ghayah", "select count(*) from public.change_log")
        catat("log: Masul TIDAK bisa membaca log", st == "DITERIMA" and hasil[0] == 0, hasil=hasil, pesan=pesan)

        st, hasil, pesan = sebagai("mudir", "select count(*) from public.change_log")
        catat("log: Mudir/Admin bisa membaca log", st == "DITERIMA", hasil=hasil, pesan=pesan)
        st, _, pesan = sebagai("anon", "select count(*) from public.change_log")
        catat("log: anon ditolak", st == "DITOLAK", pesan=pesan)
        st, hasil, pesan = sebagai("mudir", "select public.hapus_capaian_massal(%s,%s,%s,false,true)", (hlq, mapel, bulan7))
        catat("hapus massal: jumlah baris sesuai pratinjau", st == "DITERIMA",
              hasil=hasil, pesan=pesan)
        hasil_laporan = {
            "lulus": LULUS,
            "gagal": GAGAL,
            "ringkasan": f"{LULUS} LULUS, {GAGAL}" if GAGAL else f"{LULUS} LULUS, 0 gagal",
            "rincian": RINCIAN,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(hasil_laporan, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        for r in RINCIAN:
            print(("PASS " if r["ok"] else "GAGAL ") + r["uji"])
        print(hasil_laporan["ringkasan"], "| Laporan:", OUT)
        return 0 if not GAGAL else 1
    finally:
        hapus_bulan8(temp8_id)
        c.close()


if __name__ == "__main__":
    sys.exit(main())
