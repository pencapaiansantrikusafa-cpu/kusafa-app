-- KUSAFA: hak akses (Row Level Security). Aturan ditegakkan di database, bukan hanya di tampilan.
-- Ringkasan (docs/SPEC.md bagian "Role dan hak akses"):
--   semua staf aktif membaca semua data; menulis hanya sesuai role dan halaqah yang diampu;
--   Hari Efektif, penguncian bulan, dan pengguna hanya Mudir/Admin; target disetujui oleh Mudir/Admin
--   atau Masul Al Quran / Masul Wasilah / Masul Ghayah sesuai domain.

-- ---------- fungsi pembantu (security definer agar tidak terkena rekursi RLS)
create or replace function public.current_app_role() returns public.app_role
language sql stable security definer set search_path = public, pg_temp as $$
  select role from public.profiles where id = auth.uid() and is_active
$$;

create or replace function public.is_full_access() returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select coalesce(public.current_app_role() in ('mudir', 'admin'), false)
$$;

create or replace function public.is_staff() returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select coalesce(public.current_app_role() in
    ('mudir', 'admin', 'masul_alquran', 'masul_wasilah', 'masul_ghayah', 'musyrif', 'mudarris'), false)
$$;

create or replace function public.is_any_masul() returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select coalesce(public.current_app_role() in ('masul_alquran', 'masul_wasilah', 'masul_ghayah'), false)
$$;

create or replace function public.is_masul_of(d public.domain_kind) returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select coalesce(
    (d = 'alquran' and public.current_app_role() = 'masul_alquran')
    or (d = 'wasilah' and public.current_app_role() = 'masul_wasilah')
    or (d = 'ghayah' and public.current_app_role() = 'masul_ghayah'), false)
$$;

create or replace function public.can_manage(d public.domain_kind) returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select public.is_full_access() or public.is_masul_of(d)
$$;

create or replace function public.domain_of_subject(s uuid) returns public.domain_kind
language sql stable security definer set search_path = public, pg_temp as $$
  select domain from public.subjects where id = s
$$;

create or replace function public.domain_of_book(b uuid) returns public.domain_kind
language sql stable security definer set search_path = public, pg_temp as $$
  select s.domain from public.books bk join public.subjects s on s.id = bk.subject_id where bk.id = b
$$;

create or replace function public.domain_of_halaqah(h uuid) returns public.domain_kind
language sql stable security definer set search_path = public, pg_temp as $$
  select domain from public.halaqahs where id = h
$$;

create or replace function public.month_is_open(m uuid, d public.domain_kind) returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select not coalesce((select is_locked from public.month_domain_settings where month_id = m and domain = d), false)
$$;

-- Apakah pengguna mengampu halaqah ini (untuk Wasilah, juga per mata pelajaran)?
create or replace function public.teaches_halaqah_subject(h uuid, s uuid) returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select exists (
    select 1 from public.halaqah_teachers ht
    where ht.halaqah_id = h and ht.profile_id = auth.uid()
      and (ht.subject_id is null or ht.subject_id = s)
  )
$$;

-- Apakah santri ini anggota aktif halaqah yang diampu pengguna untuk bidang tersebut?
create or replace function public.student_in_taught_halaqah(st uuid, s uuid) returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select exists (
    select 1
    from public.halaqah_members hm
    join public.halaqah_subjects hs on hs.halaqah_id = hm.halaqah_id and hs.subject_id = s
    join public.halaqah_teachers ht on ht.halaqah_id = hm.halaqah_id and ht.profile_id = auth.uid()
    where hm.student_id = st and hm.left_on is null
      and (ht.subject_id is null or ht.subject_id = s)
  )
$$;

-- Apakah santri ini anggota aktif halaqah mana pun di domain tersebut yang diampu pengguna? (kehadiran, catatan)
create or replace function public.student_in_taught_domain(st uuid, d public.domain_kind) returns boolean
language sql stable security definer set search_path = public, pg_temp as $$
  select exists (
    select 1
    from public.halaqah_members hm
    join public.halaqahs h on h.id = hm.halaqah_id and h.domain = d
    join public.halaqah_teachers ht on ht.halaqah_id = hm.halaqah_id and ht.profile_id = auth.uid()
    where hm.student_id = st and hm.left_on is null
  )
$$;

grant execute on all functions in schema public to authenticated;

-- ---------- aktifkan RLS di semua tabel
alter table public.profiles enable row level security;
alter table public.academic_years enable row level security;
alter table public.hijri_months enable row level security;
alter table public.month_domain_settings enable row level security;
alter table public.students enable row level security;
alter table public.student_levels enable row level security;
alter table public.guardians enable row level security;
alter table public.subjects enable row level security;
alter table public.books enable row level security;
alter table public.curriculum_items enable row level security;
alter table public.halaqahs enable row level security;
alter table public.halaqah_subjects enable row level security;
alter table public.halaqah_teachers enable row level security;
alter table public.halaqah_members enable row level security;
alter table public.targets enable row level security;
alter table public.progress_entries enable row level security;
alter table public.attendance enable row level security;
alter table public.monthly_notes enable row level security;

-- ---------- baca: semua staf aktif
create policy profiles_read on public.profiles for select to authenticated using (public.is_staff());
create policy academic_years_read on public.academic_years for select to authenticated using (public.is_staff());
create policy hijri_months_read on public.hijri_months for select to authenticated using (public.is_staff());
create policy month_settings_read on public.month_domain_settings for select to authenticated using (public.is_staff());
create policy students_read on public.students for select to authenticated using (public.is_staff());
create policy student_levels_read on public.student_levels for select to authenticated using (public.is_staff());
create policy subjects_read on public.subjects for select to authenticated using (public.is_staff());
create policy books_read on public.books for select to authenticated using (public.is_staff());
create policy items_read on public.curriculum_items for select to authenticated using (public.is_staff());
create policy halaqahs_read on public.halaqahs for select to authenticated using (public.is_staff());
create policy halaqah_subjects_read on public.halaqah_subjects for select to authenticated using (public.is_staff());
create policy halaqah_teachers_read on public.halaqah_teachers for select to authenticated using (public.is_staff());
create policy halaqah_members_read on public.halaqah_members for select to authenticated using (public.is_staff());
create policy targets_read on public.targets for select to authenticated using (public.is_staff());
create policy progress_read on public.progress_entries for select to authenticated using (public.is_staff());
create policy attendance_read on public.attendance for select to authenticated using (public.is_staff());
create policy notes_read on public.monthly_notes for select to authenticated using (public.is_staff());
create policy guardians_read on public.guardians for select to authenticated using (public.is_staff());

-- ---------- tulis: pengguna dan kalender (Mudir/Admin)
create policy profiles_write on public.profiles for all to authenticated
  using (public.is_full_access()) with check (public.is_full_access());
create policy academic_years_write on public.academic_years for all to authenticated
  using (public.is_full_access()) with check (public.is_full_access());
create policy hijri_months_write on public.hijri_months for all to authenticated
  using (public.is_full_access()) with check (public.is_full_access());
create policy month_settings_write on public.month_domain_settings for all to authenticated
  using (public.is_full_access()) with check (public.is_full_access());
create policy guardians_write on public.guardians for all to authenticated
  using (public.is_full_access()) with check (public.is_full_access());

-- ---------- tulis: santri (Mudir/Admin, Masul Al Quran, Masul Wasilah, Masul Ghayah)
create policy students_write on public.students for all to authenticated
  using (public.is_full_access() or public.is_any_masul())
  with check (public.is_full_access() or public.is_any_masul());
create policy student_levels_write on public.student_levels for all to authenticated
  using (public.is_full_access() or public.can_manage(domain))
  with check (public.is_full_access() or public.can_manage(domain));

-- ---------- tulis: kurikulum dan halaqah (Mudir/Admin atau Masul sesuai domain)
create policy subjects_write on public.subjects for all to authenticated
  using (public.can_manage(domain)) with check (public.can_manage(domain));
create policy books_write on public.books for all to authenticated
  using (public.can_manage(public.domain_of_subject(subject_id)))
  with check (public.can_manage(public.domain_of_subject(subject_id)));
create policy items_write on public.curriculum_items for all to authenticated
  using (public.can_manage(public.domain_of_book(book_id)))
  with check (public.can_manage(public.domain_of_book(book_id)));
create policy halaqahs_write on public.halaqahs for all to authenticated
  using (public.can_manage(domain)) with check (public.can_manage(domain));
create policy halaqah_subjects_write on public.halaqah_subjects for all to authenticated
  using (public.can_manage(public.domain_of_halaqah(halaqah_id)))
  with check (public.can_manage(public.domain_of_halaqah(halaqah_id)));
create policy halaqah_teachers_write on public.halaqah_teachers for all to authenticated
  using (public.can_manage(public.domain_of_halaqah(halaqah_id)))
  with check (public.can_manage(public.domain_of_halaqah(halaqah_id)));
create policy halaqah_members_write on public.halaqah_members for all to authenticated
  using (public.can_manage(public.domain_of_halaqah(halaqah_id)))
  with check (public.can_manage(public.domain_of_halaqah(halaqah_id)));

-- ---------- tulis: capaian (Mudir/Admin kapan saja; pengampu hanya bulan yang belum terkunci)
create policy progress_insert on public.progress_entries for insert to authenticated
  with check (public.is_full_access() or (
    public.month_is_open(month_id, public.domain_of_subject(subject_id))
    and public.student_in_taught_halaqah(student_id, subject_id)));
create policy progress_update on public.progress_entries for update to authenticated
  using (public.is_full_access() or (
    public.month_is_open(month_id, public.domain_of_subject(subject_id))
    and public.student_in_taught_halaqah(student_id, subject_id)))
  with check (public.is_full_access() or (
    public.month_is_open(month_id, public.domain_of_subject(subject_id))
    and public.student_in_taught_halaqah(student_id, subject_id)));
create policy progress_delete on public.progress_entries for delete to authenticated
  using (public.is_full_access());

-- ---------- tulis: kehadiran dan catatan
create policy attendance_insert on public.attendance for insert to authenticated
  with check (public.is_full_access() or (
    public.month_is_open(month_id, domain) and public.student_in_taught_domain(student_id, domain)));
create policy attendance_update on public.attendance for update to authenticated
  using (public.is_full_access() or (
    public.month_is_open(month_id, domain) and public.student_in_taught_domain(student_id, domain)))
  with check (public.is_full_access() or (
    public.month_is_open(month_id, domain) and public.student_in_taught_domain(student_id, domain)));
create policy attendance_delete on public.attendance for delete to authenticated
  using (public.is_full_access());

create policy notes_insert on public.monthly_notes for insert to authenticated
  with check (public.is_full_access() or (
    public.month_is_open(month_id, domain) and public.student_in_taught_domain(student_id, domain)));
create policy notes_update on public.monthly_notes for update to authenticated
  using (public.is_full_access() or (
    public.month_is_open(month_id, domain) and public.student_in_taught_domain(student_id, domain)))
  with check (public.is_full_access() or (
    public.month_is_open(month_id, domain) and public.student_in_taught_domain(student_id, domain)));
create policy notes_delete on public.monthly_notes for delete to authenticated
  using (public.is_full_access());

-- ---------- target: pengampu mengajukan, Masul sesuai domain / Mudir / Admin menyetujui
create policy targets_insert on public.targets for insert to authenticated
  with check (
    public.can_manage(domain)
    or (status = 'diajukan' and (
         (student_id is not null and public.student_in_taught_halaqah(student_id, subject_id))
      or (halaqah_id is not null and public.teaches_halaqah_subject(halaqah_id, subject_id)))));
create policy targets_update on public.targets for update to authenticated
  using (public.can_manage(domain)) with check (public.can_manage(domain));
create policy targets_delete on public.targets for delete to authenticated
  using (public.can_manage(domain) or (proposed_by = auth.uid() and status = 'diajukan'));

-- ---------- Hari Efektif khusus santri hanya boleh diubah Mudir/Admin (pengampu tidak boleh lewat kolom ini)
-- Koneksi server (psql, seed) tidak memiliki auth.uid() dan dilewati.
create or replace function public.attendance_guard_override() returns trigger
language plpgsql security definer set search_path = public, pg_temp as $$
begin
  if auth.uid() is not null and not public.is_full_access() then
    if tg_op = 'INSERT' and new.effective_days_override is not null then
      raise exception 'Hari Efektif khusus santri hanya bisa diisi Mudir atau Admin.';
    end if;
    if tg_op = 'UPDATE' and new.effective_days_override is distinct from old.effective_days_override then
      raise exception 'Hari Efektif khusus santri hanya bisa diubah Mudir atau Admin.';
    end if;
  end if;
  return new;
end $$;

create trigger attendance_guard
  before insert or update on public.attendance
  for each row execute function public.attendance_guard_override();
