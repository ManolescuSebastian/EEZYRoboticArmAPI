// EEZY Robotic Arm — frontend controller.
//
// Press-and-hold model: button-down fires a single /move_start; button-up
// fires /stop. The server steps continuously in between so the motion is
// smooth, with no gaps between HTTP bursts.

const CLAW_DEBOUNCE_MS = 150;
const SPEED_DEBOUNCE_MS = 60;   // low so the "live" feel is responsive
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

// All axis names we animate — used to clear any stale class on stop.
const ALL_AXES = ["up", "down", "forward", "backward", "rotate_cw", "rotate_ccw"];

function setAxisAnim(axis, on) {
    // Clear every anim-* class first so holding two different axes in a row
    // doesn't leave a stale pose. Then set the one we want.
    for (const a of ALL_AXES) document.body.classList.remove(`anim-${a}`);
    if (on && axis) document.body.classList.add(`anim-${axis}`);
}

for (const pad of pads) {
    const axis = pad.dataset.axis;
    if (!axis) continue;

    const start = (ev) => {
        ev.preventDefault();
        if (pad.classList.contains("active")) return;
        pad.classList.add("active");
        setAxisAnim(axis, true);
        api("/move_start", { axis });
    };

    const stop = () => {
        if (!pad.classList.contains("active")) return;
        pad.classList.remove("active");
        setAxisAnim(axis, false);
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
function updateClawVisual(angle) {
    // Pass raw angle to the CSS; the stylesheet converts to a rotation per finger.
    document.documentElement.style.setProperty("--claw-open", angle);
}
claw.addEventListener("input", () => {
    clawValue.textContent = `${claw.value}°`;
    updateClawVisual(Number(claw.value));  // live, feels instant
    if (clawTimer) clearTimeout(clawTimer);
    clawTimer = setTimeout(
        () => api("/claw", { angle: Number(claw.value) }),
        CLAW_DEBOUNCE_MS
    );
});
updateClawVisual(Number(claw.value));  // initial state

// -----------------------------------------------------------------
// Speed slider (live — changes apply mid-movement)
// -----------------------------------------------------------------
const speed = document.getElementById("speed");
const speedValue = document.getElementById("speed-value");
let speedTimer = null;
speed.addEventListener("input", () => {
    speedValue.textContent = speed.value;
    if (speedTimer) clearTimeout(speedTimer);
    speedTimer = setTimeout(
        () => api("/speed", { value: Number(speed.value) }),
        SPEED_DEBOUNCE_MS
    );
});

// -----------------------------------------------------------------
// Recorder buttons (Rec toggles start/stop; Replay plays last recording)
// -----------------------------------------------------------------
const btnRecord = document.getElementById("btn-record");
let recording = false;

function setRecordingUI(on) {
    recording = on;
    btnRecord.classList.toggle("recording", on);
    btnRecord.textContent = on ? "■ Stop" : "● Rec";
}

btnRecord.addEventListener("click", async () => {
    if (recording) {
        await api("/recording/stop", {});
        setRecordingUI(false);
    } else {
        await api("/recording/start", {});
        setRecordingUI(true);
    }
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
const recIndicator = document.getElementById("rec-indicator");

// Avoid clobbering the sliders while the user is actively dragging them.
let userDraggingSpeed = false;
let userDraggingClaw = false;
speed.addEventListener("pointerdown", () => { userDraggingSpeed = true; });
speed.addEventListener("pointerup",   () => { userDraggingSpeed = false; });
claw.addEventListener("pointerdown",  () => { userDraggingClaw = true; });
claw.addEventListener("pointerup",    () => { userDraggingClaw = false; });

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

    // Keep the record indicator & button in sync with the server (so a page
    // reload or a second client doesn't get out of step).
    recIndicator.classList.toggle("on", !!s.recording);
    if (!!s.recording !== recording) setRecordingUI(!!s.recording);

    // Reflect server-side speed if the user isn't currently dragging the slider.
    if (!userDraggingSpeed && typeof s.speed === "number") {
        const rounded = Math.round(s.speed);
        if (String(rounded) !== speed.value) {
            speed.value = rounded;
            speedValue.textContent = rounded;
        }
    }
    // Same for claw.
    if (!userDraggingClaw && typeof s.claw_angle === "number") {
        const rounded = Math.round(s.claw_angle);
        if (String(rounded) !== claw.value) {
            claw.value = rounded;
            clawValue.textContent = `${rounded}°`;
            updateClawVisual(rounded);
        }
    }
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
    setAxisAnim(axis, true);
    api("/move_start", { axis });
});
document.addEventListener("keyup", (ev) => {
    const axis = keyMap[ev.key.toLowerCase()];
    if (!axis || !keyActive[axis]) return;
    delete keyActive[axis];
    setAxisAnim(axis, false);
    api("/stop", {});
});
