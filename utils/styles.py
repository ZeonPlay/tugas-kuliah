"""
Satu tempat untuk semua styling kustom + dukungan tema gelap/terang.

Semua warna diambil lewat get_tokens(dark) — bukan konstanta modul tetap —
supaya toggle tema di sidebar otomatis mengubah SEMUA halaman sekaligus,
termasuk warna kalender (yang dirender di iframe terpisah, jadi butuh
custom_css sendiri lewat calendar_css()).
"""

import colorsys

import streamlit as st

# ---------------------------------------------------------------------
# Token warna — tema terang (dasar)
# ---------------------------------------------------------------------
_LIGHT = {
    "paper": "#F6F4EE",
    "ink": "#21252C",
    "ink_soft": "#5C6270",
    "line": "#D8D3C6",
    "kartu_bg": "#FCFBF8",
    "urgent": "#A8442C",
    "near": "#B9812E",
    "safe": "#3F6B52",
    "course": [
        "#5B7FA6",
        "#5E9C8C",
        "#C08B3E",
        "#8073B3",
        "#7C9A5D",
        "#C77B5A",
        "#4F8FA6",
        "#A65B8C",
        "#6B6E8C",
    ],
}

_DARK = {
    "paper": "#1B1C20",
    "ink": "#EDEAE2",
    "ink_soft": "#A6A9B3",
    "line": "#3B3D44",
    "kartu_bg": "#232428",
    "urgent": "#D9694C",
    "near": "#D9A354",
    "safe": "#6FA184",
    # course diisi di bawah, dihitung dari _LIGHT["course"] supaya konsisten
}


def _terangkan(hex_warna: str, tambahan_lightness: float) -> str:
    """Naikkan lightness (HSL) sebuah warna hex, dipakai supaya warna
    mata kuliah tetap terbaca di latar gelap tanpa perlu menebak-nebak
    hex baru satu per satu."""
    hex_warna = hex_warna.lstrip("#")
    r, g, b = (int(hex_warna[i : i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(0.82, l + tambahan_lightness)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


_DARK["course"] = [_terangkan(c, 0.18) for c in _LIGHT["course"]]


def get_tokens(dark: bool) -> dict:
    return _DARK if dark else _LIGHT


# ---------------------------------------------------------------------
# Toggle tema — dipanggil di sidebar tiap halaman, SEBELUM inject_base_css
# ---------------------------------------------------------------------
def render_theme_toggle() -> bool:
    with st.sidebar:
        gelap = st.toggle("Tema gelap", key="tema_gelap")
    return gelap


# ---------------------------------------------------------------------
# CSS halaman utama
# ---------------------------------------------------------------------
def inject_base_css(dark: bool) -> None:
    t = get_tokens(dark)
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {{
            --paper: {t["paper"]};
            --ink: {t["ink"]};
            --ink-soft: {t["ink_soft"]};
            --line: {t["line"]};
            --kartu-bg: {t["kartu_bg"]};
            --urgent: {t["urgent"]};
            --near: {t["near"]};
            --safe: {t["safe"]};
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
            color: var(--ink);
        }}

        h1 {{ font-size: 1.9rem; margin-bottom: 0.1rem; }}
        h2 {{ font-size: 1.35rem; }}
        h3 {{ font-size: 1.1rem; }}

        p, span, div, label {{ color: var(--ink); }}

        [data-testid="stCaptionContainer"] {{ color: var(--ink-soft) !important; }}

        hr, [data-testid="stDivider"] {{ border-color: var(--line) !important; }}

        .stButton button, .stLinkButton a, .stDownloadButton button {{
            border-radius: 3px;
            border: 1px solid var(--ink);
            box-shadow: none;
            color: var(--ink);
            background-color: transparent;
        }}
        .stButton button[kind="primary"] {{
            background-color: var(--ink);
            border-color: var(--ink);
            color: var(--paper);
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div {{
            border-radius: 3px !important;
            border-color: var(--line) !important;
            background-color: var(--kartu-bg) !important;
            color: var(--ink) !important;
        }}

        [data-testid="stSidebar"] {{
            background-color: var(--kartu-bg);
            border-right: 1px solid var(--line);
        }}

        .kartu-tugas {{
            border: 1px solid var(--line);
            border-left: 4px solid var(--aksen, var(--ink));
            border-radius: 2px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.6rem;
            background-color: var(--kartu-bg);
        }}

        .baris-list {{
            border-left: 3px solid var(--aksen, var(--line));
            padding: 0.35rem 0 0.35rem 0.7rem;
            margin-bottom: 0.45rem;
        }}

        .label-kecil {{
            font-size: 0.78rem;
            color: var(--ink-soft);
        }}

        .titik-status {{
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: var(--titik, var(--ink-soft));
            margin-right: 0.4em;
        }}

        .badge-lewat {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--urgent);
            border: 1px solid var(--urgent);
            border-radius: 3px;
            padding: 0.05rem 0.45rem;
        }}

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


def calendar_css(dark: bool) -> str:
    """CSS untuk parameter custom_css milik streamlit-calendar.

    Komponen kalender dirender di iframe terpisah, jadi CSS di
    inject_base_css() TIDAK menjangkaunya — harus lewat sini.
    """
    t = get_tokens(dark)
    ink, paper, ink_soft, urgent = t["ink"], t["paper"], t["ink_soft"], t["urgent"]
    return f"""
        .fc {{
            font-family: 'IBM Plex Sans', sans-serif;
            color: {ink};
            background-color: {paper};
        }}
        .fc-toolbar-title {{
            font-family: 'IBM Plex Serif', serif;
            font-size: 1.15rem !important;
            font-weight: 600;
            color: {ink};
        }}
        .fc-button {{
            background-color: transparent !important;
            border: 1px solid {ink} !important;
            color: {ink} !important;
            box-shadow: none !important;
            border-radius: 3px !important;
            text-transform: none !important;
        }}
        .fc-button:hover {{
            background-color: {ink} !important;
            color: {paper} !important;
        }}
        .fc-button-active {{
            background-color: {ink} !important;
            color: {paper} !important;
        }}
        .fc-daygrid-day-number {{
            color: {ink};
            font-size: 0.85rem;
        }}
        .fc-col-header-cell-cushion {{
            color: {ink_soft};
            font-weight: 500;
            font-size: 0.8rem;
        }}
        .fc-scrollgrid, .fc-theme-standard td, .fc-theme-standard th {{
            border-color: {ink_soft}33;
        }}
        /* Satu event ringkasan per tanggal ("2 deadline") — dibuat besar
           dan jadi satu blok penuh supaya gampang diklik di HP, bukan
           tumpukan chip kecil per tugas seperti sebelumnya. */
        .fc-event {{
            border-radius: 3px;
            border: none;
            font-size: 0.8rem;
            font-weight: 500;
            padding: 3px 5px;
            cursor: pointer;
        }}
        .fc-daygrid-day.fc-day-today {{
            background-color: {urgent}14 !important;
        }}
        @media (max-width: 640px) {{
            .fc-toolbar {{
                flex-direction: column;
                gap: 0.4rem;
            }}
            .fc-toolbar-title {{ font-size: 1rem !important; }}
            .fc-event {{ font-size: 0.72rem; padding: 4px 3px; }}
            .fc-daygrid-day-number {{ font-size: 0.75rem; }}
        }}
    """
