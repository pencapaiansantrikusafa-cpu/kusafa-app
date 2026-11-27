-- ============================================================================
-- T7c [2/3] BACKEND (perintah Mudir, 27 November 2026) - bagian 2.
--
-- Simpan GABUNGAN untuk Ilmu Wasilah / Ilmu Ghayah dalam SATU transaksi:
--   - capaian bulan ini (alur T6b yang ada: sekali per halaqah x mapel, disalin
--     ke semua anggota aktif), DAN
--   - target BULAN DEPAN (tujuan akhir = butir kurikulum) untuk tiap mapel aktif.
--
-- Aturan (SPEC 3.2a):
--   * Gagal satu -> batal semua (satu panggilan fungsi = satu transaksi).
--   * SERVER menolak bila ada mapel aktif yang belum punya target bulan depan,
--     KECUALI mapel itu sudah TUNTAS (butir terakhir buku terakhir).
--   * Bulan berikutnya = bulan setelah bulan terpilih (v_months_ordered). Bila
--     tidak ada bulan berikutnya, target TIDAK diminta.
--   * Pengampu -> target berstatus 'diajukan'; Masul domain / Mudir / Admin ->
--     langsung 'disetujui'.
--   * Target di bawah capaian DITERIMA (pengulangan); RPC mengembalikan daftar
--     "di_bawah_capaian" agar UI memberi peringatan.
--   * Halaqah tanpa mapel (Level 6) = "Tuntas, belum ada pelajaran lanjutan";
--     tidak menulis apa pun.
--
-- Keamanan:
--   - `wasilah_simpan_gabungan` SECURITY INVOKER (RLS progress_entries tetap
--     penjaga kedua), seperti wasilah_input_save.
--   - Tulis target WAJIB lewat `wasilah_target_bulan_depan` SECURITY DEFINER
--     (tabel targets menutup tulis langsung), dengan cek hak internal.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- A. Data tuntas untuk notifikasi Masul domainnya (butir terakhir buku terakhir).
--    Level 6 (tanpa mapel) ditandai `tanpa_mapel = true`.
-- ----------------------------------------------------------------------------
create or replace function public.halaqah_status_tuntas(p_halaqah uuid, p_bulan uuid)
returns jsonb
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'tanpa_mapel', public.halaqah_tanpa_mapel(p_halaqah),
    'mapel', coalesce((
      select jsonb_agg(jsonb_build_object(
               'subject_id', mp.subject_id, 'name', mp.name,
               'tuntas', public.mapel_tuntas(p_halaqah, mp.subject_id, p_bulan))
             order by mp.sort_order)
      from public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp
    ), '[]'::jsonb),
    'tuntas_penuh', (
      not public.halaqah_tanpa_mapel(p_halaqah)
      and not exists (
        select 1 from public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp
        where not public.mapel_tuntas(p_halaqah, mp.subject_id, p_bulan))
    )
  )
$$;

revoke execute on function public.halaqah_status_tuntas(uuid, uuid) from public, anon;
grant execute on function public.halaqah_status_tuntas(uuid, uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- B. Tulis SATU target bulan depan (dipakai simpan gabungan). SECURITY DEFINER
--    karena tabel `targets` menutup tulis langsung. Semua cek di dalam fungsi.
--    Mengembalikan id target yang dibuat.
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_target_bulan_depan(
  p_halaqah uuid,
  p_subject uuid,
  p_bulan_depan uuid,
  p_target_item uuid,
  p_konfirmasi boolean default false
)
returns uuid
language plpgsql
volatile
security definer
set search_path = public, pg_temp
as $$
declare
  v_domain public.domain_kind;
  v_uid uuid := auth.uid();
  v_status public.target_status;
  v_id uuid;
begin
  if v_uid is null then
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
  -- Boleh mengajukan? (pengampu halaqah/mapel, Masul domainnya, Mudir/Admin)
  if not public.target_boleh_ajukan(v_domain, p_subject, null, p_halaqah) then
    raise exception 'Anda tidak berhak mengajukan target untuk halaqah ini.';
  end if;
  -- Butir harus milik mapel itu dan aktif (trigger juga memeriksa; pesan di sini lebih jelas).
  if not exists (
    select 1 from public.curriculum_items ci
    join public.books b on b.id = ci.book_id
    where ci.id = p_target_item and b.subject_id = p_subject and ci.is_active
  ) then
    raise exception 'Butir target bukan milik mata pelajaran tersebut (atau sudah nonaktif).';
  end if;

  -- Pengampu -> diajukan; Masul domain / Mudir / Admin -> langsung disetujui.
  if coalesce(public.is_full_access(), false) or coalesce(public.is_masul_of(v_domain), false) then
    v_status := 'disetujui';
  else
    v_status := 'diajukan';
  end if;

  -- Pengajuan baru menggantikan yang masih 'diajukan' pada (halaqah, mapel, bulan) yang sama.
  update public.targets
     set status = 'dibatalkan', updated_by = v_uid, updated_at = now()
   where halaqah_id = p_halaqah
     and subject_id = p_subject
     and effective_month_id = p_bulan_depan
     and status = 'diajukan';

  insert into public.targets
    (domain, subject_id, student_id, halaqah_id, effective_month_id,
     amount, amount_period, target_item_id, status)
  values
    (v_domain, p_subject, null, p_halaqah, p_bulan_depan,
     null, 'bulanan', p_target_item, v_status)
  returning id into v_id;

  if v_status = 'disetujui' then
    update public.targets set approved_by = v_uid, approved_at = now() where id = v_id;
  end if;

  return v_id;
end $$;

revoke execute on function public.wasilah_target_bulan_depan(uuid, uuid, uuid, uuid, boolean) from public, anon;
grant execute on function public.wasilah_target_bulan_depan(uuid, uuid, uuid, uuid, boolean) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- C. Simpan gabungan: capaian bulan ini + target bulan depan (satu transaksi).
--    p_capaian = [{subject_id, item_id}, ...]
--    p_target  = [{subject_id, target_item_id}, ...]
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
  r record;
  v_bawah jsonb;
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

  -- (2) Kewajiban target bulan depan (kecuali mapel tuntas / tidak ada bulan depan).
  --     Yang wajib = tiap mapel aktif YANG BOLEH DITULIS pemanggil (Masul/Mudir/Admin:
  --     semua mapel; pengampu: mapel yang diampu). Pengampu tidak dipaksa mengisi
  --     target mapel yang bukan tanggung jawabnya. (Asumsi, dicatat di HANDOVER.)
  if v_depan is not null then
    for r in select mp.subject_id, mp.name from public.halaqah_mapel_aktif(p_halaqah, p_bulan) mp
             where public.wasilah_can_write(p_halaqah, mp.subject_id)
    loop
      -- item capaian efektif bulan ini: baris yang DIKIRIM diutamakan, lalu yang tersimpan.
      select (x->>'item_id')::uuid into v_item
      from jsonb_array_elements(coalesce(p_capaian, '[]'::jsonb)) as x
      where (x->>'subject_id')::uuid = r.subject_id
      limit 1;
      if v_item is null then
        select (array_agg(pe.item_id order by pe.student_id))[1] into v_item
        from public.progress_entries pe
        where pe.subject_id = r.subject_id and pe.month_id = p_bulan
          and pe.student_id = any (v_anggota);
      end if;
      v_tuntas := (v_item is not null and v_item = public.mapel_butir_terakhir(r.subject_id));
      if not v_tuntas and not exists (
        select 1 from jsonb_array_elements(coalesce(p_target, '[]'::jsonb)) as x
        where (x->>'subject_id')::uuid = r.subject_id
          and nullif(x->>'target_item_id', '') is not null
      ) then
        v_msg := v_msg || r.name || ', ';
      end if;
    end loop;
    if v_msg <> '' then
      raise exception 'Target bulan depan belum diisi untuk mata pelajaran: % (kecuali yang sudah tuntas).',
        rtrim(v_msg, ', ');
    end if;
  elsif jsonb_array_length(coalesce(p_target, '[]'::jsonb)) > 0 then
    raise exception 'Tidak ada bulan berikutnya; target bulan depan tidak dapat disimpan.';
  end if;

  -- (3) Periksa baris target (mapel aktif, butir milik mapel). Pesan jelas sebelum menulis.
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
  end loop;

  -- (4) Tulis capaian (salin ke semua anggota aktif), satu baris per anggota per mapel.
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

  -- (5) Tulis target bulan depan lewat fungsi DEFINER (cek hak di dalamnya).
  for r in
    select (x->>'subject_id')::uuid as subject_id, (x->>'target_item_id')::uuid as target_item_id
    from jsonb_array_elements(coalesce(p_target, '[]'::jsonb)) as x
  loop
    perform public.wasilah_target_bulan_depan(p_halaqah, r.subject_id, v_depan, r.target_item_id, p_konfirmasi);
    v_target := v_target + 1;
  end loop;

  -- (6) Data peringatan: target di bawah capaian (pengulangan) — diterima, UI memperingatkan.
  select coalesce(jsonb_agg(jsonb_build_object(
           'subject_id', t.subject_id, 'name', sub.name,
           'pos_capaian', public.item_position(pe.item_id, pe.putaran),
           'pos_target', public.item_position(t.target_item_id, 1))), '[]'::jsonb)
    into v_bawah
  from public.targets t
  join public.subjects sub on sub.id = t.subject_id
  join lateral (
    select pe2.item_id, pe2.putaran from public.progress_entries pe2
    where pe2.subject_id = t.subject_id and pe2.month_id = p_bulan
      and pe2.student_id = any (v_anggota)
    order by pe2.student_id limit 1
  ) pe on true
  where t.halaqah_id = p_halaqah and t.effective_month_id = v_depan
    and t.status = 'disetujui'
    and public.item_position(t.target_item_id, 1) < public.item_position(pe.item_id, pe.putaran);

  return jsonb_build_object(
    'tersimpan', true,
    'tanpa_mapel', false,
    'bulan_depan', v_depan,
    'baris', v_baris,
    'mapel_capaian', v_mapel_capaian,
    'target', v_target,
    'di_bawah_capaian', v_bawah
  );
end $$;

revoke execute on function public.wasilah_simpan_gabungan(uuid, uuid, jsonb, jsonb, boolean) from public, anon;
grant execute on function public.wasilah_simpan_gabungan(uuid, uuid, jsonb, jsonb, boolean) to authenticated, service_role;
