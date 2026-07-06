#!/usr/bin/env bash
# Launch WebDriverAgent + forward port 8100 (macOS/Linux dev convenience).
# Windows users: use start-wda.ps1. See docs/SETUP.md for prereqs.
set -euo pipefail

echo "[1/3] Connected devices:"
ios list

echo "[2/3] Starting iOS 17+ tunnel (needs sudo); backgrounding..."
sudo ios tunnel start &
sleep 4

echo "[3/3] Launching WDA + forwarding port 8100..."
ios runwda &
sleep 6
ios forward 8100 8100 &

echo
echo "Verify WDA at: http://127.0.0.1:8100/status"
echo "Then run: python -m uvicorn server.main:app --host 127.0.0.1 --port 8000"
wait
