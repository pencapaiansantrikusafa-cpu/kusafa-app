-- T7 [1b/2] verifikasi: bandingkan SEMUA baris laporan Al Qur'an dengan rumus view
-- SEBELUM migrasi target (000005), pada data yang sama.
-- Semua baris (2.036 Al Qur'an) harus identik pada pos, selisih, hadir, effective_days,
-- target_amount, target_period, target_monthly, below_target, attendance_short.
--
-- Catatan: view lama memakai target tanpa syarat bulan 0/NULL Hari Efektif; lihat
-- 20261121000005_functions_views.sql. Script ini mengulang rumus lama dengan lateral
-- join yang sama dan memakai tanggal target efektif -- tidak mengubah data apa pun.

with old_report as (
  select
    e.id as entry_id, e.student_id, e.halaqah_id, e.subject_id, sj.domain,
    e.month_id, vm.month_no,
    public.item_position(e.item_id, e.putaran) as pos,
    case when pe.id is null then null
         else public.item_position(e.item_id, e.putaran) - public.item_position(pe.item_id, pe.putaran) end as selisih,
    att.hadir, att.effective_days,
    tgt.id as target_id, tgt.amount as target_amount, tgt.amount_period as target_period,
    case when tgt.id is null then null
         when tgt.amount_period = 'harian' then tgt.amount * att.hadir
         else tgt.amount end as target_monthly
  from public.progress_entries e
  join public.subjects sj on sj.id = e.subject_id
  join public.v_months_ordered vm on vm.id = e.month_id
  left join public.progress_entries pe
    on pe.student_id = e.student_id and pe.subject_id = e.subject_id and pe.month_id = vm.prev_month_id
  left join public.v_attendance att
    on att.student_id = e.student_id and att.month_id = e.month_id and att.domain = sj.domain
  left join lateral (
    select t.* from public.targets t
    join public.v_months_ordered tm on tm.id = t.effective_month_id
    where t.status = 'disetujui' and t.subject_id = e.subject_id and tm.ord <= vm.ord
      and (t.student_id = e.student_id or (t.student_id is null and t.halaqah_id = e.halaqah_id))
    order by (t.student_id is not null) desc, tm.ord desc
    limit 1
  ) tgt on true
  where sj.domain = 'alquran'
), old_final as (
  select o.*, (o.selisih < o.target_monthly) as below_target, (o.hadir < o.effective_days) as attendance_short
  from old_report o
), new_report as (
  select entry_id, student_id, halaqah_id, subject_id, domain, month_id, month_no,
         pos, selisih, hadir, effective_days, target_id, target_amount, target_period,
         target_monthly, below_target, attendance_short
  from public.v_monthly_report
  where domain = 'alquran'
)
select
  (select count(*) from old_final) as lama_baris,
  (select count(*) from new_report) as baru_baris,
  (select count(*) from (
     select entry_id, pos, selisih, hadir, effective_days, target_id, target_amount,
            target_period, target_monthly, below_target, attendance_short
     from old_final
     except
     select entry_id, pos, selisih, hadir, effective_days, target_id, target_amount,
            target_period, target_monthly, below_target, attendance_short
     from new_report
   ) q) as beda_lama_baru,
  (select count(*) from (
     select entry_id, pos, selisih, hadir, effective_days, target_id, target_amount,
            target_period, target_monthly, below_target, attendance_short
     from new_report
     except
     select entry_id, pos, selisih, hadir, effective_days, target_id, target_amount,
            target_period, target_monthly, below_target, attendance_short
     from old_final
   ) q) as beda_baru_lama;
