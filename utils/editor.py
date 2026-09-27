import re

import streamlit as st
from markdownify import markdownify
from streamlit_lexical_extended import streamlit_lexical_extended


EDITOR_TOOLBAR = [
    "undo",
    "redo",
    "block_type",
    "bold",
    "italic",
    "strikethrough",
    "quote",
    "bullet_list",
    "numbered_list",
    "table",
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

    converted = markdownify(
        text,
        heading_style="ATX",
        bullets="-",
    )
    return converted.strip()


def _editor_init_key(key: str) -> str:
    return f"_rich_text_initialized_{key}"


def rich_text_editor(*, value: str = "", placeholder: str = "", key: str) -> str:
    """Render the shared Lexical Markdown editor without resetting on reruns."""
    init_key = _editor_init_key(key)
    initial_value = value if not st.session_state.get(init_key) else None

    result = streamlit_lexical_extended(
        value=initial_value,
        placeholder=placeholder or "Tulis ketentuan tugas di sini...",
        min_height=220,
        debounce=250,
        key=key,
        toolbar=EDITOR_TOOLBAR,
    )

    st.session_state[init_key] = True

    if hasattr(result, "value"):
        return result.value or ""
    return result or ""


def reset_rich_text_editor(key: str) -> None:
    """Clear editor state so the next render uses its initial value again."""
    st.session_state.pop(key, None)
    st.session_state.pop(_editor_init_key(key), None)
