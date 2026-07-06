"""Load runtime config from config.json (falling back to config.example.json)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    wda_url: str = "http://127.0.0.1:8100"
    host: str = "127.0.0.1"
    port: int = 8000
    screenshot_fps: int = 5
    # "screenshot" (always works) or "qvh" (smooth high-FPS, needs qvh_cmd)
    video: str = "screenshot"
    # command that writes concatenated JPEG frames (MJPEG) to stdout.
    # empty = disabled. See docs/SETUP.md for a qvh + ffmpeg example.
    qvh_cmd: list[str] = field(default_factory=list)

    @classmethod
    def load(cls) -> "Config":
        known = {f.name for f in fields(cls)}
        for name in ("config.json", "config.example.json"):
            path = ROOT / name
            if path.exists():
                data = json.loads(path.read_text())
                return cls(**{k: v for k, v in data.items() if k in known})
        return cls()
