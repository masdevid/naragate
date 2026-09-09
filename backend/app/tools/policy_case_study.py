"""T6 case-study runner: prints and writes the penny-test report.

Usage (from backend/):
    python -m app.tools.policy_case_study

Writes the report to docs/t6-case-study-report.md and prints it. Exit code is
0 when the penny-test PASSES (funds T7), 1 when it FAILS.
"""

import asyncio
import os
from pathlib import Path

from app.services.case_study import format_report_markdown, run_case_studies


def _report_path() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "docs" / "t6-case-study-report.md"


async def main() -> int:
    summary = run_case_studies()
    markdown = format_report_markdown(summary)
    print(markdown)
    report = _report_path()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(markdown, encoding="utf-8")
    print(f"\nReport written to {report}")
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))