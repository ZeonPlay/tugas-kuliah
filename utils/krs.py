import streamlit as st


_KRS_KEY = "krs_selected_by_semester"
_ACTIVE_SEMESTER_KEY = "krs_active_semester"


def get_active_semester() -> int | None:
    value = st.session_state.get(_ACTIVE_SEMESTER_KEY)
    return int(value) if value is not None else None


def set_active_semester(semester: int) -> None:
    st.session_state[_ACTIVE_SEMESTER_KEY] = int(semester)


def get_krs_for_semester(semester: int) -> list[str]:
    data = st.session_state.get(_KRS_KEY, {})
    return list(data.get(str(semester), []))


def set_krs_for_semester(semester: int, courses: list[str]) -> None:
    data = st.session_state.setdefault(_KRS_KEY, {})
    data[str(semester)] = list(dict.fromkeys(courses))


def get_active_krs() -> list[str]:
    semester = get_active_semester()
    if semester is None:
        return []
    return get_krs_for_semester(semester)


def is_krs_configured() -> bool:
    return bool(st.session_state.get(_KRS_KEY))


def reset_krs() -> None:
    st.session_state.pop(_KRS_KEY, None)
    st.session_state.pop(_ACTIVE_SEMESTER_KEY, None)
