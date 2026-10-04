import streamlit as st

from utils.krs import get_active_krs, get_active_semester, is_krs_configured
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.presence import render_presence
from utils.supabase_client import ConfigError, fetch_courses, fetch_module_folders


st.set_page_config(
    page_title="Arsip Modul",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

mode = render_theme_toggle()
inject_base_css(mode)
get_tokens(mode)

st.title("Arsip Modul")
st.caption("Kumpulan folder modul dan materi yang dibagikan asisten dosen.")


try:
    courses = fetch_courses()
    folders = fetch_module_folders()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal mengambil arsip modul: {exc}")
    st.stop()


course_by_id = {course["id"]: course for course in courses}
active_krs = get_active_krs() if is_krs_configured() else []

if active_krs:
    visible_courses = [course for course in courses if course["nama"] in active_krs]
    visible_course_ids = {course["id"] for course in visible_courses}
    folders = [folder for folder in folders if folder["course_id"] in visible_course_ids]
    st.caption(f"📚 KRS aktif · Semester {get_active_semester()}")
else:
    visible_courses = courses

course_options = [course["nama"] for course in visible_courses]

with st.expander("🔎 Cari & filter arsip", expanded=False):
    search = st.text_input(
        "Cari folder",
        placeholder="Contoh: praktikum, modul 3, database",
        label_visibility="collapsed",
    )
    filter_courses = st.multiselect("Mata kuliah", course_options, default=course_options)

selected_course_names = set(filter_courses)
selected_course_ids = {
    course["id"]
    for course in visible_courses
    if course["nama"] in selected_course_names
}
filtered_folders = [
    folder for folder in folders if folder["course_id"] in selected_course_ids
]

if search.strip():
    key = search.strip().lower()
    filtered_folders = [
        folder
        for folder in filtered_folders
        if key in (folder.get("nama") or "").lower()
        or key in (folder.get("keterangan") or "").lower()
    ]

if not filtered_folders:
    st.info("Belum ada folder arsip yang sesuai.")
    st.stop()

grouped = {}
for folder in filtered_folders:
    course = course_by_id.get(folder["course_id"])
    if course:
        grouped.setdefault(course["nama"], []).append(folder)

visible_groups = [
    (course_name, grouped.get(course_name, []))
    for course_name in course_options
    if grouped.get(course_name)
]

for course_name, course_folders in visible_groups:
    with st.expander(
        f"📚 {course_name} · {len(course_folders)} folder",
        expanded=len(visible_groups) == 1,
    ):
        for folder in course_folders:
            with st.container(border=True):
                st.markdown(f"**📁 {folder['nama']}**")
                if folder.get("keterangan"):
                    st.caption(folder["keterangan"])

                st.link_button("Buka Folder ↗", folder["url"], width="stretch")
