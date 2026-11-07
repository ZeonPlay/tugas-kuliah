import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { supabase } from "../lib/supabase";

type Course = { id: string; kode: string | null; nama: string; semester: number; kategori: string; aktif: boolean };
type ModuleFolder = { id: string; course_id: string; url: string; keterangan: string | null; aktif: boolean; created_at: string };
type StatusFilter = "all" | "active" | "inactive";

function safeHttpUrl(value: string): string | null {
  try {
    const url = new URL(value.trim());
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

function explainError(message: string): string {
  if (/row-level security|permission denied|not allowed/i.test(message)) {
    return "Supabase menolak perubahan ini. Pastikan sesi admin dan policy Row Level Security sudah benar.";
  }
  if (/foreign key/i.test(message)) {
    return "Mata kuliah yang dipilih sudah tidak tersedia. Muat ulang katalog, lalu pilih mata kuliah lain.";
  }
  return message;
}

export default function ModuleManager({ onDataChanged }: { onDataChanged: () => void }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [folders, setFolders] = useState<ModuleFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [search, setSearch] = useState("");
  const [courseFilter, setCourseFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ModuleFolder | null>(null);
  const [deleteError, setDeleteError] = useState("");

  async function loadData() {
    if (!supabase) {
      setCourses([]);
      setFolders([]);
      setLoadError("Supabase belum dikonfigurasi.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setLoadError("");
    const [courseResult, folderResult] = await Promise.all([
      supabase.from("courses").select("id,kode,nama,semester,kategori,aktif").order("semester", { ascending: true }).order("nama", { ascending: true }),
      supabase.from("module_folders").select("id,course_id,url,keterangan,aktif,created_at").order("created_at", { ascending: true }).order("url", { ascending: true }),
    ]);
    const errors = [
      courseResult.error ? "Mata kuliah: " + explainError(courseResult.error.message) : "",
      folderResult.error ? "Folder arsip: " + explainError(folderResult.error.message) : "",
    ].filter(Boolean);
    if (errors.length) {
      setLoadError(errors.join(" "));
      if (courseResult.error) setCourses([]);
      else setCourses((courseResult.data ?? []) as Course[]);
      if (folderResult.error) setFolders([]);
      else setFolders((folderResult.data ?? []) as ModuleFolder[]);
    } else {
      setCourses((courseResult.data ?? []) as Course[]);
      setFolders((folderResult.data ?? []) as ModuleFolder[]);
    }
    setLoading(false);
  }

  useEffect(() => {
    let alive = true;
    async function initialLoad() {
      if (!supabase) {
        setLoadError("Supabase belum dikonfigurasi.");
        setLoading(false);
        return;
      }
      const [courseResult, folderResult] = await Promise.all([
        supabase.from("courses").select("id,nama,semester,kategori,aktif").order("semester", { ascending: true }).order("nama", { ascending: true }),
        supabase.from("module_folders").select("id,course_id,url,keterangan,aktif,created_at").order("created_at", { ascending: true }).order("url", { ascending: true }),
      ]);
      if (!alive) return;
      const errors = [
        courseResult.error ? "Mata kuliah: " + explainError(courseResult.error.message) : "",
        folderResult.error ? "Folder arsip: " + explainError(folderResult.error.message) : "",
      ].filter(Boolean);
      setLoadError(errors.join(" "));
      setCourses((courseResult.data ?? []) as Course[]);
      setFolders((folderResult.data ?? []) as ModuleFolder[]);
      setLoading(false);
    }
    void initialLoad();
    return () => { alive = false; };
  }, []);

  const activeCourses = useMemo(() => courses.filter((course) => course.aktif), [courses]);
  const courseById = useMemo(() => new Map(courses.map((course) => [course.id, course])), [courses]);
  const visibleFolders = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase("id-ID");
    return folders.filter((folder) => {
      const course = courseById.get(folder.course_id);
      const matchesSearch = !keyword || [folder.keterangan ?? "", folder.url, course?.nama ?? "", course?.kode ?? ""]
        .some((value) => value.toLocaleLowerCase("id-ID").includes(keyword));
      const matchesCourse = courseFilter === "all" || folder.course_id === courseFilter;
      const matchesStatus = statusFilter === "all" || (statusFilter === "active" ? folder.aktif : !folder.aktif);
      return matchesSearch && matchesCourse && matchesStatus;
    });
  }, [folders, courseById, search, courseFilter, statusFilter]);

  const groupedFolders = useMemo(() => {
    const groups = new Map<string, { course: Course | null; folders: ModuleFolder[] }>();
    for (const folder of visibleFolders) {
      const course = courseById.get(folder.course_id) ?? null;
      const key = course?.id ?? "missing-course";
      const existing = groups.get(key) ?? { course, folders: [] };
      existing.folders.push(folder);
      groups.set(key, existing);
    }
    return [...groups.entries()].sort((a, b) => {
      const courseA = a[1].course;
      const courseB = b[1].course;
      return (courseA?.semester ?? 99) - (courseB?.semester ?? 99) ||
        (courseA?.nama ?? "Mata kuliah tidak ditemukan").localeCompare(courseB?.nama ?? "Mata kuliah tidak ditemukan", "id-ID");
    });
  }, [visibleFolders, courseById]);

  async function createFolder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const courseId = String(form.get("course_id") ?? "");
    const rawUrl = String(form.get("url") ?? "").trim();
    const keterangan = String(form.get("keterangan") ?? "").trim();
    const url = safeHttpUrl(rawUrl);
    setSaveError("");
    if (!activeCourses.some((course) => course.id === courseId)) {
      setSaveError("Pilih mata kuliah yang masih aktif.");
      return;
    }
    if (!url) {
      setSaveError("Link folder harus berupa URL http:// atau https:// yang valid.");
      return;
    }
    setBusyId("new");
    const { error } = await supabase.from("module_folders").insert({ course_id: courseId, url, keterangan: keterangan || null, aktif: true });
    if (error) {
      setSaveError("Folder belum berhasil ditambahkan. " + explainError(error.message));
      setBusyId(null);
      return;
    }
    formElement.reset();
    await loadData();
    setBusyId(null);
    onDataChanged();
  }

  async function updateFolder(event: FormEvent<HTMLFormElement>, folder: ModuleFolder) {
    event.preventDefault();
    if (!supabase) return;
    const form = new FormData(event.currentTarget);
    const courseId = String(form.get("course_id") ?? "");
    const rawUrl = String(form.get("url") ?? "").trim();
    const keterangan = String(form.get("keterangan") ?? "").trim();
    const aktif = form.get("aktif") === "on";
    const url = safeHttpUrl(rawUrl);
    setSaveError("");
    if (!url) {
      setSaveError("Link folder harus berupa URL http:// atau https:// yang valid.");
      return;
    }
    if (!courseById.has(courseId)) {
      setSaveError("Mata kuliah tidak ditemukan. Muat ulang data dan coba kembali.");
      return;
    }
    setBusyId(folder.id);
    const { error } = await supabase.from("module_folders").update({
      course_id: courseId,
      url,
      keterangan: keterangan || null,
      aktif,
    }).eq("id", folder.id);
    if (error) {
      setSaveError("Perubahan folder belum tersimpan. " + explainError(error.message));
      setBusyId(null);
      return;
    }
    await loadData();
    setBusyId(null);
    onDataChanged();
  }

  async function removeFolder() {
    if (!supabase || !deleteTarget) return;
    setDeleteError("");
    setBusyId(deleteTarget.id);
    const { error } = await supabase.from("module_folders").delete().eq("id", deleteTarget.id);
    if (error) {
      setDeleteError("Folder belum berhasil dihapus. " + explainError(error.message));
      setBusyId(null);
      return;
    }
    setDeleteTarget(null);
    await loadData();
    setBusyId(null);
    onDataChanged();
  }

  return (
    <section className="module-manager" aria-labelledby="module-manager-title">
      <div className="module-manager-heading">
        <div>
          <p className="admin-eyebrow">MATERI PERKULIAHAN</p>
          <h1 id="module-manager-title">Arsip Modul</h1>
          <p className="admin-section-description">Kelola tautan folder materi per mata kuliah. Menonaktifkan folder menyembunyikannya dari halaman mahasiswa tanpa menghapus tautannya.</p>
        </div>
        <div className="module-manager-stat"><strong>{loading ? "—" : folders.length}</strong><span>folder total</span></div>
      </div>

      {saveError && <div className="notice notice-error" role="alert"><span>{saveError}</span></div>}
      {loadError && <div className="notice notice-error" role="alert"><strong>Arsip modul belum berhasil dimuat sepenuhnya.</strong><span>{loadError}</span><button className="text-button" type="button" onClick={() => void loadData()}>Coba lagi</button></div>}

      <details className="course-create-disclosure module-create-disclosure">
        <summary><span aria-hidden="true">＋</span><span>Tambah folder arsip</span></summary>
        {activeCourses.length === 0 ? <p className="module-no-courses">Aktifkan setidaknya satu mata kuliah sebelum menambahkan folder.</p> : (
          <form className="course-create-form" onSubmit={(event) => void createFolder(event)}>
            <div className="module-create-grid">
              <label className="form-field admin-field"><span>Mata kuliah <b aria-hidden="true">*</b></span><select name="course_id" defaultValue={activeCourses[0].id} required>{activeCourses.map((course) => <option key={course.id} value={course.id}>{course.nama}</option>)}</select></label>
              <label className="form-field admin-field"><span>Link folder <b aria-hidden="true">*</b></span><input name="url" type="url" required maxLength={2048} placeholder="https://drive.google.com/…" /></label>
            </div>
            <label className="form-field admin-field"><span>Keterangan (opsional)</span><textarea name="keterangan" rows={3} maxLength={500} placeholder="Contoh: PDF modul dan materi praktikum." /></label>
            <p className="course-form-note">Hanya tautan http dan https yang diterima. Folder baru langsung aktif.</p>
            <button className="primary-action" type="submit" disabled={busyId !== null}>{busyId === "new" ? "Menyimpan…" : "Simpan folder"}</button>
          </form>
        )}
      </details>

      <div className="module-manager-tools">
        <label className="task-search-input"><span className="task-search-icon" aria-hidden="true">⌕</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari keterangan, URL, atau mata kuliah…" aria-label="Cari folder arsip" />{search && <button className="task-search-clear" type="button" onClick={() => setSearch("")}>Hapus</button>}</label>
        <label className="course-status-select"><span>Status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}><option value="all">Semua</option><option value="active">Aktif saja</option><option value="inactive">Nonaktif saja</option></select></label>
        <label className="course-status-select module-course-filter"><span>Kuliah</span><select value={courseFilter} onChange={(event) => setCourseFilter(event.target.value)}><option value="all">Semua mata kuliah</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.nama}</option>)}</select></label>
      </div>
      <p className="course-manager-count">{loading ? "Memuat folder…" : visibleFolders.length + " dari " + folders.length + " folder"}</p>

      {loading ? <div className="archive-empty" role="status"><span className="loading-mark" /><strong>Memuat folder arsip…</strong></div>
      : groupedFolders.length === 0 ? <div className="course-manager-empty"><strong>{folders.length === 0 ? "Belum ada folder arsip." : "Folder tidak ditemukan."}</strong><span>{folders.length === 0 ? "Tambahkan folder pertama melalui formulir di atas." : "Coba kata kunci lain atau ubah filter."}</span></div>
      : <div className="module-manager-list">
        {groupedFolders.map(([key, group]) => (
          <details className="course-semester-group module-course-group" key={key} open={groupedFolders.length === 1}>
            <summary><span>{group.course?.nama ?? "Mata kuliah tidak ditemukan"}</span><span className="course-semester-count">{group.folders.length} folder{group.course && !group.course.aktif ? " · Mata kuliah nonaktif" : ""}</span></summary>
            <div className="module-manager-rows">
              {group.folders.map((folder) => (
                <details className={"course-edit-row module-edit-row" + (!folder.aktif ? " is-inactive" : "")} key={folder.id}>
                  <summary>
                    <span className="course-edit-summary-copy"><strong>{folder.keterangan?.trim() || "Folder tanpa keterangan"}</strong><small>{folder.aktif ? "Aktif" : "Nonaktif"} · {folder.url}</small></span>
                    <span className="course-edit-chevron" aria-hidden="true">›</span>
                  </summary>
                  <form className="module-edit-form" onSubmit={(event) => void updateFolder(event, folder)}>
                    <label className="form-field admin-field"><span>Mata kuliah</span><select name="course_id" defaultValue={folder.course_id} required>{courses.map((course) => <option key={course.id} value={course.id} disabled={!course.aktif && course.id !== folder.course_id}>{course.nama}{!course.aktif ? " (nonaktif)" : ""}</option>)}</select></label>
                    <label className="form-field admin-field"><span>Link folder <b aria-hidden="true">*</b></span><input name="url" type="url" defaultValue={folder.url} required maxLength={2048} /></label>
                    <label className="form-field admin-field"><span>Keterangan (opsional)</span><textarea name="keterangan" defaultValue={folder.keterangan ?? ""} rows={3} maxLength={500} placeholder="Tambahkan konteks singkat untuk mahasiswa." /></label>
                    <label className="course-active-control"><input type="checkbox" name="aktif" defaultChecked={folder.aktif} /><span><strong>Folder aktif</strong><small>Jika nonaktif, folder tidak terlihat di halaman Arsip Modul.</small></span></label>
                    <div className="course-edit-actions"><button className="primary-action" type="submit" disabled={busyId !== null}>{busyId === folder.id ? "Menyimpan…" : "Simpan perubahan"}</button><button className="danger-action" type="button" onClick={() => { setDeleteTarget(folder); setDeleteError(""); }} disabled={busyId !== null}>Hapus folder</button><a className="quiet-button module-preview-link" href={folder.url} target="_blank" rel="noopener noreferrer">Uji tautan ↗</a></div>
                  </form>
                </details>
              ))}
            </div>
          </details>
        ))}
      </div>}

      {deleteTarget && (
        <div className="delete-dialog-backdrop">
          <section className="delete-dialog" role="alertdialog" aria-modal="true" aria-labelledby="delete-folder-title" aria-describedby="delete-folder-description">
            <p className="admin-eyebrow">KONFIRMASI PENGHAPUSAN</p>
            <h2 id="delete-folder-title">Hapus folder arsip?</h2>
            <p id="delete-folder-description"><strong>{deleteTarget.keterangan || deleteTarget.url}</strong> akan dihapus dari arsip. Tindakan ini tidak dapat dibatalkan.</p>
            {deleteError && <p className="delete-dialog-error" role="alert">{deleteError}</p>}
            <div className="delete-dialog-actions"><button className="danger-action" type="button" onClick={() => void removeFolder()} disabled={busyId !== null}>{busyId === deleteTarget.id ? "Menghapus…" : "Ya, hapus folder"}</button><button className="quiet-button" type="button" onClick={() => setDeleteTarget(null)} disabled={busyId !== null}>Batal</button></div>
          </section>
        </div>
      )}
    </section>
  );
}
