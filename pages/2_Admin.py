from datetime import time as dtime

import pandas as pd
import streamlit as st
from streamlit_quill import st_quill

from utils.auth import current_email, get_authed_client, is_admin, login, logout, signup
from utils.helpers import JENIS, MATA_KULIAH, format_deadline, now_wib, parse_deadline, to_utc_iso
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.supabase_client import ConfigError, delete_task, fetch_tasks, insert_task, update_task, upload_file

st.set_page_config(page_title="Admin — Tugas Kuliah", layout="wide")
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)
st.title("Admin")


def _ambil_html(hasil_quill) -> str:
    if isinstance(hasil_quill, dict):
        return (hasil_quill.get("html") or "").strip()
    return (hasil_quill or "").strip()


if not is_admin():
    st.write("Halaman ini hanya untuk admin. Silakan masuk atau daftar akun baru.")
    tab_login, tab_signup = st.tabs(["Masuk", "Daftar Akun Baru"])

    with tab_login:
        with st.form("form_login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk", type="primary")
        if submit:
            berhasil, pesan = login(email, password)
            if berhasil:
                st.toast("Login berhasil!")
                st.rerun()
            else:
                st.error(pesan)

    with tab_signup:
        st.caption("Khusus untuk anggota/teman yang email-nya sudah didaftarkan oleh Super Admin.")
        with st.form("form_signup"):
            reg_email = st.text_input("Email yang terdaftar")
            reg_password = st.text_input("Buat Password Baru", type="password")
            reg_submit = st.form_submit_button("Daftar Akun", type="primary")
        if reg_submit:
            berhasil, pesan = signup(reg_email, reg_password)
            if berhasil:
                st.toast("Pendaftaran akun berhasil! Silakan login.")
            else:
                st.error(pesan)
    st.stop()

with st.sidebar:
    st.markdown('<p class="label-kecil">Masuk sebagai</p>', unsafe_allow_html=True)
    st.write(current_email())
    if st.button("Keluar", use_container_width=True):
        logout()
        st.toast("Berhasil keluar.")
        st.rerun()

client = get_authed_client()
if client is None:
    st.error("Sesi tidak valid. Keluar lalu masuk ulang.")
    st.stop()

try:
    tasks = fetch_tasks()
except ConfigError as exc:
    st.error(f"Konfigurasi belum lengkap.\n\n{exc}")
    st.stop()
except Exception as exc:
    st.error(f"Gagal mengambil data dari Supabase.\n\nPesan asli: `{exc}`")
    st.stop()

tab_tambah, tab_kelola, tab_admin_users = st.tabs(["Tambah tugas", "Kelola tugas", "Kelola Admin"])

with tab_tambah:
    judul = st.text_input("Judul tugas", key="tambah_judul")

    c1, c2 = st.columns(2)
    mata_kuliah = c1.selectbox("Mata kuliah", MATA_KULIAH, key="tambah_matkul")
    jenis = c2.selectbox("Jenis", JENIS, index=JENIS.index("Teori"), key="tambah_jenis")

    c3, c4 = st.columns(2)
    tgl = c3.date_input("Tanggal deadline", value=now_wib().date(), key="tambah_tgl")
    jam = c4.time_input("Jam deadline (WIB)", value=dtime(23, 59), key="tambah_jam")

    st.markdown('<p class="label-kecil">Ketentuan</p>', unsafe_allow_html=True)
    st.caption(
        "Tulis seperti di Word/Google Docs — bisa tebal, miring, dan daftar berpoin/nomor. "
        "Untuk tugas tanpa link VClass, tulis cara pengumpulannya di sini."
    )
    ketentuan_raw = st_quill(placeholder="Contoh: Format PDF, maksimal 10 halaman.", key="tambah_ketentuan")

    link_vclass = st.text_input(
        "Link VClass (boleh kosong)",
        placeholder="https://vclass.unila.ac.id/mod/assign/view.php?id=...",
        key="tambah_link",
    )

    f_uploaded = st.file_uploader(
        "Upload File Soal/Ketentuan (PDF, Gambar, Docs, Zip)",
        type=["pdf", "png", "jpg", "jpeg", "docx", "zip"],
        key="tambah_file",
    )

    if st.button("Simpan tugas", type="primary", key="tambah_simpan"):
        link_bersih = link_vclass.strip()
        ketentuan_bersih = _ambil_html(ketentuan_raw)
        if not judul.strip():
            st.error("Judul tugas wajib diisi.")
        elif link_bersih and not link_bersih.lower().startswith(("http://", "https://")):
            st.error("Link VClass harus diawali http:// atau https:// — atau dikosongkan.")
        else:
            try:
                file_url = upload_file(client, f_uploaded) if f_uploaded else None
                payload = {
                    "judul": judul.strip(),
                    "mata_kuliah": mata_kuliah,
                    "jenis": jenis,
                    "deadline": to_utc_iso(tgl, jam),
                    "ketentuan": ketentuan_bersih or None,
                    "link_vclass": link_bersih or None,
                    "file_soal": file_url,
                    "status": "Belum",
                }
                insert_task(client, payload)
                for k in ["tambah_judul", "tambah_link"]:
                    st.session_state.pop(k, None)
                st.toast("Tugas berhasil disimpan.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menyimpan data/file.\n\nPesan asli: `{exc}`")

with tab_kelola:
    if not tasks:
        st.write("Belum ada tugas.")
    else:
        f1, f2 = st.columns(2)
        f_matkul = f1.multiselect("Mata kuliah", MATA_KULIAH)
        f_jenis = f2.multiselect("Jenis", JENIS)
        cari = st.text_input("Cari judul / ketentuan")

        hasil = tasks
        if f_matkul:
            hasil = [t for t in hasil if t.get("mata_kuliah") in f_matkul]
        if f_jenis:
            hasil = [t for t in hasil if t.get("jenis") in f_jenis]
        if cari.strip():
            kunci = cari.strip().lower()
            hasil = [
                t
                for t in hasil
                if kunci in (t.get("judul") or "").lower() or kunci in (t.get("ketentuan") or "").lower()
            ]

        st.caption(f"Menampilkan {len(hasil)} dari {len(tasks)} tugas.")

        if hasil:
            df = pd.DataFrame(
                [
                    {
                        "judul": t["judul"],
                        "mata_kuliah": t["mata_kuliah"],
                        "jenis": t.get("jenis"),
                        "deadline_wib": parse_deadline(t["deadline"]).strftime("%Y-%m-%d %H:%M"),
                        "link_vclass": t.get("link_vclass") or "",
                        "file_soal": t.get("file_soal") or "",
                        "ketentuan": t.get("ketentuan") or "",
                    }
                    for t in hasil
                ]
            )
            st.download_button(
                "Export CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name="tugas-kuliah.csv",
                mime="text/csv",
            )

        st.divider()

        for t in hasil:
            label = f"{t['judul']} — {t['mata_kuliah']} ({format_deadline(t['deadline'])})"
            with st.expander(label):
                dt_lokal = parse_deadline(t["deadline"])
                tid = t["id"]

                e_judul = st.text_input("Judul", value=t["judul"], key=f"edit_judul_{tid}")

                c1, c2 = st.columns(2)
                matkul_saat_ini = t.get("mata_kuliah")
                opsi_matkul = MATA_KULIAH.copy()
                if matkul_saat_ini and matkul_saat_ini not in opsi_matkul:
                    opsi_matkul.append(matkul_saat_ini)
                e_matkul = c1.selectbox(
                    "Mata kuliah",
                    opsi_matkul,
                    index=opsi_matkul.index(matkul_saat_ini) if matkul_saat_ini in opsi_matkul else 0,
                    key=f"edit_matkul_{tid}",
                )
                e_jenis = c2.selectbox(
                    "Jenis", JENIS, index=JENIS.index(t.get("jenis", "Teori")), key=f"edit_jenis_{tid}"
                )

                c3, c4 = st.columns(2)
                e_tgl = c3.date_input("Tanggal deadline", value=dt_lokal.date(), key=f"edit_tgl_{tid}")
                e_jam = c4.time_input("Jam deadline (WIB)", value=dt_lokal.time(), key=f"edit_jam_{tid}")

                st.markdown('<p class="label-kecil">Ketentuan</p>', unsafe_allow_html=True)
                e_ketentuan_raw = st_quill(
                    value=t.get("ketentuan") or "",
                    key=f"edit_ketentuan_{tid}",
                )
                e_link = st.text_input("Link VClass", value=t.get("link_vclass") or "", key=f"edit_link_{tid}")

                if t.get("file_soal"):
                    st.markdown(
                        f'<a href="{t["file_soal"]}" target="_blank">Lihat file saat ini</a>', unsafe_allow_html=True
                    )

                e_file = st.file_uploader(
                    "Ganti File Soal/Ketentuan",
                    type=["pdf", "png", "jpg", "jpeg", "docx", "zip"],
                    key=f"edit_file_{tid}",
                )

                if st.button("Simpan perubahan", key=f"edit_simpan_{tid}"):
                    link_bersih = e_link.strip()
                    ketentuan_bersih = _ambil_html(e_ketentuan_raw)
                    if link_bersih and not link_bersih.lower().startswith(("http://", "https://")):
                        st.error("Link VClass harus diawali http:// atau https://.")
                    else:
                        try:
                            file_url = upload_file(client, e_file) if e_file else t.get("file_soal")
                            update_task(
                                client,
                                tid,
                                {
                                    "judul": e_judul.strip(),
                                    "mata_kuliah": e_matkul,
                                    "jenis": e_jenis,
                                    "deadline": to_utc_iso(e_tgl, e_jam),
                                    "ketentuan": ketentuan_bersih or None,
                                    "link_vclass": link_bersih or None,
                                    "file_soal": file_url,
                                },
                                old_file_url=t.get("file_soal") if e_file else None,
                            )
                            st.toast("Perubahan tersimpan.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Gagal menyimpan perubahan.\n\nPesan asli: `{exc}`")

                st.divider()
                konfirmasi = st.checkbox("Saya yakin ingin menghapus tugas ini", key=f"konfirmasi_{tid}")
                if st.button("Hapus tugas", key=f"hapus_{tid}", disabled=not konfirmasi):
                    try:
                        delete_task(client, tid)
                        st.toast("Tugas dan file terhapus.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menghapus.\n\nPesan asli: `{exc}`")

with tab_admin_users:
    st.subheader("Daftar Email Admin Ditambahkan")
    st.caption(
        "Masukkan email teman yang ingin diberi akses admin. Setelah didaftarkan di sini, mereka bisa langsung membuat akun sendiri di tab Daftar Akun Baru."
    )

    new_admin_email = st.text_input("Tambah Email Admin Baru", placeholder="contoh: teman@gmail.com")
    if st.button("Tambah Admin", type="primary"):
        if not new_admin_email.strip() or "@" not in new_admin_email:
            st.error("Email tidak valid.")
        else:
            try:
                client.table("admin_users").insert({"email": new_admin_email.strip().lower()}).execute()
                st.toast(f"Berhasil menambahkan {new_admin_email}!")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menambahkan admin: {exc}")

    st.divider()
    try:
        admins = client.table("admin_users").select("*").execute().data or []
        st.write("**Daftar Admin Aktif:**")
        for a in admins:
            st.text(f"• {a['email']}")
    except Exception as exc:
        st.error(f"Gagal memuat daftar admin: {exc}")
