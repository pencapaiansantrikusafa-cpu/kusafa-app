-- ============================================================================
-- T7c [3/3] UI - bagian DATABASE (keputusan Mudir 27 November 2026, jawaban
-- HANDOVER 5.13 = keputusan a):
--
--   * Target bulan depan WAJIB untuk tiap mapel yang CAPAIANNYA sedang
--     disimpan; TIDAK wajib bila untuk mapel itu di bulan berikutnya SUDAH ada
--     target hidup (`diajukan`/`disetujui`); koreksi capaian tidak memaksa
--     mengisi ulang target.
--   * Mapel yang capaiannya tidak dikirim tidak diminta apa pun; kekurangannya
--     ditampilkan lewat notifikasi "belum punya target" (baru).
--   * Jalur simpan LAMA (`wasilah_input_save`, capaian saja) DITUTUP supaya
--     kewajiban target tidak bisa dilewati.
--   * Target di bawah capaian (pengulangan) diterima hanya dengan konfirmasi.
--
-- Semua perubahan adalah `create or replace` (tidak mengubah berkas lama).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Target bulan depan (DIPAKAI simpan gabungan). SECURITY DEFINER.
--    - Butir SAMA dengan target hidup -> tidak menulis apa pun (koreksi capaian
--      tidak membuat target baru).
--    - Butir berbeda: menggantikan target hidup (baris lama -> `dibatalkan`,
--      utuh sebagai riwayat). Menggantikan target SUDAH DISETUJUI hanya boleh
--      Masul domain / Mudir / Admin; pengampu harus lewat halaman Target.
--    Hasil berupa jsonb {id, status, changed, menggantikan}.
-- ----------------------------------------------------------------------------
drop function if exists public.wasilah_target_bulan_depan(uuid, uuid, uuid, uuid, boolean);
create function public.wasilah_target_bulan_depan(
  p_halaqah uuid,
  p_subject uuid,
  p_bulan_depan uuid,
  p_target_item uuid,
  p_konfirmasi boolean default false
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = public, pg_temp
as $$
declare
  v_domain public.domain_kind;
  v_uid uuid := auth.uid();
  v_admin boolean := (
    auth.uid() is null
    and session_user in ('postgres', 'service_role', 'supabase_admin'));
  v_status public.target_status;
  v_id uuid;
  v_lama public.targets%rowtype;
begin
  if v_uid is null and not v_admin then
    raise exception 'Harus masuk untuk menyimpan target.';
  end if;
  select h.domain into v_domain from public.halaqahs h where h.id = p_halaqah;
  if v_domain is null then
    raise exception 'Halaqah tidak ditemukan.';
  end if;
  if v_domain not in ('wasilah', 'ghayah') then
    raise exception 'Fungsi ini hanya untuk Ilmu Wasilah atau Ilmu Ghayah.';
  end if;
  if p_bulan_depan is null then
    raise exception 'Bulan berikutnya tidak ditemukan; target bulan depan tidak dapat disimpan.';
  end if;
  if p_target_item is null then
    raise exception 'Butir target bulan depan belum dipilih.';
  end if;
  if not v_admin
     and not public.target_boleh_ajukan(v_domain, p_subject, null, p_halaqah) then
    raise exception 'Anda tidak berhak mengajukan target untuk halaqah ini.';
  end if;
  -- Butir harus milik mapel itu dan aktif (trigger juga memeriksa).
  if not exists (
    select 1 from public.curriculum_items ci
    join public.books b on b.id = ci.book_id
    where ci.id = p_target_item and b.subject_id = p_subject and ci.is_active
  ) then
    raise exception 'Butir target bukan milik mata pelajaran tersebut (atau sudah nonaktif).';
  end if;

  if v_admin or coalesce(public.is_full_access(), false) or coalesce(public.is_masul_of(v_domain), false) then
    v_status := 'disetujui';
  else
    v_status := 'diajukan';
  end if;

  -- Target hidup terbaru untuk kunci ini (satu target menunggu per kunci).
  select * into v_lama from public.targets
   where halaqah_id = p_halaqah and subject_id = p_subject
     and effective_month_id = p_bulan_depan
     and status in ('diajukan', 'disetujui')
   order by (status = 'disetujui') desc, created_at desc, id desc
   limit 1;

  if found then
    if v_lama.target_item_id = p_target_item then
      return jsonb_build_object('id', v_lama.id, 'status', v_lama.status,
                               'changed', false, 'menggantikan', null);
    end if;
    if v_lama.status = 'disetujui'
       and not (v_admin
                or coalesce(public.is_full_access(), false)
                or coalesce(public.is_masul_of(v_domain), false)) then
      raise exception 'Target bulan depan sudah disetujui. Untuk mengusulkan butir lain, gunakan halaman Target (tombol Ubah).';
    end if;
    update public.targets
       set status = 'dibatalkan', updated_by = v_uid, updated_at = now()
     where halaqah_id = p_halaqah and subject_id = p_subject
       and effective_month_id = p_bulan_depan
       and status in ('diajukan', 'disetujui');
  end if;

  insert into public.targets
    (domain, subject_id, student_id, halaqah_id, effective_month_id,
     amount, amount_period, target_item_id, status, proposed_by)
  values
    (v_domain, p_subject, null, p_halaqah, p_bulan_depan,
     null, 'bulanan', p_target_item, v_status, v_uid)
  returning id into v_id;

  if v_status = 'disetujui' then
    update public.targets set approved_by = v_uid, approved_at = now() where id = v_id;
  end if;

  return jsonb_build_object('id', v_id, 'status', v_status, 'changed', true,
                            'menggantikan', case when v_lama.id is null then null else v_lama.id end);
end $$;

revoke execute on function public.wasilah_target_bulan_depan(uuid, uuid, uuid, uuid, boolean) from public, anon;
grant execute on function public.wasilah_target_bulan_depan(uuid, uuid, uuid, uuid, boolean) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 2. Simpan gabungan (kewajiban target BARU):
--    - wajib target hanya untuk mapel yang ada di p_capaian;
--    - dilewati bila tuntas atau sudah ada target hidup bulan depan;
--    - target di bawah capaian hanya diterima dengan p_konfirmasi = true.
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_simpan_gabungan(
  p_halaqah uuid,
  p_bulan uuid,
  p_capaian jsonb,
  p_target jsonb,
  p_konfirmasi boolean default false
)
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
  v_mapel_aktif integer;
  v_depan uuid;
  v_baris integer := 0;
  v_mapel_capaian integer := 0;
  v_target integer := 0;
  v_tidak_boleh text;
  v_msg text := '';
  v_item uuid;
  v_tuntas boolean;
  v_sudah boolean;
  v_pos_capaian integer;
  v_pos_target integer;
  v_nama text;
  v_bawah jsonb := '[]'::jsonb;
  v_bawah_nama text := '';
  v_hasil jsonb;
  r record;
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
  if v_bulan_no = 0 then
    raise exception 'Bulan Data Awal bukan bulan input. Data Awal hanya diisi Admin/Mudir.';
  end if;

  select coalesce(ms.is_locked, false) into v_kunci
  from public.month_domain_settings ms
  where ms.month_id = p_bulan and ms.domain = v_domain;
  if coalesce(v_kunci, false) and not coalesce(public.is_full_access(), false) then
    raise exception 'Bulan ini sudah dikunci. Hanya Mudir atau Admin yang dapat mengubahnya.';
  end if;

  if p_capaian is not null and jsonb_typeof(p_capaian) <> 'array' then
    raise exception 'Data capaian tidak dikenali.';
  end if;
  if p_target is not null and jsonb_typeof(p_target) <> 'array' then
    raise exception 'Data target tidak dikenali.';
  end if;

  -- Level 6: halaqah tanpa mapel aktif -> tuntas, tidak menulis apa pun.
  select count(*) into v_mapel_aktif from public.halaqah_mapel_aktif(p_halaqah, p_bulan);
  if v_mapel_aktif = 0 then
    return jsonb_build_object(
      'tersimpan', true, 'tanpa_mapel', true, 'mapel_capaian', 0, 'target', 0, 'baris', 0,
      'mapel', 0, 'anggota', 0,
      'pesan', 'Tuntas, belum ada pelajaran lanjutan');
  end if;

  select array_agg(hm.student_id) into v_anggota
  from public.halaqah_members hm
  where hm.halaqah_id = p_halaqah and hm.left_on is null;
  v_jml := coalesce(array_length(v_anggota, 1), 0);
  if v_jml = 0 then
    raise exception 'Halaqah ini belum punya anggota aktif.';
  end if;

  v_depan := public.bulan_berikutnya(p_bulan);

  -- (1) Periksa SEMUA baris capaian (mapel aktif, item milik mapel, hak tulis).
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'item_id')::uuid as item_id
    from jsonb_array_elements(coalesce(p_capaian, '[]'::jsonb)) as x
  loop
    if r.subject_id is null or r.item_id is null then
      raise exception 'Data capaian tidak lengkap (mata pelajaran atau item kosong).';
    end if;
    if not exists (select 1 from public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp
                   where mp.subject_id = r.subject_id) then
      raise exception 'Mata pelajaran itu tidak aktif untuk halaqah ini.';
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

  -- (2) Periksa baris target (mapel aktif, butir milik mapel, hak tulis).
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'target_item_id')::uuid as target_item_id
    from jsonb_array_elements(coalesce(p_target, '[]'::jsonb)) as x
  loop
    if r.subject_id is null or r.target_item_id is null then
      raise exception 'Data target tidak lengkap (mata pelajaran atau butir kosong).';
    end if;
    if not exists (select 1 from public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp
                   where mp.subject_id = r.subject_id) then
      raise exception 'Mata pelajaran target tidak aktif untuk halaqah ini.';
    end if;
    if not exists (select 1 from public.curriculum_items ci
                   join public.books b on b.id = ci.book_id
                   where ci.id = r.target_item_id and b.subject_id = r.subject_id and ci.is_active) then
      raise exception 'Butir target bukan milik mata pelajaran tersebut (atau sudah nonaktif).';
    end if;
    if not public.wasilah_can_write(p_halaqah, r.subject_id) then
      select string_agg(s.name, ', ') into v_tidak_boleh
      from public.subjects s where s.id = r.subject_id;
      raise exception 'Anda tidak mengampu mata pelajaran % di halaqah ini.', coalesce(v_tidak_boleh, 'itu');
    end if;
  end loop;

  -- (3) Kewajiban target: HANYA mapel yang capaiannya dikirim; lewati tuntas
  --     dan mapel yang sudah punya target hidup bulan depan.
  if v_depan is not null then
    for r in select mp.subject_id, mp.name from public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp
             where public.wasilah_can_write(p_halaqah, mp.subject_id)
    loop
      if not exists (
        select 1 from jsonb_array_elements(coalesce(p_capaian, '[]'::jsonb)) x
        where (x->>'subject_id')::uuid = r.subject_id
      ) then
        continue;
      end if;

      select (x->>'item_id')::uuid into v_item
      from jsonb_array_elements(coalesce(p_capaian, '[]'::jsonb)) x
      where (x->>'subject_id')::uuid = r.subject_id
      limit 1;
      v_tuntas := (v_item is not null and v_item = public.mapel_butir_terakhir(r.subject_id));

      select exists (
        select 1 from public.targets t
        where t.halaqah_id = p_halaqah and t.subject_id = r.subject_id
          and t.effective_month_id = v_depan
          and t.status in ('diajukan', 'disetujui')
      ) into v_sudah;

      if not v_tuntas and not v_sudah and not exists (
        select 1 from jsonb_array_elements(coalesce(p_target, '[]'::jsonb)) x
        where (x->>'subject_id')::uuid = r.subject_id
          and nullif(x->>'target_item_id', '') is not null
      ) then
        v_msg := v_msg || r.name || ', ';
      end if;
    end loop;
    if v_msg <> '' then
      raise exception 'Target bulan depan belum diisi untuk mata pelajaran: % (kecuali yang sudah tuntas atau sudah punya target).',
        rtrim(v_msg, ', ');
    end if;
  elsif jsonb_array_length(coalesce(p_target, '[]'::jsonb)) > 0 then
    raise exception 'Tidak ada bulan berikutnya; target bulan depan tidak dapat disimpan.';
  end if;

  -- (4) Peringatan target di bawah capaian (pengulangan): periksa SEBELUM menulis.
  --     Posisi dibaca dari fungsi database, bukan dihitung React.
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'target_item_id')::uuid as target_item_id
    from jsonb_array_elements(coalesce(p_target, '[]'::jsonb)) as x
  loop
    select (x->>'item_id')::uuid into v_item
    from jsonb_array_elements(coalesce(p_capaian, '[]'::jsonb)) x
    where (x->>'subject_id')::uuid = r.subject_id
    limit 1;
    if v_item is null then
      select (array_agg(pe.item_id order by pe.student_id))[1] into v_item
      from public.progress_entries pe
      where pe.subject_id = r.subject_id and pe.month_id = p_bulan
        and pe.student_id = any (v_anggota);
    end if;
    if v_item is not null then
      v_pos_capaian := public.item_position(v_item, 1);
      v_pos_target := public.item_position(r.target_item_id, 1);
      if v_pos_target < v_pos_capaian then
        select name into v_nama from public.subjects where id = r.subject_id;
        v_bawah := v_bawah || jsonb_build_array(jsonb_build_object(
          'subject_id', r.subject_id, 'name', v_nama,
          'pos_capaian', v_pos_capaian, 'pos_target', v_pos_target));
        v_bawah_nama := v_bawah_nama || coalesce(v_nama, 'mata pelajaran') || ', ';
      end if;
    end if;
  end loop;
  if v_bawah_nama <> '' and not coalesce(p_konfirmasi, false) then
    raise exception 'Target bulan depan di bawah capaian (pengulangan) untuk mata pelajaran: %. Centang konfirmasi untuk melanjutkan.',
      rtrim(v_bawah_nama, ', ');
  end if;

  -- (5) Tulis capaian (salin ke semua anggota aktif), satu baris per anggota per mapel.
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'item_id')::uuid as item_id
    from jsonb_array_elements(coalesce(p_capaian, '[]'::jsonb)) as x
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
    v_mapel_capaian := v_mapel_capaian + 1;
  end loop;

  -- (6) Tulis target bulan depan lewat fungsi DEFINER (cek hak di dalamnya).
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'target_item_id')::uuid as target_item_id
    from jsonb_array_elements(coalesce(p_target, '[]'::jsonb)) as x
  loop
    v_hasil := public.wasilah_target_bulan_depan(p_halaqah, r.subject_id, v_depan, r.target_item_id, p_konfirmasi);
    if coalesce((v_hasil->>'changed')::boolean, false) then
      v_target := v_target + 1;
    end if;
  end loop;

  return jsonb_build_object(
    'tersimpan', true,
    'tanpa_mapel', false,
    'bulan_depan', v_depan,
    'baris', v_baris,
    'mapel', v_mapel_capaian,
    'anggota', v_jml,
    'mapel_capaian', v_mapel_capaian,
    'target', v_target,
    'di_bawah_capaian', v_bawah
  );
end $$;

revoke execute on function public.wasilah_simpan_gabungan(uuid, uuid, jsonb, jsonb, boolean) from public, anon;
grant execute on function public.wasilah_simpan_gabungan(uuid, uuid, jsonb, jsonb, boolean) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 3. Form Input: tambah target bulan ini, target bulan depan (label + posisi),
--    posisi capaian, penanda tuntas per mapel, dan Level 6.
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
  v_target_ini jsonb;
  v_bulan_depan jsonb;
  v_depan uuid;
  v_tanpa_mapel boolean;
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

  v_depan := public.bulan_berikutnya(p_bulan);
  v_tanpa_mapel := public.halaqah_tanpa_mapel(p_halaqah);

  select to_jsonb(x) into v_bulan_depan
  from public.v_months_ordered x where x.id = v_depan;

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
      'presensi', '[]'::jsonb, 'catatan', '[]'::jsonb, 'lalu', '[]'::jsonb,
      'target_depan', '[]'::jsonb, 'target_ini', '[]'::jsonb,
      'bulan_depan', v_bulan_depan, 'tanpa_mapel', v_tanpa_mapel);
  end if;

  select coalesce(jsonb_agg(jsonb_build_object('id', s.id, 'full_name', s.full_name)
                            order by s.full_name, s.id), '[]'::jsonb)
    into v_santri
  from public.students s
  where s.id = any (v_anggota);

  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'item_id', t.item_id, 'pos', t.pos,
           'jumlah', t.jumlah, 'variasi', t.variasi) order by t.subject_id), '[]'::jsonb)
    into v_capaian
  from (
    select pe.subject_id,
           (array_agg(pe.item_id order by pe.student_id))[1] as item_id,
           public.item_position((array_agg(pe.item_id order by pe.student_id))[1], 1) as pos,
           count(*) as jumlah,
           count(distinct pe.item_id) as variasi
    from public.progress_entries pe
    join public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp on mp.subject_id = pe.subject_id
    where pe.month_id = p_bulan and pe.student_id = any (v_anggota)
    group by pe.subject_id
  ) t;

  with terpilih as (
    select distinct pe.item_id
    from public.progress_entries pe
    join public.curriculum_items ci on ci.id = pe.item_id
    join public.books b on b.id = ci.book_id
    join public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp on mp.subject_id = b.subject_id
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

  -- Target yang sudah ada untuk BULAN INI (dibuat saat input bulan lalu).
  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'target_item_id', t.target_item_id,
           'status', t.status, 'item_label', t.item_label, 'pos', t.pos)
           order by t.subject_id), '[]'::jsonb)
    into v_target_ini
  from (
    select distinct on (t.subject_id)
           t.subject_id, t.target_item_id, t.status,
           s.name || ' · ' || ci.label as item_label,
           public.item_position(t.target_item_id, 1) as pos
    from public.targets t
    join public.subjects s on s.id = t.subject_id
    join public.curriculum_items ci on ci.id = t.target_item_id
    where t.halaqah_id = p_halaqah and t.effective_month_id = p_bulan
      and t.status in ('diajukan', 'disetujui')
    order by t.subject_id, (t.status = 'disetujui') desc, t.created_at desc, t.id desc
  ) t;

  -- Target yang sudah ada untuk BULAN BERIKUTNYA (ditampilkan & boleh diubah).
  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'target_item_id', t.target_item_id,
           'status', t.status, 'item_label', t.item_label, 'pos', t.pos)
           order by t.subject_id), '[]'::jsonb)
    into v_target_depan
  from (
    select distinct on (t.subject_id)
           t.subject_id, t.target_item_id, t.status,
           s.name || ' · ' || ci.label as item_label,
           public.item_position(t.target_item_id, 1) as pos
    from public.targets t
    join public.subjects s on s.id = t.subject_id
    join public.curriculum_items ci on ci.id = t.target_item_id
    where t.halaqah_id = p_halaqah and t.effective_month_id = v_depan
      and t.status in ('diajukan', 'disetujui')
    order by t.subject_id, (t.status = 'disetujui') desc, t.created_at desc, t.id desc
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
    'lalu', v_lalu,
    'target_depan', v_target_depan,
    'target_ini', v_target_ini,
    'bulan_depan', v_bulan_depan,
    'tanpa_mapel', v_tanpa_mapel
  );
end $$;

revoke execute on function public.wasilah_input_form(uuid, uuid) from public, anon;
grant execute on function public.wasilah_input_form(uuid, uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 4. TUTUP jalur simpan lama (capaian saja). Signature dipertahankan agar
--    pemanggil lama mendapat pesan jelas, bukan galat "fungsi tidak ada".
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_input_save(p_halaqah uuid, p_bulan uuid, p_items jsonb)
returns jsonb
language plpgsql
volatile
security invoker
set search_path = public, pg_temp
as $$
begin
  raise exception 'Jalur simpan lama sudah ditutup. Simpan capaian dan target bulan depan sekaligus lewat wasilah_simpan_gabungan.';
end $$;

revoke execute on function public.wasilah_input_save(uuid, uuid, jsonb) from public, anon;
grant execute on function public.wasilah_input_save(uuid, uuid, jsonb) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 5. Notifikasi "belum punya target" (semantik baru) + tuntas/Level 6.
--    Satu baris per (halaqah x mapel aktif). `level6` = halaqah tanpa mapel.
--    Hanya Masul domain terkait / Mudir / Admin yang mendapat baris.
-- ----------------------------------------------------------------------------
create or replace function public.target_belum_domain(p_domain public.domain_kind, p_bulan uuid)
returns table (
  halaqah_id uuid,
  halaqah_code text,
  subject_id uuid,
  subject_name text,
  tuntas boolean,
  level6 boolean,
  ada_disetujui boolean,
  ada_diajukan boolean
)
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  with izin as (
    select (coalesce(public.is_full_access(), false)
            or coalesce(public.is_masul_of(p_domain), false)) as boleh
  ),
  h as (
    select hh.id, hh.code from public.halaqahs hh
    where hh.domain = p_domain and hh.is_active
  ),
  depan as (select public.bulan_berikutnya(p_bulan) as id),
  baris as (
    select h.id as halaqah_id, h.code as halaqah_code,
           mp.subject_id, mp.name as subject_name,
           public.mapel_tuntas(h.id, mp.subject_id, p_bulan) as tuntas,
           false as level6
    from h
    cross join lateral public.halaqah_mapel_aktif(h.id, p_bulan) mp
  )
  select b.halaqah_id, b.halaqah_code, b.subject_id, b.subject_name,
         b.tuntas, b.level6,
         exists (select 1 from public.targets t
                  where t.halaqah_id = b.halaqah_id and t.subject_id = b.subject_id
                    and t.effective_month_id = (select id from depan)
                    and t.status = 'disetujui') as ada_disetujui,
         exists (select 1 from public.targets t
                  where t.halaqah_id = b.halaqah_id and t.subject_id = b.subject_id
                    and t.effective_month_id = (select id from depan)
                    and t.status = 'diajukan') as ada_diajukan
  from baris b
  where (select boleh from izin)
  union all
  select h.id, h.code, null, null, false, true, false, false
  from h
  where (select boleh from izin) and public.halaqah_tanpa_mapel(h.id)
$$;

revoke execute on function public.target_belum_domain(public.domain_kind, uuid) from public, anon;
grant execute on function public.target_belum_domain(public.domain_kind, uuid) to authenticated, service_role;
