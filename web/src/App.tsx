import { useEffect, useMemo, useState } from "react";
import { supabase, supabaseConfigMissing } from "./lib/supabase";
import AdminPanel from "./components/AdminPanel";
import CalendarPage from "./components/CalendarPage";
import MarkdownContent from "./components/MarkdownContent";

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

type Course = {
  id: string;
  nama: string;
  semester: number;
  kategori: string;
  aktif: boolean;
};

type TaskView = "upcoming" | "overdue";

const DATETIME_FORMAT = new Intl.DateTimeFormat("id-ID", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Asia/Jakarta",
});

const WEEKDAY_FORMAT = new Intl.DateTimeFormat("id-ID", {
  weekday: "short",
  timeZone: "Asia/Jakarta",
});

const DAY_MONTH_FORMAT = new Intl.DateTimeFormat("id-ID", {
  day: "numeric",
  month: "short",
  timeZone: "Asia/Jakarta",
});

const FULL_DATE_FORMAT = new Intl.DateTimeFormat("id-ID", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "Asia/Jakarta",
});

function safeHttpUrl(value: string | null): string | null {
  if (!value) return null;

  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

function deadlineText(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Tanggal tidak valid"
    : DATETIME_FORMAT.format(date) + " WIB";
}

function countdownText(value: string, now: number): string {
  const difference = new Date(value).getTime() - now;
  if (!Number.isFinite(difference)) return "Tanggal tidak valid";
  if (difference < 0) return "Sudah lewat";

  const days = Math.floor(difference / 86_400_000);
  const hours = Math.floor((difference % 86_400_000) / 3_600_000);

  if (days > 0) return days + " hari " + hours + " jam lagi";
  if (hours > 0) return hours + " jam lagi";
  return "Kurang dari 1 jam lagi";
}

function ExternalTaskLink({ href, children }: { href: string | null; children: string }) {
  if (!href) return null;

  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
      <span aria-hidden="true"> ↗</span>
    </a>
  );
}

function TaskRow({ task, now, overdue }: { task: Task; now: number; overdue: boolean }) {
  const deadlineDate = new Date(task.deadline);
  const safeDate = Number.isNaN(deadlineDate.getTime()) ? new Date(now) : deadlineDate;

  return (
    <article className={"task-row" + (overdue ? " task-row-overdue" : "")}>
      <time className="task-date" dateTime={task.deadline}>
        <span>{WEEKDAY_FORMAT.format(safeDate).replace(".", "")}</span>
        <strong>{DAY_MONTH_FORMAT.format(safeDate)}</strong>
      </time>

      <div className="task-main">
        <div className="task-meta">
          <span className="task-course">{task.mata_kuliah || "Tanpa mata kuliah"}</span>
          <span className="meta-divider" aria-hidden="true">·</span>
          <span>{task.jenis}</span>
        </div>
        <h3>{task.judul || "Tugas tanpa judul"}</h3>
        {task.ketentuan && <MarkdownContent className="task-description" content={task.ketentuan} />}
        <div className="task-links" aria-label="Tautan tugas">
          <ExternalTaskLink href={safeHttpUrl(task.link_vclass)}>VClass</ExternalTaskLink>
          <ExternalTaskLink href={safeHttpUrl(task.link_pengumpulan)}>Pengumpulan</ExternalTaskLink>
          <ExternalTaskLink href={safeHttpUrl(task.file_soal)}>File soal</ExternalTaskLink>
        </div>
      </div>

      <div className="task-timing">
        <span className={"deadline-status" + (overdue ? " is-overdue" : "")}>
          <span className="status-dot" aria-hidden="true" />
          {countdownText(task.deadline, now)}
        </span>
        <span className="task-time">{deadlineText(task.deadline)}</span>
      </div>
    </article>
  );
}

function App() {
  const [page, setPage] = useState<"home" | "admin" | "calendar">("home");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [search, setSearch] = useState("");
  const [courseFilter, setCourseFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [taskView, setTaskView] = useState<TaskView>("upcoming");
  const [refreshKey, setRefreshKey] = useState(0);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setErrorMessage("");

      if (!supabase) {
        setLoading(false);
        return;
      }

      const [taskResult, courseResult] = await Promise.all([
        supabase
          .from("tasks")
          .select("id,judul,mata_kuliah,jenis,deadline,ketentuan,link_vclass,link_pengumpulan,file_soal")
          .order("deadline", { ascending: true }),
        supabase
          .from("courses")
          .select("id,nama,semester,kategori,aktif")
          .eq("aktif", true)
          .order("semester", { ascending: true })
          .order("nama", { ascending: true }),
      ]);

      if (cancelled) return;

      if (taskResult.error || courseResult.error) {
        const messages = [
          taskResult.error ? "Tabel tasks: " + taskResult.error.message : "",
          courseResult.error ? "Tabel courses: " + courseResult.error.message : "",
        ].filter(Boolean);
        setErrorMessage(messages.join(" · "));
      } else {
        setTasks((taskResult.data ?? []) as unknown as Task[]);
        setCourses((courseResult.data ?? []) as unknown as Course[]);
      }

      setLoading(false);
    }

    void loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const filteredTasks = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase("id-ID");

    return tasks.filter((task) => {
      const searchable = [task.judul, task.mata_kuliah, task.ketentuan ?? ""];
      const matchesSearch =
        !keyword ||
        searchable.some((value) => value.toLocaleLowerCase("id-ID").includes(keyword));
      const matchesCourse = courseFilter === "all" || task.mata_kuliah === courseFilter;
      const matchesType = typeFilter === "all" || task.jenis === typeFilter;

      return matchesSearch && matchesCourse && matchesType;
    });
  }, [tasks, search, courseFilter, typeFilter]);

  const upcomingTasks = useMemo(
    () =>
      filteredTasks
        .filter((task) => new Date(task.deadline).getTime() >= now)
        .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime()),
    [filteredTasks, now],
  );

  const overdueTasks = useMemo(
    () =>
      filteredTasks
        .filter((task) => new Date(task.deadline).getTime() < now)
        .sort((a, b) => new Date(b.deadline).getTime() - new Date(a.deadline).getTime()),
    [filteredTasks, now],
  );

  const urgentCount = upcomingTasks.filter((task) => {
    const difference = new Date(task.deadline).getTime() - now;
    return difference >= 0 && difference <= 48 * 60 * 60 * 1000;
  }).length;

  const selectedTasks = taskView === "upcoming" ? upcomingTasks : overdueTasks;
  const visibleTasks = selectedTasks.slice(0, 5);

  const taskCountsByCourse = useMemo(() => {
    const counts = new Map<string, number>();
    for (const task of tasks) {
      counts.set(task.mata_kuliah, (counts.get(task.mata_kuliah) ?? 0) + 1);
    }
    return counts;
  }, [tasks]);

  function clearFilters() {
    setSearch("");
    setCourseFilter("all");
    setTypeFilter("all");
  }

  const connectionLabel = supabaseConfigMissing
    ? "Supabase belum diatur"
    : loading
      ? "Memuat data"
      : errorMessage
        ? "Koneksi bermasalah"
        : "Tersinkron";

  if (page === "calendar") {
    return (
      <CalendarPage
        tasks={tasks}
        loading={loading}
        errorMessage={errorMessage}
        onBack={() => setPage("home")}
        onOpenAdmin={() => setPage("admin")}
        onRefresh={() => setRefreshKey((key) => key + 1)}
      />
    );
  }

  if (page === "admin") {
    return (
      <AdminPanel
        tasks={tasks}
        courses={courses}
        onBack={() => setPage("home")}
        onDataChanged={() => setRefreshKey((key) => key + 1)}
      />
    );
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <a className="wordmark" href="/" aria-label="Tugas Kuliah, beranda">
          <span className="wordmark-symbol" aria-hidden="true">t<span>.</span></span>
          <span className="wordmark-name">tugas kuliah</span>
        </a>

        <div className="header-right">
          <button className="open-calendar-button" type="button" onClick={() => setPage("calendar")}>
            Kalender <span aria-hidden="true">↗</span>
          </button>
          <button className="open-admin-button" type="button" onClick={() => setPage("admin")} aria-label="Buka Panel Admin">
            Panel Admin <span aria-hidden="true">↗</span>
          </button>
          <span className={"connection-state" + (errorMessage || supabaseConfigMissing ? " is-warning" : "")}>
            <span className="connection-dot" aria-hidden="true" />
            {connectionLabel}
          </span>
          <button
            className="refresh-button"
            type="button"
            onClick={() => setRefreshKey((key) => key + 1)}
            disabled={loading}
            aria-label="Muat ulang data dari Supabase"
            title="Muat ulang"
          >
            ↻
          </button>
        </div>
      </header>

      <section className="welcome">
        <div>
          <p className="welcome-kicker">AGENDA KULIAH <span aria-hidden="true">·</span> {FULL_DATE_FORMAT.format(new Date(now))}</p>
          <h1>Tugas kuliah,<br className="wide-break" /> satu per satu.</h1>
          <p className="welcome-copy">Lihat yang paling dekat, pilih langkah berikutnya, lalu mulai dari sana.</p>
        </div>
        <p className="welcome-note">
          {loading
            ? "Menyiapkan daftar kamu…"
            : urgentCount > 0
              ? urgentCount + " deadline dalam 48 jam ke depan."
              : "Tidak ada deadline mendesak dalam 48 jam."}
        </p>
      </section>

      {supabaseConfigMissing && (
        <section className="notice notice-warning" role="alert">
          <strong>Supabase belum dikonfigurasi.</strong>
          <span>
            Salin file .env.example menjadi .env.local, lalu isi VITE_SUPABASE_URL dan
            VITE_SUPABASE_ANON_KEY dengan URL project serta publishable/anon key.
          </span>
        </section>
      )}

      {errorMessage && (
        <section className="notice notice-error" role="alert">
          <strong>Data tugas belum berhasil dimuat.</strong>
          <span>{errorMessage}. Periksa koneksi Supabase dan kebijakan akses tabel, lalu coba lagi.</span>
          <button className="text-button" type="button" onClick={() => setRefreshKey((key) => key + 1)}>
            Coba lagi
          </button>
        </section>
      )}

      <div className="workspace-grid">
        <section className="task-section" aria-labelledby="task-section-title">
          <div className="section-heading">
            <div>
              <h2 id="task-section-title">{taskView === "upcoming" ? "Yang akan datang" : "Sudah lewat"}</h2>
              <p className="section-subtitle">
                {taskView === "upcoming"
                  ? "Urut berdasarkan deadline terdekat."
                  : "Tugas yang tenggatnya sudah berlalu."}
              </p>
            </div>
            <span className="result-count">{loading ? "…" : selectedTasks.length} tugas</span>
          </div>

          <div className="task-tabs" role="group" aria-label="Tampilan tugas">
            <button
              type="button"
              className={taskView === "upcoming" ? "task-tab is-current" : "task-tab"}
              onClick={() => setTaskView("upcoming")}
              aria-pressed={taskView === "upcoming"}
            >
              Mendatang <span>{loading ? "—" : upcomingTasks.length}</span>
            </button>
            <button
              type="button"
              className={taskView === "overdue" ? "task-tab is-current" : "task-tab"}
              onClick={() => setTaskView("overdue")}
              aria-pressed={taskView === "overdue"}
            >
              Terlewat <span>{loading ? "—" : overdueTasks.length}</span>
            </button>
          </div>

          <div className="filters">
            <label className="search-field">
              <span className="search-symbol" aria-hidden="true">⌕</span>
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Cari tugas atau mata kuliah"
                aria-label="Cari tugas atau mata kuliah"
              />
              {search && (
                <button type="button" className="clear-search" onClick={() => setSearch("")} aria-label="Hapus pencarian">
                  ×
                </button>
              )}
            </label>

            <label className="select-field">
              <span className="sr-only">Mata kuliah</span>
              <select value={courseFilter} onChange={(event) => setCourseFilter(event.target.value)}>
                <option value="all">Semua mata kuliah</option>
                {courses.map((course) => (
                  <option value={course.nama} key={course.id}>{course.nama}</option>
                ))}
              </select>
            </label>

            <label className="select-field">
              <span className="sr-only">Jenis tugas</span>
              <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
                <option value="all">Semua jenis</option>
                <option value="Teori">Teori</option>
                <option value="Praktikum">Praktikum</option>
                <option value="Quiz">Quiz</option>
                <option value="Ujian">Ujian</option>
              </select>
            </label>
          </div>

          {loading ? (
            <div className="empty-state" role="status">
              <span className="loading-mark" aria-hidden="true" />
              <strong>Memuat tugas</strong>
              <span>Sebentar, daftar kamu sedang disiapkan.</span>
            </div>
          ) : visibleTasks.length > 0 ? (
            <div className="task-list">
              {visibleTasks.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  now={now}
                  overdue={taskView === "overdue"}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-mark" aria-hidden="true">{taskView === "upcoming" ? "—" : "✓"}</span>
              <strong>
                {filteredTasks.length === 0
                  ? "Tidak ada tugas yang cocok"
                  : taskView === "upcoming"
                    ? "Tidak ada deadline mendatang"
                    : "Tidak ada tugas yang terlewat"}
              </strong>
              <span>
                {filteredTasks.length === 0
                  ? "Coba kata kunci atau filter yang lain."
                  : taskView === "upcoming"
                    ? "Bagus, tidak ada tenggat yang perlu dikejar sekarang."
                    : "Semua tugas masih berada dalam tenggat."}
              </span>
              {(search || courseFilter !== "all" || typeFilter !== "all") && (
                <button className="text-button" type="button" onClick={clearFilters}>Bersihkan filter</button>
              )}
            </div>
          )}

          {!loading && selectedTasks.length > visibleTasks.length && (
            <p className="list-footnote">
              Menampilkan {visibleTasks.length} dari {selectedTasks.length} tugas.
            </p>
          )}
        </section>

        <aside className="course-section" aria-labelledby="course-section-title">
          <div className="course-heading">
            <div>
              <h2 id="course-section-title">Mata kuliah</h2>
              <p className="section-subtitle">Pilih satu untuk menyaring daftar.</p>
            </div>
            <span className="course-total">{loading ? "…" : courses.length}</span>
          </div>

          {loading ? (
            <p className="aside-message">Memuat mata kuliah…</p>
          ) : courses.length === 0 ? (
            <p className="aside-message">Belum ada mata kuliah aktif.</p>
          ) : (
            <div className="course-list">
              {courses
                .filter((course) => (taskCountsByCourse.get(course.nama) ?? 0) > 0)
                .map((course) => (
                  <button
                    className={"course-row" + (courseFilter === course.nama ? " is-selected" : "")}
                    key={course.id}
                    type="button"
                    onClick={() => setCourseFilter(courseFilter === course.nama ? "all" : course.nama)}
                    aria-pressed={courseFilter === course.nama}
                  >
                    <span className="course-row-copy">
                      <strong>{course.nama}</strong>
                      <small>Semester {course.semester} · {course.kategori}</small>
                    </span>
                    <span className="course-count">{taskCountsByCourse.get(course.nama) ?? 0}</span>
                  </button>
                ))}
            </div>
          )}

          {courseFilter !== "all" && (
            <button className="text-button clear-course-filter" type="button" onClick={() => setCourseFilter("all")}>
              Tampilkan semua mata kuliah
            </button>
          )}
        </aside>
      </div>

      <footer className="app-footer">
        <span className="footer-wordmark">tugas kuliah<span>.</span></span>
        <span>Semoga kuliahmu hari ini lancar.</span>
        <span className="footer-status">
          <span className="connection-dot" aria-hidden="true" />
          {connectionLabel}
        </span>
      </footer>
    </main>
  );
}

export default App;
