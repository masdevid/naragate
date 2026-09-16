#!/usr/bin/env python3
"""Generate harness-native multi-agent definitions from the neutral agents/ template.

The neutral template is the single source of truth:
  agents/*.md          one file per agent (YAML frontmatter + system prompt body)
  agents/agents.json   pipeline stages, agent file list, package metadata

Usage:
  python install.py --list
  python install.py --harness claude-code [--out DIR] [--dry-run]
  python install.py --harness opencode [--out DIR] [--dry-run]
  python install.py --harness codex [--out DIR] [--dry-run]
  python install.py --harness pi [--out DIR] [--dry-run]
  python install.py --harness deepagents [--out DIR] [--dry-run]
  python install.py --all [--out DIR] [--dry-run]

Run from the repo root, or point --out at the project you want to install into.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

AGENT_FILES = [
    "claim-parser.md",
    "valuation-agent.md",
    "fundamental-agent.md",
    "market-agent.md",
    "filings-agent.md",
    "news-agent.md",
    "skeptic-agent.md",
    "evidence-judge.md",
    "score-generator.md",
    "chat.md",
    "follow-up.md",
    "renderer.md",
    "pipeline-orchestrator.md",
]

SUBAGENT_TOOLS = "Read, Glob, Grep, WebFetch, WebSearch"
PRIMARY_TOOLS = "Read, Glob, Grep, Bash, Edit, Write, WebFetch, WebSearch"


def parse_frontmatter(text):
    """Parse a minimal YAML frontmatter block. Returns (dict, body)."""
    if not text.startswith("---"):
        raise ValueError("missing frontmatter")
    _, fm, body = text.split("---", 2)
    data = {}
    current_list = None
    for line in fm.strip().splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_list is None:
                raise ValueError("list item outside a list: %r" % line)
            data[current_list].append(line.strip()[4:].strip())
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = []
                current_list = key
            else:
                data[key] = value
                current_list = None
    return data, body.strip()


def load_agents():
    agents = []
    for filename in AGENT_FILES:
        path = os.path.join(HERE, filename)
        with open(path, encoding="utf-8") as f:
            meta, body = parse_frontmatter(f.read())
        meta["body"] = body
        agents.append(meta)
    return agents


def load_manifest():
    with open(os.path.join(HERE, "agents.json"), encoding="utf-8") as f:
        return json.load(f)


def yaml_frontmatter(fields):
    lines = ["---"]
    for key, value in fields.items():
        lines.append("%s: %s" % (key, value))
    lines.append("---")
    return "\n".join(lines)


def claude_code(agents, manifest):
    files = []
    for a in agents:
        tools = PRIMARY_TOOLS if a.get("mode") == "primary" else SUBAGENT_TOOLS
        content = yaml_frontmatter({
            "name": a["name"],
            "description": a["description"],
            "tools": tools,
        }) + "\n\n" + a["body"] + "\n"
        files.append((".claude/agents/%s.md" % a["name"], content))
    return files


def opencode(agents, manifest):
    files = []
    for a in agents:
        lines = ["description: %s" % a["description"], "mode: %s" % a.get("mode", "subagent")]
        if a.get("mode") != "primary":
            lines += ["permission:", "  edit: deny", "  bash: deny"]
        content = "---\n" + "\n".join(lines) + "\n---\n\n" + a["body"] + "\n"
        files.append((".opencode/agents/%s.md" % a["name"], content))
    return files


def codex(agents, manifest):
    files = []
    for a in agents:
        lines = [
            'name = "%s"' % a["name"],
            'description = "%s"' % a["description"],
            "",
            'developer_instructions = """',
            a["body"],
            '"""',
        ]
        files.append((".codex/agents/%s.toml" % a["name"], "\n".join(lines) + "\n"))
    return files


def pi(agents, manifest):
    pi_agents = [
        {"name": a["name"], "skill": ".pi/skills/%s/SKILL.md" % a["name"]}
        for a in agents
        if a.get("skill")
    ]
    data = {
        "name": manifest["name"],
        "version": manifest["version"],
        "agents": pi_agents,
    }
    return [("pi.json", json.dumps(data, indent=2) + "\n")]


def deepagents(agents, manifest):
    files = []
    for a in agents:
        tools = PRIMARY_TOOLS if a.get("mode") == "primary" else SUBAGENT_TOOLS
        content = yaml_frontmatter({
            "name": a["name"],
            "description": a["description"],
            "tools": tools,
        }) + "\n\n" + a["body"] + "\n"
        files.append((".deepagents/agent/%s.md" % a["name"], content))
    return files


HARNESSES = {
    "claude-code": claude_code,
    "opencode": opencode,
    "codex": codex,
    "pi": pi,
    "deepagents": deepagents,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list supported harnesses and exit")
    parser.add_argument("--harness", action="append", choices=sorted(HARNESSES), help="harness to generate for (repeatable)")
    parser.add_argument("--all", action="store_true", help="generate for every harness")
    parser.add_argument("--out", default=os.getcwd(), help="output directory (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="print what would be written without writing")
    args = parser.parse_args()

    if args.list:
        print("Supported harnesses:")
        for name in sorted(HARNESSES):
            print("  %s" % name)
        return

    if not args.harness and not args.all:
        parser.error("specify --harness NAME (or --all)")

    harnesses = sorted(HARNESSES) if args.all else args.harness
    agents = load_agents()
    manifest = load_manifest()

    for harness in harnesses:
        files = HARNESSES[harness](agents, manifest)
        for rel, content in files:
            path = os.path.join(args.out, rel)
            if args.dry_run:
                print("would write %s" % path)
                continue
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print("wrote %s" % path)


if __name__ == "__main__":
    sys.exit(main())