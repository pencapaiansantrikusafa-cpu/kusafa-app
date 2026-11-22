-- KUSAFA: tipe data dasar, profil pengguna, kalender Hijriyah.
-- Semua penjelasan aturan ada di docs/SPEC.md.

create type public.app_role as enum (
  'mudir', 'admin', 'masul_alquran', 'masul_wasilah', 'masul_ghayah', 'musyrif', 'mudarris', 'wali'
);
create type public.domain_kind as enum ('alquran', 'wasilah', 'ghayah');
create type public.gender_kind as enum ('L', 'P');
create type public.target_status as enum ('diajukan', 'disetujui', 'ditolak');
create type public.target_period as enum ('harian', 'bulanan');
create type public.teacher_role as enum ('utama', 'pendamping');

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  full_name text not null,
  role public.app_role not null,
  gender public.gender_kind,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table public.academic_years (
  id uuid primary key default gen_random_uuid(),
  hijri_year integer not null unique,          -- tahun Hijriyah saat Syawwal dimulai
  name text not null,
  is_active boolean not null default false
);

-- month_no: 0 = Data Awal (hanya tahun pertama pemakaian, diisi manual Admin), 1 = Syawwal ... 12 = Ramadhan
create table public.hijri_months (
  id uuid primary key default gen_random_uuid(),
  academic_year_id uuid not null references public.academic_years (id) on delete cascade,
  month_no smallint not null check (month_no between 0 and 12),
  name text not null,
  semester smallint check (semester in (1, 2)),
  start_date date,
  end_date date,
  unique (academic_year_id, month_no),
  check ((month_no = 0 and semester is null) or (month_no > 0 and semester is not null))
);

-- Hari Efektif per bulan per domain, dan penguncian bulan.
create table public.month_domain_settings (
  month_id uuid not null references public.hijri_months (id) on delete cascade,
  domain public.domain_kind not null,
  effective_days integer check (effective_days >= 0),
  is_locked boolean not null default false,
  primary key (month_id, domain)
);

-- Membuat 12 bulan (dan opsional bulan 0) untuk tahun ajaran baru. Berjalan sebagai pemanggil, jadi RLS berlaku (Admin/Mudir).
create or replace function public.create_academic_year(p_hijri_year integer, p_name text, p_with_baseline boolean default false)
returns uuid language plpgsql as $$
declare
  v_id uuid;
  v_names text[] := array['Syawwal', 'Dzul Qa''dah', 'Dzul Hijjah', 'Muharram', 'Shafar', 'Rabiul Awwal',
                          'Rabiul Akhir', 'Jumadal Ula', 'Jumadal Akhir', 'Rajab', 'Sya''ban', 'Ramadhan'];
  i integer;
begin
  insert into public.academic_years (hijri_year, name) values (p_hijri_year, p_name) returning id into v_id;
  if p_with_baseline then
    insert into public.hijri_months (academic_year_id, month_no, name, semester) values (v_id, 0, 'Data Awal', null);
  end if;
  for i in 1..12 loop
    insert into public.hijri_months (academic_year_id, month_no, name, semester)
    values (v_id, i, v_names[i], case when i <= 6 then 1 else 2 end);
  end loop;
  return v_id;
end $$;
