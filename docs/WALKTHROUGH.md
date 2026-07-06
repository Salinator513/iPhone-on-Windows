# Complete beginner walkthrough

No prior knowledge assumed. One single path — just do each step in order.

### A few words you'll see
- **PowerShell** — a window where you type commands. It comes free with Windows.
  You'll open it a couple of times below; I show you exactly how each time.
- **Folder** — a normal Windows folder, like you see in File Explorer.
- **`.ipa`** — the file type for an iPhone app (like `.exe` is for Windows).

---

## STEP 1 — Install Python (the language the app runs on)

1. Open a web browser, go to **https://python.org/downloads**
2. Click the big **Download Python** button.
3. Open the file it downloads (bottom of the browser, or your Downloads folder).
4. In the installer window, **tick the checkbox at the bottom that says
   "Add python.exe to PATH."** (This matters — don't skip it.)
5. Click **Install Now**. Wait until it says success, then click **Close**.

---

## STEP 2 — Download the project files

1. Make sure you're **signed in to GitHub** in your browser (the account that
   owns this project).
2. Click this link — it downloads the project as a zip:
   **https://github.com/Salinator513/iPhone-on-Windows/archive/refs/heads/claude/iphone-view-windows-bpix8q.zip**
3. Open your **Downloads** folder in File Explorer. You'll see a zip file named
   like `iPhone-on-Windows-claude-...zip`.
4. **Right-click it → "Extract All…" → Extract.** This makes a normal folder.
5. Open that folder. Inside you'll see another folder (also starting with
   `iPhone-on-Windows`). **That inner folder is your project folder** — the one
   with `README.md`, `server`, `web`, `scripts` inside it.
6. To keep things simple, **move that project folder to your Desktop** and
   rename it to just **`iPhone-on-Windows`**.

From now on, "the project folder" = this folder on your Desktop.

---

## STEP 3 — Get go-ios (connects the PC to the iPhone over USB)

1. Go to **https://github.com/danielpaulus/go-ios/releases**
2. Under the newest release, find **Assets** and download the **Windows** file
   (its name has `win` in it, e.g. `go-ios-win.zip`).
3. In Downloads, **right-click that zip → Extract All… → Extract.**
4. Inside the extracted folder there's a file named **`ios.exe`**.
5. **Copy `ios.exe` and paste it directly into your project folder** (next to
   `README.md`). That's it — no settings to change.

---

## STEP 4 — Install Sideloadly (puts the iPhone app on your phone)

1. Go to **https://sideloadly.app**
2. Download the **Windows** version and install it (open the downloaded file,
   click through).
3. Close it for now.

---

## STEP 5 — Remove the wrong iTunes/iCloud (a common blocker)

1. Press the **Start** button, type **"Add or remove programs"**, open it.
2. Scroll the list. If you see **iTunes** or **iCloud** and it says
   **"Microsoft Store"** under the name, click it → **Uninstall.**
   (The Store versions block the phone connection. If you don't have them,
   skip this step.)

---

## STEP 6 — Get the WebDriverAgent app file (the tricky one)

You need a file named **`WebDriverAgent....ipa`**. This is the app that will run
*on your iPhone* and receive your taps.

- Apple doesn't hand out a ready-made one, so you download a pre-made copy from a
  source you trust, **or** build one once on a rented Mac.
- **This is the one genuinely hard step.** If you're not sure where to get it,
  stop here and tell me — I'll help you find or build it. Don't guess with a
  random download.

Save the `.ipa` in your **Downloads** folder once you have it.

---

## STEP 7 — Plug in your iPhone

1. Connect the iPhone to the laptop with a USB cable.
2. On the **iPhone**, a popup says **"Trust This Computer?"** → tap **Trust** →
   type your passcode.

---

## STEP 8 — Put WebDriverAgent onto the phone with Sideloadly

1. Open **Sideloadly**.
2. **Drag your `WebDriverAgent….ipa` file into the Sideloadly window.**
3. In the box labeled **Apple ID**, type your Apple ID email. A **free** Apple ID
   is fine — you do NOT need a paid account.
4. Click **Start** (bottom right).
5. It asks for your Apple ID **password** → type it. If your Apple ID uses a
   verification code, type that too.
6. Watch the messages at the bottom. When it finishes with **"Done"**, the app
   is on your phone.

> **Note:** with a free Apple ID this app **stops working after 7 days.** When
> that happens, just repeat Step 8 to put it back.

---

## STEP 9 — Tell the iPhone to trust the app

1. On the **iPhone**: open **Settings**.
2. Tap **General** → **VPN & Device Management.**
3. Under **Developer App**, tap your Apple ID email.
4. Tap **Trust "…"**, then **Trust** again to confirm.

---

## STEP 10 — Turn on Developer Mode (iPhones on iOS 16 or newer)

1. On the **iPhone**: **Settings** → **Privacy & Security.**
2. Scroll to the bottom → tap **Developer Mode** → turn the switch **On.**
3. It asks to restart the phone → tap **Restart.**
4. After it restarts, a message pops up → tap **Turn On** → enter your passcode.

---

## STEP 11 — Start the connection (special "Administrator" window)

1. Press **Start**, type **PowerShell.**
2. **Right-click** "Windows PowerShell" → **Run as administrator** → click
   **Yes.** A blue window opens.
3. You need to point it at your project folder. Type `cd ` (the letters c, d,
   then a space), then:
   - Open your project folder in File Explorer, click once in the **address bar**
     at the top (it turns into text), copy that text.
   - Back in the blue window, **right-click** to paste it, then press **Enter.**
   - (Example of what you typed: `cd C:\Users\You\Desktop\iPhone-on-Windows`)
4. Now type this and press **Enter**:
   ```
   .\scripts\start-wda.ps1
   ```
5. If it complains about scripts being disabled, type this line, press Enter,
   then repeat step 4:
   ```
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
6. A few small windows pop open and stay open. **Leave them open** — they're the
   live connection. (Closing them disconnects the phone.)

---

## STEP 12 — Check the connection works

1. Open your web browser to: **http://127.0.0.1:8100/status**
2. You should see a page of text that includes **`"state" : "success"`.**
3. If instead you get an error, the app on the phone probably isn't running —
   redo Step 8 and Step 11. (More help in Troubleshooting below.)

---

## STEP 13 — Start the app (a second, normal window)

1. Open your project folder in **File Explorer.**
2. Click once in the **address bar** at the top, type **`powershell`** over the
   text that's there, and press **Enter.** A window opens already pointed at your
   project folder.
3. Type these three lines, pressing **Enter** after each. Wait for each to finish:
   ```
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   (The first two are instant; the third downloads a few things — give it a
   minute.)
4. If line 2 complains about scripts, type
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, press Enter, and
   redo the three lines.
5. Now start the app:
   ```
   python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
   ```
6. It prints **`Uvicorn running on http://127.0.0.1:8000`** and keeps running.
   Leave this window open too.

---

## STEP 14 — Open it and use your phone

1. Open your web browser to **http://127.0.0.1:8000**
2. Top-right should say **`WDA ✓ connected`** and your phone screen appears.
3. **Click** the screen to tap, **click and drag** to swipe. The panel on the
   right has Home, lock, volume, keyboard, clipboard, and a "get text" button.

🎉 Done.

---

## Doing it again next time (much shorter)

The phone app, Python, and files are already set up. Next time you only:
1. Plug in the iPhone (tap **Trust** if asked).
2. Admin PowerShell in the project folder → `.\scripts\start-wda.ps1` → check
   **http://127.0.0.1:8100/status**.
3. Normal PowerShell in the project folder →
   `.\.venv\Scripts\Activate.ps1` then
   `python -m uvicorn server.main:app --host 127.0.0.1 --port 8000`.
4. Open **http://127.0.0.1:8000**.

(If more than a week has passed, also redo Step 8 to re-add the phone app.)

---

## Troubleshooting

| What you see | What to do |
|---|---|
| Step 11 `ios list` shows no device | Unplug/replug the cable; tap **Trust** on the phone; make sure you did Step 5. |
| `http://127.0.0.1:8100/status` won't load | The phone app isn't running or its 7 days expired — redo Steps 8 and 11. |
| A window says "runwda" failed | The Administrator tunnel window from Step 11 must stay open. |
| "running scripts is disabled" | Type `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, Enter, then retry. |
| App page says `WDA ✗ not reachable` | Redo Step 11 and keep those small windows open. |
| "Get from phone" clipboard is empty | The phone app must be the app showing on your phone's screen at that moment. |
