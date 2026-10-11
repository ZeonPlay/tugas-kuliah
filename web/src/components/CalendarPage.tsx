import { useEffect, useMemo, useRef, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import listPlugin from "@fullcalendar/react/list";
import interactionPlugin from "@fullcalendar/react/interaction";
import type { ComponentRef, ReactNode } from "react";
import pulseTheme from "@fullcalendar/react/themes/pulse";
import "@fullcalendar/react/skeleton.css";
import "@fullcalendar/react/themes/pulse/theme.css";
import "@fullcalendar/react/themes/pulse/palettes/red.css";
import MarkdownContent from "./MarkdownContent";
import AppNavigation, { type AppPage } from "./AppNavigation";

type Task = {
  id: string; judul: string; mata_kuliah: string; jenis: string; deadline: string;
  ketentuan: string | null; link_vclass: string | null; link_pengumpulan: string | null; file_soal: string | null;
};
type Props = {
  tasks: Task[]; loading: boolean; errorMessage: string;
  onNavigate: (page: AppPage) => void; onRefresh: () => void;
};
type CalendarView = "dayGridMonth" | "listMonth";

const DATE_FORMAT = new Intl.DateTimeFormat("id-ID", {
  weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "Asia/Jakarta",
});
const DEADLINE_FORMAT = new Intl.DateTimeFormat("id-ID", {
  hour: "2-digit", minute: "2-digit", timeZone: "Asia/Jakarta", hourCycle: "h23",
});
const KNOWN_TYPES = ["Praktikum", "Teori", "Quiz", "Ujian"];

function dateKey(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jakarta", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(date);
  const get = (type: string) => parts.find((part) => part.type === type)?.value ?? "";
  return get("year") + "-" + get("month") + "-" + get("day");
}
function todayWib(): string { return dateKey(new Date()); }
function nextDateKey(key: string): string {
  const [year, month, day] = key.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day + 1));
  return [date.getUTCFullYear(), String(date.getUTCMonth() + 1).padStart(2, "0"), String(date.getUTCDate()).padStart(2, "0")].join("-");
}
function safeUrl(value: string | null): string | null {
  if (!value) return null;
  try { const url = new URL(value); return url.protocol === "http:" || url.protocol === "https:" ? url.href : null; }
  catch { return null; }
}
function Link({ href, children }: { href: string | null; children: ReactNode }) {
  return href ? <a href={href} target="_blank" rel="noopener noreferrer">{children} <span aria-hidden="true">↗</span></a> : null;
}

function CalendarTask({ task, now }: { task: Task; now: number }) {
  const overdue = new Date(task.deadline).getTime() < now;
  return (
    <article className={"calendar-task-card" + (overdue ? " is-overdue" : "")}>
      <div className="calendar-task-card-heading">
        <div>
          <p className="calendar-task-meta"><span>{task.mata_kuliah || "Tanpa mata kuliah"}</span><span aria-hidden="true">·</span><span>{task.jenis}</span></p>
          <h3>{task.judul || "Tugas tanpa judul"}</h3>
        </div>
        <time dateTime={task.deadline}>{DEADLINE_FORMAT.format(new Date(task.deadline))} WIB</time>
      </div>
      {overdue && <p className="calendar-overdue-label">Deadline sudah lewat</p>}
      {task.ketentuan && <MarkdownContent className="calendar-task-instructions" content={task.ketentuan} />}
      <div className="calendar-task-links">
        <Link href={safeUrl(task.link_vclass)}>VClass</Link>
        <Link href={safeUrl(task.link_pengumpulan)}>Pengumpulan</Link>
        <Link href={safeUrl(task.file_soal)}>File soal</Link>
      </div>
    </article>
  );
}

export default function CalendarPage({ tasks, loading, errorMessage, onNavigate, onRefresh }: Props) {
  const calendarRef = useRef<ComponentRef<typeof FullCalendar> | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [view, setView] = useState<CalendarView>("dayGridMonth");
  const [monthTitle, setMonthTitle] = useState(() => new Intl.DateTimeFormat("id-ID", { month: "long", year: "numeric", timeZone: "Asia/Jakarta" }).format(new Date()));
  const [selectedTypes, setSelectedTypes] = useState<string[] | null>(null);
  const [selectedCourses, setSelectedCourses] = useState<string[] | null>(null);
  const [now, setNow] = useState(Date.now);
  const [filterOpen, setFilterOpen] = useState(false);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  const types = useMemo(() => [...new Set([...KNOWN_TYPES, ...tasks.map((task) => task.jenis).filter(Boolean)])].sort((a,b) => a.localeCompare(b, "id-ID")), [tasks]);
  const courses = useMemo(() => [...new Set(tasks.map((task) => task.mata_kuliah).filter(Boolean))].sort((a,b) => a.localeCompare(b, "id-ID")), [tasks]);
  const filteredTasks = useMemo(() => tasks.filter((task) =>
    (selectedTypes === null || selectedTypes.includes(task.jenis)) &&
    (selectedCourses === null || selectedCourses.includes(task.mata_kuliah))
  ), [tasks, selectedTypes, selectedCourses]);

  const counts = useMemo(() => {
    const result = new Map<string, number>();
    for (const task of filteredTasks) {
      const key = dateKey(task.deadline);
      if (key) result.set(key, (result.get(key) ?? 0) + 1);
    }
    return result;
  }, [filteredTasks]);

  const events = useMemo(() => {
    // Month view intentionally contains ONLY one red count badge per date.
    // Individual task titles are exclusively supplied to the List view.
    const summaries = [...counts.entries()].map(([key, count]) => {
      // Gray out the date badge once at least one deadline on that date has passed.
      const overdue = filteredTasks.some((task) =>
        dateKey(task.deadline) === key && new Date(task.deadline).getTime() < now
      );
      return {
        id: "summary-" + key,
        start: key,
        end: nextDateKey(key),
        allDay: true,
        title: count + " deadline",
        color: overdue ? "#6b7280" : "#ef4444",
        contrastColor: "#ffffff",
        className: overdue ? "calendar-summary-event is-overdue" : "calendar-summary-event",
        extendedProps: { dateKey: key, eventKind: "summary", overdue },
      };
    });

    const details = filteredTasks.flatMap((task) => {
      const key = dateKey(task.deadline);
      if (!key) return [];
      const remaining = new Date(task.deadline).getTime() - now;
      const taskColor = remaining < 0 || remaining < 86_400_000
        ? "#ef4444"
        : remaining < 3 * 86_400_000
          ? "#f59e0b"
          : "#94a3b8";
      return [{
        id: "task-" + task.id,
        start: task.deadline,
        allDay: false,
        display: "list-item",
        title: (task.judul || "Tugas tanpa judul") + " · " + (task.mata_kuliah || "Tanpa mata kuliah"),
        color: taskColor,
        contrastColor: "#ffffff",
        className: "calendar-task-event",
        extendedProps: { dateKey: key, eventKind: "task", taskId: task.id },
      }];
    });

    return { month: summaries, list: details };
  }, [filteredTasks, counts, now]);

  const selectedTasks = useMemo(() => selectedDate
    ? filteredTasks.filter((task) => dateKey(task.deadline) === selectedDate).sort((a,b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime())
    : [], [filteredTasks, selectedDate]);
  const filtersActive = selectedTypes !== null || selectedCourses !== null;

  function toggleOption(option: string, options: string[], selected: string[] | null, update: (value: string[] | null) => void) {
    const current = selected ?? options;
    const next = current.includes(option) ? current.filter((item) => item !== option) : [...current, option];
    update(next.length === options.length ? null : next);
  }
  function resetFilters() { setSelectedTypes(null); setSelectedCourses(null); }
  function changeView(next: CalendarView) { calendarRef.current?.getApi().changeView(next); setView(next); }
  function moveMonth(direction: "previous" | "next") {
    const api = calendarRef.current?.getApi();
    if (!api) return;
    if (direction === "previous") api.prev();
    else api.next();
  }
  function goToToday() {
    calendarRef.current?.getApi().today();
    setSelectedDate(todayWib());
  }

  return (
    <main className="app-shell calendar-page">
      <AppNavigation currentPage="calendar" onNavigate={onNavigate} onRefresh={onRefresh} />

      <section className="calendar-page-heading">
        <h1>Kalender Tugas</h1>
        <p>Klik tanggal yang memiliki deadline untuk melihat detail tugas.</p>
      </section>

      {errorMessage && <section className="notice notice-error" role="alert"><strong>Data kalender belum berhasil dimuat.</strong><span>{errorMessage}</span><button className="text-button" type="button" onClick={onRefresh}>Coba lagi</button></section>}

      <details className="calendar-filter" open={filterOpen} onToggle={(event) => setFilterOpen(event.currentTarget.open)}>
        <summary>🔎 Filter kalender{filtersActive ? " · Filter aktif" : ""}</summary>
        <div className="calendar-filter-content">
          <fieldset className="calendar-filter-fieldset">
            <legend>Jenis</legend>
            <div className="calendar-filter-options">
              {types.map((type) => <label className="calendar-filter-option" key={type}>
                <input type="checkbox" checked={selectedTypes === null || selectedTypes.includes(type)} onChange={() => toggleOption(type, types, selectedTypes, setSelectedTypes)} />
                <span>{type}</span>
              </label>)}
            </div>
          </fieldset>
          <fieldset className="calendar-filter-fieldset">
            <legend>Mata kuliah</legend>
            <div className="calendar-filter-options calendar-course-filter-options">
              {courses.map((course) => <label className="calendar-filter-option" key={course}>
                <input type="checkbox" checked={selectedCourses === null || selectedCourses.includes(course)} onChange={() => toggleOption(course, courses, selectedCourses, setSelectedCourses)} />
                <span>{course}</span>
              </label>)}
            </div>
          </fieldset>
          {filtersActive && <button className="calendar-filter-reset" type="button" onClick={resetFilters}>Reset filter</button>}
        </div>
      </details>

      {loading ? <div className="calendar-loading" role="status"><span className="loading-mark" /><strong>Memuat deadline…</strong></div>
      : filteredTasks.length === 0 ? <div className="calendar-empty-result" role="status"><strong>{tasks.length === 0 ? "Belum ada tugas yang tercatat." : "Filter saat ini tidak menemukan tugas."}</strong>{tasks.length > 0 && <button className="quiet-button" type="button" onClick={resetFilters}>Tampilkan semua tugas</button>}</div>
      : <section className="calendar-surface" aria-label="Kalender deadline">
        <div className="calendar-native-toolbar">
          <div className="calendar-native-nav">
            <button type="button" className="calendar-nav-arrow" onClick={() => moveMonth("previous")} aria-label="Bulan sebelumnya" title="Bulan sebelumnya">‹</button>
            <button type="button" className="calendar-nav-arrow" onClick={() => moveMonth("next")} aria-label="Bulan berikutnya" title="Bulan berikutnya">›</button>
            <button type="button" className="calendar-today-button" onClick={goToToday}>Hari ini</button>
          </div>
          <h2>{monthTitle}</h2>
          <div className="calendar-view-switch" role="group" aria-label="Tampilan kalender">
            <button type="button" className={view === "dayGridMonth" ? "is-active" : ""} aria-pressed={view === "dayGridMonth"} onClick={() => changeView("dayGridMonth")}>Bulan</button>
            <button type="button" className={view === "listMonth" ? "is-active" : ""} aria-pressed={view === "listMonth"} onClick={() => changeView("listMonth")}>Daftar</button>
          </div>
        </div>
        <FullCalendar
          ref={calendarRef}
          plugins={[pulseTheme, dayGridPlugin, listPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          colorScheme="dark"
          dayCellClass="calendar-date-cell"
          dayHeaderClass="calendar-weekday-cell"
          initialDate={todayWib()}
          headerToolbar={false}
          height={520}
          contentHeight={520}
          expandRows
          fixedWeekCount={false}
          firstDay={1}
          timeZone="Asia/Jakarta"
          events={view === "dayGridMonth" ? events.month : events.list}
          datesSet={(info) => setMonthTitle(new Intl.DateTimeFormat("id-ID", { month: "long", year: "numeric", timeZone: "Asia/Jakarta" }).format(info.view.currentStart))}
          dayHeaderContent={(info) => new Intl.DateTimeFormat("id-ID", { weekday: "short", timeZone: "Asia/Jakarta" }).format(info.date).replace(/\./g, "")}
          dateClick={(info) => setSelectedDate(info.dateStr.slice(0, 10))}
          eventClick={(info) => {
            const key = info.event.extendedProps.dateKey as string | undefined;
            if (key) setSelectedDate(key);
          }}
          dayMaxEvents={3}
          moreLinkContent={(info) => "+" + info.num + " lagi"}
          moreLinkClick="date"
          displayEventTime={false}
          eventDisplay="block"
          views={{ listMonth: { listDayFormat: { weekday: "long", day: "numeric", month: "long" }, listDayAltFormat: false } }}
        />
        <p className="calendar-help">Tampilan Bulan menunjukkan jumlah deadline per hari. Pilih Daftar untuk melihat daftar deadline dalam bulan tersebut.</p>
      </section>}

      {!selectedDate ? <p className="calendar-selection-hint">Pilih tanggal yang memiliki deadline untuk melihat detail.</p> : (
        <section className="calendar-selected-day" aria-labelledby="selected-day-heading">
          <div className="calendar-selected-day-heading">
            <div><p className="calendar-section-kicker">AGENDA HARIAN</p><h2 id="selected-day-heading">Tugas pada {DATE_FORMAT.format(new Date(selectedDate + "T12:00:00+07:00"))}</h2><p>{selectedTasks.length} tugas jatuh tempo</p></div>
            <button className="calendar-nav-button" type="button" onClick={() => setSelectedDate(null)}>Tutup</button>
          </div>
          {selectedTasks.length === 0 ? <p className="calendar-no-tasks">Tidak ada tugas pada tanggal tersebut dengan filter saat ini.</p> : <div className="calendar-selected-task-list">{selectedTasks.map((task) => <CalendarTask key={task.id} task={task} now={now} />)}</div>}
        </section>
      )}

      <footer className="app-footer">
        <span className="footer-wordmark">tugas kuliah<span>.</span></span><span>Kalender akademik · Semua jam dalam WIB</span>
        <span className="footer-status"><span className="connection-dot" />{errorMessage ? "Koneksi bermasalah" : loading ? "Memuat data" : "Data tersinkron"}</span>
      </footer>
    </main>
  );
}
