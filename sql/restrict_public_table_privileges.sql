-- Restrict browser-role table privileges for Tugas Kuliah.
-- Run once on existing installations after confirming RLS policies are active.
-- Public visitors retain SELECT only. Authenticated users retain CRUD, but
-- their writes are still restricted by the existing Admin-only RLS policies.
-- This script does not modify or delete application data.

begin;

revoke all privileges on table
    public.tasks,
    public.courses,
    public.module_folders
from public, anon, authenticated;

grant select on table
    public.tasks,
    public.courses,
    public.module_folders
to anon;

grant select, insert, update, delete on table
    public.tasks,
    public.courses,
    public.module_folders
to authenticated;

commit;
