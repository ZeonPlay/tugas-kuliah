# Tugas Kuliah

Aplikasi sederhana untuk membantu mahasiswa melihat dan mengelola deadline tugas kuliah.

**Stack**
- Python
- Streamlit
- Toast UI rich-text editor (WYSIWYG) dengan daftar alfabet `A. B. C.` (Markdown)
- Supabase (PostgreSQL + Auth + Storage)
- FullCalendar melalui `streamlit-calendar`

## Fitur

- Dashboard deadline terdekat
- Kalender deadline
- Pencarian dan filter tugas
- Detail/instruksi tugas dengan rich-text editor
- Link VClass
- File soal/ketentuan
- Login admin
- Tambah, edit, dan hapus tugas
- Manajemen daftar admin oleh Super Admin
- Waktu deadline disimpan sebagai UTC dan ditampilkan dalam WIB
- Tampilan yang disesuaikan untuk laptop dan layar Android
- Instruksi tugas disimpan sebagai Markdown/HTML; data lama dari editor Quill dikonversi saat digunakan, dan daftar alfabet dipertahankan

## Struktur

```
tugas-kuliah/
├── .devcontainer/
├── .streamlit/
├── pages/
│   ├── 1_Kalender.py
│   └── 2_Admin.py
├── utils/
│   ├── auth.py
│   ├── components.py
│   ├── helpers.py
│   ├── styles.py
│   └── supabase_client.py
├── sql/
│   └── setup.sql
├── .env.example
├── .gitignore
├── app.py
├── requirements.txt
└── README.md
```

## Konfigurasi lokal

Buat `.env` berdasarkan `.env.example`:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Isi:

```env
SUPABASE_URL="https://YOUR-PROJECT.supabase.co"
SUPABASE_ANON_KEY="YOUR-SUPABASE-PUBLISHABLE-OR-ANON-KEY"
ADMIN_EMAIL="your-admin@email.com"
```

**Jangan commit `.env`.** File tersebut masuk `.gitignore`.

Untuk Streamlit Community Cloud, gunakan Secrets dengan format TOML:

```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR-SUPABASE-PUBLISHABLE-OR-ANON-KEY"
ADMIN_EMAIL = "your-admin@email.com"
```

Gunakan publishable/anon key, bukan service-role/secret key.

## Supabase

Database aplikasi menggunakan beberapa bagian Supabase:

1. `tasks` — data tugas.
2. `admin_users` — whitelist akun yang boleh masuk ke panel admin.
3. Authentication — akun login admin.
4. Storage bucket `task-files` — lampiran tugas.
5. RLS — membatasi operasi database.

`sql/setup.sql` berisi schema dan RLS dasar untuk tabel `tasks`. Pada project yang sedang dipakai, tabel `admin_users` dan konfigurasi Storage dapat dikelola langsung dari Supabase Dashboard sesuai setup project.

### Penting tentang authorization

Aplikasi memiliki dua level:

- **Super Admin** — email yang disimpan pada `ADMIN_EMAIL`; dapat mengelola daftar admin.
- **Admin** — email yang terdaftar pada `admin_users`; dapat mengelola tugas sesuai policy RLS Supabase.

Pastikan policy RLS di Supabase juga mengizinkan operasi yang memang dibutuhkan oleh admin. Jangan hanya mengandalkan tombol/UI Streamlit sebagai pengaman.

## Menjalankan

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\\Scripts\\Activate.ps1
```

Install dependency:

```bash
pip install -r requirements.txt
```

Jalankan:

```bash
streamlit run app.py
```

Default URL:

```
http://localhost:8501
```

## Deployment

Untuk Streamlit Community Cloud:

1. Hubungkan repository GitHub.
2. Pilih `app.py` sebagai Main file.
3. Tambahkan `SUPABASE_URL`, `SUPABASE_ANON_KEY`, dan `ADMIN_EMAIL` pada Secrets.
4. Pastikan database, Authentication, Storage, dan RLS Supabase sudah siap.
5. Deploy.

## Catatan UI

Dashboard memakai komponen Streamlit native sebanyak mungkin agar lebih stabil di layar kecil. Custom CSS hanya digunakan untuk spacing, task card, warna mata kuliah, dan kalender.

Di Android, filter berada di dalam expandable section sehingga tidak memenuhi layar. Di laptop, dashboard menggunakan dua kolom untuk memanfaatkan ruang yang lebih lebar.

## Troubleshooting

**Data kosong**
- Pastikan policy SELECT pada `tasks` mengizinkan akses yang diinginkan.
- Pastikan `SUPABASE_URL` dan key benar.

**Login ditolak**
- Pastikan email sudah ada di Authentication.
- Pastikan email juga terdaftar di `admin_users`.
- Pastikan `ADMIN_EMAIL` benar jika akun tersebut adalah Super Admin.
- Periksa policy RLS untuk operasi admin.

**Upload file gagal**
- Pastikan bucket Storage `task-files` sudah ada.
- Periksa Storage RLS/policy untuk upload dan delete.

**Tanggal terlihat salah**
- Aplikasi menggunakan timezone `Asia/Jakarta` untuk tampilan.
- Deadline disimpan sebagai `timestamptz`.

## Prinsip keamanan

- Jangan commit `.env`.
- Jangan memasukkan service-role/secret key ke aplikasi.
- RLS Supabase tetap menjadi lapisan authorization database.
- Jangan menganggap halaman Admin tersembunyi sebagai pengamanan.
