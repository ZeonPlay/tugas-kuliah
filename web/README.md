# Tugas Kuliah — Web (React)

Frontend baru untuk menggantikan Streamlit secara bertahap. Aplikasi Streamlit di root repository tetap dipertahankan selama migrasi.

## Teknologi

- React + TypeScript + Vite
- Supabase JS Client
- Cloudflare Pages untuk hosting frontend statis

## Menjalankan secara lokal

Dari folder repository, jalankan:

    cd web
    npm install
    cp .env.example .env.local

Isi file .env.local dengan URL project dan publishable key / anon key dari Supabase:

    VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
    VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY

Kemudian:

    npm run dev

Untuk menguji build produksi:

    npm run build
    npm run preview

## Deploy ke Cloudflare Pages

- Root directory: web
- Build command: npm run build
- Build output directory: dist
- Environment variables: VITE_SUPABASE_URL dan VITE_SUPABASE_ANON_KEY
- Gunakan Node.js 22 atau versi LTS yang didukung Vite untuk build.

Frontend browser hanya boleh memakai publishable key (atau anon key lama) dan RLS Supabase yang benar. Jangan pernah menaruh service-role/secret key di frontend, file environment yang di-commit, atau variabel VITE_*.

## Status migrasi

- [x] Fondasi React + Vite + TypeScript
- [x] Koneksi Supabase melalui environment variables
- [x] Dashboard awal membaca tabel tasks dan courses
- [x] Pencarian dan filter dashboard
- [ ] Kalender interaktif
- [ ] Login, daftar akun admin, logout, dan hak akses Super Admin
- [ ] Form tambah/edit/hapus tugas dan editor Markdown
- [ ] Upload dan hapus lampiran di Storage
- [ ] Manajemen mata kuliah dan arsip modul
- [ ] Kursor real-time
- [ ] Pengujian RLS, mobile, dan deployment

Frontend ini baru tahap awal. Jangan jadikan sebagai pengganti website aktif sebelum fitur admin dan policy keamanan selesai diuji.
