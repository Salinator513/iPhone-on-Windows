"""FastAPI backend: serves the web UI and proxies device control to WDA.

Run with:  python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import Config
from .video import FrameSource
from .wda import WDAClient, WDAError

ROOT = Path(__file__).resolve().parent.parent
cfg = Config.load()
wda = WDAClient(cfg.wda_url)

_ALLOWED_BUTTONS = {"home", "volumeUp", "volumeDown", "power", "snapshot"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await wda.close()


app = FastAPI(title="iPhone on Windows", lifespan=lifespan)


# ---- request models ----
class TapReq(BaseModel):
    x: float
    y: float


class SwipeReq(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    duration_ms: int = 300


class TextReq(BaseModel):
    text: str


class KeysReq(BaseModel):
    keys: list[str]


# ---- turn WDA/transport failures into clean 502s ----
@app.exception_handler(httpx.HTTPError)
async def _httpx_error(request: Request, exc: httpx.HTTPError) -> JSONResponse:
    return JSONResponse({"error": f"WDA request failed: {exc}"}, status_code=502)


@app.exception_handler(WDAError)
async def _wda_error(request: Request, exc: WDAError) -> JSONResponse:
    return JSONResponse({"error": str(exc)}, status_code=502)


# ---- status ----
@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/status")
async def status() -> dict:
    return {
        "go_ios": shutil.which("ios") is not None,
        "qvh": shutil.which("qvh") is not None,
        "wda_reachable": await wda.is_up(),
        "wda_url": cfg.wda_url,
        "screenshot_fps": cfg.screenshot_fps,
        "video": cfg.video,
        "qvh_stream": cfg.video == "qvh" and bool(cfg.qvh_cmd),
    }


# ---- video ----
@app.get("/api/screenshot")
async def screenshot() -> Response:
    png = await wda.screenshot_png()
    return Response(content=png, media_type="image/png")


@app.get("/api/stream.mjpeg")
async def stream_mjpeg() -> StreamingResponse:
    source = FrameSource(cfg.qvh_cmd)
    if not source.enabled:
        raise HTTPException(status_code=503, detail="qvh_cmd not configured")

    async def gen():
        async for jpg in source.frames():
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                + str(len(jpg)).encode()
                + b"\r\n\r\n"
                + jpg
                + b"\r\n"
            )

    return StreamingResponse(
        gen(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


# ---- control ----
@app.post("/api/tap")
async def tap(req: TapReq) -> dict:
    await wda.tap(req.x, req.y)
    return {"ok": True}


@app.post("/api/swipe")
async def swipe(req: SwipeReq) -> dict:
    await wda.swipe(req.x1, req.y1, req.x2, req.y2, req.duration_ms)
    return {"ok": True}


@app.post("/api/type")
async def type_text(req: TextReq) -> dict:
    await wda.type_text(req.text)
    return {"ok": True}


@app.post("/api/keys")
async def keys(req: KeysReq) -> dict:
    await wda.keys(req.keys)
    return {"ok": True}


@app.post("/api/home")
async def home() -> dict:
    await wda.press_home()
    return {"ok": True}


@app.post("/api/recents")
async def recents() -> dict:
    await wda.app_switcher()
    return {"ok": True}


@app.post("/api/lock")
async def lock() -> dict:
    await wda.lock()
    return {"ok": True}


@app.post("/api/button/{name}")
async def button(name: str) -> dict:
    if name not in _ALLOWED_BUTTONS:
        raise HTTPException(status_code=400, detail=f"unknown button: {name}")
    await wda.press_button(name)
    return {"ok": True}


# ---- text / clipboard ----
@app.get("/api/text")
async def get_text() -> dict:
    return {"lines": await wda.text_lines()}


@app.get("/api/clipboard")
async def get_clipboard() -> dict:
    return {"text": await wda.get_clipboard()}


@app.post("/api/clipboard")
async def set_clipboard(req: TextReq) -> dict:
    await wda.set_clipboard(req.text)
    return {"ok": True}


# ---- static web UI (mounted last so /api/* routes win) ----
app.mount("/", StaticFiles(directory=str(ROOT / "web"), html=True), name="web")
