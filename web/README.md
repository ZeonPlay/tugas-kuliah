# Tugas Kuliah — Web (React)

Frontend baru untuk menggantikan Streamlit secara bertahap. Aplikasi Streamlit di root repository tetap dipertahankan selama migrasi.

## Teknologi

- React + TypeScript + Vite
- FullCalendar React 7.1.1 for the academic calendar
- Tiptap WYSIWYG editor with Markdown serialization
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
- [x] Dashboard tugas membaca tabel tasks dan courses
- [x] Pencarian, filter, tampilan mendatang/terlewat, dan katalog mata kuliah
- [x] Render ketentuan sebagai Markdown dengan daftar, tautan, tabel, dan format umum
- [x] Navigasi ke Panel Admin
- [x] Login dan pendaftaran admin yang memeriksa allowlist tabel admin_users
- [x] Form tambah/edit tugas dengan validasi judul, mata kuliah, deadline, URL, dan ukuran lampiran
- [x] Editor visual Tiptap dengan toolbar, format Markdown, tautan, daftar, dan tabel
- [x] Alur admin terpisah: daftar tugas → form edit/tambah; hapus menggunakan dialog konfirmasi
- [x] Upload, penggantian, dan penghapusan lampiran melalui bucket task-files
- [x] Hapus tugas dengan konfirmasi
- [x] Kalender bulanan dengan deadline per tanggal, agenda harian, navigasi bulan, dan dukungan WIB
- [ ] Manajemen mata kuliah
- [ ] Arsip modul
- [ ] Pengelolaan daftar admin oleh Super Admin
- [ ] Kursor real-time
- [ ] Pengujian manual RLS dan kebijakan Storage untuk akun admin serta non-admin
- [ ] Uji visual pada lebar 320, 375, 414, dan 768 px; deploy Cloudflare Pages

## Catatan keamanan

- Panel Admin memeriksa email melalui tabel `admin_users`, tetapi operasi tulis tetap wajib dilindungi oleh policy RLS Supabase.
- Bucket `task-files` harus mengizinkan upload dan penghapusan hanya untuk akun admin yang sah. Jika upload ditolak, periksa policy Storage; jangan membuat bucket dapat ditulis publik.
- Frontend hanya memakai publishable key (atau anon key lama). Jangan pernah menaruh service-role/secret key di frontend, file environment yang di-commit, atau variabel `VITE_*`.
- Streamlit di root repository tetap dipertahankan dan belum digantikan. Uji akun, Storage, dan RLS sebelum menjadikan frontend ini website utama.
