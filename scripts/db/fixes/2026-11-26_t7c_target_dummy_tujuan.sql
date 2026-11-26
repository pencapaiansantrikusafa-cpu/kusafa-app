-- ============================================================================
-- T7c [1/3]: DUMMY target Wasilah/Ghayah BENTUK BARU (tujuan akhir = butir kurikulum).
-- Izin Mudir 26 November 2026 (HANYA Wasilah/Ghayah). Satu DUMMY per halaqah x mapel
-- yang ditetapkan; butir = item pertama buku pertama mapel itu (posisi awal yang sah).
-- Berlaku Syawwal 1447, status 'disetujui'. Diganti data asli di T8/T10.
--
-- Idempoten: tidak menambah bila sudah ada target 'disetujui' untuk halaqah x mapel itu.
-- Jalankan SESUDAH migrasi 20261126000032.
--   npm run db:sql -- scripts/db/fixes/2026-11-26_t7c_target_dummy_tujuan.sql
-- ============================================================================

with pilih as (
  select hs.halaqah_id, hs.subject_id, h.domain,
         (select ci.id
            from public.curriculum_items ci
            join public.books b on b.id = ci.book_id
           where b.subject_id = hs.subject_id and ci.is_active and b.is_active
           order by b.sort_order, ci.seq
           limit 1) as item_id
    from public.halaqah_subjects hs
    join public.halaqahs h on h.id = hs.halaqah_id
   where h.domain in ('wasilah', 'ghayah') and h.is_active
)
insert into public.targets
  (domain, subject_id, target_item_id, halaqah_id, effective_month_id,
   amount, amount_period, status, note)
select p.domain, p.subject_id, p.item_id, p.halaqah_id,
       (select id from public.hijri_months where month_no = 1),
       null, 'bulanan', 'disetujui',
       'DUMMY - target sementara Wasilah/Ghayah (tujuan akhir), diganti data asli T8/T10 (izin Mudir 26 Nov 2026)'
  from pilih p
 where p.item_id is not null
   and not exists (
     select 1 from public.targets t
      where t.halaqah_id = p.halaqah_id and t.subject_id = p.subject_id and t.status = 'disetujui'
   );
