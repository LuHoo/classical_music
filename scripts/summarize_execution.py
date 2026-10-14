#!/usr/bin/env python3
"""Render what actually executed for a GitHub job summary (issue #308 / PR #314 review).

Complements ``summarize_classification.py``, which only describes the
*selected* route before the pytest step runs. This script is meant to be
invoked after the relevant steps, with ``if: always()``, so it can report
the real outcome of the canonical validator and pytest steps (success,
failure, cancelled, skipped, or unknown) instead of inferring execution from
the classification alone. A missing artifact is never treated as proof of
success.
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _outcome_word(outcome: str | None) -> str:
    normalized = (outcome or "").strip().lower()
    if normalized == "success":
        return "succeeded"
    if normalized == "failure":
        return "failed"
    if normalized == "cancelled":
        return "cancelled"
    if normalized == "skipped":
        return "skipped"
    return f"unknown/incomplete ({outcome!r})"


def _parse_junit(path: Path) -> dict[str, int] | None:
    """Sum testsuite attributes; returns ``None`` if the file is missing or unparsable."""
    if not path.exists():
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    if not suites:
        return None
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.get(key, 0) or 0)
    return totals


def render(
    *,
    classification: dict[str, Any],
    validator_outcome: str | None,
    pytest_outcome: str | None,
    validation_report: dict[str, Any] | None,
    junit: dict[str, int] | None,
) -> str:
    route = classification.get("route", "unknown")
    lines = [
        "## Execution summary",
        "",
        f"Selected route (see Validation policy above): **{route}**",
        "",
        "| Control | Outcome | Detail |",
        "|---|---|---|",
    ]

    validator_detail = "no evidence available"
    if validation_report is not None:
        validator_detail = (
            f"errors={validation_report.get('error_count', '?')}, "
            f"warnings={validation_report.get('warning_count', '?')}"
        )
    elif (validator_outcome or "").strip().lower() in ("success", "failure"):
        validator_detail = "no validation-report.json found; not treated as success"
    lines.append(f"| Canonical validation | {_outcome_word(validator_outcome)} | {validator_detail} |")

    pytest_detail = "no evidence available"
    normalized_pytest = (pytest_outcome or "").strip().lower()
    if normalized_pytest == "skipped":
        pytest_detail = "not executed; a prior required step did not succeed"
    elif junit is not None:
        pytest_detail = (
            f"tests={junit['tests']}, failures={junit['failures']}, "
            f"errors={junit['errors']}, skipped={junit['skipped']}"
        )
    elif normalized_pytest in ("success", "failure"):
        pytest_detail = "no junit.xml found; not treated as success"
    lines.append(f"| Pytest (selected scope) | {_outcome_word(pytest_outcome)} | {pytest_detail} |")

    lines += [
        "",
        "Publication validation and cross-intake checks are established by the pytest step above "
        "(the curator/data regression subset on the data-only route, the full suite on the full route), "
        "not by the canonical validation step itself: `DataValidator.run()` does not invoke "
        "`PublicationValidator`. The separate \"Build and Deploy Jekyll site to GitHub Pages\" workflow "
        "independently builds the real site and checks internal links on every pull request, under its "
        "own required check; its result is not reflected in this summary.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--validator-outcome", default=None)
    parser.add_argument("--pytest-outcome", default=None)
    parser.add_argument("--validation-report", type=Path, default=None)
    parser.add_argument("--junit", type=Path, default=None)
    args = parser.parse_args(argv)

    classification: dict[str, Any] = {}
    if args.classification.exists():
        try:
            classification = json.loads(args.classification.read_text())
        except json.JSONDecodeError:
            classification = {}

    validation_report: dict[str, Any] | None = None
    if args.validation_report is not None and args.validation_report.exists():
        try:
            validation_report = json.loads(args.validation_report.read_text())
        except json.JSONDecodeError:
            validation_report = None

    junit = _parse_junit(args.junit) if args.junit is not None else None

    print(
        render(
            classification=classification,
            validator_outcome=args.validator_outcome,
            pytest_outcome=args.pytest_outcome,
            validation_report=validation_report,
            junit=junit,
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
