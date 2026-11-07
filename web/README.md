# Tugas Kuliah — Web

Frontend utama aplikasi Tugas Kuliah. Aplikasi dibangun menggunakan React, TypeScript, dan Vite, dengan Supabase sebagai backend.

## Menjalankan secara lokal

Dari root repository:

```bash
cd web
npm ci
cp .env.example .env.local
```

Isi environment variables di `.env.local`:

```env
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
VITE_ADMIN_EMAIL=your-admin@email.com
```

Jalankan development server:

```bash
npm run dev
```

Build dan preview produksi:

```bash
npm run build
npm run preview
```

## Deployment Cloudflare Pages

- Production branch: `main`
- Root directory: `web`
- Build command: `npm run build`
- Build output directory: `dist`
- Node.js: `22`
- Environment variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, dan `VITE_ADMIN_EMAIL`

## Database dan keamanan

Jalankan `sql/setup.sql` dan `sql/super_admin_security.sql` dari root repository melalui Supabase SQL Editor. Atur email Super Admin di skrip kedua sebelum menjalankannya.

Buat bucket Storage `task-files` dan terapkan policy yang hanya mengizinkan admin melakukan upload serta penghapusan. Frontend hanya menggunakan publishable/anon key; service-role key tidak boleh masuk ke browser.

Semua izin operasi database wajib ditegakkan oleh Row Level Security Supabase. Variabel `VITE_ADMIN_EMAIL` hanya dipakai untuk identitas Super Admin di antarmuka, bukan sebagai pengganti RLS.

## Fitur

- Dashboard deadline dengan pencarian dan filter.
- Kalender bulanan dan agenda harian dalam WIB.
- Panel admin untuk tugas dan lampiran.
- Katalog mata kuliah.
- Arsip modul per mata kuliah.
- Login admin dan pengelolaan Super Admin.
- Editor instruksi berbasis Markdown.
- Kursor pengunjung real-time melalui Supabase Realtime.
