import type { MouseEvent, ReactNode } from "react";

export type AppPage = "home" | "calendar" | "archive" | "admin";

type PrimaryPage = Exclude<AppPage, "admin">;

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

const primaryItems: { page: PrimaryPage; label: string; icon: "home" | "calendar" | "archive" }[] = [
  { page: "home", label: "Beranda", icon: "home" },
  { page: "calendar", label: "Kalender", icon: "calendar" },
  { page: "archive", label: "Arsip Modul", icon: "archive" },
];

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
          aria-label="Tugas Kuliah, kembali ke beranda"
          onClick={(event) => { event.preventDefault(); onNavigate("home"); }}
        >
          <span className="wordmark-symbol" aria-hidden="true">t<span>.</span></span>
          <span className="wordmark-name">tugas kuliah</span>
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
