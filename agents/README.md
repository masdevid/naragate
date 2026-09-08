# Naragate Agents Template

A multi-agent template for the **Naragate Reality Gap** evidence engine. It defines the agent topology that turns an Indonesian market narrative into a Reality Gap score (0-100) and verdict, and it can be installed into any harness that supports multiple agents.

This template **complements** the Naragate skills package. Each agent loads its corresponding skill from `skills/`; the skills remain the single source of truth for the actual instructions. This template only wires the agents together.

## Topology

```mermaid
flowchart TD
    N([narrative — Indonesian text]) --> O[pipeline-orchestrator<br/>coordinator]
    O -->|1. parse| CP[claim-parser]
    CP -->|Claim JSON| VA[valuation-agent]
    CP -->|Claim JSON| FA[fundamental-agent]
    CP -->|Claim JSON| MA[market-agent]
    CP -->|Claim JSON, always| NA[news-agent]
    VA -->|2. evidence| SK[skeptic-agent]
    FA -->|2. evidence| SK
    MA -->|2. evidence| SK
    NA -->|2. evidence| SK
    SK -->|3. SkepticAnalysis JSON| JJ[evidence-judge]
    JJ -->|4. Assessment JSON| SG[score-generator]
    SG -->|5. score| RG([Reality Gap score + verdict])
    RG -.->|completed analysis| CH[chat<br/>follow-up Q&A]
```

Support agents:

| Agent | Role |
|-------|------|
| `chat` | Answers follow-up questions about a completed analysis using only the evidence |

## Agents

| Agent | Skill | Input | Output |
|-------|-------|-------|--------|
| `pipeline-orchestrator` | `pipeline-orchestrator` | narrative (text) | score + verdict |
| `claim-parser` | `claim-parser` | narrative (text) | Claim JSON |
| `valuation-agent` | `valuation-agent` | Claim JSON (valuation) | ValuationEvidence JSON |
| `fundamental-agent` | `fundamental-agent` | Claim JSON (fundamental) | FundamentalEvidence JSON |
| `market-agent` | `market-agent` | Claim JSON (market) | MarketEvidence JSON |
| `news-agent` | `news-agent` | Claim JSON | NewsEvidence JSON |
| `skeptic-agent` | `skeptic-agent` | Claim + evidence | SkepticAnalysis JSON |
| `evidence-judge` | `evidence-judge` | Claim + evidence + skeptic | Assessment JSON |
| `score-generator` | `score-generator` | Assessment + skeptic score | RealityGapScore JSON |
| `chat` | `chat` | question + completed analysis | answer (text) |

## Layout

```
agents/
  agents.json              # pipeline stages, agent file list, package metadata
  *.md                     # neutral agent definitions (source of truth)
  install.py               # generator: emits harness-native agent files
  README.md
```

## Prerequisites

Install the Naragate skills first so each agent can load its skill:

```bash
npx skills add masdevid/naragate
```

## Install

The neutral definitions in `agents/` are the source of truth. `install.py` generates harness-native files.

```bash
# list supported harnesses
python agents/install.py --list

# generate for one harness into the current project
python agents/install.py --harness opencode

# generate for every harness into a specific directory (dry-run first)
python agents/install.py --all --out /path/to/project --dry-run
python agents/install.py --all --out /path/to/project
```

### Supported harnesses

| Harness | Generated files | Notes |
|---------|-----------------|-------|
| `claude-code` | `.claude/agents/<name>.md` | Claude Code subagents |
| `opencode` | `.opencode/agents/<name>.md` | OpenCode agents (file name = agent name) |
| `codex` | `.codex/agents/<name>.toml` | Codex custom agents |
| `pi` | `pi.json` | Pi harness manifest (`{name, skill}` per agent) |
| `deepagents` | `.deepagents/agent/<name>.md` | Deep Agents |

The generator does not hardcode a model or provider — each harness uses its default model. Set a per-agent model in the generated files if you want one.

## Extending

1. Add a neutral definition `agents/<name>.md` (frontmatter: `name`, `description`, `skill`, `mode`, `handoffs`, `input`, `output`; body = system prompt)
2. Add the filename to `agent_files` in `agents/agents.json` (and to `pipeline`/`support` as appropriate)
3. Re-run `python agents/install.py --all`

## Design notes

- **No duplication**: the neutral `.md` files are the single source of truth; generated harness files are derived artifacts, not edited by hand.
- **Skills stay canonical**: agents load skills by name; the template never embeds skill content.
- **No hardcoded credentials or budgets**: the harness injects the Sectors API key and credit budget at runtime.