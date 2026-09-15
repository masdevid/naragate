"""Full-parity guarantee: every tool declared in skills/*/tools.yaml must be
exposed by the MCP server, so a non-web harness has the exact same primitives as
the web backend's evidence agents.
"""

import re
from pathlib import Path

import pytest

from naragate_mcp import server

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"


def _declared_tools() -> set[str]:
    names: set[str] = set()
    for tools_yaml in SKILLS_DIR.glob("*/tools.yaml"):
        text = tools_yaml.read_text(encoding="utf-8")
        names.update(re.findall(r"^\s*-\s*name:\s*([A-Za-z0-9_]+)\s*$", text, re.M))
    return names


@pytest.mark.skipif(not SKILLS_DIR.is_dir(), reason="skills/ not present (running from an installed sdist)")
async def test_every_declared_skill_tool_is_exposed_by_the_mcp_server():
    declared = _declared_tools()
    assert declared, f"no tools.yaml declarations found under {SKILLS_DIR}"
    tools = {t.name for t in await server.mcp.list_tools()}
    missing = declared - tools
    assert not missing, f"MCP server is missing tools declared in tools.yaml: {sorted(missing)}"


@pytest.mark.skipif(not SKILLS_DIR.is_dir(), reason="skills/ not present (running from an installed sdist)")
def test_known_low_level_tool_names_present():
    expected = {
        "sectors_company_report", "sectors_subsector_report", "sectors_quarterly_financials",
        "sectors_daily_transaction", "sectors_news", "sectors_corporate_actions", "sectors_filings",
        "evidence_cache_get", "evidence_cache_merge", "llm_complete",
    }
    assert expected <= _declared_tools()
