"""High-FPS video path.

A helper that runs an external command emitting concatenated JPEG frames
(MJPEG) on stdout and yields them frame-by-frame. The backend re-serves those
frames as an ``multipart/x-mixed-replace`` stream that a plain ``<img>`` can
display.

The command is configurable (``qvh_cmd`` in config) so the codec plumbing is
decoupled from this app: point it at a ``qvh | ffmpeg`` pipeline that outputs
MJPEG (see docs/SETUP.md). This module itself is transport-only and has no
qvh/ffmpeg dependency.
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

JPEG_SOI = b"\xff\xd8"  # start of image
JPEG_EOI = b"\xff\xd9"  # end of image


class FrameSource:
    def __init__(self, cmd: list[str], read_size: int = 65536) -> None:
        self._cmd = cmd
        self._read_size = read_size
        self._proc: asyncio.subprocess.Process | None = None

    @property
    def enabled(self) -> bool:
        return bool(self._cmd)

    async def frames(self) -> AsyncIterator[bytes]:
        """Yield complete JPEG frames parsed from the command's stdout."""
        if not self._cmd:
            return
        proc = await asyncio.create_subprocess_exec(
            *self._cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._proc = proc
        buf = bytearray()
        try:
            assert proc.stdout is not None
            while True:
                chunk = await proc.stdout.read(self._read_size)
                if not chunk:
                    break
                buf.extend(chunk)
                # emit every complete SOI..EOI frame currently buffered
                while True:
                    start = buf.find(JPEG_SOI)
                    if start == -1:
                        # no frame start buffered yet; drop junk but keep a
                        # trailing 0xFF that might be a split SOI marker
                        if buf and buf[-1] == 0xFF:
                            del buf[:-1]
                        else:
                            buf.clear()
                        break
                    end = buf.find(JPEG_EOI, start + 2)
                    if end == -1:
                        # drop anything before a dangling SOI to bound memory
                        if start > 0:
                            del buf[:start]
                        break
                    end += 2
                    yield bytes(buf[start:end])
                    del buf[:end]
        finally:
            await self.stop()

    async def stop(self) -> None:
        proc, self._proc = self._proc, None
        if proc and proc.returncode is None:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=3)
            except (ProcessLookupError, asyncio.TimeoutError):
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
