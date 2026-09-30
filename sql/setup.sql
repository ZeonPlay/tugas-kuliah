-- =====================================================================
-- setup.sql — Skema + Row Level Security untuk aplikasi Tugas Kuliah
-- Cara pakai: Supabase Dashboard > SQL Editor > New query >
--             paste seluruh isi file ini > Run.
--
-- Tidak ada email admin yang perlu di-hardcode di SQL ini.
-- ADMIN_EMAIL digunakan oleh aplikasi sebagai identitas Super Admin,
-- sedangkan hak tulis database memeriksa tabel public.admin_users.
-- =====================================================================

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------
-- 1. TABEL
-- ---------------------------------------------------------------------
create table if not exists public.tasks (
    id           uuid primary key default gen_random_uuid(),
    judul        text        not null,
    mata_kuliah  text        not null,
    jenis        text        not null default 'Teori'
                 check (jenis in ('Praktikum', 'Teori', 'Quiz', 'Ujian')),
    deadline     timestamptz not null,
    ketentuan    text,
    link_vclass  text,                       -- boleh NULL: tugas lisan tidak punya link
    file_soal    text,                        -- URL lampiran di Storage
    -- prioritas dan status sudah tidak digunakan oleh aplikasi.
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create index if not exists tasks_deadline_idx on public.tasks (deadline);

alter table public.tasks add column if not exists file_soal text;

-- ---------------------------------------------------------------------
-- 2. KATALOG MATA KULIAH
--    Mata kuliah tidak lagi hardcoded di Python. Semester/kategori dapat
--    berubah setiap tahun tanpa mengubah tabel tasks.
-- ---------------------------------------------------------------------
create table if not exists public.courses (
    id          uuid primary key default gen_random_uuid(),
    kode        text unique,
    nama        text not null unique,
    semester    smallint not null check (semester between 1 and 8),
    kategori    text not null default 'Belum dikategorikan'
                check (kategori in ('Wajib', 'Pilihan', 'Belum dikategorikan')),
    aktif       boolean not null default true,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index if not exists courses_semester_idx
    on public.courses (semester, aktif);

alter table public.courses enable row level security;

drop policy if exists courses_select_public on public.courses;
drop policy if exists courses_insert_admin on public.courses;
drop policy if exists courses_update_admin on public.courses;
drop policy if exists courses_delete_admin on public.courses;

create policy courses_select_public
    on public.courses
    for select
    to anon, authenticated
    using (aktif = true);

-- Semua email yang sudah masuk admin_users boleh mengelola katalog.
create policy courses_insert_admin
    on public.courses
    for insert
    to authenticated
    with check (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

create policy courses_update_admin
    on public.courses
    for update
    to authenticated
    using (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    )
    with check (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

create policy courses_delete_admin
    on public.courses
    for delete
    to authenticated
    using (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

-- Data awal dari katalog semester 3 saat ini.
insert into public.courses (kode, nama, semester, kategori)
values
    (null, 'Analisis Kota Cerdas', 3, 'Wajib'),
    (null, 'Jaringan Komputer dan Komunikasi Data', 3, 'Wajib'),
    (null, 'Manajemen Proses Bisnis', 3, 'Wajib'),
    (null, 'Pemrograman Berorientasi Objek', 3, 'Wajib'),
    (null, 'Pemrograman Terstruktur', 3, 'Wajib'),
    (null, 'Rekayasa Perangkat Lunak', 3, 'Wajib'),
    (null, 'Sistem Basis Data', 3, 'Wajib'),
    (null, 'Sistem Operasi', 3, 'Wajib'),
    (null, 'UI/UX Design', 3, 'Wajib')
on conflict (nama) do nothing;

-- Migrasi dari versi awal arsip modul:
-- versi sebelumnya memakai tabel public.modules dan kolom judul.
do $$
begin
    if to_regclass('public.modules') is not null
       and to_regclass('public.module_folders') is null then
        alter table public.modules rename to module_folders;
    end if;

    if to_regclass('public.module_folders') is not null
       and exists (
           select 1
           from information_schema.columns
           where table_schema = 'public'
             and table_name = 'module_folders'
             and column_name = 'judul'
       )
       and not exists (
           select 1
           from information_schema.columns
           where table_schema = 'public'
             and table_name = 'module_folders'
             and column_name = 'nama'
       ) then
        alter table public.module_folders rename column judul to nama;
    end if;
end
$$;

-- ---------------------------------------------------------------------
-- 3. ARSIP MODUL
--    Setiap entri mewakili satu folder arsip yang dibuka langsung dari URL.
--    Aplikasi tidak membutuhkan OAuth/API Google Drive untuk membuka link.
-- ---------------------------------------------------------------------
create table if not exists public.module_folders (
    id           uuid primary key default gen_random_uuid(),
    course_id    uuid not null references public.courses(id) on delete restrict,
    nama         text not null,
    urutan       smallint not null default 1 check (urutan between 1 and 99),
    url          text not null,
    keterangan   text,
    aktif        boolean not null default true,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create index if not exists module_folders_course_order_idx
    on public.module_folders (course_id, urutan, nama);

alter table public.module_folders enable row level security;

drop policy if exists modules_select_public on public.module_folders;
drop policy if exists modules_insert_admin on public.module_folders;
drop policy if exists modules_update_admin on public.module_folders;
drop policy if exists modules_delete_admin on public.module_folders;
drop policy if exists module_folders_select_public on public.module_folders;
drop policy if exists module_folders_insert_admin on public.module_folders;
drop policy if exists module_folders_update_admin on public.module_folders;
drop policy if exists module_folders_delete_admin on public.module_folders;

create policy module_folders_select_public
    on public.module_folders
    for select
    to anon, authenticated
    using (aktif = true);

create policy module_folders_insert_admin
    on public.module_folders
    for insert
    to authenticated
    with check (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

create policy module_folders_update_admin
    on public.module_folders
    for update
    to authenticated
    using (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    )
    with check (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

create policy module_folders_delete_admin
    on public.module_folders
    for delete
    to authenticated
    using (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

-- ---------------------------------------------------------------------
-- 4. TRIGGER updated_at
-- ---------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists tasks_set_updated_at on public.tasks;
create trigger tasks_set_updated_at
    before update on public.tasks
    for each row
    execute function public.set_updated_at();

drop trigger if exists courses_set_updated_at on public.courses;
create trigger courses_set_updated_at
    before update on public.courses
    for each row
    execute function public.set_updated_at();

drop trigger if exists module_folders_set_updated_at on public.module_folders;
create trigger module_folders_set_updated_at
    before update on public.module_folders
    for each row
    execute function public.set_updated_at();

-- ---------------------------------------------------------------------
-- 5. ROW LEVEL SECURITY
--    Ini lapisan keamanan utama. Meskipun seseorang membuka halaman
--    Admin lewat URL langsung, database tetap menolak operasi tulis.
-- ---------------------------------------------------------------------
alter table public.tasks enable row level security;

drop policy if exists tasks_select_public on public.tasks;
drop policy if exists tasks_insert_admin  on public.tasks;
drop policy if exists tasks_update_admin  on public.tasks;
drop policy if exists tasks_delete_admin  on public.tasks;

-- SELECT: siapa pun (anonim + login) boleh baca
create policy tasks_select_public
    on public.tasks
    for select
    to anon, authenticated
    using (true);

-- INSERT: hanya email yang terdaftar di admin_users
create policy tasks_insert_admin
    on public.tasks
    for insert
    to authenticated
    with check (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

-- UPDATE: hanya email yang terdaftar di admin_users
create policy tasks_update_admin
    on public.tasks
    for update
    to authenticated
    using (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    )
    with check (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

-- DELETE: hanya email yang terdaftar di admin_users
create policy tasks_delete_admin
    on public.tasks
    for delete
    to authenticated
    using (
        exists (
            select 1
            from public.admin_users
            where lower(email) = lower(auth.jwt() ->> 'email')
        )
    );

-- ---------------------------------------------------------------------
-- 6. (Opsional) Data contoh untuk mengetes tampilan kalender.
--    Hapus tanda komentar kalau mau dipakai.
-- ---------------------------------------------------------------------
-- insert into public.tasks (judul, mata_kuliah, jenis, deadline, ketentuan, link_vclass)
-- values
--   ('Laporan Praktikum Modul 1', 'Sistem Basis Data', 'Praktikum',
--    now() + interval '2 days', 'Format PDF, maksimal 10 halaman.',
--    'https://vclass.unila.ac.id/mod/assign/view.php?id=12345'),
--   ('Tugas ERD Perpustakaan', 'Sistem Basis Data', 'Teori',
--    now() + interval '5 days', 'Dikumpulkan langsung ke dosen saat kelas.',
--    null);

-- ---------------------------------------------------------------------
-- 7. Bersihkan kolom lama yang sudah tidak digunakan.
--    Jalankan setup.sql pada database lama untuk menghapusnya.
-- ---------------------------------------------------------------------
alter table public.tasks drop column if exists prioritas;
alter table public.tasks drop column if exists status;