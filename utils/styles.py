import streamlit as st


def get_tokens(mode="Sistem") -> dict:
    # Palet warna netral (dibutuhkan oleh helpers.py agar tidak error)
    return {
        "urgent": "#ef4444",
        "near": "#f59e0b",
        "safe": "#10b981",
        "ink": "#ffffff",
        "ink_soft": "#94a3b8",
        "course": ["#3b82f6", "#10b981", "#8b5cf6", "#f43f5e", "#d946ef", "#06b6d4", "#f97316", "#84cc16", "#6366f1"],
    }


def render_theme_toggle() -> str:
    # Kita matikan toggle custom agar tidak merusak tema bawaan Streamlit
    return "Sistem"


def inject_base_css(mode="Sistem") -> None:
    # Hanya reset margin, tidak ada tag HTML (p, span, div) yang di-override
    st.markdown(
        """
    <style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def calendar_css(mode="Sistem") -> str:
    # CSS Kalender menggunakan variabel warna Streamlit bawaan
    return """
    .fc { background-color: var(--secondary-background-color); border-radius: 8px; padding: 10px; border: 1px solid rgba(150, 150, 150, 0.2); }
    .fc-toolbar-title { font-size: 1.25rem !important; font-weight: bold; color: var(--text-color) !important;}
    .fc-button { background-color: var(--background-color) !important; border: 1px solid rgba(150, 150, 150, 0.2) !important; color: var(--text-color) !important; border-radius: 6px !important; }
    .fc-button:hover, .fc-button-active { background-color: var(--primary-color) !important; color: white !important; }
    .fc-daygrid-day-number { color: var(--text-color) !important; font-weight: 500; }
    .fc-col-header-cell-cushion { color: var(--text-color) !important; opacity: 0.7; font-weight: 600; padding: 8px 0 !important; }
    .fc-scrollgrid, .fc-theme-standard td, .fc-theme-standard th { border-color: rgba(150, 150, 150, 0.2) !important; }
    .fc-event { border-radius: 4px !important; border: none !important; font-size: 0.75rem !important; font-weight: 600 !important; padding: 4px !important; margin: 2px !important; cursor: pointer; }
    """
