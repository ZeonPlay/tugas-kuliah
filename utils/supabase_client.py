import os
import uuid

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def read_config(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets[name]
    except Exception:
        return default


SUPABASE_URL = read_config("SUPABASE_URL")
SUPABASE_ANON_KEY = read_config("SUPABASE_ANON_KEY")
ADMIN_EMAIL = (read_config("ADMIN_EMAIL") or "").strip().lower()


class ConfigError(RuntimeError):
    """Kredensial Supabase belum diisi."""


def _require_credentials() -> tuple[str, str]:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ConfigError(
            "SUPABASE_URL / SUPABASE_ANON_KEY belum diisi. "
            "Di lokal: buat file .env (contoh ada di .env.example). "
            "Di Streamlit Cloud: isi lewat menu Settings > Secrets."
        )
    return SUPABASE_URL, SUPABASE_ANON_KEY


@st.cache_resource(show_spinner=False)
def get_public_client() -> Client:
    url, key = _require_credentials()
    return create_client(url, key)


def build_client_with_token(access_token: str) -> Client:
    url, key = _require_credentials()
    client = create_client(url, key)
    client.postgrest.auth(access_token)
    return client


@st.cache_data(ttl=30, show_spinner=False)
def fetch_tasks() -> list[dict]:
    client = get_public_client()
    response = client.table("tasks").select("*").order("deadline").execute()
    return response.data or []


def clear_cache() -> None:
    fetch_tasks.clear()


def insert_task(client: Client, payload: dict) -> dict:
    response = client.table("tasks").insert(payload).execute()
    clear_cache()
    return (response.data or [{}])[0]


def update_task(client: Client, task_id: str, payload: dict) -> dict:
    response = client.table("tasks").update(payload).eq("id", task_id).execute()
    clear_cache()
    return (response.data or [{}])[0]


def delete_task(client: Client, task_id: str) -> None:
    client.table("tasks").delete().eq("id", task_id).execute()
    clear_cache()


def upload_file(client: Client, uploaded_file) -> str:
    """Upload file ke bucket 'task-files' dan mengembalikan public URL nya."""
    if not uploaded_file:
        return None

    ext = uploaded_file.name.split(".")[-1]
    file_name = f"{uuid.uuid4().hex}.{ext}"
    file_bytes = uploaded_file.getvalue()

    # Upload ke Supabase Storage
    client.storage.from_("task-files").upload(
        path=file_name, file=file_bytes, file_options={"content-type": uploaded_file.type}
    )

    # Ambil public URL
    public_url = client.storage.from_("task-files").get_public_url(file_name)
    return public_url
