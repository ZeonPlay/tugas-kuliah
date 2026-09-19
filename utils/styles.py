"""
Satu tempat untuk semua styling kustom, supaya ketiga halaman (app, Kalender,
Admin) punya identitas visual yang sama persis. Dipanggil sekali di awal
setiap halaman lewat inject_base_css().

Konsep: "kartu indeks arsip akademik" — garis tipis, aksen warna di kiri
per elemen (bukan kotak penuh warna dengan shadow), tanpa emoji.
"""

import streamlit as st

# ---------------------------------------------------------------------
# Token warna — 6 nilai inti, dipakai konsisten di seluruh aplikasi.
# ---------------------------------------------------------------------
PAPER = "#F6F4EE"       # latar
INK = "#21252C"         # teks utama
INK_SOFT = "#5C6270"    # teks sekunder / caption
LINE = "#D8D3C6"        # garis pembatas
URGENT = "#A8442C"      # deadline lewat / mendesak (<24 jam)
NEAR = "#B9812E"        # deadline dekat (<3 hari)
SAFE = "#3F6B52"         # aman / selesai

# Warna per mata kuliah — hue berbeda-beda tapi saturasi & kecerahan
# sepadan, supaya tidak ada satu warna yang "berteriak" dibanding lainnya.
# Sengaja tidak memakai URGENT/NEAR/SAFE di sini supaya makna warna
# tidak tertukar antara "identitas mata kuliah" dan "status/urgensi".
COURSE_PALETTE = [
    "#5B7FA6",  # denim
    "#5E9C8C",  # teal
    "#C08B3E",  # ochre
    "#8073B3",  # plum
    "#7C9A5D",  # sage
    "#C77B5A",  # terracotta muda
    "#4F8FA6",  # steel blue
    "#A65B8C",  # mauve
    "#6B6E8C",  # blue-grey
]

STATUS_WARNA = {"Belum": INK_SOFT, "Dikerjakan": NEAR, "Selesai": SAFE}
PRIORITAS_WARNA = {"Tinggi": URGENT, "Sedang": NEAR, "Rendah": SAFE}


def _course_colors(nama_list: list[str]) -> dict[str, str]:
    return {
        nama: COURSE_PALETTE[i % len(COURSE_PALETTE)]
        for i, nama in enumerate(nama_list)
    }


def inject_base_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {{
            --paper: {PAPER};
            --ink: {INK};
            --ink-soft: {INK_SOFT};
            --line: {LINE};
            --urgent: {URGENT};
            --near: {NEAR};
            --safe: {SAFE};
        }}

        html, body, [class*="css"] {{
            font-family: 'IBM Plex Sans', sans-serif;
            color: var(--ink);
        }}

        .stApp {{
            background-color: var(--paper);
        }}

        h1, h2, h3 {{
            font-family: 'IBM Plex Serif', serif;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}

        h1 {{ font-size: 1.9rem; margin-bottom: 0.1rem; }}
        h2 {{ font-size: 1.35rem; }}
        h3 {{ font-size: 1.1rem; }}

        [data-testid="stCaptionContainer"] {{
            color: var(--ink-soft);
        }}

        hr, [data-testid="stDivider"] {{
            border-color: var(--line) !important;
        }}

        /* Tombol: sudut tegas, tanpa shadow, garis tipis */
        .stButton button, .stLinkButton a, .stDownloadButton button {{
            border-radius: 3px;
            border: 1px solid var(--ink);
            box-shadow: none;
        }}
        .stButton button[kind="primary"] {{
            background-color: var(--ink);
            border-color: var(--ink);
        }}

        /* Input & select: garis tipis konsisten dengan tema */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div {{
            border-radius: 3px !important;
            border-color: var(--line) !important;
        }}

        /* Sidebar lebih tenang, dipisah dari konten dengan garis, bukan shadow */
        [data-testid="stSidebar"] {{
            background-color: #EFEBDD;
            border-right: 1px solid var(--line);
        }}

        /* Kartu baris tugas: garis tipis + aksen warna di kiri */
        .kartu-tugas {{
            border: 1px solid var(--line);
            border-left: 4px solid var(--aksen, var(--ink));
            border-radius: 2px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.6rem;
            background-color: #FCFBF8;
        }}

        .baris-list {{
            border-left: 3px solid var(--aksen, var(--line));
            padding: 0.35rem 0 0.35rem 0.7rem;
            margin-bottom: 0.45rem;
        }}

        .label-kecil {{
            font-size: 0.78rem;
            color: var(--ink-soft);
            text-transform: none;
        }}

        .titik-status {{
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: var(--titik, var(--ink-soft));
            margin-right: 0.4em;
        }}

        /* Mobile: rapatkan jarak & kecilkan judul supaya tidak terasa kaku */
        @media (max-width: 640px) {{
            h1 {{ font-size: 1.5rem; }}
            h2 {{ font-size: 1.15rem; }}
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.5rem;
            }}
            .kartu-tugas {{ padding: 0.65rem 0.8rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def calendar_css() -> str:
    """CSS untuk diteruskan ke parameter custom_css milik streamlit-calendar.

    Komponen kalender dirender di iframe terpisah, jadi CSS di
    inject_base_css() di atas TIDAK menjangkaunya — harus lewat sini.
    """
    return f"""
        .fc {{
            font-family: 'IBM Plex Sans', sans-serif;
            color: {INK};
        }}
        .fc-toolbar-title {{
            font-family: 'IBM Plex Serif', serif;
            font-size: 1.15rem !important;
            font-weight: 600;
        }}
        .fc-button {{
            background-color: transparent !important;
            border: 1px solid {INK} !important;
            color: {INK} !important;
            box-shadow: none !important;
            border-radius: 3px !important;
            text-transform: none !important;
        }}
        .fc-button:hover {{
            background-color: {INK} !important;
            color: {PAPER} !important;
        }}
        .fc-button-active {{
            background-color: {INK} !important;
            color: {PAPER} !important;
        }}
        .fc-daygrid-day-number {{
            color: {INK};
            font-size: 0.85rem;
        }}
        .fc-col-header-cell-cushion {{
            color: {INK_SOFT};
            font-weight: 500;
            font-size: 0.8rem;
        }}
        .fc-event {{
            border-radius: 2px;
            border: none;
            font-size: 0.78rem;
            padding: 1px 4px;
        }}
        .fc-daygrid-day.fc-day-today {{
            background-color: rgba(168, 68, 44, 0.08) !important;
        }}
        @media (max-width: 640px) {{
            .fc-toolbar {{
                flex-direction: column;
                gap: 0.4rem;
            }}
            .fc-toolbar-title {{
                font-size: 1rem !important;
            }}
            .fc-event {{
                font-size: 0.68rem;
            }}
        }}
    """
