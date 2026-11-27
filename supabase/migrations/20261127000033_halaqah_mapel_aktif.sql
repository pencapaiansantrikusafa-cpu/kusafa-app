-- ============================================================================
-- T7c [2/3] BACKEND (perintah Mudir, 27 November 2026) - bagian 1.
--
-- halaqah_mapel_aktif(halaqah, bulan): SATU-SATUNYA sumber daftar mata pelajaran
-- aktif sebuah halaqah pada suatu bulan. SEMUA RPC Input (boot/form) memakai
-- fungsi ini, bukan membaca `halaqah_subjects` langsung lagi.
--
--   Sekarang      : mapel aktif = halaqah_subjects (mapel aktif).
--   Nanti (T8)    : masa berlaku mapel per bulan ditambahkan DI DALAM fungsi ini,
--                   tanpa mengubah pemanggil (boot/form/gabungan).
--
-- Helper tuntas (SPEC 3.2a):
--   mapel_butir_terakhir(subject)      : butir terakhir dari buku terakhir mapel.
--   mapel_tuntas(halaqah,subject,bulan): capaian bulan itu sudah mencapai butir
--                                        terakhir mapel -> TUNTAS (tidak wajib target).
--   halaqah_tanpa_mapel(halaqah)       : halaqah Level 6 (belum/tidak punya mapel).
--
-- Keamanan: SECURITY INVOKER (RLS tetap berlaku), dipanggil dari RPC INVOKER;
-- EXECUTE hanya untuk authenticated + service_role.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Sumber tunggal mapel aktif per halaqah (+ bulan, dipakai mulai T8).
-- ----------------------------------------------------------------------------
create or replace function public.halaqah_mapel_aktif(p_halaqah uuid, p_bulan uuid default null)
returns table (subject_id uuid, name text, sort_order integer)
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  -- p_bulan dipakai mulai T8 (masa berlaku mapel). Saat ini diabaikan:
  -- mapel aktif = mapel yang ditetapkan halaqah dan mapelnya aktif.
  select s.id, s.name, s.sort_order
  from public.halaqah_subjects hs
  join public.subjects s on s.id = hs.subject_id
  where hs.halaqah_id = p_halaqah and s.is_active
  order by s.sort_order, s.name
$$;

revoke execute on function public.halaqah_mapel_aktif(uuid, uuid) from public, anon;
grant execute on function public.halaqah_mapel_aktif(uuid, uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 2. Butir terakhir dari buku terakhir suatu mata pelajaran.
--    Urutan: books.sort_order, books.stage_order, lalu curriculum_items.seq.
-- ----------------------------------------------------------------------------
create or replace function public.mapel_butir_terakhir(p_subject uuid)
returns uuid
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select ci.id
  from public.curriculum_items ci
  join public.books b on b.id = ci.book_id
  where b.subject_id = p_subject and ci.is_active and b.is_active
  order by b.sort_order desc, b.stage_order desc, ci.seq desc
  limit 1
$$;

revoke execute on function public.mapel_butir_terakhir(uuid) from public, anon;
grant execute on function public.mapel_butir_terakhir(uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 3. Tuntas: capaian bulan itu (satu nilai per halaqah x mapel) sudah mencapai
--    butir terakhir mapel. Bila tuntas, target bulan depan TIDAK diwajibkan.
-- ----------------------------------------------------------------------------
create or replace function public.mapel_tuntas(p_halaqah uuid, p_subject uuid, p_bulan uuid)
returns boolean
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select coalesce((
    -- nilai capaian halaqah ini (satu per mapel; ambil baris anggota pertama)
    select (array_agg(pe.item_id order by pe.student_id))[1]
    from public.progress_entries pe
    where pe.subject_id = p_subject and pe.month_id = p_bulan
      and pe.student_id in (
        select hm.student_id from public.halaqah_members hm
        where hm.halaqah_id = p_halaqah and hm.left_on is null)
  ) = public.mapel_butir_terakhir(p_subject), false)
$$;

revoke execute on function public.mapel_tuntas(uuid, uuid, uuid) from public, anon;
grant execute on function public.mapel_tuntas(uuid, uuid, uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 4. Halaqah Level 6: tidak punya mata pelajaran -> "Tuntas, belum ada
--    pelajaran lanjutan"; tidak dihitung dalam notifikasi kekurangan.
-- ----------------------------------------------------------------------------
create or replace function public.halaqah_tanpa_mapel(p_halaqah uuid)
returns boolean
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select not exists (select 1 from public.halaqah_subjects where halaqah_id = p_halaqah)
$$;

revoke execute on function public.halaqah_tanpa_mapel(uuid) from public, anon;
grant execute on function public.halaqah_tanpa_mapel(uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 5. Bulan berikutnya (bulan setelah bulan terpilih menurut v_months_ordered).
--    Mengembalikan NULL bila bulan terpilih adalah bulan terakhir tahun ajaran
--    (maka target bulan depan TIDAK diminta).
-- ----------------------------------------------------------------------------
create or replace function public.bulan_berikutnya(p_bulan uuid)
returns uuid
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select x.id
  from public.v_months_ordered x
  where x.ord > (select ord from public.v_months_ordered where id = p_bulan)
    and x.month_no <> 0
  order by x.ord
  limit 1
$$;

revoke execute on function public.bulan_berikutnya(uuid) from public, anon;
grant execute on function public.bulan_berikutnya(uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 6. Pakai sumber tunggal di RPC boot (pembukaan halaman Input Wasilah/Ghayah).
--    Perilaku sama dengan sebelumnya, hanya kini lewat halaqah_mapel_aktif.
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_input_boot(p_domain public.domain_kind)
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  v_boleh boolean;
  v_halaqah jsonb;
  v_guru jsonb;
  v_bulan jsonb;
  v_mapel jsonb;
  v_setelan jsonb;
begin
  v_boleh := coalesce(public.is_staff(), false)
             or (public.current_app_role() is null
                 and session_user in ('postgres', 'service_role', 'supabase_admin'));
  if not v_boleh then
    return jsonb_build_object('boleh', false);
  end if;
  if p_domain not in ('wasilah', 'ghayah') then
    raise exception 'Fungsi ini hanya untuk Ilmu Wasilah atau Ilmu Ghayah.';
  end if;

  select coalesce(jsonb_agg(jsonb_build_object('id', h.id, 'code', h.code) order by h.code), '[]'::jsonb)
    into v_halaqah
  from public.halaqahs h
  where h.domain = p_domain and h.is_active;

  select coalesce(jsonb_agg(jsonb_build_object(
           'halaqah_id', ht.halaqah_id, 'profile_id', ht.profile_id,
           'subject_id', ht.subject_id, 'full_name', p.full_name)
           order by ht.halaqah_id, p.full_name), '[]'::jsonb)
    into v_guru
  from public.halaqah_teachers ht
  join public.profiles p on p.id = ht.profile_id
  join public.halaqahs h on h.id = ht.halaqah_id
  where h.domain = p_domain and h.is_active
  limit 2000;

  select coalesce(jsonb_agg(jsonb_build_object(
           'id', m.id, 'month_no', m.month_no, 'name', m.name, 'hijri_year', ay.hijri_year)
           order by ay.hijri_year, m.month_no), '[]'::jsonb)
    into v_bulan
  from public.hijri_months m
  join public.academic_years ay on ay.id = m.academic_year_id;

  -- Mata pelajaran tiap halaqah: lewat SUMBER TUNGGAL halaqah_mapel_aktif.
  select coalesce(jsonb_agg(jsonb_build_object(
           'halaqah_id', h.id, 'subject_id', mp.subject_id, 'name', mp.name)
           order by h.code, mp.sort_order), '[]'::jsonb)
    into v_mapel
  from public.halaqahs h
  cross join lateral public.halaqah_mapel_aktif(h.id, null) mp
  where h.domain = p_domain and h.is_active;

  select coalesce(jsonb_agg(jsonb_build_object(
           'month_id', ms.month_id, 'effective_days', ms.effective_days, 'terkunci', ms.is_locked)
           order by ms.month_id), '[]'::jsonb)
    into v_setelan
  from public.month_domain_settings ms
  where ms.domain = p_domain;

  return jsonb_build_object(
    'boleh', true,
    'domain', p_domain,
    'halaqah', v_halaqah,
    'guru', v_guru,
    'bulan', v_bulan,
    'mapel', v_mapel,
    'setelan', v_setelan
  );
end $$;

revoke execute on function public.wasilah_input_boot(public.domain_kind) from public, anon;
grant execute on function public.wasilah_input_boot(public.domain_kind) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 7. Pakai sumber tunggal di RPC form (isi form Input Wasilah/Ghayah).
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_input_form(p_halaqah uuid, p_bulan uuid)
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  v_boleh boolean;
  v_domain public.domain_kind;
  v_anggota uuid[];
  v_jml integer;
  v_bulan_no integer;
  v_eff integer;
  v_kunci boolean;
  v_mapel jsonb;
  v_santri jsonb;
  v_capaian jsonb;
  v_terpilih jsonb;
  v_presensi jsonb;
  v_catatan jsonb;
  v_lalu jsonb;
  v_boleh_tulis jsonb;
  v_target_depan jsonb;
begin
  v_boleh := coalesce(public.is_staff(), false)
             or (public.current_app_role() is null
                 and session_user in ('postgres', 'service_role', 'supabase_admin'));
  if not v_boleh then
    return jsonb_build_object('boleh', false);
  end if;

  select h.domain into v_domain from public.halaqahs h where h.id = p_halaqah;
  if v_domain is null then
    raise exception 'Halaqah tidak ditemukan.';
  end if;
  if v_domain not in ('wasilah', 'ghayah') then
    raise exception 'Fungsi ini hanya untuk Ilmu Wasilah atau Ilmu Ghayah.';
  end if;

  select m.month_no into v_bulan_no from public.hijri_months m where m.id = p_bulan;
  if v_bulan_no is null then
    raise exception 'Bulan tidak ditemukan.';
  end if;

  select ms.effective_days, ms.is_locked into v_eff, v_kunci
  from public.month_domain_settings ms
  where ms.month_id = p_bulan and ms.domain = v_domain;

  -- Mata pelajaran halaqah ini: SUMBER TUNGGAL + hak tulis per mapel.
  select coalesce(jsonb_agg(jsonb_build_object(
           'id', mp.subject_id, 'name', mp.name,
           'tuntas', public.mapel_tuntas(p_halaqah, mp.subject_id, p_bulan),
           'boleh_tulis', public.wasilah_can_write(p_halaqah, mp.subject_id))
           order by mp.sort_order, mp.name), '[]'::jsonb)
    into v_mapel
  from public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp;

  select coalesce(jsonb_object_agg(x.id, x.boleh_tulis), '{}'::jsonb)
    into v_boleh_tulis
  from jsonb_to_recordset(v_mapel) as x(id uuid, name text, tuntas boolean, boleh_tulis boolean);

  -- Anggota aktif saja.
  select array_agg(hm.student_id)
    into v_anggota
  from public.halaqah_members hm
  where hm.halaqah_id = p_halaqah and hm.left_on is null;

  v_jml := coalesce(array_length(v_anggota, 1), 0);
  if v_jml > 2000 then
    raise exception 'Anggota halaqah terlalu banyak (%) untuk dimuat sekaligus.', v_jml;
  end if;
  if v_jml = 0 then
    return jsonb_build_object(
      'boleh', true, 'domain', v_domain, 'hari_efektif', v_eff,
      'terkunci', coalesce(v_kunci, false), 'mapel', v_mapel, 'boleh_tulis', v_boleh_tulis,
      'santri', '[]'::jsonb, 'capaian', '[]'::jsonb, 'item_terpilih', '[]'::jsonb,
      'presensi', '[]'::jsonb, 'catatan', '[]'::jsonb, 'lalu', '[]'::jsonb);
  end if;

  select coalesce(jsonb_agg(jsonb_build_object('id', s.id, 'full_name', s.full_name)
                            order by s.full_name, s.id), '[]'::jsonb)
    into v_santri
  from public.students s
  where s.id = any (v_anggota);

  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'item_id', t.item_id,
           'jumlah', t.jumlah, 'variasi', t.variasi) order by t.subject_id), '[]'::jsonb)
    into v_capaian
  from (
    select pe.subject_id,
           (array_agg(pe.item_id order by pe.student_id))[1] as item_id,
           count(*) as jumlah,
           count(distinct pe.item_id) as variasi
    from public.progress_entries pe
    join public.halaqah_subjects hs
      on hs.halaqah_id = p_halaqah and hs.subject_id = pe.subject_id
    where pe.month_id = p_bulan and pe.student_id = any (v_anggota)
    group by pe.subject_id
  ) t;

  with terpilih as (
    select distinct pe.item_id
    from public.progress_entries pe
    join public.curriculum_items ci on ci.id = pe.item_id
    join public.books b on b.id = ci.book_id
    join public.halaqah_subjects hs on hs.halaqah_id = p_halaqah and hs.subject_id = b.subject_id
    where pe.month_id = p_bulan and pe.student_id = any (v_anggota)
  )
  select coalesce(jsonb_agg(jsonb_build_object(
           'id', ci.id, 'subject_id', b.subject_id,
           'label', s.name || ' · ' || ci.label, 'value', ci.value, 'siklik', b.is_cyclic)
           order by s.sort_order, ci.seq, ci.id), '[]'::jsonb)
    into v_terpilih
  from terpilih t
  join public.curriculum_items ci on ci.id = t.item_id
  join public.books b on b.id = ci.book_id
  join public.subjects s on s.id = b.subject_id;

  -- Kehadiran bulan ini (domain ini). Hadir dan Hari Efektif dibaca dari view
  -- `v_attendance` (dihitung database), BUKAN dihitung ulang di React.
  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', v.student_id, 'izin', v.izin, 'sakit', v.sakit, 'alpha', v.alpha,
           'hadir', v.hadir, 'effective_days', v.effective_days,
           'effective_days_override', a.effective_days_override) order by v.student_id), '[]'::jsonb)
    into v_presensi
  from public.v_attendance v
  join public.attendance a
    on a.student_id = v.student_id and a.month_id = v.month_id and a.domain = v.domain
  where v.month_id = p_bulan and v.domain = v_domain and v.student_id = any (v_anggota);

  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', n.student_id, 'note', n.note) order by n.student_id), '[]'::jsonb)
    into v_catatan
  from public.monthly_notes n
  where n.month_id = p_bulan and n.domain = v_domain and n.student_id = any (v_anggota);

  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'item_label', t.item_label, 'pos', t.pos, 'putaran', t.putaran)
           order by t.subject_id), '[]'::jsonb)
    into v_lalu
  from (
    select distinct on (v.subject_id)
           v.subject_id, v.item_label, v.pos, v.putaran
    from public.v_monthly_report v
    join public.v_months_ordered vm on vm.id = p_bulan
    where v.halaqah_id = p_halaqah
      and v.month_id = vm.prev_month_id
      and v.domain = v_domain
    order by v.subject_id, v.student_id
  ) t;

  -- Target yang sudah ada untuk BULAN BERIKUTNYA (dipakai form menampilkan target terpasang).
  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'target_item_id', t.target_item_id,
           'status', t.status) order by t.subject_id), '[]'::jsonb)
    into v_target_depan
  from public.targets t
  join public.v_months_ordered vm on vm.id = p_bulan
  where t.halaqah_id = p_halaqah
    and t.effective_month_id = public.bulan_berikutnya(p_bulan)
    and t.status in ('diajukan', 'disetujui');

  return jsonb_build_object(
    'boleh', true,
    'domain', v_domain,
    'hari_efektif', v_eff,
    'terkunci', coalesce(v_kunci, false),
    'mapel', v_mapel,
    'boleh_tulis', v_boleh_tulis,
    'santri', v_santri,
    'capaian', v_capaian,
    'item_terpilih', v_terpilih,
    'presensi', v_presensi,
    'catatan', v_catatan,
    'lalu', v_lalu,
    'target_depan', v_target_depan
  );
end $$;

revoke execute on function public.wasilah_input_form(uuid, uuid) from public, anon;
grant execute on function public.wasilah_input_form(uuid, uuid) to authenticated, service_role;
