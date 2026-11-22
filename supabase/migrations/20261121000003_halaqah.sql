-- KUSAFA: halaqah, mata pelajaran, pengampu, dan anggota.
--   Al Quran : satu halaqah (HLQ-PA-n / HLQ-PI-n), bidang Tilawah, Tahfidz, Kitabah, satu musyrif/ah.
--   Wasilah  : satu halaqah = satu Level; tiap mata pelajaran punya pengampu, hari, dan sesi KBM sendiri (halaqah_teachers).
--   Ghayah   : satu halaqah = satu kelompok usia (Putra/Putri), satu materi, muallim + pendamping.

create table public.halaqahs (
  id uuid primary key default gen_random_uuid(),
  academic_year_id uuid not null references public.academic_years (id) on delete cascade,
  domain public.domain_kind not null,
  code text not null,
  name text not null,
  category text check (category in ('Putra', 'Putri')),
  level_label text,
  is_active boolean not null default true,
  unique (academic_year_id, domain, code)
);

create table public.halaqah_subjects (
  halaqah_id uuid not null references public.halaqahs (id) on delete cascade,
  subject_id uuid not null references public.subjects (id),
  primary key (halaqah_id, subject_id)
);

-- Halaqah boleh belum punya pengampu dan jadwal (contoh: Level 6).
create table public.halaqah_teachers (
  id uuid primary key default gen_random_uuid(),
  halaqah_id uuid not null references public.halaqahs (id) on delete cascade,
  profile_id uuid not null references public.profiles (id),
  subject_id uuid references public.subjects (id),     -- diisi untuk Wasilah (pengampu per mata pelajaran)
  schedule_days text,                                  -- misalnya 'Ahad - Senin'
  kbm_session smallint check (kbm_session between 1 and 3),
  teacher_role public.teacher_role not null default 'utama'
);
create unique index halaqah_teachers_uniq
  on public.halaqah_teachers (halaqah_id, profile_id, coalesce(subject_id, '00000000-0000-0000-0000-000000000000'::uuid), teacher_role);

create table public.halaqah_members (
  id uuid primary key default gen_random_uuid(),
  halaqah_id uuid not null references public.halaqahs (id) on delete cascade,
  student_id uuid not null references public.students (id) on delete cascade,
  joined_on date not null default current_date,
  left_on date
);
create unique index halaqah_members_uniq on public.halaqah_members (halaqah_id, student_id) where left_on is null;
create index halaqah_members_student_idx on public.halaqah_members (student_id);
