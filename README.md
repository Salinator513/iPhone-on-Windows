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
| See the screen | poll WDA `/screenshot` (PNG) | ✅ works (low FPS) |
| Tap / swipe | WDA W3C pointer actions | ✅ |
| Type text | WDA `/wda/keys` into focused field | ✅ |
| Home button | WDA `/wda/homescreen` | ✅ |
| Read on-screen text | WDA accessibility source | ✅ |
| Clipboard both ways | WDA `get/setPasteboard` | ✅ (WDA must be foreground) |
| Smooth high-FPS video | **QVH** over USB | 🔜 roadmap (see below) |

> The screenshot-poll mirror is intentionally simple (a few FPS). For a fluid,
> high-frame-rate picture, [QVH](https://github.com/danielpaulus/quicktime_video_hack)
> taps the hidden QuickTime USB video stream — that's the planned upgrade for the
> video path. Control stays on WDA either way.

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

Click = tap · drag = swipe · use the side panel for typing, text, and clipboard.

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
- Built and reviewed without a physical device in the loop, so the **control
  endpoints follow standard WDA conventions but haven't been exercised against a
  live phone** — expect to tweak an endpoint or two per your WDA build. The
  server, web UI, and status checks run without a device.

## License

MIT — see [LICENSE](LICENSE).
