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
            border-radius: var(--morph-radius);
            background: var(--secondary-background-color);
            transition:
                transform var(--mograph-slow) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                border-color var(--mograph-fast) ease;
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

        .krs-course-item,
        .krs-summary-item {
            display: flex;
            align-items: center;
            gap: 10px;
            min-height: 40px;
            padding: 9px 12px;
            margin-bottom: 7px;
            border: 1px solid rgba(150,150,150,.18);
            border-radius: 10px;
            background: var(--secondary-background-color);
            color: var(--text-color);
        }

        .krs-course-item {
            font-weight: 600;
        }

        .krs-summary-item {
            padding-left: 14px;
        }

        .krs-course-item,
        .krs-summary-item {
            transition:
                transform var(--mograph-slow) var(--mograph-ease),
                border-color var(--mograph-fast) ease,
                box-shadow var(--mograph-slow) var(--mograph-ease),
                border-radius var(--mograph-slow) var(--mograph-ease);
        }

        .krs-course-item:hover,
        .krs-summary-item:hover {
            transform: translateX(4px);
            border-radius: 13px;
            border-color: rgba(150,150,150,.32);
            box-shadow: 0 8px 20px rgba(0, 0, 0, .10);
        }

        .krs-check {
            transition: transform var(--mograph-slow) var(--mograph-ease);
        }

        .krs-course-item:hover .krs-check {
            transform: scale(1.08) rotate(-4deg);
        }

        .krs-check {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            flex: 0 0 22px;
            border-radius: 50%;
            background: var(--primary-color);
            color: white;
            font-size: .78rem;
            font-weight: 800;
        }

        /* Fluid motion: spring-like easing + subtle morphing. */
        :root {
            --mograph-ease: cubic-bezier(.18, 1.28, .32, 1);
            --mograph-fast: 170ms;
            --mograph-slow: 360ms;
            --morph-radius: 10px;
            --morph-radius-hover: 14px;
        }

        @keyframes caelestia-enter {
            0% {
                opacity: 0;
                transform: translateY(9px) scale(.965);
                filter: blur(3px);
            }
            62% {
                opacity: 1;
                transform: translateY(-2px) scale(1.008);
                filter: blur(0);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        @keyframes caelestia-pop {
            0% {
                transform: scale(.96);
            }
            55% {
                transform: scale(1.025);
            }
            100% {
                transform: scale(1);
            }
        }

        /* Task cards: subtle lift + corner morph, without affecting layout flow. */
        [class*="st-key-task-card-"] {
            transition:
                transform var(--mograph-slow) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                border-color var(--mograph-fast) ease,
                border-radius var(--mograph-slow) var(--mograph-ease);
            border-radius: var(--morph-radius);
            animation: caelestia-enter 420ms var(--mograph-ease) both;
            will-change: transform;
        }

        [class*="st-key-task-card-"]:hover {
            transform: translateY(-3px) scale(1.006);
            border-radius: var(--morph-radius-hover);
            box-shadow: 0 14px 34px rgba(0, 0, 0, .16);
            border-color: rgba(150, 150, 150, .34);
        }

        /* Main-page navigation links should read clearly as clickable buttons. */
        /* Sidebar navigation: clear slide + highlight on hover. */
        [data-testid="stSidebarNav"] li > a,
        [data-testid="stSidebarNav"] li > button {
            position: relative;
            border-radius: var(--morph-radius) !important;
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                background-color var(--mograph-fast) ease,
                color var(--mograph-fast) ease,
                padding-left var(--mograph-fast) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease);
        }

        [data-testid="stSidebarNav"] li > a::before,
        [data-testid="stSidebarNav"] li > button::before {
            content: "";
            position: absolute;
            left: 0;
            top: 8px;
            bottom: 8px;
            width: 3px;
            border-radius: 999px;
            background: var(--primary-color);
            opacity: 0;
            transform: scaleY(.25);
            transform-origin: center;
            transition:
                opacity var(--mograph-fast) ease,
                transform var(--mograph-slow) var(--mograph-ease);
        }

        [data-testid="stSidebarNav"] li > a:hover,
        [data-testid="stSidebarNav"] li > button:hover {
            transform: translateX(6px);
            padding-left: 5px;
            box-shadow: 0 7px 18px rgba(0, 0, 0, .10);
        }

        [data-testid="stSidebarNav"] li > a:hover::before,
        [data-testid="stSidebarNav"] li > button:hover::before,
        [data-testid="stSidebarNav"] li > a[aria-current="page"]::before,
        [data-testid="stSidebarNav"] li > button[aria-current="page"]::before {
            opacity: .95;
            transform: scaleY(1);
        }

        [data-testid="stSidebarNav"] li > a[aria-current="page"],
        [data-testid="stSidebarNav"] li > button[aria-current="page"] {
            border-radius: var(--morph-radius-hover) !important;
        }

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
            transform: translateY(-3px) scale(1.012);
            border-radius: var(--morph-radius-hover);
            border-color: var(--primary-color);
            box-shadow: 0 12px 26px rgba(0, 0, 0, .14);
        }

        .block-container a[data-testid="stPageLink-NavLink"] svg {
            transition:
                transform var(--mograph-fast) var(--mograph-ease);
        }

        .block-container a[data-testid="stPageLink-NavLink"]:hover svg {
            transform: scale(1.08) rotate(-2deg);
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
            border-radius: var(--morph-radius);
            cursor: pointer;
        }

        .stButton > button:hover,
        .stLinkButton a:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px) scale(1.018);
            border-radius: var(--morph-radius-hover);
            box-shadow: 0 10px 26px rgba(0, 0, 0, .16);
            filter: brightness(1.045);
        }

        .stButton > button:active,
        .stLinkButton a:active,
        .stDownloadButton > button:active,
        [data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(1px) scale(.955);
            border-radius: 9px;
            transition-duration: 80ms;
        }

        .stButton > button:focus-visible,
        .stLinkButton a:focus-visible,
        .stDownloadButton > button:focus-visible,
        [data-testid="stFormSubmitButton"] > button:focus-visible {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }

        [data-baseweb="tab"] {
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                color var(--mograph-fast) ease,
                opacity var(--mograph-fast) ease;
            border-radius: 8px;
        }

        [data-baseweb="tab"]:hover {
            transform: translateY(-2px) scale(1.015);
            background: rgba(127, 127, 127, .08);
        }

        [data-baseweb="tab"][aria-selected="true"] {
            animation: caelestia-pop 260ms var(--mograph-ease) both;
        }

        /* Dropdown/popover: animate when BaseWeb inserts the menu. */
        [data-baseweb="popover"] {
            transform-origin: top center;
            animation: caelestia-popover 240ms var(--mograph-ease) both;
            will-change: transform, opacity;
        }

        [data-baseweb="menu"],
        [role="listbox"] {
            transform-origin: top center;
            animation: caelestia-menu 220ms var(--mograph-ease) both;
            will-change: transform, opacity;
        }

        [role="option"],
        [data-baseweb="menu"] li {
            transition:
                background-color var(--mograph-fast) ease,
                transform var(--mograph-fast) var(--mograph-ease);
        }

        [role="option"]:hover,
        [data-baseweb="menu"] li:hover {
            transform: translateX(3px);
        }

        @keyframes caelestia-popover {
            0% {
                opacity: 0;
                transform: translateY(-6px) scale(.965);
                filter: blur(2px);
            }
            65% {
                opacity: 1;
                transform: translateY(1px) scale(1.006);
                filter: blur(0);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        @keyframes caelestia-menu {
            0% {
                opacity: 0;
                transform: translateY(-5px) scale(.975);
            }
            60% {
                opacity: 1;
                transform: translateY(1px) scale(1.004);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        [data-testid="stExpander"] details > summary {
            transition:
                background-color var(--mograph-fast) ease,
                color var(--mograph-fast) ease,
                padding-left var(--mograph-fast) var(--mograph-ease),
                transform var(--mograph-fast) var(--mograph-ease),
                border-radius var(--mograph-slow) var(--mograph-ease);
        }

        [data-testid="stExpander"] details > summary:hover {
            padding-left: 5px;
            transform: translateX(2px);
        }

        [data-testid="stExpander"] details[open] > div {
            animation: caelestia-expand 300ms var(--mograph-ease) both;
            transform-origin: top center;
        }

        @keyframes caelestia-expand {
            0% {
                opacity: 0;
                transform: translateY(-5px) scaleY(.965);
                clip-path: inset(0 0 10px 0 round 10px);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scaleY(1);
                clip-path: inset(0 0 0 0 round 10px);
            }
        }

        input,
        textarea,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div {
            transition:
                transform var(--mograph-fast) var(--mograph-ease),
                box-shadow var(--mograph-slow) var(--mograph-ease),
                border-color var(--mograph-fast) ease,
                border-radius var(--mograph-slow) var(--mograph-ease);
        }

        input:hover,
        textarea:hover,
        [data-baseweb="select"] > div:hover,
        [data-baseweb="input"] > div:hover {
            transform: translateY(-1px);
            border-radius: 12px;
        }

        input:focus,
        textarea:focus,
        [data-baseweb="select"] > div:focus-within,
        [data-baseweb="input"] > div:focus-within {
            transform: translateY(-1px) scale(1.002);
            border-radius: 13px;
            box-shadow: 0 0 0 1px var(--primary-color), 0 10px 24px rgba(0, 0, 0, .12);
        }

        .course-row:hover {
            transform: translateX(4px);
            box-shadow: 0 10px 24px rgba(0, 0, 0, .14);
            border-color: rgba(150, 150, 150, .35);
            border-radius: 13px;
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
            transform: translateY(-2px) scale(1.025);
            border-radius: 10px !important;
            box-shadow: 0 9px 20px rgba(0, 0, 0, .14);
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
            border-radius: 7px !important;
            filter: brightness(1.08);
        }

        /* Interactive elements animate on interaction; task cards use the
           dedicated enter animation above so periodic Streamlit reruns do not
           make every button flash. */

        @media (hover: none) {
            [data-testid="stSidebarNav"] li > a:hover,
            [data-testid="stSidebarNav"] li > button:hover {
                transform: none !important;
                padding-left: inherit !important;
                box-shadow: none !important;
            }

            [role="option"]:hover,
            [data-baseweb="menu"] li:hover {
                transform: none !important;
            }

            .stButton > button:hover,
            .stLinkButton a:hover,
            .stDownloadButton > button:hover,
            [data-testid="stFormSubmitButton"] > button:hover,
            .block-container a[data-testid="stPageLink-NavLink"]:hover,
            .course-row:hover,
            .krs-course-item:hover,
            .krs-summary-item:hover,
            [data-testid="stSidebarNav"] a:hover {
                transform: none !important;
                box-shadow: none !important;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 1ms !important;
                animation-iteration-count: 1 !important;
                scroll-behavior: auto !important;
                transition-duration: 1ms !important;
                animation: none !important;
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

        .krs-course-item,
        .krs-summary-item {
            min-height: 38px;
            padding: 8px 10px;
            font-size: .88rem;
        }
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

    /* View switcher (Bulan / Daftar): dibuat seperti segmented control
       agar jelas bahwa keduanya adalah tombol yang bisa ditekan. */
    .fc-toolbar-chunk:last-child .fc-button-group {
        display: inline-flex;
        gap: 0 !important;
        padding: 3px;
        border: 1px solid rgba(150, 150, 150, 0.24);
        border-radius: 10px;
        background: var(--secondary-background-color);
    }

    .fc-toolbar-chunk:last-child .fc-button {
        min-width: 82px;
        min-height: 38px;
        padding: 7px 13px !important;
        background: transparent !important;
        border: 0 !important;
        border-radius: 7px !important;
        color: var(--text-color) !important;
        font-weight: 700 !important;
        box-shadow: none !important;
    }

    .fc-toolbar-chunk:last-child .fc-button:hover {
        background: rgba(127, 127, 127, 0.10) !important;
    }

    .fc-toolbar-chunk:last-child .fc-button-active {
        background: var(--primary-color) !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, .14) !important;
    }

    .fc-toolbar-chunk:last-child .fc-button:active {
        transform: translateY(1px) scale(.98);
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

    /* Pisahkan event ringkasan Bulan dari event detail Daftar. */
    .fc-daygrid .fc-event.calendar-task-event,
    .fc-daygrid .calendar-task-event,
    .fc-daygrid .fc-daygrid-dot-event.calendar-task-event {
        display: none !important;
    }

    .fc-list .fc-event.calendar-summary-event,
    .fc-list .calendar-summary-event {
        display: none !important;
    }

    .fc-list {
        background: var(--secondary-background-color) !important;
        border: 1px solid rgba(150, 150, 150, .18) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }

    .fc-list-day-cushion {
        padding: 11px 14px !important;
        background: rgba(127, 127, 127, .08) !important;
        color: var(--text-color) !important;
        font-weight: 750 !important;
        border-bottom: 1px solid rgba(150, 150, 150, .16) !important;
    }

    .fc-list-day-text,
    .fc-list-day-side-text {
        color: var(--text-color) !important;
        font-weight: 750 !important;
        text-decoration: none !important;
    }

    .fc-list-table {
        border: 0 !important;
    }

    .fc-list-table td {
        border-color: rgba(150, 150, 150, .13) !important;
    }

    .fc-list-event:hover td {
        background: rgba(127, 127, 127, .07) !important;
    }

    .fc-list-event-dot {
        border-width: 6px !important;
        margin: 0 10px !important;
    }

    .fc-list-event-time {
        width: 92px;
        color: var(--text-color) !important;
        opacity: .72;
        font-weight: 650 !important;
        white-space: nowrap;
        vertical-align: middle !important;
    }

    .fc-list-event-title {
        padding: 11px 14px 11px 4px !important;
        color: var(--text-color) !important;
        font-weight: 650 !important;
        line-height: 1.35;
        vertical-align: middle !important;
    }

    .fc-list-event-title a {
        color: var(--text-color) !important;
        text-decoration: none !important;
    }

    .fc-list-empty {
        background: transparent !important;
        border: 0 !important;
    }

    .fc-list-empty-cushion {
        color: var(--text-color) !important;
        opacity: .7;
        font-weight: 600;
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

        .fc-toolbar-chunk:last-child .fc-button-group {
            width: 100%;
        }

        .fc-toolbar-chunk:last-child .fc-button {
            min-width: 0;
            min-height: 40px;
            flex: 1 1 0;
            padding: 8px 12px !important;
            font-size: .82rem !important;
        }

        .fc-daygrid-day-number { font-size: .8rem; }

        .fc-list-event-time {
            width: 72px;
            font-size: .78rem !important;
        }

        .fc-list-event-title {
            padding: 10px 10px 10px 2px !important;
            font-size: .82rem !important;
        }

        .fc-list-day-cushion {
            padding: 10px 12px !important;
        }
    }
    """
