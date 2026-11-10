import { useEffect, useMemo, useState } from "react";
import AppNavigation, { type AppPage } from "./AppNavigation";
import MarkdownContent from "./MarkdownContent";

type Task = {
  id: string;
  judul: string;
  mata_kuliah: string;
  jenis: string;
  deadline: string;
  ketentuan: string | null;
  link_vclass: string | null;
  link_pengumpulan: string | null;
  file_soal: string | null;
};

type Progress = "todo" | "doing" | "done";
type Props = {
  tasks: Task[];
  loading: boolean;
  errorMessage: string;
  onNavigate: (page: AppPage) => void;
  onRefresh: () => void;
};

const STORAGE_KEY = "tugas-kuliah.task-progress.v1";
const DATE_FORMAT = new Intl.DateTimeFormat("id-ID", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Asia/Jakarta",
});

function readProgress(): Record<string, Progress> {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return Object.fromEntries(
      Object.entries(parsed).filter((entry): entry is [string, Progress] =>
        typeof entry[0] === "string" &&
        (entry[1] === "todo" || entry[1] === "doing" || entry[1] === "done"),
      ),
    );
  } catch {
    return {};
  }
}

function safeUrl(value: string | null): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}

function progressLabel(value: Progress): string {
  if (value === "done") return "Selesai";
  if (value === "doing") return "Sedang dikerjakan";
  return "Belum mulai";
}

function deadlineState(deadline: string, now: number): { overdue: boolean; label: string } {
  const timestamp = new Date(deadline).getTime();
  if (!Number.isFinite(timestamp)) return { overdue: false, label: "Tanggal tidak valid" };
  const difference = timestamp - now;
  if (difference < 0) return { overdue: true, label: "Deadline sudah lewat" };
  if (difference < 60 * 60 * 1000) return { overdue: false, label: "Kurang dari 1 jam lagi" };
  const days = Math.floor(difference / 86_400_000);
  if (days > 0) return { overdue: false, label: days + " hari lagi" };
  return { overdue: false, label: Math.floor(difference / 3_600_000) + " jam lagi" };
}

export default function TaskListPage({ tasks, loading, errorMessage, onNavigate, onRefresh }: Props) {
  const [progress, setProgress] = useState<Record<string, Progress>>(readProgress);
  const [search, setSearch] = useState("");
  const [courseFilter, setCourseFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [deadlineFilter, setDeadlineFilter] = useState("all");
  const [progressFilter, setProgressFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("nearest");
  const [now, setNow] = useState(Date.now);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
    } catch {
      // The task list remains usable if browser storage is disabled or full.
    }
  }, [progress]);

  useEffect(() => {
    if (loading) return;
    const validIds = new Set(tasks.map((task) => task.id));
    setProgress((current) => {
      const next = Object.fromEntries(Object.entries(current).filter(([id]) => validIds.has(id)));
      return Object.keys(next).length === Object.keys(current).length ? current : next;
    });
  }, [tasks, loading]);

  const courses = useMemo(
    () => [...new Set(tasks.map((task) => task.mata_kuliah).filter(Boolean))].sort((a, b) => a.localeCompare(b, "id-ID")),
    [tasks],
  );
  const types = useMemo(
    () => [...new Set(tasks.map((task) => task.jenis).filter(Boolean))].sort((a, b) => a.localeCompare(b, "id-ID")),
    [tasks],
  );

  const counts = useMemo(() => ({
    todo: tasks.filter((task) => (progress[task.id] ?? "todo") === "todo").length,
    doing: tasks.filter((task) => progress[task.id] === "doing").length,
    done: tasks.filter((task) => progress[task.id] === "done").length,
  }), [tasks, progress]);

  const filteredTasks = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase("id-ID");
    return tasks.filter((task) => {
      const searchable = [
        task.judul,
        task.mata_kuliah,
        task.jenis,
        task.ketentuan ?? "",
      ].join(" ").toLocaleLowerCase("id-ID");
      const timestamp = new Date(task.deadline).getTime();
      const currentProgress = progress[task.id] ?? "todo";
      const matchesDeadline =
        deadlineFilter === "all" ||
        (deadlineFilter === "upcoming" && timestamp >= now) ||
        (deadlineFilter === "overdue" && timestamp < now);
      return (
        (!keyword || searchable.includes(keyword)) &&
        (courseFilter === "all" || task.mata_kuliah === courseFilter) &&
        (typeFilter === "all" || task.jenis === typeFilter) &&
        matchesDeadline &&
        (progressFilter === "all" || currentProgress === progressFilter)
      );
    }).sort((a, b) => {
      if (sortOrder === "title") return a.judul.localeCompare(b.judul, "id-ID");
      const aTime = new Date(a.deadline).getTime();
      const bTime = new Date(b.deadline).getTime();
      return sortOrder === "latest" ? bTime - aTime : aTime - bTime;
    });
  }, [tasks, progress, search, courseFilter, typeFilter, deadlineFilter, progressFilter, sortOrder, now]);

  function updateProgress(taskId: string, value: Progress) {
    setProgress((current) => ({ ...current, [taskId]: value }));
  }

  function resetFilters() {
    setSearch("");
    setCourseFilter("all");
    setTypeFilter("all");
    setDeadlineFilter("all");
    setProgressFilter("all");
    setSortOrder("nearest");
  }

  function clearProgress() {
    if (!window.confirm("Hapus seluruh progress tugas yang tersimpan di browser ini?")) return;
    setProgress({});
  }

  return (
    <main className="app-shell all-tasks-page">
      <AppNavigation currentPage="tasks" onNavigate={onNavigate} onRefresh={onRefresh} />
      <section className="all-tasks-heading">
        <p className="welcome-kicker">AGENDA AKADEMIK <span aria-hidden="true">·</span> DAFTAR LENGKAP</p>
        <h1>Semua Tugas</h1>
        <p>Semua deadline dalam satu tempat. Tandai progress agar kamu tahu apa yang masih perlu dikerjakan.</p>
      </section>

      {errorMessage && (
        <section className="notice notice-error" role="alert">
          <strong>Data tugas belum berhasil dimuat.</strong>
          <span>{errorMessage}</span>
          <button className="text-button" type="button" onClick={onRefresh}>Coba lagi</button>
        </section>
      )}

      <section className="all-tasks-progress" aria-label="Ringkasan progress tugas">
        <div><strong>{loading ? "—" : tasks.length}</strong><span>Total tugas</span></div>
        <div><strong>{loading ? "—" : counts.todo}</strong><span>Belum mulai</span></div>
        <div><strong>{loading ? "—" : counts.doing}</strong><span>Dikerjakan</span></div>
        <div><strong>{loading ? "—" : counts.done}</strong><span>Selesai</span></div>
      </section>

      <section className="all-tasks-tools" aria-label="Pencarian dan filter tugas">
        <label className="all-tasks-search">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Cari judul, mata kuliah, atau instruksi…"
            aria-label="Cari semua tugas"
          />
          {search && <button type="button" onClick={() => setSearch("")} aria-label="Hapus pencarian">×</button>}
        </label>
        <div className="all-tasks-filter-grid">
          <label><span>Mata kuliah</span>
            <select value={courseFilter} onChange={(event) => setCourseFilter(event.target.value)}>
              <option value="all">Semua mata kuliah</option>
              {courses.map((course) => <option value={course} key={course}>{course}</option>)}
            </select>
          </label>
          <label><span>Jenis tugas</span>
            <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
              <option value="all">Semua jenis</option>
              {types.map((type) => <option value={type} key={type}>{type}</option>)}
            </select>
          </label>
          <label><span>Deadline</span>
            <select value={deadlineFilter} onChange={(event) => setDeadlineFilter(event.target.value)}>
              <option value="all">Semua deadline</option>
              <option value="upcoming">Mendatang</option>
              <option value="overdue">Terlewat</option>
            </select>
          </label>
          <label><span>Progress</span>
            <select value={progressFilter} onChange={(event) => setProgressFilter(event.target.value)}>
              <option value="all">Semua progress</option>
              <option value="todo">Belum mulai</option>
              <option value="doing">Sedang dikerjakan</option>
              <option value="done">Selesai</option>
            </select>
          </label>
          <label><span>Urutkan</span>
            <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
              <option value="nearest">Deadline terdekat</option>
              <option value="latest">Deadline terjauh</option>
              <option value="title">Nama tugas</option>
            </select>
          </label>
        </div>
        <div className="all-tasks-tool-footer">
          <span>{loading ? "Memuat tugas…" : filteredTasks.length + " dari " + tasks.length + " tugas"}</span>
          <div>
            <button className="text-button" type="button" onClick={resetFilters}>Reset filter</button>
            <button className="text-button" type="button" onClick={clearProgress} disabled={counts.todo === tasks.length}>Reset progress</button>
          </div>
        </div>
      </section>

      <section className="all-task-list" aria-label="Daftar seluruh tugas">
        {loading ? (
          <div className="empty-state" role="status"><span className="loading-mark" /><strong>Memuat semua tugas…</strong></div>
        ) : filteredTasks.length === 0 ? (
          <div className="empty-state">
            <span className="empty-mark" aria-hidden="true">⌕</span>
            <strong>{tasks.length === 0 ? "Belum ada tugas yang tercatat." : "Tidak ada tugas yang cocok."}</strong>
            <span>{tasks.length === 0 ? "Tugas yang ditambahkan admin akan muncul di sini." : "Coba ubah kata kunci atau filter pencarian."}</span>
            {(search || courseFilter !== "all" || typeFilter !== "all" || deadlineFilter !== "all" || progressFilter !== "all") &&
              <button className="text-button" type="button" onClick={resetFilters}>Bersihkan filter</button>}
          </div>
        ) : filteredTasks.map((task) => {
          const status = progress[task.id] ?? "todo";
          const due = deadlineState(task.deadline, now);
          const timestamp = new Date(task.deadline);
          const dateLabel = Number.isNaN(timestamp.getTime()) ? "Tanggal tidak valid" : DATE_FORMAT.format(timestamp) + " WIB";
          return (
            <article className={"all-task-card" + (due.overdue ? " is-overdue" : "") + (status === "done" ? " is-complete" : "")} key={task.id}>
              <div className="all-task-main">
                <div className="all-task-meta">
                  <span>{task.mata_kuliah || "Tanpa mata kuliah"}</span>
                  <span aria-hidden="true">·</span>
                  <span>{task.jenis}</span>
                </div>
                <h2>{task.judul || "Tugas tanpa judul"}</h2>
                <p className={"all-task-deadline" + (due.overdue && status !== "done" ? " is-overdue" : "")}>
                  <strong>{dateLabel}</strong><span>{status === "done" ? "Ditandai selesai" : due.label}</span>
                </p>
                {task.ketentuan && (
                  <details className="all-task-instructions">
                    <summary>Lihat instruksi tugas</summary>
                    <MarkdownContent content={task.ketentuan} />
                  </details>
                )}
                <div className="all-task-links">
                  {safeUrl(task.link_vclass) && <a href={safeUrl(task.link_vclass)!} target="_blank" rel="noopener noreferrer">VClass ↗</a>}
                  {safeUrl(task.link_pengumpulan) && <a href={safeUrl(task.link_pengumpulan)!} target="_blank" rel="noopener noreferrer">Pengumpulan ↗</a>}
                  {safeUrl(task.file_soal) && <a href={safeUrl(task.file_soal)!} target="_blank" rel="noopener noreferrer">File soal ↗</a>}
                </div>
              </div>
              <label className="all-task-progress-control">
                <span>Progress</span>
                <select value={status} onChange={(event) => updateProgress(task.id, event.target.value as Progress)} aria-label={"Progress " + (task.judul || "tugas")}>
                  <option value="todo">Belum mulai</option>
                  <option value="doing">Sedang dikerjakan</option>
                  <option value="done">Selesai</option>
                </select>
                <small>{progressLabel(status)}</small>
              </label>
            </article>
          );
        })}
      </section>
      <p className="all-tasks-local-note"><strong>Catatan progress:</strong> status pengerjaan disimpan di browser/perangkat ini saja, bukan di akun atau database bersama.</p>
      <footer className="app-footer">
        <span className="footer-wordmark">tugas kuliah<span>.</span></span>
        <span>Seluruh deadline · Waktu Indonesia Barat</span>
        <span className="footer-status"><span className="connection-dot" />{errorMessage ? "Koneksi bermasalah" : loading ? "Memuat data" : "Data tersinkron"}</span>
      </footer>
    </main>
  );
}
