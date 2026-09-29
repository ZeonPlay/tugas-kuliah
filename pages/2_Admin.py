from datetime import time as dtime

import streamlit as st
from utils.editor import rich_text_editor, rich_text_to_markdown, reset_rich_text_editor

from utils.auth import current_email, get_authed_client, is_admin, login, logout, signup
from utils.helpers import JENIS, format_deadline, now_wib, parse_deadline, to_utc_iso
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.supabase_client import (
    ADMIN_EMAIL,
    delete_task,
    fetch_courses,
    fetch_modules,
    fetch_tasks,
    insert_course,
    insert_module,
    insert_task,
    update_course,
    update_module,
    update_task,
    delete_module,
    upload_file,
)

st.set_page_config(page_title="Admin Tugas Kuliah", layout="wide")
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)

st.title("Panel Admin")


def _ambil_markdown(hasil_editor) -> str:
    return (hasil_editor or "").strip()


if not is_admin():
    st.warning("Halaman ini hanya untuk admin. Silakan masuk atau daftar akun baru.")
    tab_login, tab_signup = st.tabs(["Masuk", "Daftar Akun Baru"])
    with tab_login:
        with st.form("form_login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk", type="primary", use_container_width=True)
        if submit:
            berhasil, pesan = login(email, password)
            if berhasil:
                st.toast("Login berhasil!")
                st.rerun()
            else:
                st.error(pesan)
    with tab_signup:
        st.caption("Khusus untuk anggota yang email-nya sudah didaftarkan oleh Super Admin.")
        with st.form("form_signup"):
            reg_email = st.text_input("Email yang terdaftar")
            reg_password = st.text_input("Buat Password Baru", type="password")
            reg_submit = st.form_submit_button("Daftar Akun", type="primary", use_container_width=True)
        if reg_submit:
            berhasil, pesan = signup(reg_email, reg_password)
            if berhasil:
                st.toast("Pendaftaran akun berhasil! Silakan login.")
            else:
                st.error(pesan)
    st.stop()

with st.sidebar:
    st.write("Masuk sebagai:")
    st.write(f"**{current_email()}**")
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
    courses = fetch_courses(only_active=False)
    modules = fetch_modules(only_active=False)
except Exception as exc:
    st.error(f"Gagal mengambil data: {exc}")
    st.stop()

active_courses = [course for course in courses if course.get("aktif", True)]
course_names = [course["nama"] for course in active_courses]
course_labels = {
    course["nama"]: (course.get("kode") or "-") + " · " + course["nama"]
    for course in active_courses
}

tab_tambah, tab_kelola, tab_kuliah, tab_modul, tab_admin_users = st.tabs(
    ["Tambah Tugas", "Kelola Tugas", "Mata Kuliah", "Arsip Modul", "Kelola Admin"]
)

with tab_tambah:
    judul = st.text_input("Judul tugas", key="tambah_judul")
    c1, c2 = st.columns(2)
    if not course_names:
        st.warning("Belum ada mata kuliah. Tambahkan mata kuliah terlebih dahulu di tab Mata Kuliah.")
        mata_kuliah = None
    else:
        mata_kuliah = c1.selectbox(
            "Mata kuliah",
            course_names,
            format_func=lambda name: course_labels.get(name, name),
            key="tambah_matkul",
        )
    jenis = c2.selectbox("Jenis", JENIS, index=JENIS.index("Teori"), key="tambah_jenis")

    c3, c4 = st.columns(2)
    tgl = c3.date_input("Tanggal deadline", value=now_wib().date(), key="tambah_tgl")
    jam = c4.time_input("Jam deadline (WIB)", value=dtime(23, 59), key="tambah_jam")

    st.write("**Ketentuan & Instruksi**")
    with st.container(border=True):
        ketentuan_raw = rich_text_editor(
            placeholder="Tulis ketentuan tugas di sini...",
            key="tambah_ketentuan",
        )

    link_vclass = st.text_input(
        "Link VClass (Opsional)", placeholder="https://vclass.unila.ac.id/...", key="tambah_link"
    )
    f_uploaded = st.file_uploader(
        "Upload File Soal/Ketentuan (Opsional)", type=["pdf", "png", "jpg", "jpeg", "docx", "zip"], key="tambah_file"
    )

    if st.button("Simpan Tugas Baru", type="primary", key="tambah_simpan"):
        link_bersih = link_vclass.strip()
        ketentuan_bersih = _ambil_markdown(ketentuan_raw)
        if not judul.strip():
            st.error("Judul tugas wajib diisi.")
        elif not mata_kuliah:
            st.error("Mata kuliah wajib dipilih.")
        elif link_bersih and not link_bersih.lower().startswith(("http://", "https://")):
            st.error("Link VClass harus diawali http:// atau https://")
        else:
            try:
                file_url = upload_file(client, f_uploaded) if f_uploaded else None
                insert_task(
                    client,
                    {
                        "judul": judul.strip(),
                        "mata_kuliah": mata_kuliah,
                        "jenis": jenis,
                        "deadline": to_utc_iso(tgl, jam),
                        "ketentuan": ketentuan_bersih or None,
                        "link_vclass": link_bersih or None,
                        "file_soal": file_url,
                    },
                )
                for k in ["tambah_judul", "tambah_link"]:
                    st.session_state.pop(k, None)
                reset_rich_text_editor("tambah_ketentuan")
                st.toast("Tugas berhasil disimpan.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menyimpan data: {exc}")

with tab_kelola:
    if not tasks:
        st.info("Belum ada tugas.")
    else:
        legacy_courses = sorted(
            {
                task.get("mata_kuliah")
                for task in tasks
                if task.get("mata_kuliah") and task.get("mata_kuliah") not in course_names
            }
        )
        filter_course_options = course_names + legacy_courses

        f1, f2 = st.columns(2)
        f_matkul = f1.multiselect("Filter Mata Kuliah", filter_course_options)
        f_jenis = f2.multiselect("Filter Jenis", JENIS)
        cari = st.text_input("Cari judul / ketentuan", placeholder="Ketik kata kunci...")

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
        st.divider()

        for t in hasil:
            label = f"{t['judul']} - {t['mata_kuliah']} ({format_deadline(t['deadline'])})"
            with st.expander(label):
                dt_lokal = parse_deadline(t["deadline"])
                tid = t["id"]
                e_judul = st.text_input("Judul", value=t["judul"], key=f"edit_judul_{tid}")

                c1, c2 = st.columns(2)
                matkul_saat_ini = t.get("mata_kuliah")
                opsi_matkul = course_names.copy()
                if matkul_saat_ini and matkul_saat_ini not in opsi_matkul:
                    opsi_matkul.append(matkul_saat_ini)
                e_matkul = c1.selectbox(
                    "Mata kuliah",
                    opsi_matkul,
                    format_func=lambda name: course_labels.get(name, name),
                    index=opsi_matkul.index(matkul_saat_ini) if matkul_saat_ini in opsi_matkul else 0,
                    key=f"edit_matkul_{tid}",
                )
                e_jenis = c2.selectbox(
                    "Jenis", JENIS, index=JENIS.index(t.get("jenis", "Teori")), key=f"edit_jenis_{tid}"
                )

                c3, c4 = st.columns(2)
                e_tgl = c3.date_input("Tanggal deadline", value=dt_lokal.date(), key=f"edit_tgl_{tid}")
                e_jam = c4.time_input("Jam deadline (WIB)", value=dt_lokal.time(), key=f"edit_jam_{tid}")

                st.write("**Ketentuan**")
                with st.container(border=True):
                    editor_key = f"edit_ketentuan_{tid}"
                    e_ketentuan_raw = rich_text_editor(
                        value=rich_text_to_markdown(t.get("ketentuan")),
                        placeholder="Tulis ketentuan tugas di sini...",
                        key=editor_key,
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

                if st.button("Simpan Perubahan", type="primary", key=f"edit_simpan_{tid}"):
                    link_bersih = e_link.strip()
                    if link_bersih and not link_bersih.lower().startswith(("http://", "https://")):
                        st.error("Link VClass harus valid.")
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
                                    "ketentuan": _ambil_markdown(e_ketentuan_raw) or None,
                                    "link_vclass": link_bersih or None,
                                    "file_soal": file_url,
                                },
                                old_file_url=t.get("file_soal") if e_file else None,
                            )
                            reset_rich_text_editor(editor_key)
                            st.toast("Perubahan tersimpan.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Gagal menyimpan: {exc}")

                st.divider()
                konfirmasi = st.checkbox("Saya yakin ingin menghapus tugas ini", key=f"konfirmasi_{tid}")
                if st.button("Hapus Tugas (Permanen)", key=f"hapus_{tid}", disabled=not konfirmasi):
                    try:
                        delete_task(client, tid)
                        st.toast("Tugas terhapus.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menghapus: {exc}")

with tab_kuliah:
    st.subheader("Katalog Mata Kuliah")
    st.caption("Daftar ini menjadi sumber mata kuliah untuk tugas dan pengaturan KRS. Semester dan kategori bisa diperbarui tanpa mengubah tugas lama.")

    with st.form("form_tambah_mata_kuliah"):
        c1, c2 = st.columns(2)
        kode_baru = c1.text_input("Kode mata kuliah", placeholder="Contoh: SI401")
        nama_baru = c2.text_input("Nama mata kuliah", placeholder="Contoh: Data Mining")

        c3, c4 = st.columns(2)
        semester_baru = c3.number_input("Semester", min_value=1, max_value=8, value=4, step=1)
        kategori_baru = c4.selectbox("Kategori", ["Wajib", "Pilihan", "Belum dikategorikan"])

        if st.form_submit_button("Tambah Mata Kuliah", type="primary", use_container_width=True):
            kode_bersih = kode_baru.strip().upper()
            nama_bersih = nama_baru.strip()
            try:
                if not nama_bersih:
                    raise ValueError("Nama mata kuliah wajib diisi.")
                insert_course(
                    client,
                    {
                        "kode": kode_bersih or None,
                        "nama": nama_bersih,
                        "semester": int(semester_baru),
                        "kategori": kategori_baru,
                        "aktif": True,
                    },
                )
                st.toast("Mata kuliah berhasil ditambahkan.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menambahkan mata kuliah: {exc}")

    st.divider()

    if not courses:
        st.info("Belum ada mata kuliah.")
    else:
        for course in courses:
            cid = course["id"]
            label = f'{course.get("kode") or "-"} · {course["nama"]} · Semester {course["semester"]}'
            with st.expander(label):
                c1, c2, c3 = st.columns([2, 1, 1])
                e_kode = c1.text_input("Kode", value=course.get("kode") or "", key=f"course_kode_{cid}")
                e_semester = c2.number_input(
                    "Semester",
                    min_value=1,
                    max_value=8,
                    value=int(course.get("semester") or 1),
                    step=1,
                    key=f"course_semester_{cid}",
                )
                kategori_opsi = ["Wajib", "Pilihan", "Belum dikategorikan"]
                current_kategori = course.get("kategori") or "Belum dikategorikan"
                e_kategori = c3.selectbox(
                    "Kategori",
                    kategori_opsi,
                    index=kategori_opsi.index(current_kategori) if current_kategori in kategori_opsi else 2,
                    key=f"course_kategori_{cid}",
                )

                st.text_input("Nama mata kuliah", value=course["nama"], disabled=True, key=f"course_nama_{cid}")

                if st.button("Simpan perubahan", type="primary", key=f"course_simpan_{cid}"):
                    try:
                        update_course(
                            client,
                            cid,
                            {
                                "kode": e_kode.strip().upper() or None,
                                "semester": int(e_semester),
                                "kategori": e_kategori,
                            },
                        )
                        st.toast("Data mata kuliah diperbarui.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal memperbarui mata kuliah: {exc}")

with tab_modul:
    st.subheader("Arsip Modul")
    st.caption("Simpan tautan modul per mata kuliah. Tautan Google Drive maupun tautan custom didukung; aplikasi hanya menyimpan URL dan membukanya langsung.")

    if not course_names:
        st.warning("Belum ada mata kuliah. Tambahkan mata kuliah terlebih dahulu di tab Mata Kuliah.")
    else:
        with st.form("form_tambah_modul"):
            c1, c2 = st.columns([2, 1])
            modul_judul = c1.text_input("Judul modul", placeholder="Contoh: Modul 3 — ERD")
            modul_urutan = c2.number_input("Nomor modul", min_value=1, max_value=99, value=1, step=1)

            modul_course = st.selectbox(
                "Mata kuliah",
                course_names,
                format_func=lambda name: course_labels.get(name, name),
            )
            modul_url = st.text_input(
                "Link modul",
                placeholder="https://drive.google.com/... atau https://contoh-link...",
            )
            modul_keterangan = st.text_area(
                "Keterangan (opsional)",
                placeholder="Contoh: Materi sebelum praktikum minggu depan.",
            )

            if st.form_submit_button("Tambah Modul", type="primary", use_container_width=True):
                url_bersih = modul_url.strip()
                if not modul_judul.strip():
                    st.error("Judul modul wajib diisi.")
                elif not url_bersih.lower().startswith(("http://", "https://")):
                    st.error("Link modul harus diawali http:// atau https://")
                else:
                    try:
                        course_id = next(
                            course["id"] for course in active_courses if course["nama"] == modul_course
                        )
                        insert_module(
                            client,
                            {
                                "course_id": course_id,
                                "judul": modul_judul.strip(),
                                "urutan": int(modul_urutan),
                                "url": url_bersih,
                                "keterangan": modul_keterangan.strip() or None,
                                "aktif": True,
                            },
                        )
                        st.toast("Modul berhasil ditambahkan.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menambahkan modul: {exc}")

    st.divider()

    visible_modules = [
        module for module in modules
        if module.get("course_id") in {course["id"] for course in active_courses}
    ]

    if not visible_modules:
        st.info("Belum ada modul.")
    else:
        course_by_id = {course["id"]: course for course in courses}
        for module in visible_modules:
            module_id = module["id"]
            course = course_by_id.get(module["course_id"], {})
            order_label = f"Modul {module['urutan']}" if module.get("urutan") is not None else "Materi"
            label = f"{course.get('nama', 'Mata Kuliah tidak ditemukan')} · {order_label} — {module['judul']}"

            with st.expander(label):
                current_course_id = module["course_id"]
                module_course_options = course_names.copy()
                current_course = course_by_id.get(current_course_id)
                if current_course and current_course["nama"] not in module_course_options:
                    module_course_options.append(current_course["nama"])

                current_course_name = current_course["nama"] if current_course else course_names[0]
                e_modul_course = st.selectbox(
                    "Mata kuliah",
                    module_course_options,
                    index=module_course_options.index(current_course_name),
                    format_func=lambda name: course_labels.get(name, name),
                    key=f"module_course_{module_id}",
                )
                e_modul_judul = st.text_input(
                    "Judul modul",
                    value=module["judul"],
                    key=f"module_judul_{module_id}",
                )
                e_modul_urutan = st.number_input(
                    "Nomor modul",
                    min_value=1,
                    max_value=99,
                    value=int(module.get("urutan") or 1),
                    step=1,
                    key=f"module_urutan_{module_id}",
                )
                e_modul_url = st.text_input(
                    "Link modul",
                    value=module["url"],
                    key=f"module_url_{module_id}",
                )
                e_modul_keterangan = st.text_area(
                    "Keterangan",
                    value=module.get("keterangan") or "",
                    key=f"module_keterangan_{module_id}",
                )

                if st.button("Simpan perubahan", type="primary", key=f"module_simpan_{module_id}"):
                    url_bersih = e_modul_url.strip()
                    if not e_modul_judul.strip():
                        st.error("Judul modul wajib diisi.")
                    elif not url_bersih.lower().startswith(("http://", "https://")):
                        st.error("Link modul harus diawali http:// atau https://")
                    else:
                        try:
                            new_course_id = next(
                                course["id"] for course in active_courses if course["nama"] == e_modul_course
                            )
                            update_module(
                                client,
                                module_id,
                                {
                                    "course_id": new_course_id,
                                    "judul": e_modul_judul.strip(),
                                    "urutan": int(e_modul_urutan),
                                    "url": url_bersih,
                                    "keterangan": e_modul_keterangan.strip() or None,
                                },
                            )
                            st.toast("Perubahan modul tersimpan.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Gagal menyimpan modul: {exc}")

                if st.button("Hapus modul", key=f"module_hapus_{module_id}"):
                    try:
                        delete_module(client, module_id)
                        st.toast("Modul terhapus.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menghapus modul: {exc}")

with tab_admin_users:
    is_super_admin = current_email() == ADMIN_EMAIL

    st.subheader("Daftar Email Admin")
    if is_super_admin:
        st.caption("Hanya Super Admin yang dapat menambah atau mencabut akses admin.")
        new_admin_email = st.text_input(
            "Tambah Email Admin Baru",
            placeholder="contoh: teman@gmail.com",
        )
        if st.button("Tambah Admin", type="primary", use_container_width=True):
            email_baru = new_admin_email.strip().lower()
            if not email_baru or "@" not in email_baru:
                st.error("Email tidak valid.")
            else:
                try:
                    client.table("admin_users").insert({"email": email_baru}).execute()
                    st.toast(f"Berhasil menambahkan {email_baru}!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal menambahkan: {exc}")
    else:
        st.info("Daftar admin hanya dapat dikelola oleh Super Admin.")

    st.divider()
    try:
        admins = client.table("admin_users").select("*").execute().data or []
        st.write("**Daftar Admin Aktif:**")

        for a in admins:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"- `{a['email']}`")

            # Tampilkan tombol Hapus HANYA untuk Super Admin dan cegah penghapusan diri sendiri
            if is_super_admin and a["email"] != ADMIN_EMAIL:
                if c2.button("Hapus", key=f"hapus_admin_{a['email']}"):
                    try:
                        client.table("admin_users").delete().eq("email", a["email"]).execute()
                        st.toast(f"Akses admin untuk {a['email']} berhasil dicabut.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menghapus admin: {exc}")

    except Exception as exc:
        st.error(f"Gagal memuat daftar: {exc}")
