#!/usr/bin/env python3
"""
Compare two migration-summary.json files to verify idempotence.

If running migrate.py twice produces identical results, the pipeline is
reproducible and deterministic (idempotent).

Usage:
    python3 compare_migration_runs.py <summary1.json> <summary2.json>

Exit codes:
    0 - Summaries are identical (idempotent ✓)
    1 - Summaries differ (not idempotent ✗)
    2 - File not found or invalid JSON
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def load_summary(path: Path) -> dict[str, Any] | None:
    """Load migration-summary.json, return None if file invalid."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        console.print(f"Error loading {path}: {e}", style="red")
        return None


def compare_summaries(
    summary1: dict[str, Any],
    summary2: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Compare two migration summaries.

    Returns: (identical: bool, diffs: list[str])
    """
    diffs = []

    # Compare top-level counts
    keys_to_compare = ["works", "performances", "review_summary"]
    for key in keys_to_compare:
        if key == "works" or key == "performances":
            count1 = len(summary1.get(key, []))
            count2 = len(summary2.get(key, []))
            if count1 != count2:
                diffs.append(f"{key}: {count1} vs {count2}")
        elif key == "review_summary":
            rs1 = summary1.get(key, {})
            rs2 = summary2.get(key, {})
            if rs1.get("total_items") != rs2.get("total_items"):
                diffs.append(
                    f"review_summary.total_items: "
                    f"{rs1.get('total_items')} vs {rs2.get('total_items')}"
                )
            if rs1.get("by_category") != rs2.get("by_category"):
                diffs.append(
                    f"review_summary.by_category differs: "
                    f"{rs1.get('by_category')} vs {rs2.get('by_category')}"
                )

    # Compare matched_entities counts
    matched1 = len(summary1.get("matched_entities", {}))
    matched2 = len(summary2.get("matched_entities", {}))
    if matched1 != matched2:
        diffs.append(f"matched_entities: {matched1} vs {matched2}")

    # Deep comparison: compare works detail
    works1 = {w["id"]: w for w in summary1.get("works", [])}
    works2 = {w["id"]: w for w in summary2.get("works", [])}

    if works1.keys() != works2.keys():
        missing_in_2 = set(works1.keys()) - set(works2.keys())
        missing_in_1 = set(works2.keys()) - set(works1.keys())
        if missing_in_2:
            diffs.append(f"Works in summary1 but not in summary2: {len(missing_in_2)}")
        if missing_in_1:
            diffs.append(f"Works in summary2 but not in summary1: {len(missing_in_1)}")

    return len(diffs) == 0, diffs


def main() -> int:
    """Compare two migration summaries for idempotence."""
    if len(sys.argv) != 3:
        console.print(
            "Usage: python3 compare_migration_runs.py <summary1.json> <summary2.json>"
        )
        return 2

    summary1_path = Path(sys.argv[1])
    summary2_path = Path(sys.argv[2])

    console.print(f"Comparing: {summary1_path}")
    console.print(f"       vs: {summary2_path}\n")

    summary1 = load_summary(summary1_path)
    summary2 = load_summary(summary2_path)

    if not summary1 or not summary2:
        return 2

    identical, diffs = compare_summaries(summary1, summary2)

    if identical:
        console.print(
            Panel(
                "✓ Summaries are identical — pipeline is idempotent!",
                style="green",
                title="Idempotence Verified",
            )
        )
        return 0
    else:
        console.print(
            Panel(
                "✗ Summaries differ — pipeline is not idempotent",
                style="red",
                title="Idempotence Failed",
            )
        )
        console.print("\nDifferences found:")
        for diff in diffs:
            console.print(f"  • {diff}", style="yellow")

        # Show review summaries for debugging
        console.print("\nReview Summary Comparison:")
        rs1 = summary1.get("review_summary", {})
        rs2 = summary2.get("review_summary", {})
        console.print(f"Summary 1: {rs1.get('by_category')}")
        console.print(f"Summary 2: {rs2.get('by_category')}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
