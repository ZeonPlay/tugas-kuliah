from streamlit_quill import st_quill

EDITOR_TOOLBAR = [
    [{"header": [1, 2, 3, False]}],
    ["bold", "italic", "underline", "strike"],
    [{"list": "ordered"}, {"list": "bullet"}],
    [{"indent": "-1"}, {"indent": "+1"}],
    [{"align": []}],
    ["blockquote", "link"],
    ["clean"],
]

EDITOR_HISTORY = {
    "delay": 1000,
    "maxStack": 500,
    "userOnly": False,
}


def rich_text_editor(*, value="", placeholder="", key=None):
    """Render a consistent HTML rich-text editor for task instructions."""
    return st_quill(
        value=value,
        placeholder=placeholder,
        html=True,
        toolbar=EDITOR_TOOLBAR,
        history=EDITOR_HISTORY,
        preserve_whitespace=True,
        readonly=False,
        key=key,
    )
