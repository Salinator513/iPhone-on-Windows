# iPhone on Windows

See **and control** your iPhone from a Windows laptop — no Mac, no jailbreak.

It drives the phone through Apple's own automation server, **WebDriverAgent
(WDA)**, launched over USB with **go-ios**. A small local web app shows the
screen and turns your mouse/keyboard into taps, swipes, and text.

```
  iPhone (USB)                Windows laptop
 ┌────────────┐   USB    ┌──────────────────────────────┐
 │  WDA app   │◀────────▶│  go-ios  (launch + port 8100) │
 │ (on-device)│          │            │                  │
 └────────────┘          │            ▼                  │
                         │   FastAPI backend (server/)    │
                         │   • screenshot mirror          │
                         │   • tap / swipe / type         │
                         │   • on-screen text + clipboard │
                         │            │                   │
                         │            ▼                   │
                         │   Web UI (web/)  ── browser     │
                         └──────────────────────────────┘
```

## What works today

| Feature | How | Status |
|---|---|---|
| See the screen (default) | poll WDA `/screenshot` (PNG) | ✅ works (few FPS) |
| See the screen (smooth) | **QVH** → MJPEG stream | ✅ wired — needs `qvh_cmd` + a device |
| Tap / swipe | WDA W3C pointer actions | ✅ |
| Type text | WDA `/wda/keys` into focused field | ✅ |
| Physical keyboard | browser keydown → focused field | ✅ (toggle in UI) |
| Hardware buttons | home · app switcher · lock · volume | ✅ |
| Read on-screen text | WDA accessibility tree → selectable list | ✅ |
| Clipboard both ways | WDA `get/setPasteboard` | ✅ (WDA must be foreground) |
| Survives WDA restarts | session auto-recreates + retries | ✅ |

### Video modes

- **`screenshot`** (default) — polls WDA `/screenshot`, a few FPS, zero extra
  dependencies. Always works once WDA is up.
- **`qvh`** — smooth, high-frame-rate video from
  [QVH](https://github.com/danielpaulus/quicktime_video_hack), which taps the
  hidden QuickTime USB video stream. Set `"video": "qvh"` and a `qvh_cmd` that
  emits MJPEG (a `qvh | ffmpeg` pipeline — see
  [`docs/SETUP.md`](docs/SETUP.md)). The backend re-serves those frames at
  `/api/stream.mjpeg`; the UI switches to it automatically. Control stays on WDA
  either way.

## Requirements

- Windows 10/11, **Python 3.10+**
- [`go-ios`](https://github.com/danielpaulus/go-ios) on your `PATH` (the `ios` command)
- A **signed WebDriverAgent** installed on the iPhone — a **free Apple ID** is
  enough (no paid developer account). Full walkthrough in
  [`docs/SETUP.md`](docs/SETUP.md).
- (Optional) [`qvh`](https://github.com/danielpaulus/quicktime_video_hack) for the future high-FPS video path

## Quick start

```powershell
# 1. install python deps
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. get WDA running on the phone + forwarded to this PC (see docs/SETUP.md)
#    (run in an *Administrator* terminal — the iOS 17+ tunnel needs it)
.\scripts\start-wda.ps1
#    verify: open http://127.0.0.1:8100/status  → should return JSON

# 3. start the app
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
#    open http://127.0.0.1:8000
```

Click = tap · drag = swipe. The side panel has hardware buttons (home, app
switcher, lock, volume), a **keyboard-capture** toggle (your physical typing
goes to the phone's focused field), clipboard sync, and a selectable dump of the
screen's text. For smooth video instead of the screenshot poll, enable `qvh`
mode (see below).

## Config

Copy `config.example.json` to `config.json` to override defaults (WDA URL,
screenshot FPS, host/port). Defaults work for the standard setup.

## How the pieces map

- **go-ios** — talks to the iPhone over USB from Windows; installs/launches WDA,
  starts the iOS 17+ tunnel, forwards WDA's port 8100 to the PC. (Replaces the
  older, unmaintained `tidevice`, which stopped at iOS 16.)
- **WebDriverAgent** — Apple XCUITest server running *on the phone*; every
  tap/swipe/type/text/clipboard call is a REST request to it.
- **QVH** — reverse-engineered QuickTime USB video grabber for the smooth-video
  upgrade (roadmap).

## Notes / honesty

- This is **automation-grade** remote control: real, but with more setup and
  higher latency than Android's `scrcpy`. That's an Apple-platform limit, not a
  bug here.
- A **free** Apple ID re-signs WDA every **7 days** — you'll re-install weekly
  (AltStore can auto-refresh). A paid developer account lasts a year. See
  `docs/SETUP.md`.
- Built without a physical device in the loop. **Verified here:** the server,
  web UI, status checks, every endpoint's error handling, and the full MJPEG
  streaming path (with a synthetic frame source). **Not yet exercised on a live
  phone:** the actual WDA taps/swipes/keys and the real `qvh_cmd` pipeline —
  both follow standard conventions but expect to finalize `qvh_cmd` and maybe
  tweak an endpoint per your WDA build.

## License

MIT — see [LICENSE](LICENSE).
