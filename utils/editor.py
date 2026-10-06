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

    # Normalize inline bullet/circle groups line-by-line. This preserves
    # nested bullets inside an ordered item, e.g.:
    # 4. Jelaskan perubahan:
    #    - bagian kode
    #    - teknik refactoring
    #
    # while a normal "Ketentuan ● A ● B ● C" becomes a top-level list.
    normalized_lines = []
    for line in text.splitlines():
        bullets = list(re.finditer(r"[•●○]\s*", line))
        if len(bullets) < 2:
            normalized_lines.append(line)
            continue

        first = bullets[0]
        prefix = line[:first.start()].rstrip()
        items = []

        for index, marker in enumerate(bullets):
            item_start = marker.end()
            item_end = bullets[index + 1].start() if index + 1 < len(bullets) else len(line)
            item_text = line[item_start:item_end].strip()
            if item_text:
                items.append(item_text)

        if not items:
            normalized_lines.append(line)
            continue

        is_ordered_item = bool(re.match(r"^\d{1,2}\.\s+", prefix))
        normalized_lines.append(prefix)
        if is_ordered_item:
            normalized_lines.extend(f"   - {item}" for item in items)
        else:
            normalized_lines.append("")
            normalized_lines.extend(f"- {item}" for item in items)

    text = "\n".join(normalized_lines)

    # Keep list markers clean when pasted with spaces before them.
    text = re.sub(
        r"(?m)^[ \t]+(?=(?:\d{1,2}\.\s+|[-*+]\s+))",
        "",
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
