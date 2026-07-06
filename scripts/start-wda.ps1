# Launch WebDriverAgent on the connected iPhone and forward it to this PC.
#
# Prereqs (see docs/SETUP.md):
#   - go-ios (`ios`) on PATH
#   - a signed WDA already installed on the phone (Sideloadly + free Apple ID)
#   - run this from an **Administrator** PowerShell (iOS 17+ tunnel needs it)
#
# The tunnel, WDA, and port-forward are long-running, so each opens in its own
# window. Close them to stop.

$ErrorActionPreference = "Stop"

Write-Host "[1/3] Connected devices:" -ForegroundColor Cyan
ios list

Write-Host "[2/3] Starting iOS 17+ tunnel (admin) - leave its window open..." -ForegroundColor Cyan
Start-Process powershell -Verb RunAs -ArgumentList "-NoExit", "-Command", "ios tunnel start"
Start-Sleep -Seconds 4

Write-Host "[3/3] Launching WDA, then forwarding port 8100..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ios runwda"
Start-Sleep -Seconds 6
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ios forward 8100 8100"

Write-Host ""
Write-Host "Done. Verify WDA at: http://127.0.0.1:8100/status" -ForegroundColor Green
Write-Host "Then run: python -m uvicorn server.main:app --host 127.0.0.1 --port 8000" -ForegroundColor Green
