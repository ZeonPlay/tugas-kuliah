import { useMemo, useRef, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import interactionPlugin from "@fullcalendar/react/interaction";
import type { ComponentRef } from "react";
import type { ReactNode } from "react";
import "@fullcalendar/react/skeleton.css";

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

type CalendarPageProps = {
  tasks: Task[];
  loading: boolean;
  errorMessage: string;
  onBack: () => void;
  onOpenAdmin: () => void;
  onRefresh: () => void;
};

const DATE_FORMAT = new Intl.DateTimeFormat("id-ID", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "Asia/Jakarta",
});

const DEADLINE_FORMAT = new Intl.DateTimeFormat("id-ID", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Asia/Jakarta",
  hourCycle: "h23",
});

const WEEKDAY_LABELS = ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"];

function wibDateKey(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jakarta",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const get = (type: string) => parts.find((part) => part.type === type)?.value ?? "";
  return get("year") + "-" + get("month") + "-" + get("day");
}

function todayWib(): string {
  return wibDateKey(new Date());
}

function formatMonth(value: Date): string {
  return new Intl.DateTimeFormat("id-ID", {
    month: "long",
    year: "numeric",
    timeZone: "Asia/Jakarta",
  }).format(value);
}

function safeHttpUrl(value: string | null): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}

function OutboundLink({ href, children }: { href: string | null; children: ReactNode }) {
  if (!href) return null;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children} <span aria-hidden="true">↗</span>
    </a>
  );
}

function CalendarTask({ task, now }: { task: Task; now: number }) {
  const overdue = new Date(task.deadline).getTime() < now;
  const deadline = new Date(task.deadline);

  return (
    <article className={"calendar-task" + (overdue ? " is-overdue" : "")}>
      <div className="calendar-task-time">
        <strong>{DEADLINE_FORMAT.format(deadline)}</strong>
        <span>WIB</span>
      </div>
      <div className="calendar-task-copy">
        <div className="calendar-task-meta">
          <span>{task.mata_kuliah || "Tanpa mata kuliah"}</span>
          <span aria-hidden="true">·</span>
          <span>{task.jenis}</span>
        </div>
        <h3>{task.judul || "Tugas tanpa judul"}</h3>
        {overdue && <span className="calendar-overdue-label">Deadline terlewat</span>}
        <div className="calendar-task-links">
          <OutboundLink href={safeHttpUrl(task.link_vclass)}>VClass</OutboundLink>
          <OutboundLink href={safeHttpUrl(task.link_pengumpulan)}>Pengumpulan</OutboundLink>
          <OutboundLink href={safeHttpUrl(task.file_soal)}>File soal</OutboundLink>
        </div>
      </div>
    </article>
  );
}

export default function CalendarPage({
  tasks,
  loading,
  errorMessage,
  onBack,
  onOpenAdmin,
  onRefresh,
}: CalendarPageProps) {
  const calendarRef = useRef<ComponentRef<typeof FullCalendar> | null>(null);
  const [selectedDate, setSelectedDate] = useState(todayWib);
  const [monthTitle, setMonthTitle] = useState(() => formatMonth(new Date()));
  const [now, setNow] = useState(() => Date.now());

  const countsByDate = useMemo(() => {
    const counts = new Map<string, number>();
    for (const task of tasks) {
      const key = wibDateKey(task.deadline);
      if (key) counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return counts;
  }, [tasks]);

  const calendarEvents = useMemo(
    () =>
      tasks.flatMap((task) => {
        const date = wibDateKey(task.deadline);
        if (!date) return [];
        return [{
          id: task.id,
          title: task.judul || "Tugas tanpa judul",
          start: date,
          allDay: true,
          extendedProps: { task },
        }];
      }),
    [tasks],
  );

  const selectedTasks = useMemo(
    () =>
      tasks
        .filter((task) => wibDateKey(task.deadline) === selectedDate)
        .sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime()),
    [tasks, selectedDate],
  );

  function selectDate(value: string) {
    setSelectedDate(value.slice(0, 10));
  }

  function goToToday() {
    const today = todayWib();
    setSelectedDate(today);
    calendarRef.current?.getApi().today();
  }

  function moveMonth(direction: "previous" | "next") {
    const api = calendarRef.current?.getApi();
    if (!api) return;
    if (direction === "previous") api.prev();
    else api.next();
  }

  return (
    <main className="app-shell calendar-page">
      <header className="app-header">
        <a className="wordmark" href="/" onClick={(event) => { event.preventDefault(); onBack(); }} aria-label="Kembali ke beranda">
          <span className="wordmark-symbol" aria-hidden="true">t<span>.</span></span>
          <span className="wordmark-name">tugas kuliah</span>
        </a>
        <div className="calendar-header-actions">
          <button className="calendar-nav-button" type="button" onClick={onBack}>Beranda</button>
          <button className="open-admin-button" type="button" onClick={onOpenAdmin}>Panel Admin <span aria-hidden="true">↗</span></button>
          <button className="refresh-button" type="button" onClick={() => { onRefresh(); setNow(Date.now()); }} aria-label="Muat ulang data" title="Muat ulang">↻</button>
        </div>
      </header>

      <section className="calendar-welcome">
        <div>
          <p className="welcome-kicker">AGENDA KULIAH <span aria-hidden="true">·</span> KALENDER</p>
          <h1>Semua deadline,<br className="calendar-wide-break" /> kelihatan jelas.</h1>
          <p className="welcome-copy">Pilih tanggal untuk melihat tugas yang harus dikumpulkan. Semua jam menggunakan WIB.</p>
        </div>
        <div className="calendar-summary-note" aria-live="polite">
          <strong>{tasks.length}</strong>
          <span>tugas tercatat</span>
          <span className="calendar-summary-divider" />
          <strong>{countsByDate.size}</strong>
          <span>hari dengan deadline</span>
        </div>
      </section>

      {errorMessage && (
        <section className="notice notice-error" role="alert">
          <strong>Data kalender belum berhasil dimuat.</strong>
          <span>{errorMessage}</span>
          <button className="text-button" type="button" onClick={onRefresh}>Coba lagi</button>
        </section>
      )}

      <section className="calendar-workspace" aria-label="Kalender dan daftar tugas">
        <div className="calendar-main">
          <div className="calendar-toolbar">
            <div>
              <p className="calendar-section-kicker">KALENDER AKADEMIK</p>
              <h2>{monthTitle}</h2>
            </div>
            <div className="calendar-toolbar-actions">
              <button type="button" className="calendar-nav-button calendar-today-button" onClick={goToToday}>Hari ini</button>
              <button type="button" className="calendar-arrow-button" onClick={() => moveMonth("previous")} aria-label="Bulan sebelumnya" title="Bulan sebelumnya">‹</button>
              <button type="button" className="calendar-arrow-button" onClick={() => moveMonth("next")} aria-label="Bulan berikutnya" title="Bulan berikutnya">›</button>
            </div>
          </div>

          {loading ? (
            <div className="calendar-loading" role="status">
              <span className="loading-mark" />
              <strong>Memuat deadline…</strong>
            </div>
          ) : (
            <div className="planner-calendar">
              <FullCalendar
                ref={calendarRef}
                plugins={[dayGridPlugin, interactionPlugin]}
                initialView="dayGridMonth"
                initialDate={selectedDate}
                headerToolbar={false}
                height="auto"
                contentHeight="auto"
                fixedWeekCount={false}
                firstDay={1}
                timeZone="Asia/Jakarta"
                events={calendarEvents}
                dateClick={(info) => selectDate(info.dateStr)}
                eventClick={(info) => {
                  const task = info.event.extendedProps.task as Task | undefined;
                  if (task) selectDate(wibDateKey(task.deadline));
                }}
                datesSet={(info) => setMonthTitle(formatMonth(info.view.currentStart))}
                dayHeaderContent={(info) => WEEKDAY_LABELS[info.date.getDay()]}
                dayCellTopContent={(info) => {
                  const key = wibDateKey(info.date);
                  const count = countsByDate.get(key) ?? 0;
                  return (
                    <span className="calendar-day-top">
                      <span className="calendar-day-number">{info.dayNumberText}</span>
                      {count > 0 && <span className="calendar-day-count">{count}</span>}
                    </span>
                  );
                }}
                eventContent={(info) => (
                  <span className="calendar-event-content" title={info.event.title}>
                    <span className="calendar-event-dot" aria-hidden="true" />
                    <span>{info.event.title}</span>
                  </span>
                )}
                dayMaxEvents={3}
                moreLinkContent={(info) => "+" + info.num + " lagi"}
                moreLinkClick="date"
                eventDisplay="block"
                displayEventTime={false}
                navLinks={false}
                selectable={false}
              />
              <p className="calendar-help">Klik tanggal atau nama tugas di kalender untuk melihat rincian deadline di samping.</p>
            </div>
          )}
        </div>

        <aside className="calendar-day-panel" aria-labelledby="selected-day-heading">
          <div className="selected-day-heading">
            <p className="calendar-section-kicker">AGENDA HARIAN</p>
            <h2 id="selected-day-heading">{DATE_FORMAT.format(new Date(selectedDate + "T12:00:00+07:00"))}</h2>
            <p>{selectedTasks.length === 1 ? "1 tugas jatuh tempo" : selectedTasks.length + " tugas jatuh tempo"}</p>
          </div>

          {loading ? (
            <div className="calendar-day-empty"><span className="loading-mark" /><span>Memuat daftar tugas…</span></div>
          ) : selectedTasks.length > 0 ? (
            <div className="calendar-day-tasks">
              {selectedTasks.map((task) => <CalendarTask key={task.id} task={task} now={now} />)}
            </div>
          ) : (
            <div className="calendar-day-empty">
              <span className="calendar-empty-mark" aria-hidden="true">✳</span>
              <strong>Belum ada deadline</strong>
              <span>Tanggal ini kosong. Pilih hari lain atau nikmati waktu luangmu.</span>
            </div>
          )}
          <button className="calendar-today-link" type="button" onClick={goToToday}>Lihat agenda hari ini <span aria-hidden="true">→</span></button>
        </aside>
      </section>

      <footer className="app-footer">
        <span className="footer-wordmark">tugas kuliah<span>.</span></span>
        <span>Kalender akademik · Semua jam dalam WIB</span>
        <span className="footer-status"><span className="connection-dot" />{errorMessage ? "Koneksi bermasalah" : loading ? "Memuat data" : "Data tersinkron"}</span>
      </footer>
    </main>
  );
}
