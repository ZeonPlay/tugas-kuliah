import streamlit as st

from utils.helpers import format_deadline
from utils.krs import get_active_krs, get_active_semester, is_krs_configured
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.supabase_client import ConfigError, fetch_courses, fetch_modules


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
st.caption("Kumpulan modul dan materi kuliah yang dibagikan asisten dosen.")


try:
    courses = fetch_courses()
    modules = fetch_modules()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal mengambil arsip modul: {exc}")
    st.stop()


course_by_name = {course["nama"]: course for course in courses}
active_krs = get_active_krs() if is_krs_configured() else []

if active_krs:
    visible_courses = [course for course in courses if course["nama"] in active_krs]
    modules = [module for module in modules if module["course_id"] in {course["id"] for course in visible_courses}]
    st.caption(f"📚 KRS aktif · Semester {get_active_semester()}")
else:
    visible_courses = courses

course_options = [course["nama"] for course in visible_courses]

with st.expander("🔎 Cari & filter modul", expanded=False):
    search = st.text_input(
        "Cari modul",
        placeholder="Contoh: modul basis data",
        label_visibility="collapsed",
    )
    filter_courses = st.multiselect("Mata kuliah", course_options, default=course_options)

selected_course_names = set(filter_courses)
filtered_modules = [
    module
    for module in modules
    if course_by_name.get(next(
        (name for name in course_by_name if course_by_name[name]["id"] == module["course_id"]),
        "",
    ), {}).get("nama") in selected_course_names
]

if search.strip():
    key = search.strip().lower()
    filtered_modules = [
        module
        for module in filtered_modules
        if key in (module.get("judul") or "").lower()
        or key in (module.get("keterangan") or "").lower()
    ]

if not filtered_modules:
    st.info("Belum ada modul yang sesuai.")
    st.stop()

# Group by mata kuliah so the archive remains easy to scan.
grouped = {}
for module in filtered_modules:
    course = next(
        (course for course in visible_courses if course["id"] == module["course_id"]),
        None,
    )
    if course:
        grouped.setdefault(course["nama"], []).append(module)

for course_name in course_options:
    course_modules = grouped.get(course_name, [])
    if not course_modules:
        continue

    st.subheader(course_name)
    for module in course_modules:
        prefix = f"Modul {module['urutan']}" if module.get("urutan") is not None else "Materi"
        with st.container(border=True):
            st.markdown(f"### {prefix} — {module['judul']}")
            if module.get("keterangan"):
                st.caption(module["keterangan"])

            url = module["url"]
            host = url.split("/")[2].lower() if "://" in url and "/" in url[8:] else ""
            is_drive = host == "drive.google.com" or host.endswith(".drive.google.com") or host == "docs.google.com"
            label = "Buka Google Drive ↗" if is_drive else "Buka Materi ↗"
            st.link_button(label, url, width="stretch")
