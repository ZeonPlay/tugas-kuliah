import streamlit as st


def get_tokens(mode="Sistem") -> dict:
    return {
        "urgent": "#ef4444",
        "near": "#f59e0b",
        "safe": "#10b981",
        "ink": "#ffffff",
        "ink_soft": "#94a3b8",
        "course": ["#3b82f6", "#10b981", "#8b5cf6", "#f43f5e", "#d946ef", "#06b6d4", "#f97316", "#84cc16", "#6366f1"],
    }


def render_theme_toggle() -> str:
    return "Sistem"


def inject_base_css(mode="Sistem") -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px;
        }

        .course-row {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            margin-bottom: 7px;
            border: 1px solid rgba(150,150,150,.18);
            border-radius: 10px;
            background: var(--secondary-background-color);
        }

        .course-row span:nth-child(2) {
            flex: 1;
            line-height: 1.25;
        }

        .course-dot {
            width: 10px;
            height: 10px;
            min-width: 10px;
            border-radius: 50%;
        }

        /* Mograph test: subtle spring-like motion for interactive UI. */
        :root {
            --mograph-ease: cubic-bezier(.22, 1, .36, 1);
            --mograph-fast: 160ms;
            --mograph-slow: 320ms;
        }

        @keyframes mograph-enter {
            from {
                opacity: 0;
                transform: translateY(8px) scale(.985);
                filter: blur(2px);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
                filter: blur(0);
            }
        }

        /* Main-page navigation links should read clearly as clickable buttons. */
        .block-container .stPageLink {
            margin-bottom: 0 !important;
        }

        .block-container a[data-testid="stPageLink-NavLink"] {
            box-sizing: border-box;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            display: flex !important;
            min-height: 44px;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 14px !important;
            border: 1px solid rgba(150, 150, 150, .24);
            border-radius: 10px;
            background: var(--secondary-background-color);
            color: var(--text-color) !important;
            text-decoration: none !important;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 1px 2px rgba(0, 0, 0, .06);
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                border-color var(--mograph-fast) ease,
                background-color var(--mograph-fast) ease;
        }

        .block-container a[data-testid="stPageLink-NavLink"]:hover {
            transform: translateY(-2px);
            border-color: var(--primary-color);
            box-shadow: 0 8px 20px rgba(0, 0, 0, .12);
        }

        .block-container a[data-testid="stPageLink-NavLink"]:active {
            transform: translateY(1px) scale(.98);
        }

        .block-container a[data-testid="stPageLink-NavLink"] span {
            color: var(--text-color) !important;
        }

        .stButton > button,
        .stLinkButton a,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                filter var(--mograph-fast) var(--mograph-ease);
            transform-origin: center;
            will-change: transform;
        }

        .stButton > button:hover,
        .stLinkButton a:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px) scale(1.015);
            box-shadow: 0 8px 24px rgba(0, 0, 0, .18);
            filter: brightness(1.04);
        }

        .stButton > button:active,
        .stLinkButton a:active,
        .stDownloadButton > button:active,
        [data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(1px) scale(.975);
            transition-duration: 70ms;
        }

        [data-baseweb="tab"] {
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                color var(--mograph-fast) ease,
                opacity var(--mograph-fast) ease;
        }

        [data-baseweb="tab"]:hover {
            transform: translateY(-1px);
        }

        [data-testid="stExpander"] details > summary {
            transition:
                background-color var(--mograph-fast) ease,
                color var(--mograph-fast) ease,
                padding-left var(--mograph-fast) var(--mograph-ease),
                transform var(--mograph-fast) var(--mograph-ease);
        }

        [data-testid="stExpander"] details > summary:hover {
            padding-left: 4px;
        }

        input,
        textarea,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div {
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                border-color var(--mograph-fast) ease;
        }

        input:hover,
        textarea:hover,
        [data-baseweb="select"] > div:hover,
        [data-baseweb="input"] > div:hover {
            transform: translateY(-1px);
        }

        input:focus,
        textarea:focus,
        [data-baseweb="select"] > div:focus-within,
        [data-baseweb="input"] > div:focus-within {
            transform: translateY(-1px);
            box-shadow: 0 0 0 1px var(--primary-color), 0 8px 20px rgba(0, 0, 0, .10);
        }

        .course-row {
            transition:
                transform var(--mograph-slow) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                border-color var(--mograph-fast) ease;
        }

        .course-row:hover {
            transform: translateX(4px);
            box-shadow: 0 10px 24px rgba(0, 0, 0, .14);
            border-color: rgba(150, 150, 150, .35);
        }

        .course-dot {
            transition: transform var(--mograph-slow) var(--mograph-ease);
        }

        .course-row:hover .course-dot {
            transform: scale(1.35);
        }

        .fc-button {
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                background-color var(--mograph-fast) ease !important;
        }

        .fc-button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 7px 18px rgba(0, 0, 0, .14);
        }

        .fc-button:active {
            transform: translateY(1px) scale(.97);
        }

        .fc-event {
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                filter var(--mograph-fast) ease;
        }

        .fc-event:hover {
            transform: translateY(-2px) scale(1.025);
            filter: brightness(1.08);
        }

        .stButton > button,
        .stLinkButton a,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button,
        [data-baseweb="tab"],
        [data-testid="stExpander"] details > summary,
        .course-row,
        .fc-button,
        .fc-event {
            animation: mograph-enter 420ms var(--mograph-ease) both;
        }

        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 1ms !important;
                animation-iteration-count: 1 !important;
                scroll-behavior: auto !important;
                transition-duration: 1ms !important;
            }
        }

        @media (max-width: 640px) {
            .block-container {
                padding: .75rem .75rem 1.5rem !important;
            }
            h1 { font-size: 1.65rem !important; }
            h2 { font-size: 1.25rem !important; }
            h3 { font-size: 1.05rem !important; }
            [data-testid="stMetricValue"] { font-size: 1.35rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def calendar_css(mode="Sistem") -> str:
    return """
    .fc {
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        padding: 8px;
        border: 1px solid rgba(150, 150, 150, 0.18);
    }

    .fc-toolbar {
        flex-wrap: wrap;
        gap: 6px;
    }

    .fc-toolbar-title {
        font-size: 1.15rem !important;
        font-weight: 700;
        color: var(--text-color) !important;
    }

    .fc-button {
        background-color: var(--background-color) !important;
        border: 1px solid rgba(150, 150, 150, 0.2) !important;
        color: var(--text-color) !important;
        border-radius: 7px !important;
    }

    .fc-button:hover,
    .fc-button-active {
        background-color: var(--primary-color) !important;
        color: white !important;
    }

    .fc-daygrid-day-number {
        color: var(--text-color) !important;
        font-weight: 600;
    }

    .fc-col-header-cell-cushion {
        color: var(--text-color) !important;
        opacity: .72;
        font-weight: 600;
        padding: 7px 0 !important;
    }

    .fc-scrollgrid,
    .fc-theme-standard td,
    .fc-theme-standard th {
        border-color: rgba(150, 150, 150, 0.18) !important;
    }

    .fc-event {
        border-radius: 5px !important;
        border: none !important;
        font-size: .72rem !important;
        font-weight: 700 !important;
        padding: 3px !important;
        margin: 2px !important;
        cursor: pointer;
    }

    @media (max-width: 640px) {
        .fc-toolbar-title { font-size: 1rem !important; }
        .fc-button { padding: 4px 7px !important; font-size: .78rem !important; }
        .fc-daygrid-day-number { font-size: .8rem; }
    }
    """
