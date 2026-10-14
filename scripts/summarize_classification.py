#!/usr/bin/env python3
"""Render the CI validation-route decision for a GitHub job summary (issue #308).

This describes the selected route only, not what actually executed: it runs
before the pytest step, so it must never claim pytest ran or finished. See
``summarize_execution.py`` for the post-execution report, which is the only
place that may describe what the test suite actually did.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(classification: dict) -> str:
    route = classification.get("route", "unknown")
    reason = classification.get("reason", "")
    changed = classification.get("changed_files", [])
    diff_complete = classification.get("diff_complete", False)
    evidence = classification.get("evidence", {})

    lines = [
        "## Validation policy",
        "",
        f"- Classification: {'curator/data-only' if route == 'data-only' else 'code/schema/dependencies/workflow/unknown'}",
        f"- Selected route: **{route}**",
        f"- Reason: {reason}",
        f"- Diff complete: {diff_complete}",
        f"- Changed files: {len(changed)}",
    ]

    if evidence.get("expected_head_sha"):
        lines += [
            f"- Expected head/base revision: `{evidence.get('expected_head_sha')}` / `{evidence.get('expected_base_sha')}`",
        ]
    if evidence.get("changed_files_reported") is not None:
        lines += [
            f"- Changed files reported by PR metadata: {evidence.get('changed_files_reported')}",
            f"- Changed files actually fetched: {evidence.get('changed_files_fetched')}",
        ]

    if changed:
        lines += ["", "| Status | Path | Previous path |", "|---|---|---|"]
        for entry in changed[:200]:
            previous = entry.get("previous_path") or ""
            lines.append(f"| {entry.get('status', '')} | `{entry.get('path', '')}` | `{previous}` |")
        if len(changed) > 200:
            lines.append(f"\n... and {len(changed) - 200} more changed file(s).")

    lines += ["", "### Controls this route will select"]
    if route == "data-only":
        lines += [
            "",
            "- Canonical catalog validation (`DataValidator`): will run once, against the complete current dataset.",
            "- The curator/data regression test subset (chamber, piano, best-classical, curator decisions, "
            "publication validation, cross-intake checks): selected for the pytest step below.",
            "- The broader software test suite: **not selected** for this route.",
            "",
            "This section describes what is *planned*. Whether each control actually completed is reported "
            "separately, after the relevant steps have run, in the execution summary below.",
        ]
    else:
        lines += [
            "",
            "- Canonical catalog validation (`DataValidator`): will run once, against the complete current dataset.",
            "- The full relevant software test suite is selected for the pytest step below, which includes "
            "publication validation and cross-intake checks.",
            "",
            "This section describes what is *planned*. Whether each control actually completed is reported "
            "separately, after the relevant steps have run, in the execution summary below.",
        ]

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    if not args.path.exists():
        print("## Validation policy\n\nClassification report missing; treat as unverified.\n", end="")
        return 0

    classification = json.loads(args.path.read_text())
    print(render(classification), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

