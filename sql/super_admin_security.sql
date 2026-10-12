-- =====================================================================
-- super_admin_security.sql
-- Lock down admin_users writes and separate Super Admin identity from
-- ordinary admin access. This migration is intentionally separate from
-- setup.sql so the existing Streamlit app can keep running during migration.
--
-- BEFORE RUNNING: replace the placeholder email below with the same value
-- used by ADMIN_EMAIL in Streamlit and VITE_ADMIN_EMAIL in the web frontend.
-- Run once in Supabase Dashboard > SQL Editor.
-- =====================================================================

create table if not exists public.admin_users (
    email text primary key,
    created_at timestamptz not null default now()
);

create table if not exists public.super_admins (
    email text primary key,
    created_at timestamptz not null default now(),
    constraint super_admins_email_normalized check (email = lower(trim(email)))
);

alter table public.admin_users enable row level security;
alter table public.super_admins enable row level security;

-- No browser client may read or edit the Super Admin registry directly.
revoke all on table public.super_admins from anon, authenticated;

create or replace function public.is_super_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $function$
    select exists (
        select 1
        from public.super_admins
        where lower(email) = lower(auth.jwt() ->> 'email')
    );
$function$;

create or replace function public.is_protected_super_admin(target_email text)
returns boolean
language sql
stable
security definer
set search_path = public
as $function$
    select public.is_super_admin()
       and exists (
            select 1
            from public.super_admins
            where lower(email) = lower(coalesce(target_email, ''))
       );
$function$;

revoke all on function public.is_super_admin() from public, anon;
grant execute on function public.is_super_admin() to authenticated;

revoke all on function public.is_protected_super_admin(text) from public, anon;
grant execute on function public.is_protected_super_admin(text) to authenticated;

-- Register the original server-side Super Admin in a protected table and
-- ensure that identity remains an allowed admin account. Change this value
-- before running the script; it is intentionally a placeholder in Git.
do $block$
declare
    v_super_admin_email text := lower(trim('zeonplaychannel@gmail.com'));
begin
    if v_super_admin_email is null
       or v_super_admin_email = ''
       or v_super_admin_email = 'zeonplaychannel@gmail.com'
       or position('@' in v_super_admin_email) = 0 then
        raise exception 'Edit super_admin_security.sql and replace the Super Admin email placeholder before running.';
    end if;

    insert into public.super_admins (email)
    values (v_super_admin_email)
    on conflict (email) do nothing;

    insert into public.admin_users (email)
    values (v_super_admin_email)
    on conflict (email) do nothing;
end;
$block$;

-- Remove pre-existing policies before defining a single, explicit policy set.
-- This is important because permissive RLS policies are combined with OR.
do $block$
declare
    policy_row record;
begin
    for policy_row in
        select policyname
        from pg_policies
        where schemaname = 'public'
          and tablename = 'admin_users'
    loop
        execute format('drop policy if exists %I on public.admin_users', policy_row.policyname);
    end loop;
end;
$block$;

-- Keep the current read policy during the Streamlit transition: the existing
-- Streamlit login/signup flow checks admin_users before opening a session.
-- This preserves compatibility, while all browser writes are now role-gated.
create policy admin_users_select
on public.admin_users
for select
to anon, authenticated
using (true);

create policy admin_users_insert_super_admin
on public.admin_users
for insert
to authenticated
with check (public.is_super_admin());

create policy admin_users_delete_super_admin
on public.admin_users
for delete
to authenticated
using (
    public.is_super_admin()
    and not public.is_protected_super_admin(email)
);

grant select on public.admin_users to anon, authenticated;
grant insert, delete on public.admin_users to authenticated;
revoke insert, update, delete on public.admin_users from anon;

-- Verification query (run separately after the migration if desired):
-- select schemaname, tablename, policyname, roles, cmd, qual, with_check
-- from pg_policies
-- where schemaname = 'public'
--   and tablename in ('admin_users', 'super_admins')
-- order by tablename, policyname;
