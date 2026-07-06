// iPhone on Windows — front-end.
// Video: MJPEG stream when qvh is configured, else chained screenshot polling.
// Control: mouse → tap/swipe, optional physical keyboard → focused field.

const screen = document.getElementById("screen");
const offline = document.getElementById("offline");
const statusEl = document.getElementById("status");

let fps = 5; // from /api/status
let videoMode = "screenshot"; // or "qvh"
let dragStart = null;
let screenTimer = null;

function postJSON(path, body) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  }).then((r) => r.json());
}

// ---- video -------------------------------------------------------------
function onFrameOk() {
  screen.classList.remove("hidden");
  offline.classList.add("hidden");
}
function onFrameFail() {
  screen.classList.add("hidden");
  offline.classList.remove("hidden");
}

function pollScreenshot() {
  // chain requests: fetch the next frame only once the current one decodes,
  // so a slow phone/USB link never piles up in-flight requests.
  const img = new Image();
  img.onload = () => {
    screen.src = img.src;
    onFrameOk();
    screenTimer = setTimeout(pollScreenshot, Math.max(0, 1000 / fps - 30));
  };
  img.onerror = () => {
    onFrameFail();
    screenTimer = setTimeout(pollScreenshot, 1000);
  };
  img.src = "/api/screenshot?t=" + Date.now();
}

function startVideo() {
  if (screenTimer) {
    clearTimeout(screenTimer);
    screenTimer = null;
  }
  if (videoMode === "qvh") {
    screen.onload = onFrameOk;
    screen.onerror = onFrameFail;
    screen.src = "/api/stream.mjpeg";
  } else {
    screen.onload = null;
    screen.onerror = null;
    pollScreenshot();
  }
}

// ---- click → tap, drag → swipe ----------------------------------------
function normCoords(ev) {
  const rect = screen.getBoundingClientRect();
  const x = (ev.clientX - rect.left) / rect.width;
  const y = (ev.clientY - rect.top) / rect.height;
  return { x: Math.min(Math.max(x, 0), 1), y: Math.min(Math.max(y, 0), 1) };
}
screen.addEventListener("mousedown", (ev) => {
  dragStart = normCoords(ev);
});
screen.addEventListener("mouseup", (ev) => {
  if (!dragStart) return;
  const end = normCoords(ev);
  const moved = Math.hypot(end.x - dragStart.x, end.y - dragStart.y);
  if (moved < 0.02) {
    postJSON("/api/tap", { x: dragStart.x, y: dragStart.y });
  } else {
    postJSON("/api/swipe", {
      x1: dragStart.x, y1: dragStart.y, x2: end.x, y2: end.y, duration_ms: 300,
    });
  }
  dragStart = null;
});

// ---- hardware buttons --------------------------------------------------
document.querySelectorAll(".buttons button").forEach((btn) => {
  btn.onclick = () => {
    const act = btn.dataset.act;
    if (act === "home") postJSON("/api/home");
    else if (act === "recents") postJSON("/api/recents");
    else if (act === "lock") postJSON("/api/lock");
    else postJSON("/api/button/" + act);
  };
});

// ---- keyboard ----------------------------------------------------------
const kbdToggle = document.getElementById("kbd-toggle");
function onKeyDown(ev) {
  if (ev.metaKey || ev.ctrlKey || ev.altKey) return; // let shortcuts through
  let key = null;
  if (ev.key === "Enter") key = "\n";
  else if (ev.key === "Backspace") key = "\b";
  else if (ev.key === "Tab") key = "\t";
  else if (ev.key.length === 1) key = ev.key;
  if (key === null) return;
  ev.preventDefault();
  postJSON("/api/keys", { keys: [key] });
}
kbdToggle.addEventListener("change", () => {
  if (kbdToggle.checked) document.addEventListener("keydown", onKeyDown);
  else document.removeEventListener("keydown", onKeyDown);
});

document.getElementById("type-btn").onclick = () => {
  const input = document.getElementById("type-input");
  if (input.value) postJSON("/api/type", { text: input.value });
};

// ---- text / clipboard --------------------------------------------------
document.getElementById("get-text").onclick = async () => {
  const out = document.getElementById("text-out");
  const r = await fetch("/api/text").then((r) => r.json());
  out.textContent = "";
  const lines = r.lines || [];
  if (!lines.length) {
    out.textContent = r.error || "(no text found)";
    return;
  }
  for (const line of lines) {
    const div = document.createElement("div");
    div.textContent = line;
    out.appendChild(div);
  }
};

document.getElementById("clip-get").onclick = async () => {
  const r = await fetch("/api/clipboard").then((r) => r.json());
  document.getElementById("clip-input").value = r.text || "";
};
document.getElementById("clip-set").onclick = () => {
  postJSON("/api/clipboard", { text: document.getElementById("clip-input").value });
};

// ---- status ------------------------------------------------------------
const tick = (ok) => (ok ? "✓" : "✗");
async function refreshStatus() {
  try {
    const s = await fetch("/api/status").then((r) => r.json());
    if (s.screenshot_fps) fps = s.screenshot_fps;
    const wantMode = s.qvh_stream ? "qvh" : "screenshot";
    if (wantMode !== videoMode) {
      videoMode = wantMode;
      startVideo();
    }
    statusEl.textContent =
      `go-ios ${tick(s.go_ios)}   qvh ${tick(s.qvh)}   ` +
      `WDA ${s.wda_reachable ? "✓ connected" : "✗ not reachable"}   ` +
      `[${videoMode}]`;
    statusEl.className = "status " + (s.wda_reachable ? "ok" : "bad");
  } catch (e) {
    statusEl.textContent = "backend unreachable";
    statusEl.className = "status bad";
  }
}

// ---- boot --------------------------------------------------------------
startVideo();
refreshStatus();
setInterval(refreshStatus, 3000);
