# Tugas Kuliah — Web

Frontend utama aplikasi Tugas Kuliah. Aplikasi dibangun menggunakan React, TypeScript, dan Vite, dengan Supabase sebagai backend.

## Menjalankan secara lokal

Dari root repository:

```bash
cd web
npm ci
cp .env.example .env.local
```

Isi environment variables koneksi Supabase di `.env.local`:

```env
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
```

Konfigurasi akun istimewa tidak disertakan dalam dokumentasi publik.

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
- Environment variables: `VITE_SUPABASE_URL` dan `VITE_SUPABASE_ANON_KEY`

## Keamanan

Hak istimewa admin ditentukan dan diverifikasi oleh Supabase di sisi database. Dokumentasi publik ini tidak memuat panduan provisioning akun istimewa.

Frontend hanya menggunakan publishable/anon key. Service-role/secret key tidak boleh masuk ke browser atau variabel `VITE_*`. Semua izin operasi database wajib ditegakkan oleh Row Level Security Supabase.

## Fitur

- Halaman Semua Tugas dengan pencarian, filter, pengurutan, dan progress pribadi lokal di browser.
- Supabase Realtime untuk menyegarkan tugas, mata kuliah, dan arsip modul (aktif setelah `sql/security_hardening.sql` diterapkan).

- Dashboard deadline dengan pencarian dan filter.
- Kalender bulanan dan agenda harian dalam WIB.
- Panel admin untuk tugas dan lampiran.
- Katalog mata kuliah.
- Arsip modul per mata kuliah.
- Login admin dan pengelolaan Super Admin.
- Editor instruksi berbasis Markdown.
- Kursor pengunjung real-time melalui Supabase Realtime.
