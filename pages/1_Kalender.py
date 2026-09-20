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
from utils.supabase_client import ConfigError, fetch_tasks

st.set_page_config(page_title="Kalender — Tugas Kuliah", layout="wide")
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)

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

with st.sidebar:
    st.markdown('<p class="label-kecil">Filter</p>', unsafe_allow_html=True)
    filter_jenis = st.multiselect("Jenis", JENIS, default=JENIS, label_visibility="collapsed")

    st.divider()
    st.markdown('<p class="label-kecil">Deadline terdekat</p>', unsafe_allow_html=True)

    terdekat = deadline_terdekat(semua_tasks, jumlah=5)
    if not terdekat:
        st.caption("Tidak ada deadline yang akan datang.")
    else:
        baris = []
        for t in terdekat:
            teks_sisa, level = sisa_waktu(t["deadline"])
            warna = warna_urgensi(tokens, level)
            baris.append(
                f'<div class="baris-list" style="--aksen:{warna}">'
                f'<div style="font-weight:500">{t["judul"]}</div>'
                f'<div class="label-kecil">{t["mata_kuliah"]} · {format_deadline(t["deadline"])}</div>'
                f'<div class="label-kecil" style="color:{warna}">{teks_sisa}</div>'
                f"</div>"
            )
        st.markdown("".join(baris), unsafe_allow_html=True)

tasks = [t for t in semua_tasks if t.get("jenis") in filter_jenis]

opsi_kalender = {
    "initialView": "dayGridMonth",
    "locale": "id",
    "firstDay": 1,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,listMonth",
    },
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

st.caption("Setiap tanggal menampilkan jumlah deadline hari itu — klik untuk melihat detail tugasnya di bawah.")

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
    aksen = warna_matkul(tokens, t.get("mata_kuliah"))
    teks_sisa, level = sisa_waktu(t["deadline"])

    st.markdown(f'<div class="kartu-tugas" style="--aksen:{aksen}">', unsafe_allow_html=True)

    atas_kiri, atas_kanan = st.columns([3, 1])
    with atas_kiri:
        st.markdown(f"#### {t['judul']}")
        st.markdown(
            f'<span style="color:{aksen};font-weight:500">{t["mata_kuliah"]}</span>'
            f' &nbsp;·&nbsp; <span class="label-kecil">{t.get("jenis", "-")}</span>',
            unsafe_allow_html=True,
        )
        st.caption(format_deadline(t["deadline"]))

    with atas_kanan:
        if level == "lewat":
            st.markdown('<span class="badge-lewat">Sudah lewat</span>', unsafe_allow_html=True)
        else:
            warna_sisa = warna_urgensi(tokens, level)
            st.markdown(
                f'<span class="label-kecil" style="color:{warna_sisa}">{teks_sisa}</span>',
                unsafe_allow_html=True,
            )

    ketentuan_html = (t.get("ketentuan") or "").strip()
    if ketentuan_html:
        with st.expander("Ketentuan"):
            st.markdown(ketentuan_html, unsafe_allow_html=True)

    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if punya_link(t):
            st.link_button("Buka di VClass", t["link_vclass"], use_container_width=True)
        else:
            st.caption("Tanpa link — lihat bagian Ketentuan untuk cara pengumpulan.")

    with btn_c2:
        if t.get("file_soal"):
            st.link_button("Lihat / Download File Soal", t["file_soal"], use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
