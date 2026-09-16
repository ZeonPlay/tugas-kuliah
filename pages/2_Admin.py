"""
Halaman admin: login Supabase Auth + CRUD tugas.

Pengecekan is_admin() di sini hanya mengatur tampilan. Perlindungan
sebenarnya ada di policy RLS (sql/setup.sql): tanpa token admin,
database menolak INSERT/UPDATE/DELETE apa pun.
"""

from datetime import time as dtime

import pandas as pd
import streamlit as st

from utils.auth import current_email, get_authed_client, is_admin, login, logout
from utils.helpers import (
    JENIS,
    MATA_KULIAH,
    PRIORITAS,
    STATUS,
    format_deadline,
    now_wib,
    parse_deadline,
    to_utc_iso,
)
from utils.supabase_client import (
    ConfigError,
    delete_task,
    fetch_tasks,
    insert_task,
    update_task,
)

st.set_page_config(page_title="Admin Tugas", page_icon="🔐", layout="wide")
st.title("🔐 Admin")

# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------
if not is_admin():
    st.info("Halaman ini hanya untuk admin. Silakan login.")
    with st.form("form_login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    if submit:
        berhasil, pesan = login(email, password)
        if berhasil:
            st.rerun()
        else:
            st.error(pesan)
    st.stop()

with st.sidebar:
    st.success(f"Login sebagai\n\n**{current_email()}**")
    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()

client = get_authed_client()
if client is None:
    st.error("Sesi tidak valid. Silakan logout lalu login ulang.")
    st.stop()

try:
    tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"⚙️ Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"🔌 Gagal mengambil data dari Supabase.\n\nPesan asli: `{exc}`")
    st.stop()

tab_tambah, tab_kelola = st.tabs(["➕ Tambah Tugas", "📋 Kelola Tugas"])

# ---------------------------------------------------------------------
# Tab 1 — Tambah
# ---------------------------------------------------------------------
with tab_tambah:
    with st.form("form_tambah", clear_on_submit=True):
        judul = st.text_input("Judul tugas *")

        c1, c2 = st.columns(2)
        mata_kuliah = c1.selectbox("Mata kuliah *", MATA_KULIAH)
        jenis = c2.selectbox("Jenis *", JENIS, index=JENIS.index("Teori"))

        c3, c4 = st.columns(2)
        tgl = c3.date_input("Tanggal deadline *", value=now_wib().date())
        jam = c4.time_input("Jam deadline (WIB) *", value=dtime(23, 59))

        ketentuan = st.text_area(
            "Ketentuan",
            placeholder=(
                "Contoh: Format PDF, maksimal 10 halaman.\n"
                "Untuk tugas tanpa link, tulis cara pengumpulannya di sini "
                "(mis. 'Dikumpulkan langsung ke dosen saat kelas berikutnya')."
            ),
            height=120,
        )

        link_vclass = st.text_input(
            "Link VClass (boleh kosong)",
            placeholder="https://vclass.unila.ac.id/mod/assign/view.php?id=...",
        )

        c5, c6 = st.columns(2)
        prioritas = c5.selectbox("Prioritas", PRIORITAS, index=PRIORITAS.index("Sedang"))
        status = c6.selectbox("Status", STATUS, index=STATUS.index("Belum"))

        simpan = st.form_submit_button("Simpan tugas", type="primary")

    if simpan:
        link_bersih = link_vclass.strip()
        if not judul.strip():
            st.error("Judul tugas wajib diisi.")
        elif link_bersih and not link_bersih.lower().startswith(("http://", "https://")):
            st.error("Link VClass harus diawali http:// atau https:// — atau dikosongkan.")
        else:
            payload = {
                "judul": judul.strip(),
                "mata_kuliah": mata_kuliah,
                "jenis": jenis,
                "deadline": to_utc_iso(tgl, jam),
                "ketentuan": ketentuan.strip() or None,
                "link_vclass": link_bersih or None,
                "prioritas": prioritas,
                "status": status,
            }
            try:
                insert_task(client, payload)
                st.success("Tugas tersimpan.")
                st.rerun()
            except Exception as exc:
                st.error(
                    "Gagal menyimpan. Kalau pesannya soal row-level security, "
                    "berarti email di policy RLS belum cocok dengan akun ini.\n\n"
                    f"Pesan asli: `{exc}`"
                )

# ---------------------------------------------------------------------
# Tab 2 — Kelola (filter, edit, hapus, export)
# ---------------------------------------------------------------------
with tab_kelola:
    if not tasks:
        st.info("Belum ada tugas.")
        st.stop()

    f1, f2, f3 = st.columns(3)
    f_matkul = f1.multiselect("Mata kuliah", MATA_KULIAH)
    f_jenis = f2.multiselect("Jenis", JENIS)
    f_status = f3.multiselect("Status", STATUS)
    cari = st.text_input("🔍 Cari judul / ketentuan")

    hasil = tasks
    if f_matkul:
        hasil = [t for t in hasil if t.get("mata_kuliah") in f_matkul]
    if f_jenis:
        hasil = [t for t in hasil if t.get("jenis") in f_jenis]
    if f_status:
        hasil = [t for t in hasil if t.get("status") in f_status]
    if cari.strip():
        kunci = cari.strip().lower()
        hasil = [
            t
            for t in hasil
            if kunci in (t.get("judul") or "").lower()
            or kunci in (t.get("ketentuan") or "").lower()
        ]

    st.caption(f"Menampilkan {len(hasil)} dari {len(tasks)} tugas.")

    # --- Export (backup) ---
    if hasil:
        df = pd.DataFrame(
            [
                {
                    "judul": t["judul"],
                    "mata_kuliah": t["mata_kuliah"],
                    "jenis": t.get("jenis"),
                    "deadline_wib": parse_deadline(t["deadline"]).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "prioritas": t.get("prioritas"),
                    "status": t.get("status"),
                    "link_vclass": t.get("link_vclass") or "",
                    "ketentuan": t.get("ketentuan") or "",
                }
                for t in hasil
            ]
        )
        st.download_button(
            "⬇️ Export CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="tugas-kuliah.csv",
            mime="text/csv",
        )

    st.divider()

    for t in hasil:
        label = f"{t['judul']} — {t['mata_kuliah']} ({format_deadline(t['deadline'])})"
        with st.expander(label):
            dt_lokal = parse_deadline(t["deadline"])

            with st.form(f"form_edit_{t['id']}"):
                e_judul = st.text_input("Judul", value=t["judul"])

                c1, c2 = st.columns(2)
                matkul_saat_ini = t.get("mata_kuliah")
                opsi_matkul = MATA_KULIAH.copy()
                if matkul_saat_ini and matkul_saat_ini not in opsi_matkul:
                    # Data lama dari mata kuliah semester sebelumnya tetap muncul
                    opsi_matkul.append(matkul_saat_ini)
                e_matkul = c1.selectbox(
                    "Mata kuliah",
                    opsi_matkul,
                    index=opsi_matkul.index(matkul_saat_ini)
                    if matkul_saat_ini in opsi_matkul
                    else 0,
                )
                e_jenis = c2.selectbox(
                    "Jenis", JENIS, index=JENIS.index(t.get("jenis", "Teori"))
                )

                c3, c4 = st.columns(2)
                e_tgl = c3.date_input("Tanggal deadline", value=dt_lokal.date())
                e_jam = c4.time_input("Jam deadline (WIB)", value=dt_lokal.time())

                e_ketentuan = st.text_area(
                    "Ketentuan", value=t.get("ketentuan") or "", height=120
                )
                e_link = st.text_input(
                    "Link VClass", value=t.get("link_vclass") or ""
                )

                c5, c6 = st.columns(2)
                e_prioritas = c5.selectbox(
                    "Prioritas",
                    PRIORITAS,
                    index=PRIORITAS.index(t.get("prioritas", "Sedang")),
                )
                e_status = c6.selectbox(
                    "Status", STATUS, index=STATUS.index(t.get("status", "Belum"))
                )

                simpan_edit = st.form_submit_button("💾 Simpan perubahan")

            if simpan_edit:
                link_bersih = e_link.strip()
                if link_bersih and not link_bersih.lower().startswith(
                    ("http://", "https://")
                ):
                    st.error("Link VClass harus diawali http:// atau https://.")
                else:
                    try:
                        update_task(
                            client,
                            t["id"],
                            {
                                "judul": e_judul.strip(),
                                "mata_kuliah": e_matkul,
                                "jenis": e_jenis,
                                "deadline": to_utc_iso(e_tgl, e_jam),
                                "ketentuan": e_ketentuan.strip() or None,
                                "link_vclass": link_bersih or None,
                                "prioritas": e_prioritas,
                                "status": e_status,
                            },
                        )
                        st.success("Perubahan tersimpan.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menyimpan perubahan.\n\nPesan asli: `{exc}`")

            # --- Hapus, dengan konfirmasi ---
            st.markdown("---")
            konfirmasi = st.checkbox(
                "Saya yakin ingin menghapus tugas ini", key=f"konfirmasi_{t['id']}"
            )
            if st.button(
                "🗑️ Hapus tugas",
                key=f"hapus_{t['id']}",
                disabled=not konfirmasi,
                type="secondary",
            ):
                try:
                    delete_task(client, t["id"])
                    st.success("Tugas dihapus.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal menghapus.\n\nPesan asli: `{exc}`")
