-- KUSAFA: target, capaian bulanan, kehadiran, catatan.

-- Target Al Quran: individual (student_id), harian. Target Wasilah/Ghayah: untuk halaqah (halaqah_id), bulanan.
-- Target berlaku mulai effective_month_id sampai ada target baru yang disetujui.
create table public.targets (
  id uuid primary key default gen_random_uuid(),
  domain public.domain_kind not null,
  subject_id uuid not null references public.subjects (id),
  student_id uuid references public.students (id) on delete cascade,
  halaqah_id uuid references public.halaqahs (id) on delete cascade,
  effective_month_id uuid not null references public.hijri_months (id),
  amount numeric not null check (amount >= 0),
  amount_period public.target_period not null,
  status public.target_status not null default 'diajukan',
  proposed_by uuid references public.profiles (id) default auth.uid(),
  approved_by uuid references public.profiles (id),
  approved_at timestamptz,
  note text,
  created_at timestamptz not null default now(),
  check ((student_id is not null) <> (halaqah_id is not null))
);

-- Satu baris = posisi santri pada satu bidang di satu bulan.
-- Wasilah/Ghayah: pengampu mengisi satu kali per halaqah dan bidang; aplikasi menyalinnya per anggota halaqah.
-- putaran: untuk buku siklik (Tilawah Al Qur'an). Naik 1 hanya lewat pilihan "khatam, mulai putaran baru".
create table public.progress_entries (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students (id) on delete cascade,
  halaqah_id uuid references public.halaqahs (id) on delete set null,
  subject_id uuid not null references public.subjects (id),
  month_id uuid not null references public.hijri_months (id),
  item_id uuid not null references public.curriculum_items (id),
  putaran integer not null default 1 check (putaran >= 1),
  entered_by uuid references public.profiles (id) default auth.uid(),
  entered_at timestamptz not null default now(),
  unique (student_id, subject_id, month_id)
);
create index progress_entries_month_idx on public.progress_entries (month_id, subject_id);
create index progress_entries_halaqah_idx on public.progress_entries (halaqah_id, month_id);

-- Hadir tidak disimpan; dihitung dari Hari Efektif - (izin + sakit + alpha). Lihat v_attendance.
-- effective_days_override: Hari Efektif khusus santri (misalnya masuk terlambat). Kosong = pakai Hari Efektif domain.
-- Hanya Mudir/Admin yang boleh mengisinya (dijaga trigger di migrasi RLS).
create table public.attendance (
  student_id uuid not null references public.students (id) on delete cascade,
  month_id uuid not null references public.hijri_months (id),
  domain public.domain_kind not null,
  izin integer not null default 0 check (izin >= 0),
  sakit integer not null default 0 check (sakit >= 0),
  alpha integer not null default 0 check (alpha >= 0),
  effective_days_override integer check (effective_days_override >= 0),
  entered_by uuid references public.profiles (id) default auth.uid(),
  entered_at timestamptz not null default now(),
  primary key (student_id, month_id, domain)
);

-- Catatan per santri per bulan per domain (termasuk catatan muhasabah).
create table public.monthly_notes (
  student_id uuid not null references public.students (id) on delete cascade,
  month_id uuid not null references public.hijri_months (id),
  domain public.domain_kind not null,
  note text not null,
  entered_by uuid references public.profiles (id) default auth.uid(),
  entered_at timestamptz not null default now(),
  primary key (student_id, month_id, domain)
);
