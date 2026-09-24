import streamlit as st
from supabase import create_client

from utils.supabase_client import ConfigError, _require_credentials, build_client_with_token

_TOKEN_KEY = "sb_access_token"
_EMAIL_KEY = "sb_email"


def is_email_whitelisted(email: str) -> bool:
    """Cek apakah email ada di tabel admin_users."""
    try:
        url, key = _require_credentials()
        client = create_client(url, key)
        res = client.table("admin_users").select("email").eq("email", email.strip().lower()).execute()
        return len(res.data or []) > 0
    except Exception:
        return False


def login(email: str, password: str) -> tuple[bool, str]:
    email_clean = email.strip().lower()
    try:
        url, key = _require_credentials()
        client = create_client(url, key)
        result = client.auth.sign_in_with_password({"email": email_clean, "password": password})
    except Exception as exc:
        return False, f"Login gagal: {exc}"

    session = getattr(result, "session", None)
    user = getattr(result, "user", None)
    if session is None or user is None:
        return False, "Login gagal: email atau password salah."

    if not is_email_whitelisted(email_clean):
        return False, "Akun ini belum didaftarkan sebagai admin oleh Super Admin."

    st.session_state[_TOKEN_KEY] = session.access_token
    st.session_state[_EMAIL_KEY] = email_clean
    return True, "Login berhasil."


def signup(email: str, password: str) -> tuple[bool, str]:
    email_clean = email.strip().lower()
    if not is_email_whitelisted(email_clean):
        return False, "Email ini belum didaftarkan ke daftar admin. Minta Super Admin untuk menambahkan emailmu dulu."

    try:
        url, key = _require_credentials()
        client = create_client(url, key)
        result = client.auth.sign_up({"email": email_clean, "password": password})
        if getattr(result, "user", None):
            return True, "Pendaftaran berhasil! Sekarang silakan login di tab Masuk."
        return False, "Pendaftaran gagal."
    except Exception as exc:
        return False, f"Gagal mendaftar: {exc}"


def logout() -> None:
    st.session_state.pop(_TOKEN_KEY, None)
    st.session_state.pop(_EMAIL_KEY, None)


def is_admin() -> bool:
    email = st.session_state.get(_EMAIL_KEY)
    return bool(st.session_state.get(_TOKEN_KEY)) and is_email_whitelisted(email)


def current_email() -> str | None:
    return st.session_state.get(_EMAIL_KEY)


def get_authed_client():
    token = st.session_state.get(_TOKEN_KEY)
    if not token:
        return None
    try:
        return build_client_with_token(token)
    except ConfigError:
        return None
