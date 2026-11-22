import { useEffect, useState } from "react";
import type { MouseEvent, ReactNode } from "react";

export type AppPage = "home" | "calendar" | "archive" | "admin";

type PrimaryPage = Exclude<AppPage, "admin">;
type Theme = "light" | "dark";

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

const THEME_STORAGE_KEY = "tugas-kuliah-theme";

const primaryItems: { page: PrimaryPage; label: string; icon: "home" | "calendar" | "archive" }[] = [
  { page: "home", label: "Tugas", icon: "home" },
  { page: "calendar", label: "Kalender", icon: "calendar" },
  { page: "archive", label: "Arsip Modul", icon: "archive" },
];

function initialTheme(): Theme {
  if (typeof document !== "undefined") {
    const applied = document.documentElement.dataset.theme;
    if (applied === "light" || applied === "dark") return applied;
  }

  try {
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    // Theme switching still works for this session when storage is unavailable.
  }

  return "light";
}

function NavIcon({ name }: { name: "home" | "calendar" | "archive" | "more" }) {
  if (name === "home") {
    return <svg className="app-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m3 10 9-7 9 7" /><path d="M5.5 9v11h13V9M9.5 20v-6h5v6" /></svg>;
  }
  if (name === "calendar") {
    return <svg className="app-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="5" width="17" height="16" rx="2" /><path d="M7.5 3v4M16.5 3v4M3.5 9.5h17M8 13h2M14 13h2M8 17h2" /></svg>;
  }
  if (name === "archive") {
    return <svg className="app-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16v4H4zM5.5 8v12h13V8M9 12h6" /></svg>;
  }
  return <svg className="app-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /></svg>;
}

function ThemeIcon({ theme }: { theme: Theme }) {
  return theme === "dark" ? (
    <svg className="theme-toggle-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" />
    </svg>
  ) : (
    <svg className="theme-toggle-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20.2 15.1A8.5 8.5 0 0 1 8.9 3.8 8.6 8.6 0 1 0 20.2 15.1Z" />
    </svg>
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
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')?.setAttribute(
      "content",
      theme === "dark" ? "#191b1a" : "#f5f5f1",
    );

    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // The selected theme remains active until the page is closed.
    }
  }, [theme]);

  function refreshFromMenu(event: MouseEvent<HTMLButtonElement>) {
    onRefresh?.();
    event.currentTarget.closest("details")?.removeAttribute("open");
  }

  return (
    <>
      <header className="app-header app-navigation-header">
        <a
          className="wordmark"
          href="/"
          aria-label="Tugas Kuliah, kembali ke daftar tugas"
          onClick={(event) => { event.preventDefault(); onNavigate("home"); }}
        >
          <span className="wordmark-symbol" aria-hidden="true">t<span>.</span></span>
          <span className="wordmark-name">Tugas Kuliah</span>
        </a>

        <nav className="app-primary-nav" aria-label="Navigasi utama">
          {primaryItems.map((item) => (
            <button
              key={item.page}
              type="button"
              className={"app-nav-item" + (currentPage === item.page ? " is-current" : "")}
              aria-current={currentPage === item.page ? "page" : undefined}
              onClick={() => onNavigate(item.page)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="app-navigation-actions">
          {connectionLabel && (
            <span className={"connection-state app-nav-connection" + (connectionWarning ? " is-warning" : "")}>
              <span className="connection-dot" aria-hidden="true" />
              {connectionLabel}
            </span>
          )}
          <button
            className="theme-toggle"
            type="button"
            onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
            aria-label={theme === "dark" ? "Ganti ke tema terang" : "Ganti ke tema gelap"}
            title={theme === "dark" ? "Ganti ke tema terang" : "Ganti ke tema gelap"}
          >
            <ThemeIcon theme={theme} />
            <span>{theme === "dark" ? "Tema terang" : "Tema gelap"}</span>
          </button>
          {onRefresh && (
            <button
              className="refresh-button app-nav-refresh"
              type="button"
              onClick={onRefresh}
              disabled={refreshDisabled}
              aria-label="Muat ulang data"
              title="Muat ulang data"
            >
              ↻
            </button>
          )}
          <details className="app-more-menu">
            <summary aria-label="Buka menu lainnya"><NavIcon name="more" /><span>Lainnya</span></summary>
            <div className="app-more-popover">
              {adminEmail && <p className="app-more-email" title={adminEmail}>{adminEmail}</p>}
              <button type="button" className={currentPage === "admin" ? "is-current" : ""} onClick={() => onNavigate("admin")}>
                <span className="app-more-item-icon" aria-hidden="true">⚙</span><span>Panel Admin</span>
              </button>
              {onRefresh && (
                <button type="button" className="app-more-refresh" onClick={refreshFromMenu} disabled={refreshDisabled}>
                  <span className="app-more-item-icon" aria-hidden="true">↻</span><span>Muat ulang data</span>
                </button>
              )}
              {onSignOut && (
                <button type="button" onClick={onSignOut}>
                  <span className="app-more-item-icon" aria-hidden="true">↪</span><span>Keluar dari admin</span>
                </button>
              )}
            </div>
          </details>
          {trailingActions}
        </div>
      </header>

      <nav className="app-bottom-nav" aria-label="Navigasi utama mobile">
        {primaryItems.map((item) => (
          <button
            key={item.page}
            type="button"
            className={"app-bottom-nav-item" + (currentPage === item.page ? " is-current" : "")}
            aria-current={currentPage === item.page ? "page" : undefined}
            onClick={() => onNavigate(item.page)}
          >
            <NavIcon name={item.icon} />
            <span>{item.label === "Arsip Modul" ? "Arsip" : item.label}</span>
          </button>
        ))}
      </nav>
    </>
  );
}
