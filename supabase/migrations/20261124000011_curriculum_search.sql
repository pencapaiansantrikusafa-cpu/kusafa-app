-- ============================================================================
-- T5c: pencarian item kurikulum di sisi server (Opsi A, docs/STATUS.md 2c).
--
-- Masalah: halaman Input Al Qur'an memuat SEMUA item domain (9.177 item aktif,
-- 129 permintaan HTTP) sebelum dropdown bisa dipakai, sehingga halaman butuh ~4-7 detik.
--
-- Perbaikan: fungsi `curriculum_items_search` mengembalikan HANYA item yang cocok,
-- dibatasi 60 baris (sama dengan batas tampil dropdown). Halaman tidak lagi
-- mengunduh seluruh daftar; item yang sudah tersimpan diambil terpisah (by id).
--
-- Yang TIDAK berubah: rumus posisi/selisih/putaran/target/Hadir tetap di database
-- (item_position, v_monthly_report, v_attendance). Fungsi ini hanya MEMILIH item,
-- tidak menghitung capaian.
--
-- Keamanan (pola migrasi 000007/000010):
--   - SECURITY INVOKER + `set search_path`; RLS `items_read` (is_staff) tetap berlaku.
--   - Diperiksa juga `public.is_staff()` secara eksplisit; pengguna tanpa profil (JWT
--     tanpa baris profiles) dan anon tidak mendapat baris.
--   - EXECUTE dicabut dari anon/PUBLIC, hanya authenticated + service_role.
--
-- Skor urutan SAMA dengan DropdownCari versi klien:
--   0 nomor persis di ujung label, 2 diawali kata kunci, 3 awal kata, 4 mengandung.
-- Label selalu berawalan nama bidang ("Tahfidz · An Naba' - 40").
-- ============================================================================

-- (Tidak memakai begin/commit eksplisit: Supabase CLI membungkus tiap migrasi.)

-- pg_trgm dipasang di skema terpisah `extensions` (seperti yang disarankan Supabase untuk
-- ekstensi). Bila dipasang di `public`, ±31 fungsi bantuan ekstensi ikut muncul di public
-- dan terbuka ke anon (pemiliknya supabase_admin, sehingga tidak bisa dicabut oleh kita).
create schema if not exists extensions;
create extension if not exists pg_trgm with schema extensions;
grant usage on schema extensions to authenticated, service_role;

-- Indeks bantu pencarian teks label (dipakai ILIKE '%...%').
create index if not exists curriculum_items_label_trgm
  on public.curriculum_items using gin (label extensions.gin_trgm_ops);

create or replace function public.curriculum_items_search(
  p_subject uuid,
  p_q text default '',
  p_limit integer default 60
)
returns table (
  id uuid,
  subject_id uuid,
  label text,
  value numeric,
  siklik boolean
)
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  with izin as (
    -- Pengguna aplikasi: harus staf (lewat profil). Koneksi admin/skrip lokal tanpa JWT
    -- (postgres/service_role/supabase_admin) diizinkan, pola sama dengan migrasi 000009.
    select public.is_staff()
           or (public.current_app_role() is null
               and session_user in ('postgres', 'service_role', 'supabase_admin')) as boleh
  ),
  kunci as (
    select lower(trim(coalesce(p_q, ''))) as k
  ),
  kata as (
    -- Kata kunci dipecah seperti versi klien; setiap kata harus cocok (DAN).
    select unnest(regexp_split_to_array((select k from kunci), '\s+')) as w
    where (select k from kunci) <> ''
  ),
  kandidat_buku as (
    -- Tidak dipakai untuk memfilter: kata kunci bisa ada di LABEL item (mis. "Quraisy"),
    -- bukan di judul buku. Disediakan untuk indeks trigram judul buku bila diperlukan nanti.
    select b.id from public.books b where b.subject_id = p_subject and b.is_active
  ),
  dasar as (
    select ci.id,
           ci.value,
           b.subject_id,
           b.is_cyclic,
           b.stage_order,
           b.sort_order,
           ci.seq,
           s.name || ' · ' || ci.label                     as teks,
           lower(s.name || ' · ' || ci.label)              as t,
           -- Nomor di ujung label: "- 88", ": 12" (sama seperti `nomorAkhir`).
           nullif(substring(ci.label from '[-:]\s*(\d+)\s*$'), '')::integer as nomor,
           (select k from kunci)                           as kunci_teks
    from public.curriculum_items ci
    join public.books b    on b.id = ci.book_id
    join public.subjects s on s.id = b.subject_id
    where b.subject_id = p_subject
      and ci.is_active
      and b.is_active
      and (select boleh from izin)
  ),
  cocok as (
    select d.*
    from dasar d
    where d.kunci_teks = ''
       or not exists (select 1 from kata where d.t not like '%' || kata.w || '%')
       or (
            -- nomor persis bila hanya satu kata angka, walau teks tidak cocok
            (select count(*) from kata) = 1
            and d.kunci_teks ~ '^\d+$'
            and d.nomor = d.kunci_teks::integer
          )
  ),
  berskor as (
    select c.*,
           case
             when c.kunci_teks = '' then 4
             when (select count(*) from kata) = 1
                  and c.kunci_teks ~ '^\d+$'
                  and c.nomor = c.kunci_teks::integer then 0
             when c.t like c.kunci_teks || '%' then 2
             when c.t ~ ('(^|[\s''\-\:·])' || regexp_replace(c.kunci_teks,
                    '([.*+?^${}()|\[\]\\])', '\\\1', 'g')) then 3
             else 4
           end as skor
    from cocok c
  )
  select b.id, b.subject_id, b.teks, b.value, b.is_cyclic
  from berskor b
  order by b.skor,
           b.stage_order,
           b.sort_order,
           b.seq,
           b.id
  limit greatest(1, least(coalesce(p_limit, 60), 200));
$$;

-- Item yang sudah tersimpan (untuk menampilkan nilai terpilih walau di luar hasil cari).
create or replace function public.curriculum_items_by_ids(p_ids uuid[])
returns table (
  id uuid,
  subject_id uuid,
  label text,
  value numeric,
  siklik boolean
)
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select ci.id,
         b.subject_id,
         s.name || ' · ' || ci.label,
         ci.value,
         b.is_cyclic
  from public.curriculum_items ci
  join public.books b    on b.id = ci.book_id
  join public.subjects s on s.id = b.subject_id
  where ci.id = any (p_ids)
    and (
      public.is_staff()
      or (public.current_app_role() is null
          and session_user in ('postgres', 'service_role', 'supabase_admin'))
    )
$$;

-- ---------- Hardening: tanpa EXECUTE untuk anon/PUBLIC
revoke execute on function public.curriculum_items_search(uuid, text, integer) from public, anon;
revoke execute on function public.curriculum_items_by_ids(uuid[]) from public, anon;
grant execute on function public.curriculum_items_search(uuid, text, integer) to authenticated, service_role;
grant execute on function public.curriculum_items_by_ids(uuid[]) to authenticated, service_role;

-- Catatan: bila pg_trgm telanjur dipasang di `public`, fungsi bantu ekstensi (dimiliki
-- supabase_admin) tetap terbuka ke anon dan TIDAK bisa dicabut dari sini. Hapus ekstensi
-- lalu pasang ulang ke skema `extensions` (lihat bagian atas). Indeks GIN ikut dibuat ulang.


-- Verifikasi setelah migrasi:
--   select * from public.curriculum_items_search(
--     (select id from public.subjects where name='Tilawah'), 'quraisy', 5);
--   select * from public.curriculum_items_search(
--     (select id from public.subjects where name='Tilawah'), '351', 5);  -- nomor persis di urutan 1
--   sebagai anon: ditolak 42501; authenticated tanpa profil: 0 baris.