"""Pulihkan data PERSIS untuk uji yang menulis (T6d3).

Database lokal dan produksi adalah SATU Supabase, jadi uji E2E/smoke yang menulis
WAJIB mengembalikan baris persis: nilai, `entered_by`/`entered_at`, dan
`updated_by`/`updated_at`. Modul ini menyimpan salinan tiga tabel yang boleh ditulis
uji, lalu mengembalikannya (menghapus baris baru, memperbaiki nilai baris lama).

Hanya untuk tabel data uji: `progress_entries`, `attendance`, `monthly_notes`.
Jangan memakai ini untuk "merapikan" data asli. Tabel log `change_log` tidak
disentuh: uji yang menulis akan MENAMBAH baris log (itu bukti, bukan sampah).

Pakai:
    from pulihkan_data import rekam_semua, pulihkan_semua, sama_dengan
    asli = rekam_semua(db)
    ... uji menulis ...
    pulihkan_semua(db, asli)
    catat("dipulihkan", sama_dengan(db, asli))
"""
from __future__ import annotations

# `change_log` sengaja TIDAK dipulihkan: log bersifat append-only, perubahan yang
# dilakukan uji memang harus tercatat. db_fingerprint.py menanganinya terpisah
# ("boleh tumbuh, isi lama utuh").
TABEL = ("progress_entries", "attendance", "monthly_notes")
KUNCI = {
    "progress_entries": ("id",),
    "attendance": ("student_id", "month_id", "domain"),
    "monthly_notes": ("student_id", "month_id", "domain"),
}


def _kolom(db, tabel: str) -> list[str]:
    return [r[0] for r in db.execute(
        "select column_name from information_schema.columns where table_schema='public' "
        "and table_name=%s order by ordinal_position", (tabel,)).fetchall()]


def rekam(db) -> dict:
    """Salinan penuh (semua kolom) ketiga tabel uji, berkunci kunci alami."""
    hasil = {}
    for t in TABEL:
        kol = _kolom(db, t)
        rows = db.execute(f'select {", ".join(kol)} from public.{t}').fetchall()
        isi = {}
        for r in rows:
            k = tuple(str(r[kol.index(x)]) for x in KUNCI[t])
            isi[k] = dict(zip(kol, r))
        hasil[t] = isi
    return hasil


def pulihkan(db, asli: dict) -> None:
    for t in TABEL:
        asli_t = asli.get(t, {})
        kol = _kolom(db, t)
        sekarang = {}
        for r in db.execute(f'select {", ".join(kol)} from public.{t}').fetchall():
            sekarang[tuple(str(r[kol.index(x)]) for x in KUNCI[t])] = dict(zip(kol, r))
        kondisi = " and ".join(f"{x}=%s" for x in KUNCI[t])
        for k in sekarang:
            if k not in asli_t:
                db.execute(f"delete from public.{t} where {kondisi}", tuple(k))
        for k, v in asli_t.items():
            if sekarang.get(k) == v:
                continue
            if k not in sekarang:
                # Baris DIHAPUS uji: masukkan kembali nilai aslinya (bukan dibiarkan hilang).
                db.execute(
                    f"insert into public.{t} ({', '.join(kol)}) values ({', '.join('%s' for _ in kol)})",
                    tuple(v[c] for c in kol),
                )
                continue
            db.execute(
                f"update public.{t} set {', '.join(f'{c}=%s' for c in kol)} where {kondisi}",
                tuple(v[c] for c in kol) + tuple(k),
            )


def sama_dengan(db, asli: dict) -> tuple[bool, dict]:
    beda = {}
    for t in TABEL:
        asli_t = asli.get(t, {})
        kol = _kolom(db, t)
        sekarang = {}
        for r in db.execute(f'select {", ".join(kol)} from public.{t}').fetchall():
            sekarang[tuple(str(r[kol.index(x)]) for x in KUNCI[t])] = dict(zip(kol, r))
        n = sum(1 for k in set(asli_t) | set(sekarang) if asli_t.get(k) != sekarang.get(k))
        if n or len(asli_t) != len(sekarang):
            beda[t] = {"baris_beda": n, "sebelum": len(asli_t), "sesudah": len(sekarang)}
    return (not beda), beda
