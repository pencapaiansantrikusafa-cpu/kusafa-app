-- Koreksi satu kali: Hari Efektif Rabiul Awwal (month_no 6) domain Al Qur'an 3 -> 19.
--
-- Sumber data: data/source/3-Al Quran (halaqah dan pencapaian).xlsx
--   sheet  : "Halaqah Al Quran dan pencapaian"
--   sel    : BZ4 (header "HE"), nilai BZ5:B113 = 3 untuk 109 santri
--   arti   : blok Rabiul Awwal (indeks bulan ke-6) dimulai di kolom BZ;
--            BZ=HE, CA=H, CB=S, CC=I, CD=A, lalu pasangan label-nilai capaian.
--
-- Keputusan Mudir 24 November 2026: nilai yang benar adalah 19 hari.
-- Skrip ini TIDAK menyentuh file Excel. Agar seed ulang tidak mengembalikan 3,
-- Mudir harus memperbaiki sel BZ5:B113 di file Excel tersebut menjadi 19.
--
-- Prasyarat yang diperiksa skrip ini:
--   1. Baris month_domain_settings untuk Rabiul Awwal domain alquran ada.
--   2. Tidak ada santri dengan izin+sakit+alpha > 19 pada bulan itu (Hadir tidak boleh negatif).
--   3. Tidak ada effective_days_override santri yang lebih kecil dari izin+sakit+alpha.
--
-- Jalankan: python scripts/db/run_sql.py scripts/db/fixes/2026-11-24_rabiul_awwal_effective_days.sql

begin;

do $$
declare
  v_month uuid;
  v_bad integer;
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

  -- Presensi tidak boleh melebihi 19 hari per santri.
  select count(*) into v_bad
  from public.attendance a
  where a.month_id = v_month
    and a.domain = 'alquran'
    and (a.izin + a.sakit + a.alpha) > 19;
  if v_bad > 0 then
    raise exception 'Ada % baris presensi dengan izin+sakit+alpha > 19 hari; koreksi dibatalkan.', v_bad;
  end if;

  -- Hari Efektif khusus santri (bila ada) juga tidak boleh lebih kecil dari ketidakhadiran.
  select count(*) into v_bad
  from public.attendance a
  where a.month_id = v_month
    and a.domain = 'alquran'
    and a.effective_days_override is not null
    and a.effective_days_override < (a.izin + a.sakit + a.alpha);
  if v_bad > 0 then
    raise exception 'Ada % baris dengan Hari Efektif khusus < ketidakhadiran; koreksi dibatalkan.', v_bad;
  end if;

  update public.month_domain_settings
     set effective_days = 19
   where month_id = v_month
     and domain = 'alquran'
     and effective_days = 3;

  if not found then
    raise notice 'Tidak ada baris dengan effective_days = 3; mungkin sudah 19. Tidak ada perubahan.';
  end if;
end $$;

commit;

-- Verifikasi setelah koreksi:
select ay.hijri_year, m.month_no, m.name, mds.domain::text, mds.effective_days
from public.month_domain_settings mds
join public.hijri_months m on m.id = mds.month_id
join public.academic_years ay on ay.id = m.academic_year_id
where m.month_no = 6 and mds.domain = 'alquran'
order by ay.hijri_year desc;
