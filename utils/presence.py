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

.zeon-presence-cursor.is-other-page {
    opacity: .45;
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
        peerCount: 0,
        listenersAttached: false,
        cursors: new Map(),
        iframeListeners: new Map(),
        iframeScanTimer: null,
        iframeObserver: null,
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

        const normalizedX = Number(payload.x);
        const normalizedY = Number(payload.y);
        if (!Number.isFinite(normalizedX) || !Number.isFinite(normalizedY)) return;

        const fallbackX = Math.max(0, Math.min(1, normalizedX)) * window.innerWidth;
        const fallbackY = Math.max(0, Math.min(1, normalizedY)) * window.innerHeight;
        let resolvedPoint = null;

        if (payload.frame === "calendar" && (!payload.page || payload.page === config.page)) {
            const calendarFrame = Array.from(document.querySelectorAll("iframe"))
                .find((frame) => isCalendarFrame(frame));
            if (calendarFrame) {
                const rect = calendarFrame.getBoundingClientRect();
                resolvedPoint = {
                    x: rect.left + Math.max(0, Math.min(1, Number(payload.frame_x) || 0)) * rect.width,
                    y: rect.top + Math.max(0, Math.min(1, Number(payload.frame_y) || 0)) * rect.height,
                };
            }
        }

        if (!resolvedPoint && (!payload.frame || payload.frame !== "calendar") && (!payload.page || payload.page === config.page)) {
            resolvedPoint = resolveAnchor(payload.anchor, fallbackX, fallbackY);
        }

        const screenX = resolvedPoint?.x ?? fallbackX;
        const screenY = resolvedPoint?.y ?? fallbackY;

        const cursor = getOrCreateCursor(payload.session_id, payload);
        const timestamp = Number(payload.ts || Date.now());

        cursor.element.classList.toggle("is-touch", payload.device !== "mouse");
        cursor.element.style.setProperty(
            "--zeon-cursor-color",
            payload.color || cursorColor(payload.session_id)
        );
        cursor.element.style.transform =
            "translate3d(" + screenX + "px, " + screenY + "px, 0)";
        cursor.element.classList.toggle("is-other-page", Boolean(payload.page && payload.page !== config.page));
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

    function cleanText(value) {
        return String(value || "").replace(/\s+/g, " ").trim().slice(0, 80);
    }

    function isUsefulAnchor(element) {
        if (!element || !(element instanceof HTMLElement)) {
            return false;
        }

        const tag = element.tagName.toLowerCase();
        const meaningfulTag = [
            "a", "button", "input", "select", "textarea",
            "h1", "h2", "h3", "h4", "summary",
        ].includes(tag);
        const meaningfulRole = Boolean(element.getAttribute("role"));
        const hasTestId = Boolean(element.getAttribute("data-testid"));
        const rect = element.getBoundingClientRect();

        return rect.width > 0 && rect.height > 0 &&
            (meaningfulTag || meaningfulRole || hasTestId);
    }

    function getAnchorAtPoint(x, y) {
        let element = document.elementFromPoint(x, y);

        for (let depth = 0; element && depth < 7; depth += 1) {
            if (isUsefulAnchor(element)) {
                const rect = element.getBoundingClientRect();
                return {
                    tag: element.tagName.toLowerCase(),
                    testid: element.getAttribute("data-testid") || "",
                    role: element.getAttribute("role") || "",
                    aria: element.getAttribute("aria-label") || "",
                    title: element.getAttribute("title") || "",
                    placeholder: element.getAttribute("placeholder") || "",
                    text: cleanText(element.innerText || element.textContent),
                    offset_x: rect.width ? (x - rect.left) / rect.width : 0.5,
                    offset_y: rect.height ? (y - rect.top) / rect.height : 0.5,
                };
            }
            element = element.parentElement;
        }
        return null;
    }

    function isCandidateForAnchor(node, anchor) {
        if (!isUsefulAnchor(node)) return false;
        const tag = node.tagName.toLowerCase();
        const nodeText = cleanText(node.innerText || node.textContent);
        if (anchor.testid && node.getAttribute("data-testid") !== anchor.testid) return false;
        if (anchor.tag && tag !== anchor.tag) return false;
        const attrs = [
            ["role", anchor.role],
            ["aria-label", anchor.aria],
            ["title", anchor.title],
            ["placeholder", anchor.placeholder],
        ];
        for (const [name, expected] of attrs) {
            if (expected && node.getAttribute(name) !== expected) return false;
        }
        if (anchor.text && nodeText !== anchor.text && !nodeText.includes(anchor.text)) return false;
        return true;
    }

    function resolveAnchor(anchor, fallbackX, fallbackY) {
        if (!anchor) return null;

        const selectors = "a,button,input,select,textarea,h1,h2,h3,h4,summary,[role],[data-testid]";
        const candidates = Array.from(document.querySelectorAll(selectors))
            .filter((node) => isCandidateForAnchor(node, anchor));
        if (!candidates.length) return null;

        let best = null;
        let bestDistance = Number.POSITIVE_INFINITY;
        for (const node of candidates) {
            const rect = node.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const distance = Math.pow(centerX - fallbackX, 2) + Math.pow(centerY - fallbackY, 2);
            if (distance < bestDistance) {
                bestDistance = distance;
                best = rect;
            }
        }

        if (!best || best.width <= 0 || best.height <= 0) return null;
        return {
            x: best.left + Math.max(0, Math.min(1, Number(anchor.offset_x) || 0.5)) * best.width,
            y: best.top + Math.max(0, Math.min(1, Number(anchor.offset_y) || 0.5)) * best.height,
        };
    }

    function buildCursorPayload(event) {
        const width = Math.max(window.innerWidth, 1);
        const height = Math.max(window.innerHeight, 1);
        return {
            x: event.clientX / width,
            y: event.clientY / height,
            device: event.pointerType,
            anchor: getAnchorAtPoint(event.clientX, event.clientY),
        };
    }

    function sendCursor(point, force = false) {
        state.pendingCursor = point;

        // Presence stays connected so new visitors can be detected, but
        // cursor broadcasts are completely paused while we're alone.
        if (!force && state.peerCount <= 0) {
            return;
        }

        if (!state.ready || !state.channel) return;

        const now = performance.now();
        const elapsed = now - state.lastSentAt;
        const send = () => {
            state.sendTimer = null;
            if (!state.pendingCursor || !state.ready || !state.channel || state.peerCount <= 0) return;
            const cursor = state.pendingCursor;
            state.lastSentAt = performance.now();
            state.channel.send({
                type: "broadcast",
                event: "cursor",
                payload: {
                    session_id: config.sessionId,
                    display_name: state.identity.display_name,
                    role: state.identity.role,
                    device: cursor.device,
                    x: cursor.x,
                    y: cursor.y,
                    anchor: cursor.anchor || null,
                    frame: cursor.frame || null,
                    frame_x: cursor.frame_x ?? null,
                    frame_y: cursor.frame_y ?? null,
                    frame_w: cursor.frame_w ?? null,
                    frame_h: cursor.frame_h ?? null,
                    color: state.identity.color,
                    page: config.page,
                    ts: Date.now(),
                },
            });
        };

        if (elapsed >= 66) send();
        else if (!state.sendTimer) state.sendTimer = window.setTimeout(send, 66 - elapsed);
    }
    function viewportPointFromFrame(frame, event) {
        const rect = frame.getBoundingClientRect();
        const width = Math.max(rect.width, 1);
        const height = Math.max(rect.height, 1);
        return {
            x: (rect.left + event.clientX) / Math.max(window.innerWidth, 1),
            y: (rect.top + event.clientY) / Math.max(window.innerHeight, 1),
            frame: "calendar",
            frame_x: Math.max(0, Math.min(1, event.clientX / width)),
            frame_y: Math.max(0, Math.min(1, event.clientY / height)),
            frame_w: width,
            frame_h: height,
            device: event.pointerType,
            anchor: null,
        };
    }

    function handlePointerMove(event) {
        if (!["mouse", "touch", "pen"].includes(event.pointerType)) return;
        sendCursor(buildCursorPayload(event));
    }

    function handlePointerDown(event) {
        if (event.pointerType !== "touch") return;
        sendCursor(buildCursorPayload(event));
    }

    function isCalendarFrame(frame) {
        try {
            return Boolean(frame.contentDocument?.querySelector(".fc"));
        } catch (error) {
            return false;
        }
    }

    function attachCalendarFrame(frame) {
        if (!frame || state.iframeListeners.has(frame) || !isCalendarFrame(frame)) {
            return;
        }

        let doc;
        try {
            doc = frame.contentDocument;
        } catch (error) {
            return;
        }
        if (!doc) return;

        const onMove = (event) => {
            sendCursor(viewportPointFromFrame(frame, event));
        };
        const onDown = (event) => {
            if (event.pointerType === "touch") {
                sendCursor(viewportPointFromFrame(frame, event));
            }
        };

        doc.addEventListener("pointermove", onMove, { passive: true });
        doc.addEventListener("pointerdown", onDown, { passive: true });
        state.iframeListeners.set(frame, { doc, onMove, onDown });
    }

    function scanCalendarFrames() {
        document.querySelectorAll("iframe").forEach((frame) => {
            attachCalendarFrame(frame);
        });
    }

    function startCalendarFrameTracking() {
        scanCalendarFrames();
        if (!state.iframeObserver) {
            state.iframeObserver = new MutationObserver(() => scanCalendarFrames());
            state.iframeObserver.observe(document.body, { childList: true, subtree: true });
        }
        if (!state.iframeScanTimer) {
            state.iframeScanTimer = window.setInterval(scanCalendarFrames, 1000);
        }
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

            const updatePeerCount = () => {
                if (!state.channel) {
                    state.peerCount = 0;
                    return;
                }

                const presenceState = state.channel.presenceState();
                state.peerCount = Object.keys(presenceState).filter(
                    (key) => key !== config.sessionId
                ).length;

                // A peer just appeared. Send the most recent local position once
                // so they don't have to wait for the next pointer movement.
                if (state.peerCount > 0 && state.pendingCursor && state.ready) {
                    const pending = state.pendingCursor;
                    state.pendingCursor = null;
                    sendCursor(pending, true);
                }
            };

            state.channel
                .on("broadcast", { event: "cursor" }, ({ payload }) => {
                    renderCursor(payload);
                })
                .on("presence", { event: "sync" }, () => {
                    updatePeerCount();
                })
                .on("presence", { event: "join" }, () => {
                    updatePeerCount();
                })
                .on("presence", { event: "leave" }, ({ key }) => {
                    removeCursor(key);
                    updatePeerCount();
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

                    updatePeerCount();

                    if (state.peerCount > 0 && state.pendingCursor) {
                        const pending = state.pendingCursor;
                        state.pendingCursor = null;
                        sendCursor(pending, true);
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

    startCalendarFrameTracking();
    updateIdentity();
    startRealtime();

    return () => {
        document.removeEventListener("pointermove", handlePointerMove);
        document.removeEventListener("pointerdown", handlePointerDown);

        if (state.sendTimer) {
            clearTimeout(state.sendTimer);
            state.sendTimer = null;
        }
        state.peerCount = 0;
        if (state.iframeScanTimer) {
            clearInterval(state.iframeScanTimer);
            state.iframeScanTimer = null;
        }
        if (state.iframeObserver) {
            state.iframeObserver.disconnect();
            state.iframeObserver = null;
        }
        state.cursors.forEach((cursor) => {
            if (cursor.staleTimer) {
                clearTimeout(cursor.staleTimer);
            }
            cursor.element.remove();
        });
        state.cursors.clear();
        state.iframeListeners.forEach(({ doc, onMove, onDown }) => {
            try {
                doc.removeEventListener("pointermove", onMove);
                doc.removeEventListener("pointerdown", onDown);
            } catch (error) {
                // The iframe may already have been destroyed.
            }
        });
        state.iframeListeners.clear();

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
