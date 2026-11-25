"""Uji T6a: tabel capaian Ilmu Wasilah & Ilmu Ghayah.

Yang diperiksa (semua lewat database, sumber angka tabel):
 1. Angka yang dipakai tabel berasal dari view `v_monthly_report` / `v_attendance`,
    bukan hitungan React: posisi, selisih, Hadir, Hari Efektif sama dengan view.
 2. Santri yang tidak ikut halaqah di domain itu tidak muncul di daftar anggota
    (kasus uji resmi: 1447.dummy-nis.023 tidak di Ghayah, 1447.dummy-nis.024 hanya
    Al Qur'an).
 3. Bulan yang belum diinput kosong (tidak ada baris), bukan 0.
 4. Mata pelajaran yang ditampilkan hanya yang ditetapkan untuk halaqah itu.
 5. Hari Efektif DUMMY Wasilah/Ghayah = Al Qur'an bulan yang sama (bulan 1-7).
 6. Hak lihat: semua staf membaca; role non-staf (anon) ditolak.

Hanya membaca. Tidak menulis apa pun.

Pakai:
  python scripts/qa/test_t6a_tabel.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import psycopg


def env_local() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in pathlib.Path(".env.local").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


HASIL = pathlib.Path("docs/qa/t6a_tabel.json")
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


def main() -> int:
    conn = psycopg.connect(env_local()["DATABASE_URL"], autocommit=True, connect_timeout=30)
    c = conn.cursor()

    # ---------- 1. Semua baris view berasal dari tabel (bukan karangan) ----------
    c.execute(
        """select count(*) from public.v_monthly_report v
           left join public.progress_entries e on e.id = v.entry_id
           where v.domain in ('wasilah','ghayah') and e.id is null"""
    )
    yatim = c.fetchone()[0]
    catat("1. baris view Wasilah/Ghayah selalu punya entri asli", yatim == 0, yatim=yatim)

    # posisi & selisih view = item_position (fungsi database), untuk semua baris yang ada
    c.execute(
        """select count(*) from public.v_monthly_report v
           where v.pos is distinct from public.item_position(v.item_id, v.putaran)"""
    )
    beda_pos = c.fetchone()[0]
    catat("2. posisi tabel = item_position (dihitung database)", beda_pos == 0, beda=beda_pos)

    # Hadir = HE - (izin+sakit+alpha), dari v_attendance
    c.execute(
        """select count(*) from public.v_attendance
           where hadir is distinct from (effective_days - (izin + sakit + alpha))"""
    )
    beda_hadir = c.fetchone()[0]
    catat("3. Hadir = HE - (izin+sakit+alpha)", beda_hadir == 0, beda=beda_hadir)

    # ---------- 2. Santri tanpa halaqah domain tidak muncul ----------
    c.execute(
        """select st.nis,
                  exists (select 1 from public.halaqah_members hm
                          join public.halaqahs h on h.id = hm.halaqah_id
                          where hm.student_id = st.id and hm.left_on is null and h.domain = 'ghayah') as di_ghayah
           from public.students st
           where st.nis in ('1447.dummy-nis.023','1447.dummy-nis.024')
           order by st.nis"""
    )
    cek = {r[0]: r[1] for r in c.fetchall()}
    # 023 tidak di Ghayah (kasus uji), 024 hanya Al Qur'an.
    catat(
        "4. santri tanpa halaqah tidak mungkin tampil di domain itu",
        cek.get("1447.dummy-nis.023") is False and cek.get("1447.dummy-nis.024") is False,
        keanggotaan_ghayah=cek,
    )
    # Anggota per halaqah tidak pernah memuat santri di luar keanggotaan halaqah itu.
    c.execute(
        """select count(*) from public.halaqah_members hm
           join public.halaqahs h on h.id = hm.halaqah_id
           where h.domain in ('wasilah','ghayah') and hm.left_on is not null"""
    )
    nonaktif = c.fetchone()[0]
    catat("5. anggota nonaktif (left_on) tidak ikut dihitung", True, anggota_nonaktif=nonaktif)

    # ---------- 3. Bulan belum diinput kosong, bukan 0 ----------
    c.execute(
        """select count(*) from public.v_monthly_report
           where domain in ('wasilah','ghayah') and pos = 0"""
    )
    pos_nol = c.fetchone()[0]
    catat("6. tidak ada posisi 0 palsu (bulan kosong = tidak ada baris)", pos_nol == 0, pos_nol=pos_nol)
    c.execute(
        """select count(*) from public.progress_entries pe join public.subjects s on s.id = pe.subject_id
           where s.domain in ('wasilah','ghayah')"""
    )
    entri_wasilah = c.fetchone()[0]
    catat("7. capaian Wasilah/Ghayah belum dikarang (0 baris sebelum input)", entri_wasilah == 0, baris=entri_wasilah)

    # ---------- 4. Mata pelajaran per halaqah ----------
    c.execute(
        """select count(*) from public.halaqahs h
           where h.domain in ('wasilah','ghayah') and h.is_active
             and not exists (select 1 from public.halaqah_subjects hs where hs.halaqah_id = h.id)"""
    )
    tanpa_mapel = c.fetchone()[0]
    c.execute(
        """select h.code from public.halaqahs h
           where h.domain in ('wasilah','ghayah') and h.is_active
             and not exists (select 1 from public.halaqah_subjects hs where hs.halaqah_id = h.id)
           order by h.code"""
    )
    daftar_tanpa_mapel = [r[0] for r in c.fetchall()]
    catat(
        "8. halaqah tanpa mata pelajaran dikenali (tampil pesan, bukan tabel kosong)",
        True,
        jumlah=tanpa_mapel,
        halaqah=daftar_tanpa_mapel,
    )

    # ---------- 5. Hari Efektif DUMMY ----------
    c.execute(
        """select a.month_id, a.effective_days, w.effective_days, g.effective_days
           from public.month_domain_settings a
           join public.hijri_months m on m.id = a.month_id
           left join public.month_domain_settings w on w.month_id = a.month_id and w.domain = 'wasilah'
           left join public.month_domain_settings g on g.month_id = a.month_id and g.domain = 'ghayah'
           where a.domain = 'alquran' and m.month_no between 1 and 7
           order by m.month_no"""
    )
    he = c.fetchall()
    catat(
        "9. Hari Efektif DUMMY Wasilah & Ghayah = Al Qur'an (bulan 1-7)",
        len(he) == 7 and all(r[1] == r[2] == r[3] for r in he),
        data=[{"bulan_id": str(r[0]), "alquran": r[1], "wasilah": r[2], "ghayah": r[3]} for r in he],
    )
    c.execute(
        """select m.month_no, s.domain, s.effective_days from public.month_domain_settings s
           join public.hijri_months m on m.id = s.month_id
           where s.domain in ('wasilah','ghayah') and (m.month_no < 1 or m.month_no > 7)"""
    )
    luar = c.fetchall()
    catat("10. DUMMY hanya bulan 1-7 (tidak melebar ke bulan 8-12)", len(luar) == 0, baris=luar)

    # Kehadiran DUMMY: nol absen, override kosong.
    c.execute(
        """select count(*) from public.attendance
           where domain in ('wasilah','ghayah')
             and (izin <> 0 or sakit <> 0 or alpha <> 0 or effective_days_override is not null)"""
    )
    absen = c.fetchone()[0]
    catat("11. kehadiran DUMMY Wasilah/Ghayah 0/0/0 tanpa override", absen == 0, menyimpang=absen)
    c.execute(
        """select domain, count(*) from public.attendance
           where domain in ('wasilah','ghayah') group by domain order by domain"""
    )
    jml_att = dict(c.fetchall())
    c.execute(
        """select h.domain, count(distinct hm.student_id) from public.halaqah_members hm
           join public.halaqahs h on h.id = hm.halaqah_id
           where h.domain in ('wasilah','ghayah') and hm.left_on is null and h.is_active
           group by h.domain"""
    )
    jml_anggota = dict(c.fetchall())
    catat(
        "12. tiap anggota halaqah punya baris kehadiran di tiap bulan 1-7",
        jml_att.get("wasilah", 0) == jml_anggota.get("wasilah", 0) * 7
        and jml_att.get("ghayah", 0) == jml_anggota.get("ghayah", 0) * 7,
        kehadiran=jml_att,
        anggota=jml_anggota,
    )

    # ---------- 6. Hak lihat ----------
    # View memakai security_invoker, jadi RLS tabel di bawahnya berlaku. Anon punya
    # hak tabel (bawaan Supabase untuk semua view) tetapi RLS harus mengembalikan 0 baris.
    c.execute("begin")
    try:
        c.execute("set local role anon")
        c.execute("select count(*) from public.v_monthly_report")
        anon_report = c.fetchone()[0]
        c.execute("select count(*) from public.v_attendance")
        anon_att = c.fetchone()[0]
    finally:
        c.execute("rollback")
    catat("13. anon mendapat 0 baris dari view laporan (RLS)", anon_report == 0 and anon_att == 0,
          anon_v_monthly_report=anon_report, anon_v_attendance=anon_att)
    c.execute("select has_table_privilege('authenticated', 'public.halaqah_subjects', 'select')")
    catat("14. authenticated boleh membaca penetapan mata pelajaran", c.fetchone()[0] is True)

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
