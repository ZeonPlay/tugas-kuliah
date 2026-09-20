# Manajemen Tugas Kuliah

Website sederhana untuk mencatat deadline tugas kuliah. Halaman kalender
terbuka untuk teman sekelas (read-only), halaman admin hanya untuk pemilik akun.

Dibuat dengan Python + Streamlit + Supabase. Tidak ada HTML/CSS/JS custom.

---

## Ringkasan Arsitektur

Streamlit berperan sebagai frontend sekaligus backend, tanpa server terpisah.
Semua data ada di satu tabel `tasks` di Supabase (PostgreSQL).

Pembeda akses bukan kode Streamlit, melainkan Row Level Security di database:
pengunjung anonim memakai _anon key_ yang hanya diizinkan `SELECT`, sedangkan
setelah login token admin dilampirkan ke request sehingga policy
`INSERT/UPDATE/DELETE` aktif. Konsekuensinya, membuka halaman Admin lewat URL
langsung tidak memberi akses apa pun — database tetap menolak.

Ada dua client Supabase di `utils/supabase_client.py`. Client anonim di-cache
dengan `st.cache_resource` (dibagi ke semua pengunjung, jadi tidak boleh membawa
token siapa pun), sedangkan client admin dibuat ulang per sesi dari token di
`st.session_state`. Pemisahan ini mencegah token admin bocor ke sesi pengunjung lain.

Waktu disimpan sebagai `timestamptz` (UTC) dan selalu ditampilkan dalam WIB.

---

## Struktur Proyek

```
tugas-kuliah/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── app.py
├── pages/
│   ├── 1_Kalender.py
│   └── 2_Admin.py
├── utils/
│   ├── supabase_client.py
│   ├── auth.py
│   └── helpers.py
└── sql/
    └── setup.sql
```

Yang perlu kamu ubah sendiri:

- `sql/setup.sql` — ganti `zeonplaychannel@gmail.com` (4 tempat)
- `.env` — isi URL, anon key, dan `ADMIN_EMAIL`
- `utils/helpers.py` — daftar `MATA_KULIAH` kalau semester berganti

---

## Setup Supabase

**1. Buat project.** Masuk ke supabase.com, Sign in dengan GitHub, klik
_New project_. Isi nama project, buat _Database Password_ (simpan, walau
aplikasi ini tidak memakainya langsung), pilih region terdekat — Singapore
paling dekat dari Indonesia. Tunggu beberapa menit sampai project aktif.

**2. Jalankan skema.** Buka menu _SQL Editor_ di sidebar kiri, klik
_New query_. Salin seluruh isi `sql/setup.sql`, ganti dulu semua
`zeonplaychannel@gmail.com` dengan email yang akan kamu pakai sebagai admin,
lalu klik _Run_. Kalau berhasil akan muncul "Success. No rows returned".

**3. Cek tabelnya.** Buka menu _Table Editor_, tabel `tasks` seharusnya
sudah ada. Di sampingnya ada label yang menandakan RLS aktif.

**4. Buat akun admin.** Buka _Authentication_ > _Users_ > _Add user_ >
_Create new user_. Isi email (harus sama persis dengan yang kamu tulis di
`setup.sql`) dan password. Centang _Auto Confirm User_ supaya tidak perlu
verifikasi email.

**5. Ambil kredensial.** Buka _Project Settings_ > _Data API_ untuk
mendapatkan _Project URL_, dan _Project Settings_ > _API Keys_ untuk
mendapatkan kunci `anon` / `public`.

Anon key memang dirancang untuk dipublikasikan selama RLS aktif — itu sebabnya
langkah 2 tidak boleh dilewat. Jangan pernah memakai `service_role` key di
aplikasi ini; kunci itu menembus semua policy RLS.

---

## Menjalankan di Lokal

```bash
git clone <url-repo-kamu>
cd tugas-kuliah

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env           # lalu isi nilainya
streamlit run app.py
```

Aplikasi terbuka di `http://localhost:8501`.

---

## Deploy ke Streamlit Community Cloud

**1. Push ke GitHub.** Buat repository baru (boleh public — kredensial tidak
ikut ter-commit karena `.env` sudah masuk `.gitignore`). Pastikan
`requirements.txt` ikut ter-push, karena dari file itulah Streamlit Cloud
menginstal dependensi.

**2. Buat app.** Masuk ke share.streamlit.io dengan akun GitHub, klik
_Create app_ > _Deploy a public app from GitHub_. Pilih repository dan branch,
isi _Main file path_ dengan `app.py`, lalu atur URL aplikasinya.

**3. Isi secrets.** Sebelum klik Deploy, buka _Advanced settings_ > _Secrets_
dan tempelkan ini (format TOML, bukan format `.env`):

```toml
SUPABASE_URL = "https://xxxxxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOi..."
ADMIN_EMAIL = "email-kamu@gmail.com"
```

Kalau app sudah terlanjur di-deploy, secrets bisa diisi belakangan lewat
menu titik tiga > _Settings_ > _Secrets_. App akan restart otomatis.

**4. Deploy.** Proses build berjalan beberapa menit. Setelah selesai, bagikan
URL-nya ke teman sekelas — mereka langsung melihat kalender tanpa perlu login.

Catatan: app gratis di Community Cloud akan "tidur" kalau tidak dibuka
beberapa hari, dan butuh sekitar setengah menit untuk bangun saat dibuka lagi.
Project Supabase gratis juga di-pause kalau tidak ada aktivitas selama seminggu,
dan harus di-restore manual dari dashboard.

---

## Troubleshooting

**Kalender tidak muncul sama sekali (area kosong).**
Biasanya `streamlit-calendar` gagal terpasang. Cek log build di Streamlit Cloud
(menu _Manage app_ di pojok kanan bawah). Di lokal, jalankan
`pip install streamlit-calendar` lalu restart Streamlit sepenuhnya — bukan
sekadar refresh browser. Komponen Streamlit memuat file statis sendiri, jadi
ad-blocker yang agresif juga bisa memblokirnya; coba mode penyamaran.

**Klik tanggal tidak memunculkan apa-apa.**
Pastikan yang diklik adalah area kosong di dalam kotak tanggal, bukan chip
tugasnya. Kalau tetap tidak bereaksi, kemungkinan versi `streamlit-calendar`
yang terpasang tidak mengirim callback `dateClick`. Sebagai alternatif, ganti
tampilan ke _Daftar_ lewat tombol di kanan atas kalender.

**Tanggal yang muncul meleset satu hari.**
Ini gejala timezone. Kalender berjalan di browser, jadi kalau perangkat kamu
disetel ke zona waktu selain WIB, tanggal hasil klik bisa bergeser. Betulkan
zona waktu perangkat. Waktu yang tertulis di detail tugas selalu WIB karena
dikonversi di sisi Python.

**Error "new row violates row-level security policy".**
Email di policy RLS tidak cocok dengan email akun yang login. Buka Supabase >
SQL Editor dan jalankan `select auth.jwt() ->> 'email';` — atau lebih mudah,
cek ulang bahwa email di `setup.sql`, di `ADMIN_EMAIL`, dan di
_Authentication > Users_ ketiganya persis sama, termasuk huruf besar/kecil.

**Error koneksi / "Invalid API key".**
Cek anon key tersalin utuh (kuncinya panjang dan gampang terpotong), dan URL
tidak punya garis miring di akhir. Di Streamlit Cloud, pastikan secrets ditulis
dalam format TOML dengan tanda kutip, bukan format `KEY=value` seperti `.env`.

**Aplikasi jalan tapi data kosong padahal tabel ada isinya.**
Kemungkinan policy `SELECT` belum dibuat, sehingga RLS memblokir semua baris.
Jalankan ulang `sql/setup.sql` — file itu aman dijalankan berkali-kali.

**Perubahan dari halaman admin tidak langsung terlihat di kalender.**
Data dibaca dari cache 30 detik. Tunggu sebentar atau refresh halaman.

**Login berhasil di lokal tapi gagal di Streamlit Cloud.**
Hampir selalu karena `ADMIN_EMAIL` belum diisi di Secrets. Tanpa itu,
`utils/auth.py` menolak semua login.

---

## Ide Pengembangan Lanjutan

Beberapa yang belum dikerjakan dan bisa ditambahkan nanti: halaman arsip
khusus tugas selesai, notifikasi email H-1 lewat Supabase Edge Function,
dan dukungan multi-user supaya tiap orang punya daftar sendiri (butuh kolom
`user_id` plus perubahan policy RLS).
