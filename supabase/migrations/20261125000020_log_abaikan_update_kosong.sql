-- ============================================================================
-- T6e (koreksi): log perubahan mengabaikan UPDATE yang tidak mengubah nilai apa pun.
--
-- Temuan uji: `pulihkan_data` (dan beberapa skrip pemulihan) menjalankan
-- `update ... set kolom = kolom`. Tanpa penjaga, setiap pemulihan menulis 2.000+ baris
-- log palsu "update" yang nilai lama = nilai baru, sehingga log penuh sampah.
-- Migration ini mengganti fungsi `catat_perubahan` saja: UPDATE dengan
-- to_jsonb(new) = to_jsonb(old) tidak dicatat; DELETE selalu dicatat.
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

create or replace function public.catat_perubahan() returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_kunci jsonb;
  v_aktor uuid := auth.uid();
  v_role public.app_role;
  v_sumber text;
begin
  if tg_op not in ('UPDATE', 'DELETE') then
    return coalesce(new, old);
  end if;

  -- UPDATE yang tidak mengubah nilai apa pun (mis. `set izin = izin` dari skrip/pulihkan_data)
  -- tidak dicatat: log hanya untuk perubahan yang berarti. DELETE selalu dicatat.
  if tg_op = 'UPDATE' and to_jsonb(new) = to_jsonb(old) then
    return new;
  end if;

  -- Kunci baris: id untuk progress_entries, kunci alami untuk kehadiran/catatan.
  if tg_table_name = 'progress_entries' then
    v_kunci := jsonb_build_object('id', old.id);
  elsif tg_table_name in ('attendance', 'monthly_notes') then
    v_kunci := jsonb_build_object('student_id', old.student_id,
                                  'month_id', old.month_id,
                                  'domain', old.domain);
  else
    v_kunci := jsonb_build_object('id', old.id);
  end if;

  if v_aktor is not null then
    select p.role into v_role from public.profiles p where p.id = v_aktor;
    v_sumber := 'aplikasi';
  else
    v_role := null;
    v_sumber := 'skrip:' || current_user;
  end if;

  insert into public.change_log
    (tabel, aksi, kunci, nilai_lama, nilai_baru, aktor, aktor_role, sumber)
  values
    (tg_table_name, lower(tg_op), v_kunci,
     to_jsonb(old),
     case when tg_op = 'UPDATE' then to_jsonb(new) else null end,
     v_aktor, v_role, v_sumber);

  return coalesce(new, old);
end $$;

revoke execute on function public.catat_perubahan() from public, anon, authenticated;

-- Verifikasi: `update public.attendance set alpha = alpha ...` tidak menambah baris log;
-- `delete`/`update` yang mengubah nilai tetap tercatat.
