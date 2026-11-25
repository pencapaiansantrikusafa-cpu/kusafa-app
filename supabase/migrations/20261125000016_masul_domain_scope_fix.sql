-- ============================================================================
-- T6b: koreksi cakupan policy "Masul penanggung jawab domain".
--
-- Temuan uji `scripts/qa/rls_matrix.py` atas migrasi 20261125000015:
-- policy `progress_insert_masul_domain` / `progress_update_masul_domain` memakai
-- `is_masul_of(domain_of_subject(subject_id))`. Untuk Masul Al Quran fungsi itu
-- bernilai TRUE pada domain alquran, sehingga policy baru ikut memberi Masul Al Quran
-- hak menulis SEMUA halaqah Al Qur'an — padahal migrasi 000015 menyatakan dengan tegas
-- bahwa perilaku Al Qur'an TIDAK berubah ("halaqah yang diampu").
--
-- Koreksi: policy tambahan dibatasi ke domain wasilah dan ghayah saja
-- (`domain_of_subject(subject_id) <> 'alquran'`). Aturan Masul Al Quran tetap
-- seperti sebelumnya; bila ingin disamakan, harus diputuskan Mudir terpisah.
--
-- Tidak ada perubahan lain: policy lama tidak disentuh, dan `wasilah_can_write`
-- tetap menolak halaqah Al Qur'an (sudah diperiksa `wasilah_input_save`).
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

drop policy if exists progress_insert_masul_domain on public.progress_entries;
drop policy if exists progress_update_masul_domain on public.progress_entries;

-- Hanya untuk Ilmu Wasilah dan Ilmu Ghayah (bukan Al Qur'an).
create policy progress_insert_masul_domain on public.progress_entries for insert to authenticated
  with check (
    public.domain_of_subject(subject_id) <> 'alquran'
    and public.is_masul_of(public.domain_of_subject(subject_id))
    and public.month_is_open(month_id, public.domain_of_subject(subject_id))
  );

create policy progress_update_masul_domain on public.progress_entries for update to authenticated
  using (
    public.domain_of_subject(subject_id) <> 'alquran'
    and public.is_masul_of(public.domain_of_subject(subject_id))
    and public.month_is_open(month_id, public.domain_of_subject(subject_id))
  )
  with check (
    public.domain_of_subject(subject_id) <> 'alquran'
    and public.is_masul_of(public.domain_of_subject(subject_id))
    and public.month_is_open(month_id, public.domain_of_subject(subject_id))
  );

-- Verifikasi:
--   select policyname, with_check from pg_policies
--    where schemaname='public' and tablename='progress_entries' order by policyname;
--   -- policy *_masul_domain harus memuat "domain_of_subject(subject_id) <> 'alquran'"
