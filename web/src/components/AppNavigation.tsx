import { useEffect, useState } from "react";
import type { ReactNode } from "react";

export type AppPage = "home" | "calendar" | "archive" | "admin";
type Theme = "dark" | "light";

type Props = {
  currentPage: AppPage;
  onNavigate: (page: AppPage) => void;
  connectionLabel?: string;
  connectionWarning?: boolean;
  onRefresh?: () => void;
  refreshDisabled?: boolean;
  adminEmail?: string | null;
  onSignOut?: () => void;
  trailingActions?: ReactNode;
};

const THEME_KEY = "tugas-kuliah-theme";

const items: { page: AppPage; label: string; shortLabel: string; icon: "tasks" | "calendar" | "books" | "settings" }[] = [
  { page: "home", label: "Tugas", shortLabel: "Tugas", icon: "tasks" },
  { page: "calendar", label: "Kalender", shortLabel: "Kalender", icon: "calendar" },
  { page: "archive", label: "Arsip materi", shortLabel: "Materi", icon: "books" },
  { page: "admin", label: "Panel admin", shortLabel: "Admin", icon: "settings" },
];

function readTheme(): Theme {
  if (typeof document !== "undefined") {
    const current = document.documentElement.dataset.theme;
    if (current === "dark" || current === "light") return current;
  }
  try {
    const saved = window.localStorage.getItem(THEME_KEY);
    if (saved === "dark" || saved === "light") return saved;
  } catch {
    // Use the default when storage is unavailable.
  }
  return "dark";
}

function Glyph({ name }: { name: "tasks" | "calendar" | "books" | "settings" | "sun" | "moon" | "refresh" | "brand" }) {
  const common = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  const paths: Record<typeof name, ReactNode> = {
    tasks: <><path d="M8 6h12M8 12h12M8 18h12" /><path d="m3 6 .8.8L5.5 5M3 12l.8.8L5.5 11M3 18l.8.8L5.5 17" /></>,
    calendar: <><rect x="3.5" y="5" width="17" height="16" rx="2.2" /><path d="M7.5 3.5v3M16.5 3.5v3M3.5 9.5h17M8 13h2M14 13h2M8 17h2" /></>,
    books: <><path d="M4 4.5h11a2 2 0 0 1 2 2V20H6a2 2 0 0 1-2-2V4.5Z" /><path d="M17 7h2a1.5 1.5 0 0 1 1.5 1.5V20H17M7.5 8.5h6M7.5 12h6" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="m19.4 15 .1.1a1.8 1.8 0 0 1-2.5 2.5l-.1-.1a1.8 1.8 0 0 0-3 .9v.2a1.8 1.8 0 0 1-3.6 0v-.2a1.8 1.8 0 0 0-3-.9l-.1.1a1.8 1.8 0 0 1-2.5-2.5l.1-.1a1.8 1.8 0 0 0-.9-3h-.2a1.8 1.8 0 0 1 0-3.6h.2a1.8 1.8 0 0 0 .9-3l-.1-.1a1.8 1.8 0 0 1 2.5-2.5l.1.1a1.8 1.8 0 0 0 3-.9v-.2a1.8 1.8 0 0 1 3.6 0v.2a1.8 1.8 0 0 0 3 .9l.1-.1a1.8 1.8 0 0 1 2.5 2.5l-.1.1a1.8 1.8 0 0 0 .9 3h.2a1.8 1.8 0 0 1 0 3.6h-.2a1.8 1.8 0 0 0-.9 3Z" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" /></>,
    moon: <path d="M20.2 15.1A8.5 8.5 0 0 1 8.9 3.8 8.6 8.6 0 1 0 20.2 15.1Z" />,
    refresh: <><path d="M20 7v5h-5M4 17v-5h5" /><path d="M5.5 9a7 7 0 0 1 12-2L20 12M4 12l2.5 5a7 7 0 0 0 12-2" /></>,
    brand: <><path d="M4 6.5 12 3l8 3.5v11L12 21l-8-3.5v-11Z" /><path d="M8 9h8M8 12.5h8M8 16h5" /></>,
  };

  return <svg className="study-icon" viewBox="0 0 24 24" aria-hidden="true" {...common}>{paths[name]}</svg>;
}

function Brand() {
  return (
    <span className="study-brand">
      <span className="study-brand-mark"><Glyph name="brand" /></span>
      <span className="study-brand-copy">
        <strong>Tugas Kuliah</strong>
        <small>Ruang belajarmu</small>
      </span>
    </span>
  );
}

function ThemeButton({ theme, onToggle, compact = false }: { theme: Theme; onToggle: () => void; compact?: boolean }) {
  const label = theme === "dark" ? "Gunakan tema terang" : "Gunakan tema gelap";
  return (
    <button className={compact ? "theme-button theme-button-compact" : "theme-button"} type="button" onClick={onToggle} aria-label={label} title={label} aria-pressed={theme === "dark"}>
      <Glyph name={theme === "dark" ? "sun" : "moon"} />
      {!compact && <span>{theme === "dark" ? "Tema terang" : "Tema gelap"}</span>}
    </button>
  );
}

function PageLink({ page, currentPage, onNavigate, mobile = false }: {
  page: AppPage;
  currentPage: AppPage;
  onNavigate: (page: AppPage) => void;
  mobile?: boolean;
}) {
  const item = items.find((entry) => entry.page === page);
  if (!item) return null;
  const active = currentPage === page;
  return (
    <button
      className={(mobile ? "mobile-link" : "study-link") + (active ? " is-active" : "")}
      type="button"
      onClick={() => onNavigate(page)}
      aria-current={active ? "page" : undefined}
    >
      <Glyph name={item.icon} />
      <span>{mobile ? item.shortLabel : item.label}</span>
    </button>
  );
}

export default function AppNavigation({
  currentPage,
  onNavigate,
  connectionLabel,
  connectionWarning = false,
  onRefresh,
  refreshDisabled = false,
  adminEmail,
  onSignOut,
  trailingActions,
}: Props) {
  const [theme, setTheme] = useState<Theme>(readTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')?.setAttribute(
      "content",
      theme === "dark" ? "#172631" : "#F2F5F3",
    );
    try {
      window.localStorage.setItem(THEME_KEY, theme);
    } catch {
      // The current page still uses the selected theme.
    }
  }, [theme]);

  const toggleTheme = () => setTheme((current) => current === "dark" ? "light" : "dark");

  return (
    <>
      <aside className="study-sidebar" aria-label="Navigasi utama">
        <a className="brand-link" href="/" onClick={(event) => { event.preventDefault(); onNavigate("home"); }}>
          <Brand />
        </a>

        <div className="study-nav-heading">Ruang kerja</div>
        <nav className="study-nav">
          {items.map((item) => <PageLink key={item.page} page={item.page} currentPage={currentPage} onNavigate={onNavigate} />)}
        </nav>

        <div className="study-sidebar-spacer" />
        {adminEmail && <div className="study-account" title={adminEmail}>{adminEmail}</div>}

        <div className="study-sidebar-footer">
          {connectionLabel && (
            <div className={"sync-indicator" + (connectionWarning ? " is-warning" : "")}>
              <span className="sync-dot" />
              <span>{connectionLabel}</span>
            </div>
          )}
          <ThemeButton theme={theme} onToggle={toggleTheme} />
          {onRefresh && (
            <button className="sidebar-tool" type="button" onClick={onRefresh} disabled={refreshDisabled}>
              <Glyph name="refresh" /><span>Muat ulang data</span>
            </button>
          )}
          {onSignOut && (
            <button className="sidebar-tool sign-out-tool" type="button" onClick={onSignOut}>
              <span className="sign-out-glyph" aria-hidden="true">↗</span><span>Keluar dari admin</span>
            </button>
          )}
          {trailingActions}
        </div>
      </aside>

      <header className="mobile-topbar">
        <a href="/" onClick={(event) => { event.preventDefault(); onNavigate("home"); }}><Brand /></a>
        <ThemeButton theme={theme} onToggle={toggleTheme} compact />
      </header>

      <nav className="mobile-dock" aria-label="Navigasi utama">
        {items.map((item) => <PageLink key={item.page} page={item.page} currentPage={currentPage} onNavigate={onNavigate} mobile />)}
      </nav>
    </>
  );
}
