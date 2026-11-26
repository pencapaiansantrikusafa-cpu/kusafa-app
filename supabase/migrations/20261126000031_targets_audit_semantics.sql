-- T7a: jejak target mencatat pengubah saat ini, sambil menjaga pengaju asli.
-- Tidak mengubah baris target yang sudah ada.
create or replace function public.catat_jejak_target() returns trigger
language plpgsql security invoker set search_path = public, pg_temp as $$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then
    if tg_op = 'INSERT' and new.entered_at is null then new.entered_at := now(); end if;
    return new;
  end if;
  if tg_op = 'INSERT' then
    new.entered_by := coalesce(new.entered_by, v_uid);
    new.entered_at := coalesce(new.entered_at, now());
    return new;
  end if;
  -- Pengaju awal tetap tersimpan. Pada UPDATE, updated_by selalu orang yang
  -- melakukan perubahan saat ini, termasuk pengaju yang membatalkan miliknya.
  new.entered_by := old.entered_by;
  new.entered_at := old.entered_at;
  new.updated_by := v_uid;
  new.updated_at := now();
  return new;
end $$;

revoke execute on function public.catat_jejak_target() from public, anon, authenticated;
drop trigger if exists catat_jejak_targets on public.targets;
create trigger catat_jejak_targets
  before insert or update on public.targets
  for each row execute function public.catat_jejak_target();
