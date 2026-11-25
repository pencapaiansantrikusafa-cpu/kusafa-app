-- ============================================================================
-- T6d2 (koreksi): trigger jejak tidak boleh menyentuh baris bila tidak ada pengguna.
--
-- Temuan uji sesudah migrasi 20261125000017:
--   Trigger `catat_jejak` memakai `if new.entered_by is distinct from v_uid then`
--   untuk mendeteksi "menimpa isian lama". Ketika koneksi TANPA JWT (seed, skrip
--   service_role), `auth.uid()` = NULL dan `new.entered_by` (kosong) juga NULL,
--   sehingga perbandingan `null is distinct from null` bernilai FALSE dan trigger
--   MELANJUTKAN ke cabang update: `entered_by`/`entered_at` baris seed DITIMPA
--   menjadi NULL / now(). Itu merusak jejak asli seed dan membuat waktu masuk
--   semua baris terlihat "baru".
--
-- Perbaikan (migrasi ini mengganti fungsi `catat_jejak`):
--   - Bila `auth.uid()` NULL (seed, skrip admin tanpa JWT): trigger TIDAK mengubah
--     apa pun selain mengisi `entered_at`/`entered_by` pada INSERT bila memang
--     dikirim. Baris yang ada dibiarkan persis seperti semula.
--   - Bila ada pengguna:
--       INSERT : entered_by kosong -> auth.uid(); entered_at ??= now().
--       UPDATE : bila entered_by tidak berubah -> bila pengubah berbeda dari
--                pengisi, pengubah dicatat di updated_by/updated_at dan
--                entered_by/entered_at menjadi pengubah sekarang
--                (entered_by = "terakhir mengisi", updated_by = "terakhir mengubah").
--
-- Sekaligus memulihkan `entered_at` baris seed yang sempat tertimpa: lihat
-- scripts/db/fixes/2026-11-25_pulihkan_entered_at_seed.sql untuk prosesnya.
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

create or replace function public.catat_jejak() returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_uid uuid := auth.uid();
begin
  -- Tanpa pengguna (seed / skrip tanpa JWT): jangan sentuh jejak yang sudah ada.
  if v_uid is null then
    if tg_op = 'INSERT' then
      if new.entered_at is null then
        new.entered_at := now();
      end if;
    end if;
    return new;
  end if;

  if tg_op = 'INSERT' then
    new.entered_by := coalesce(new.entered_by, v_uid);
    new.entered_at := coalesce(new.entered_at, now());
    return new;
  end if;

  -- UPDATE oleh pengguna: siapa pun yang menyimpan menjadi pengisi terakhir.
  if new.entered_by is distinct from old.entered_by then
    -- Pemanggil mengubah pengisi secara eksplisit: catat pengubahnya saja.
    new.updated_by := v_uid;
    new.updated_at := now();
  elsif old.entered_by is distinct from v_uid then
    -- Orang lain (atau isian seed tanpa pengisi) menimpa: pengisi lama -> jejak ubah,
    -- lalu pengubah sekarang menjadi pengisi terakhir.
    new.updated_by := coalesce(old.entered_by, new.updated_by);
    new.updated_at := coalesce(old.entered_at, now());
    new.entered_by := v_uid;
    new.entered_at := now();
  end if;
  return new;
end $$;

revoke execute on function public.catat_jejak() from public, anon;
grant execute on function public.catat_jejak() to authenticated, service_role;

-- Verifikasi:
--   select pg_get_functiondef('public.catat_jejak()'::regprocedure);
--   -- memuat "if v_uid is null then" di awal (perlindungan koneksi tanpa JWT)
