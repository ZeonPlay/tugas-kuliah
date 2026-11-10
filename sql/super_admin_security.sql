-- =====================================================================
-- super_admin_security.sql
-- Admin identities are private: regular users can only read their own
-- allowlist row, while the Super Admin can manage the full allowlist.
-- Configure the initial Super Admin only in a private SQL copy.
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

-- Remove any earlier policies. Permissive policies are combined with OR,
-- so leaving an old public-read policy in place would expose every email.
do $block$
declare
    policy_row record;
begin
    for policy_row in
        select schemaname, tablename, policyname
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
grant select on table public.admin_users to anon;
grant select, insert, delete on table public.admin_users to authenticated;
revoke insert, update, delete on table public.admin_users from anon;

-- A signed-in user can check only their own allowlist entry.
create policy admin_users_select_self
on public.admin_users
for select
to authenticated
using (lower(email) = lower((select auth.jwt() ->> 'email')));

-- A Super Admin can see the allowlist because this subquery can see only
-- the caller's own row in super_admins.
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

-- Register the privately configured Super Admin. Do not commit the actual
-- email address: replace the placeholder only in a private SQL Editor copy.
do $block$
declare
    v_super_admin_email text := lower(trim('configure_super_admin_privately'));
begin
    if v_super_admin_email is null
       or v_super_admin_email = 'configure_super_admin_privately'
       or v_super_admin_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' then
        raise exception 'The Super Admin identity is not configured in this private SQL copy.';
    end if;

    insert into public.super_admins (email)
    values (v_super_admin_email)
    on conflict (email) do nothing;

    insert into public.admin_users (email)
    values (v_super_admin_email)
    on conflict (email) do nothing;
end;
$block$;
