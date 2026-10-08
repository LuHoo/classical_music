#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def top_rule_counts(findings: list[dict[str, Any]], limit: int) -> list[tuple[str, int]]:
    counts = Counter(str(finding.get("rule_id", "unknown")) for finding in findings)
    return counts.most_common(limit)


def render_summary(report: dict[str, Any], limit: int) -> str:
    findings = list(report.get("findings", []))
    errors = int(report.get("error_count", 0))
    warnings = int(report.get("warning_count", 0))
    info = int(report.get("info_count", 0))
    action_required = int(report.get("action_required_count", 0))
    background = int(report.get("background_suspicion_count", 0))
    auto_resolved = int(report.get("auto_resolved_count", 0))

    lines = [
        "## Canonical Data Validation",
        "",
        f"- Errors: {errors}",
        f"- Warnings: {warnings}",
        f"- Info: {info}",
        f"- Action required: {action_required}",
        f"- Background suspicions: {background}",
        f"- Automatically resolved/classified: {auto_resolved}",
        "",
    ]

    if errors:
        lines.extend([
            "### Attention Needed",
            "",
            "Validation errors block regular work and should be fixed before merging.",
            "",
        ])
    elif action_required:
        lines.extend([
            "### Attention Needed",
            "",
            "No blocking errors. Only explicitly activated identity decisions require curator action.",
            "",
        ])
    elif warnings:
        lines.extend([
            "### Attention Needed",
            "",
            "No blocking errors or active identity decisions. Remaining findings are background suspicions.",
            "",
        ])
    else:
        lines.extend([
            "### Attention Needed",
            "",
            "No validation findings.",
            "",
        ])

    if findings:
        lines.extend([
            "### Top Rule Groups",
            "",
            "| Rule | Count |",
            "| --- | ---: |",
        ])
        for rule_id, count in top_rule_counts(findings, limit):
            lines.append(f"| `{rule_id}` | {count} |")
        lines.append("")

        lines.extend([
            "### First Findings",
            "",
            "| Severity | Rule | File | Message |",
            "| --- | --- | --- | --- |",
        ])
        for finding in findings[:limit]:
            severity = str(finding.get("severity", ""))
            rule_id = str(finding.get("rule_id", ""))
            file_path = str(finding.get("file", ""))
            message = str(finding.get("message", "")).replace("|", "\\|")
            lines.append(f"| {severity} | `{rule_id}` | `{file_path}` | {message} |")
        lines.append("")

    lines.append("Full machine-readable details are available in the `validation-report` artifact.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a GitHub summary for validation-report.json")
    parser.add_argument("report", type=Path)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    print(render_summary(load_report(args.report), args.limit), end="")


if __name__ == "__main__":
    main()
