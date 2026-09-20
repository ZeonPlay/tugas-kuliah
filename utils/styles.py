"""
Satu tempat untuk semua styling kustom + dukungan tema gelap/terang/sistem.
"""

import colorsys

import streamlit as st

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
}


def _terangkan(hex_warna: str, tambahan_lightness: float) -> str:
    hex_warna = hex_warna.lstrip("#")
    r, g, b = (int(hex_warna[i : i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(0.82, l + tambahan_lightness)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


_DARK["course"] = [_terangkan(c, 0.18) for c in _LIGHT["course"]]


def get_tokens(mode: str | bool = "Sistem") -> dict:
    if mode is True or mode == "Gelap":
        return _DARK
    elif mode is False or mode == "Terang":
        return _LIGHT
    return _LIGHT


def render_theme_toggle() -> str:
    if "tema_mode" not in st.session_state:
        st.session_state["tema_mode"] = "Sistem"

    opsi = ["Sistem", "Terang", "Gelap"]
    idx = opsi.index(st.session_state["tema_mode"]) if st.session_state["tema_mode"] in opsi else 0

    with st.sidebar:
        mode = st.selectbox("Tema tampilan", opsi, index=idx, key="select_tema_mode")
        st.session_state["tema_mode"] = mode
    return mode


def inject_base_css(mode: str | bool = "Sistem") -> None:
    if mode is True or mode == "Gelap":
        selected_mode = "Gelap"
    elif mode is False or mode == "Terang":
        selected_mode = "Terang"
    else:
        selected_mode = mode

    t_light = _LIGHT
    t_dark = _DARK

    if selected_mode == "Gelap":
        root_css = f"""
            :root {{
                --paper: {t_dark["paper"]};
                --ink: {t_dark["ink"]};
                --ink-soft: {t_dark["ink_soft"]};
                --line: {t_dark["line"]};
                --kartu-bg: {t_dark["kartu_bg"]};
                --urgent: {t_dark["urgent"]};
                --near: {t_dark["near"]};
                --safe: {t_dark["safe"]};
            }}
        """
    elif selected_mode == "Terang":
        root_css = f"""
            :root {{
                --paper: {t_light["paper"]};
                --ink: {t_light["ink"]};
                --ink-soft: {t_light["ink_soft"]};
                --line: {t_light["line"]};
                --kartu-bg: {t_light["kartu_bg"]};
                --urgent: {t_light["urgent"]};
                --near: {t_light["near"]};
                --safe: {t_light["safe"]};
            }}
        """
    else:
        root_css = f"""
            :root {{
                --paper: {t_light["paper"]};
                --ink: {t_light["ink"]};
                --ink-soft: {t_light["ink_soft"]};
                --line: {t_light["line"]};
                --kartu-bg: {t_light["kartu_bg"]};
                --urgent: {t_light["urgent"]};
                --near: {t_light["near"]};
                --safe: {t_light["safe"]};
            }}
            @media (prefers-color-scheme: dark) {{
                :root {{
                    --paper: {t_dark["paper"]};
                    --ink: {t_dark["ink"]};
                    --ink-soft: {t_dark["ink_soft"]};
                    --line: {t_dark["line"]};
                    --kartu-bg: {t_dark["kartu_bg"]};
                    --urgent: {t_dark["urgent"]};
                    --near: {t_dark["near"]};
                    --safe: {t_dark["safe"]};
                }}
            }}
        """

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        {root_css}

        html, body, .stApp {{
            font-family: 'IBM Plex Sans', sans-serif;
            background-color: var(--paper) !important;
            color: var(--ink) !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: 'IBM Plex Serif', serif;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: var(--ink) !important;
        }}

        h1 {{ font-size: 1.9rem; margin-bottom: 0.1rem; }}
        h2 {{ font-size: 1.35rem; }}
        h3 {{ font-size: 1.1rem; }}

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span {{
            color: var(--ink);
        }}

        [data-testid="stCaptionContainer"] {{ color: var(--ink-soft) !important; }}

        hr, [data-testid="stDivider"] {{ border-color: var(--line) !important; }}

        /* DESAIN TOMBOL OUTLINE */
        .stButton button, .stDownloadButton button, .stLinkButton a {{
            background-color: var(--paper) !important;
            border: 1.5px solid var(--ink) !important;
            color: var(--ink) !important;
            border-radius: 4px !important;
            font-weight: 500 !important;
            box-shadow: none !important;
        }}
        .stButton button:hover, .stDownloadButton button:hover, .stLinkButton a:hover {{
            background-color: var(--ink) !important;
            color: var(--paper) !important;
            border-color: var(--ink) !important;
        }}

        .stButton button[kind="primary"] {{
            background-color: var(--paper) !important;
            border: 2px solid var(--ink) !important;
            color: var(--ink) !important;
            font-weight: 600 !important;
        }}
        .stButton button[kind="primary"]:hover {{
            background-color: var(--ink) !important;
            color: var(--paper) !important;
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div {{
            border-radius: 4px !important;
            border: 1px solid var(--line) !important;
            background-color: var(--kartu-bg) !important;
            color: var(--ink) !important;
        }}

        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [data-baseweb="calendar"] {{
            background-color: var(--kartu-bg) !important;
            border: 1px solid var(--line) !important;
            color: var(--ink) !important;
        }}

        [data-baseweb="calendar"] button,
        [data-baseweb="calendar"] div {{
            color: var(--ink) !important;
        }}

        [role="option"] {{
            background-color: var(--kartu-bg) !important;
            color: var(--ink) !important;
        }}
        [role="option"]:hover, [role="option"][aria-selected="true"] {{
            background-color: var(--line) !important;
            color: var(--ink) !important;
        }}

        /* PERBAIKAN STYLING FILE UPLOADER */
        [data-testid="stFileUploader"] {{
            background-color: var(--kartu-bg) !important;
            border: 1.5px dashed var(--line) !important;
            border-radius: 6px !important;
            padding: 0.8rem !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background-color: var(--kartu-bg) !important;
            border: none !important;
        }}
        [data-testid="stFileUploaderDropzone"] * {{
            color: var(--ink) !important;
        }}
        [data-testid="stFileUploaderDropzone"] button {{
            background-color: var(--paper) !important;
            border: 1.5px solid var(--ink) !important;
            color: var(--ink) !important;
        }}

        /* Kartu file yang sudah diunggah */
        [data-testid="stFileUploaderFileData"],
        div[data-testid="stFileUploaderFileData"] {{
            background-color: var(--paper) !important;
            border: 1px solid var(--line) !important;
            border-radius: 4px !important;
        }}
        [data-testid="stFileUploaderFileData"] * {{
            color: var(--ink) !important;
            fill: var(--ink) !important;
        }}
        [data-testid="stFileUploaderDeleteBtn"] button,
        [data-testid="stFileUploaderDeleteBtn"] svg {{
            color: var(--ink) !important;
            fill: var(--ink) !important;
        }}

        [data-testid="stExpander"] {{
            background-color: var(--kartu-bg) !important;
            border: 1px solid var(--line) !important;
            border-radius: 4px !important;
        }}
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span,
        [data-testid="stExpander"] summary svg {{
            color: var(--ink) !important;
            fill: var(--ink) !important;
        }}

        [data-testid="stSidebar"] {{
            background-color: var(--kartu-bg) !important;
            border-right: 1px solid var(--line) !important;
        }}

        .kartu-tugas {{
            border: 1px solid var(--line);
            border-left: 4px solid var(--aksen, var(--ink));
            border-radius: 4px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.6rem;
            background-color: var(--kartu-bg);
            color: var(--ink);
        }}

        .baris-list {{
            border-left: 3px solid var(--aksen, var(--line));
            padding: 0.35rem 0 0.35rem 0.7rem;
            margin-bottom: 0.45rem;
            color: var(--ink);
        }}

        .label-kecil {{
            font-size: 0.78rem;
            color: var(--ink-soft) !important;
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


def calendar_css(mode: str | bool = "Sistem") -> str:
    if mode is True or mode == "Gelap":
        selected_mode = "Gelap"
    elif mode is False or mode == "Terang":
        selected_mode = "Terang"
    else:
        selected_mode = mode

    t_light = _LIGHT
    t_dark = _DARK

    if selected_mode == "Gelap":
        cal_vars = f"""
            :root {{
                --cal-ink: {t_dark["ink"]};
                --cal-paper: {t_dark["paper"]};
                --cal-soft: {t_dark["ink_soft"]};
                --cal-line: {t_dark["line"]};
                --cal-urgent: {t_dark["urgent"]};
            }}
        """
    elif selected_mode == "Terang":
        cal_vars = f"""
            :root {{
                --cal-ink: {t_light["ink"]};
                --cal-paper: {t_light["paper"]};
                --cal-soft: {t_light["ink_soft"]};
                --cal-line: {t_light["line"]};
                --cal-urgent: {t_light["urgent"]};
            }}
        """
    else:
        cal_vars = f"""
            :root {{
                --cal-ink: {t_light["ink"]};
                --cal-paper: {t_light["paper"]};
                --cal-soft: {t_light["ink_soft"]};
                --cal-line: {t_light["line"]};
                --cal-urgent: {t_light["urgent"]};
            }}
            @media (prefers-color-scheme: dark) {{
                :root {{
                    --cal-ink: {t_dark["ink"]};
                    --cal-paper: {t_dark["paper"]};
                    --cal-soft: {t_dark["ink_soft"]};
                    --cal-line: {t_dark["line"]};
                    --cal-urgent: {t_dark["urgent"]};
                }}
            }}
        """

    return f"""
        {cal_vars}
        .fc {{
            font-family: 'IBM Plex Sans', sans-serif;
            color: var(--cal-ink) !important;
            background-color: var(--cal-paper) !important;
            border-radius: 6px;
        }}
        .fc-toolbar-title {{
            font-family: 'IBM Plex Serif', serif;
            font-size: 1.2rem !important;
            font-weight: 600;
            color: var(--cal-ink) !important;
        }}
        .fc-button {{
            background-color: var(--cal-paper) !important;
            border: 1.5px solid var(--cal-ink) !important;
            color: var(--cal-ink) !important;
            box-shadow: none !important;
            border-radius: 4px !important;
            font-weight: 500 !important;
            text-transform: none !important;
        }}
        .fc-button:hover {{
            background-color: var(--cal-ink) !important;
            color: var(--cal-paper) !important;
        }}
        .fc-button-active {{
            background-color: var(--cal-ink) !important;
            color: var(--cal-paper) !important;
        }}
        .fc-daygrid-day-number {{
            color: var(--cal-ink) !important;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .fc-col-header-cell-cushion {{
            color: var(--cal-soft) !important;
            font-weight: 600;
            font-size: 0.82rem;
        }}
        .fc-scrollgrid, .fc-theme-standard td, .fc-theme-standard th {{
            border-color: var(--cal-line) !important;
        }}
        .fc-event {{
            border-radius: 4px !important;
            border: none !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            padding: 4px 6px !important;
            margin: 2px 3px !important;
            cursor: pointer;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        .fc-daygrid-day.fc-day-today {{
            background-color: var(--cal-urgent)1A !important;
        }}
        @media (max-width: 640px) {{
            .fc-toolbar {{
                flex-direction: column;
                gap: 0.4rem;
            }}
            .fc-toolbar-title {{ font-size: 1rem !important; }}
            .fc-event {{ font-size: 0.72rem !important; padding: 3px 4px !important; }}
            .fc-daygrid-day-number {{ font-size: 0.75rem; }}
        }}
    """
