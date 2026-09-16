"""
Koneksi ke Supabase + semua query ke tabel `tasks`.

Ada DUA jenis client di sini, dan pemisahan ini penting:

1. get_public_client()  -> client ANONIM, di-cache dengan st.cache_resource.
   Dipakai untuk semua operasi baca. Karena st.cache_resource dibagi ke
   SEMUA pengunjung aplikasi, client ini tidak boleh pernah membawa token
   login siapa pun.

2. get_authed_client()  -> client dengan token admin, dibuat ulang per
   session dari token yang disimpan di st.session_state (lihat utils/auth.py).
   TIDAK di-cache, supaya token admin tidak bocor ke sesi pengunjung lain.
"""

import os

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


# ---------------------------------------------------------------------
# Kredensial
# ---------------------------------------------------------------------
def read_config(name: str, default: str | None = None) -> str | None:
    """Ambil konfigurasi dari .env (lokal) atau st.secrets (Streamlit Cloud)."""
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets[name]
    except Exception:
        # st.secrets melempar error kalau file secrets.toml tidak ada
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


# ---------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_public_client() -> Client:
    """Client anonim untuk baca. Dibagi ke semua pengunjung — jangan diberi token."""
    url, key = _require_credentials()
    return create_client(url, key)


def build_client_with_token(access_token: str) -> Client:
    """Client baru yang memakai token login admin (dipakai utils/auth.py)."""
    url, key = _require_credentials()
    client = create_client(url, key)
    # Supaya PostgREST mengirim Authorization: Bearer <token>,
    # sehingga policy RLS untuk 'authenticated' ikut dievaluasi.
    client.postgrest.auth(access_token)
    return client


# ---------------------------------------------------------------------
# Query baca (dipakai halaman publik & admin)
# ---------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_tasks() -> list[dict]:
    """
    Ambil semua tugas, diurutkan dari deadline paling awal.

    ttl=30 detik disamakan dengan interval auto-refresh halaman kalender,
    supaya refresh tidak memukul database setiap kali halaman dimuat ulang.
    """
    client = get_public_client()
    response = client.table("tasks").select("*").order("deadline").execute()
    return response.data or []


def clear_cache() -> None:
    """Panggil setelah insert/update/delete supaya data langsung segar."""
    fetch_tasks.clear()


# ---------------------------------------------------------------------
# Query tulis (hanya berhasil kalau token admin lolos RLS)
# ---------------------------------------------------------------------
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
