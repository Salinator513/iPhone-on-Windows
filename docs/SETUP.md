# Setup — getting WebDriverAgent running (Mac-free)

This is the one-time-ish part: put a **signed** WebDriverAgent (WDA) on your
iPhone and launch it from Windows. No Mac required — a **free Apple ID** signs
it.

## 0. Install the tools

- **Python 3.10+** — https://python.org
- **go-ios** (`ios` command) — https://github.com/danielpaulus/go-ios
  (download the release, put it on your `PATH`, check with `ios list`)
- **Sideloadly** — https://sideloadly.app (signs & installs the WDA `.ipa`)
- Latest **iTunes/iCloud drivers**, but **not** the Microsoft Store versions —
  the Store builds are sandboxed and hide the USB device from Sideloadly/go-ios.
  Uninstall the Store versions and use the ones from apple.com.

## 1. Get a WebDriverAgent `.ipa`

You need a pre-built, installable WDA. Grab a `WebDriverAgent*.ipa` from a
trusted release (the Appium/WDA community publishes them), or build one if you
have access to a Mac. Keep the file handy.

## 2. Sign + install it with Sideloadly (free Apple ID)

1. Plug the iPhone into the laptop via USB, trust the computer on the phone.
2. Open **Sideloadly**, drag the WDA `.ipa` in.
3. Enter your **Apple ID** (a free one works). Sideloadly asks Apple for a free
   signing certificate; if you have 2FA, enter the code.
4. Hit **Start**. Sideloadly signs and installs WDA onto the phone.

> **Free Apple ID limits:** the signature is valid **7 days**, then WDA stops
> launching until you re-install it (repeat this step). You're also limited to
> ~3 sideloaded apps at once. A **paid Apple Developer account ($99/yr)** makes
> the signature last a year. [AltStore](https://altstore.io) can auto-refresh in
> the background on the same Wi-Fi to dodge the weekly re-install.

## 3. Trust the app + enable Developer Mode (iOS 16+)

- On the phone: **Settings → General → VPN & Device Management** → trust your
  Apple ID's developer profile.
- iOS 16+: **Settings → Privacy & Security → Developer Mode → On**, then reboot
  and confirm.

## 4. Launch WDA + forward the port

In an **Administrator** terminal (the iOS 17+ tunnel needs admin):

```powershell
ios list                     # confirm the device shows up

# iOS 17+ only: start the tunnel and LEAVE IT RUNNING (admin required)
ios tunnel start

# in another terminal: launch WDA on the phone
ios runwda
#   if the default bundle id doesn't match your ipa, pass it explicitly:
#   ios runwda --bundleid=<your.wda.bundleid> \
#              --testrunnerbundleid=<your.wda.bundleid> \
#              --xctestconfig=WebDriverAgentRunner.xctest

# in another terminal: forward WDA's port 8100 to this PC
ios forward 8100 8100
```

Or just run the helper: `./scripts/start-wda.ps1` (it opens the tunnel, WDA,
and forward in separate windows).

**Verify:** open <http://127.0.0.1:8100/status> — you should get a JSON blob
with `"state": "success"`. That means WDA is alive and reachable. 🎉

## 5. Run the app

```powershell
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The status bar shows whether `go-ios`, `qvh`, and
WDA are detected.

## Optional: smooth video with QVH

The default `screenshot` mode needs nothing extra. For fluid, high-FPS video:

1. Install [`qvh`](https://github.com/danielpaulus/quicktime_video_hack) **and
   `ffmpeg`**, both on your `PATH`.
2. Confirm qvh sees the phone (it uses the same USB device go-ios does).
3. In `config.json` set `video` to `qvh` and a `qvh_cmd` that writes **MJPEG
   (concatenated JPEG frames) to stdout**:

   ```json
   {
     "video": "qvh",
     "qvh_cmd": ["cmd", "/c", "qvh gstreamer <emit h264...> | ffmpeg -i - -f mpjpeg -"]
   }
   ```

The app runs `qvh_cmd`, splits its stdout into JPEG frames, and re-serves them at
`/api/stream.mjpeg`; the UI switches to it automatically. The command only has to
emit MJPEG on stdout — the usual shape is:

```
qvh (QuickTime USB video) → H.264 → ffmpeg → MJPEG (stdout)
```

Run `qvh gstreamer --examples` to see the exact streaming pipelines your qvh
build supports, then transcode to `mjpeg` with ffmpeg. Because those flags vary
by qvh version and platform, **`qvh_cmd` is the one value to finalize against
your device** — until it's set, the app stays in the (always-working)
screenshot mode.

## Troubleshooting

- **`ios list` shows nothing** → cable/trust issue, or Microsoft-Store
  iTunes/iCloud is shadowing the device. Reinstall the apple.com drivers.
- **`8100/status` fails** → WDA isn't running or the signature expired (free ID,
  7-day limit) — re-run steps 2 and 4.
- **`runwda` errors on iOS 17+** → the tunnel (`ios tunnel start`, admin) isn't
  running.
- **Taps land in the wrong place** → your WDA reports a different window size;
  the backend scales normalized coords by WDA's `window/size`, so this usually
  self-corrects. If not, check the WDA version's coordinate space.
- **`getPasteboard` returns empty** → iOS only allows pasteboard reads while WDA
  is in the foreground.
