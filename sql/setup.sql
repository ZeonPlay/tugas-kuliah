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
    -- Kolom ini tidak lagi ditampilkan/diminta di form (semua tugas
    -- dianggap sama pentingnya). Dibiarkan ada dengan nilai default
    -- supaya tidak perlu migrasi kalau nanti dipakai lagi.
    -- Kolom ini TIDAK LAGI dipakai di UI (semua tugas dianggap sama
    -- pentingnya). Dibiarkan ada dengan default otomatis supaya baris
    -- lama tidak error; boleh dihapus permanen lewat migrasi di bagian
    -- paling bawah file ini kalau kamu yakin tidak butuh lagi.
    prioritas    text        not null default 'Sedang'
                 check (prioritas in ('Tinggi', 'Sedang', 'Rendah')),
    status       text        not null default 'Belum'
                 check (status in ('Belum', 'Dikerjakan', 'Selesai')),
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create index if not exists tasks_deadline_idx on public.tasks (deadline);

-- ---------------------------------------------------------------------
-- 2. TRIGGER updated_at
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
-- 3. ROW LEVEL SECURITY
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
-- 4. (Opsional) Data contoh untuk mengetes tampilan kalender.
--    Hapus tanda komentar kalau mau dipakai.
-- ---------------------------------------------------------------------
-- insert into public.tasks (judul, mata_kuliah, jenis, deadline, ketentuan, link_vclass, prioritas, status)
-- values
--   ('Laporan Praktikum Modul 1', 'Sistem Basis Data', 'Praktikum',
--    now() + interval '2 days', 'Format PDF, maksimal 10 halaman.',
--    'https://vclass.unila.ac.id/mod/assign/view.php?id=12345', 'Tinggi', 'Belum'),
--   ('Tugas ERD Perpustakaan', 'Sistem Basis Data', 'Teori',
--    now() + interval '5 days', 'Dikumpulkan langsung ke dosen saat kelas.',
--    null, 'Sedang', 'Belum');

-- ---------------------------------------------------------------------
-- 5. (Opsional) Hapus kolom prioritas secara permanen.
--    Hanya jalankan ini kalau kamu YAKIN tidak akan memakainya lagi —
--    tidak bisa dibatalkan tanpa backup.
-- ---------------------------------------------------------------------
-- alter table public.tasks drop column prioritas;