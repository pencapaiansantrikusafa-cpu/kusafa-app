-- ============================================================================
-- T6b (lanjutan): Hadir dan Hari Efektif per santri di form Wasilah/Ghayah.
--
-- Alasan: migrasi 20261125000013 mengirim izin/sakit/alpha dan Hari Efektif domain,
-- lalu form menghitung Hadir di React. Aturan keras project: Hadir dan Hari Efektif
-- HARUS dibaca dari view database (`v_attendance`), bukan dihitung di React.
--
-- Migrasi ini hanya MENGGANTI `wasilah_input_form` (create or replace) agar tiap baris
-- presensi memuat `hadir` dan `effective_days` hasil view. Tidak ada perubahan lain:
-- aturan hak tulis, penolakan bulan 0/terkunci, dan penyalinan ke anggota tetap sama
-- (fungsi `wasilah_input_save` dari migrasi 000013 tidak diubah).
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

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

-- Verifikasi:
--   select jsonb_array_elements(public.wasilah_input_form(
--     (select id from public.halaqahs where domain='wasilah' order by code limit 1),
--     (select id from public.hijri_months where month_no=6))->'presensi');
