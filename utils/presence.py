import uuid

import streamlit as st

from utils.auth import is_admin
from utils.supabase_client import SUPABASE_ANON_KEY, SUPABASE_URL, read_config


_PRESENCE_HTML = "<span aria-hidden='true'></span>"

_PRESENCE_CSS = r"""
#zeon-presence-layer {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    z-index: 2147483646;
    pointer-events: none;
    overflow: hidden;
}

.zeon-presence-cursor {
    position: fixed;
    left: 0;
    top: 0;
    pointer-events: none !important;
    will-change: transform, opacity;
    transform: translate3d(-100px, -100px, 0);
    transition: opacity 180ms ease;
    opacity: 1;
}

.zeon-presence-cursor.is-stale {
    opacity: 0;
}

.zeon-presence-pointer {
    display: block;
    width: 22px;
    height: 26px;
    color: var(--zeon-cursor-color);
    filter: drop-shadow(0 2px 3px rgba(0, 0, 0, .30));
}

.zeon-presence-pointer svg {
    display: block;
    width: 22px;
    height: 26px;
    overflow: visible;
}

.zeon-presence-dot {
    display: none;
    width: 13px;
    height: 13px;
    border-radius: 50%;
    background: var(--zeon-cursor-color);
    border: 2px solid rgba(255, 255, 255, .95);
    box-shadow:
        0 0 0 3px color-mix(in srgb, var(--zeon-cursor-color) 28%, transparent),
        0 2px 7px rgba(0, 0, 0, .28);
}

.zeon-presence-label {
    position: absolute;
    left: 17px;
    top: 18px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    max-width: min(260px, 55vw);
    padding: 4px 8px;
    border-radius: 999px;
    background: var(--zeon-cursor-color);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, .25);
    box-shadow: 0 3px 12px rgba(0, 0, 0, .18);
    font: 650 11px/1.2 var(--st-font, Inter, sans-serif);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
}

.zeon-presence-device {
    font-size: 10px;
    line-height: 1;
    opacity: .88;
}

.zeon-presence-cursor.is-touch .zeon-presence-pointer {
    display: none;
}

.zeon-presence-cursor.is-touch .zeon-presence-dot {
    display: block;
}

.zeon-presence-cursor.is-touch .zeon-presence-label {
    left: 12px;
    top: -4px;
}

@media (prefers-reduced-motion: reduce) {
    .zeon-presence-cursor {
        transition: none;
    }
}
"""

_PRESENCE_JS = r"""
export default function(component) {
    const { data, parentElement } = component;

    const state = window.__zeonSitePresence ??= {
        initialized: false,
        starting: false,
        ready: false,
        supabase: null,
        channel: null,
        channelName: "zeon-site-presence-v1",
        sessionId: null,
        lastSentAt: 0,
        sendTimer: null,
        pendingCursor: null,
        listenersAttached: false,
        cursors: new Map(),
        cleanupTimer: null,
    };

    const config = {
        url: String(data?.supabase_url || ""),
        key: String(data?.supabase_key || ""),
        sessionId: String(data?.session_id || ""),
        displayName: String(data?.display_name || "Pelajar Anonim"),
        role: String(data?.role || "anonymous"),
        page: String(data?.page || "unknown"),
    };

    state.sessionId = config.sessionId;
    state.identity = {
        display_name: config.displayName,
        role: config.role,
        page: config.page,
        color: cursorColor(config.sessionId),
    };

    let layer = document.getElementById("zeon-presence-layer");
    if (!layer) {
        layer = document.createElement("div");
        layer.id = "zeon-presence-layer";
        document.body.appendChild(layer);
    }

    function cursorColor(seed) {
        let hash = 0;
        for (let i = 0; i < seed.length; i += 1) {
            hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
        }
        const hue = Math.abs(hash) % 360;
        return `hsl(${hue} 78% 55%)`;
    }

    function isTouchDevice() {
        return window.matchMedia("(pointer: coarse)").matches;
    }

    function updateIdentity() {
        state.identity = {
            display_name: config.displayName,
            role: config.role,
            page: config.page,
            color: cursorColor(config.sessionId),
        };

        if (!state.channel || !state.ready) {
            return;
        }

        state.channel.track({
            session_id: config.sessionId,
            display_name: config.displayName,
            role: config.role,
            page: config.page,
            device: isTouchDevice() ? "touch" : "mouse",
            updated_at: new Date().toISOString(),
        });
    }

    function getOrCreateCursor(id, payload) {
        let cursor = state.cursors.get(id);
        if (cursor) {
            return cursor;
        }

        const element = document.createElement("div");
        element.className = "zeon-presence-cursor";
        element.dataset.sessionId = id;
        element.style.setProperty("--zeon-cursor-color", payload.color || cursorColor(id));

        const pointer = document.createElement("span");
        pointer.className = "zeon-presence-pointer";
        pointer.innerHTML = `
            <svg viewBox="0 0 24 28" aria-hidden="true">
                <path
                    d="M4.2 2.2 4 23.5l6.2-5.1 4.2 7.5 3.1-1.8-4.3-7.6h7.3L4.2 2.2Z"
                    fill="currentColor"
                    stroke="white"
                    stroke-width="1.3"
                    stroke-linejoin="round"
                />
            </svg>
        `;

        const dot = document.createElement("span");
        dot.className = "zeon-presence-dot";

        const label = document.createElement("span");
        label.className = "zeon-presence-label";

        const device = document.createElement("span");
        device.className = "zeon-presence-device";

        const name = document.createElement("span");
        label.append(device, name);

        element.append(pointer, dot, label);
        layer.appendChild(element);
        state.cursors.set(id, {
            element,
            label,
            device,
            name,
            lastTs: 0,
            staleTimer: null,
        });

        return state.cursors.get(id);
    }

    function deviceIcon(deviceType) {
        if (deviceType === "touch") {
            return "●";
        }
        if (deviceType === "pen") {
            return "✎";
        }
        return "↖";
    }

    function renderCursor(payload) {
        if (!payload || !payload.session_id || payload.session_id === config.sessionId) {
            return;
        }

        const x = Number(payload.x);
        const y = Number(payload.y);

        if (!Number.isFinite(x) || !Number.isFinite(y)) {
            return;
        }

        const cursor = getOrCreateCursor(payload.session_id, payload);
        const timestamp = Number(payload.ts || Date.now());

        cursor.element.classList.toggle("is-touch", payload.device !== "mouse");
        cursor.element.style.setProperty(
            "--zeon-cursor-color",
            payload.color || cursorColor(payload.session_id)
        );
        cursor.element.style.transform =
            `translate3d(${Math.max(0, Math.min(1, x)) * 100}vw, ${Math.max(0, Math.min(1, y)) * 100}vh, 0)`;
        cursor.element.classList.remove("is-stale");

        cursor.name.textContent = payload.display_name || "Pelajar Anonim";
        cursor.device.textContent = deviceIcon(payload.device);
        cursor.lastTs = timestamp;

        if (cursor.staleTimer) {
            clearTimeout(cursor.staleTimer);
        }

        cursor.staleTimer = window.setTimeout(() => {
            const current = state.cursors.get(payload.session_id);
            if (!current || current.lastTs !== timestamp) {
                return;
            }
            current.element.classList.add("is-stale");
        }, 4500);
    }

    function removeCursor(sessionId) {
        const cursor = state.cursors.get(sessionId);
        if (!cursor) {
            return;
        }
        if (cursor.staleTimer) {
            clearTimeout(cursor.staleTimer);
        }
        cursor.element.remove();
        state.cursors.delete(sessionId);
    }

    function sendCursor(x, y, device) {
        state.pendingCursor = { x, y, device };

        if (!state.ready || !state.channel) {
            return;
        }

        const now = performance.now();
        const elapsed = now - state.lastSentAt;
        const send = () => {
            state.sendTimer = null;
            if (!state.pendingCursor || !state.ready || !state.channel) {
                return;
            }

            const point = state.pendingCursor;
            state.lastSentAt = performance.now();

            state.channel.send({
                type: "broadcast",
                event: "cursor",
                payload: {
                    session_id: config.sessionId,
                    display_name: state.identity.display_name,
                    role: state.identity.role,
                    device: point.device,
                    x: point.x,
                    y: point.y,
                    color: state.identity.color,
                    ts: Date.now(),
                },
            });
        };

        if (elapsed >= 66) {
            send();
        } else if (!state.sendTimer) {
            state.sendTimer = window.setTimeout(send, 66 - elapsed);
        }
    }

    function handlePointerMove(event) {
        if (!["mouse", "touch", "pen"].includes(event.pointerType)) {
            return;
        }

        const width = Math.max(window.innerWidth, 1);
        const height = Math.max(window.innerHeight, 1);

        sendCursor(
            event.clientX / width,
            event.clientY / height,
            event.pointerType,
        );
    }

    function handlePointerDown(event) {
        if (event.pointerType !== "touch") {
            return;
        }

        const width = Math.max(window.innerWidth, 1);
        const height = Math.max(window.innerHeight, 1);

        sendCursor(
            event.clientX / width,
            event.clientY / height,
            "touch",
        );
    }

    function removePresenceChannel() {
        if (state.channel && state.supabase) {
            state.supabase.removeChannel(state.channel);
        }
        state.channel = null;
        state.ready = false;
    }

    async function startRealtime() {
        if (state.starting || state.ready || !config.url || !config.key) {
            return;
        }

        state.starting = true;

        try {
            const module = await import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm");
            const createClient = module.createClient;

            state.supabase = createClient(config.url, config.key);
            state.channel = state.supabase.channel(state.channelName, {
                config: {
                    broadcast: { self: false },
                    presence: { key: config.sessionId },
                },
            });

            state.channel
                .on("broadcast", { event: "cursor" }, ({ payload }) => {
                    renderCursor(payload);
                })
                .on("presence", { event: "leave" }, ({ key }) => {
                    removeCursor(key);
                })
                .subscribe(async (status) => {
                    if (status !== "SUBSCRIBED") {
                        return;
                    }

                    state.ready = true;

                    await state.channel.track({
                        session_id: config.sessionId,
                        display_name: config.displayName,
                        role: config.role,
                        page: config.page,
                        device: isTouchDevice() ? "touch" : "mouse",
                        updated_at: new Date().toISOString(),
                    });

                    if (state.pendingCursor) {
                        const pending = state.pendingCursor;
                        state.pendingCursor = null;
                        sendCursor(pending.x, pending.y, pending.device);
                    }
                });
        } catch (error) {
            console.warn("[Zeon Presence] Realtime unavailable:", error);
            removePresenceChannel();
        } finally {
            state.starting = false;
        }
    }

    if (!state.listenersAttached) {
        document.addEventListener("pointermove", handlePointerMove, { passive: true });
        document.addEventListener("pointerdown", handlePointerDown, { passive: true });
        state.listenersAttached = true;
    }

    updateIdentity();
    startRealtime();

    return () => {
        document.removeEventListener("pointermove", handlePointerMove);
        document.removeEventListener("pointerdown", handlePointerDown);

        if (state.sendTimer) {
            clearTimeout(state.sendTimer);
        }

        state.cursors.forEach((cursor) => {
            if (cursor.staleTimer) {
                clearTimeout(cursor.staleTimer);
            }
            cursor.element.remove();
        });
        state.cursors.clear();

        removePresenceChannel();
        layer.remove();
        delete window.__zeonSitePresence;
    };
}
"""

_presence_component = st.components.v2.component(
    "zeon_site_presence",
    html=_PRESENCE_HTML,
    css=_PRESENCE_CSS,
    js=_PRESENCE_JS,
    isolate_styles=False,
)


def render_presence(page: str = "unknown") -> None:
    """Render realtime visitor cursors without adding any persistent database rows."""
    session_id = st.session_state.get("zeon_presence_session_id")
    if not session_id:
        session_id = uuid.uuid4().hex
        st.session_state["zeon_presence_session_id"] = session_id

    display_name = "Admin" if is_admin() else "Pelajar Anonim"
    role = "admin" if display_name == "Admin" else "anonymous"

    realtime_key = read_config("SUPABASE_PUBLISHABLE_KEY") or SUPABASE_ANON_KEY
    if not SUPABASE_URL or not realtime_key:
        return

    _presence_component(
        key="zeon-site-presence",
        data={
            "supabase_url": SUPABASE_URL,
            "supabase_key": realtime_key,
            "session_id": session_id,
            "display_name": display_name,
            "role": role,
            "page": page,
        },
    )
