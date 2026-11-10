import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { RealtimeChannel } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";

type CursorPosition = {
  x: number;
  y: number;
  device: string;
};

type RemoteCursor = {
  session_id: string;
  display_name: string;
  device: string;
  x: number;
  y: number;
  color: string;
  receivedAt: number;
  page: string;
  chatText: string;
};

const CHAT_MAX_LENGTH = 240;
const CHAT_SHORTCUT = "Alt + Shift + C";

const PAGE_LABELS: Record<string, string> = {
  home: "Beranda",
  calendar: "Kalender Tugas",
  archive: "Arsip Modul",
  admin: "Panel Admin",
};

const PRESENCE_CSS = `
.web-presence-layer {
  position: fixed;
  inset: 0;
  z-index: 9998;
  overflow: hidden;
  pointer-events: none;
  contain: layout style;
}
.web-presence-cursor {
  position: absolute;
  z-index: 1;
  top: 0;
  left: 0;
  color: var(--web-cursor-color);
  will-change: transform, opacity;
  pointer-events: none;
  transition: opacity 180ms ease;
  filter: drop-shadow(0 1px 1px rgb(0 0 0 / 22%));
}
.web-presence-pointer {
  display: block;
  width: 18px;
  height: 22px;
  color: var(--web-cursor-color);
}
.web-presence-pointer svg {
  display: block;
  width: 18px;
  height: 22px;
  overflow: visible;
}
.web-presence-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin: 1px 0 0 14px;
  max-width: 190px;
  padding: 3px 8px;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 999px;
  background: var(--web-cursor-color);
  color: #fff;
  font: 600 10px/1.45 "DM Sans", sans-serif;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgb(0 0 0 / 18%);
}
.web-presence-device {
  opacity: .8;
  font-size: 11px;
}
.web-presence-name {
  overflow: hidden;
  text-overflow: ellipsis;
}
.web-presence-cursor.is-stale {
  opacity: .3;
}
.web-presence-cursor.is-other-page {
  opacity: .55;
}
.web-presence-chat-bubble {
  position: absolute;
  top: 22px;
  left: 22px;
  display: block;
  width: max-content;
  max-width: min(280px, calc(100vw - 36px));
  padding: 9px 12px;
  border: 1px solid color-mix(in srgb, var(--web-cursor-color) 75%, white 12%);
  border-radius: 12px 12px 12px 4px;
  background: rgb(28 26 42 / 96%);
  color: #f5f2ff;
  font: 500 12px/1.5 "DM Sans", sans-serif;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  box-shadow: 0 8px 24px rgb(0 0 0 / 28%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  pointer-events: none;
}
.web-presence-cursor.is-flipped .web-presence-chat-bubble {
  right: 0;
  left: auto;
  border-radius: 12px 12px 4px 12px;
}
.web-presence-cursor.is-low .web-presence-chat-bubble {
  top: auto;
  bottom: 18px;
}
.web-presence-chat-local {
  position: absolute;
  top: 22px;
  left: 22px;
  width: min(288px, calc(100vw - 36px));
  pointer-events: none;
}
.web-presence-chat-local.is-flipped {
  right: 0;
  left: auto;
}
.web-presence-chat-local.is-low {
  top: auto;
  bottom: 18px;
}
.web-presence-chat-composer {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 44px;
  padding: 5px 6px 5px 12px;
  border: 1px solid rgb(183 165 255 / 65%);
  border-radius: 13px 13px 13px 4px;
  background: rgb(28 26 42 / 97%);
  box-shadow: 0 8px 26px rgb(0 0 0 / 34%);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  pointer-events: auto;
}
.web-presence-chat-local.is-flipped .web-presence-chat-composer {
  border-radius: 13px 13px 4px 13px;
}
.web-presence-chat-input {
  width: 100%;
  min-width: 0;
  padding: 5px 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #f5f2ff;
  font: 500 12px/1.45 "DM Sans", sans-serif;
}
.web-presence-chat-input::placeholder {
  color: #928da9;
}
.web-presence-chat-close {
  display: grid;
  width: 29px;
  height: 29px;
  flex: 0 0 29px;
  place-items: center;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 9px;
  background: rgb(255 255 255 / 5%);
  color: #c9c2dc;
  font: 500 18px/1 "DM Sans", sans-serif;
  cursor: pointer;
}
.web-presence-chat-close:hover {
  background: rgb(255 255 255 / 12%);
  color: white;
}
.web-presence-chat-hint {
  display: block;
  margin: 5px 4px 0;
  color: #a7a1bd;
  font: 500 10px/1.4 "DM Sans", sans-serif;
  text-shadow: 0 1px 3px rgb(0 0 0 / 70%);
  pointer-events: none;
}
@media (prefers-reduced-motion: reduce) {
  .web-presence-cursor {
    transition: none;
  }
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

function safeSessionId(value: unknown): string {
  if (typeof value !== "string" || value.length > 80) return "";
  return /^[a-zA-Z0-9_-]+$/.test(value) ? value : "";
}

function safeDevice(value: unknown): string {
  return value === "touch" || value === "pen" ? value : "mouse";
}

function safeChatText(value: unknown): string {
  return String(value ?? "")
    .replace(/[\x00-\x1F\x7F]/g, " ")
    .slice(0, CHAT_MAX_LENGTH);
}

function safeCoordinate(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.min(1, number)) : fallback;
}

export default function PresenceLayer({ page }: { page: "home" | "calendar" | "archive" | "admin" }) {
  const [sessionId] = useState(getSessionId);
  const [cursors, setCursors] = useState<RemoteCursor[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatText, setChatText] = useState("");
  const [ownPosition, setOwnPosition] = useState<CursorPosition>({ x: 0.5, y: 0.5, device: "mouse" });
  const chatInputRef = useRef<HTMLInputElement>(null);
  const channelRef = useRef<RealtimeChannel | null>(null);
  const channelReadyRef = useRef(false);
  const peerCountRef = useRef(0);
  const latestPositionRef = useRef<CursorPosition | null>(null);
  const chatTextRef = useRef("");
  const pageLabel = PAGE_LABELS[page] ?? page;

  const publishChatText = (value: string) => {
    const text = safeChatText(value);
    chatTextRef.current = text;
    const channel = channelRef.current;
    if (!channel || !channelReadyRef.current || peerCountRef.current < 1) return;

    const position = latestPositionRef.current ?? { x: 0.5, y: 0.5, device: "mouse" };
    void channel.send({
      type: "broadcast",
      event: "cursor-chat",
      payload: {
        session_id: sessionId,
        text,
        x: position.x,
        y: position.y,
        device: position.device,
        page: pageLabel,
        ts: Date.now(),
      },
    });
  };

  const closeChat = () => {
    publishChatText("");
    setChatText("");
    setChatOpen(false);
  };

  useEffect(() => {
    const client = supabase;
    if (!client) return;

    let alive = true;
    let peerCount = 0;
    let lastSentAt = 0;
    let sendTimer: number | null = null;
    const pageName = PAGE_LABELS[page] ?? page;
    latestPositionRef.current = null;
    channelReadyRef.current = false;
    peerCountRef.current = 0;

    const publishCursor = (force = false) => {
      const channel = channelRef.current;
      const position = latestPositionRef.current;
      if (!channel || !channelReadyRef.current || peerCountRef.current < 1 || !position) return;

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
      void channel.send({
        type: "broadcast",
        event: "cursor",
        payload: {
          session_id: sessionId,
          x: position.x,
          y: position.y,
          device: position.device,
          page: pageName,
          ts: Date.now(),
        },
      });
    };

    const trackPresence = async (channel: RealtimeChannel) => {
      try {
        await channel.track({
          session_id: sessionId,
          display_name: "Pengunjung",
          page: pageName,
          device: window.matchMedia("(pointer: coarse)").matches ? "touch" : "mouse",
          online_at: new Date().toISOString(),
        });
      } catch {
        // Presence is an enhancement; a failed track must not affect the planner.
      }
    };

    const handlePointerMove = (event: PointerEvent) => {
      if (!["mouse", "touch", "pen"].includes(event.pointerType)) return;
      const position: CursorPosition = {
        x: Math.max(0, Math.min(1, event.clientX / Math.max(window.innerWidth, 1))),
        y: Math.max(0, Math.min(1, event.clientY / Math.max(window.innerHeight, 1))),
        device: safeDevice(event.pointerType),
      };
      latestPositionRef.current = position;
      setOwnPosition(position);
      publishCursor();
    };

    const channel = client.channel("zeon-site-presence-v1", {
      config: {
        broadcast: { self: false },
        presence: { key: sessionId },
      },
    });
    channelRef.current = channel;

    const updatePeerCount = () => {
      const presence = channel.presenceState();
      peerCount = Object.keys(presence).filter((key) => key !== sessionId).length;
      peerCountRef.current = peerCount;
      if (peerCount === 0) {
        setCursors([]);
      } else {
        publishCursor(true);
        if (chatTextRef.current.trim()) publishChatText(chatTextRef.current);
      }
    };

    channel
      .on("broadcast", { event: "cursor" }, ({ payload }) => {
        if (!alive || !payload) return;
        const id = safeSessionId(payload.session_id);
        if (!id || id === sessionId) return;

        const x = safeCoordinate(payload.x, 0.5);
        const y = safeCoordinate(payload.y, 0.5);
        const device = safeDevice(payload.device);
        const remotePage = String(payload.page ?? "").slice(0, 48);

        setCursors((current) => {
          const previous = current.find((cursor) => cursor.session_id === id);
          const next: RemoteCursor = {
            session_id: id,
            display_name: "Pengunjung",
            device,
            x,
            y,
            color: cursorColor(id),
            receivedAt: Date.now(),
            page: remotePage,
            chatText: previous?.chatText ?? "",
          };
          return [...current.filter((cursor) => cursor.session_id !== id), next];
        });
      })
      .on("broadcast", { event: "cursor-chat" }, ({ payload }) => {
        if (!alive || !payload) return;
        const id = safeSessionId(payload.session_id);
        if (!id || id === sessionId) return;

        const text = safeChatText(payload.text);
        const x = safeCoordinate(payload.x, 0.5);
        const y = safeCoordinate(payload.y, 0.5);
        const device = safeDevice(payload.device);
        const remotePage = String(payload.page ?? "").slice(0, 48);

        setCursors((current) => {
          const previous = current.find((cursor) => cursor.session_id === id);
          if (!previous && !text.trim()) return current;

          const next: RemoteCursor = {
            session_id: id,
            display_name: "Pengunjung",
            device: previous?.device ?? device,
            x: previous?.x ?? x,
            y: previous?.y ?? y,
            color: previous?.color ?? cursorColor(id),
            receivedAt: Date.now(),
            page: previous?.page || remotePage,
            chatText: text,
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
        if (!alive || status !== "SUBSCRIBED") return;
        channelReadyRef.current = true;
        await trackPresence(channel);
        updatePeerCount();
        if (chatTextRef.current.trim()) publishChatText(chatTextRef.current);
      });

    document.addEventListener("pointermove", handlePointerMove, { passive: true });

    const pruneTimer = window.setInterval(() => {
      const cutoff = Date.now() - 12_000;
      setCursors((current) => current.filter((cursor) => cursor.receivedAt >= cutoff));
    }, 3_000);

    return () => {
      alive = false;
      document.removeEventListener("pointermove", handlePointerMove);
      window.clearInterval(pruneTimer);
      if (sendTimer !== null) window.clearTimeout(sendTimer);
      channelReadyRef.current = false;
      peerCountRef.current = 0;
      if (channelRef.current === channel) channelRef.current = null;
      void client.removeChannel(channel);
      setCursors([]);
    };
  }, [page, sessionId]);

  useEffect(() => {
    if (chatOpen) {
      window.requestAnimationFrame(() => chatInputRef.current?.focus());
    } else {
      chatInputRef.current?.blur();
    }
  }, [chatOpen]);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      const target = event.target instanceof HTMLElement ? event.target : null;
      const isEditing = Boolean(target && (
        target.isContentEditable ||
        ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)
      ));
      const shortcutPressed =
        event.altKey &&
        event.shiftKey &&
        !event.ctrlKey &&
        !event.metaKey &&
        event.code === "KeyC";

      if (shortcutPressed && !event.repeat && (!isEditing || target === chatInputRef.current)) {
        event.preventDefault();
        if (chatOpen) closeChat();
        else setChatOpen(true);
        return;
      }

      if (event.key === "Escape" && chatOpen) {
        event.preventDefault();
        closeChat();
      }
    };

    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, [chatOpen, chatText, sessionId, page]);

  if (!supabase) return null;

  return (
    <>
      <style>{PRESENCE_CSS}</style>
      <div className="web-presence-layer">
        {cursors.map((cursor) => {
          const stale = Date.now() - cursor.receivedAt > 2_500;
          const flipped = cursor.x > 0.68;
          const low = cursor.y > 0.72;
          const style = {
            "--web-cursor-color": cursor.color,
            transform: `translate3d(${cursor.x * window.innerWidth}px, ${cursor.y * window.innerHeight}px, 0)`,
          } as CSSProperties;
          return (
            <div
              className={
                "web-presence-cursor" +
                (stale ? " is-stale" : "") +
                (cursor.page && cursor.page !== pageLabel ? " is-other-page" : "") +
                (flipped ? " is-flipped" : "") +
                (low ? " is-low" : "")
              }
              key={cursor.session_id}
              style={style}
              aria-hidden="true"
            >
              <span className="web-presence-pointer">
                <svg viewBox="0 0 18 22" fill="none">
                  <path
                    d="M2 1.5 15.4 12.4 9 13.3 12.2 19.3 9.8 20.5 6.5 14.5 2.2 19Z"
                    fill="currentColor"
                    stroke="white"
                    strokeWidth="1.2"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <span className="web-presence-label">
                <span className="web-presence-device">{deviceIcon(cursor.device)}</span>
                <span className="web-presence-name">{cursor.display_name}</span>
              </span>
              {cursor.chatText.trim() && (
                <span className="web-presence-chat-bubble">{cursor.chatText}</span>
              )}
            </div>
          );
        })}

        {chatOpen && (
          <div
            className={
              "web-presence-chat-local" +
              (ownPosition.x > 0.68 ? " is-flipped" : "") +
              (ownPosition.y > 0.72 ? " is-low" : "")
            }
            style={{
              transform: `translate3d(${ownPosition.x * window.innerWidth}px, ${ownPosition.y * window.innerHeight}px, 0)`,
            }}
          >
            <div className="web-presence-chat-composer">
              <input
                ref={chatInputRef}
                className="web-presence-chat-input"
                type="text"
                value={chatText}
                maxLength={CHAT_MAX_LENGTH}
                placeholder="Tulis pesan untuk semua pengunjung…"
                aria-label="Pesan realtime di samping kursor"
                onChange={(event) => {
                  const next = safeChatText(event.target.value);
                  setChatText(next);
                  publishChatText(next);
                }}
              />
              <button
                className="web-presence-chat-close"
                type="button"
                onClick={closeChat}
                title="Tutup bubble (Esc)"
                aria-label="Tutup bubble chat"
              >
                ×
              </button>
            </div>
            <span className="web-presence-chat-hint">
              Terlihat saat ada teks · {CHAT_SHORTCUT} untuk buka · Esc untuk tutup
            </span>
          </div>
        )}
      </div>
    </>
  );
}
