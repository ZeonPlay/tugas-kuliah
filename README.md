# Tugas Kuliah

Aplikasi sederhana untuk membantu mahasiswa melihat dan mengelola deadline tugas kuliah.

**Stack**
- Python
- Streamlit
- Toast UI rich-text editor (WYSIWYG) (Markdown)
- Supabase (PostgreSQL + Auth + Storage)
- FullCalendar melalui `streamlit-calendar`

## Fitur

- Dashboard deadline terdekat
- Kalender deadline
- Pencarian dan filter tugas
- Filter tugas berdasarkan KRS/mata kuliah yang sedang diambil
- Pengaturan KRS per semester tanpa akun mahasiswa
- Katalog mata kuliah berbasis database (semester + Wajib/Pilihan)
- Arsip modul per mata kuliah
- Tautan Google Drive langsung maupun tautan custom
- Detail/instruksi tugas dengan rich-text editor
- Link VClass
- File soal/ketentuan
- Login admin
- Tambah, edit, dan hapus tugas
- Manajemen daftar admin oleh Super Admin
- Waktu deadline disimpan sebagai UTC dan ditampilkan dalam WIB
- Tampilan yang disesuaikan untuk laptop dan layar Android
- Instruksi tugas disimpan sebagai Markdown; data lama dari editor Quill dikonversi saat digunakan

## Struktur

```
tugas-kuliah/
├── .devcontainer/
├── .streamlit/
├── pages/
│   ├── 1_Kalender.py
│   ├── 2_Admin.py
│   └── 3_KRS.py
├── utils/
│   ├── auth.py
│   ├── components.py
│   ├── krs.py
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
2. `courses` — katalog mata kuliah, semester, dan kategori Wajib/Pilihan.
3. `modules` — arsip modul/materi per mata kuliah beserta URL.
4. `admin_users` — whitelist akun yang boleh masuk ke panel admin.
4. Authentication — akun login admin.
5. Storage bucket `task-files` — lampiran tugas.
7. RLS — membatasi operasi database.

`sql/setup.sql` berisi schema dan RLS untuk tabel `tasks` dan `courses`. Pada project yang sedang dipakai, tabel `admin_users` dan konfigurasi Storage dapat dikelola langsung dari Supabase Dashboard sesuai setup project.

### Penting tentang authorization

Aplikasi memiliki dua level:

- **Super Admin** — email yang disimpan pada `ADMIN_EMAIL`; dapat mengelola daftar admin.
- **Admin** — email yang terdaftar pada `admin_users`; dapat mengelola tugas sesuai policy RLS Supabase.

Pastikan policy RLS di Supabase juga mengizinkan operasi yang memang dibutuhkan oleh admin. Jangan hanya mengandalkan tombol/UI Streamlit sebagai pengaman.


### Arsip modul

Admin dapat menyimpan modul berdasarkan mata kuliah melalui tab **Arsip Modul**. Setiap entri memiliki judul, nomor modul, URL, dan keterangan opsional.

URL dapat berupa tautan **Google Drive langsung** maupun **tautan custom** milik asisten/dosen yang pada akhirnya mengarah ke materi. Aplikasi tidak mengunduh atau menyalin file Google Drive; aplikasi hanya menyimpan URL dan menyediakan tombol untuk membukanya. Hak akses file/folder tetap mengikuti pengaturan berbagi pada Google Drive atau situs tujuan.

### KRS dan mata kuliah

Mata kuliah tidak lagi disimpan sebagai daftar hardcoded di Python. Admin dapat menambah mata kuliah dari tab **Mata Kuliah** pada Panel Admin dan mengatur semester serta kategorinya.

Pada halaman **KRS Saya**, pengguna dapat memilih mata kuliah yang sedang diambil untuk setiap semester. Mata kuliah Wajib otomatis masuk, sedangkan mata kuliah Pilihan dipilih secara manual. Dashboard dan Kalender kemudian hanya menampilkan tugas dari KRS aktif.

Pengaturan KRS saat ini disimpan di session Streamlit, sehingga belum memerlukan akun mahasiswa. Setelah session berakhir, pengguna dapat mengatur KRS kembali.

Setelah perubahan ini, jalankan kembali `sql/setup.sql` di Supabase. File tersebut juga menambahkan tabel `courses` dan kolom `file_soal` bila belum ada. Data awal katalog berisi mata kuliah semester 3 saat ini; kategori/semester dapat disesuaikan oleh admin.

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
