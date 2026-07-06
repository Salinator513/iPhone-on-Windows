"""Minimal async client for a WebDriverAgent (WDA) server.

WDA runs *on the iPhone* and exposes device control over HTTP (default port
8100, forwarded to this PC by go-ios). This wraps the endpoints the app needs:
screenshot, tap, swipe, type, buttons, on-screen text, and clipboard.

Sessions on the phone can die (WDA restart, timeout); session-scoped calls
transparently recreate the session and retry once. Endpoint shapes follow
common Appium/WDA conventions and can vary slightly between WDA builds.
"""
from __future__ import annotations

import base64
from xml.etree import ElementTree

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

    def _drop_session(self) -> None:
        self._session_id = None
        self._window = None

    async def _session_post(self, subpath: str, payload: dict | None = None, *, _retry: bool = True):
        sid = await self.ensure_session()
        r = await self._client.post(f"/session/{sid}/{subpath}", json=payload or {})
        if r.status_code == 404 and _retry:
            # session likely expired; recreate and try once more
            self._drop_session()
            return await self._session_post(subpath, payload, _retry=False)
        r.raise_for_status()
        return r.json().get("value")

    async def _session_get(self, subpath: str, *, _retry: bool = True):
        sid = await self.ensure_session()
        r = await self._client.get(f"/session/{sid}/{subpath}")
        if r.status_code == 404 and _retry:
            self._drop_session()
            return await self._session_get(subpath, _retry=False)
        r.raise_for_status()
        return r.json().get("value")

    async def _window_size(self) -> dict[str, float]:
        if self._window:
            return self._window
        self._window = await self._session_get("window/size")
        return self._window

    async def _to_device(self, nx: float, ny: float) -> tuple[float, float]:
        """Map normalized (0..1) coords onto WDA's point space."""
        size = await self._window_size()
        return nx * size["width"], ny * size["height"]

    def _pointer(self, actions: list[dict]) -> dict:
        return {
            "actions": [
                {
                    "type": "pointer",
                    "id": "finger1",
                    "parameters": {"pointerType": "touch"},
                    "actions": actions,
                }
            ]
        }

    # -- visual ----------------------------------------------------------
    async def screenshot_png(self) -> bytes:
        # /screenshot works without a session
        r = await self._client.get("/screenshot")
        r.raise_for_status()
        return base64.b64decode(r.json().get("value"))

    # -- control ---------------------------------------------------------
    async def tap(self, nx: float, ny: float) -> None:
        x, y = await self._to_device(nx, ny)
        await self._session_post("actions", self._pointer([
            {"type": "pointerMove", "duration": 0, "x": x, "y": y},
            {"type": "pointerDown", "button": 0},
            {"type": "pause", "duration": 60},
            {"type": "pointerUp", "button": 0},
        ]))

    async def swipe(
        self, nx1: float, ny1: float, nx2: float, ny2: float, duration_ms: int = 300
    ) -> None:
        x1, y1 = await self._to_device(nx1, ny1)
        x2, y2 = await self._to_device(nx2, ny2)
        await self._session_post("actions", self._pointer([
            {"type": "pointerMove", "duration": 0, "x": x1, "y": y1},
            {"type": "pointerDown", "button": 0},
            {"type": "pointerMove", "duration": duration_ms, "x": x2, "y": y2},
            {"type": "pointerUp", "button": 0},
        ]))

    async def app_switcher(self) -> None:
        """Approximate the app switcher on Face ID phones: swipe up from the
        bottom edge and hold. (Gesture-based; exact behavior varies by model.)"""
        w = await self._window_size()
        cx = w["width"] * 0.5
        await self._session_post("actions", self._pointer([
            {"type": "pointerMove", "duration": 0, "x": cx, "y": w["height"] * 0.999},
            {"type": "pointerDown", "button": 0},
            {"type": "pointerMove", "duration": 350, "x": cx, "y": w["height"] * 0.6},
            {"type": "pause", "duration": 700},
            {"type": "pointerUp", "button": 0},
        ]))

    async def keys(self, keys: list[str]) -> None:
        """Send keystrokes to the focused field. Accepts plain chars plus
        "\\n" (return) and "\\b" (delete)."""
        await self._session_post("wda/keys", {"value": keys})

    async def type_text(self, text: str) -> None:
        await self.keys(list(text))

    async def press_home(self) -> None:
        await self._session_post("wda/homescreen")

    async def press_button(self, name: str) -> None:
        """Hardware button by name: home, volumeUp, volumeDown, etc."""
        await self._session_post("wda/pressButton", {"name": name})

    async def lock(self) -> None:
        await self._session_post("wda/lock")

    async def unlock(self) -> None:
        await self._session_post("wda/unlock")

    # -- text / clipboard ------------------------------------------------
    async def source_xml(self) -> str:
        """Raw accessibility tree (XML)."""
        r = await self._client.get("/source")
        r.raise_for_status()
        return r.json().get("value", "")

    async def text_lines(self) -> list[str]:
        """Visible, selectable text pulled from the accessibility tree."""
        xml = await self.source_xml()
        lines: list[str] = []
        seen: set[str] = set()
        try:
            root = ElementTree.fromstring(xml)
        except ElementTree.ParseError:
            return lines
        for el in root.iter():
            for attr in ("value", "label", "name"):
                text = (el.attrib.get(attr) or "").strip()
                if text and text not in seen and not text.isnumeric():
                    seen.add(text)
                    lines.append(text)
        return lines

    async def get_clipboard(self) -> str:
        """Read the phone's clipboard. Requires WDA to be in the foreground."""
        b64 = await self._session_post("wda/getPasteboard", {"contentType": "plaintext"})
        if not b64:
            return ""
        try:
            return base64.b64decode(b64).decode("utf-8", "replace")
        except (ValueError, TypeError):
            return b64

    async def set_clipboard(self, text: str) -> None:
        b64 = base64.b64encode(text.encode()).decode()
        await self._session_post(
            "wda/setPasteboard", {"content": b64, "contentType": "plaintext"}
        )
