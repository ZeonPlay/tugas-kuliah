import { useEffect, useMemo, useState } from "react";
import { supabase, supabaseConfigMissing } from "./lib/supabase";

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

const DATETIME_FORMAT = new Intl.DateTimeFormat("id-ID", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Asia/Jakarta",
});

const DATE_FORMAT = new Intl.DateTimeFormat("id-ID", {
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
  return Number.isNaN(date.getTime()) ? "Tanggal tidak valid" : DATETIME_FORMAT.format(date) + " WIB";
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

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [search, setSearch] = useState("");
  const [courseFilter, setCourseFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
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
      const matchesSearch = !keyword || searchable.some((value) =>
        value.toLocaleLowerCase("id-ID").includes(keyword),
      );
      const matchesCourse = courseFilter === "all" || task.mata_kuliah === courseFilter;
      const matchesType = typeFilter === "all" || task.jenis === typeFilter;
      return matchesSearch && matchesCourse && matchesType;
    });
  }, [tasks, search, courseFilter, typeFilter]);

  const upcomingTasks = useMemo(
    () => filteredTasks
      .filter((task) => new Date(task.deadline).getTime() >= now)
      .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime())
      .slice(0, 5),
    [filteredTasks, now],
  );

  const overdueCount = filteredTasks.filter((task) => new Date(task.deadline).getTime() < now).length;
  const urgentCount = filteredTasks.filter((task) => {
    const difference = new Date(task.deadline).getTime() - now;
    return difference >= 0 && difference <= 48 * 60 * 60 * 1000;
  }).length;

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

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Tugas Kuliah - Beranda">
          <span className="brand-mark" aria-hidden="true">T</span>
          <span className="brand-copy">
            <strong>Tugas Kuliah</strong>
            <small>SI · Ruang belajar bersama</small>
          </span>
        </a>
        <div className="topbar-date"><span className="live-dot" />{DATE_FORMAT.format(new Date(now))}</div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">DASHBOARD MAHASISWA</p>
          <h1>Halo, selamat datang.</h1>
          <p className="hero-description">
            Pantau deadline tugas dan siapkan langkah berikutnya tanpa terburu-buru.
          </p>
        </div>
        <div className="hero-decoration" aria-hidden="true">
          <span className="decoration-ring ring-one" />
          <span className="decoration-ring ring-two" />
          <span className="decoration-cap">✳</span>
        </div>
      </section>

      {supabaseConfigMissing && (
        <section className="notice notice-warning" role="alert">
          <strong>Supabase belum dikonfigurasi.</strong>
          <span>
            Salin file .env.example menjadi .env.local, lalu isi VITE_SUPABASE_URL dan
            VITE_SUPABASE_ANON_KEY menggunakan URL serta publishable/anon key project.
          </span>
        </section>
      )}

      {errorMessage && (
        <section className="notice notice-error" role="alert">
          <strong>Gagal memuat data dari Supabase.</strong>
          <span>{errorMessage}</span>
          <button className="button button-secondary" onClick={() => setRefreshKey((key) => key + 1)}>
            Coba lagi
          </button>
        </section>
      )}

      <section className="stats-grid" aria-label="Ringkasan tugas">
        <article className="stat-card">
          <span className="stat-icon icon-blue">▤</span>
          <span className="stat-label">Tugas ditampilkan</span>
          <strong className="stat-value">{loading ? "—" : filteredTasks.length}</strong>
          <span className="stat-note">Sesuai filter saat ini</span>
        </article>
        <article className="stat-card">
          <span className="stat-icon icon-amber">◷</span>
          <span className="stat-label">Deadline 48 jam</span>
          <strong className="stat-value">{loading ? "—" : urgentCount}</strong>
          <span className="stat-note">Perlu segera diperhatikan</span>
        </article>
        <article className="stat-card">
          <span className="stat-icon icon-rose">↗</span>
          <span className="stat-label">Sudah terlewat</span>
          <strong className="stat-value">{loading ? "—" : overdueCount}</strong>
          <span className="stat-note">Tetap tersimpan untuk ditinjau</span>
        </article>
      </section>

      <div className="content-grid">
        <section className="panel task-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">YANG PERLU DIKERJAKAN</p>
              <h2>Deadline terdekat</h2>
            </div>
            <button className="icon-button" type="button" onClick={() => setRefreshKey((key) => key + 1)}
              aria-label="Muat ulang data" title="Muat ulang data">↻</button>
          </div>

          <div className="filters">
            <label className="search-box">
              <span aria-hidden="true">⌕</span>
              <input value={search} onChange={(event) => setSearch(event.target.value)}
                placeholder="Cari judul, mata kuliah, ketentuan..." aria-label="Cari tugas" />
            </label>
            <div className="filter-row">
              <label className="filter-control">
                <span>Mata kuliah</span>
                <select value={courseFilter} onChange={(event) => setCourseFilter(event.target.value)}>
                  <option value="all">Semua mata kuliah</option>
                  {courses.map((course) => <option value={course.nama} key={course.id}>{course.nama}</option>)}
                </select>
              </label>
              <label className="filter-control">
                <span>Jenis tugas</span>
                <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
                  <option value="all">Semua jenis</option>
                  <option value="Teori">Teori</option>
                  <option value="Praktikum">Praktikum</option>
                  <option value="Quiz">Quiz</option>
                  <option value="Ujian">Ujian</option>
                </select>
              </label>
            </div>
          </div>

          {loading ? (
            <div className="empty-state"><span className="loading-spinner" /><strong>Memuat tugas...</strong><span>Menghubungkan dashboard ke Supabase.</span></div>
          ) : upcomingTasks.length > 0 ? (
            <div className="task-list">
              {upcomingTasks.map((task) => (
                <article className="task-card" key={task.id}>
                  <div className="task-meta">
                    <span className="course-pill">{task.mata_kuliah || "Tanpa mata kuliah"}</span>
                    <span className="type-label">{task.jenis}</span>
                  </div>
                  <h3>{task.judul || "Tugas tanpa judul"}</h3>
                  {task.ketentuan && <p className="task-description">{task.ketentuan}</p>}
                  <div className="deadline-line">
                    <span aria-hidden="true">◷</span>
                    <span>{deadlineText(task.deadline)}</span>
                    <span className="countdown">{countdownText(task.deadline, now)}</span>
                  </div>
                  <div className="task-links">
                    <ExternalTaskLink href={safeHttpUrl(task.link_vclass)}>Buka VClass ↗</ExternalTaskLink>
                    <ExternalTaskLink href={safeHttpUrl(task.link_pengumpulan)}>Pengumpulan ↗</ExternalTaskLink>
                    <ExternalTaskLink href={safeHttpUrl(task.file_soal)}>File soal ↗</ExternalTaskLink>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">✓</span>
              <strong>{filteredTasks.length === 0 ? "Belum ada tugas yang cocok" : "Tidak ada deadline mendatang"}</strong>
              <span>{filteredTasks.length === 0 ? "Coba ubah kata kunci atau filter mata kuliah." : "Untuk sementara, kamu bisa bernapas lega."}</span>
              <button className="button button-secondary" type="button" onClick={clearFilters}>Reset filter</button>
            </div>
          )}

          {!loading && filteredTasks.length > upcomingTasks.length && (
            <p className="panel-footnote">
              Menampilkan {upcomingTasks.length} deadline mendatang dari {filteredTasks.length} tugas.
              {overdueCount > 0 ? " Ada " + overdueCount + " tugas yang sudah lewat." : ""}
            </p>
          )}
        </section>

        <aside className="panel course-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">KATALOG AKADEMIK</p>
              <h2>Mata kuliah</h2>
            </div>
            <span className="heading-count">{courses.length}</span>
          </div>
          {loading ? (
            <p className="muted-text">Memuat katalog...</p>
          ) : courses.length === 0 ? (
            <p className="muted-text">Belum ada mata kuliah aktif di katalog.</p>
          ) : (
            <div className="course-list">
              {courses.filter((course) => (taskCountsByCourse.get(course.nama) ?? 0) > 0).map((course, index) => (
                <button
                  className={"course-row" + (courseFilter === course.nama ? " is-selected" : "")}
                  key={course.id}
                  type="button"
                  onClick={() => setCourseFilter(courseFilter === course.nama ? "all" : course.nama)}
                >
                  <span className={"course-marker marker-" + (index % 5)} />
                  <span className="course-row-name">
                    <strong>{course.nama}</strong>
                    <small>Semester {course.semester} · {course.kategori}</small>
                  </span>
                  <span className="course-count">{taskCountsByCourse.get(course.nama) ?? 0}</span>
                </button>
              ))}
            </div>
          )}
          <div className="course-panel-footer"><span className="live-dot" /><span>Data tersimpan di Supabase</span></div>
        </aside>
      </div>

      <footer className="page-footer">
        <span>© {new Date(now).getFullYear()} Tugas Kuliah</span>
        <span>Dibuat untuk membantu kuliah terasa lebih teratur.</span>
      </footer>
    </main>
  );
}

export default App;
