-- ============================================================================
-- Koreksi: Hari Efektif Rabiul Awwal (month_no 6) domain Al Qur'an = 3 hari.
--
-- DIBUAT 24 November 2026 atas koreksi Mudir. Nilai yang BENAR adalah **3 hari**,
-- bukan 19. Rabiul Awwal 1447 memuat libur sekitar dua pekan lebih, sehingga
-- hanya 3 hari efektif. Nilai 19 yang sempat diterapkan lewat
-- `2026-11-24_rabiul_awwal_effective_days.sql` adalah KEKELIRUAN dan
-- dikembalikan oleh skrip ini.
--
-- Sumber data (tidak diubah oleh skrip ini):
--   data/source/3-Al Quran (halaqah dan pencapaian).xlsx
--   sheet  : "Halaqah Al Quran dan pencapaian"
--   sel    : BZ4 = header "HE"; BZ5:BZ113 = 3 untuk 109 santri
--   blok   : BZ=HE, CA=H, CB=S, CC=I, CD=A (Rabiul Awwal)
--
-- Prasyarat:
--   1. Tidak ada baris presensi dengan izin+sakit+alpha > 3 (Hadir tidak boleh negatif).
--   2. Tidak ada Hari Efektif khusus santri yang lebih kecil dari ketidakhadiran.
--   3. Tidak ada `effective_days_override` yang tidak perlu (Excel tidak punya
--      angka HE berbeda pada bulan ini, jadi override seharusnya kosong).
--
-- Yang diubah HANYA satu nilai: month_domain_settings.effective_days.
-- Tidak ada kolom turunan tersimpan; `hadir`, `selisih`, `target_monthly` dihitung
-- oleh view (v_attendance / v_monthly_report), jadi otomatis ikut benar.
--
-- Jalankan:
--   python scripts/db/run_sql.py scripts/db/fixes/2026-11-24_rabiul_awwal_revert_to_3.sql
-- ============================================================================

begin;

do $$
declare
  v_month uuid;
  v_bad integer;
  v_override integer;
  v_lama integer;
begin
  select m.id into v_month
  from public.hijri_months m
  join public.academic_years ay on ay.id = m.academic_year_id
  where m.month_no = 6
  order by ay.hijri_year desc
  limit 1;

  if v_month is null then
    raise exception 'Bulan Rabiul Awwal (month_no 6) tidak ditemukan.';
  end if;

  select mds.effective_days into v_lama
  from public.month_domain_settings mds
  where mds.month_id = v_month and mds.domain = 'alquran';

  if v_lama is null then
    raise exception 'Baris month_domain_settings Rabiul Awwal alquran tidak ditemukan.';
  end if;

  -- 1. Ketidakhadiran total tidak boleh melebihi 3 hari.
  select count(*) into v_bad
  from public.attendance a
  where a.month_id = v_month
    and a.domain = 'alquran'
    and (a.izin + a.sakit + a.alpha) > 3;
  if v_bad > 0 then
    raise exception 'Ada % baris presensi dengan izin+sakit+alpha > 3 hari; pemulihan dibatalkan.', v_bad;
  end if;

  -- 2. Hari Efektif khusus santri tidak boleh lebih kecil dari ketidakhadiran.
  select count(*) into v_bad
  from public.attendance a
  where a.month_id = v_month
    and a.domain = 'alquran'
    and a.effective_days_override is not null
    and a.effective_days_override < (a.izin + a.sakit + a.alpha);
  if v_bad > 0 then
    raise exception 'Ada % baris dengan Hari Efektif khusus < ketidakhadiran; pemulihan dibatalkan.', v_bad;
  end if;

  -- 3. Excel tidak memuat HE berbeda untuk bulan ini, jadi override seharusnya kosong.
  select count(*) into v_override
  from public.attendance a
  where a.month_id = v_month
    and a.domain = 'alquran'
    and a.effective_days_override is not null;
  if v_override > 0 then
    raise notice 'Ada % baris dengan effective_days_override pada bulan ini (periksa apakah perlu).', v_override;
  end if;

  update public.month_domain_settings
     set effective_days = 3
   where month_id = v_month
     and domain = 'alquran';

  raise notice 'Hari Efektif Rabiul Awwal alquran: % -> 3.', v_lama;
end $$;

commit;

-- Verifikasi setelah pemulihan.
select ay.hijri_year, m.month_no, m.name, mds.domain::text, mds.effective_days, mds.is_locked
from public.month_domain_settings mds
join public.hijri_months m on m.id = mds.month_id
join public.academic_years ay on ay.id = m.academic_year_id
where m.month_no = 6 and mds.domain = 'alquran'
order by ay.hijri_year desc;

-- Hadir harus berada di 1..3 (HE 3 dikurangi izin+sakit+alpha).
select min(hadir) as hadir_min, max(hadir) as hadir_max, count(*) as baris
from public.v_attendance va
join public.hijri_months m on m.id = va.month_id
where m.month_no = 6 and va.domain = 'alquran';