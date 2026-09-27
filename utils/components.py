import html
import streamlit as st

from utils.helpers import format_deadline, punya_link, sisa_waktu, warna_matkul


def _safe(value) -> str:
    return html.escape(str(value or ""))


def render_task_card(task: dict, tokens: dict, *, detail_label: str = "Detail & Instruksi") -> None:
    """Render one task consistently across the dashboard and calendar."""
    accent = warna_matkul(tokens, task.get("mata_kuliah"))
    remaining, level = sisa_waktu(task["deadline"])

    if level == "lewat":
        badge_bg, badge_color = "rgba(239,68,68,.14)", tokens["urgent"]
    elif level == "mendesak":
        badge_bg, badge_color = "rgba(245,158,11,.16)", tokens["near"]
    else:
        badge_bg, badge_color = "rgba(16,185,129,.14)", tokens["safe"]

    with st.container(border=True):
        left, right = st.columns([3, 1])

        with left:
            st.markdown(
                f"<span style='color:{accent};font-weight:700;font-size:.82rem'>"
                f"{_safe(task.get('mata_kuliah'))} · {_safe(task.get('jenis', '-'))}</span>",
                unsafe_allow_html=True,
            )

        with right:
            st.markdown(
                f"<div style='background:{badge_bg};color:{badge_color};padding:4px 8px;"
                f"border-radius:999px;text-align:center;font-weight:700;font-size:.78rem'>"
                f"{_safe(remaining)}</div>",
                unsafe_allow_html=True,
            )

        st.markdown(f"### {_safe(task.get('judul'))}")
        st.caption(f"Deadline · {format_deadline(task['deadline'])}")

        details = (task.get("ketentuan") or "").strip()
        if details:
            with st.expander(detail_label):
                st.markdown(
                    f'<div class="rich-text-content">{details}</div>',
                    unsafe_allow_html=True,
                )

        actions = []
        if punya_link(task):
            actions.append(("VClass", task["link_vclass"]))
        if task.get("file_soal"):
            actions.append(("File soal", task["file_soal"]))

        if actions:
            columns = st.columns(len(actions))
            for column, (label, url) in zip(columns, actions):
                column.link_button(label, url, use_container_width=True)
