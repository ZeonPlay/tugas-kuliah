import re

import streamlit as st
from markdownify import markdownify


EDITOR_TOOLBAR_ITEMS = [
    ["heading", "bold", "italic", "ul", "ol", "task", "link"],
]

ALPHA_EDITOR_CSS = r"""
@import url("https://uicdn.toast.com/editor/3.2.2/toastui-editor.min.css");
@import url("https://uicdn.toast.com/editor/3.2.2/theme/toastui-editor-dark.css");

.toastui-editor-ww-container .toastui-editor-contents ol[type="a"] {
    list-style: none !important;
    counter-reset: alpha-list;
    padding-left: 24px;
}

.toastui-editor-ww-container .toastui-editor-contents ol[type="a"] > li {
    counter-increment: alpha-list;
    position: relative;
}

.toastui-editor-ww-container .toastui-editor-contents ol[type="a"] > li::before {
    content: counter(alpha-list, lower-alpha) ".";
    position: absolute;
    left: -28px;
    width: 24px;
    text-align: right;
    color: currentColor;
}

.toastui-editor-defaultUI {
    width: 100%;
    max-width: 100%;
    overflow: hidden;
}

.toastui-editor-toolbar {
    max-width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
}

.toastui-editor-toolbar::-webkit-scrollbar {
    display: none;
}

.toastui-editor-toolbar-group {
    flex-shrink: 0;
}
"""

ALPHA_EDITOR_JS = r'''
const SCRIPT_ID = "tugas-kuliah-toast-ui-script";
const SCRIPT_SRC = "https://uicdn.toast.com/editor/3.2.2/toastui-editor-all.min.js";

function loadScript() {
    if (window.toastui?.Editor) return Promise.resolve();

    const existing = document.getElementById(SCRIPT_ID);
    if (existing) {
        return new Promise((resolve, reject) => {
            existing.addEventListener("load", resolve, { once: true });
            existing.addEventListener("error", reject, { once: true });
        });
    }

    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.id = SCRIPT_ID;
        script.src = SCRIPT_SRC;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

function alphaListPlugin() {
    return function(context) {
        function findOrderedList(state) {
            let found = null;

            state.doc.nodesBetween(
                state.selection.from,
                state.selection.to,
                (node, pos) => {
                    if (node.type.name === "orderedList" && !found) {
                        found = { node, pos };
                        return false;
                    }
                    return true;
                },
            );

            return found;
        }

        function alphaList(_payload, state, dispatch) {
            const existing = findOrderedList(state);

            if (existing) {
                const currentRaw = existing.node.attrs.rawHTML || "";
                const isAlpha = /type=["']a["']/i.test(currentRaw);

                const attrs = {
                    ...existing.node.attrs,
                    rawHTML: isAlpha ? null : 'ol type="a"',
                };

                if (dispatch) {
                    dispatch(
                        state.tr.setNodeMarkup(
                            existing.pos,
                            existing.node.type,
                            attrs,
                        ),
                    );
                }
                return true;
            }

            const range = state.selection.$from.blockRange(state.selection.$to);
            if (!range) return false;

            const listItemType = state.schema.nodes.listItem;
            const orderedListType = state.schema.nodes.orderedList;

            if (!listItemType || !orderedListType) return false;

            const items = [];
            for (
                let index = range.startIndex;
                index < range.endIndex;
                index += 1
            ) {
                const block = range.parent.child(index);

                if (!block.isBlock) return false;
                items.push(listItemType.create(null, block));
            }

            if (!items.length) return false;

            const list = orderedListType.create(
                { order: 1, rawHTML: 'ol type="a"' },
                items,
            );

            if (dispatch) {
                dispatch(
                    state.tr.replaceRangeWith(range.start, range.end, list),
                );
            }

            return true;
        }

        return {
            wysiwygCommands: {
                alphaList,
            },
            markdownCommands: {
                alphaList,
            },
            toolbarItems: [
                {
                    groupIndex: 0,
                    itemIndex: 5,
                    item: {
                        name: "alphaList",
                        tooltip: "Alphabetical list",
                        command: "alphaList",
                        text: "A.",
                        className: "toastui-editor-toolbar-icons",
                        style: {
                            backgroundImage: "none",
                            fontSize: "13px",
                            fontWeight: "700",
                            fontFamily: "sans-serif",
                        },
                    },
                },
            ],
        };
    };
}

export default async function(component) {
    const { parentElement, data, setStateValue } = component;
    const root = parentElement.querySelector(".tugas-kuliah-editor");
    if (!root) return;

    await loadScript();

    const editor = new window.toastui.Editor({
        el: root,
        initialValue: data.value || "",
        height: data.height || "320px",
        minHeight: data.minHeight || "260px",
        initialEditType: "wysiwyg",
        previewStyle: "tab",
        hideModeSwitch: true,
        usageStatistics: false,
        placeholder: data.placeholder || "Tulis ketentuan tugas di sini...",
        autofocus: false,
        toolbarItems: data.toolbarItems || [
            ["heading", "bold", "italic", "ul", "ol", "task", "link"],
        ],
        theme: data.theme === "dark" ? "dark" : "light",
        plugins: [alphaListPlugin()],
    });

    const emit = () => {
        setStateValue("content", {
            markdown: editor.getMarkdown(),
        });
    };

    editor.on("change", emit);
    emit();

    return () => editor.destroy();
};
'''

rich_text_editor_component = st.components.v2.component(
    name="tugas_kuliah_rich_text_editor",
    html='<div class="tugas-kuliah-editor"></div>',
    css=ALPHA_EDITOR_CSS,
    js=ALPHA_EDITOR_JS,
    isolate_styles=False,
)


def _has_html(value: str) -> bool:
    return bool(
        re.search(
            r"<(?:p|div|ol|ul|li|h[1-6]|strong|em|u|s|blockquote|a|br)(?:\s|>)",
            value,
            flags=re.IGNORECASE,
        )
    )


def editor_initial_value(value: str | None) -> str:
    """Keep alpha-list HTML intact; convert legacy Quill HTML otherwise."""
    text = (value or "").strip()
    if not text:
        return ""

    if re.search(r'<ol\b[^>]*type=["\']a["\'][^>]*>', text, flags=re.IGNORECASE):
        return text

    if _has_html(text):
        return markdownify(text, heading_style="ATX", bullets="-").strip()

    return text


def rich_text_to_markdown(value: str | None) -> str:
    """Convert legacy Quill HTML for the editor."""
    return editor_initial_value(value)


def _alpha_html_to_markdown(text: str) -> str:
    pattern = re.compile(
        r'<ol\b[^>]*type=["\']a["\'][^>]*>(.*?)</ol>',
        flags=re.IGNORECASE | re.DOTALL,
    )

    def replace(match: re.Match) -> str:
        body = match.group(1)
        items = re.findall(
            r"<li\b[^>]*>(.*?)</li>",
            body,
            flags=re.IGNORECASE | re.DOTALL,
        )
        lines = []
        for index, item in enumerate(items):
            item_md = markdownify(item, heading_style="ATX", bullets="-").strip()
            marker = chr(ord("a") + index) if index < 26 else f"({index + 1})"
            lines.append(f"{marker}. {item_md}")
        return "\n".join(lines)

    return pattern.sub(replace, text)


def display_rich_text(value: str | None) -> str:
    """Render stored rich text as Markdown-friendly text."""
    text = (value or "").strip()
    if not text:
        return ""

    if re.search(r'<ol\b[^>]*type=["\']a["\'][^>]*>', text, flags=re.IGNORECASE):
        text = _alpha_html_to_markdown(text)
        return markdownify(text, heading_style="ATX", bullets="-").strip()

    return editor_initial_value(text)


def reset_rich_text_editor(key: str) -> None:
    st.session_state.pop(key, None)


def render_rich_text_editor(*, value: str = "", placeholder: str = "", key: str) -> str:
    theme = getattr(getattr(st.context, "theme", None), "type", None) or "light"

    result = rich_text_editor_component(
        key=key,
        data={
            "value": value,
            "height": "320px",
            "minHeight": "260px",
            "placeholder": placeholder,
            "theme": theme,
            "toolbarItems": EDITOR_TOOLBAR_ITEMS,
        },
        default={"content": {"markdown": value}},
        on_content_change=lambda: None,
    )

    if not result:
        return value or ""

    content = result.get("content", {}) if isinstance(result, dict) else {}
    return (content.get("markdown") or value or "").strip()


# Backwards-compatible name used by the admin page.
rich_text_editor = render_rich_text_editor
