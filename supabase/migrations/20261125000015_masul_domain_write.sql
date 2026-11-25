-- ============================================================================
-- T6b: Masul = penanggung jawab domain untuk Ilmu Wasilah dan Ilmu Ghayah.
--
-- Keputusan Mudir 25 November 2026 (T6), menjawab pertanyaan yang muncul saat uji:
--   "Masul Wasilah/Masul Ghayah boleh menulis semua halaqah di domainnya walau tidak
--    tercatat sebagai pengampu mata pelajaran itu."
--
-- Masalah yang diselesaikan: `progress_entries` hanya punya policy tulis berbasis
-- `student_in_taught_halaqah(...)`, yaitu pengampu halaqah/mapel. Masul Wasilah dan
-- Masul Ghayah pada data dummy TIDAK tercatat sebagai pengampu mapel mana pun
-- (`halaqah_teachers`), sehingga mereka tidak bisa menginput apa pun — padahal mereka
-- penanggung jawab domain dan (menurut SPEC bagian 3) menyetujui target domainnya
-- serta mengelola kurikulum domainnya.
--
-- Yang diubah HANYA untuk domain wasilah dan ghayah:
--   1. `wasilah_can_write(halaqah, subject)` juga menerima Masul domain tersebut.
--   2. Dua policy tulis tambahan pada `progress_entries` untuk Masul domain itu.
--      Policy lama TIDAK dihapus dan TIDAK diubah; policy tambahan hanya MENAMBAH
--      izin (policy RLS digabung dengan OR).
--
-- Yang TIDAK diubah (sengaja):
--   - Al Qur'an tetap "halaqah yang diampu": tidak ada policy baru untuk domain
--     alquran, dan `wasilah_can_write` menolak halaqah Al Qur'an. Perubahan aturan
--     untuk Masul Al Quran harus diputuskan Mudir terpisah.
--   - Bulan terkunci: Masul bukan `is_full_access()`, jadi `month_is_open` tetap
--     berlaku dan bulan terkunci tetap ditolak untuk mereka.
--   - Santri di luar halaqah: tidak berubah. Penulisan tetap per santri anggota
--     halaqah (disalin oleh `wasilah_input_save`), bukan lintas halaqah.
-- ============================================================================

-- (Tanpa begin/commit: Supabase CLI membungkus tiap migrasi.)

-- ----------------------------------------------------------------------------
-- 1. Hak tulis capaian Wasilah/Ghayah: Mudir/Admin, pengampu mapel, atau Masul domain.
-- ----------------------------------------------------------------------------
create or replace function public.wasilah_can_write(p_halaqah uuid, p_subject uuid)
returns boolean
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select coalesce(public.is_full_access(), false)
         or coalesce(public.is_masul_of(public.domain_of_halaqah(p_halaqah)), false)
         or coalesce(public.teaches_halaqah_subject(p_halaqah, p_subject), false)
         or (public.current_app_role() is null
             and session_user in ('postgres', 'service_role', 'supabase_admin'))
$$;

revoke execute on function public.wasilah_can_write(uuid, uuid) from public, anon;
grant execute on function public.wasilah_can_write(uuid, uuid) to authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 2. Policy tulis tambahan untuk Masul domain Wasilah/Ghayah.
--    Syarat: domain mata pelajaran adalah domainnya, DAN bulan belum terkunci.
--    (Mudir/Admin sudah tercakup `is_full_access()` pada policy lama.)
-- ----------------------------------------------------------------------------
create policy progress_insert_masul_domain on public.progress_entries for insert to authenticated
  with check (
    public.is_masul_of(public.domain_of_subject(subject_id))
    and public.month_is_open(month_id, public.domain_of_subject(subject_id))
  );

create policy progress_update_masul_domain on public.progress_entries for update to authenticated
  using (
    public.is_masul_of(public.domain_of_subject(subject_id))
    and public.month_is_open(month_id, public.domain_of_subject(subject_id))
  )
  with check (
    public.is_masul_of(public.domain_of_subject(subject_id))
    and public.month_is_open(month_id, public.domain_of_subject(subject_id))
  );

-- ----------------------------------------------------------------------------
-- Verifikasi:
--   select policyname from pg_policies
--    where schemaname='public' and tablename='progress_entries' order by policyname;
--   -- harus ada 5 policy: progress_delete, progress_insert, progress_insert_masul_domain,
--   -- progress_update, progress_update_masul_domain
--   select public.wasilah_can_write(
--     (select id from public.halaqahs where domain='wasilah' order by code limit 1),
--     (select id from public.subjects where name='Sirah'));
-- ----------------------------------------------------------------------------
