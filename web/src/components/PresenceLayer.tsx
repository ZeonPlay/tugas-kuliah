import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import type { RealtimeChannel } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";

type RemoteCursor = {
  session_id: string;
  display_name: string;
  role: string;
  device: string;
  x: number;
  y: number;
  color: string;
  receivedAt: number;
  page: string;
};

type Position = { x: number; y: number; device: string };

const PAGE_LABELS: Record<string, string> = {
  home: "Beranda",
  calendar: "Kalender Tugas",
  archive: "Arsip Modul",
  admin: "Panel Admin",
};

const PRESENCE_CSS = `
.web-presence-layer {
  position: fixed; inset: 0; z-index: 9998; overflow: hidden;
  pointer-events: none; contain: layout style;
}
.web-presence-cursor {
  position: absolute; top: 0; left: 0; color: var(--web-cursor-color);
  will-change: transform, opacity; pointer-events: none;
  transition: opacity 180ms ease; filter: drop-shadow(0 1px 1px rgb(0 0 0 / 22%));
}
.web-presence-pointer { display: block; width: 18px; height: 22px; color: var(--web-cursor-color); }
.web-presence-pointer svg { display: block; width: 18px; height: 22px; overflow: visible; }
.web-presence-label {
  display: inline-flex; align-items: center; gap: 5px; margin: 1px 0 0 14px;
  max-width: 190px; padding: 3px 8px; border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 999px; background: var(--web-cursor-color); color: #fff;
  font: 600 10px/1.45 "DM Sans", sans-serif; white-space: nowrap;
  box-shadow: 0 2px 8px rgb(0 0 0 / 18%);
}
.web-presence-device { opacity: .8; font-size: 11px; }
.web-presence-name { overflow: hidden; text-overflow: ellipsis; }
.web-presence-cursor.is-stale { opacity: .3; }
.web-presence-cursor.is-other-page { opacity: .55; }
@media (prefers-reduced-motion: reduce) {
  .web-presence-cursor { transition: none; }
}
`;

function getSessionId(): string {
  const key = "zeon-presence-session-id";
  try {
    const previous = window.sessionStorage.getItem(key);
    if (previous) return previous;
    const next = typeof window.crypto?.randomUUID === "function"
      ? window.crypto.randomUUID()
      : `presence-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    window.sessionStorage.setItem(key, next);
    return next;
  } catch {
    return `presence-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  }
}

function cursorColor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
  return `hsl(${Math.abs(hash) % 360} 78% 48%)`;
}

function deviceIcon(device: string): string {
  return device === "touch" ? "●" : device === "pen" ? "✎" : "↖";
}

export default function PresenceLayer({ page }: { page: "home" | "calendar" | "archive" | "admin" }) {
  const [sessionId] = useState(getSessionId);
  const [cursors, setCursors] = useState<RemoteCursor[]>([]);

  useEffect(() => {
    const client = supabase;
    if (!client) return;

    let alive = true;
    let ready = false;
    let peerCount = 0;
    let lastSentAt = 0;
    let sendTimer: number | null = null;
    let latestPosition: Position | null = null;
    let channel: RealtimeChannel | null = null;
    let identity = {
      display_name: "Pelajar Anonim",
      role: "anonymous",
      color: cursorColor(sessionId),
    };

    const pageLabel = PAGE_LABELS[page] ?? page;

    const trackPresence = async () => {
      if (!channel || !ready) return;
      try {
        await channel.track({
          session_id: sessionId,
          display_name: identity.display_name,
          role: identity.role,
          color: identity.color,
          page: pageLabel,
          route: page,
          device: window.matchMedia("(pointer: coarse)").matches ? "touch" : "mouse",
          updated_at: new Date().toISOString(),
        });
      } catch {
        // Presence is an enhancement; a failed track must not affect the planner.
      }
    };

    const refreshIdentity = async (email: string | null | undefined) => {
      const normalizedEmail = email?.trim().toLowerCase() ?? "";
      let isAdmin = false;
      if (normalizedEmail) {
        try {
          const { data, error } = await client
            .from("admin_users")
            .select("email")
            .eq("email", normalizedEmail)
            .maybeSingle();
          isAdmin = !error && Boolean(data);
        } catch {
          isAdmin = false;
        }
      }
      if (!alive) return;
      identity = {
        display_name: isAdmin ? "Admin" : "Pelajar Anonim",
        role: isAdmin ? "admin" : "anonymous",
        color: cursorColor(sessionId),
      };
      await trackPresence();
    };

    const publishCursor = (force = false) => {
      if (!ready || !channel || peerCount < 1 || !latestPosition) return;
      const elapsed = performance.now() - lastSentAt;
      if (!force && elapsed < 66) {
        if (sendTimer === null) {
          sendTimer = window.setTimeout(() => {
            sendTimer = null;
            publishCursor(true);
          }, 66 - elapsed);
        }
        return;
      }
      lastSentAt = performance.now();
      const position = latestPosition;
      void channel.send({
        type: "broadcast",
        event: "cursor",
        payload: {
          session_id: sessionId,
          display_name: identity.display_name,
          role: identity.role,
          device: position.device,
          x: position.x,
          y: position.y,
          color: identity.color,
          page: pageLabel,
          route: page,
          ts: Date.now(),
        },
      });
    };

    const handlePointerMove = (event: PointerEvent) => {
      if (!["mouse", "touch", "pen"].includes(event.pointerType)) return;
      latestPosition = {
        x: Math.max(0, Math.min(1, event.clientX / Math.max(window.innerWidth, 1))),
        y: Math.max(0, Math.min(1, event.clientY / Math.max(window.innerHeight, 1))),
        device: event.pointerType || "mouse",
      };
      publishCursor();
    };

    channel = client.channel("zeon-site-presence-v1", {
      config: {
        broadcast: { self: false },
        presence: { key: sessionId },
      },
    });

    const updatePeerCount = () => {
      if (!channel) return;
      const presence = channel.presenceState();
      peerCount = Object.keys(presence).filter((key) => key !== sessionId).length;
      if (peerCount === 0) setCursors([]);
      else publishCursor(true);
    };

    channel
      .on("broadcast", { event: "cursor" }, ({ payload }) => {
        if (!alive || !payload || payload.session_id === sessionId) return;
        const x = Number(payload.x);
        const y = Number(payload.y);
        if (!Number.isFinite(x) || !Number.isFinite(y)) return;
        const id = String(payload.session_id ?? "");
        if (!id) return;
        setCursors((current) => {
          const next: RemoteCursor = {
            session_id: id,
            display_name: String(payload.display_name || "Pelajar Anonim"),
            role: String(payload.role || "anonymous"),
            device: String(payload.device || "mouse"),
            x: Math.max(0, Math.min(1, x)),
            y: Math.max(0, Math.min(1, y)),
            color: String(payload.color || cursorColor(id)),
            receivedAt: Date.now(),
            page: String(payload.page || payload.route || ""),
          };
          return [...current.filter((cursor) => cursor.session_id !== id), next];
        });
      })
      .on("presence", { event: "sync" }, updatePeerCount)
      .on("presence", { event: "join" }, updatePeerCount)
      .on("presence", { event: "leave" }, ({ key }) => {
        setCursors((current) => current.filter((cursor) => cursor.session_id !== key));
        updatePeerCount();
      })
      .subscribe(async (status) => {
        if (!alive || status !== "SUBSCRIBED" || !channel) return;
        ready = true;
        await trackPresence();
        updatePeerCount();
      });

    const { data: { subscription: authSubscription } } = client.auth.onAuthStateChange((_event, session) => {
      // Defer network work until after Supabase has released its auth lock.
      window.setTimeout(() => {
        void refreshIdentity(session?.user.email);
      }, 0);
    });

    void client.auth.getSession().then(({ data, error }) => {
      if (alive) void refreshIdentity(error ? null : data.session?.user.email);
    });

    document.addEventListener("pointermove", handlePointerMove, { passive: true });

    const pruneTimer = window.setInterval(() => {
      const cutoff = Date.now() - 12_000;
      setCursors((current) => current.filter((cursor) => cursor.receivedAt >= cutoff));
    }, 3_000);

    return () => {
      alive = false;
      document.removeEventListener("pointermove", handlePointerMove);
      authSubscription.unsubscribe();
      window.clearInterval(pruneTimer);
      if (sendTimer !== null) window.clearTimeout(sendTimer);
      if (channel) void client.removeChannel(channel);
      setCursors([]);
    };
  }, [page, sessionId]);

  if (!supabase) return null;

  return (
    <>
      <style>{PRESENCE_CSS}</style>
      <div className="web-presence-layer" aria-hidden="true">
        {cursors.map((cursor) => {
          const stale = Date.now() - cursor.receivedAt > 2_500;
          const style = {
            "--web-cursor-color": cursor.color,
            transform: `translate3d(${cursor.x * window.innerWidth}px, ${cursor.y * window.innerHeight}px, 0)`,
          } as CSSProperties;
          return (
            <div
              className={"web-presence-cursor" + (stale ? " is-stale" : "") + (cursor.page && cursor.page !== PAGE_LABELS[page] ? " is-other-page" : "")}
              key={cursor.session_id}
              style={style}
            >
              <span className="web-presence-pointer">
                <svg viewBox="0 0 18 22" fill="none">
                  <path d="M2 1.5 15.4 12.4 9 13.3 12.2 19.3 9.8 20.5 6.5 14.5 2.2 19Z" fill="currentColor" stroke="white" strokeWidth="1.2" strokeLinejoin="round" />
                </svg>
              </span>
              <span className="web-presence-label">
                <span className="web-presence-device">{deviceIcon(cursor.device)}</span>
                <span className="web-presence-name">{cursor.display_name}</span>
              </span>
            </div>
          );
        })}
      </div>
    </>
  );
}
