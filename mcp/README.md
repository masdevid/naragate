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
uvx naragate-mcp           # run without installing (recommended)
pip install naragate-mcp   # or install into your environment
pipx install naragate-mcp
```

From a checkout: `pip install -e mcp`.

Point it at your backend (default `http://127.0.0.1:5678`):

```bash
export NARAGATE_BACKEND_URL="http://127.0.0.1:5678"
export NARAGATE_TOKEN="nrg_..."   # optional: act as your own account
naragate-mcp
```

Transport is **stdio**.

### Acting as your own account (`NARAGATE_TOKEN`)

The backend owns the Sectors key and LLM configuration; this server never sees them. To use **your own** key, cache and credits, mint a token in the web UI (**Settings → MCP & API Access**) and set `NARAGATE_TOKEN`. Every request then carries `Authorization: Bearer <token>`, which the backend resolves to your email — the same identity the web session uses.

- Without a token the server falls back to the backend's **deployment key** (fine for single-user self-hosts; all callers share one key/ledger).
- `whoami` confirms the resolved account; `get_setup_status` reports missing config; `bind_sectors_key` sets your key off-web.
- Tokens are stored hashed server-side and revocable from the same settings page.

### No backend? Run it embedded

`naragate-mcp --local` runs the engine **in this process** — no separate
process, no `NARAGATE_BACKEND_URL`:

```bash
pip install "naragate-mcp[local]"     # Python 3.12+; pulls naragate-engine
SECTORS_API_KEY=... naragate-mcp --local
# or: NARAGATE_ENGINE=embedded naragate-mcp
```

It serves the exact same engine as the hosted deployment (one cache, one credit
ledger), just in-process. Configure the Sectors key / LLM through the
environment (`SECTORS_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`); per-user
tokens and `bind_sectors_key` don't apply to a single local user.

Prefer a separate engine process (shared cache, multiple clients)? Run one and
point `NARAGATE_BACKEND_URL` at it:

```bash
pip install naragate-engine && SECTORS_API_KEY=... naragate-engine
# or
docker run --rm -p 5678:5678 -e SECTORS_API_KEY=... ghcr.io/masdevid/naragate-engine
```

If no engine answers, tools fail with an actionable hint on how to start one.

## Tools

**30 tools total — 15 high-level + 15 low-level** (every primitive declared in `skills/*/tools.yaml`).

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
| `whoami()` | Which account this session acts as (email + whether a Sectors key is bound) |
| `get_setup_status()` | Missing backend config (`sectors_api_key`, `llm_model`) |
| `bind_sectors_key(api_key)` | Bind a Sectors v2 key to this session's user (requires `NARAGATE_TOKEN`) |
| `ask_followup(claim_id, question)` | Ask a follow-up about a completed analysis, grounded in its evidence |
| `get_followup_suggestions(claim_id)` | 3-5 contextual follow-up templates (the web suggestion chips) |
| `next_followup_suggestion(claim_id, exclude)` | One fresh template, avoiding `exclude` |

### Low-level tools — full `tools.yaml` parity

Every primitive declared in `skills/*/tools.yaml` is also exposed, for harnesses that want to compose
per-agent exactly like the Pi pipeline (check the cache, then fetch on a miss and merge back):

| Tool | What it does |
|---|---|
| `sectors_company_report(ticker, sections)` | Sectors v2 company report (valuation/overview/financials) |
| `sectors_subsector_report(sub_sector, sections)` | Sectors v2 subsector report |
| `sectors_quarterly_financials(ticker, n_quarters)` | Sectors v2 quarterly financials |
| `sectors_daily_transaction(ticker, start, end)` | Sectors v2 daily price/volume (Sectors caps a call at 90 days) |
| `sectors_news(ticker, limit)` | Sectors v2 news headlines |
| `sectors_corporate_actions(ticker)` | Sectors v2 corporate actions |
| `sectors_filings(ticker, filing_type)` | Sectors v2 insider-trade filings |
| `sectors_foreign_flow(ticker, start, end)` | Sectors v2 foreign investor flow (net inflow/outflow) |
| `sectors_broker_summary(ticker, start, end)` | Sectors v2 broker accumulation/distribution summary |
| `sectors_top_changes(classifications, periods, n_stock)` | Sectors v2 top gainers/losers across the IDX universe |
| `sectors_segments(ticker, financial_year)` | Sectors v2 revenue-segment breakdown |
| `sectors_index_daily(index_code, start, end)` | Sectors v2 daily closing prices for an IDX index (e.g. `ihsg`) |
| `evidence_cache_get(ticker)` | Read the Evidence Graph (null on miss) |
| `evidence_cache_merge(ticker, key, value, ttl?)` | Merge one section into the cache |
| `llm_complete(prompt, system?, response_format?, role?)` | One-shot completion on Naragate's configured LLM |

A test (`tests/test_parity.py`) asserts that **every** tool declared in any `skills/*/tools.yaml`
exists on the server, so this can't drift.

## Resources

- `naragate://templates`
- `naragate://usage`
- `naragate://history`
- `naragate://claim/{claim_id}`

## Harness configuration

### Claude Code

```bash
claude mcp add naragate \
  -e NARAGATE_BACKEND_URL=http://127.0.0.1:5678 \
  -e NARAGATE_TOKEN=nrg_... \
  -- uvx naragate-mcp
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "naragate": {
      "command": "uvx",
      "args": ["naragate-mcp"],
      "env": { "NARAGATE_BACKEND_URL": "http://127.0.0.1:5678", "NARAGATE_TOKEN": "nrg_..." }
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
      "environment": { "NARAGATE_BACKEND_URL": "http://127.0.0.1:5678", "NARAGATE_TOKEN": "nrg_..." }
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
      "env": { "NARAGATE_BACKEND_URL": "http://127.0.0.1:5678", "NARAGATE_TOKEN": "nrg_..." }
    }
  }
}
```

### Codex (`~/.codex/config.toml`)

```toml
[mcp_servers.naragate]
command = "uvx"
args = ["naragate-mcp"]
env = { NARAGATE_BACKEND_URL = "http://127.0.0.1:5678", NARAGATE_TOKEN = "nrg_..." }
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

## Publishing

CI publishes via [`.github/workflows/publish-mcp.yml`](https://github.com/masdevid/naragate/blob/master/.github/workflows/publish-mcp.yml)
when a GitHub release is published (or `gh workflow run publish-mcp.yml`). It authenticates with
**PyPI Trusted Publishing (OIDC)** — no API token secret. One-time setup on PyPI
(project → *Publishing* → *Add a new publisher*):

| Field | Value |
|---|---|
| Owner | `masdevid` |
| Repository | `naragate` |
| Workflow name | `publish-mcp.yml` |
| Environment name | `pypi` |

→ https://pypi.org/manage/project/naragate-mcp/settings/publishing/

For local/manual publishing, `publish.sh` uses an API token instead:

```bash
mcp/publish.sh              # PyPI
mcp/publish.sh testpypi     # TestPyPI
mcp/publish.sh check        # dry run: build + twine check (no token, no upload)
```

`publish.sh` reads `PYPI_TOKEN` from the environment or the repo-root `.env`, builds with
`python -m build`, validates with `twine check`, and uploads — the token is never echoed. Manual
equivalent:

```bash
python -m build
python -m twine check dist/*
TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" python -m twine upload dist/*
```

## Related

- [Naragate README](https://github.com/masdevid/naragate#readme) — project overview and the "Use Naragate from any MCP agent" section
- [Skills](https://github.com/masdevid/naragate/blob/master/skills/README.md) — the 13 skills whose `tools.yaml` this server satisfies
- [Agents](https://github.com/masdevid/naragate/blob/master/agents/README.md) — optional subagent topology for harnesses that support it
- [Parity test](https://github.com/masdevid/naragate/blob/master/mcp/tests/test_parity.py) — enforces that every `skills/*/tools.yaml` tool is exposed here
