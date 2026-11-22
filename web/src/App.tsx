import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { supabase, supabaseConfigMissing } from "./lib/supabase";
const AdminPanel = lazy(() => import("./components/AdminPanel"));
const CalendarPage = lazy(() => import("./components/CalendarPage"));
const ArchiveModules = lazy(() => import("./components/ArchiveModules"));
import MarkdownContent from "./components/MarkdownContent";
import AppNavigation, { type AppPage } from "./components/AppNavigation";
import PresenceLayer from "./components/PresenceLayer";

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
  return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
}

function TaskRow({ task, now, overdue }: { task: Task; now: number; overdue: boolean }) {
  const date = new Date(task.deadline);
  const validDate = Number.isNaN(date.getTime()) ? new Date(now) : date;

  return (
    <article className={"agenda-item" + (overdue ? " is-overdue" : "")}>
      <div className="agenda-date" aria-label={FULL_DATE_FORMAT.format(validDate)}>
        <span>{WEEKDAY_FORMAT.format(validDate).replace(".", "")}</span>
        <strong>{new Intl.DateTimeFormat("id-ID", { day: "2-digit", timeZone: "Asia/Jakarta" }).format(validDate)}</strong>
        <span>{new Intl.DateTimeFormat("id-ID", { month: "short", timeZone: "Asia/Jakarta" }).format(validDate)}</span>
      </div>
      <div className="agenda-task-copy">
        <div className="agenda-task-meta">
          <span className="agenda-course-name">{task.mata_kuliah || "Tanpa mata kuliah"}</span>
          <span className="agenda-task-type">{task.jenis}</span>
        </div>
        <h3>{task.judul || "Tugas tanpa judul"}</h3>
        {task.ketentuan && <MarkdownContent className="agenda-task-description" content={task.ketentuan} />}
        <div className="agenda-task-links">
          <ExternalTaskLink href={safeHttpUrl(task.link_vclass)}>VClass</ExternalTaskLink>
          <ExternalTaskLink href={safeHttpUrl(task.link_pengumpulan)}>Pengumpulan</ExternalTaskLink>
          <ExternalTaskLink href={safeHttpUrl(task.file_soal)}>File soal</ExternalTaskLink>
        </div>
      </div>
      <div className="agenda-task-deadline">
        <span className={"deadline-countdown" + (overdue ? " is-overdue" : "")}>{countdownText(task.deadline, now)}</span>
        <time dateTime={task.deadline}>{deadlineText(task.deadline)}</time>
      </div>
    </article>
  );
}

function DashboardMetrics({ taskCount, nearCount, overdueCount, loading }: {
  taskCount: number;
  nearCount: number;
  overdueCount: number;
  loading: boolean;
}) {
  const metrics = [
    { label: "Tugas ditampilkan", value: taskCount },
    { label: "Deadline dekat", value: nearCount },
    { label: "Sudah lewat", value: overdueCount },
  ];

  return (
    <section className="dashboard-metrics" aria-label="Ringkasan deadline">
      {metrics.map((metric) => (
        <div className="dashboard-metric" key={metric.label}>
          <strong>{loading ? "—" : metric.value}</strong>
          <span>{metric.label}</span>
        </div>
      ))}
    </section>
  );
}

function NewlyOverdueNotice({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) return null;

  const visibleTasks = tasks.slice(0, 3);
  const remaining = tasks.length - visibleTasks.length;

  return (
    <section className="recent-overdue" aria-labelledby="recent-overdue-heading">
      <div className="recent-overdue-heading">
        <span className="recent-overdue-mark" aria-hidden="true">!</span>
        <div>
          <h2 id="recent-overdue-heading">Baru terlewat</h2>
          <p>Deadline yang lewat dalam 3 hari terakhir. Buka tautan langsung untuk segera menindaklanjutinya.</p>
        </div>
      </div>
      <div className="recent-overdue-list">
        {visibleTasks.map((task) => (
          <article className="recent-overdue-item" key={task.id}>
            <div className="recent-overdue-copy">
              <strong>{task.judul || "Tugas tanpa judul"}</strong>
              <span>{task.mata_kuliah || "Tanpa mata kuliah"} · Deadline {deadlineText(task.deadline)}</span>
            </div>
            <div className="recent-overdue-links" aria-label={"Tautan " + (task.judul || "tugas")}>
              <ExternalTaskLink href={safeHttpUrl(task.link_vclass)}>VClass</ExternalTaskLink>
              <ExternalTaskLink href={safeHttpUrl(task.link_pengumpulan)}>Pengumpulan</ExternalTaskLink>
              <ExternalTaskLink href={safeHttpUrl(task.file_soal)}>File soal</ExternalTaskLink>
            </div>
          </article>
        ))}
      </div>
      {remaining > 0 && <p className="recent-overdue-more">Dan {remaining} tugas baru terlewat lainnya ada di daftar tugas.</p>}
    </section>
  );
}

function App() {
  const [page, setPage] = useState<AppPage>("home");
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

  const navigationRequest = useRef(0);
  const activeTransition = useRef<{
    finished: Promise<void>;
    skipTransition: () => void;
  } | null>(null);

  async function navigateTo(nextPage: AppPage) {
    const request = ++navigationRequest.current;
    if (nextPage === page) return;

    // Load the destination before starting the transition so Suspense cannot
    // flash a second loading page over the current screen.
    switch (nextPage) {
      case "calendar":
        await import("./components/CalendarPage");
        break;
      case "archive":
        await import("./components/ArchiveModules");
        break;
      case "admin":
        await import("./components/AdminPanel");
        break;
    }

    if (request !== navigationRequest.current) return;

    // Never overlap two browser view transitions. Finish the previous snapshot
    // before starting the newest navigation request.
    const previousTransition = activeTransition.current;
    if (previousTransition) {
      previousTransition.skipTransition();
      try {
        await previousTransition.finished;
      } catch {
        // A skipped transition may reject in some browser implementations.
      }
      if (request !== navigationRequest.current) return;
      if (activeTransition.current === previousTransition) activeTransition.current = null;
    }

    const commitNavigation = () => flushSync(() => setPage(nextPage));
    const transitionDocument = document as Document & {
      startViewTransition?: (callback: () => void) => {
        finished: Promise<void>;
        skipTransition: () => void;
      };
    };

    if (
      typeof transitionDocument.startViewTransition === "function" &&
      !window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      const transition = transitionDocument.startViewTransition(commitNavigation);
      activeTransition.current = transition;
      void transition.finished.then(
        () => {
          if (activeTransition.current === transition) activeTransition.current = null;
        },
        () => {
          if (activeTransition.current === transition) activeTransition.current = null;
        },
      );
    } else {
      commitNavigation();
    }
  }

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!supabase) return;
    const client = supabase;
    let refreshTimer: number | undefined;
    const scheduleRefresh = () => {
      if (refreshTimer !== undefined) window.clearTimeout(refreshTimer);
      refreshTimer = window.setTimeout(() => {
        setRefreshKey((key) => key + 1);
        refreshTimer = undefined;
      }, 250);
    };
    const channel = client
      .channel("tugas-kuliah-data-changes")
      .on("postgres_changes", { event: "*", schema: "public", table: "tasks" }, scheduleRefresh)
      .on("postgres_changes", { event: "*", schema: "public", table: "courses" }, scheduleRefresh)
      .on("postgres_changes", { event: "*", schema: "public", table: "module_folders" }, scheduleRefresh)
      .subscribe();

    return () => {
      if (refreshTimer !== undefined) window.clearTimeout(refreshTimer);
      void client.removeChannel(channel);
    };
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

  const newlyOverdueTasks = useMemo(() => {
    const cutoff = now - 3 * 24 * 60 * 60 * 1000;
    return filteredTasks
      .filter((task) => {
        const deadline = new Date(task.deadline).getTime();
        return deadline < now && deadline >= cutoff;
      })
      .sort((a, b) => new Date(b.deadline).getTime() - new Date(a.deadline).getTime());
  }, [filteredTasks, now]);

  const urgentCount = upcomingTasks.filter((task) => {
    const difference = new Date(task.deadline).getTime() - now;
    return difference >= 0 && difference <= 48 * 60 * 60 * 1000;
  }).length;

  // Mirror Streamlit: count near deadlines only in the five nearest upcoming tasks.
  const nearDeadlineCount = upcomingTasks.slice(0, 5).filter((task) => {
    const difference = new Date(task.deadline).getTime() - now;
    return difference >= 0 && difference < 3 * 24 * 60 * 60 * 1000;
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

  // Keep legacy task course names filterable even if the catalog entry was deactivated.
  const courseOptions = useMemo(() => {
    const activeNames = courses.map((course) => course.nama);
    const activeSet = new Set(activeNames);
    const legacyNames = [...new Set(tasks.map((task) => task.mata_kuliah).filter(Boolean).filter((name) => !activeSet.has(name)))]
      .sort((a, b) => a.localeCompare(b, "id-ID"));
    return [...activeNames, ...legacyNames];
  }, [courses, tasks]);

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
      <>
      <PresenceLayer page={page} />
      <Suspense fallback={
        <main className="app-shell calendar-loading-page" role="status">
          <div className="calendar-loading">
            <span className="loading-mark" />
            <strong>Membuka kalender…</strong>
          </div>
        </main>
      }>
        <CalendarPage
          tasks={tasks}
          loading={loading}
          errorMessage={errorMessage}
          onNavigate={navigateTo}
          onRefresh={() => setRefreshKey((key) => key + 1)}
        />
      </Suspense>
      </>
    );
  }

  if (page === "archive") {
    return (
      <>
      <PresenceLayer page={page} />
      <Suspense fallback={
        <main className="app-shell calendar-loading-page" role="status">
          <div className="calendar-loading">
            <span className="loading-mark" />
            <strong>Membuka arsip modul…</strong>
          </div>
        </main>
      }>
        <ArchiveModules
          key={refreshKey}
          courses={courses}
          onNavigate={navigateTo}
          onRefresh={() => setRefreshKey((key) => key + 1)}
        />
      </Suspense>
      </>
    );
  }

  if (page === "admin") {
    return (
      <>
      <PresenceLayer page={page} />
      <Suspense fallback={
        <main className="app-shell calendar-loading-page" role="status">
          <div className="calendar-loading">
            <span className="loading-mark" />
            <strong>Membuka panel admin…</strong>
          </div>
        </main>
      }>
        <AdminPanel
          tasks={tasks}
          courses={courses}
          onNavigate={navigateTo}
          onDataChanged={() => setRefreshKey((key) => key + 1)}
        />
      </Suspense>
      </>
    );
  }

  return (
    <>
    <PresenceLayer page={page} />
    <main className="app-shell">
      <AppNavigation
        currentPage="home"
        onNavigate={navigateTo}
        connectionLabel={connectionLabel}
        connectionWarning={Boolean(errorMessage || supabaseConfigMissing)}
        onRefresh={() => setRefreshKey((key) => key + 1)}
        refreshDisabled={loading}
      />

      <div className="page-stage home-stage">
        <header className="desk-heading">
          <div>
            <p className="desk-date">{FULL_DATE_FORMAT.format(new Date(now))}</p>
            <h1>Agenda belajar</h1>
            <p className="desk-intro">Semua tenggat kuliahmu ada di satu tempat. Mulai dari yang paling dekat.</p>
          </div>
          <div className="desk-heading-count">
            <strong>{loading ? "—" : upcomingTasks.length}</strong>
            <span>tugas mendatang</span>
            <span>{urgentCount} deadline dalam 48 jam</span>
          </div>
        </header>

        {supabaseConfigMissing && (
          <section className="notice notice-warning" role="alert">
            <strong>Supabase belum dikonfigurasi.</strong>
            <span>Salin .env.example menjadi .env.local, lalu isi URL project dan publishable key.</span>
          </section>
        )}

        {errorMessage && (
          <section className="notice notice-error" role="alert">
            <strong>Data tugas belum berhasil dimuat.</strong>
            <span>{errorMessage}. Periksa koneksi dan kebijakan akses tabel, lalu coba lagi.</span>
            <button className="text-button" type="button" onClick={() => setRefreshKey((key) => key + 1)}>Coba lagi</button>
          </section>
        )}

        <section className="focus-panel" aria-labelledby="focus-heading">
          <div className="focus-panel-label">
            <span className="focus-orbit" aria-hidden="true" />
            <span id="focus-heading">Berikutnya</span>
          </div>
          {upcomingTasks.length > 0 ? (
            <div className="focus-panel-content">
              <div className="focus-task-main">
                <p>{upcomingTasks[0].mata_kuliah} <span>{upcomingTasks[0].jenis}</span></p>
                <h2>{upcomingTasks[0].judul}</h2>
                <time dateTime={upcomingTasks[0].deadline}>{deadlineText(upcomingTasks[0].deadline)}</time>
                <div className="focus-task-links">
                  <ExternalTaskLink href={safeHttpUrl(upcomingTasks[0].link_vclass)}>Buka VClass</ExternalTaskLink>
                  <ExternalTaskLink href={safeHttpUrl(upcomingTasks[0].link_pengumpulan)}>Pengumpulan</ExternalTaskLink>
                </div>
              </div>
              <div className="focus-countdown">
                <strong>{countdownText(upcomingTasks[0].deadline, now)}</strong>
                <span>menuju deadline</span>
              </div>
            </div>
          ) : (
            <div className="focus-panel-empty">
              <div>
                <h2>{loading ? "Menyiapkan daftar tugas" : "Tidak ada deadline mendatang"}</h2>
                <p>{loading ? "Tugas dari mata kuliahmu sedang dimuat." : "Semua tenggat yang tercatat sudah terlewati. Cek daftar terlewat atau kembali lagi nanti."}</p>
              </div>
              {!loading && overdueTasks.length > 0 && <button type="button" className="focus-link-button" onClick={() => setTaskView("overdue")}>Lihat tugas terlewat</button>}
            </div>
          )}
        </section>

        <DashboardMetrics taskCount={filteredTasks.length} nearCount={nearDeadlineCount} overdueCount={overdueTasks.length} loading={loading} />
        <NewlyOverdueNotice tasks={newlyOverdueTasks} />

        <div className="agenda-layout">
          <section className="agenda-main" aria-labelledby="agenda-title">
            <header className="agenda-heading">
              <div>
                <h2 id="agenda-title">Daftar tugas</h2>
                <p>{taskView === "upcoming" ? "Urut dari tenggat paling dekat." : "Tenggat yang sudah berlalu."}</p>
              </div>
              <div className="agenda-tabs" role="group" aria-label="Tampilan tugas">
                <button type="button" className={taskView === "upcoming" ? "is-current" : ""} onClick={() => setTaskView("upcoming")} aria-pressed={taskView === "upcoming"}>
                  Mendatang <span>{loading ? "—" : upcomingTasks.length}</span>
                </button>
                <button type="button" className={taskView === "overdue" ? "is-current" : ""} onClick={() => setTaskView("overdue")} aria-pressed={taskView === "overdue"}>
                  Terlewat <span>{loading ? "—" : overdueTasks.length}</span>
                </button>
              </div>
            </header>

            <div className="agenda-filters">
              <label className="agenda-search">
                <span aria-hidden="true">⌕</span>
                <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari tugas atau mata kuliah" aria-label="Cari tugas atau mata kuliah" />
                {search && <button type="button" onClick={() => setSearch("")} aria-label="Hapus pencarian">×</button>}
              </label>
              <label className="agenda-select">
                <span className="sr-only">Mata kuliah</span>
                <select value={courseFilter} onChange={(event) => setCourseFilter(event.target.value)}>
                  <option value="all">Semua mata kuliah</option>
                  {courseOptions.map((courseName) => <option value={courseName} key={courseName}>{courseName}</option>)}
                </select>
              </label>
              <label className="agenda-select">
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
              <div className="agenda-empty" role="status"><span className="loading-mark" /><strong>Memuat tugas</strong><p>Daftar tugas sedang disiapkan.</p></div>
            ) : visibleTasks.length > 0 ? (
              <div className="agenda-list">
                {visibleTasks.map((task) => <TaskRow key={task.id} task={task} now={now} overdue={taskView === "overdue"} />)}
              </div>
            ) : (
              <div className="agenda-empty">
                <strong>{filteredTasks.length === 0 ? "Tugas tidak ditemukan" : taskView === "upcoming" ? "Tidak ada deadline mendatang" : "Tidak ada tugas terlewat"}</strong>
                <p>{filteredTasks.length === 0 ? "Ubah kata kunci atau hapus filter." : taskView === "upcoming" ? "Belum ada tenggat berikutnya di daftar." : "Tidak ada tugas dengan tenggat yang lewat."}</p>
                {(search || courseFilter !== "all" || typeFilter !== "all") && <button className="text-button" type="button" onClick={clearFilters}>Hapus filter</button>}
              </div>
            )}

            {!loading && selectedTasks.length > visibleTasks.length && (
              <p className="agenda-footnote">Menampilkan {visibleTasks.length} dari {selectedTasks.length} tugas.</p>
            )}
          </section>

          <aside className="course-shelf" aria-labelledby="course-shelf-title">
            <header>
              <div>
                <h2 id="course-shelf-title">Mata kuliah</h2>
                <p>Pilih mata kuliah untuk menyaring agenda.</p>
              </div>
              <span>{loading ? "—" : courseOptions.length}</span>
            </header>
            {loading ? (
              <p className="course-shelf-empty">Memuat mata kuliah…</p>
            ) : courseOptions.filter((name) => (taskCountsByCourse.get(name) ?? 0) > 0).length === 0 ? (
              <p className="course-shelf-empty">Belum ada mata kuliah dengan tugas aktif.</p>
            ) : (
              <div className="course-shelf-list">
                {courseOptions.filter((name) => (taskCountsByCourse.get(name) ?? 0) > 0).map((courseName, index) => {
                  const course = courses.find((item) => item.nama === courseName);
                  return (
                    <button key={courseName} type="button" className={"course-shelf-row" + (courseFilter === courseName ? " is-selected" : "")} onClick={() => setCourseFilter(courseFilter === courseName ? "all" : courseName)} aria-pressed={courseFilter === courseName}>
                      <span className={"course-swatch course-swatch-" + (index % 5)} />
                      <span className="course-shelf-copy"><strong>{courseName}</strong><small>{course ? "Semester " + course.semester : "Mata kuliah"}</small></span>
                      <span className="course-shelf-count">{taskCountsByCourse.get(courseName) ?? 0}</span>
                    </button>
                  );
                })}
              </div>
            )}
            {courseFilter !== "all" && <button className="clear-course-filter" type="button" onClick={() => setCourseFilter("all")}>Tampilkan semua mata kuliah</button>}
          </aside>
        </div>

        <footer className="desk-footer">
          <span>Tugas Kuliah</span>
          <span>{connectionLabel}</span>
        </footer>
      </div>

    </main>
    </>
  );
}

export default App;
