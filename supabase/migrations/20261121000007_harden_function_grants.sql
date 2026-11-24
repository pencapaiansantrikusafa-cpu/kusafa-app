-- KUSAFA: perkuat hak akses fungsi (hardening pra-T6).
--
-- Sebelum migrasi ini, semua 18 fungsi di skema public punya EXECUTE untuk
-- anon, authenticated, service_role, dan PUBLIC (ACL =X). Anon tidak boleh
-- memanggil fungsi apa pun; hanya authenticated (dan service_role) yang
-- boleh memanggil fungsi yang benar-benar dipakai lewat policy RLS, view,
-- atau rpc() di src/. Fungsi trigger tidak diberi GRANT ke authenticated.
--
-- Semua fungsi SECURITY DEFINER juga dikunci search_path-nya (sudah sebagian,
-- dilengkapi di sini), dan 4 fungsi INVOKER diberi SET search_path eksplisit.
-- ALTER DEFAULT PRIVILEGES memastikan fungsi baru tidak otomatis terbuka ke
-- anon/PUBLIC.

-- ---------- 1. Cabut EXECUTE dari PUBLIC dan anon untuk semua fungsi public
revoke execute on all functions in schema public from public;
revoke execute on all functions in schema public from anon;

-- ---------- 2. GRANT EXECUTE hanya ke authenticated + service_role
-- Fungsi yang dipakai policy RLS (dipanggil dari policy, bukan dari klien):
grant execute on function public.current_app_role()               to authenticated, service_role;
grant execute on function public.is_full_access()                 to authenticated, service_role;
grant execute on function public.is_staff()                       to authenticated, service_role;
grant execute on function public.is_any_masul()                   to authenticated, service_role;
grant execute on function public.is_masul_of(public.domain_kind)  to authenticated, service_role;
grant execute on function public.can_manage(public.domain_kind)   to authenticated, service_role;
grant execute on function public.domain_of_subject(uuid)          to authenticated, service_role;
grant execute on function public.domain_of_book(uuid)             to authenticated, service_role;
grant execute on function public.domain_of_halaqah(uuid)          to authenticated, service_role;
grant execute on function public.month_is_open(uuid, public.domain_kind) to authenticated, service_role;
grant execute on function public.teaches_halaqah_subject(uuid, uuid)     to authenticated, service_role;
grant execute on function public.student_in_taught_halaqah(uuid, uuid)   to authenticated, service_role;
grant execute on function public.student_in_taught_domain(uuid, public.domain_kind) to authenticated, service_role;

-- Fungsi yang dipakai lewat rpc() di src/ atau oleh view:
grant execute on function public.item_position(uuid, integer)     to authenticated, service_role;

-- Fungsi utilitas admin (akan dipakai lewat rpc() di T8). RLS pada tabel
-- yang ditulisnya sudah menjaga; hanya authenticated yang boleh memanggil.
grant execute on function public.create_academic_year(integer, text, boolean) to authenticated, service_role;
grant execute on function public.reorder_items(uuid, uuid[])                  to authenticated, service_role;
grant execute on function public.resequence_subject(uuid)                     to authenticated, service_role;

-- attendance_guard_override() sengaja tidak diberi GRANT ke authenticated:
-- hanya dipakai sebagai trigger attendance_guard, bukan dipanggil klien.

-- ---------- 3. Fungsi baru tidak otomatis terbuka ke anon/PUBLIC
-- ALTER DEFAULT PRIVILEGES untuk role postgres (pemilik objek di schema public).
-- Ganti from postgres sesuai role yang membuat fungsi (di Supabase: postgres).
alter default privileges for role postgres in schema public
  revoke execute on functions from public;
alter default privileges for role postgres in schema public
  revoke execute on functions from anon;
-- Beri otomatis ke authenticated + service_role agar fungsi baru tetap bisa
-- dipakai aplikasi tanpa langkah tambahan (RLS tetap penjaga data).
alter default privileges for role postgres in schema public
  grant execute on functions to authenticated;
alter default privileges for role postgres in schema public
  grant execute on functions to service_role;

-- ---------- 4. Lengkapi search_path untuk fungsi INVOKER (penguatan)
-- item_position dipakai view v_monthly_report_base dan rpc() src/lib/posisi.ts.
create or replace function public.item_position(p_item uuid, p_putaran integer default 1)
returns numeric language sql stable set search_path = public, pg_temp as $$
  select ci.value + b.value_offset
         + case when b.is_cyclic then (coalesce(p_putaran, 1) - 1) * b.cycle_length else 0 end
  from public.curriculum_items ci
  join public.books b on b.id = ci.book_id
  where ci.id = p_item
$$;

-- Utilitas admin (T8). Berjalan sebagai pemanggil, jadi RLS tetap berlaku.
create or replace function public.create_academic_year(p_hijri_year integer, p_name text, p_with_baseline boolean default false)
returns uuid language plpgsql set search_path = public, pg_temp as $$
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

create or replace function public.reorder_items(p_book uuid, p_ordered uuid[]) returns void
language plpgsql set search_path = public, pg_temp as $$
begin
  set constraints all deferred;
  update public.curriculum_items ci
     set seq = o.ord
    from unnest(p_ordered) with ordinality as o(id, ord)
   where ci.id = o.id and ci.book_id = p_book;
  perform public.resequence_subject((select subject_id from public.books where id = p_book));
end $$;

create or replace function public.resequence_subject(p_subject uuid) returns void
language plpgsql set search_path = public, pg_temp as $$
declare
  v_domain public.domain_kind;
  b record;
  v_run integer := 0;
  v_n integer;
begin
  select domain into v_domain from public.subjects where id = p_subject;
  if v_domain is null then raise exception 'Bidang tidak ditemukan.'; end if;
  if v_domain = 'alquran' then
    raise exception 'Nilai Al Qur''an diisi manual dan tidak dihitung ulang otomatis.';
  end if;
  set constraints all deferred;
  for b in select id from public.books where subject_id = p_subject order by stage_order, sort_order, name loop
    update public.books set value_offset = v_run where id = b.id;
    update public.curriculum_items ci
       set seq = r.rn, value = r.rn
      from (select id, row_number() over (order by seq, id)::integer as rn
              from public.curriculum_items where book_id = b.id) r
     where ci.id = r.id;
    select count(*) into v_n from public.curriculum_items where book_id = b.id;
    v_run := v_run + v_n;
  end loop;
end $$;
