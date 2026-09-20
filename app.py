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

st.set_page_config(page_title="Dashboard — Tugas Kuliah", layout="wide", initial_sidebar_state="expanded")
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)

st.title("Dashboard Tugas Kuliah")
st.caption(f"S1 Sistem Informasi · {format_tanggal(now_wib().date())} · Waktu dalam WIB")

try:
    tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal terhubung ke Supabase.\n\nPesan asli: `{exc}`")
    st.stop()

st.divider()

# ---------------------------------------------------------------------
# 1. Ringkasan Atas (Metrics)
# ---------------------------------------------------------------------
terlewat = tugas_terlewat(tasks)
terdekat_all = deadline_terdekat(tasks, jumlah=100)
mendesak_count = sum(1 for t in terdekat_all if sisa_waktu(t["deadline"])[1] in ["mendesak", "dekat"])

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(
        f'<div style="border-left:3px solid {tokens["ink"]}; padding-left:12px;">'
        f'<div class="label-kecil">Total Tugas Aktif</div>'
        f'<h2 style="margin:0; font-size:1.8rem;">{len(tasks)}</h2>'
        f"</div>",
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f'<div style="border-left:3px solid {tokens["near"]}; padding-left:12px;">'
        f'<div class="label-kecil">Mendesak (&lt; 3 Hari)</div>'
        f'<h2 style="margin:0; font-size:1.8rem; color:{tokens["near"]};">{mendesak_count}</h2>'
        f"</div>",
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f'<div style="border-left:3px solid {tokens["urgent"]}; padding-left:12px;">'
        f'<div class="label-kecil">Sudah Lewat</div>'
        f'<h2 style="margin:0; font-size:1.8rem; color:{tokens["urgent"]};">{len(terlewat)}</h2>'
        f"</div>",
        unsafe_allow_html=True,
    )

st.write("")

# Peringatan jika ada tugas terlewat
if terlewat:
    daftar = ", ".join(t["judul"] for t in terlewat[:3])
    lebih = f" dan {len(terlewat) - 3} lainnya" if len(terlewat) - 3 > 0 else ""
    st.markdown(
        f'<div class="baris-list" style="--aksen:{tokens["urgent"]}">'
        f'<span class="badge-lewat">Sudah lewat</span>&nbsp; <strong>{daftar}</strong>{lebih}'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

# ---------------------------------------------------------------------
# 2. Konten Utama (Maksimal 3 Tugas Terdekat)
# ---------------------------------------------------------------------
kiri, kanan = st.columns([2.2, 1], gap="large")

with kiri:
    st.markdown("### Deadline Terdekat")

    terdekat_list = deadline_terdekat(tasks, jumlah=3)

    if not terdekat_list:
        st.write("Tidak ada deadline mendatang.")
    else:
        for t in terdekat_list:
            aksen = warna_matkul(tokens, t.get("mata_kuliah"))
            teks_sisa, level = sisa_waktu(t["deadline"])

            # Header tugas dengan indikator garis vertikal di kiri
            st.markdown(
                f'<div style="border-left: 3px solid {aksen}; padding-left: 10px; margin-top: 10px; margin-bottom: 8px;">'
                f'<div style="display:flex; justify-content:space-between; align-items:flex-start;">'
                f"<div>"
                f'<div style="font-size:1.1rem; font-weight:600;">{t["judul"]}</div>'
                f'<div style="font-size:0.88rem; color:{aksen}; font-weight:500;">{t["mata_kuliah"]} · <span class="label-kecil">{t.get("jenis", "-")}</span></div>'
                f'<div class="label-kecil">{format_deadline(t["deadline"])}</div>'
                f"</div>"
                f'<div style="text-align:right;">'
                f"{"<span class='badge-lewat'>Sudah lewat</span>" if level == 'lewat' else f"<span class='label-kecil' style='color:{warna_urgensi(tokens, level)}; font-weight:600'>{teks_sisa}</span>"}"
                f"</div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            ketentuan_html = (t.get("ketentuan") or "").strip()
            if ketentuan_html:
                with st.expander("Ketentuan & Instruksi"):
                    st.markdown(ketentuan_html, unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            with b1:
                if punya_link(t):
                    st.link_button("Buka VClass", t["link_vclass"], use_container_width=True)
            with b2:
                if t.get("file_soal"):
                    st.link_button("Download/Lihat File Soal", t["file_soal"], use_container_width=True)

            st.divider()

with kanan:
    st.markdown("### Ringkasan Mata Kuliah")

    count_per_matkul = {}
    for t in tasks:
        mk = t.get("mata_kuliah")
        count_per_matkul[mk] = count_per_matkul.get(mk, 0) + 1

    baris_matkul = []
    for m in MATA_KULIAH:
        jumlah = count_per_matkul.get(m, 0)
        aksen_mk = warna_matkul(tokens, m)
        badge_html = (
            f'<span style="float:right; font-weight:600; opacity:0.8;">{jumlah} tugas</span>'
            if jumlah > 0
            else '<span style="float:right; opacity:0.4;">0</span>'
        )

        baris_matkul.append(
            f'<div class="baris-list" style="--aksen:{aksen_mk}; margin-bottom:0.6rem;">'
            f'<div style="font-weight:500;">{m} {badge_html}</div>'
            f"</div>"
        )

    st.markdown("".join(baris_matkul), unsafe_allow_html=True)
