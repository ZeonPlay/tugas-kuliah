-- =====================================================================
-- setup.sql — Skema + Row Level Security untuk aplikasi Tugas Kuliah
-- Cara pakai: Supabase Dashboard > SQL Editor > New query >
--             paste seluruh isi file ini > Run.
--
-- >>> UBAH SEBELUM RUN <<<
-- Ganti SEMUA 'zeonplaychannel@gmail.com' di bawah dengan email admin kamu
-- (ada 4 tempat; pakai Find & Replace di editor).
-- Email ini HARUS sama persis dengan email user yang kamu buat di
-- Supabase > Authentication > Users.
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

-- ---------------------------------------------------------------------
-- 3. TRIGGER updated_at
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

-- ---------------------------------------------------------------------
-- 4. ROW LEVEL SECURITY
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

-- INSERT: hanya admin
create policy tasks_insert_admin
    on public.tasks
    for insert
    to authenticated
    with check ((auth.jwt() ->> 'email') = 'zeonplaychannel@gmail.com');  -- <<< GANTI

-- UPDATE: hanya admin
create policy tasks_update_admin
    on public.tasks
    for update
    to authenticated
    using      ((auth.jwt() ->> 'email') = 'zeonplaychannel@gmail.com')   -- <<< GANTI
    with check ((auth.jwt() ->> 'email') = 'zeonplaychannel@gmail.com');  -- <<< GANTI

-- DELETE: hanya admin
create policy tasks_delete_admin
    on public.tasks
    for delete
    to authenticated
    using ((auth.jwt() ->> 'email') = 'zeonplaychannel@gmail.com');       -- <<< GANTI

-- ---------------------------------------------------------------------
-- 5. (Opsional) Data contoh untuk mengetes tampilan kalender.
--    Hapus tanda komentar kalau mau dipakai.
-- ---------------------------------------------------------------------
-- insert into public.tasks (judul, mata_kuliah, jenis, deadline, ketentuan, link_vclass)
-- values
--   ('Laporan Praktikum Modul 1', 'Sistem Basis Data', 'Praktikum',
--    now() + interval '2 days', 'Format PDF, maksimal 10 halaman.',
--    'https://vclass.unila.ac.id/mod/assign/view.php?id=12345', 'Tinggi', 'Belum'),
--   ('Tugas ERD Perpustakaan', 'Sistem Basis Data', 'Teori',
--    now() + interval '5 days', 'Dikumpulkan langsung ke dosen saat kelas.',
--    null);

-- ---------------------------------------------------------------------
-- 6. Bersihkan kolom lama yang sudah tidak digunakan.
--    Jalankan setup.sql pada database lama untuk menghapusnya.
-- ---------------------------------------------------------------------
alter table public.tasks drop column if exists prioritas;
alter table public.tasks drop column if exists status;