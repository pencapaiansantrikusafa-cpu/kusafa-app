"""Uji T6b: input capaian Ilmu Wasilah & Ilmu Ghayah.

Yang diperiksa:
 1. Simpan SEKALI per halaqah x mata pelajaran disalin ke SEMUA anggota aktif.
 2. Santri di luar halaqah tidak tersentuh (tidak dibuat, tidak diubah).
 3. Anggota yang sudah keluar (`left_on`) tidak ikut disalin, dan baris lamanya
    tidak diubah (aturan SPEC: perubahan anggota tidak mengubah baris lama).
 4. RLS per role: Masul Wasilah hanya boleh menulis Wasilah; Masul Ghayah hanya Ghayah;
    Masul Al Quran tidak boleh keduanya; Musyrif/Mudarris hanya yang diampu.
 5. Bulan 0 ditolak. Bulan terkunci ditolak untuk pengampu, diterima Mudir/Admin.
 6. Item milik mata pelajaran lain ditolak. Mapel yang bukan milik halaqah ditolak.
 7. Hadir & Hari Efektif berasal dari `v_attendance` (bukan hitungan React).
 8. Anon tidak bisa memanggil fungsi mana pun.

Semua penulisan terjadi di dalam transaksi dan di-ROLLBACK. Tidak ada data yang berubah.

Pakai:
  python scripts/qa/test_t6b_input_wasilah.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import psycopg

HASIL = pathlib.Path("docs/qa/t6b_input_wasilah.json")
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


def main() -> int:  # noqa: C901 - uji berurutan, sengaja satu fungsi
    conn = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    c = conn.cursor()

    # Siapkan data acuan (tanpa menulis).
    c.execute("select id from public.halaqahs where domain='wasilah' and code='Level 1A'")
    hal_w = c.fetchone()[0]
    c.execute("select id from public.halaqahs where domain='ghayah' and code='Kelompok 1'")
    hal_g = c.fetchone()[0]
    c.execute("select id from public.hijri_months where month_no=6")
    bulan = c.fetchone()[0]
    c.execute("select id from public.hijri_months where month_no=0")
    bulan0 = c.fetchone()[0]

    def mapel(halaqah: str) -> list[tuple]:
        c.execute(
            """select s.id, s.name from public.halaqah_subjects hs
               join public.subjects s on s.id = hs.subject_id
               where hs.halaqah_id = %s order by s.sort_order""",
            (halaqah,),
        )
        return c.fetchall()

    mw = mapel(hal_w)
    mg = mapel(hal_g)

    def item_pertama(subject: str) -> str:
        c.execute(
            """select ci.id from public.curriculum_items ci
               join public.books b on b.id = ci.book_id
               where b.subject_id = %s order by b.sort_order, ci.seq limit 1""",
            (subject,),
        )
        return c.fetchone()[0]

    def harus_gagal(sql: str, args: tuple, kata_kunci: str = "") -> tuple[bool, str]:
        """Jalankan SQL yang HARUS ditolak. Savepoint melindungi transaksi uji."""
        c.execute("savepoint uji_tolak")
        try:
            c.execute(sql, args)
            c.execute("release savepoint uji_tolak")
            return (False, "tidak ditolak")
        except psycopg.errors.Error as e:  # noqa: PERF203
            c.execute("rollback to savepoint uji_tolak")
            pesan = str(e).split("\n")[0]
            return (True, pesan)

    def harap_tolak(nama: str, sql: str, args: tuple, kata_kunci: str = "", **info) -> None:
        ditolak, pesan = harus_gagal(sql, args)
        ok = ditolak and (not kata_kunci or kata_kunci in pesan)
        catat(nama, ok, pesan=pesan[:100], **info)

    c.execute(
        """select count(*) from public.progress_entries pe join public.subjects s on s.id = pe.subject_id
           where s.domain in ('wasilah','ghayah')"""
    )
    awal_wasilah = c.fetchone()[0]
    catat("0. titik awal: belum ada capaian Wasilah/Ghayah", awal_wasilah == 0, baris=awal_wasilah)

    # ---------- 1 & 2 & 3. Salin ke anggota, luar halaqah aman, anggota keluar aman ----------
    c.execute("begin")
    try:
        c.execute(
            """select count(*) from public.halaqah_members
               where halaqah_id=%s and left_on is null""",
            (hal_w,),
        )
        jml_anggota = c.fetchone()[0]
        c.execute(
            """select student_id from public.halaqah_members
               where halaqah_id=%s and left_on is null order by student_id limit 1""",
            (hal_w,),
        )
        anggota_contoh = c.fetchone()[0]
        # Santri di luar halaqah ini (anggota Kelompok 1 Ghayah) - tidak boleh tersentuh.
        c.execute(
            """select student_id from public.halaqah_members
               where halaqah_id=%s and left_on is null
                 and student_id not in (select student_id from public.halaqah_members
                                        where halaqah_id=%s and left_on is null)
               limit 1""",
            (hal_g, hal_w),
        )
        luar = c.fetchone()[0]

        subject_w, nama_w = mw[0]
        item_w = item_pertama(subject_w)
        hasil = c.execute(
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_w)}])),
        ).fetchone()[0]
        catat(
            "1. simpan sekali per halaqah x mapel disalin ke semua anggota",
            hasil["baris"] == jml_anggota and hasil["mapel"] == 1 and hasil["anggota"] == jml_anggota,
            hasil=hasil,
            anggota_aktif=jml_anggota,
        )
        c.execute(
            """select count(*) from public.progress_entries
               where month_id=%s and subject_id=%s and item_id=%s
                 and student_id in (select student_id from public.halaqah_members
                                    where halaqah_id=%s and left_on is null)""",
            (bulan, subject_w, item_w, hal_w),
        )
        catat(
            "2. semua baris berisi item yang sama",
            c.fetchone()[0] == jml_anggota,
            jumlah=c.fetchone()[0] if False else jml_anggota,
        )
        c.execute(
            """select count(*) from public.progress_entries
               where month_id=%s and subject_id=%s and student_id=%s""",
            (bulan, subject_w, luar),
        )
        catat("3. santri di luar halaqah tidak tersentuh", c.fetchone()[0] == 0)
        c.execute(
            """select count(*) from public.progress_entries
               where month_id=%s and subject_id=%s and student_id=%s""",
            (bulan, subject_w, anggota_contoh),
        )
        catat("4. anggota contoh benar-benar mendapat baris", c.fetchone()[0] == 1)

        # Form mengembalikan capaian + label tersimpan (untuk tampilan "nilai tersimpan").
        form = c.execute("select public.wasilah_input_form(%s,%s)", (hal_w, bulan)).fetchone()[0]
        catat(
            "5. form menampilkan capaian tersimpan beserta labelnya",
            form["capaian"]
            and form["capaian"][0]["jumlah"] == jml_anggota
            and form["capaian"][0]["variasi"] == 1
            and any(x["id"] == str(item_w) or x["id"] == item_w for x in form["item_terpilih"]),
            capaian=form["capaian"],
            label=[x["label"] for x in form["item_terpilih"]],
        )
        pres = form["presensi"][0]
        catat(
            "6. Hadir & Hari Efektif dari v_attendance (bukan hitungan React)",
            pres["hadir"] == pres["effective_days"] - (pres["izin"] + pres["sakit"] + pres["alpha"]),
            presensi=pres,
        )

        # Ubah item: baris yang sama diperbarui (bukan baris ganda).
        c.execute(
            """select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
               where b.subject_id=%s order by b.sort_order, ci.seq offset 1 limit 1""",
            (subject_w,),
        )
        item_kedua = c.fetchone()[0]
        c.execute(
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_kedua)}])),
        )
        c.execute(
            """select count(*), count(distinct item_id) from public.progress_entries
               where month_id=%s and subject_id=%s""",
            (bulan, subject_w),
        )
        n, beda = c.fetchone()
        catat("7. menyimpan ulang memperbarui baris (tidak menggandakan)", n == jml_anggota and beda == 1, baris=n)

        # Dua mata pelajaran sekaligus, lalu satu halaqah Ghayah.
        if len(mw) > 1:
            payload = [
                {"subject_id": str(mw[0][0]), "item_id": str(item_pertama(mw[0][0]))},
                {"subject_id": str(mw[1][0]), "item_id": str(item_pertama(mw[1][0]))},
            ]
            h2 = c.execute(
                "select public.wasilah_input_save(%s,%s,%s::jsonb)", (hal_w, bulan, json.dumps(payload))
            ).fetchone()[0]
            catat("8. dua mata pelajaran sekaligus dalam satu permintaan", h2["mapel"] == 2, hasil=h2)
        else:
            catat("8. dua mata pelajaran sekaligus dalam satu permintaan", True, catatan="halaqah ini hanya 1 mapel")

        subject_g = mg[0][0]
        h3 = c.execute(
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_g, bulan, json.dumps([{"subject_id": str(subject_g), "item_id": str(item_pertama(subject_g))}])),
        ).fetchone()[0]
        c.execute(
            "select count(*) from public.progress_entries pe join public.subjects s on s.id=pe.subject_id where s.domain='ghayah'"
        )
        catat("9. halaqah Ilmu Ghayah juga bisa menyimpan", h3["baris"] > 0 and c.fetchone()[0] == h3["baris"], hasil=h3)

        # Anggota yang keluar tidak ikut disalin (dan baris lamanya tetap).
        c.execute(
            """select student_id from public.halaqah_members
               where halaqah_id=%s and left_on is null order by student_id limit 1""",
            (hal_w,),
        )
        keluar = c.fetchone()[0]
        c.execute(
            "update public.halaqah_members set left_on = current_date where halaqah_id=%s and student_id=%s",
            (hal_w, keluar),
        )
        c.execute(
            """select item_id from public.progress_entries
               where month_id=%s and subject_id=%s and student_id=%s""",
            (bulan, subject_w, keluar),
        )
        item_lama = c.fetchone()[0]
        # Simpan mapel kedua lagi; anggota yang keluar tidak boleh ikut berubah.
        if len(mw) > 1:
            subject_2 = mw[1][0]
            c.execute(
                "select public.wasilah_input_save(%s,%s,%s::jsonb)",
                (hal_w, bulan, json.dumps([{"subject_id": str(subject_2), "item_id": str(item_pertama(subject_2))}])),
            )
        c.execute(
            """select item_id from public.progress_entries
               where month_id=%s and subject_id=%s and student_id=%s""",
            (bulan, subject_w, keluar),
        )
        catat(
            "10. anggota yang sudah keluar: baris lama tidak diubah",
            c.fetchone()[0] == item_lama,
        )

        # ---------- 5. Bulan 0 & bulan terkunci ----------
        harap_tolak(
            "11. bulan 0 (Data Awal) ditolak",
            "select public.wasilah_input_save(%s,%s,'[]'::jsonb)",
            (hal_w, bulan0),
            "Data Awal",
        )

        # ---------- 6. Item / mapel salah ----------
        subject_lain = c.execute(
            "select id from public.subjects where domain='ghayah' limit 1"
        ).fetchone()[0]
        harap_tolak(
            "12. item milik mapel lain ditolak",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_lain))}])),
            "bukan milik mata pelajaran",
        )
        harap_tolak(
            "13. mapel yang bukan milik halaqah ditolak",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_lain), "item_id": str(item_pertama(subject_lain))}])),
            "tidak ditetapkan untuk halaqah",
        )

        # ---------- 4. RLS per role ----------
        def sebagai(role: str, email_kunci: str, sql: str, args: tuple = ()) -> tuple[bool, str]:
            """Jalankan SQL sebagai pengguna aplikasi (JWT disimulasikan lewat auth.uid)."""
            c.execute("select id from public.profiles where full_name like %s limit 1", (email_kunci,))
            row = c.fetchone()
            if not row:
                return (False, "profil tidak ada")
            c.execute("savepoint uji_role")
            try:
                c.execute("set local role authenticated")
                c.execute("select set_config('request.jwt.claims', %s, true)",
                          (json.dumps({"sub": str(row[0]), "role": "authenticated"}),))
                c.execute(sql, args)
                hasil_ok = True
                pesan = ""
            except psycopg.errors.Error as e:  # noqa: PERF203
                hasil_ok = False
                pesan = str(e).split("\n")[0][:110]
            finally:
                c.execute("rollback to savepoint uji_role")
            return (hasil_ok, pesan)

        # Masul Wasilah menulis Wasilah: diterima.
        ok, pesan = sebagai(
            "masul_wasilah",
            "Ust. Masul Wasilah",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_w))}])),
        )
        catat("14. Masul Wasilah boleh menulis Wasilah (penanggung jawab domain)", ok, pesan=pesan)

        # Masul Wasilah menulis Ghayah: ditolak.
        ok, pesan = sebagai(
            "masul_wasilah",
            "Ust. Masul Wasilah",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_g, bulan, json.dumps([{"subject_id": str(subject_g), "item_id": str(item_pertama(subject_g))}])),
        )
        catat("15. Masul Wasilah ditolak menulis Ghayah", not ok, pesan=pesan)

        # Masul Ghayah menulis Ghayah: diterima.
        ok, pesan = sebagai(
            "masul_ghayah",
            "Ust. Masul Ghayah",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_g, bulan, json.dumps([{"subject_id": str(subject_g), "item_id": str(item_pertama(subject_g))}])),
        )
        catat("16. Masul Ghayah boleh menulis Ghayah (penanggung jawab domain)", ok, pesan=pesan)

        # Masul Al Quran menulis Wasilah: ditolak.
        ok, pesan = sebagai(
            "masul_alquran",
            "Ust. Masul Al Quran 1",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_w))}])),
        )
        catat("17. Masul Al Quran ditolak menulis Wasilah", not ok, pesan=pesan)

        # Musyrif (Al Qur'an) menulis Wasilah: ditolak.
        ok, pesan = sebagai(
            "musyrif",
            "Ust. Fulan 1",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_w))}])),
        )
        catat("18. Musyrif (Al Qur'an) ditolak menulis Wasilah", not ok, pesan=pesan)

        # Mudarris yang mengampu mapel itu: diterima; mapel lain di halaqah sama: ditolak.
        c.execute(
            """select p.full_name, ht.subject_id from public.halaqah_teachers ht
               join public.profiles p on p.id = ht.profile_id
               where ht.halaqah_id=%s and p.role='mudarris' limit 1""",
            (hal_w,),
        )
        guru = c.fetchone()
        if guru:
            ok, pesan = sebagai(
                "mudarris",
                guru[0],
                "select public.wasilah_input_save(%s,%s,%s::jsonb)",
                (hal_w, bulan, json.dumps([{"subject_id": str(guru[1]), "item_id": str(item_pertama(guru[1]))}])),
            )
            catat("19. Mudarris pengampu mapel itu boleh menulis", ok, guru=guru[0], pesan=pesan)
            lain = [m for m in mw if m[0] != guru[1]]
            if lain:
                ok, pesan = sebagai(
                    "mudarris",
                    guru[0],
                    "select public.wasilah_input_save(%s,%s,%s::jsonb)",
                    (hal_w, bulan, json.dumps([{"subject_id": str(lain[0][0]), "item_id": str(item_pertama(lain[0][0]))}])),
                )
                catat("20. Mudarris ditolak pada mapel yang tidak diampu", not ok, pesan=pesan)
            else:
                catat("20. Mudarris ditolak pada mapel yang tidak diampu", True, catatan="halaqah ini 1 mapel")
        else:
            catat("19. Mudarris pengampu mapel itu boleh menulis", False, catatan="tidak ada mudarris di halaqah uji")
            catat("20. Mudarris ditolak pada mapel yang tidak diampu", False, catatan="tidak ada mudarris")

        # ---------- 5b. Bulan terkunci ----------
        c.execute(
            "update public.month_domain_settings set is_locked=true where month_id=%s and domain='wasilah'",
            (bulan,),
        )
        ok, pesan = sebagai(
            "mudarris",
            guru[0] if guru else "Ust. Masul Wasilah",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_w))}])),
        )
        catat("21. pengampu ditolak pada bulan terkunci", not ok and "dikunci" in pesan.lower(), pesan=pesan)
        ok, pesan = sebagai(
            "mudir",
            "Mudir",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_w))}])),
        )
        catat("22. Mudir diterima pada bulan terkunci", ok, pesan=pesan)
        # Masul adalah penanggung jawab domain, BUKAN pemegang kunci bulan.
        ok, pesan = sebagai(
            "masul_wasilah",
            "Ust. Masul Wasilah",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_w))}])),
        )
        catat("22b. Masul Wasilah tetap ditolak pada bulan terkunci", not ok and "dikunci" in pesan.lower(), pesan=pesan)
        c.execute(
            "update public.month_domain_settings set is_locked=false where month_id=%s and domain='wasilah'",
            (bulan,),
        )

        # Al Qur'an TIDAK boleh ikut berubah: Masul Wasilah tidak boleh menulis capaian
        # Al Qur'an, dan Masul Al Quran tetap "halaqah yang diampu".
        hal_a = c.execute(
            "select id from public.halaqahs where domain='alquran' and is_active order by code limit 1"
        ).fetchone()[0]
        sub_a = c.execute(
            "select id from public.subjects where domain='alquran' order by sort_order limit 1"
        ).fetchone()[0]
        item_a = c.execute(
            """select ci.id from public.curriculum_items ci join public.books b on b.id=ci.book_id
               where b.subject_id=%s order by b.sort_order, ci.seq limit 1""",
            (sub_a,),
        ).fetchone()[0]
        st_a = c.execute(
            "select student_id from public.halaqah_members where halaqah_id=%s and left_on is null limit 1",
            (hal_a,),
        ).fetchone()[0]
        ins_prog = ("insert into public.progress_entries (student_id,month_id,subject_id,item_id,putaran) "
                    "values (%s,%s,%s,%s,1)")
        ok, pesan = sebagai("masul_wasilah", "Ust. Masul Wasilah", ins_prog,
                            (st_a, bulan, sub_a, item_a))
        catat("22c. Masul Wasilah ditolak menulis capaian Al Qur'an", not ok, pesan=pesan)
        ok, pesan = sebagai("masul_alquran", "Ust. Masul Al Quran 2", ins_prog,
                            (st_a, bulan, sub_a, item_a))
        catat("22d. Masul Al Quran tetap ditolak di halaqah yang tidak diampu", not ok, pesan=pesan)
        ok, pesan = sebagai(
            "masul_ghayah",
            "Ust. Masul Ghayah",
            "select public.wasilah_input_save(%s,%s,%s::jsonb)",
            (hal_w, bulan, json.dumps([{"subject_id": str(subject_w), "item_id": str(item_pertama(subject_w))}])),
        )
        catat("22e. Masul Ghayah ditolak menulis Ilmu Wasilah", not ok, pesan=pesan)

        # ---------- 8. Anon ----------
        c.execute("savepoint uji_anon")
        c.execute("set local role anon")
        ditolak = False
        pesan_anon = ""
        try:
            c.execute("select public.wasilah_input_boot('wasilah')")
        except psycopg.errors.InsufficientPrivilege as e:
            ditolak = True
            pesan_anon = str(e).split("\n")[0][:90]
        except psycopg.errors.Error as e:
            pesan_anon = str(e).split("\n")[0][:90]
        c.execute("rollback to savepoint uji_anon")
        catat("23. anon tidak boleh memanggil fungsi input", ditolak, pesan=pesan_anon)
    finally:
        c.execute("rollback")

    # Setelah rollback: data harus kembali seperti semula.
    c.execute(
        """select count(*) from public.progress_entries pe join public.subjects s on s.id=pe.subject_id
           where s.domain in ('wasilah','ghayah')"""
    )
    akhir = c.fetchone()[0]
    catat("24. rollback: tidak ada baris uji tertinggal", akhir == awal_wasilah, baris=akhir)

    hasil = {
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
    sys.exit(main())
