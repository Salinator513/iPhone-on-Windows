// iPhone on Windows — tiny front-end.
// Polls WDA screenshots for the picture, maps mouse/keyboard onto WDA control.

const screen = document.getElementById("screen");
const offline = document.getElementById("offline");
const statusEl = document.getElementById("status");

let fps = 5; // overwritten by /api/status
let dragStart = null;

function postJSON(path, body) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  }).then((r) => r.json());
}

// ---- screenshot mirror -------------------------------------------------
function refreshScreen() {
  const img = new Image();
  img.onload = () => {
    screen.src = img.src;
    screen.classList.remove("hidden");
    offline.classList.add("hidden");
  };
  img.onerror = () => {
    screen.classList.add("hidden");
    offline.classList.remove("hidden");
  };
  img.src = "/api/screenshot?t=" + Date.now();
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

// ---- side-panel actions ------------------------------------------------
document.getElementById("home").onclick = () => postJSON("/api/home");

document.getElementById("type-btn").onclick = () => {
  const input = document.getElementById("type-input");
  if (input.value) postJSON("/api/type", { text: input.value });
};

document.getElementById("get-text").onclick = async () => {
  const r = await fetch("/api/text").then((r) => r.json());
  document.getElementById("text-out").textContent = r.source || r.error || "(empty)";
};

document.getElementById("clip-get").onclick = async () => {
  const r = await fetch("/api/clipboard").then((r) => r.json());
  document.getElementById("clip-input").value = r.text || "";
};
document.getElementById("clip-set").onclick = () => {
  postJSON("/api/clipboard", { text: document.getElementById("clip-input").value });
};

// ---- status bar --------------------------------------------------------
function tick(mark) {
  return mark ? "✓" : "✗";
}
async function refreshStatus() {
  try {
    const s = await fetch("/api/status").then((r) => r.json());
    if (s.screenshot_fps) fps = s.screenshot_fps;
    statusEl.textContent =
      `go-ios ${tick(s.go_ios)}   qvh ${tick(s.qvh)}   ` +
      `WDA ${s.wda_reachable ? "✓ connected" : "✗ not reachable"}`;
    statusEl.className = "status " + (s.wda_reachable ? "ok" : "bad");
  } catch (e) {
    statusEl.textContent = "backend unreachable";
    statusEl.className = "status bad";
  }
}

// ---- loops -------------------------------------------------------------
let screenTimer = null;
function startLoops() {
  refreshScreen();
  refreshStatus();
  if (screenTimer) clearInterval(screenTimer);
  screenTimer = setInterval(refreshScreen, Math.max(200, 1000 / fps));
  setInterval(refreshStatus, 3000);
}
startLoops();
