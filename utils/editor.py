import re

import streamlit as st
from markdownify import markdownify
from st_tui_editor import st_tui_editor


# Keep the toolbar compact enough for narrow screens.
# Toast UI can add its own overflow/"More" control when the toolbar
# cannot fit; using only the controls needed for task instructions avoids
# that overflow path on phones.
EDITOR_TOOLBAR = [
    ["heading", "bold", "italic", "ul", "ol", "task", "link"],
]


def normalize_instruction_markdown(value: str | None) -> str:
    """Normalize common pasted inline numbering/bullets into real Markdown lists."""
    text = (value or "").strip()
    if not text:
        return ""

    # A common paste pattern is:
    # "1. First 2. Second 3. Third"
    # Markdown sees that as one paragraph, so split only when another
    # numbered item follows on the same line.
    text = re.sub(
        r"\s+(?=\d{1,2}\.\s+)",
        "\n",
        text,
    )

    # Convert inline bullet separators such as:
    # "Ketentuan • A • B • C"
    # into a proper Markdown bullet list.
    text = re.sub(
        r"\s+[•●]\s+",
        "\n- ",
        text,
    )

    # Keep list markers clean when pasted with spaces before them.
    text = re.sub(r"(?m)^[ \t]+(?=(?:\d{1,2}\.\s+|[-*+]\s+))", "", text)

    return text.strip()


def rich_text_to_markdown(value: str | None) -> str:
    """Convert legacy editor HTML to Markdown and normalize pasted lists."""
    text = (value or "").strip()
    if not text:
        return ""

    looks_like_html = re.search(
        r"<(?:p|div|ol|ul|li|h[1-6]|strong|em|u|s|blockquote|a|br)(?:\s|>)",
        text,
        flags=re.IGNORECASE,
    )
    if looks_like_html:
        text = markdownify(
            text,
            heading_style="ATX",
            bullets="-",
        ).strip()

    return normalize_instruction_markdown(text)


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
    return normalize_instruction_markdown(content.get("markdown") or value or "")


def reset_rich_text_editor(key: str) -> None:
    """Clear Streamlit state associated with an editor key."""
    st.session_state.pop(key, None)
