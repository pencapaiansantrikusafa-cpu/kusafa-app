-- T7b: Target DUMMY Wasilah/Ghayah (IZIN KHUSUS MUDIR, HANDOVER 26 Nov 2026).
-- Tujuan: fondasi uji T7. BUKAN data asli; akan diganti data asli di T8/T10.
-- Bentuk: per halaqah per mata pelajaran, BULANAN (tidak dikali Hadir), status disetujui.
-- Berlaku mulai: Syawwal 1447 (bulan 1), berlaku sampai diganti.
-- Aman dijalankan ulang: hanya menyisipkan bila belum ada target disetujui/diajukan
-- yang identik untuk kombinasi (domain, subject, halaqah, effective_month).

insert into public.targets
  (domain, subject_id, student_id, halaqah_id, effective_month_id, amount, amount_period,
   status, proposed_by, approved_by, approved_at, note)
select
  s.domain,
  hs.subject_id,
  null,
  hs.halaqah_id,
  m.id,
  1::numeric,
  'bulanan'::public.target_period,
  'disetujui'::public.target_status,
  null,
  null,
  now(),
  'DUMMY - target sementara Wasilah/Ghayah, diganti data asli T8/T10 (izin Mudir 26 Nov 2026)'
from public.halaqah_subjects hs
join public.subjects s on s.id = hs.subject_id
join public.hijri_months m on m.month_no = 1
join public.academic_years ay on ay.id = m.academic_year_id and ay.hijri_year = 1447
where s.domain in ('wasilah', 'ghayah')
  and not exists (
    select 1 from public.targets t
    where t.domain = s.domain
      and t.subject_id = hs.subject_id
      and t.halaqah_id = hs.halaqah_id
      and t.student_id is null
      and t.effective_month_id = m.id
      and t.note like 'DUMMY - target sementara Wasilah/Ghayah%'
  );
