-- T7a: hak EXECUTE RPC target. Cek hak di dalam fungsi; anon tidak boleh.
revoke execute on function public.target_bulan_berjalan(public.domain_kind) from public, anon;
revoke execute on function public.target_info_konfirmasi(uuid, public.domain_kind) from public, anon;
revoke execute on function public.target_cek_konfirmasi(uuid, public.domain_kind, boolean) from public, anon;
revoke execute on function public.target_boleh_ajukan(public.domain_kind, uuid, uuid, uuid) from public, anon;
revoke execute on function public.target_validasi_bentuk(public.domain_kind, uuid, uuid, uuid, public.target_period) from public, anon;
revoke execute on function public.ajukan_target(public.domain_kind, uuid, uuid, uuid, uuid, numeric, public.target_period, text, boolean) from public, anon;
revoke execute on function public.setujui_target(uuid, boolean) from public, anon;
revoke execute on function public.tolak_target(uuid, text, boolean) from public, anon;
revoke execute on function public.ubah_target(uuid, numeric, uuid, text, boolean) from public, anon;
revoke execute on function public.ajukan_target_massal_alquran(uuid, uuid, uuid, numeric, text, boolean) from public, anon;
revoke execute on function public.riwayat_target(uuid, uuid, uuid) from public, anon;

grant execute on function public.target_bulan_berjalan(public.domain_kind) to authenticated;
grant execute on function public.target_info_konfirmasi(uuid, public.domain_kind) to authenticated;
grant execute on function public.ajukan_target(public.domain_kind, uuid, uuid, uuid, uuid, numeric, public.target_period, text, boolean) to authenticated;
grant execute on function public.setujui_target(uuid, boolean) to authenticated;
grant execute on function public.tolak_target(uuid, text, boolean) to authenticated;
grant execute on function public.ubah_target(uuid, numeric, uuid, text, boolean) to authenticated;
grant execute on function public.ajukan_target_massal_alquran(uuid, uuid, uuid, numeric, text, boolean) to authenticated;
grant execute on function public.riwayat_target(uuid, uuid, uuid) to authenticated;
-- helper internal tidak perlu di-grant ke authenticated (dipanggil dari RPC definer)
