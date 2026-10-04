import streamlit as st

from utils.components import render_task_card
from utils.helpers import (
    JENIS,
    deadline_terdekat,
    format_tanggal,
    now_wib,
    sisa_waktu,
    tugas_terlewat,
    tugas_baru_terlewat,
    warna_matkul,
)
from utils.krs import get_active_krs, get_active_semester, is_krs_configured
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.presence import render_presence
from utils.supabase_client import ConfigError, fetch_courses, fetch_tasks

st.set_page_config(
    page_title="Tugas Kuliah",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)
render_presence("Beranda")

st.title("Tugas Kuliah")
st.caption(f"S1 Sistem Informasi · {format_tanggal(now_wib().date())} · WIB")

try:
    all_tasks = fetch_tasks()
    all_courses = fetch_courses()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\\n\\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal terhubung ke Supabase.\\n\\nPesan asli: {exc}")
    st.stop()

course_names = [course["nama"] for course in all_courses]
legacy_courses = sorted(
    {
        task.get("mata_kuliah")
        for task in all_tasks
        if task.get("mata_kuliah") and task.get("mata_kuliah") not in course_names
    }
)
course_options = course_names + legacy_courses

active_krs = get_active_krs() if is_krs_configured() else []
if active_krs:
    all_tasks = [task for task in all_tasks if task.get("mata_kuliah") in active_krs]
    semester = get_active_semester()
    st.caption(f"📚 KRS aktif · Semester {semester} · {len(active_krs)} mata kuliah")
elif is_krs_configured():
    st.caption("📚 KRS aktif, tetapi belum ada mata kuliah yang dipilih.")

visible_course_options = active_krs or course_options

c_nav1, c_nav2 = st.columns(2)
c_nav1.page_link(
    "pages/3_KRS.py",
    label="Atur KRS Saya",
    icon=":material/tune:",
    width="stretch",
    help="Atur mata kuliah yang kamu ambil di KRS.",
)
c_nav2.page_link(
    "pages/4_Modul.py",
    label="Arsip Modul",
    icon=":material/folder_open:",
    width="stretch",
    help="Buka arsip folder modul per mata kuliah.",
)

with st.expander("🔎 Cari & filter tugas", expanded=False):
    search = st.text_input(
        "Cari tugas",
        placeholder="Contoh: laporan basis data",
        label_visibility="collapsed",
    )
    f_matkul = st.multiselect("Mata kuliah", visible_course_options)
    f_jenis = st.multiselect("Jenis", JENIS)

tasks = all_tasks
if f_matkul:
    tasks = [t for t in tasks if t.get("mata_kuliah") in f_matkul]
if f_jenis:
    tasks = [t for t in tasks if t.get("jenis") in f_jenis]
if search.strip():
    key = search.strip().lower()
    tasks = [
        t for t in tasks
        if key in (t.get("judul") or "").lower()
        or key in (t.get("mata_kuliah") or "").lower()
        or key in (t.get("ketentuan") or "").lower()
    ]

terlewat = tugas_terlewat(tasks)
baru_terlewat = tugas_baru_terlewat(tasks, hari=3)
terdekat = deadline_terdekat(tasks, jumlah=5)
mendesak_count = sum(
    1 for t in terdekat
    if sisa_waktu(t["deadline"])[1] in {"mendesak", "dekat"}
)

m1, m2, m3 = st.columns(3)
m1.metric("Tugas ditampilkan", len(tasks))
m2.metric("Deadline dekat", mendesak_count)
m3.metric("Sudah lewat", len(terlewat))

if search or f_matkul or f_jenis:
    st.caption(f"Menampilkan {len(tasks)} dari {len(all_tasks)} tugas.")

if baru_terlewat:
    st.markdown(
        """
        <div style="
            padding: 14px 16px;
            border: 1px solid rgba(245,158,11,.30);
            border-radius: 14px;
            background: rgba(245,158,11,.08);
            margin-bottom: 12px;
        ">
            <div style="font-weight:800;font-size:1rem;">⚠️ Baru terlewat</div>
            <div style="opacity:.72;font-size:.82rem;margin-top:3px;">
                Deadline yang lewat dalam 3 hari terakhir · buka langsung untuk segera mengerjakannya.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for task in baru_terlewat[:3]:
        with st.container(border=True):
            left, action1, action2 = st.columns([5, 1.6, 1.6], vertical_alignment="center")

            with left:
                st.markdown(
                    f"**{task.get('judul') or 'Tugas tanpa judul'}**"
                )
                st.caption(
                    f"{task.get('mata_kuliah') or 'Tanpa Mata Kuliah'} · Deadline {format_deadline(task['deadline'])}"
                )

            vclass_url = (task.get("link_vclass") or "").strip()
            file_url = (task.get("file_soal") or "").strip()

            if vclass_url:
                action1.link_button(
                    "Kerjakan ↗",
                    vclass_url,
                    width="stretch",
                )
            elif file_url:
                action1.link_button(
                    "Buka soal ↗",
                    file_url,
                    width="stretch",
                )

            if vclass_url and file_url:
                action2.link_button(
                    "File soal ↗",
                    file_url,
                    width="stretch",
                )
            else:
                action2.markdown("")

    if len(baru_terlewat) > 3:
        st.caption(
            f"Dan {len(baru_terlewat) - 3} tugas baru terlewat lainnya ada di daftar tugas."
        )

st.divider()

kiri, kanan = st.columns([2, 1], gap="large")

with kiri:
    st.subheader("Deadline Terdekat")
    if not terdekat:
        st.success("Tidak ada deadline mendatang. Saatnya bersantai. 🎉")
    else:
        for task in terdekat:
            render_task_card(task, tokens)

with kanan:
    st.subheader("Mata Kuliah")
    count_per_matkul = {}
    for task in all_tasks:
        course = task.get("mata_kuliah")
        count_per_matkul[course] = count_per_matkul.get(course, 0) + 1

    visible_courses = [
        course for course in course_options
        if count_per_matkul.get(course, 0) > 0
    ]

    if not visible_courses:
        st.info("Belum ada tugas.")
    else:
        for course in visible_courses:
            accent = warna_matkul(tokens, course)
            st.markdown(
                f"""
                <div class="course-row">
                    <span class="course-dot" style="background:{accent}"></span>
                    <span>{course}</span>
                    <strong>{count_per_matkul[course]}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
