import streamlit as st

from utils.krs import get_active_semester, get_krs_for_semester, reset_krs, set_active_semester, set_krs_for_semester
from utils.styles import inject_base_css, render_theme_toggle
from utils.supabase_client import ConfigError, fetch_courses

st.set_page_config(page_title="KRS Saya", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

mode = render_theme_toggle()
inject_base_css(mode)

st.title("KRS Saya")
st.caption("Pilih mata kuliah yang sedang kamu ambil. Dashboard dan kalender akan mengikuti pilihan ini.")

try:
    courses = fetch_courses()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal mengambil daftar mata kuliah: {exc}")
    st.stop()

if not courses:
    st.info("Belum ada mata kuliah di katalog. Minta admin menambahkannya terlebih dahulu.")
    st.stop()

semesters = sorted({int(course["semester"]) for course in courses if course.get("semester") is not None})
if not semesters:
    st.info("Belum ada mata kuliah yang memiliki semester.")
    st.stop()

active_semester = get_active_semester()
if active_semester not in semesters:
    active_semester = max(semesters)
    set_active_semester(active_semester)

active_semester = st.selectbox(
    "Semester aktif",
    semesters,
    index=semesters.index(active_semester),
    format_func=lambda value: f"Semester {value}",
)

if get_active_semester() != active_semester:
    set_active_semester(active_semester)

semester_courses = [course for course in courses if int(course["semester"]) == active_semester]
wajib = [course["nama"] for course in semester_courses if course.get("kategori") == "Wajib"]
pilihan = [course["nama"] for course in semester_courses if course.get("kategori") == "Pilihan"]
lainnya = [
    course["nama"]
    for course in semester_courses
    if course.get("kategori") not in {"Wajib", "Pilihan"}
]

tersimpan = get_krs_for_semester(active_semester)
default_pilihan = [name for name in tersimpan if name in pilihan]
default_lainnya = [name for name in tersimpan if name in lainnya]

st.subheader(f"Semester {active_semester}")

if wajib:
    st.write("**Mata kuliah wajib**")
    st.caption("Otomatis masuk KRS.")

    for name in wajib:
        st.markdown(
            f'<div class="krs-course-item"><span class="krs-check">✓</span><span>{name}</span></div>',
            unsafe_allow_html=True,
        )

pilihan_terpilih = st.multiselect(
    "Mata kuliah pilihan yang kamu ambil",
    pilihan,
    default=default_pilihan,
    placeholder="Pilih mata kuliah pilihan...",
)

if lainnya:
    tambahan_kurikulum = st.multiselect(
        "Mata kuliah lain",
        lainnya,
        default=default_lainnya,
        placeholder="Pilih bila ada mata kuliah yang belum dikategorikan...",
    )
else:
    tambahan_kurikulum = []

semua_dipilih = list(dict.fromkeys(wajib + pilihan_terpilih + tambahan_kurikulum))
set_krs_for_semester(active_semester, semua_dipilih)

st.divider()
st.subheader("Ringkasan KRS")
st.metric("Mata kuliah aktif", len(semua_dipilih))

if semua_dipilih:
    for name in semua_dipilih:
        st.markdown(
            f'<div class="krs-summary-item">{name}</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("Belum ada mata kuliah terpilih.")

st.caption("Perubahan KRS tersimpan otomatis selama sesi browser ini.")

with st.expander("Pengaturan ulang", expanded=False):
    st.caption("Gunakan ini bila ingin menghapus pilihan KRS dari semua semester.")
    if st.button("Reset KRS semua semester", type="secondary", width="stretch"):
        reset_krs()
        st.rerun()
