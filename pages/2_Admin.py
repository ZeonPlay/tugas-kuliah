from datetime import time as dtime

import streamlit as st
from utils.editor import rich_text_editor, rich_text_to_markdown, reset_rich_text_editor

from utils.auth import current_email, get_authed_client, is_admin, login, logout, signup
from utils.helpers import JENIS, format_deadline, now_wib, parse_deadline, to_utc_iso
from utils.styles import get_tokens, inject_base_css, render_theme_toggle
from utils.presence import render_presence
from utils.supabase_client import (
    ADMIN_EMAIL,
    delete_task,
    fetch_courses,
    fetch_module_folders,
    fetch_tasks,
    insert_course,
    insert_module_folder,
    insert_task,
    update_course,
    update_module_folder,
    update_task,
    delete_module_folder,
    upload_file,
)

st.set_page_config(
    page_title="Admin Tugas Kuliah",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
mode = render_theme_toggle()
inject_base_css(mode)
tokens = get_tokens(mode)
render_presence("Panel Admin")

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
            submit = st.form_submit_button("Masuk", type="primary", width="stretch")
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
            reg_submit = st.form_submit_button("Daftar Akun", type="primary", width="stretch")
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
    if st.button("Keluar", width="stretch"):
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
    modules = fetch_module_folders(only_active=False)
except Exception as exc:
    st.error(f"Gagal mengambil data: {exc}")
    st.stop()

active_courses = [course for course in courses if course.get("aktif", True)]
course_names = [course["nama"] for course in active_courses]

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
                if kunci in (t.get("judul") or "").lower()
                or kunci in (t.get("ketentuan") or "").lower()
            ]

        st.caption(f"Menampilkan {len(hasil)} dari {len(tasks)} tugas.")

        if not hasil:
            st.info("Tidak ada tugas yang cocok dengan filter.")
        else:

            # Kelompokkan tugas secara dinamis dan pertahankan urutan katalog.
            grouped_tasks = {}
            for task in hasil:
                course_name = task.get("mata_kuliah") or "Tanpa Mata Kuliah"
                grouped_tasks.setdefault(course_name, []).append(task)

            group_order = course_names + [
                name for name in legacy_courses if name not in course_names
            ]
            group_order = [
                name for name in group_order
                if name in grouped_tasks
            ]
            selected_id = st.session_state.get("admin_selected_task_id")

            st.divider()
            st.subheader("Daftar Tugas")

            for course_name in group_order:
                course_tasks = grouped_tasks[course_name]
                course_task_ids = {task["id"] for task in course_tasks}
                is_selected_course = selected_id in course_task_ids
                with st.expander(
                    f"📚 {course_name}  ·  {len(course_tasks)} tugas",
                    expanded=is_selected_course,
                ):
                    for task in sorted(course_tasks, key=lambda item: item.get("deadline") or ""):
                        tid = task["id"]
                        c1, c2 = st.columns([6, 1])

                        c1.markdown(f"**{task['judul']}**")
                        c1.caption(
                            f"{task.get('jenis', 'Teori')} · Deadline {format_deadline(task['deadline'])}"
                        )
                        if c2.button(
                            "Edit",
                            key=f"pilih_edit_{tid}",
                            type="primary" if selected_id == tid else "secondary",
                            width="stretch",
                        ):
                            st.session_state["admin_selected_task_id"] = tid
                            st.rerun()

            selected_task = next(
                (task for task in hasil if task["id"] == st.session_state.get("admin_selected_task_id")),
                None,
            )

            if selected_task is not None:
                tid = selected_task["id"]
                st.divider()
                st.subheader(f"Edit Tugas: {selected_task['judul']}")

                dt_lokal = parse_deadline(selected_task["deadline"])
                e_judul = st.text_input(
                    "Judul",
                    value=selected_task["judul"],
                    key=f"edit_judul_{tid}",
                )

                c1, c2 = st.columns(2)
                matkul_saat_ini = selected_task.get("mata_kuliah")
                opsi_matkul = course_names.copy()
                if matkul_saat_ini and matkul_saat_ini not in opsi_matkul:
                    opsi_matkul.append(matkul_saat_ini)

                e_matkul = c1.selectbox(
                    "Mata kuliah",
                    opsi_matkul,
                    index=opsi_matkul.index(matkul_saat_ini) if matkul_saat_ini in opsi_matkul else 0,
                    key=f"edit_matkul_{tid}",
                )
                e_jenis = c2.selectbox(
                    "Jenis",
                    JENIS,
                    index=JENIS.index(selected_task.get("jenis", "Teori")),
                    key=f"edit_jenis_{tid}",
                )

                c3, c4 = st.columns(2)
                e_tgl = c3.date_input(
                    "Tanggal deadline",
                    value=dt_lokal.date(),
                    key=f"edit_tgl_{tid}",
                )
                e_jam = c4.time_input(
                    "Jam deadline (WIB)",
                    value=dt_lokal.time(),
                    key=f"edit_jam_{tid}",
                )

                st.write("**Ketentuan**")
                with st.container(border=True):
                    editor_key = f"edit_ketentuan_{tid}"
                    e_ketentuan_raw = rich_text_editor(
                        value=rich_text_to_markdown(selected_task.get("ketentuan")),
                        placeholder="Tulis ketentuan tugas di sini...",
                        key=editor_key,
                    )

                e_link = st.text_input(
                    "Link VClass",
                    value=selected_task.get("link_vclass") or "",
                    key=f"edit_link_{tid}",
                )

                if selected_task.get("file_soal"):
                    st.markdown(
                        f'<a href="{selected_task["file_soal"]}" target="_blank">Lihat file saat ini</a>',
                        unsafe_allow_html=True,
                    )

                e_file = st.file_uploader(
                    "Ganti File Soal/Ketentuan",
                    type=["pdf", "png", "jpg", "jpeg", "docx", "zip"],
                    key=f"edit_file_{tid}",
                )

                c_simpan, c_batal = st.columns(2)

                if c_simpan.button(
                    "Simpan Perubahan",
                    type="primary",
                    key=f"edit_simpan_{tid}",
                    width="stretch",
                ):
                    link_bersih = e_link.strip()
                    if link_bersih and not link_bersih.lower().startswith(("http://", "https://")):
                        st.error("Link VClass harus valid.")
                    else:
                        try:
                            file_url = upload_file(client, e_file) if e_file else selected_task.get("file_soal")
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
                                old_file_url=selected_task.get("file_soal") if e_file else None,
                            )
                            reset_rich_text_editor(editor_key)
                            st.session_state.pop("admin_selected_task_id", None)
                            st.toast("Perubahan tersimpan.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Gagal menyimpan: {exc}")

                if c_batal.button(
                    "Tutup Editor",
                    key=f"edit_batal_{tid}",
                    width="stretch",
                ):
                    reset_rich_text_editor(editor_key)
                    st.session_state.pop("admin_selected_task_id", None)
                    st.rerun()

                st.divider()
                konfirmasi = st.checkbox(
                    "Saya yakin ingin menghapus tugas ini",
                    key=f"konfirmasi_{tid}",
                )
                if st.button(
                    "Hapus Tugas (Permanen)",
                    key=f"hapus_{tid}",
                    disabled=not konfirmasi,
                    width="stretch",
                ):
                    try:
                        delete_task(client, tid)
                        st.session_state.pop("admin_selected_task_id", None)
                        st.toast("Tugas terhapus.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menghapus: {exc}")

with tab_kuliah:
    st.subheader("Katalog Mata Kuliah")
    st.caption("Daftar ini menjadi sumber mata kuliah untuk tugas. Semester dan kategori bisa diperbarui tanpa mengubah tugas lama.")

    with st.form("form_tambah_mata_kuliah"):
        c1, c2 = st.columns(2)
        kode_baru = c1.text_input("Kode mata kuliah", placeholder="Contoh: SI401")
        nama_baru = c2.text_input("Nama mata kuliah", placeholder="Contoh: Data Mining")

        c3, c4 = st.columns(2)
        semester_baru = c3.number_input("Semester", min_value=1, max_value=8, value=4, step=1)
        kategori_baru = c4.selectbox("Kategori", ["Wajib", "Pilihan", "Belum dikategorikan"])

        if st.form_submit_button("Tambah Mata Kuliah", type="primary", width="stretch"):
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
        courses_by_semester = {}
        for course in courses:
            semester = int(course.get("semester") or 0)
            courses_by_semester.setdefault(semester, []).append(course)

        for semester in sorted(courses_by_semester):
            semester_courses = courses_by_semester[semester]
            with st.expander(
                f"Semester {semester} · {len(semester_courses)} mata kuliah",
                expanded=len(courses_by_semester) == 1,
            ):
                for course in semester_courses:
                    cid = course["id"]
                    code = (course.get("kode") or "").strip()
                    status_label = "" if course.get("aktif", True) else " · Nonaktif"
                    label = f"{code} · {course['nama']}{status_label}" if code else f"{course['nama']}{status_label}"
                    with st.expander(label):
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
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
                        e_aktif = c4.checkbox(
                            "Aktif",
                            value=bool(course.get("aktif", True)),
                            key=f"course_aktif_{cid}",
                        )

                        st.text_input("Nama mata kuliah", value=course["nama"], disabled=True, key=f"course_nama_{cid}")

                        if st.button("Simpan perubahan", type="primary", key=f"course_simpan_{cid}", width="stretch"):
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
    st.caption("Simpan tautan folder modul per mata kuliah. Folder Google Drive maupun folder dari tautan custom didukung; aplikasi hanya menyimpan URL dan membukanya langsung.")

    if not course_names:
        st.warning("Belum ada mata kuliah. Tambahkan mata kuliah terlebih dahulu di tab Mata Kuliah.")
    else:
        with st.form("form_tambah_module_folder"):
            modul_course = st.selectbox(
                "Mata kuliah",
                course_names,
            )
            modul_url = st.text_input(
                "Link folder",
                placeholder="https://drive.google.com/... atau https://contoh-link...",
            )
            modul_keterangan = st.text_area(
                "Keterangan (opsional)",
                placeholder="Contoh: Berisi PDF modul dan materi praktikum.",
            )

            if st.form_submit_button("Tambah Folder", type="primary", width="stretch"):
                url_bersih = modul_url.strip()
                if not url_bersih.lower().startswith(("http://", "https://")):
                    st.error("Link folder harus diawali http:// atau https://")
                else:
                    try:
                        course_id = next(
                            course["id"] for course in active_courses if course["nama"] == modul_course
                        )
                        insert_module_folder(
                            client,
                            {
                                "course_id": course_id,
                                "url": url_bersih,
                                "keterangan": modul_keterangan.strip() or None,
                                "aktif": True,
                            },
                        )
                        st.toast("Folder arsip berhasil ditambahkan.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menambahkan folder: {exc}")

    st.divider()

    visible_folders = [
        module for module in modules
        if module.get("course_id") in {course["id"] for course in active_courses}
    ]

    if not visible_folders:
        st.info("Belum ada modul.")
    else:
        course_by_id = {course["id"]: course for course in courses}
        grouped_modules = {}
        for module in visible_folders:
            course = course_by_id.get(module["course_id"], {})
            course_name = course.get("nama", "Mata Kuliah tidak ditemukan")
            grouped_modules.setdefault(course_name, []).append(module)

        for course_name in [course["nama"] for course in active_courses if course["nama"] in grouped_modules]:
            course_modules = grouped_modules[course_name]
            with st.expander(
                f"📚 {course_name} · {len(course_modules)} folder",
                expanded=len(grouped_modules) == 1,
            ):
                for module in course_modules:
                    module_id = module["id"]
                    with st.container(border=True):
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
                            key=f"module_course_{module_id}",
                        )
                        e_modul_url = st.text_input(
                            "Link folder",
                            value=module["url"],
                            key=f"module_url_{module_id}",
                        )
                        e_modul_keterangan = st.text_area(
                            "Keterangan",
                            value=module.get("keterangan") or "",
                            key=f"module_keterangan_{module_id}",
                        )
                        e_modul_aktif = st.checkbox(
                            "Aktif",
                            value=bool(module.get("aktif", True)),
                            key=f"module_aktif_{module_id}",
                        )

                        c_simpan, c_hapus = st.columns(2)
                        if c_simpan.button(
                            "Simpan perubahan",
                            type="primary",
                            key=f"module_simpan_{module_id}",
                            width="stretch",
                        ):
                            url_bersih = e_modul_url.strip()
                            if not url_bersih.lower().startswith(("http://", "https://")):
                                st.error("Link folder harus diawali http:// atau https://")
                            else:
                                try:
                                    new_course_id = next(
                                        course["id"] for course in active_courses if course["nama"] == e_modul_course
                                    )
                                    update_module_folder(
                                        client,
                                        module_id,
                                        {
                                            "course_id": new_course_id,
                                            "url": url_bersih,
                                            "keterangan": e_modul_keterangan.strip() or None,
                                            "aktif": e_modul_aktif,
                                        },
                                    )
                                    st.toast("Perubahan folder tersimpan.")
                                    st.rerun()
                                except Exception as exc:
                                    st.error(f"Gagal menyimpan folder: {exc}")

                        if c_hapus.button(
                            "Hapus folder",
                            key=f"module_hapus_{module_id}",
                            width="stretch",
                        ):
                            try:
                                delete_module_folder(client, module_id)
                                st.toast("Folder arsip terhapus.")
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
        if st.button("Tambah Admin", type="primary", width="stretch"):
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
