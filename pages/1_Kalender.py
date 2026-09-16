"""
Halaman publik: kalender bulanan + daftar tugas per tanggal.
Read-only, tidak butuh login.
"""

from datetime import date

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_calendar import calendar

from utils.helpers import (
    EMOJI_PRIORITAS,
    EMOJI_STATUS,
    JENIS,
    WARNA_MATKUL,
    build_calendar_events,
    deadline_terdekat,
    format_deadline,
    format_tanggal,
    ikon_peringatan,
    now_wib,
    parse_click_date,
    parse_deadline,
    punya_link,
    tasks_pada_tanggal,
)
from utils.supabase_client import ConfigError, fetch_tasks

st.set_page_config(page_title="Kalender Tugas", page_icon="📅", layout="wide")

# Auto-refresh tiap 30 detik. Interval ini sengaja disamakan dengan ttl
# cache di fetch_tasks(), jadi refresh tidak membanjiri database.
st_autorefresh(interval=30_000, key="auto_refresh_kalender")

st.title("📅 Kalender Deadline")

# ---------------------------------------------------------------------
# Ambil data
# ---------------------------------------------------------------------
try:
    semua_tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"⚙️ Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"🔌 Gagal mengambil data dari Supabase.\n\nPesan asli: `{exc}`")
    st.stop()

if not semua_tasks:
    st.info("Belum ada tugas yang tercatat.")

# ---------------------------------------------------------------------
# Sidebar: filter + deadline terdekat
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Filter")
    filter_jenis = st.multiselect("Jenis", JENIS, default=JENIS)
    sembunyikan_selesai = st.checkbox("Sembunyikan yang sudah selesai", value=False)

    st.divider()
    st.header("⏰ Deadline Terdekat")

    terdekat = deadline_terdekat(semua_tasks, jumlah=5)
    if not terdekat:
        st.caption("Tidak ada deadline yang akan datang.")
    for t in terdekat:
        dt = parse_deadline(t["deadline"])
        selisih_hari = (dt - now_wib()).total_seconds() / 86400
        judul = f"{ikon_peringatan(t['deadline'])}{t['judul']}"
        badan = f"{t['mata_kuliah']} • {dt:%d %b, %H:%M} WIB"
        if selisih_hari < 3:
            st.error(f"**{judul}**\n\n{badan}")
        else:
            st.info(f"**{judul}**\n\n{badan}")

tasks = [t for t in semua_tasks if t.get("jenis") in filter_jenis]
if sembunyikan_selesai:
    tasks = [t for t in tasks if t.get("status") != "Selesai"]

# ---------------------------------------------------------------------
# Kalender
# ---------------------------------------------------------------------
opsi_kalender = {
    "initialView": "dayGridMonth",
    "locale": "id",
    "firstDay": 1,  # mulai hari Senin
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,listMonth",
    },
    "buttonText": {"today": "Hari ini", "month": "Bulan", "list": "Daftar"},
    "height": 640,
    "dayMaxEvents": 3,
}

state = calendar(
    events=build_calendar_events(tasks),
    options=opsi_kalender,
    key="kalender_publik",
)

# Simpan tanggal terpilih di session_state supaya tidak hilang
# setiap kali auto-refresh menjalankan ulang skrip.
if isinstance(state, dict):
    callback = state.get("callback")
    if callback == "dateClick":
        klik = parse_click_date(state.get("dateClick", {}).get("date", ""))
        if klik:
            st.session_state["tanggal_dipilih"] = klik.isoformat()
    elif callback == "eventClick":
        mulai = (
            state.get("eventClick", {})
            .get("event", {})
            .get("start", "")
        )
        klik = parse_click_date(mulai)
        if klik:
            st.session_state["tanggal_dipilih"] = klik.isoformat()

st.caption(
    "Blok merah = ada deadline. Klik tanggalnya untuk melihat detail tugas. "
    "Warna chip mengikuti mata kuliah."
)

# ---------------------------------------------------------------------
# Detail tugas pada tanggal terpilih
# ---------------------------------------------------------------------
st.divider()

tanggal_iso = st.session_state.get("tanggal_dipilih")
if not tanggal_iso:
    st.info("👆 Klik salah satu tanggal di kalender untuk melihat tugasnya.")
    st.stop()

tanggal = date.fromisoformat(tanggal_iso)
tugas_hari_itu = tasks_pada_tanggal(tasks, tanggal)

judul_kolom, tombol_kolom = st.columns([4, 1])
judul_kolom.subheader(f"Tugas pada {format_tanggal(tanggal)}")
if tombol_kolom.button("Tutup detail", use_container_width=True):
    st.session_state.pop("tanggal_dipilih", None)
    st.rerun()

if not tugas_hari_itu:
    st.write("Tidak ada tugas pada tanggal ini (atau tersaring oleh filter di sidebar).")
    st.stop()

for t in tugas_hari_itu:
    warna = WARNA_MATKUL.get(t.get("mata_kuliah"), "#868E96")
    with st.container(border=True):
        atas_kiri, atas_kanan = st.columns([3, 1])

        with atas_kiri:
            st.markdown(f"### {ikon_peringatan(t['deadline'])}{t['judul']}")
            st.markdown(
                f"<span style='color:{warna};font-weight:600'>{t['mata_kuliah']}</span>"
                f" &nbsp;·&nbsp; {t.get('jenis', '-')}",
                unsafe_allow_html=True,
            )
            st.caption(f"🕒 {format_deadline(t['deadline'])}")

        with atas_kanan:
            st.markdown(
                f"**{EMOJI_STATUS.get(t.get('status'), '')} {t.get('status', '-')}**"
            )
            st.markdown(
                f"{EMOJI_PRIORITAS.get(t.get('prioritas'), '')} "
                f"Prioritas {t.get('prioritas', '-')}"
            )

        ketentuan = (t.get("ketentuan") or "").strip()
        if ketentuan:
            with st.expander("Ketentuan"):
                st.write(ketentuan)

        if punya_link(t):
            st.link_button(
                "🔗 Buka di VClass",
                t["link_vclass"],
                use_container_width=False,
            )
        else:
            st.caption("📌 Tanpa link — lihat bagian Ketentuan untuk cara pengumpulan.")
