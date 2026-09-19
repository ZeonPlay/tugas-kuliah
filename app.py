"""
Entry point aplikasi. Jalankan dengan:  streamlit run app.py

Streamlit otomatis membaca folder pages/ dan menampilkannya di sidebar,
jadi file ini cukup jadi halaman sambutan + pengecekan konfigurasi.
"""

import streamlit as st
from utils.styles import INK_SOFT, inject_base_css

from utils.helpers import MATA_KULIAH, deadline_terdekat, format_tanggal, now_wib, parse_deadline
from utils.supabase_client import ConfigError, fetch_tasks

st.set_page_config(page_title="Tugas Kuliah", layout="wide", initial_sidebar_state="expanded")
inject_base_css()

st.title("Tugas Kuliah")
st.caption(f"S1 Sistem Informasi · {format_tanggal(now_wib().date())} · waktu ditampilkan dalam WIB")

try:
    tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(
        "Gagal terhubung ke Supabase.\n\n"
        f"Pesan asli: `{exc}`\n\n"
        "Cek URL & anon key, tabel `tasks` sudah dibuat (jalankan `sql/setup.sql`), "
        "dan project Supabase tidak sedang paused."
    )
    st.stop()

st.divider()

# ---------------------------------------------------------------------
# Hero: yang paling penting untuk dilihat pertama kali — bukan deretan
# metrik generik, tapi tugas berikutnya yang deadline-nya paling dekat.
# ---------------------------------------------------------------------
terdekat = deadline_terdekat(tasks, jumlah=1)

kiri, kanan = st.columns([2, 1], gap="large")

with kiri:
    if terdekat:
        t = terdekat[0]
        dt = parse_deadline(t["deadline"])
        st.markdown('<p class="label-kecil">Deadline berikutnya</p>', unsafe_allow_html=True)
        st.markdown(f"### {t['judul']}")
        st.write(f"{t['mata_kuliah']} — {t.get('jenis', '-')}")
        st.caption(f"{format_tanggal(dt.date())} · {dt:%H:%M} WIB")
    else:
        st.markdown('<p class="label-kecil">Deadline berikutnya</p>', unsafe_allow_html=True)
        st.write("Tidak ada deadline yang akan datang.")

    st.write("")
    belum = sum(1 for x in tasks if x.get("status") == "Belum")
    dikerjakan = sum(1 for x in tasks if x.get("status") == "Dikerjakan")
    st.caption(f"{belum} tugas belum dikerjakan · {dikerjakan} sedang dikerjakan dari {len(tasks)} total")

    st.write("")
    st.markdown(
        "Buka **Kalender** di sidebar untuk melihat semua deadline dan detail tiap tugas. "
        "Tugas yang tidak punya link VClass tetap dicatat — cara pengumpulannya ada di "
        "bagian Ketentuan pada tugas tersebut."
    )

with kanan:
    st.markdown('<p class="label-kecil">Mata kuliah</p>', unsafe_allow_html=True)
    st.markdown(
        "".join(
            f'<div class="baris-list" style="--aksen:{INK_SOFT}"><span class="label-kecil">{m}</span></div>'
            for m in MATA_KULIAH
        ),
        unsafe_allow_html=True,
    )
