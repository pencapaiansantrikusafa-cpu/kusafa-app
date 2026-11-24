-- ============================================================================
-- T5c-2: satu permintaan untuk seluruh isi form Input Al Qur'an.
--
-- Masalah yang diselesaikan: halaman Input masih menjalankan ±20 permintaan
-- berurutan ke database (bidang, bulan, anggota, santri, capaian, kehadiran,
-- catatan, dua view laporan, bulan sesudahnya, buku, item terpilih). Latensi
-- jaringan ke database (Singapore) 0,24-1,3 s per permintaan, sehingga halaman
-- butuh ±1,5-2 s walau query masing-masing hanya 0,1-0,2 s.
--
-- Perbaikan: `input_alquran_data(p_halaqah, p_bulan, p_bulan_lalu)` mengembalikan
-- SATU baris berisi semua bagian sebagai JSON. Halaman tetap memakai logika yang
-- sama untuk menyusun baris form; yang berubah hanya CARA mengambil data.
--
-- Yang TIDAK berubah (aturan keras project):
--   - posisi, selisih, putaran, target bulanan, Hadir — tetap dibaca dari view
--     `v_monthly_report` / `v_attendance` / `item_position`. Fungsi ini TIDAK
--     menghitung ulang apa pun; ia hanya mengumpulkan baris yang sudah dihitung.
--   - RLS: SECURITY INVOKER, jadi kebijakan tabel tetap berlaku.
--
-- Keamanan:
--   - Diperiksa `public.is_staff()` di dalam fungsi; pengguna tanpa profil aktif
--     (JWT tanpa baris profiles) dan anon tidak mendapat data (array kosong).
--     Anon tetap ditolak karena tidak punya EXECUTE.
--   - EXECUTE hanya untuk authenticated + service_role.
--
-- Batas ukuran: anggota halaqah dibatasi 2.000 (satu halaqah jauh di bawah itu;
-- data dummy terbesar 11 santri). Bila terlampaui, permintaan ditolak agar tidak
-- diam-diam terpotong.
-- ============================================================================

-- (Tidak memakai begin/commit eksplisit: Supabase CLI membungkus tiap migrasi.)

create or replace function public.input_alquran_data(
  p_halaqah uuid,
  p_bulan uuid,
  p_bulan_lalu uuid default null
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  v_boleh boolean;
  v_bidang jsonb;
  v_anggota uuid[];
  v_jml integer;
  v_eff integer;
  v_kunci boolean;
  v_capaian jsonb;
  v_item_terpilih jsonb;
  v_buku jsonb;
  v_presensi jsonb;
  v_catatan jsonb;
  v_lalu jsonb;
  v_kini jsonb;
  v_setelah jsonb;
  v_santri jsonb;
begin
  -- Pengguna aplikasi: harus staf (lewat profil). Koneksi admin/skrip lokal tanpa JWT
  -- (postgres/service_role/supabase_admin) diizinkan, pola sama dengan migrasi 000009/000011.
  v_boleh := coalesce(public.is_staff(), false)
             or (public.current_app_role() is null
                 and session_user in ('postgres', 'service_role', 'supabase_admin'));
  if not v_boleh then
    return jsonb_build_object('boleh', false);
  end if;

  -- Bidang domain Al Qur'an (urutan sama dengan halaman lama: sort_order).
  select coalesce(jsonb_agg(jsonb_build_object('id', s.id, 'name', s.name) order by s.sort_order, s.name), '[]'::jsonb)
    into v_bidang
  from public.subjects s
  where s.domain = 'alquran';

  -- Hari Efektif & kunci bulan (boleh kosong bila bulan belum punya setelan).
  select mds.effective_days, mds.is_locked
    into v_eff, v_kunci
  from public.month_domain_settings mds
  where mds.month_id = p_bulan and mds.domain = 'alquran';

  -- Anggota halaqah yang masih aktif (left_on is null), sama dengan halaman lama.
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
      'boleh', true, 'bidang', v_bidang, 'hari_efektif', v_eff, 'terkunci', coalesce(v_kunci, false),
      'santri', '[]'::jsonb, 'capaian', '[]'::jsonb, 'item_terpilih', '[]'::jsonb, 'buku', '[]'::jsonb,
      'presensi', '[]'::jsonb, 'catatan', '[]'::jsonb, 'lalu', '[]'::jsonb, 'kini', '[]'::jsonb,
      'setelah', '[]'::jsonb);
  end if;

  -- Santri (nama; urut nama seperti halaman lama).
  select coalesce(jsonb_agg(jsonb_build_object('id', s.id, 'full_name', s.full_name)
                            order by s.full_name, s.id), '[]'::jsonb)
    into v_santri
  from public.students s
  where s.id = any (v_anggota);

  -- Capaian bulan ini untuk halaqah ini (item + putaran + label item).
  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', pe.student_id, 'subject_id', pe.subject_id, 'item_id', pe.item_id,
           'putaran', pe.putaran, 'label', ci.label) order by pe.student_id, pe.subject_id), '[]'::jsonb)
    into v_capaian
  from public.progress_entries pe
  join public.curriculum_items ci on ci.id = pe.item_id
  where pe.month_id = p_bulan and pe.halaqah_id = p_halaqah;

  -- Detail item yang sudah terpilih (label berawalan bidang, nilai, siklik).
  with terpilih as (
    select distinct pe.item_id
    from public.progress_entries pe
    where pe.month_id = p_bulan and pe.halaqah_id = p_halaqah
  )
  select coalesce(jsonb_agg(jsonb_build_object(
           'id', ci.id, 'subject_id', b.subject_id,
           'label', s.name || ' · ' || ci.label, 'value', ci.value, 'siklik', b.is_cyclic)
           order by ci.seq, ci.id), '[]'::jsonb)
    into v_item_terpilih
  from terpilih t
  join public.curriculum_items ci on ci.id = t.item_id
  join public.books b on b.id = ci.book_id
  join public.subjects s on s.id = b.subject_id;

  -- Daftar buku aktif domain Al Qur'an (urutan buku).
  select coalesce(jsonb_agg(jsonb_build_object('id', b.id, 'subject_id', b.subject_id,
           'is_cyclic', b.is_cyclic, 'sort_order', b.sort_order)
           order by b.stage_order, b.sort_order), '[]'::jsonb)
    into v_buku
  from public.books b
  join public.subjects s on s.id = b.subject_id
  where s.domain = 'alquran' and b.is_active;

  -- Kehadiran bulan ini.
  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', a.student_id, 'month_id', a.month_id,
           'izin', a.izin, 'sakit', a.sakit, 'alpha', a.alpha,
           'effective_days_override', a.effective_days_override) order by a.student_id), '[]'::jsonb)
    into v_presensi
  from public.attendance a
  where a.month_id = p_bulan and a.domain = 'alquran' and a.student_id = any (v_anggota);

  -- Catatan bulanan.
  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', n.student_id, 'month_id', n.month_id, 'note', n.note) order by n.student_id), '[]'::jsonb)
    into v_catatan
  from public.monthly_notes n
  where n.month_id = p_bulan and n.domain = 'alquran' and n.student_id = any (v_anggota);

  -- Pos, putaran, teks capaian bulan lalu (pembanding otomatis) — dari view.
  if p_bulan_lalu is not null then
    select coalesce(jsonb_agg(jsonb_build_object(
             'student_id', v.student_id, 'subject_id', v.subject_id, 'pos', v.pos,
             'putaran', v.putaran, 'item_label', v.item_label) order by v.student_id, v.subject_id), '[]'::jsonb)
      into v_lalu
    from public.v_monthly_report v
    where v.halaqah_id = p_halaqah and v.month_id = p_bulan_lalu and v.domain = 'alquran';
  else
    v_lalu := '[]'::jsonb;
  end if;

  -- Isi tersimpan bulan ini menurut view (pos, selisih, teks).
  select coalesce(jsonb_agg(jsonb_build_object(
           'student_id', v.student_id, 'subject_id', v.subject_id, 'pos', v.pos,
           'putaran', v.putaran, 'item_label', v.item_label,
           'prev_item_label', v.prev_item_label, 'selisih', v.selisih)
           order by v.student_id, v.subject_id), '[]'::jsonb)
    into v_kini
  from public.v_monthly_report v
  where v.halaqah_id = p_halaqah and v.month_id = p_bulan and v.domain = 'alquran';

  -- Bulan-bulan SESUDAH bulan ini yang sudah terisi (peringatan peninjauan putaran).
  -- Urutan bulan lintas tahun memakai `v_months_ordered.ord` (hijri_year*100 + month_no),
  -- bukan perbandingan id/akademik apa pun.
  select coalesce(jsonb_agg(distinct jsonb_build_object(
           'student_id', pe.student_id, 'subject_id', pe.subject_id)), '[]'::jsonb)
    into v_setelah
  from public.progress_entries pe
  join public.v_months_ordered vm on vm.id = pe.month_id
  join public.v_months_ordered vb on vb.id = p_bulan
  where pe.student_id = any (v_anggota)
    and vm.ord > vb.ord;

  return jsonb_build_object(
    'boleh', true,
    'bidang', v_bidang,
    'hari_efektif', v_eff,
    'terkunci', coalesce(v_kunci, false),
    'santri', v_santri,
    'capaian', v_capaian,
    'item_terpilih', v_item_terpilih,
    'buku', v_buku,
    'presensi', v_presensi,
    'catatan', v_catatan,
    'lalu', v_lalu,
    'kini', v_kini,
    'setelah', v_setelah
  );
end $$;

-- ---------- Hardening: tanpa EXECUTE untuk anon/PUBLIC
revoke execute on function public.input_alquran_data(uuid, uuid, uuid) from public, anon;
grant execute on function public.input_alquran_data(uuid, uuid, uuid) to authenticated, service_role;

-- Verifikasi setelah migrasi:
--   select jsonb_pretty(public.input_alquran_data(
--     (select id from public.halaqahs where code='HLQ-PA-1'),
--     (select m.id from public.hijri_months m where m.month_no=6),
--     (select m.id from public.hijri_months m where m.month_no=5)))->'boleh';
--   sebagai anon: ditolak 42501; authenticated tanpa profil: {"boleh": false}.
-- ============================================================================
-- T5c-2 (lanjutan): satu permintaan untuk pembukaan halaman Input.
-- Sebelumnya: halaqah + bulan + pengampu (3 permintaan berurutan sebelum form bisa dimuat).
-- Sekarang: satu RPC mengembalikan ketiganya.
--   - `guru`: SEMUA baris pengampu (sama seperti `ambilGuru()` versi klien: halaqah_id,
--     profile_id, full_name; dibatasi 2.000 baris). Dipakai untuk label dropdown dan
--     untuk menyaring halaqah yang diampu (aturan yang tetap dijalankan di React,
--     database tetap penjaga terakhir lewat RLS).
--   - `halaqah`: halaqah aktif domain Al Qur'an (kode + nama).
--   - `bulan`: semua bulan lintas tahun ajaran (urut tahun, bulan).
-- ============================================================================

create or replace function public.input_alquran_boot()
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  v_boleh boolean;
  v_guru jsonb;
  v_halaqah jsonb;
  v_bulan jsonb;
begin
  v_boleh := coalesce(public.is_staff(), false)
             or (public.current_app_role() is null
                 and session_user in ('postgres', 'service_role', 'supabase_admin'));
  if not v_boleh then
    return jsonb_build_object('boleh', false);
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
           'halaqah_id', ht.halaqah_id, 'profile_id', ht.profile_id,
           'full_name', p.full_name) order by ht.halaqah_id, ht.profile_id), '[]'::jsonb)
    into v_guru
  from (select halaqah_id, profile_id from public.halaqah_teachers limit 2000) ht
  join public.profiles p on p.id = ht.profile_id;

  -- `name` tidak dikirim: dropdown hanya menampilkan kode + pengampu (label baku);
  -- pencarian memakai kode & nama pengampu. Menghemat payload pembukaan halaman.
  select coalesce(jsonb_agg(jsonb_build_object('id', h.id, 'code', h.code)
                            order by h.code), '[]'::jsonb)
    into v_halaqah
  from public.halaqahs h
  where h.domain = 'alquran' and h.is_active;

  select coalesce(jsonb_agg(jsonb_build_object(
           'id', m.id, 'month_no', m.month_no, 'name', m.name, 'hijri_year', ay.hijri_year)
           order by ay.hijri_year, m.month_no), '[]'::jsonb)
    into v_bulan
  from public.hijri_months m
  join public.academic_years ay on ay.id = m.academic_year_id;

  return jsonb_build_object('boleh', true, 'guru', v_guru, 'halaqah', v_halaqah, 'bulan', v_bulan);
end $$;

revoke execute on function public.input_alquran_boot() from public, anon;
grant execute on function public.input_alquran_boot() to authenticated, service_role;

-- Verifikasi: select public.input_alquran_boot(); -- guru, halaqah, bulan
