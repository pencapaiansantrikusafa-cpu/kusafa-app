-- ============================================================================
-- T7c [2/3] BACKEND (perintah Mudir, 27 November 2026) - bagian 4.
--
-- `v_monthly_report` untuk Ilmu Wasilah / Ilmu Ghayah kini menampilkan TARGET
-- (tujuan akhir = butir kurikulum) dan STATUS pencapaiannya:
--   target_item_id  : butir tujuan akhir yang disetujui (NULL bila tidak ada).
--   target_label    : label butir target (polos; UI menambahkan "Mapel · <label>").
--   target_pos      : posisi target lewat item_position (lintas buku).
--   target_tercapai : true bila posisi capaian >= posisi target.
--   target_kurang   : selisih butir yang kurang (lintas buku), 0 bila tercapai.
--   target_status   : 'Tercapai' atau 'Kurang N butir'; NULL bila tidak ada target.
--
-- Al Qur'an TIDAK berubah: target Al Qur'an punya `amount` (tanpa `target_item_id`),
-- sehingga keenam kolom baru ini NULL untuk Al Qur'an, dan seluruh kolom lama tetap
-- sama persis. Semua hitungan tetap di database (item_position / view), React tidak
-- menghitung ulang.
--
-- Migrasi ini HANYA MENAMBAH kolom di akhir view (kolom lama nama+urutan tetap),
-- memakai `create or replace view ... with (security_invoker = true)` agar RLS
-- (yang berlaku karena security_invoker) TIDAK berubah.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. v_monthly_report_base: tambahkan butir target pada lateral `targets` + kolom baru.
-- ----------------------------------------------------------------------------
create or replace view public.v_monthly_report_base with (security_invoker = true) as
  select e.id as entry_id,
         e.student_id,
         e.halaqah_id,
         e.subject_id,
         sj.domain,
         e.month_id,
         vm.hijri_year,
         vm.month_no,
         vm.name as month_name,
         vm.prev_month_id,
         e.item_id,
         ci.label as item_label,
         e.putaran,
         pe.item_id as prev_item_id,
         pci.label as prev_item_label,
         pe.putaran as prev_putaran,
         item_position(e.item_id, e.putaran) as pos,
         case
           when pe.id is null then null
           else item_position(e.item_id, e.putaran) - item_position(pe.item_id, pe.putaran)
         end as selisih,
         att.hadir,
         att.effective_days,
         tgt.id as target_id,
         tgt.amount as target_amount,
         tgt.amount_period as target_period,
         case
           when vm.month_no = 0 then null
           when tgt.id is null then null
           when att.effective_days is null then null
           when tgt.amount_period = 'harian' then
             case
               when att.hadir is null then null
               else tgt.amount * att.hadir::numeric
             end
           else tgt.amount
         end as target_monthly,
         -- ===== kolom BARU (tujuan akhir untuk Wasilah/Ghayah) =====
         tgt.target_item_id,
         tci.label as target_label,
         case when tgt.target_item_id is null then null
              else item_position(tgt.target_item_id, 1) end as target_pos,
         case when tgt.target_item_id is null then null
              else item_position(e.item_id, e.putaran) >= item_position(tgt.target_item_id, 1)
         end as target_tercapai,
         case when tgt.target_item_id is null then null
              when item_position(e.item_id, e.putaran) >= item_position(tgt.target_item_id, 1) then 0
              else item_position(tgt.target_item_id, 1) - item_position(e.item_id, e.putaran)
         end as target_kurang,
         case
           when tgt.target_item_id is null then null
           when item_position(e.item_id, e.putaran) >= item_position(tgt.target_item_id, 1) then 'Tercapai'
           else 'Kurang ' || trim(to_char(
                  item_position(tgt.target_item_id, 1) - item_position(e.item_id, e.putaran), 'FM999999'))
                || ' butir'
         end as target_status
    from progress_entries e
      join subjects sj on sj.id = e.subject_id
      join curriculum_items ci on ci.id = e.item_id
      join v_months_ordered vm on vm.id = e.month_id
      left join progress_entries pe
        on pe.student_id = e.student_id and pe.subject_id = e.subject_id and pe.month_id = vm.prev_month_id
      left join curriculum_items pci on pci.id = pe.item_id
      left join v_attendance att
        on att.student_id = e.student_id and att.month_id = e.month_id and att.domain = sj.domain
      left join lateral (
        select t.id, t.amount, t.amount_period, t.target_item_id
          from targets t
          join v_months_ordered tm on tm.id = t.effective_month_id
         where t.status = 'disetujui'
           and t.subject_id = e.subject_id
           and tm.ord <= vm.ord
           and (t.student_id = e.student_id
                or (t.student_id is null and t.halaqah_id = e.halaqah_id))
         order by (t.student_id is not null) desc, tm.ord desc, t.created_at desc, t.id desc
         limit 1
      ) tgt on true
      left join curriculum_items tci on tci.id = tgt.target_item_id;

-- ----------------------------------------------------------------------------
-- 2. v_monthly_report: bawa kolom baru ke view siap pakai (kolom lama tetap di depan).
-- ----------------------------------------------------------------------------
create or replace view public.v_monthly_report with (security_invoker = true) as
  select entry_id,
         student_id,
         halaqah_id,
         subject_id,
         domain,
         month_id,
         hijri_year,
         month_no,
         month_name,
         prev_month_id,
         item_id,
         item_label,
         putaran,
         prev_item_id,
         prev_item_label,
         prev_putaran,
         pos,
         selisih,
         hadir,
         effective_days,
         target_id,
         target_amount,
         target_period,
         target_monthly,
         selisih < target_monthly as below_target,
         hadir < effective_days as attendance_short,
         target_item_id,
         target_label,
         target_pos,
         target_tercapai,
         target_kurang,
         target_status
    from v_monthly_report_base b;

-- ----------------------------------------------------------------------------
-- Verifikasi (jalankan setelah migrasi):
--   -- Al Qur'an tidak berubah: target butir = NULL untuk semua baris
--   select domain, count(*) filter (where target_item_id is not null) as ada_butir,
--          count(*) as baris from v_monthly_report group by domain;
--   -- Contoh Wasilah (setelah ada capaian + target): posisi target & status
--   select subject_id, item_label, target_label, pos, target_pos, target_status
--     from v_monthly_report where domain='wasilah' limit 5;
-- ----------------------------------------------------------------------------
