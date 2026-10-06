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

    # Some older editor output contains literal escape characters before
    # ordinary punctuation (for example: "1\\. Item"). They are not needed
    # in task descriptions and prevent Markdown list detection.
    text = re.sub(r"\\+(?=[.,:;!?()\]])", "", text)

    # Detect an inline numbered sequence such as:
    # "Tugas Anda: 1. A 2. B 3. C"
    # and turn it into a real Markdown ordered list.
    numbered = list(re.finditer(r"(?<!\w)\d{1,2}\.\s+", text))
    if len(numbered) >= 2:
        first = numbered[0]
        prefix = text[:first.start()].rstrip()
        items = []

        for index, marker in enumerate(numbered):
            item_start = marker.end()
            item_end = numbered[index + 1].start() if index + 1 < len(numbered) else len(text)
            item_text = text[item_start:item_end].strip()
            if item_text:
                items.append(f"{index + 1}. {item_text}")

        if items:
            text = f"{prefix}\n\n" + "\n".join(items)

    # Normalize standalone bullet/circle markers, including older data where
    # every bullet is already on its own line.
    lines = text.splitlines()
    normalized_lines = []
    ordered_list_active = False
    nested_bullets = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            normalized_lines.append("")
            ordered_list_active = False
            nested_bullets = False
            continue

        ordered_match = re.match(r"^(\d{1,2})\.\s+(.+)$", stripped)
        if ordered_match:
            ordered_list_active = True
            nested_bullets = False
            normalized_lines.append(f"{ordered_match.group(1)}. {ordered_match.group(2)}")
            continue

        bullet_match = re.match(r"^[•●○]\s*(.+)$", stripped)
        if bullet_match:
            item = bullet_match.group(1).strip()

            # Bullets directly following an ordered item belong to that item.
            if ordered_list_active:
                normalized_lines.append(f"    - {item}")
                nested_bullets = True
            else:
                normalized_lines.append(f"- {item}")
            continue

        # A normal heading/paragraph ends any ordered-list nesting context.
        if nested_bullets:
            nested_bullets = False
        normalized_lines.append(stripped)

    text = "\n".join(normalized_lines)

    # Finally handle multiple inline bullets on one line.
    text = re.sub(
        r"\s*[•●○]\s*",
        lambda match: "\n- ",
        text,
    )

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
