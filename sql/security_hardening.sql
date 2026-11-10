-- =====================================================================
-- security_hardening.sql
-- Idempotent hardening for existing Tugas Kuliah Supabase projects.
--
-- IMPORTANT DEPLOYMENT ORDER:
-- 1. Deploy the frontend update first (it authenticates before checking
--    the current user's allowlist row).
-- 2. Run this SQL from Supabase SQL Editor.
--
-- This script does not delete application rows or uploaded objects.
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- Browser-role SQL privileges:
-- public visitors are read-only; signed-in users keep row-scoped CRUD
-- controlled by the RLS policies below. RLS does not protect TRUNCATE.
-- ---------------------------------------------------------------------
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

-- ---------------------------------------------------------------------
-- 1. Admin identity access: no anonymous email enumeration.
-- ---------------------------------------------------------------------
alter table public.admin_users enable row level security;
alter table public.super_admins enable row level security;

do $block$
declare
    policy_row record;
begin
    for policy_row in
        select tablename, policyname
        from pg_policies
        where schemaname = 'public'
          and tablename in ('admin_users', 'super_admins')
    loop
        execute format('drop policy if exists %I on public.%I', policy_row.policyname, policy_row.tablename);
    end loop;
end;
$block$;

revoke all on table public.super_admins from public, anon, authenticated;
grant select on table public.super_admins to authenticated;

revoke all on table public.admin_users from public, anon, authenticated;
-- The anon role retains SQL SELECT privilege only so nested policies can
-- safely evaluate to zero rows; there is deliberately no anon SELECT policy.
grant select on table public.admin_users to anon;
grant select, insert, delete on table public.admin_users to authenticated;
revoke insert, update, delete on table public.admin_users from anon;

create policy admin_users_select_self
on public.admin_users
for select
to authenticated
using (lower(email) = lower((select auth.jwt() ->> 'email')));

create policy admin_users_select_super_admin
on public.admin_users
for select
to authenticated
using (
    exists (
        select 1 from public.super_admins
        where email = lower((select auth.jwt() ->> 'email'))
    )
);

create policy admin_users_insert_super_admin
on public.admin_users
for insert
to authenticated
with check (
    exists (
        select 1 from public.super_admins
        where email = lower((select auth.jwt() ->> 'email'))
    )
);

create policy admin_users_delete_super_admin
on public.admin_users
for delete
to authenticated
using (
    exists (
        select 1 from public.super_admins
        where email = lower((select auth.jwt() ->> 'email'))
    )
    and not exists (
        select 1 from public.super_admins
        where email = lower(admin_users.email)
    )
);

create policy super_admins_select_self
on public.super_admins
for select
to authenticated
using (email = lower((select auth.jwt() ->> 'email')));

-- ---------------------------------------------------------------------
-- 2. Application table policies: one select policy per table and admin
--    predicates use initplan-friendly scalar subqueries.
-- ---------------------------------------------------------------------
drop policy if exists courses_select_public on public.courses;
drop policy if exists courses_select_admin on public.courses;
drop policy if exists courses_select_public_and_admin on public.courses;

create policy courses_select_public_and_admin
on public.courses
for select
to anon, authenticated
using (
    aktif = true
    or exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists module_folders_select_public on public.module_folders;
drop policy if exists module_folders_select_admin on public.module_folders;
drop policy if exists module_folders_select_public_and_admin on public.module_folders;

create policy module_folders_select_public_and_admin
on public.module_folders
for select
to anon, authenticated
using (
    aktif = true
    or exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists courses_insert_admin on public.courses;
create policy courses_insert_admin
on public.courses
for insert
to authenticated
with check (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists courses_update_admin on public.courses;
create policy courses_update_admin
on public.courses
for update
to authenticated
using (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
)
with check (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists courses_delete_admin on public.courses;
create policy courses_delete_admin
on public.courses
for delete
to authenticated
using (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists module_folders_insert_admin on public.module_folders;
create policy module_folders_insert_admin
on public.module_folders
for insert
to authenticated
with check (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists module_folders_update_admin on public.module_folders;
create policy module_folders_update_admin
on public.module_folders
for update
to authenticated
using (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
)
with check (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists module_folders_delete_admin on public.module_folders;
create policy module_folders_delete_admin
on public.module_folders
for delete
to authenticated
using (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists tasks_insert_admin on public.tasks;
create policy tasks_insert_admin
on public.tasks
for insert
to authenticated
with check (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists tasks_update_admin on public.tasks;
create policy tasks_update_admin
on public.tasks
for update
to authenticated
using (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
)
with check (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

drop policy if exists tasks_delete_admin on public.tasks;
create policy tasks_delete_admin
on public.tasks
for delete
to authenticated
using (
    exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

-- ---------------------------------------------------------------------
-- 3. Task attachments: public object URLs remain readable, but anonymous
--    users cannot list the bucket or upload/change/delete objects.
-- ---------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'task-files',
    'task-files',
    true,
    10485760,
    array[
        'application/pdf',
        'image/png',
        'image/jpeg',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/zip',
        'application/x-zip-compressed'
    ]::text[]
)
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Public Access for Task Files" on storage.objects;
drop policy if exists "Admin Upload for Task Files" on storage.objects;
drop policy if exists "Admin Update for Task Files" on storage.objects;
drop policy if exists "Admin Delete for Task Files" on storage.objects;
drop policy if exists task_files_admin_insert on storage.objects;
drop policy if exists task_files_admin_update on storage.objects;
drop policy if exists task_files_admin_delete on storage.objects;

create policy task_files_admin_insert
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'task-files'
    and exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

create policy task_files_admin_update
on storage.objects
for update
to authenticated
using (
    bucket_id = 'task-files'
    and exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
)
with check (
    bucket_id = 'task-files'
    and exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

create policy task_files_admin_delete
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'task-files'
    and exists (
        select 1 from public.admin_users
        where lower(email) = lower((select auth.jwt() ->> 'email'))
    )
);

-- ---------------------------------------------------------------------
-- 4. Realtime: subscribe to task, course, and module folder updates.
-- ---------------------------------------------------------------------
do $block$
declare
    table_name text;
begin
    if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
        foreach table_name in array array['tasks', 'courses', 'module_folders'] loop
            if to_regclass('public.' || table_name) is not null
               and not exists (
                    select 1
                    from pg_publication_tables
                    where pubname = 'supabase_realtime'
                      and schemaname = 'public'
                      and tablename = table_name
               ) then
                execute format('alter publication supabase_realtime add table public.%I', table_name);
            end if;
        end loop;
    end if;
end;
$block$;

-- Legacy SECURITY DEFINER helpers are no longer used by frontend policies.
-- Revoke their API execution grants; authorization now uses row-scoped
-- lookups against admin_users and super_admins.
do $block$
begin
    if to_regprocedure('public.is_admin()') is not null then
        execute 'revoke all on function public.is_admin() from public, anon, authenticated';
    end if;
    if to_regprocedure('public.is_super_admin()') is not null then
        execute 'revoke all on function public.is_super_admin() from public, anon, authenticated';
    end if;
    if to_regprocedure('public.is_protected_super_admin(text)') is not null then
        execute 'revoke all on function public.is_protected_super_admin(text) from public, anon, authenticated';
    end if;
end;
$block$;

commit;
