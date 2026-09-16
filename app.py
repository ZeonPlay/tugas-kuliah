"""
Entry point aplikasi. Jalankan dengan:  streamlit run app.py

Streamlit otomatis membaca folder pages/ dan menampilkannya di sidebar,
jadi file ini cukup jadi halaman sambutan + pengecekan konfigurasi.
"""

import streamlit as st

from utils.helpers import MATA_KULIAH, now_wib, format_tanggal
from utils.supabase_client import ConfigError, fetch_tasks

st.set_page_config(
    page_title="Tugas Kuliah",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📚 Manajemen Tugas Kuliah")
st.caption(f"S1 Sistem Informasi • {format_tanggal(now_wib().date())} • Zona waktu WIB")

# --- Cek koneksi database lebih awal, supaya pesan errornya jelas ---
try:
    tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"⚙️ Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(
        "🔌 Gagal terhubung ke Supabase.\n\n"
        f"Pesan asli: `{exc}`\n\n"
        "Cek: URL & anon key benar, tabel `tasks` sudah dibuat "
        "(jalankan `sql/setup.sql`), dan project Supabase tidak sedang paused."
    )
    st.stop()

belum = sum(1 for t in tasks if t.get("status") == "Belum")
dikerjakan = sum(1 for t in tasks if t.get("status") == "Dikerjakan")
selesai = sum(1 for t in tasks if t.get("status") == "Selesai")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total tugas", len(tasks))
k2.metric("Belum dikerjakan", belum)
k3.metric("Sedang dikerjakan", dikerjakan)
k4.metric("Selesai", selesai)

st.divider()

kiri, kanan = st.columns([2, 1])

with kiri:
    st.subheader("Cara pakai")
    st.markdown(
        """
**Kalender** — halaman utama, terbuka untuk siapa saja.
Tanggal yang punya deadline diberi blok merah. Klik tanggal tersebut untuk
melihat daftar tugas pada hari itu, lengkap dengan ketentuan dan link VClass.

**Admin** — hanya bisa dibuka oleh pemilik akun admin. Di sini tugas
ditambah, diubah, dan dihapus.

Gunakan menu di sidebar kiri untuk berpindah halaman.
        """
    )
    st.info(
        "Tugas yang tidak punya link VClass (misal diumumkan lisan di kelas) "
        "tetap bisa dicatat — keterangan pengumpulannya ditulis di kolom Ketentuan."
    )

with kanan:
    st.subheader("Mata kuliah")
    st.markdown("\n".join(f"- {m}" for m in MATA_KULIAH))
