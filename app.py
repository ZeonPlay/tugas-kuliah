import streamlit as st

from utils.helpers import MATA_KULIAH, deadline_terdekat, format_tanggal, now_wib, parse_deadline, tugas_terlewat
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.supabase_client import ConfigError, fetch_tasks

st.set_page_config(page_title="Tugas Kuliah", layout="wide", initial_sidebar_state="expanded")
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)

st.title("Tugas Kuliah")
st.caption(f"S1 Sistem Informasi · {format_tanggal(now_wib().date())} · waktu ditampilkan dalam WIB")

try:
    tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(
        "Gagal terhubung ke Supabase.\n\n"
        f"Pesan asli: `{exc}`\n\n"
        "Cek URL & anon key, tabel `tasks` sudah dibuat (jalankan `sql/setup.sql`), "
        "dan project Supabase tidak sedang paused."
    )
    st.stop()

st.divider()

terlewat = tugas_terlewat(tasks)
if terlewat:
    daftar = ", ".join(t["judul"] for t in terlewat[:3])
    lebih = f" dan {len(terlewat) - 3} lainnya" if len(terlewat) - 3 > 0 else ""
    st.markdown(
        f'<div class="baris-list" style="--aksen:{tokens["urgent"]}">'
        f'<span class="badge-lewat">Sudah lewat</span>&nbsp; {daftar}{lebih}'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

terdekat = deadline_terdekat(tasks, jumlah=1)

kiri, kanan = st.columns([2, 1], gap="large")

with kiri:
    st.markdown('<p class="label-kecil">Deadline berikutnya</p>', unsafe_allow_html=True)
    if terdekat:
        t = terdekat[0]
        dt = parse_deadline(t["deadline"])
        st.markdown(f"### {t['judul']}")
        st.write(f"{t['mata_kuliah']} — {t.get('jenis', '-')}")
        st.caption(f"{format_tanggal(dt.date())} · {dt:%H:%M} WIB")
    else:
        st.write("Tidak ada deadline yang akan datang.")

    st.write("")
    st.caption(f"{len(tasks)} total tugas tercatat")

    st.write("")
    st.markdown(
        "Buka **Kalender** di sidebar untuk melihat semua deadline dan detail tiap tugas. "
        "Tugas yang tidak punya link VClass tetap dicatat — cara pengumpulannya ada di "
        "bagian Ketentuan pada tugas tersebut."
    )

with kanan:
    st.markdown('<p class="label-kecil">Mata kuliah</p>', unsafe_allow_html=True)
    st.markdown(
        "".join(
            f'<div class="baris-list" style="--aksen:{tokens["ink_soft"]}"><span class="label-kecil">{m}</span></div>'
            for m in MATA_KULIAH
        ),
        unsafe_allow_html=True,
    )
