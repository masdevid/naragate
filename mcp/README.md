# Naragate MCP Server

One portable tool layer so the **same Naragate experience** works on the custom web UI *and* on any
MCP-capable agent surface — Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code, opencode,
Codex, or your own harness.

```
                 ┌─ custom web UI (Angular)
Naragate backend ├─ MCP server  ──► any MCP harness (desktop / CLI / IDE)
(FastAPI+cache)  └─ Pi agent harness
```

## The three layers (what a user actually needs)

| Layer | Path | Required? | Role |
|---|---|---|---|
| **MCP server** | `mcp/` (this package) | **Yes** for non-web | The tools: analyze, history, trend, precheck, usage |
| **Skills** | `skills/` | **Yes** | Domain instructions: how to parse, challenge and score a claim |
| **Agents** | `agents/` | No | Optional orchestration for harnesses with subagents |

Skills alone can't fetch data (they declare tools but don't ship them); agents+skills add
orchestration but still have no data. **The MCP bundle is the data layer** — with it, skills run
anywhere.

## Credit safety (hard requirement)

This server **never talks to Sectors directly**. Every tool is a thin client over the Naragate
backend, so evidence gathering, the Evidence Graph cache and credit accounting live in exactly one
place. A warm re-run costs **0 additional Sectors calls**, identical to the web UI. There is a test
asserting the MCP package never references the Sectors API.

## Install

```bash
# from a checkout
pip install -e mcp

# or, once published
uvx naragate-mcp
pipx install naragate-mcp
```

Point it at your backend (default `http://127.0.0.1:5678`):

```bash
export NARAGATE_BACKEND_URL="http://127.0.0.1:5678"
naragate-mcp
```

Transport is **stdio**.

## Tools

| Tool | What it does |
|---|---|
| `analyze_narrative(narrative)` | Verify a narrative end-to-end → Reality Gap score, verdict, evidence sections, policy signal, skeptic summary |
| `analyze_template(template_id)` | Run one of the 12 curated dashboard templates by id |
| `list_templates()` | The 12 curated narratives (same tiles as the web dashboard) |
| `get_claim(claim_id)` | Full stored record (claim, evidence, skeptic, score, policy) |
| `get_reality_gap(claim_id)` | Compact report for a stored claim |
| `list_history(limit)` | Recent analyses, most recent first |
| `get_trend_summary()` | Totals, average score, verdict distribution, per-ticker history |
| `get_policy_precheck(sector)` | Policy→price pre-check, scoped to the claim's sector |
| `get_usage()` | Sectors/LLM credit usage, cache hits, remaining budget |

## Resources

- `naragate://templates`
- `naragate://usage`
- `naragate://history`
- `naragate://claim/{claim_id}`

## Harness configuration

### Claude Code

```bash
claude mcp add naragate -e NARAGATE_BACKEND_URL=http://127.0.0.1:5678 -- uvx naragate-mcp
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "naragate": {
      "command": "uvx",
      "args": ["naragate-mcp"],
      "env": { "NARAGATE_BACKEND_URL": "http://127.0.0.1:5678" }
    }
  }
}
```

### opencode (`opencode.json`)

```json
{
  "mcp": {
    "naragate": {
      "type": "local",
      "command": ["uvx", "naragate-mcp"],
      "enabled": true,
      "environment": { "NARAGATE_BACKEND_URL": "http://127.0.0.1:5678" }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`) / Windsurf / Zed / VS Code

```json
{
  "mcpServers": {
    "naragate": {
      "command": "uvx",
      "args": ["naragate-mcp"],
      "env": { "NARAGATE_BACKEND_URL": "http://127.0.0.1:5678" }
    }
  }
}
```

### Codex (`~/.codex/config.toml`)

```toml
[mcp_servers.naragate]
command = "uvx"
args = ["naragate-mcp"]
env = { NARAGATE_BACKEND_URL = "http://127.0.0.1:5678" }
```

## Example prompts

- *"Use naragate to verify: PE BBCA mahal di 25x."*
- *"List the naragate templates and run the nickel policy one."*
- *"Show my last 10 naragate analyses and the trend summary."*
- *"What's my Sectors credit usage?"*

## Tests

```bash
cd mcp
python -m pytest -q
```

Covers the REST client (mock transport), the tool surface, compact-report shaping, and the
credit-safety guarantee. No live backend or Sectors access required.
