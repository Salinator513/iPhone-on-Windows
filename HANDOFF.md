# Handoff — iPhone on Windows

_Last updated: 2026-07-06 · Branch: `claude/iphone-view-windows-bpix8q`_

Pick-up notes for whoever continues this (future session or another person).
Two threads are in flight: **(1) the software** (built, mostly done) and
**(2) helping a non-technical user set it up** (in progress, just started).

---

## TL;DR

Goal: **see and control an iPhone from a Windows laptop, no Mac, no jailbreak.**
The Windows-side software is **feature-complete and pushed**. What remains is
**device-side**: getting a signed WebDriverAgent onto a real phone and
finalizing the one QVH command. We're currently walking a non-technical user
through setup **one step at a time**; they haven't installed anything yet, and
the known blocker ahead is getting the WebDriverAgent `.ipa`.

---

## What we're building

- **View + control**: a local web app on Windows shows the iPhone screen and
  turns mouse/keyboard into taps, swipes, and text.
- Control runs through Apple's own automation server, **WebDriverAgent (WDA)**,
  which runs *on the phone* and is launched over USB by **go-ios**.

## Key decisions (so they don't get re-litigated)

- **Control = WebDriverAgent.** Consumer mirroring apps (AirDroid Cast, etc.) are
  **view-only**; WDA (Appium/XCUITest) is the only real way to *control* an
  iPhone from Windows without a jailbreak.
- **Launch/forward = go-ios**, not tidevice. The original `tidevice` stopped at
  iOS 16; go-ios (same author as QVH) supports current iOS incl. the iOS 17+
  tunnel.
- **Signing = Sideloadly + a FREE Apple ID.** No Mac and no paid developer
  account needed. Trade-off: a free Apple ID's signature **expires every 7 days**
  → re-install WDA weekly (AltStore can auto-refresh). Paid ($99/yr) = 1 year.
- **Video**: default is a **screenshot-poll mirror** (few FPS, zero deps, always
  works). **QVH** (hidden QuickTime USB video stream) is the **high-FPS upgrade**,
  wired as an MJPEG stream and opt-in via config.
- **Backend = Python/FastAPI** orchestrating the external Go binaries (go-ios,
  qvh) and proxying WDA's HTTP API.

---

## Repo layout

```
server/
  main.py     FastAPI app: static UI + /api/* endpoints, error handling
  wda.py      WDA client: session (auto-recovery), tap/swipe/keys, buttons,
              lock, text extraction, clipboard
  video.py    FrameSource: runs a configurable MJPEG command, splits JPEG frames
  config.py   loads config.json / config.example.json
web/
  index.html, app.js, style.css   browser UI (screenshot or MJPEG, controls)
scripts/
  start-wda.ps1   Windows: tunnel + runwda + forward 8100 (finds ./ios.exe)
  start-wda.sh    macOS/Linux equivalent
docs/
  WALKTHROUGH.md  beginner, click-by-click setup (the doc we're guiding from)
  SETUP.md        concise setup + the QVH video (qvh_cmd) instructions
config.example.json, requirements.txt, README.md, LICENSE
```

---

## Status

### Done & verified here (no device needed)
- Server boots; `/api/health`, `/api/status`, static UI all serve.
- Every control endpoint returns clean errors with **no phone**: graceful `502`
  when WDA is down, `422` on bad input, `400` on unknown button.
- **Full MJPEG streaming path** verified against a synthetic frame source
  (correct `multipart/x-mixed-replace`, frame headers, chunk-boundary parsing).
- `server/video.py` FrameSource unit-tested (3 frames across split chunks).

### Built, but NOT yet exercised on a real phone
- Actual WDA taps/swipes/typing/buttons/clipboard (endpoints follow standard
  WDA conventions; may need a per-build tweak).
- The real **`qvh_cmd`** pipeline (qvh → ffmpeg → MJPEG). The app plumbing is
  done; the exact qvh command must be finalized on-device via
  `qvh gstreamer --examples`.

---

## Open work items

1. **Get a WebDriverAgent `.ipa`** — the user's immediate blocker (Step 6 of the
   walkthrough). Apple ships none; options are a trusted prebuilt runner or a
   one-time build on a (cloud) Mac. Help the user choose safely.
2. **Live-test WDA control** once WDA runs — confirm tap/swipe/keys/buttons/
   clipboard endpoints; fix any endpoint-shape mismatches per their WDA build.
3. **Finalize `qvh_cmd`** for smooth video (needs qvh + ffmpeg on the device).
4. Optional: open a PR for this branch (not opened yet — user hasn't asked).

---

## Where the human is

- **Non-technical.** Earlier drafts confused them (jargon, "git / no-git" forks),
  so `docs/WALKTHROUGH.md` was rewritten to a **single path with every term
  explained**, and `start-wda.ps1` was changed so `ios.exe` just lives in the
  project folder (no PATH editing).
- We agreed to go **one step at a time** interactively. They were handed **Step 1
  (install Python)** and haven't reported back yet.
- Nothing is installed on their machine yet; no phone connected yet.

## How to resume

- **If continuing the setup:** wait for the user's "done"/error on the current
  step, then hand them the next step from `docs/WALKTHROUGH.md`. Keep it to one
  step at a time. Expect the `.ipa` (Step 6) to be where they get stuck — offer
  concrete help there.
- **If continuing dev:** work the Open Work Items above. The venv here is
  `.venv` (gitignored); `pip install -r requirements.txt` then
  `python -m uvicorn server.main:app` to run.

---

## Commits (this branch, newest first)

- `4b64008` Rewrite walkthrough for non-technical users; simplify go-ios setup
- `c84c46b` Add click-by-click setup walkthrough
- `7398086` Complete the Windows side: QVH video, keyboard, buttons, text, resilience
- `d973783` Scaffold iPhone mirror-and-control app (WDA + go-ios)

## References

- WebDriverAgent — https://github.com/appium/WebDriverAgent
- go-ios — https://github.com/danielpaulus/go-ios
- QVH (quicktime_video_hack) — https://github.com/danielpaulus/quicktime_video_hack
- Sideloadly — https://sideloadly.app
