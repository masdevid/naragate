"""Embedded engine mode for `naragate-mcp`.

Runs the Naragate engine **in this process** (uvicorn on a loopback port in a
daemon thread), so the MCP needs no external backend at all: one command,
`naragate-mcp --local`, is fully self-contained.

This reuses the exact same engine as the hosted deployment (the `naragate-engine`
package), so the Evidence Graph cache and credit discipline are unchanged — it
is simply served in-process. Requires the optional engine dependency:

    pip install "naragate-mcp[local]"   # or: uvx --from "naragate-mcp[local]" naragate-mcp --local
"""

from __future__ import annotations

import socket
import threading
import time
from typing import Optional


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class LocalEngine:
    """An in-process engine (uvicorn server on a background thread)."""

    def __init__(self, host: str = "127.0.0.1", port: Optional[int] = None):
        self.host = host
        self.port = port or _free_port()
        self._server = None
        self._thread: Optional[threading.Thread] = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self, timeout: float = 30.0) -> "LocalEngine":
        try:
            import uvicorn
            from app.main import app as engine_app
        except ImportError as exc:  # engine package not installed
            raise RuntimeError(
                'Embedded mode needs the engine package (Python 3.12+). Install it with '
                '`pip install "naragate-mcp[local]"` (or `pip install naragate-engine`), '
                "or point NARAGATE_BACKEND_URL at a running engine instead."
            ) from exc

        config = uvicorn.Config(
            engine_app, host=self.host, port=self.port, log_level="warning"
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(
            target=self._server.run, name="naragate-engine", daemon=True
        )
        self._thread.start()
        self._wait_ready(timeout)
        return self

    def _wait_ready(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex((self.host, self.port)) == 0:
                    return
            time.sleep(0.05)
        raise RuntimeError(
            f"embedded engine did not become ready on {self.base_url} within {timeout:.0f}s"
        )

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
