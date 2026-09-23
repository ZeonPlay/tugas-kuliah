import colorsys

import streamlit as st

_LIGHT = {
    "paper": "#F8FAFC",
    "ink": "#0F172A",
    "ink_soft": "#64748B",
    "line": "#E2E8F0",
    "kartu_bg": "#FFFFFF",
    "urgent": "#EF4444",
    "near": "#F59E0B",
    "safe": "#10B981",
    "course": ["#3B82F6", "#14B8A6", "#8B5CF6", "#F43F5E", "#D946EF", "#06B6D4", "#F97316", "#84CC16", "#6366F1"],
}

_DARK = {
    "paper": "#0B0F19",
    "ink": "#F8FAFC",
    "ink_soft": "#94A3B8",
    "line": "#1E293B",
    "kartu_bg": "#171E2E",
    "urgent": "#F87171",
    "near": "#FBBF24",
    "safe": "#34D399",
}


def _terangkan(hex_warna: str, tambahan_lightness: float) -> str:
    hex_warna = hex_warna.lstrip("#")
    r, g, b = (int(hex_warna[i : i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(0.82, l + tambahan_lightness)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


_DARK["course"] = [_terangkan(c, 0.15) for c in _LIGHT["course"]]


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
        mode = st.selectbox("Tema Tampilan", opsi, index=idx, key="select_tema_mode")
        st.session_state["tema_mode"] = mode
    return mode


def inject_base_css(mode: str | bool = "Sistem") -> None:
    selected_mode = mode
    if mode is True or mode == "Gelap":
        selected_mode = "Gelap"
    elif mode is False or mode == "Terang":
        selected_mode = "Terang"

    t_light, t_dark = _LIGHT, _DARK

    def build_vars(t):
        return f"""
            --paper: {t["paper"]}; --ink: {t["ink"]}; --ink-soft: {t["ink_soft"]};
            --line: {t["line"]}; --kartu-bg: {t["kartu_bg"]}; --urgent: {t["urgent"]};
            --near: {t["near"]}; --safe: {t["safe"]};
        """

    if selected_mode == "Gelap":
        root_css = f":root {{ {build_vars(t_dark)} }}"
    elif selected_mode == "Terang":
        root_css = f":root {{ {build_vars(t_light)} }}"
    else:
        root_css = f"""
            :root {{ {build_vars(t_light)} }}
            @media (prefers-color-scheme: dark) {{ :root {{ {build_vars(t_dark)} }} }}
        """

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        {root_css}
        
        /* Hanya target container utama, hindari override class bawaan Streamlit agar icon tidak rusak */
        .stApp {{
            font-family: 'Inter', sans-serif !important;
            background-color: var(--paper) !important;
        }}
        
        /* Perbaikan warna teks yang aman */
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, .stMarkdown li, .stMarkdown span {{ 
            color: var(--ink) !important; 
        }}
        [data-testid="stCaptionContainer"] p {{ 
            color: var(--ink-soft) !important; 
            font-size: 0.85rem !important; 
        }}
        hr, [data-testid="stDivider"] {{ border-color: var(--line) !important; }}
        
        .metric-card {{
            background-color: var(--kartu-bg);
            padding: 1.25rem;
            border-radius: 12px;
            border: 1px solid var(--line);
            border-left: 5px solid var(--aksen);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
            margin-bottom: 1rem;
        }}
        .metric-title {{ color: var(--ink-soft); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
        .metric-value {{ color: var(--ink); font-size: 2rem; font-weight: 700; margin-top: 0.5rem; }}

        .kartu-tugas {{
            background-color: var(--kartu-bg);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .kartu-tugas:hover {{ transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.06); }}
        
        /* Perbaikan Button (Text Color Inheritance) */
        .stButton button, .stDownloadButton button, .stLinkButton a {{
            background-color: var(--kartu-bg) !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            transition: all 0.2s;
        }}
        .stButton button p, .stDownloadButton button p, .stLinkButton a p {{
            color: var(--ink) !important;
            font-weight: 600 !important;
        }}
        .stButton button:hover, .stLinkButton a:hover {{
            border-color: var(--ink) !important;
            background-color: var(--paper) !important;
        }}
        
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, 
        [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input, 
        [data-baseweb="select"] > div {{
            border-radius: 8px !important;
            border: 1px solid var(--line) !important;
            background-color: var(--kartu-bg) !important;
            color: var(--ink) !important;
        }}
        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{
            background-color: var(--kartu-bg) !important;
            border: 1px solid var(--line) !important;
        }}
        [role="option"] {{ color: var(--ink) !important; background-color: transparent !important; }}
        [role="option"]:hover, [role="option"][aria-selected="true"] {{ background-color: var(--paper) !important; }}
        
        [data-testid="stExpander"] {{ background-color: var(--kartu-bg) !important; border: 1px solid var(--line) !important; border-radius: 8px !important; }}
        [data-testid="stFileUploader"] {{ background-color: var(--kartu-bg) !important; border: 1.5px dashed var(--ink-soft) !important; border-radius: 8px !important; }}
        
        .badge-lewat {{
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--urgent) !important;
            padding: 0.2rem 0.6rem;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-aman {{
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--safe) !important;
            padding: 0.2rem 0.6rem;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def calendar_css(mode: str | bool = "Sistem") -> str:
    return """
        .fc { font-family: 'Inter', sans-serif; background-color: var(--kartu-bg) !important; border-radius: 12px; padding: 10px; border: 1px solid var(--line); }
        .fc-toolbar-title { font-size: 1.25rem !important; font-weight: 700; color: var(--ink) !important; }
        .fc-button { background-color: var(--paper) !important; border: 1px solid var(--line) !important; color: var(--ink) !important; border-radius: 6px !important; font-weight: 600 !important; text-transform: capitalize !important; }
        .fc-button:hover, .fc-button-active { background-color: var(--ink) !important; color: var(--paper) !important; }
        .fc-daygrid-day-number { color: var(--ink) !important; font-weight: 500; }
        .fc-col-header-cell-cushion { color: var(--ink-soft) !important; font-weight: 600; font-size: 0.85rem; padding: 8px 0 !important; }
        .fc-scrollgrid, .fc-theme-standard td, .fc-theme-standard th { border-color: var(--line) !important; }
        .fc-event { border-radius: 4px !important; border: none !important; font-size: 0.75rem !important; font-weight: 600 !important; padding: 4px !important; margin: 2px !important; cursor: pointer; }
    """
