-- T7 [1b/2]: seluruh perubahan target melalui RPC; jejak audit; pembatalan pengajuan.
-- Keputusan final: target lama tidak dihapus, hanya pengaju dapat membatalkan status diajukan.

-- Jejak audit standar. Baris lama tidak disentuh/backfill untuk menjaga fingerprint data.
alter table public.targets
  add column if not exists entered_by uuid references public.profiles(id),
  add column if not exists entered_at timestamptz,
  add column if not exists updated_by uuid references public.profiles(id),
  add column if not exists updated_at timestamptz;

comment on column public.targets.entered_by is 'Pengisi/pengaju terakhir target.';
comment on column public.targets.entered_at is 'Waktu pengisian/pengajuan terakhir target.';
comment on column public.targets.updated_by is 'Pengguna terakhir yang mengubah status target.';
comment on column public.targets.updated_at is 'Waktu terakhir target diubah.';

-- Penggunaan trigger umum yang telah dipakai capaian, kehadiran, dan catatan.
drop trigger if exists catat_jejak_targets on public.targets;
create trigger catat_jejak_targets
  before insert or update on public.targets
  for each row execute function public.catat_jejak();

drop trigger if exists catat_perubahan_targets on public.targets;
create trigger catat_perubahan_targets
  after update or delete on public.targets
  for each row execute function public.catat_perubahan();

-- Cabut jalur tulis langsung, selain policy juga cabut privilege tabel dari API roles.
drop policy if exists targets_insert on public.targets;
drop policy if exists targets_update on public.targets;
drop policy if exists targets_delete on public.targets;
revoke insert, update, delete, truncate, trigger, references on public.targets from public, anon, authenticated;
-- SELECT tetap diizinkan lewat policy targets_read.
grant select on public.targets to authenticated;

-- Pembatalan: hanya pemilik pengajuan berstatus diajukan. Tidak menghapus baris.
create or replace function public.batalkan_target(p_target_id uuid)
returns jsonb
language plpgsql volatile security definer set search_path = public, pg_temp as $$
declare
  v_uid uuid := auth.uid();
  v_target public.targets%rowtype;
begin
  if v_uid is null then raise exception 'Harus masuk untuk membatalkan pengajuan target.'; end if;
  select * into v_target from public.targets where id = p_target_id for update;
  if not found then raise exception 'Target tidak ditemukan.'; end if;
  if v_target.proposed_by is distinct from v_uid then
    raise exception 'Hanya pengaju target ini yang dapat membatalkannya.';
  end if;
  if v_target.status <> 'diajukan' then
    raise exception 'Hanya target berstatus diajukan yang dapat dibatalkan. Target ditolak atau disetujui tetap menjadi riwayat.';
  end if;

  update public.targets
  set status = 'dibatalkan'
  where id = p_target_id;

  return jsonb_build_object('id', p_target_id, 'status', 'dibatalkan');
end $$;

revoke execute on function public.batalkan_target(uuid) from public, anon;
grant execute on function public.batalkan_target(uuid) to authenticated;
