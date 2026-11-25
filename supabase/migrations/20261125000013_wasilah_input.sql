-- ============================================================================
-- T6b: input capaian Ilmu Wasilah dan Ilmu Ghayah.
--
-- Aturan bisnis (docs/SPEC.md bagian 2 dan 5.6):
--   Input Wasilah/Ghayah dilakukan SEKALI per halaqah x mata pelajaran, lalu
--   disalin ke tiap anggota halaqah yang masih aktif. Perubahan anggota sesudahnya
--   tidak mengubah baris lama (baris capaian tidak pernah dihapus di sini).
--
-- Tiga fungsi:
--   1. wasilah_input_boot(domain)   -> pembukaan halaman: halaqah + pengampu + bulan
--                                      + mata pelajaran per halaqah + Hari Efektif.
--   2. wasilah_input_form(halaqah, bulan) -> isi form: anggota, capaian tersimpan,
--                                      item terpilih, bulan lalu, kehadiran, catatan.
--   3. wasilah_input_save(halaqah, bulan, items) -> tulis sekali untuk semua anggota,
--                                      dalam SATU transaksi (semua atau tidak sama sekali).
--
-- Yang TIDAK dihitung di sini: posisi, selisih, Hadir, dan target. Ketiganya tetap
-- dibaca dari `v_monthly_report` / `v_attendance` (fungsi ini hanya mengumpulkan
-- baris yang sudah dihitung database).
--
-- Keamanan:
--   - SECURITY INVOKER, jadi RLS tabel tetap berlaku.
--   - Setiap fungsi memeriksa `public.is_staff()`; anon tidak punya EXECUTE sama sekali.
--   - Pola koneksi admin tanpa JWT (postgres/service_role/supabase_admin) diizinkan
--     untuk skrip lokal, sama seperti migrasi 000009/000011/000012.
--   - Hak tulis per mata pelajaran tetap dinilai database: `is_full_access()` atau
--     `teaches_halaqah_subject(halaqah, subject)`. Bila satu mata pelajaran saja tidak
--     boleh ditulis, SELURUH penyimpanan ditolak (tidak ada penyimpanan sebagian).
--   - Bulan 0 (Data Awal) selalu ditolak. Bulan terkunci hanya boleh diubah
--     Mudir/Admin (`is_full_access()`), sesuai SPEC bagian 3.
--
-- Batas ukuran: anggota halaqah dibatasi 2.000 (data dummy terbesar 13).
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

-- ----------------------------------------------------------------------------
-- 0. Penentu hak tulis capaian Wasilah/Ghayah untuk satu halaqah + mata pelajaran.
--    Mudir/Admin: semua. Pengampu: hanya mapel yang diampu di halaqah itu.
--    Koneksi admin tanpa JWT (skrip lokal/service_role) diizinkan, pola migrasi 000009.
--    SECURITY INVOKER + hanya membaca fungsi bantu yang sudah ada.
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_can_write(p_halaqah uuid, p_subject uuid)
returns boolean
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select coalesce(public.is_full_access(), false)
         or coalesce(public.teaches_halaqah_subject(p_halaqah, p_subject), false)
         or (public.current_app_role() is null
             and session_user in ('postgres', 'service_role', 'supabase_admin'))
$$;

revoke execute on function public.wasilah_can_write(uuid, uuid) from public, anon;
grant execute on function public.wasilah_can_write(uuid, uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 1. Pembukaan halaman Input Wasilah/Ghayah.
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

  -- Pengampu beserta mata pelajaran yang diampu (subject_id null = semua mapel halaqah).
  -- `name` tidak dikirim: dropdown memakai kode + nama pengampu (pelajaran T5c-2).
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

  -- Mata pelajaran yang ditetapkan untuk tiap halaqah (halaqah_subjects).
  select coalesce(jsonb_agg(jsonb_build_object(
           'halaqah_id', hs.halaqah_id, 'subject_id', s.id, 'name', s.name)
           order by hs.halaqah_id, s.sort_order), '[]'::jsonb)
    into v_mapel
  from public.halaqah_subjects hs
  join public.subjects s on s.id = hs.subject_id
  join public.halaqahs h on h.id = hs.halaqah_id
  where h.domain = p_domain and h.is_active and s.is_active;

  -- Hari Efektif + kunci per bulan (boleh kosong bila belum diisi; DUMMY untuk Wasilah/Ghayah).
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
-- 2. Isi form untuk satu halaqah + bulan.
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

  -- Mata pelajaran halaqah ini + apakah pemanggil boleh menulisnya.
  select coalesce(jsonb_agg(jsonb_build_object(
           'id', s.id, 'name', s.name,
           'boleh_tulis', public.wasilah_can_write(p_halaqah, s.id))
           order by s.sort_order, s.name), '[]'::jsonb)
    into v_mapel
  from public.halaqah_subjects hs
  join public.subjects s on s.id = hs.subject_id
  where hs.halaqah_id = p_halaqah and s.is_active;

  -- Peta boleh-tulis per mapel (dipakai halaman untuk mengunci dropdown).
  select coalesce(jsonb_object_agg(x.id, x.boleh_tulis), '{}'::jsonb)
    into v_boleh_tulis
  from jsonb_to_recordset(v_mapel) as x(id uuid, name text, boleh_tulis boolean);

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

  -- Capaian bulan ini. Input disalin ke semua anggota, jadi nilainya sama; bila berbeda
  -- (mis. anggota baru ditambahkan setelah input), `variasi` > 1 dan halaman memberi tanda.
  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'item_id', t.item_id,
           'jumlah', t.jumlah, 'variasi', t.variasi) order by t.subject_id), '[]'::jsonb)
    into v_capaian
  from (
    -- PostgreSQL tidak punya min(uuid); dipakai (array_agg(... order by ...))[1].
    -- Disaring ke mata pelajaran halaqah ini: santri yang sama juga punya capaian
    -- Al Qur'an pada bulan yang sama, dan itu TIDAK boleh ikut terbaca di sini.
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

  -- Detail item terpilih (label berawalan nama mata pelajaran, sesuai aturan tampilan).
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

  -- Kehadiran bulan ini (domain ini).
  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', a.student_id, 'izin', a.izin, 'sakit', a.sakit, 'alpha', a.alpha,
           'effective_days_override', a.effective_days_override) order by a.student_id), '[]'::jsonb)
    into v_presensi
  from public.attendance a
  where a.month_id = p_bulan and a.domain = v_domain and a.student_id = any (v_anggota);

  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', n.student_id, 'note', n.note) order by n.student_id), '[]'::jsonb)
    into v_catatan
  from public.monthly_notes n
  where n.month_id = p_bulan and n.domain = v_domain and n.student_id = any (v_anggota);

  -- Bulan lalu: diambil dari view (posisi & teks dihitung database). Satu baris per mapel
  -- diwakili anggota pertama; `prev_item_label` sama untuk semua anggota.
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
    'lalu', v_lalu
  );
end $$;

revoke execute on function public.wasilah_input_form(uuid, uuid) from public, anon;
grant execute on function public.wasilah_input_form(uuid, uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 3. Simpan sekali per halaqah x mata pelajaran, disalin ke semua anggota aktif.
--    p_items = jsonb array: [{"subject_id": uuid, "item_id": uuid}, ...]
--    Semua atau tidak sama sekali: satu mata pelajaran ditolak => seluruhnya batal.
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_input_save(p_halaqah uuid, p_bulan uuid, p_items jsonb)
returns jsonb
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
declare
  v_boleh boolean;
  v_domain public.domain_kind;
  v_bulan_no integer;
  v_kunci boolean;
  v_anggota uuid[];
  v_jml integer;
  v_baris integer := 0;
  v_mapel integer := 0;
  r record;
  v_tidak_boleh text;
begin
  v_boleh := coalesce(public.is_staff(), false)
             or (public.current_app_role() is null
                 and session_user in ('postgres', 'service_role', 'supabase_admin'));
  if not v_boleh then
    raise exception 'Profil akun belum aktif atau tidak punya akses untuk menyimpan.';
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
  -- Bulan 0 (Data Awal) bukan bulan input staf (SPEC 4a).
  if v_bulan_no = 0 then
    raise exception 'Bulan Data Awal bukan bulan input. Data Awal hanya diisi Admin/Mudir.';
  end if;

  select coalesce(ms.is_locked, false) into v_kunci
  from public.month_domain_settings ms
  where ms.month_id = p_bulan and ms.domain = v_domain;
  if coalesce(v_kunci, false) and not coalesce(public.is_full_access(), false) then
    raise exception 'Bulan ini sudah dikunci. Hanya Mudir atau Admin yang dapat mengubahnya.';
  end if;

  if p_items is null or jsonb_typeof(p_items) <> 'array' then
    raise exception 'Data capaian tidak dikenali.';
  end if;

  select array_agg(hm.student_id)
    into v_anggota
  from public.halaqah_members hm
  where hm.halaqah_id = p_halaqah and hm.left_on is null;
  v_jml := coalesce(array_length(v_anggota, 1), 0);
  if v_jml = 0 then
    raise exception 'Halaqah ini belum punya anggota aktif.';
  end if;

  -- Periksa SEMUA baris dulu (mapel milik halaqah, item milik mapel itu, hak tulis),
  -- baru menulis. Dengan begitu tidak ada penyimpanan sebagian.
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'item_id')::uuid as item_id
    from jsonb_array_elements(p_items) as x
  loop
    if r.subject_id is null or r.item_id is null then
      raise exception 'Data capaian tidak lengkap (mata pelajaran atau item kosong).';
    end if;
    if not exists (select 1 from public.halaqah_subjects hs
                   where hs.halaqah_id = p_halaqah and hs.subject_id = r.subject_id) then
      raise exception 'Mata pelajaran itu tidak ditetapkan untuk halaqah ini.';
    end if;
    if not exists (select 1 from public.curriculum_items ci
                   join public.books b on b.id = ci.book_id
                   where ci.id = r.item_id and b.subject_id = r.subject_id) then
      raise exception 'Item yang dipilih bukan milik mata pelajaran tersebut.';
    end if;
    if not public.wasilah_can_write(p_halaqah, r.subject_id) then
      select string_agg(s.name, ', ') into v_tidak_boleh
      from public.subjects s where s.id = r.subject_id;
      raise exception 'Anda tidak mengampu mata pelajaran % di halaqah ini.', coalesce(v_tidak_boleh, 'itu');
    end if;
  end loop;

  -- Tulis: satu baris per anggota aktif untuk tiap mata pelajaran yang dikirim.
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'item_id')::uuid as item_id
    from jsonb_array_elements(p_items) as x
  loop
    insert into public.progress_entries (student_id, halaqah_id, subject_id, month_id, item_id, putaran)
    select a, p_halaqah, r.subject_id, p_bulan, r.item_id, 1
    from unnest(v_anggota) as a
    on conflict (student_id, subject_id, month_id) do update
      set item_id = excluded.item_id,
          halaqah_id = excluded.halaqah_id,
          putaran = excluded.putaran,
          entered_at = now();
    v_baris := v_baris + v_jml;
    v_mapel := v_mapel + 1;
  end loop;

  return jsonb_build_object(
    'tersimpan', true,
    'mapel', v_mapel,
    'anggota', v_jml,
    'baris', v_baris
  );
end $$;

revoke execute on function public.wasilah_input_save(uuid, uuid, jsonb) from public, anon;
grant execute on function public.wasilah_input_save(uuid, uuid, jsonb) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- Verifikasi setelah migrasi (jalankan sebagai admin/koneksi tanpa JWT):
--   select jsonb_pretty(public.wasilah_input_boot('wasilah'))->'mapel';
--   select public.wasilah_input_form(
--     (select id from public.halaqahs where domain='wasilah' order by code limit 1),
--     (select m.id from public.hijri_months m where m.month_no=6))->'mapel';
--   sebagai anon: ditolak 42501; authenticated tanpa profil: {"boleh": false}.
-- ----------------------------------------------------------------------------
