// EEZY Robotic Arm — frontend controller.
//
// Hold-to-move: while a pad is held down, the client fires /api/move with
// HOLD_STEPS steps every HOLD_INTERVAL_MS. Release stops firing. This gives
// an analog "pressed = moving" feel while the backend still handles each
// burst as an interruptible background movement.

const HOLD_STEPS = 5;
const HOLD_INTERVAL_MS = 120;
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
// Hold-to-move on the directional pads
// -----------------------------------------------------------------
const pads = document.querySelectorAll(".pad");

// Which visual element to highlight for each axis
const axisVisual = {
    up: "viz-shoulder", down: "viz-shoulder",
    forward: "viz-elbow", backward: "viz-elbow",
    rotate_cw: "viz-base", rotate_ccw: "viz-base",
};

for (const pad of pads) {
    const axis = pad.dataset.axis;
    if (!axis) continue;

    let holdTimer = null;

    const start = (ev) => {
        ev.preventDefault();
        if (holdTimer) return;
        pad.classList.add("active");
        highlightViz(axis, true);
        // Fire immediately, then at interval while held.
        api("/move", { axis, steps: HOLD_STEPS });
        holdTimer = setInterval(
            () => api("/move", { axis, steps: HOLD_STEPS }),
            HOLD_INTERVAL_MS
        );
    };

    const stop = () => {
        if (!holdTimer) return;
        clearInterval(holdTimer);
        holdTimer = null;
        pad.classList.remove("active");
        highlightViz(axis, false);
        // Tell the backend to stop any in-flight burst so the arm halts cleanly.
        api("/stop", {});
    };

    pad.addEventListener("pointerdown", start);
    pad.addEventListener("pointerup", stop);
    pad.addEventListener("pointerleave", stop);
    pad.addEventListener("pointercancel", stop);
    // Keyboard: focus + hold space/enter
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
// Keyboard shortcuts for desk use
// -----------------------------------------------------------------
// W/S shoulder, A/D elbow, Q/E base, Space = stop
const keyMap = {
    w: "up", s: "down",
    a: "forward", d: "backward",
    q: "rotate_ccw", e: "rotate_cw",
};
const keyHoldTimers = {};
document.addEventListener("keydown", (ev) => {
    if (ev.repeat) return;
    if (ev.key === " ") { api("/stop", {}); return; }
    const axis = keyMap[ev.key.toLowerCase()];
    if (!axis || keyHoldTimers[axis]) return;
    highlightViz(axis, true);
    api("/move", { axis, steps: HOLD_STEPS });
    keyHoldTimers[axis] = setInterval(
        () => api("/move", { axis, steps: HOLD_STEPS }),
        HOLD_INTERVAL_MS
    );
});
document.addEventListener("keyup", (ev) => {
    const axis = keyMap[ev.key.toLowerCase()];
    if (!axis || !keyHoldTimers[axis]) return;
    clearInterval(keyHoldTimers[axis]);
    delete keyHoldTimers[axis];
    highlightViz(axis, false);
    api("/stop", {});
});
