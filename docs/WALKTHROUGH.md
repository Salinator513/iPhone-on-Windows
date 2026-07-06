# Step-by-step walkthrough

Granular setup from zero to "I can see and control my iPhone on Windows."
Every action spelled out. Do the parts in order.

---

## Part A — Install the tools on Windows

### 1. Install Python
1. Go to <https://python.org/downloads> and click **Download Python 3.x**.
2. Run the installer.
3. **Check the box "Add python.exe to PATH"** at the bottom (important).
4. Click **Install Now**, wait, then **Close**.
5. Open **PowerShell** (Start menu → type "PowerShell" → Enter) and check:
   ```
   python --version
   ```
   You should see `Python 3.x`. If "not recognized," reinstall and re-check the PATH box.

### 2. Download the project
1. If you have git: in PowerShell run
   ```
   git clone -b claude/iphone-view-windows-bpix8q https://github.com/Salinator513/iPhone-on-Windows.git
   cd iPhone-on-Windows
   ```
2. No git? On GitHub, open the repo → switch the branch dropdown to
   `claude/iphone-view-windows-bpix8q` → **Code ▾ → Download ZIP** → unzip it →
   remember the folder.
3. Keep this PowerShell window open in that folder (`cd` into it if needed).

### 3. Install go-ios (the USB bridge — runs on the PC, not the phone)
1. Go to <https://github.com/danielpaulus/go-ios/releases>.
2. Under the latest release's **Assets**, download the **Windows** zip
   (e.g. `go-ios-win.zip`).
3. Unzip it — inside is `ios.exe`.
4. Make a folder `C:\tools`, move `ios.exe` into it.
5. Add it to PATH:
   - Start menu → type **"environment variables"** → open **Edit the system
     environment variables**.
   - Click **Environment Variables…**
   - Under **User variables**, select **Path** → **Edit… → New** → type
     `C:\tools` → **OK** on every window.
6. **Close and reopen** PowerShell, then check:
   ```
   ios -h
   ```
   You should see go-ios help text.

### 4. Fix the iTunes/iCloud driver gotcha
1. Start menu → **Add or remove programs**.
2. If you see **iTunes** or **iCloud** marked "Microsoft Store," **uninstall
   them** (the Store versions hide the phone from go-ios/Sideloadly).
3. If you need them, reinstall from <https://apple.com> (the classic installers),
   not the Store.

### 5. Install Sideloadly (signs the WDA app with a free Apple ID)
1. Go to <https://sideloadly.app>, download the **Windows** version, install it.
2. Leave it closed for now.

---

## Part B — Put WebDriverAgent on the iPhone

### 6. Get a WebDriverAgent `.ipa`
WDA is the small app that runs *on the phone* and receives taps/swipes.
1. You need a prebuilt **`WebDriverAgent*.ipa`** file. Get it from a source you
   trust — a community prebuilt runner, or build it once on a (cloud) Mac.
2. Save the `.ipa` somewhere easy like your Downloads folder.

> This is the fiddliest step because Apple doesn't publish a ready-made `.ipa`.
> If you can't find a trusted prebuilt one, a one-time build on a rented cloud
> Mac (then reuse the `.ipa` forever) is the reliable route.

### 7. Plug in the iPhone and trust the PC
1. Connect the iPhone to the laptop with a USB cable.
2. On the phone a **"Trust This Computer?"** popup appears → tap **Trust** →
   enter your passcode.
3. Back in PowerShell, confirm go-ios sees it:
   ```
   ios list
   ```
   A device UDID (long string) should print.

### 8. Sign + install WDA with Sideloadly
1. Open **Sideloadly**.
2. **Drag your WDA `.ipa`** into the Sideloadly window (or click the box and
   pick it).
3. In the **Apple ID** field, type your Apple ID email (a **free** one is fine).
4. Click **Start**.
5. When prompted, enter your Apple ID **password** (and the **2FA code** if asked).
6. Watch the log at the bottom — it should end with **"Done"** / success. WDA is
   now installed on the phone.

> **Free Apple ID = 7-day limit.** After a week WDA stops launching; just repeat
> step 8 to reinstall. (A paid $99/yr Apple Developer account lasts a year.)

### 9. Trust the developer profile on the phone
1. On the iPhone: **Settings → General → VPN & Device Management**.
2. Under **Developer App**, tap your Apple ID.
3. Tap **Trust "…"** → **Trust** in the confirmation.

### 10. Turn on Developer Mode (iOS 16 and newer)
1. On the iPhone: **Settings → Privacy & Security**.
2. Scroll down to **Developer Mode** → toggle it **On**.
3. The phone asks to **restart** → tap **Restart**.
4. After reboot, a prompt appears → tap **Turn On** → enter passcode.

---

## Part C — Start the bridge (WDA + port forward)

### 11. Open PowerShell as Administrator
1. Start menu → type **PowerShell**.
2. Right-click **Windows PowerShell → Run as administrator** → **Yes**.
3. `cd` into the project folder, e.g.:
   ```
   cd C:\Users\<you>\iPhone-on-Windows
   ```

### 12. Run the launch script
1. Run:
   ```
   .\scripts\start-wda.ps1
   ```
2. If you get a script-blocked error, run this once then retry:
   ```
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
3. Three windows/steps happen: **tunnel** (needs admin), **runwda** (launches
   WDA on the phone), **forward** (pipes port 8100 to the PC). **Leave those
   windows open** — closing them stops the bridge.

   *Manual equivalent if the script misbehaves — one command per window:*
   ```
   ios tunnel start          # admin window; leave open (iOS 17+)
   ios runwda                # leave open
   ios forward 8100 8100     # leave open
   ```

### 13. Verify WDA is alive
1. Open a browser to <http://127.0.0.1:8100/status>.
2. You should see JSON containing `"state" : "success"`.
3. Nothing / error? WDA isn't running or the signature expired — redo steps 8
   and 12. (See Troubleshooting.)

---

## Part D — Run the app

### 14. Create the environment + install dependencies (first time only)
In a **normal** (non-admin) PowerShell, in the project folder:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then retry.

### 15. Start the server
```
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```
Leave it running. You'll see `Uvicorn running on http://127.0.0.1:8000`.

### 16. Open the app
1. Browser → <http://127.0.0.1:8000>.
2. The status bar (top right) should read **`WDA ✓ connected`**.
3. Your phone screen appears in the frame. 🎉

---

## Part E — Using it

- **Click** the screen = tap. **Click-drag** = swipe.
- **Buttons row:** home · app switcher · lock · volume up/down.
- **Keyboard:** tick **"Capture my keyboard"**, then whatever you type on the
  laptop goes to the phone's focused field (Enter/Backspace work).
- **Clipboard:** "From phone" pulls the phone's clipboard to the box; "To phone"
  pushes the box's text to the phone. (Reads need WDA in the foreground.)
- **Fetch text:** dumps the current screen's text as a selectable list you can
  copy.
- **Smooth video:** the default is a few-FPS screenshot mirror. For fluid video,
  set up `qvh` mode — see the "Optional: smooth video with QVH" section of
  [SETUP.md](SETUP.md).

---

## Every time after the first

You only repeat:
1. Plug in the phone.
2. Admin PowerShell → `.\scripts\start-wda.ps1` → check `:8100/status`.
3. Normal PowerShell → `.\.venv\Scripts\Activate.ps1` → `python -m uvicorn server.main:app --host 127.0.0.1 --port 8000`.
4. Open <http://127.0.0.1:8000>.

(If a week has passed, also redo step 8 to re-sign WDA.)

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ios list` shows nothing | Reconnect cable; tap **Trust** on the phone; uninstall Store iTunes/iCloud (step 4). |
| `:8100/status` fails | WDA not running or signature expired (7-day free-ID limit) — redo steps 8 + 12. |
| `runwda` errors on iOS 17+ | The `ios tunnel start` admin window isn't running (step 12). |
| Script won't run | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then retry. |
| Status shows `WDA ✗ not reachable` | Redo Part C; make sure the forward window is still open. |
| Taps land slightly off | The backend auto-scales to WDA's window size; if it persists, note your WDA version in an issue. |
| Clipboard "From phone" is empty | iOS only allows reads while WDA is in the foreground on the phone. |
