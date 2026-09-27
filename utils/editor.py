import re

import streamlit as st
from markdownify import markdownify
from st_tui_editor import st_tui_editor


# Keep the toolbar compact enough for narrow screens.
# Toast UI can add its own overflow/"More" control when the toolbar
# cannot fit; using only the controls needed for task instructions avoids
# that overflow path on phones.
EDITOR_TOOLBAR = [
    ["bold", "italic"],
    ["ul", "ol"],
    ["link"],
]


def rich_text_to_markdown(value: str | None) -> str:
    """Convert legacy Quill HTML to Markdown while keeping Markdown unchanged."""
    text = (value or "").strip()
    if not text:
        return ""

    looks_like_html = re.search(
        r"<(?:p|div|ol|ul|li|h[1-6]|strong|em|u|s|blockquote|a|br)(?:\s|>)",
        text,
        flags=re.IGNORECASE,
    )
    if not looks_like_html:
        return text

    return markdownify(
        text,
        heading_style="ATX",
        bullets="-",
    ).strip()


def rich_text_editor(*, value: str = "", placeholder: str = "", key: str) -> str:
    """Render a WYSIWYG Toast UI editor and return Markdown."""
    theme = "dark" if st.context.theme.type == "dark" else "light"

    result = st_tui_editor(
        initial_value=value,
        height="320px",
        min_height="260px",
        initial_edit_type="wysiwyg",
        hide_mode_switch=True,
        placeholder=placeholder or "Tulis ketentuan tugas di sini...",
        usage_statistics=False,
        theme=theme,
        toolbar_items=EDITOR_TOOLBAR,
        key=key,
    )

    if not result:
        return value or ""

    content = result.get("content", {}) if isinstance(result, dict) else {}
    return (content.get("markdown") or value or "").strip()


def reset_rich_text_editor(key: str) -> None:
    """Clear Streamlit state associated with an editor key."""
    st.session_state.pop(key, None)
