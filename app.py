import streamlit as st

from utils.helpers import (
    MATA_KULIAH,
    deadline_terdekat,
    format_deadline,
    format_tanggal,
    now_wib,
    punya_link,
    sisa_waktu,
    tugas_terlewat,
    warna_matkul,
)
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.supabase_client import ConfigError, fetch_tasks

st.set_page_config(page_title="Dashboard Tugas Kuliah", layout="wide", initial_sidebar_state="expanded")
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)

st.title("Dashboard Tugas Kuliah")
st.caption(f"S1 Sistem Informasi | {format_tanggal(now_wib().date())} | WIB")

try:
    tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal terhubung ke Supabase.\n\nPesan asli: `{exc}`")
    st.stop()

st.divider()

terlewat = tugas_terlewat(tasks)
terdekat_all = deadline_terdekat(tasks, jumlah=100)
mendesak_count = sum(1 for t in terdekat_all if sisa_waktu(t["deadline"])[1] in ["mendesak", "dekat"])

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.info(f"**Total Tugas Aktif:**\n\n### {len(tasks)}")
with col_m2:
    st.warning(f"**Mendesak (< 3 Hari):**\n\n### {mendesak_count}")
with col_m3:
    st.error(f"**Sudah Lewat:**\n\n### {len(terlewat)}")

if terlewat:
    daftar = ", ".join(t["judul"] for t in terlewat[:3])
    lebih = f" dan {len(terlewat) - 3} lainnya" if len(terlewat) - 3 > 0 else ""
    st.error(f"Tugas Terlewat: {daftar}{lebih}")

st.write("")

kiri, kanan = st.columns([2, 1], gap="large")
with kiri:
    st.subheader("Deadline Terdekat")
    terdekat_list = deadline_terdekat(tasks, jumlah=3)

    if not terdekat_list:
        st.success("Tidak ada deadline mendatang. Saatnya bersantai.")
    else:
        for t in terdekat_list:
            aksen = warna_matkul(tokens, t.get("mata_kuliah"))
            teks_sisa, level = sisa_waktu(t["deadline"])
            badge_bg = "rgba(239, 68, 68, 0.2)" if level == "lewat" else "rgba(16, 185, 129, 0.2)"
            badge_color = "#ef4444" if level == "lewat" else "#10b981"

            card_html = f"""
<div style="background-color: var(--secondary-background-color); border: 1px solid rgba(150, 150, 150, 0.2); border-left: 5px solid {aksen}; border-radius: 8px; padding: 15px; margin-bottom: 10px; color: var(--text-color);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="color: {aksen}; font-weight: 600; font-size: 0.85rem;">{t["mata_kuliah"]} | {t.get("jenis", "-")}</span>
        <span style="background-color: {badge_bg}; color: {badge_color}; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;">{teks_sisa}</span>
    </div>
    <h3 style="margin: 0 0 5px 0; padding: 0; color: var(--text-color);">{t["judul"]}</h3>
    <div style="font-size: 0.85rem; opacity: 0.8; color: var(--text-color);">Batas Waktu: {format_deadline(t["deadline"])}</div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)

            ketentuan_html = (t.get("ketentuan") or "").strip()
            if ketentuan_html:
                with st.expander("Detail & Instruksi"):
                    st.markdown(ketentuan_html, unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            if punya_link(t):
                b1.link_button("Buka VClass", t["link_vclass"], use_container_width=True)
            if t.get("file_soal"):
                b2.link_button("Download File Soal", t["file_soal"], use_container_width=True)
            st.write("")

with kanan:
    st.subheader("Ringkasan Mata Kuliah")
    count_per_matkul = {}
    for t in tasks:
        mk = t.get("mata_kuliah")
        count_per_matkul[mk] = count_per_matkul.get(mk, 0) + 1

    for m in MATA_KULIAH:
        jumlah = count_per_matkul.get(m, 0)
        aksen_mk = warna_matkul(tokens, m)
        if jumlah > 0:
            matkul_html = f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background-color: var(--secondary-background-color); border: 1px solid rgba(150, 150, 150, 0.2); border-radius: 8px; margin-bottom: 8px;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <div style="width: 12px; height: 12px; border-radius: 50%; background-color: {aksen_mk};"></div>
        <span style="font-weight: 500; font-size: 0.9rem; color: var(--text-color);">{m}</span>
    </div>
    <span style="font-weight: 700; color: var(--text-color);">{jumlah}</span>
</div>
"""
            st.markdown(matkul_html, unsafe_allow_html=True)
