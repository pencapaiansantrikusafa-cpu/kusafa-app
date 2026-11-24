-- KUSAFA: bulan 0 (Data Awal) bukan bulan input staf.
--
-- Aturan final (docs/SPEC.md bagian 4 dan docs/DATA-NOTES.md):
--   month_no 0 = catatan awal untuk santri baru / pembanding Syawwal tahun pertama.
--   Bulan 0 BUKAN bulan efektif, BUKAN bulan target bulanan, dan TIDAK boleh
--   ditulis staf pengampu lewat RLS. Data Awal diisi manual oleh Admin/Mudir.
--
-- Sebelum migrasi ini, month_is_open(month_0, ...) mengembalikan true karena
-- tidak ada baris month_domain_settings untuk bulan 0. Akibatnya staf pengampu
-- yang memanggil API langsung bisa menulis capaian/kehadiran/catatan bulan 0.
-- Fungsi ini mengembalikan false untuk bulan 0 dan untuk bulan yang tidak ada;
-- bulan 1-12 tetap mengikuti is_locked seperti sebelumnya.
--
-- Admin/Mudir tetap bisa menulis bulan 0 karena policy memakai is_full_access()
-- lebih dahulu; seed berjalan sebagai postgres dan tidak terpengaruh RLS.

create or replace function public.month_is_open(m uuid, d public.domain_kind)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select coalesce(
    (
      select not coalesce(mds.is_locked, false)
      from public.hijri_months hm
      left join public.month_domain_settings mds
             on mds.month_id = hm.id and mds.domain = d
      where hm.id = m
        and hm.month_no > 0
    ),
    false
  )
$$;

-- create or replace mempertahankan OID dan grant yang sudah ada; ulangi grant
-- agar aman bila migrasi ini dijalankan ulang di database baru.
revoke execute on function public.month_is_open(uuid, public.domain_kind) from public, anon;
grant execute on function public.month_is_open(uuid, public.domain_kind) to authenticated, service_role;

-- Verifikasi:
--   public.month_is_open(<bulan 0>, 'alquran') = false
--   public.month_is_open(<bulan 1>, 'alquran') = true
