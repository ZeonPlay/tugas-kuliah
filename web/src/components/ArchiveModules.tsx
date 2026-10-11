import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { supabase } from "../lib/supabase";

type Course = { id: string; nama: string; semester: number; kategori: string; aktif: boolean };
type ModuleFolder = { id: string; course_id: string; url: string; keterangan: string | null; aktif: boolean; created_at: string };

type Props = { courses: Course[]; onBack: () => void; onOpenAdmin: () => void; onRefresh: () => void };

function validHttpUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch { return null; }
}

export default function ArchiveModules({ courses, onBack, onOpenAdmin, onRefresh }: Props) {
  const [folders, setFolders] = useState<ModuleFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[] | null>(null);
  const [filterOpen, setFilterOpen] = useState(false);
  const [openGroups, setOpenGroups] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function loadFolders() {
      setLoading(true);
      setError("");
      if (!supabase) {
        setFolders([]);
        setLoading(false);
        setError("Supabase belum dikonfigurasi.");
        return;
      }
      const { data, error: queryError } = await supabase
        .from("module_folders")
        .select("id,course_id,url,keterangan,aktif,created_at")
        .eq("aktif", true)
        .order("created_at", { ascending: true })
        .order("url", { ascending: true });
      if (cancelled) return;
      if (queryError) {
        setError(queryError.message);
        setFolders([]);
      } else {
        setFolders((data ?? []) as ModuleFolder[]);
      }
      setLoading(false);
    }
    void loadFolders();
    return () => { cancelled = true; };
  }, []);

  const activeCourses = useMemo(() => courses.filter((course) => course.aktif), [courses]);
  const visibleFolders = useMemo(() => {
    const courseIds = new Set(activeCourses.map((course) => course.id));
    const keyword = search.trim().toLocaleLowerCase("id-ID");
    return folders.filter((folder) => {
      if (!courseIds.has(folder.course_id)) return false;
      if (selectedCourseIds !== null && !selectedCourseIds.includes(folder.course_id)) return false;
      const course = activeCourses.find((item) => item.id === folder.course_id);
      const searchable = [folder.keterangan ?? "", course?.nama ?? "", folder.url];
      return !keyword || searchable.some((value) => value.toLocaleLowerCase("id-ID").includes(keyword));
    });
  }, [folders, activeCourses, selectedCourseIds, search]);

  const grouped = useMemo(() => {
    return activeCourses.map((course) => ({
      course,
      folders: visibleFolders.filter((folder) => folder.course_id === course.id),
    })).filter((group) => group.folders.length > 0);
  }, [activeCourses, visibleFolders]);

  function toggleCourse(id: string) {
    const current = selectedCourseIds ?? activeCourses.map((course) => course.id);
    const next = current.includes(id) ? current.filter((value) => value !== id) : [...current, id];
    setSelectedCourseIds(next.length === activeCourses.length ? null : next);
  }
  function resetFilters() { setSearch(""); setSelectedCourseIds(null); }
  function toggleAllGroups() {
    setOpenGroups(openGroups.length === grouped.length ? [] : grouped.map((group) => group.course.id));
  }

  return (
    <main className="app-shell archive-page">
      <header className="app-header">
        <a className="wordmark" href="/" onClick={(event) => { event.preventDefault(); onBack(); }} aria-label="Kembali ke beranda">
          <span className="wordmark-symbol" aria-hidden="true">t<span>.</span></span><span className="wordmark-name">tugas kuliah</span>
        </a>
        <div className="calendar-header-actions">
          <button className="calendar-nav-button" type="button" onClick={onBack}>Beranda</button>
          <button className="open-calendar-button" type="button" onClick={onRefresh}>Muat ulang <span aria-hidden="true">↻</span></button>
          <button className="open-admin-button" type="button" onClick={onOpenAdmin}>Panel Admin <span aria-hidden="true">↗</span></button>
        </div>
      </header>

      <section className="archive-heading">
        <p className="welcome-kicker">MATERI KULIAH <span aria-hidden="true">·</span> PUSAT REFERENSI</p>
        <h1>Arsip Modul</h1>
        <p>Kumpulan folder modul dan materi yang dibagikan untuk tiap mata kuliah.</p>
        <div className="archive-summary"><strong>{loading ? "—" : visibleFolders.length}</strong><span>folder tersedia</span><span className="archive-summary-divider" /><strong>{grouped.length}</strong><span>mata kuliah</span></div>
      </section>

      {error && <section className="notice notice-error" role="alert"><strong>Arsip modul belum berhasil dimuat.</strong><span>{error}</span><button className="text-button" type="button" onClick={onRefresh}>Coba lagi</button></section>}

      <section className="archive-tools" aria-label="Pencarian dan filter arsip">
        <label className="archive-search">
          <span aria-hidden="true">⌕</span>
          <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari keterangan, folder, atau mata kuliah…" aria-label="Cari arsip modul" />
          {search && <button type="button" onClick={() => setSearch("")} aria-label="Hapus pencarian">×</button>}
        </label>
        <button className={"archive-filter-toggle" + (filterOpen || selectedCourseIds !== null ? " is-active" : "")} type="button" onClick={() => setFilterOpen((open) => !open)} aria-expanded={filterOpen}>
          Filter mata kuliah <span aria-hidden="true">⌄</span>{selectedCourseIds !== null && <span className="archive-filter-count">{selectedCourseIds.length}</span>}
        </button>
        <button className="archive-expand-toggle" type="button" onClick={toggleAllGroups} disabled={grouped.length === 0}>{openGroups.length === grouped.length && grouped.length > 0 ? "Tutup semua" : "Buka semua"}</button>
      </section>

      {filterOpen && <fieldset className="archive-course-filter">
        <legend>Pilih mata kuliah</legend>
        <div className="archive-course-options">
          {activeCourses.map((course) => <label key={course.id} className="archive-course-option">
            <input type="checkbox" checked={selectedCourseIds === null || selectedCourseIds.includes(course.id)} onChange={() => toggleCourse(course.id)} />
            <span>{course.nama}</span>
          </label>)}
        </div>
        {selectedCourseIds !== null && <button className="text-button" type="button" onClick={() => setSelectedCourseIds(null)}>Pilih semua mata kuliah</button>}
      </fieldset>}

      {loading ? <div className="archive-empty" role="status"><span className="loading-mark" /><strong>Memuat arsip modul…</strong></div>
      : grouped.length === 0 ? <div className="archive-empty"><span className="empty-mark" aria-hidden="true">⌕</span><strong>{folders.length === 0 ? "Belum ada folder arsip." : "Tidak ada arsip yang cocok."}</strong><span>{folders.length === 0 ? "Folder yang aktif akan muncul di sini setelah ditambahkan admin." : "Coba kata kunci lain atau reset filter mata kuliah."}</span>{(search || selectedCourseIds !== null) && <button className="text-button" type="button" onClick={resetFilters}>Reset pencarian dan filter</button>}</div>
      : <div className="archive-groups">
        {grouped.map(({ course, folders: courseFolders }) => {
          const expanded = openGroups.includes(course.id) || (openGroups.length === 0 && grouped.length === 1);
          return <section className={"archive-course-group" + (expanded ? " is-expanded" : "")} key={course.id}>
            <button className="archive-course-heading" type="button" aria-expanded={expanded} onClick={() => setOpenGroups((current) => current.includes(course.id) ? current.filter((id) => id !== course.id) : [...current, course.id])}>
              <span className="archive-course-icon" aria-hidden="true">▤</span>
              <span className="archive-course-title"><strong>{course.nama}</strong><small>Semester {course.semester} · {course.kategori}</small></span>
              <span className="archive-folder-count">{courseFolders.length} folder</span>
              <span className="archive-chevron" aria-hidden="true">{expanded ? "−" : "+"}</span>
            </button>
            {expanded && <div className="archive-folder-list">
              {courseFolders.map((folder) => {
                const url = validHttpUrl(folder.url);
                return <article className="archive-folder-row" key={folder.id}>
                  <span className="archive-folder-icon" aria-hidden="true">↗</span>
                  <div className="archive-folder-copy"><strong>{folder.keterangan?.trim() || "Folder materi"}</strong><span>{url ? new URL(url).hostname.replace(/^www\./, "") : "Tautan tidak valid"}</span></div>
                  {url ? <a className="archive-open-link" href={url} target="_blank" rel="noopener noreferrer">Buka folder <span aria-hidden="true">↗</span></a> : <span className="archive-invalid-link">Tautan tidak valid</span>}
                </article>;
              })}
            </div>}
          </section>;
        })}
      </div>}

      <footer className="app-footer"><span className="footer-wordmark">tugas kuliah<span>.</span></span><span>Materi kuliah, tersusun per mata kuliah.</span><span className="footer-status"><span className="connection-dot" />{error ? "Koneksi bermasalah" : loading ? "Memuat data" : "Data tersinkron"}</span></footer>
    </main>
  );
}
