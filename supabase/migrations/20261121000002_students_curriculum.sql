-- KUSAFA: santri, wali (disiapkan), dan kurikulum dinamis.

create table public.students (
  id uuid primary key default gen_random_uuid(),
  nis text not null unique,
  full_name text not null,
  gender public.gender_kind not null,
  angkatan integer,
  is_active boolean not null default true
);

-- Level hanya label pengelompokan. Posisi belajar santri dicatat per bidang (progress_entries), bukan per level.
create table public.student_levels (
  student_id uuid not null references public.students (id) on delete cascade,
  academic_year_id uuid not null references public.academic_years (id) on delete cascade,
  domain public.domain_kind not null,
  level_label text not null,
  primary key (student_id, academic_year_id, domain)
);

-- Disiapkan untuk login wali santri (belum diaktifkan; lihat docs/SPEC.md bagian "Ditunda").
create table public.guardians (
  profile_id uuid not null references public.profiles (id) on delete cascade,
  student_id uuid not null references public.students (id) on delete cascade,
  primary key (profile_id, student_id)
);

create table public.subjects (
  id uuid primary key default gen_random_uuid(),
  domain public.domain_kind not null,
  code text not null unique,
  name text not null,
  unit text not null,
  sort_order integer not null default 0,
  is_active boolean not null default true
);

-- value_offset: penyelaras posisi. posisi = item.value + value_offset (+ (putaran - 1) * cycle_length bila siklik).
--   Al Qur'an: value dari file dropdown; Iqro' dijajarkan ke Karima lewat value_offset.
--   Wasilah/Ghayah: item.value = nomor urut baris dalam buku; value_offset = jumlah item buku-buku sebelumnya di bidang yang sama.
create table public.books (
  id uuid primary key default gen_random_uuid(),
  subject_id uuid not null references public.subjects (id) on delete cascade,
  name text not null,
  stage_order integer not null default 0,
  is_cyclic boolean not null default false,
  cycle_length integer,
  value_offset numeric not null default 0,
  sort_order integer not null default 0,
  is_active boolean not null default true,
  unique (subject_id, name),
  check (not is_cyclic or cycle_length is not null)
);

create table public.curriculum_items (
  id uuid primary key default gen_random_uuid(),
  book_id uuid not null references public.books (id) on delete cascade,
  label text not null,        -- teks untuk dropdown
  detail text not null,       -- halaman / bab / bait / ayat sesuai file asli
  value numeric not null,
  seq integer not null,
  is_active boolean not null default true,
  legacy_id integer,
  constraint curriculum_items_book_seq_uniq unique (book_id, seq) deferrable initially immediate
);
create index curriculum_items_book_idx on public.curriculum_items (book_id, seq);
