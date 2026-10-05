// EEZY Robotic Arm — frontend controller.
//
// Press-and-hold model: button-down fires a single /move_start; button-up
// fires /stop. The server steps continuously in between so the motion is
// smooth, with no gaps between HTTP bursts.

const CLAW_DEBOUNCE_MS = 150;
const STATUS_POLL_MS = 400;

// -----------------------------------------------------------------
// Tiny API wrapper
// -----------------------------------------------------------------
async function api(path, body) {
    try {
        const res = await fetch(`/api${path}`, {
            method: body === undefined ? "GET" : "POST",
            headers: body ? { "Content-Type": "application/json" } : {},
            body: body ? JSON.stringify(body) : undefined,
        });
        if (!res.ok && res.status !== 409) {
            console.warn(`${path} -> ${res.status}`);
        }
        return await res.json().catch(() => ({}));
    } catch (err) {
        console.error(`${path} failed`, err);
        return null;
    }
}

// -----------------------------------------------------------------
// Directional pads: hold-to-move via start/stop
// -----------------------------------------------------------------
const pads = document.querySelectorAll(".pad");

const axisVisual = {
    up: "viz-shoulder", down: "viz-shoulder",
    forward: "viz-elbow", backward: "viz-elbow",
    rotate_cw: "viz-base", rotate_ccw: "viz-base",
};

for (const pad of pads) {
    const axis = pad.dataset.axis;
    if (!axis) continue;

    const start = (ev) => {
        ev.preventDefault();
        if (pad.classList.contains("active")) return;
        pad.classList.add("active");
        highlightViz(axis, true);
        api("/move_start", { axis });
    };

    const stop = () => {
        if (!pad.classList.contains("active")) return;
        pad.classList.remove("active");
        highlightViz(axis, false);
        api("/stop", {});
    };

    pad.addEventListener("pointerdown", start);
    pad.addEventListener("pointerup", stop);
    pad.addEventListener("pointerleave", stop);
    pad.addEventListener("pointercancel", stop);
    pad.addEventListener("keydown", (e) => {
        if (e.key === " " || e.key === "Enter") start(e);
    });
    pad.addEventListener("keyup", (e) => {
        if (e.key === " " || e.key === "Enter") stop();
    });
}

function highlightViz(axis, on) {
    const id = axisVisual[axis];
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.classList.toggle("active-viz", on);
}

// -----------------------------------------------------------------
// Stop button
// -----------------------------------------------------------------
document.getElementById("btn-stop").addEventListener("click", () => {
    api("/stop", {});
});

// -----------------------------------------------------------------
// Claw slider (debounced so dragging doesn't spam the server)
// -----------------------------------------------------------------
const claw = document.getElementById("claw");
const clawValue = document.getElementById("claw-value");
let clawTimer = null;
claw.addEventListener("input", () => {
    clawValue.textContent = `${claw.value}°`;
    if (clawTimer) clearTimeout(clawTimer);
    clawTimer = setTimeout(
        () => api("/claw", { angle: Number(claw.value) }),
        CLAW_DEBOUNCE_MS
    );
});

// -----------------------------------------------------------------
// Recorder buttons
// -----------------------------------------------------------------
document.getElementById("btn-clear").addEventListener("click", () => {
    api("/recording/clear", {});
});
document.getElementById("btn-replay").addEventListener("click", () => {
    api("/recording/replay", {});
});

// -----------------------------------------------------------------
// Status polling → updates dot, step count, last-action line
// -----------------------------------------------------------------
const statusDot = document.getElementById("status-dot");
const recCount = document.getElementById("rec-count");
const recLast = document.getElementById("rec-last");

async function pollStatus() {
    const s = await api("/status");
    if (s === null) {
        statusDot.classList.remove("online", "moving");
        statusDot.classList.add("offline");
        recLast.textContent = "disconnected";
        return;
    }
    statusDot.classList.remove("offline");
    statusDot.classList.toggle("moving", !!s.running);
    statusDot.classList.toggle("online", !s.running);
    recCount.textContent = s.recorded_steps ?? 0;
    recLast.textContent = s.last_action || "idle";
}

pollStatus();
setInterval(pollStatus, STATUS_POLL_MS);

// -----------------------------------------------------------------
// Keyboard shortcuts: W/S shoulder, A/D elbow, Q/E base, Space = stop
// -----------------------------------------------------------------
const keyMap = {
    w: "up", s: "down",
    a: "forward", d: "backward",
    q: "rotate_ccw", e: "rotate_cw",
};
const keyActive = {};
document.addEventListener("keydown", (ev) => {
    if (ev.repeat) return;
    if (ev.key === " ") { api("/stop", {}); return; }
    const axis = keyMap[ev.key.toLowerCase()];
    if (!axis || keyActive[axis]) return;
    keyActive[axis] = true;
    highlightViz(axis, true);
    api("/move_start", { axis });
});
document.addEventListener("keyup", (ev) => {
    const axis = keyMap[ev.key.toLowerCase()];
    if (!axis || !keyActive[axis]) return;
    delete keyActive[axis];
    highlightViz(axis, false);
    api("/stop", {});
});
