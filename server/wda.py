"""Minimal async client for a WebDriverAgent (WDA) server.

WDA runs *on the iPhone* and exposes device control over HTTP (default port
8100, forwarded to this PC by go-ios). This wraps the handful of endpoints the
app needs: screenshot, tap, swipe, type, on-screen text, and clipboard.

Endpoint shapes follow common Appium/WDA conventions. They can vary slightly
between WDA builds -- if a call 404s, check your WDA version.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx


class WDAError(RuntimeError):
    """Raised when WDA returns something we can't use (e.g. no session id)."""


class WDAClient:
    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base, timeout=timeout)
        self._session_id: str | None = None
        self._window: dict[str, float] | None = None

    async def close(self) -> None:
        await self._client.aclose()

    # -- low level -------------------------------------------------------
    async def _get_value(self, path: str) -> Any:
        r = await self._client.get(path)
        r.raise_for_status()
        return r.json().get("value")

    async def _post_value(self, path: str, payload: dict | None = None) -> Any:
        r = await self._client.post(path, json=payload or {})
        r.raise_for_status()
        return r.json().get("value")

    # -- session ---------------------------------------------------------
    async def is_up(self) -> bool:
        """True if WDA answers /status (used by the health panel)."""
        try:
            r = await self._client.get("/status")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def ensure_session(self) -> str:
        """Return a live session id, creating one on first use."""
        if self._session_id:
            return self._session_id
        r = await self._client.post(
            "/session",
            json={"capabilities": {"alwaysMatch": {}, "firstMatch": [{}]}},
        )
        r.raise_for_status()
        data = r.json()
        sid = data.get("sessionId") or (data.get("value") or {}).get("sessionId")
        if not sid:
            raise WDAError(f"WDA did not return a session id: {data}")
        self._session_id = sid
        return sid

    async def _window_size(self) -> dict[str, float]:
        if self._window:
            return self._window
        sid = await self.ensure_session()
        self._window = await self._get_value(f"/session/{sid}/window/size")
        return self._window

    async def _to_device(self, nx: float, ny: float) -> tuple[float, float]:
        """Map normalized (0..1) coords onto WDA's point space."""
        size = await self._window_size()
        return nx * size["width"], ny * size["height"]

    # -- visual ----------------------------------------------------------
    async def screenshot_png(self) -> bytes:
        # /screenshot works without a session
        b64 = await self._get_value("/screenshot")
        return base64.b64decode(b64)

    # -- control ---------------------------------------------------------
    async def tap(self, nx: float, ny: float) -> None:
        sid = await self.ensure_session()
        x, y = await self._to_device(nx, ny)
        await self._post_value(
            f"/session/{sid}/actions",
            {
                "actions": [
                    {
                        "type": "pointer",
                        "id": "finger1",
                        "parameters": {"pointerType": "touch"},
                        "actions": [
                            {"type": "pointerMove", "duration": 0, "x": x, "y": y},
                            {"type": "pointerDown", "button": 0},
                            {"type": "pause", "duration": 60},
                            {"type": "pointerUp", "button": 0},
                        ],
                    }
                ]
            },
        )

    async def swipe(
        self, nx1: float, ny1: float, nx2: float, ny2: float, duration_ms: int = 300
    ) -> None:
        sid = await self.ensure_session()
        x1, y1 = await self._to_device(nx1, ny1)
        x2, y2 = await self._to_device(nx2, ny2)
        await self._post_value(
            f"/session/{sid}/actions",
            {
                "actions": [
                    {
                        "type": "pointer",
                        "id": "finger1",
                        "parameters": {"pointerType": "touch"},
                        "actions": [
                            {"type": "pointerMove", "duration": 0, "x": x1, "y": y1},
                            {"type": "pointerDown", "button": 0},
                            {"type": "pointerMove", "duration": duration_ms, "x": x2, "y": y2},
                            {"type": "pointerUp", "button": 0},
                        ],
                    }
                ]
            },
        )

    async def type_text(self, text: str) -> None:
        """Type into the currently focused field."""
        sid = await self.ensure_session()
        await self._post_value(f"/session/{sid}/wda/keys", {"value": list(text)})

    async def press_home(self) -> None:
        sid = await self.ensure_session()
        await self._post_value(f"/session/{sid}/wda/homescreen")

    async def source(self) -> str:
        """Accessibility tree (on-screen text lives in its attributes)."""
        return await self._get_value("/source")

    async def get_clipboard(self) -> str:
        """Read the phone's clipboard. Requires WDA to be in the foreground."""
        sid = await self.ensure_session()
        b64 = await self._post_value(
            f"/session/{sid}/wda/getPasteboard", {"contentType": "plaintext"}
        )
        if not b64:
            return ""
        try:
            return base64.b64decode(b64).decode("utf-8", "replace")
        except (ValueError, TypeError):
            return b64

    async def set_clipboard(self, text: str) -> None:
        sid = await self.ensure_session()
        b64 = base64.b64encode(text.encode()).decode()
        await self._post_value(
            f"/session/{sid}/wda/setPasteboard",
            {"content": b64, "contentType": "plaintext"},
        )
