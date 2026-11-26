-- T7 [1b/2]: status target dibatalkan untuk pengajuan yang ditarik pengaju.
-- Status baru ditambahkan terpisah agar dapat dipakai setelah migrasi ini selesai.
alter type public.target_status add value if not exists 'dibatalkan';
