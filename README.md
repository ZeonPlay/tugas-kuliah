# Tugas Kuliah

Aplikasi web untuk mengelola tugas, deadline, kalender akademik, dan arsip materi kuliah.

> **Aplikasi utama saat ini adalah React + TypeScript di folder `web/`.**
> Versi Streamlit sudah dihentikan dan tidak lagi menjadi bagian dari proyek aktif.

## Teknologi

- React 19 + TypeScript
- Vite
- Supabase (Database, Authentication, Storage, Realtime)
- FullCalendar untuk kalender deadline
- Tiptap untuk editor instruksi tugas
- Cloudflare Pages untuk deployment

## Menjalankan secara lokal

Persyaratan: Node.js 22 atau lebih baru dan npm.

```bash
cd web
npm ci
cp .env.example .env.local
```

Isi `web/.env.local` dengan konfigurasi koneksi Supabase:

```env
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
```

Konfigurasi dan provisioning identitas Super Admin tidak disertakan dalam dokumentasi publik. Untuk instalasi baru, jalankan `sql/setup.sql`, siapkan `sql/super_admin_security.sql` secara privat, lalu jalankan `sql/security_hardening.sql` setelah frontend terbaru sudah ter-deploy.

Kemudian jalankan:

```bash
npm run dev
```

Untuk memeriksa build produksi:

```bash
npm run build
npm run preview
```

## Deployment Cloudflare Pages

Gunakan pengaturan berikut:

| Pengaturan | Nilai |
|---|---|
| Production branch | `main` |
| Root directory | `web` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Node.js | `22` |

Tambahkan environment variables koneksi Supabase berikut di pengaturan Cloudflare Pages:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

Jangan menambahkan identitas atau kredensial admin ke variabel frontend. Nilai dengan awalan `VITE_` akan tersedia di browser.

Setelah deployment berhasil, setiap push ke `main` akan menjadi versi produksi.

## Keamanan

Aplikasi menggunakan Supabase Authentication dan Row Level Security (RLS). Hak istimewa admin ditentukan dan diverifikasi di sisi database, bukan dari konfigurasi frontend. Pengguna biasa hanya dapat memeriksa emailnya sendiri dalam daftar admin; seluruh daftar hanya dapat dilihat Super Admin. Bucket lampiran dapat dibaca melalui URL publik, sedangkan upload, perubahan, dan penghapusan dibatasi untuk admin.

Panduan provisioning akun istimewa dan konfigurasi internal sengaja tidak dipublikasikan. Frontend hanya boleh menggunakan publishable key (atau anon key lama). **Jangan pernah menaruh service-role/secret key di variabel `VITE_*` atau mengirimkannya ke browser.**

## Fitur utama

- Dashboard deadline dan kalender tugas.
- Halaman Semua Tugas dengan pencarian, filter, dan pengurutan.
- Progress pribadi per tugas: belum mulai, sedang dikerjakan, dan selesai.
- Progress disimpan lokal di browser/perangkat, bukan di database bersama dan tidak tersinkron antarperangkat.
- Sinkronisasi perubahan tugas, mata kuliah, dan arsip modul melalui Supabase Realtime setelah hardening SQL diterapkan.

## Pemeriksaan otomatis

GitHub Actions menjalankan:

```bash
cd web
npm ci
npm run build
```

Build diperiksa saat ada perubahan frontend di pull request maupun branch `main` dan `feat/web-migration`.

## Struktur proyek

```
tugas-kuliah/
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── web-build.yml
├── sql/
│   ├── setup.sql
│   └── super_admin_security.sql
├── web/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```
