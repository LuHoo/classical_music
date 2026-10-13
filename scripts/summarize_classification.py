#!/usr/bin/env python3
"""Render the CI validation-policy decision for a GitHub job summary (issue #308)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(classification: dict) -> str:
    route = classification.get("route", "unknown")
    reason = classification.get("reason", "")
    changed = classification.get("changed_files", [])
    diff_complete = classification.get("diff_complete", False)

    lines = [
        "## Validation policy",
        "",
        f"- Classification: {'curator/data-only' if route == 'data-only' else 'code/schema/dependencies/workflow/unknown'}",
        f"- Selected route: **{route}**",
        f"- Reason: {reason}",
        f"- Diff complete: {diff_complete}",
        f"- Changed files: {len(changed)}",
    ]

    if changed:
        lines += ["", "| Status | Path | Previous path |", "|---|---|---|"]
        for entry in changed[:200]:
            previous = entry.get("previous_path") or ""
            lines.append(f"| {entry.get('status', '')} | `{entry.get('path', '')}` | `{previous}` |")
        if len(changed) > 200:
            lines.append(f"\n... and {len(changed) - 200} more changed file(s).")

    if route == "data-only":
        lines += [
            "", "Full canonical and publication validation still ran against the complete "
            "current dataset. Only the selected pytest targets were narrowed to the "
            "curator/data regression subset; the broader software test suite was not executed.",
        ]
    else:
        lines += ["", "The full relevant software regression suite ran."]

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
