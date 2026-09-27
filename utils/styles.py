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

        .rich-text-content {
            line-height: 1.7;
        }

        .rich-text-content p {
            margin: 0 0 .65rem;
        }

        .rich-text-content h1,
        .rich-text-content h2,
        .rich-text-content h3 {
            margin: 1rem 0 .5rem;
            line-height: 1.3;
        }

        .rich-text-content ul,
        .rich-text-content ol {
            margin: .35rem 0 .75rem 1.5rem;
            padding-left: 1rem;
        }

        .rich-text-content li {
            margin: .2rem 0;
            padding-left: .2rem;
        }

        .rich-text-content blockquote {
            margin: .75rem 0;
            padding: .65rem 1rem;
            border-left: 3px solid var(--primary-color);
            background: rgba(150,150,150,.08);
            border-radius: 0 8px 8px 0;
        }

        .rich-text-content a {
            text-decoration: underline;
        }

        .editor-note {
            margin: .35rem 0 .6rem;
            color: var(--text-color);
            opacity: .62;
            font-size: .82rem;
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
