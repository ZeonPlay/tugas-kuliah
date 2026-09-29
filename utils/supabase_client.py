import os
import uuid

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, ClientOptions, create_client

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
    options = ClientOptions(headers={"Authorization": f"Bearer {access_token}"})
    client = create_client(url, key, options=options)
    client.postgrest.auth(access_token)
    return client


@st.cache_data(ttl=30, show_spinner=False)
def fetch_tasks() -> list[dict]:
    client = get_public_client()
    response = client.table("tasks").select("*").order("deadline").execute()
    return response.data or []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_courses(only_active: bool = True) -> list[dict]:
    client = get_public_client()
    query = client.table("courses").select("id,kode,nama,semester,kategori,aktif").order("semester").order("nama")
    if only_active:
        query = query.eq("aktif", True)
    response = query.execute()
    return response.data or []


def clear_cache() -> None:
    fetch_tasks.clear()
    fetch_courses.clear()
    fetch_module_folders.clear()


def delete_file_from_storage(client: Client, file_url: str | None) -> None:
    """Hapus file dari bucket 'task-files' berdasarkan public URL."""
    if not file_url:
        return
    try:
        file_name = file_url.split("/task-files/")[-1]
        if file_name:
            client.storage.from_("task-files").remove([file_name])
    except Exception:
        pass


@st.cache_data(ttl=300, show_spinner=False)
def fetch_module_folders(only_active: bool = True) -> list[dict]:
    client = get_public_client()
    query = (
        client.table("module_folders")
        .select("id,course_id,judul,urutan,url,keterangan,aktif")
        .order("urutan")
        .order("judul")
    )
    if only_active:
        query = query.eq("aktif", True)
    response = query.execute()
    return response.data or []


def insert_module_folder(client: Client, payload: dict) -> dict:
    response = client.table("module_folders").insert(payload).execute()
    fetch_module_folders.clear()
    return (response.data or [{}])[0]


def update_module_folder(client: Client, module_id: str, payload: dict) -> dict:
    response = client.table("module_folders").update(payload).eq("id", module_id).execute()
    fetch_module_folders.clear()
    return (response.data or [{}])[0]


def delete_module_folder(client: Client, module_id: str) -> None:
    client.table("module_folders").delete().eq("id", module_id).execute()
    fetch_module_folders.clear()


def insert_course(client: Client, payload: dict) -> dict:
    response = client.table("courses").insert(payload).execute()
    fetch_courses.clear()
    return (response.data or [{}])[0]


def update_course(client: Client, course_id: str, payload: dict) -> dict:
    response = client.table("courses").update(payload).eq("id", course_id).execute()
    fetch_courses.clear()
    return (response.data or [{}])[0]


def insert_task(client: Client, payload: dict) -> dict:
    response = client.table("tasks").insert(payload).execute()
    clear_cache()
    return (response.data or [{}])[0]


def update_task(client: Client, task_id: str, payload: dict, old_file_url: str | None = None) -> dict:
    # Jika file diganti dengan file baru, hapus file lama dari storage
    if old_file_url and payload.get("file_soal") != old_file_url:
        delete_file_from_storage(client, old_file_url)

    response = client.table("tasks").update(payload).eq("id", task_id).execute()
    clear_cache()
    return (response.data or [{}])[0]


def delete_task(client: Client, task_id: str) -> None:
    # Hapus file lampiran terlebih dahulu jika ada
    try:
        res = client.table("tasks").select("file_soal").eq("id", task_id).execute()
        if res.data and res.data[0].get("file_soal"):
            delete_file_from_storage(client, res.data[0]["file_soal"])
    except Exception:
        pass

    client.table("tasks").delete().eq("id", task_id).execute()
    clear_cache()


def upload_file(client: Client, uploaded_file) -> str:
    """Upload file ke bucket 'task-files' dan mengembalikan public URL nya."""
    if not uploaded_file:
        return None

    ext = uploaded_file.name.split(".")[-1]
    file_name = f"{uuid.uuid4().hex}.{ext}"
    file_bytes = uploaded_file.getvalue()

    client.storage.from_("task-files").upload(
        path=file_name, file=file_bytes, file_options={"content-type": uploaded_file.type}
    )

    public_url = client.storage.from_("task-files").get_public_url(file_name)
    return public_url
