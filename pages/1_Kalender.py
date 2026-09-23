from datetime import date

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_calendar import calendar

from utils.helpers import (
    JENIS,
    build_calendar_events,
    deadline_terdekat,
    format_deadline,
    format_tanggal,
    parse_click_date,
    punya_link,
    sisa_waktu,
    tasks_pada_tanggal,
    warna_matkul,
    warna_urgensi,
)
from utils.styles import calendar_css, get_tokens, inject_base_css, render_theme_toggle
from utils.supabase_client import fetch_tasks

st.set_page_config(page_title="Kalender Tugas Kuliah", layout="wide")
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)
st_autorefresh(interval=30_000, key="auto_refresh_kalender")

st.title("Kalender Deadline")

try:
    semua_tasks = fetch_tasks()
except Exception as exc:
    st.error(f"Gagal mengambil data: `{exc}`")
    st.stop()

if not semua_tasks:
    st.info("Belum ada tugas yang tercatat.")
    st.stop()

with st.sidebar:
    st.markdown("### Filter Jenis")
    filter_jenis = st.multiselect("Jenis", JENIS, default=JENIS, label_visibility="collapsed")
    st.divider()
    st.markdown("### Deadline Terdekat")
    terdekat = deadline_terdekat(semua_tasks, jumlah=5)
    if terdekat:
        for t in terdekat:
            teks_sisa, level = sisa_waktu(t["deadline"])
            warna = warna_urgensi(tokens, level)
            html_side = f"""
<div style="border-left: 3px solid {warna}; padding-left: 10px; margin-bottom: 12px;">
    <div style="font-weight:600; font-size: 0.9rem; color: var(--text-color);">{t["judul"]}</div>
    <div style="font-size: 0.8rem; opacity: 0.8; color: var(--text-color);">{t["mata_kuliah"]}</div>
    <div style="font-size: 0.75rem; color: {warna}; font-weight: 600;">{teks_sisa}</div>
</div>
"""
            st.markdown(html_side, unsafe_allow_html=True)

tasks = [t for t in semua_tasks if t.get("jenis") in filter_jenis]
opsi_kalender = {
    "initialView": "dayGridMonth",
    "locale": "id",
    "firstDay": 1,
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"},
    "buttonText": {"today": "Hari ini", "month": "Bulan", "list": "Daftar"},
    "height": 620,
}

state = calendar(
    events=build_calendar_events(tasks, tokens),
    options=opsi_kalender,
    custom_css=calendar_css(mode),
    key="kalender_publik",
)

if isinstance(state, dict):
    cb = state.get("callback")
    if cb == "dateClick":
        klik = parse_click_date(state.get("dateClick", {}).get("date", ""))
        if klik:
            st.session_state["tanggal_dipilih"] = klik.isoformat()
    elif cb == "eventClick":
        klik = parse_click_date(state.get("eventClick", {}).get("event", {}).get("start", ""))
        if klik:
            st.session_state["tanggal_dipilih"] = klik.isoformat()

st.caption("Klik tanggal kalender untuk melihat detail tugas di bawah.")
st.divider()

tanggal_iso = st.session_state.get("tanggal_dipilih")
if not tanggal_iso:
    st.info("Klik salah satu tanggal di kalender untuk melihat daftar tugasnya.")
    st.stop()

tanggal = date.fromisoformat(tanggal_iso)
tugas_hari_itu = tasks_pada_tanggal(tasks, tanggal)

col1, col2 = st.columns([4, 1])
col1.subheader(f"Tugas pada: {format_tanggal(tanggal)}")
if col2.button("Tutup Detail", use_container_width=True):
    st.session_state.pop("tanggal_dipilih", None)
    st.rerun()

if not tugas_hari_itu:
    st.write("Tidak ada tugas pada tanggal ini.")
    st.stop()

for t in tugas_hari_itu:
    aksen = warna_matkul(tokens, t.get("mata_kuliah"))
    teks_sisa, level = sisa_waktu(t["deadline"])
    badge_bg = "rgba(239, 68, 68, 0.2)" if level == "lewat" else "rgba(16, 185, 129, 0.2)"
    badge_color = "#ef4444" if level == "lewat" else "#10b981"

    html_card_cal = f"""
<div style="background-color: var(--secondary-background-color); border: 1px solid rgba(150, 150, 150, 0.2); border-left: 5px solid {aksen}; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="color: {aksen}; font-weight: 600; font-size: 0.9rem;">{t["mata_kuliah"]} | {t.get("jenis", "-")}</span>
        <span style="background-color: {badge_bg}; color: {badge_color}; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;">{teks_sisa}</span>
    </div>
    <h3 style="margin: 0 0 5px 0; padding: 0; color: var(--text-color);">{t["judul"]}</h3>
    <div style="font-size: 0.85rem; opacity: 0.8; color: var(--text-color);">Waktu: {format_deadline(t["deadline"])}</div>
</div>
"""
    st.markdown(html_card_cal, unsafe_allow_html=True)

    ketentuan_html = (t.get("ketentuan") or "").strip()
    if ketentuan_html:
        with st.expander("Ketentuan"):
            st.markdown(ketentuan_html, unsafe_allow_html=True)

    btn_c1, btn_c2 = st.columns(2)
    if punya_link(t):
        btn_c1.link_button("Buka di VClass", t["link_vclass"], use_container_width=True)
    if t.get("file_soal"):
        btn_c2.link_button("Download File Soal", t["file_soal"], use_container_width=True)
    st.write("")
