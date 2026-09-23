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
    warna_urgensi,
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

m1, m2, m3 = st.columns(3)

metric_1 = f"""
<div class="metric-card" style="--aksen: {tokens["ink"]};">
    <div class="metric-title">Total Tugas Aktif</div>
    <div class="metric-value">{len(tasks)}</div>
</div>
"""
with m1:
    st.markdown(metric_1, unsafe_allow_html=True)

metric_2 = f"""
<div class="metric-card" style="--aksen: {tokens["near"]};">
    <div class="metric-title">Mendesak (&lt; 3 Hari)</div>
    <div class="metric-value" style="color: {tokens["near"]};">{mendesak_count}</div>
</div>
"""
with m2:
    st.markdown(metric_2, unsafe_allow_html=True)

metric_3 = f"""
<div class="metric-card" style="--aksen: {tokens["urgent"]};">
    <div class="metric-title">Sudah Lewat</div>
    <div class="metric-value" style="color: {tokens["urgent"]};">{len(terlewat)}</div>
</div>
"""
with m3:
    st.markdown(metric_3, unsafe_allow_html=True)

if terlewat:
    daftar = ", ".join(t["judul"] for t in terlewat[:3])
    lebih = f" dan {len(terlewat) - 3} lainnya" if len(terlewat) - 3 > 0 else ""
    st.warning(f"Tugas Terlewat: {daftar}{lebih}")

st.write("")

kiri, kanan = st.columns([2, 1], gap="large")
with kiri:
    st.subheader("Deadline Terdekat")
    terdekat_list = deadline_terdekat(tasks, jumlah=3)

    if not terdekat_list:
        st.info("Tidak ada deadline mendatang. Saatnya bersantai.")
    else:
        for t in terdekat_list:
            aksen = warna_matkul(tokens, t.get("mata_kuliah"))
            teks_sisa, level = sisa_waktu(t["deadline"])
            badge_class = "badge-lewat" if level == "lewat" else "badge-aman"
            badge_color = tokens["urgent"] if level == "lewat" else tokens["safe"]

            # HINDARI INDENTASI PADA HTML AGAR TIDAK DIBACA SEBAGAI MARKDOWN CODE BLOCK
            html_card = f"""
<div class="kartu-tugas" style="border-left: 5px solid {aksen};">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
        <span style="color: {aksen}; font-weight: 600; font-size: 0.85rem;">{t["mata_kuliah"]} | {t.get("jenis", "-")}</span>
        <span class="{badge_class}" style="color: {badge_color} !important;">{teks_sisa}</span>
    </div>
    <h3 style="margin: 0 0 4px 0; font-size: 1.15rem; color: var(--ink) !important;">{t["judul"]}</h3>
    <div style="color: var(--ink-soft) !important; font-size: 0.85rem;">Batas Waktu: {format_deadline(t["deadline"])}</div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)

            ketentuan_html = (t.get("ketentuan") or "").strip()
            if ketentuan_html:
                with st.expander("Detail & Instruksi"):
                    st.markdown(f'<div class="ketentuan-body">{ketentuan_html}</div>', unsafe_allow_html=True)

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
            html_matkul = f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--kartu-bg); border: 1px solid var(--line); border-radius: 8px; margin-bottom: 8px;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <div style="width: 12px; height: 12px; border-radius: 50%; background-color: {aksen_mk};"></div>
        <span style="font-weight: 500; color: var(--ink) !important; font-size: 0.9rem;">{m}</span>
    </div>
    <span style="font-weight: 700; color: var(--ink) !important;">{jumlah}</span>
</div>
"""
            st.markdown(html_matkul, unsafe_allow_html=True)
