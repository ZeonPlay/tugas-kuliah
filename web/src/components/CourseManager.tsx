import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { supabase } from "../lib/supabase";

type Course = {
  id: string;
  kode: string | null;
  nama: string;
  semester: number;
  kategori: "Wajib" | "Pilihan" | "Belum dikategorikan";
  aktif: boolean;
};
type StatusFilter = "all" | "active" | "inactive";

const CATEGORIES = ["Wajib", "Pilihan", "Belum dikategorikan"] as const;

function explainError(message: string): string {
  if (/duplicate key|unique constraint|courses_nama_key/i.test(message)) {
    return "Nama atau kode mata kuliah sudah digunakan. Periksa kembali data yang diisi.";
  }
  if (/row-level security|permission denied|not allowed/i.test(message)) {
    return "Supabase menolak perubahan ini. Pastikan sesi admin dan policy Row Level Security sudah benar.";
  }
  return message;
}

export default function CourseManager({ onDataChanged }: { onDataChanged: () => void }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [busyId, setBusyId] = useState<string | null>(null);

  async function loadCourses() {
    if (!supabase) {
      setCourses([]);
      setLoadError("Supabase belum dikonfigurasi.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setLoadError("");
    const { data, error } = await supabase
      .from("courses")
      .select("id,kode,nama,semester,kategori,aktif")
      .order("semester", { ascending: true })
      .order("nama", { ascending: true });
    if (error) {
      setLoadError(explainError(error.message));
      setCourses([]);
    } else {
      setCourses((data ?? []) as Course[]);
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
      const { data, error } = await supabase
        .from("courses")
        .select("id,kode,nama,semester,kategori,aktif")
        .order("semester", { ascending: true })
        .order("nama", { ascending: true });
      if (!alive) return;
      if (error) {
        setLoadError(explainError(error.message));
        setCourses([]);
      } else {
        setCourses((data ?? []) as Course[]);
      }
      setLoading(false);
    }
    void initialLoad();
    return () => { alive = false; };
  }, []);

  const visibleCourses = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase("id-ID");
    return courses.filter((course) => {
      const matchesSearch = !keyword || [course.nama, course.kode ?? "", course.kategori, String(course.semester)]
        .some((value) => value.toLocaleLowerCase("id-ID").includes(keyword));
      const matchesStatus = statusFilter === "all" ||
        (statusFilter === "active" ? course.aktif : !course.aktif);
      return matchesSearch && matchesStatus;
    });
  }, [courses, search, statusFilter]);

  const groupedCourses = useMemo(() => {
    const groups = new Map<number, Course[]>();
    for (const course of visibleCourses) {
      const group = groups.get(course.semester) ?? [];
      group.push(course);
      groups.set(course.semester, group);
    }
    return [...groups.entries()].sort(([a], [b]) => a - b);
  }, [visibleCourses]);

  async function createCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase) return;
    setSaveError("");
    setBusyId("new");
    const form = new FormData(event.currentTarget);
    const nama = String(form.get("nama") ?? "").trim();
    const kode = String(form.get("kode") ?? "").trim().toLocaleUpperCase("id-ID");
    const semester = Number(form.get("semester"));
    const kategori = String(form.get("kategori") ?? "Belum dikategorikan");
    if (!nama) {
      setSaveError("Nama mata kuliah wajib diisi.");
      setBusyId(null);
      return;
    }
    if (!Number.isInteger(semester) || semester < 1 || semester > 8) {
      setSaveError("Semester harus berupa angka 1 sampai 8.");
      setBusyId(null);
      return;
    }
    const { error } = await supabase.from("courses").insert({
      kode: kode || null,
      nama,
      semester,
      kategori,
      aktif: true,
    });
    if (error) {
      setSaveError("Mata kuliah belum berhasil ditambahkan. " + explainError(error.message));
      setBusyId(null);
      return;
    }
    event.currentTarget.reset();
    await loadCourses();
    setBusyId(null);
    onDataChanged();
  }

  async function updateCourse(event: FormEvent<HTMLFormElement>, course: Course) {
    event.preventDefault();
    if (!supabase) return;
    setSaveError("");
    setBusyId(course.id);
    const form = new FormData(event.currentTarget);
    const kode = String(form.get("kode") ?? "").trim().toLocaleUpperCase("id-ID");
    const semester = Number(form.get("semester"));
    const kategori = String(form.get("kategori") ?? "Belum dikategorikan");
    const aktif = form.get("aktif") === "on";
    if (!Number.isInteger(semester) || semester < 1 || semester > 8) {
      setSaveError("Semester harus berupa angka 1 sampai 8.");
      setBusyId(null);
      return;
    }
    const { error } = await supabase.from("courses").update({
      kode: kode || null,
      semester,
      kategori,
      aktif,
    }).eq("id", course.id);
    if (error) {
      setSaveError("Perubahan untuk " + course.nama + " belum tersimpan. " + explainError(error.message));
      setBusyId(null);
      return;
    }
    await loadCourses();
    setBusyId(null);
    onDataChanged();
  }

  return (
    <section className="course-manager" aria-labelledby="course-manager-title">
      <div className="course-manager-heading">
        <div>
          <p className="admin-eyebrow">KATALOG AKADEMIK</p>
          <h1 id="course-manager-title">Mata kuliah</h1>
          <p className="admin-section-description">Kelola katalog untuk tugas dan arsip modul. Mata kuliah yang tidak dipakai lagi sebaiknya dinonaktifkan, bukan dihapus.</p>
        </div>
        <div className="course-manager-stat"><strong>{loading ? "—" : courses.length}</strong><span>terdaftar</span></div>
      </div>

      {saveError && <div className="notice notice-error" role="alert"><span>{saveError}</span></div>}
      {loadError && <div className="notice notice-error" role="alert"><strong>Katalog belum berhasil dimuat.</strong><span>{loadError}</span><button className="text-button" type="button" onClick={() => void loadCourses()}>Coba lagi</button></div>}

      <details className="course-create-disclosure">
        <summary><span aria-hidden="true">＋</span><span>Tambah mata kuliah</span></summary>
        <form className="course-create-form" onSubmit={(event) => void createCourse(event)}>
          <div className="course-form-grid">
            <label className="admin-field course-name-field"><span>Nama mata kuliah <b aria-hidden="true">*</b></span><input name="nama" required maxLength={120} placeholder="Contoh: Data Mining" /></label>
            <label className="admin-field"><span>Kode (opsional)</span><input name="kode" maxLength={24} placeholder="Contoh: SI401" /></label>
            <label className="admin-field"><span>Semester</span><select name="semester" defaultValue="4">{Array.from({ length: 8 }, (_, index) => index + 1).map((semester) => <option key={semester} value={semester}>{semester}</option>)}</select></label>
            <label className="admin-field"><span>Kategori</span><select name="kategori" defaultValue="Wajib">{CATEGORIES.map((category) => <option key={category}>{category}</option>)}</select></label>
          </div>
          <p className="course-form-note">Nama harus unik. Setelah ditambahkan, mata kuliah langsung aktif dan bisa dipilih saat membuat tugas.</p>
          <button className="primary-action" type="submit" disabled={busyId !== null}>{busyId === "new" ? "Menyimpan…" : "Simpan mata kuliah"}</button>
        </form>
      </details>

      <div className="course-manager-tools">
        <label className="task-search-input">
          <span className="task-search-icon" aria-hidden="true">⌕</span>
          <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari nama, kode, semester…" aria-label="Cari mata kuliah" />
          {search && <button className="task-search-clear" type="button" onClick={() => setSearch("")}>Hapus</button>}
        </label>
        <label className="course-status-select"><span>Status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}><option value="all">Semua</option><option value="active">Aktif saja</option><option value="inactive">Nonaktif saja</option></select></label>
      </div>

      <p className="course-manager-count">{loading ? "Memuat katalog…" : visibleCourses.length + " dari " + courses.length + " mata kuliah"}</p>

      {loading ? <div className="archive-empty" role="status"><span className="loading-mark" /><strong>Memuat katalog mata kuliah…</strong></div>
      : groupedCourses.length === 0 ? <div className="course-manager-empty"><strong>{courses.length === 0 ? "Belum ada mata kuliah." : "Mata kuliah tidak ditemukan."}</strong><span>{courses.length === 0 ? "Tambahkan katalog pertama melalui formulir di atas." : "Coba kata kunci lain atau ubah filter status."}</span></div>
      : <div className="course-manager-list">
        {groupedCourses.map(([semester, semesterCourses]) => (
          <details className="course-semester-group" key={semester} open={groupedCourses.length === 1}>
            <summary><span>Semester {semester}</span><span className="course-semester-count">{semesterCourses.length} mata kuliah</span></summary>
            <div className="course-semester-items">
              {semesterCourses.map((course) => (
                <details className={"course-edit-row" + (!course.aktif ? " is-inactive" : "")} key={course.id}>
                  <summary>
                    <span className="course-edit-summary-copy">
                      <strong>{course.kode ? course.kode + " · " : ""}{course.nama}</strong>
                      <small>{course.kategori}{!course.aktif ? " · Nonaktif" : " · Aktif"}</small>
                    </span>
                    <span className="course-edit-chevron" aria-hidden="true">›</span>
                  </summary>
                  <form className="course-edit-form" onSubmit={(event) => void updateCourse(event, course)}>
                    <label className="admin-field"><span>Nama mata kuliah</span><input value={course.nama} readOnly disabled /></label>
                    <div className="course-form-grid course-edit-grid">
                      <label className="admin-field"><span>Kode (opsional)</span><input name="kode" maxLength={24} defaultValue={course.kode ?? ""} placeholder="Contoh: SI401" /></label>
                      <label className="admin-field"><span>Semester</span><select name="semester" defaultValue={String(course.semester)}>{Array.from({ length: 8 }, (_, index) => index + 1).map((number) => <option value={number} key={number}>{number}</option>)}</select></label>
                      <label className="admin-field"><span>Kategori</span><select name="kategori" defaultValue={course.kategori}>{CATEGORIES.map((category) => <option key={category}>{category}</option>)}</select></label>
                      <label className="course-active-control"><input type="checkbox" name="aktif" defaultChecked={course.aktif} /><span><strong>Aktif</strong><small>Nonaktifkan jika tidak digunakan lagi.</small></span></label>
                    </div>
                    <div className="course-edit-actions"><button className="primary-action" type="submit" disabled={busyId !== null}>{busyId === course.id ? "Menyimpan…" : "Simpan perubahan"}</button><button className="quiet-button" type="button" onClick={() => void loadCourses()} disabled={busyId !== null}>Muat ulang</button></div>
                  </form>
                </details>
              ))}
            </div>
          </details>
        ))}
      </div>}
    </section>
  );
}
