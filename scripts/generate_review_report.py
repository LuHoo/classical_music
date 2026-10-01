#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import typer
from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(input_file: str = typer.Option("generated/migration/migration-summary.json", "--input")) -> None:
    summary_path = ROOT / input_file
    if not summary_path.exists():
        raise typer.BadParameter(f"Missing input file: {summary_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    review_items = summary.get("review_items", [])

    items_by_composer: dict[str, list[dict]] = defaultdict(list)
    for item in review_items:
        source_file = str(item.get("source_file", ""))
        composer = Path(source_file).stem if source_file else "unknown"
        items_by_composer[composer].append(item)

    review_root = ROOT / "reports" / "review"
    issue_root = review_root / "issues"
    review_root.mkdir(parents=True, exist_ok=True)
    issue_root.mkdir(parents=True, exist_ok=True)

    for composer, items in sorted(items_by_composer.items()):
        lines = [f"# Review Report: {composer}", "", "| Candidate | Review Type | Source | Possible Work | Notes |", "| --- | --- | --- | --- | --- |"]

        for item in items:
            classifications = item.get("classifications", [])
            top = classifications[0] if classifications else {"reason": "uncertain_match", "notes": ""}
            source = f"{item.get('source_file')}:{item.get('source_line')}"
            lines.append(
                "| {candidate} | {reason} | {source} | {work} | {notes} |".format(
                    candidate=item.get("source_id", ""),
                    reason=top.get("reason", "uncertain_match"),
                    source=source,
                    work=item.get("work_text", ""),
                    notes=top.get("notes", ""),
                )
            )

        report_path = review_root / f"{composer}.md"
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        issue_lines = [
            f"# Candidate Review Queue: {composer}",
            "",
            "Use this issue body to process candidates manually.",
            "",
        ]
        for item in items:
            issue_lines.extend(
                [
                    "## Candidate",
                    f"- source_file: {item.get('source_file')}",
                    f"- source_line: {item.get('source_line')}",
                    f"- candidate_work: {item.get('work_text')}",
                    f"- review_reason: {item.get('classifications', [{}])[0].get('reason', 'uncertain_match')}",
                    "- status: open",
                    "",
                ]
            )

        issue_path = issue_root / f"{composer}-issue.md"
        issue_path.write_text("\n".join(issue_lines), encoding="utf-8")

    console.print(f"Wrote review reports to {review_root}")


if __name__ == "__main__":
    app()
