"""In-process (embedded) engine integration.

Skipped unless the optional engine package is installed (`pip install
"naragate-mcp[local]"`), so the default MCP test run stays lightweight. When it
runs, it proves `naragate-mcp --local` serves the real engine with no external
backend — and with 0 Sectors calls (only local/deterministic tools are used).
"""

import pytest

pytest.importorskip("app.main", reason="engine package not installed (mcp[local])")

from naragate_mcp import server  # noqa: E402
from naragate_mcp.local_engine import LocalEngine  # noqa: E402


def test_embedded_engine_serves_tools_in_process():
    engine = LocalEngine().start(timeout=30)
    previous = server._BASE_URL
    server._BASE_URL = engine.base_url
    try:
        # list_templates + setup status are local/deterministic: no Sectors calls.
        templates = server.list_templates().get("templates")
        assert templates and any(t.get("id") == "valuation" for t in templates)
        assert "missing" in server.get_setup_status()
    finally:
        server._BASE_URL = previous
        engine.stop()
