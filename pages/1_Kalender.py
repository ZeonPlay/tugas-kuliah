import streamlit as st
from datetime import date
from streamlit_autorefresh import st_autorefresh
from streamlit_calendar import calendar

from utils.components import render_task_card
from utils.helpers import JENIS, build_calendar_events, format_tanggal, parse_click_date, tasks_pada_tanggal
from utils.krs import get_active_krs, get_active_semester, is_krs_configured
from utils.styles import calendar_css, get_tokens, inject_base_css, render_theme_toggle
from utils.supabase_client import ConfigError, fetch_courses, fetch_tasks

st.set_page_config(page_title="Kalender Tugas", page_icon="🗓️", layout="wide", initial_sidebar_state="collapsed")

mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)
st_autorefresh(interval=30_000, key="auto_refresh_kalender")

st.title("Kalender Tugas")
st.caption("Klik tanggal yang memiliki deadline untuk melihat detail tugas.")

try:
    all_tasks = fetch_tasks()
    all_courses = fetch_courses()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\\n\\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal mengambil data: {exc}")
    st.stop()

active_krs = get_active_krs() if is_krs_configured() else []
if active_krs:
    all_tasks = [task for task in all_tasks if task.get("mata_kuliah") in active_krs]
    st.caption(f"📚 KRS aktif · Semester {get_active_semester()} · {len(active_krs)} mata kuliah")

if not all_tasks:
    st.info("Belum ada tugas yang tercatat.")
    st.stop()

with st.expander("🔎 Filter kalender", expanded=False):
    filter_jenis = st.multiselect("Jenis", JENIS, default=JENIS)
    course_names = [course["nama"] for course in all_courses]
    visible_course_names = active_krs or course_names
    filter_matkul = st.multiselect("Mata kuliah", visible_course_names, default=visible_course_names)

tasks = [
    task for task in all_tasks
    if task.get("jenis") in filter_jenis and task.get("mata_kuliah") in filter_matkul
]

if not tasks:
    st.warning("Filter saat ini tidak menemukan tugas.")
    st.stop()

calendar_options = {
    "initialView": "dayGridMonth",
    "locale": "id",
    "firstDay": 1,
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"},
    "buttonText": {"today": "Hari ini", "month": "Bulan", "list": "Daftar"},
    "height": 520,
}

state = calendar(
    events=build_calendar_events(tasks, tokens),
    options=calendar_options,
    custom_css=calendar_css(mode),
    key="kalender_publik",
)

if isinstance(state, dict):
    # Tombol "Tutup" melakukan rerun. Calendar component dapat mengembalikan
    # callback terakhir pada rerun tersebut, sehingga tanggal bisa langsung
    # terpilih lagi. Abaikan satu callback setelah penutupan.
    abaikan_callback = st.session_state.pop("_kalender_abaikan_callback", False)

    if not abaikan_callback:
        callback = state.get("callback")
        if callback == "dateClick":
            clicked = parse_click_date(state.get("dateClick", {}).get("date", ""))
            if clicked:
                st.session_state["tanggal_dipilih"] = clicked.isoformat()
        elif callback == "eventClick":
            clicked = parse_click_date(state.get("eventClick", {}).get("event", {}).get("start", ""))
            if clicked:
                st.session_state["tanggal_dipilih"] = clicked.isoformat()

selected = st.session_state.get("tanggal_dipilih")
if not selected:
    st.info("Pilih tanggal yang memiliki deadline untuk melihat detail.")
    st.stop()

try:
    selected_date = date.fromisoformat(selected)
except ValueError:
    st.session_state.pop("tanggal_dipilih", None)
    st.rerun()

tasks_on_day = tasks_pada_tanggal(tasks, selected_date)

left, right = st.columns([4, 1])
left.subheader(f"Tugas pada {format_tanggal(selected_date)}")
if right.button("Tutup", use_container_width=True):
    st.session_state.pop("tanggal_dipilih", None)
    st.session_state["_kalender_abaikan_callback"] = True
    st.rerun()

if not tasks_on_day:
    st.info("Tidak ada tugas pada tanggal tersebut.")
    st.stop()

for task in tasks_on_day:
    render_task_card(task, tokens, detail_label="Ketentuan")
