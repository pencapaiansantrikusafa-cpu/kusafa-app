-- T7a: perbaiki kasus (f) pada v_monthly_report.
-- Keputusan Mudir (f): target_monthly KOSONG bila tidak ada target ATAU Hari Efektif
-- belum diatur; 0 hanya bila target ada dan Hadir benar-benar 0; bulan 0 tetap NULL.
-- Untuk target bulanan (Wasilah/Ghayah, tidak dikali Hadir): Hari Efektif belum diatur
-- => NULL; bila Hari Efektif ada, target_monthly = amount (bukan 0 meski Hadir 0,
-- karena bulanan tidak dikali Hadir).

create or replace view public.v_monthly_report_base with (security_invoker = true) as
select
  e.id as entry_id, e.student_id, e.halaqah_id, e.subject_id, sj.domain,
  e.month_id, vm.hijri_year, vm.month_no, vm.name as month_name, vm.prev_month_id,
  e.item_id, ci.label as item_label, e.putaran,
  pe.item_id as prev_item_id, pci.label as prev_item_label, pe.putaran as prev_putaran,
  public.item_position(e.item_id, e.putaran) as pos,
  case when pe.id is null then null
       else public.item_position(e.item_id, e.putaran) - public.item_position(pe.item_id, pe.putaran) end as selisih,
  att.hadir, att.effective_days,
  tgt.id as target_id, tgt.amount as target_amount, tgt.amount_period as target_period,
  case
    when vm.month_no = 0 then null
    when tgt.id is null then null
    when att.effective_days is null then null  -- Hari Efektif belum diatur (f)
    when tgt.amount_period = 'harian' then
      case
        when att.hadir is null then null
        else tgt.amount * att.hadir  -- hadir=0 => 0 (f)
      end
    else tgt.amount  -- bulanan: langsung, tidak dikali Hadir (c)
  end as target_monthly
from public.progress_entries e
join public.subjects sj on sj.id = e.subject_id
join public.curriculum_items ci on ci.id = e.item_id
join public.v_months_ordered vm on vm.id = e.month_id
left join public.progress_entries pe
  on pe.student_id = e.student_id and pe.subject_id = e.subject_id and pe.month_id = vm.prev_month_id
left join public.curriculum_items pci on pci.id = pe.item_id
left join public.v_attendance att
  on att.student_id = e.student_id and att.month_id = e.month_id and att.domain = sj.domain
left join lateral (
  select t.* from public.targets t
  join public.v_months_ordered tm on tm.id = t.effective_month_id
  where t.status = 'disetujui' and t.subject_id = e.subject_id and tm.ord <= vm.ord
    and (t.student_id = e.student_id or (t.student_id is null and t.halaqah_id = e.halaqah_id))
  order by (t.student_id is not null) desc, tm.ord desc
  limit 1
) tgt on true;

create or replace view public.v_monthly_report with (security_invoker = true) as
select b.*,
       (b.selisih < b.target_monthly) as below_target,
       (b.hadir < b.effective_days) as attendance_short
from public.v_monthly_report_base b;
