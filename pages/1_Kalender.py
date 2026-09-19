"""
Halaman publik: kalender bulanan + daftar tugas per tanggal.
Read-only, tidak butuh login.
"""

from datetime import date

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_calendar import calendar
from utils.styles import calendar_css, inject_base_css

from utils.helpers import (
    JENIS,
    PRIORITAS_WARNA,
    STATUS_WARNA,
    WARNA_MATKUL,
    build_calendar_events,
    deadline_terdekat,
    format_deadline,
    format_tanggal,
    now_wib,
    parse_click_date,
    parse_deadline,
    punya_link,
    sisa_waktu,
    tasks_pada_tanggal,
    warna_urgensi,
)
from utils.supabase_client import ConfigError, fetch_tasks

st.set_page_config(page_title="Kalender — Tugas Kuliah", layout="wide")
inject_base_css()

# Auto-refresh tiap 30 detik, disamakan dengan ttl cache fetch_tasks()
# supaya refresh tidak membanjiri database.
st_autorefresh(interval=30_000, key="auto_refresh_kalender")

st.title("Kalender Deadline")

try:
    semua_tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal mengambil data dari Supabase.\n\nPesan asli: `{exc}`")
    st.stop()

if not semua_tasks:
    st.write("Belum ada tugas yang tercatat.")
    st.stop()

# ---------------------------------------------------------------------
# Sidebar: filter ringkas + daftar deadline terdekat sebagai list tipis
# (bukan kotak alert warna-warni bertumpuk seperti versi sebelumnya).
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown('<p class="label-kecil">Filter</p>', unsafe_allow_html=True)
    filter_jenis = st.multiselect("Jenis", JENIS, default=JENIS, label_visibility="collapsed")
    sembunyikan_selesai = st.checkbox("Sembunyikan yang sudah selesai", value=False)

    st.divider()
    st.markdown('<p class="label-kecil">Deadline terdekat</p>', unsafe_allow_html=True)

    terdekat = deadline_terdekat(semua_tasks, jumlah=5)
    if not terdekat:
        st.caption("Tidak ada deadline yang akan datang.")
    else:
        baris = []
        for t in terdekat:
            dt = parse_deadline(t["deadline"])
            teks_sisa, level = sisa_waktu(t["deadline"])
            warna = warna_urgensi(level)
            baris.append(
                f'<div class="baris-list" style="--aksen:{warna}">'
                f'<div style="font-weight:500">{t["judul"]}</div>'
                f'<div class="label-kecil">{t["mata_kuliah"]} · {dt:%d %b, %H:%M} WIB</div>'
                f'<div class="label-kecil" style="color:{warna}">{teks_sisa}</div>'
                f"</div>"
            )
        st.markdown("".join(baris), unsafe_allow_html=True)

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
    "height": 620,
    "dayMaxEvents": 3,
}

state = calendar(
    events=build_calendar_events(tasks),
    options=opsi_kalender,
    custom_css=calendar_css(),
    key="kalender_publik",
)

# Simpan tanggal terpilih di session_state supaya tidak hilang setiap
# kali auto-refresh menjalankan ulang skrip.
if isinstance(state, dict):
    callback = state.get("callback")
    if callback == "dateClick":
        klik = parse_click_date(state.get("dateClick", {}).get("date", ""))
        if klik:
            st.session_state["tanggal_dipilih"] = klik.isoformat()
    elif callback == "eventClick":
        mulai = state.get("eventClick", {}).get("event", {}).get("start", "")
        klik = parse_click_date(mulai)
        if klik:
            st.session_state["tanggal_dipilih"] = klik.isoformat()

st.caption(
    "Garis merah menandai tanggal dengan deadline. Klik tanggalnya untuk melihat "
    "detail tugas — warna tiap tugas mengikuti mata kuliahnya."
)

# ---------------------------------------------------------------------
# Detail tugas pada tanggal terpilih
# ---------------------------------------------------------------------
st.divider()

tanggal_iso = st.session_state.get("tanggal_dipilih")
if not tanggal_iso:
    st.write("Klik salah satu tanggal di kalender untuk melihat tugasnya.")
    st.stop()

tanggal = date.fromisoformat(tanggal_iso)
tugas_hari_itu = tasks_pada_tanggal(tasks, tanggal)

judul_kolom, tombol_kolom = st.columns([4, 1])
judul_kolom.markdown(f"### {format_tanggal(tanggal)}")
if tombol_kolom.button("Tutup", use_container_width=True):
    st.session_state.pop("tanggal_dipilih", None)
    st.rerun()

if not tugas_hari_itu:
    st.write("Tidak ada tugas pada tanggal ini (atau tersaring oleh filter di sidebar).")
    st.stop()

for t in tugas_hari_itu:
    warna_matkul = WARNA_MATKUL.get(t.get("mata_kuliah"), "#868E96")
    warna_status = STATUS_WARNA.get(t.get("status"), "#868E96")
    warna_prioritas = PRIORITAS_WARNA.get(t.get("prioritas"), "#868E96")

    st.markdown(f'<div class="kartu-tugas" style="--aksen:{warna_matkul}">', unsafe_allow_html=True)

    atas_kiri, atas_kanan = st.columns([3, 1])
    with atas_kiri:
        st.markdown(f"#### {t['judul']}")
        st.markdown(
            f'<span style="color:{warna_matkul};font-weight:500">{t["mata_kuliah"]}</span>'
            f' &nbsp;·&nbsp; <span class="label-kecil">{t.get("jenis", "-")}</span>',
            unsafe_allow_html=True,
        )
        st.caption(format_deadline(t["deadline"]))

    with atas_kanan:
        st.markdown(
            f'<span class="titik-status" style="--titik:{warna_status}"></span>{t.get("status", "-")}',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span class="titik-status" style="--titik:{warna_prioritas}"></span>Prioritas {t.get("prioritas", "-")}',
            unsafe_allow_html=True,
        )

    ketentuan = (t.get("ketentuan") or "").strip()
    if ketentuan:
        with st.expander("Ketentuan"):
            st.write(ketentuan)

    if punya_link(t):
        st.link_button("Buka di VClass", t["link_vclass"])
    else:
        st.caption("Tanpa link — lihat bagian Ketentuan untuk cara pengumpulan.")

    st.markdown("</div>", unsafe_allow_html=True)
