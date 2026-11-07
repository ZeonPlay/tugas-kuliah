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

Isi `web/.env.local`:

```env
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
VITE_ADMIN_EMAIL=your-admin@email.com
```

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

Tambahkan environment variables berikut di pengaturan Cloudflare Pages:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_ADMIN_EMAIL`

Setelah deployment berhasil, setiap push ke `main` akan menjadi versi produksi.

## Setup Supabase

1. Jalankan `sql/setup.sql` pada Supabase SQL Editor untuk menyiapkan tabel, index, trigger, dan RLS.
2. Atur email Super Admin di `sql/super_admin_security.sql`, lalu jalankan skrip tersebut satu kali.
3. Buat bucket Storage bernama `task-files` dan atur policy upload serta delete khusus admin.
4. Pastikan URL dan publishable/anon key Supabase sudah dimasukkan ke environment variables frontend.

Frontend hanya boleh menggunakan publishable key (atau anon key lama). **Jangan pernah menaruh service-role/secret key di variabel `VITE_*` atau mengirimkannya ke browser.** Keamanan operasi database tetap harus ditegakkan oleh RLS Supabase.

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
