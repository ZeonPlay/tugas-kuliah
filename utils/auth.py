"""
Login / logout admin lewat Supabase Auth.

Catatan keamanan: fungsi is_admin() di sini hanya mengatur TAMPILAN.
Yang benar-benar melindungi data adalah policy RLS di sql/setup.sql.
Kalau seseorang memanipulasi session Streamlit, database tetap menolak
operasi tulis karena email di JWT-nya tidak cocok.
"""

import streamlit as st
from supabase import Client

from utils.supabase_client import (
    ADMIN_EMAIL,
    ConfigError,
    build_client_with_token,
    _require_credentials,
)
from supabase import create_client

_TOKEN_KEY = "sb_access_token"
_EMAIL_KEY = "sb_email"


def login(email: str, password: str) -> tuple[bool, str]:
    """Return (berhasil, pesan)."""
    try:
        url, key = _require_credentials()
    except ConfigError as exc:
        return False, str(exc)

    try:
        client = create_client(url, key)
        result = client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
    except Exception as exc:
        return False, f"Login gagal: {exc}"

    session = getattr(result, "session", None)
    user = getattr(result, "user", None)
    if session is None or user is None:
        return False, "Login gagal: email atau password salah."

    user_email = (user.email or "").strip().lower()
    if not ADMIN_EMAIL:
        return False, "ADMIN_EMAIL belum diisi di .env / secrets."
    if user_email != ADMIN_EMAIL:
        # Akun valid tapi bukan admin — RLS juga akan menolaknya.
        return False, "Akun ini bukan admin."

    st.session_state[_TOKEN_KEY] = session.access_token
    st.session_state[_EMAIL_KEY] = user_email
    return True, "Login berhasil."


def logout() -> None:
    st.session_state.pop(_TOKEN_KEY, None)
    st.session_state.pop(_EMAIL_KEY, None)


def is_admin() -> bool:
    email = st.session_state.get(_EMAIL_KEY)
    return bool(st.session_state.get(_TOKEN_KEY)) and email == ADMIN_EMAIL


def current_email() -> str | None:
    return st.session_state.get(_EMAIL_KEY)


def get_authed_client() -> Client | None:
    """Client ber-token untuk operasi tulis. None kalau belum login."""
    token = st.session_state.get(_TOKEN_KEY)
    if not token:
        return None
    try:
        return build_client_with_token(token)
    except ConfigError:
        return None
