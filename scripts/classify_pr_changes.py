#!/usr/bin/env python3
"""Classify a pull request's changed files into a CI validation route (issue #308).

Usage (inside GitHub Actions):

    GH_TOKEN=... python scripts/classify_pr_changes.py \\
        --event-name "$GITHUB_EVENT_NAME" \\
        --repository "$GITHUB_REPOSITORY" \\
        --pr-number "${{ github.event.pull_request.number }}" \\
        --force-full "${{ inputs.force_full }}" \\
        --output ci-metrics/classification.json

Writes the classification JSON to ``--output`` and, when ``GITHUB_OUTPUT``
is set, the ``route``, ``reason`` and space-joined ``pytest_targets`` step
outputs.

This script degrades to the full route and exits 0 on any failure to obtain
a reliable, complete change list (missing token, API error, non-JSON
response, pull_request context without a PR number, and so on). It never
raises: a classification failure must never abort the workflow, because the
full route is always safe.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classical_music.ci_policy import (  # noqa: E402
    Classification,
    FileChange,
    classify,
    pytest_targets,
)

#: GitHub's own vocabulary, see
#: https://docs.github.com/en/rest/pulls/pulls#list-pull-requests-files
_GITHUB_STATUS_MAP = {
    "added": "added",
    "removed": "removed",
    "modified": "modified",
    "renamed": "renamed",
    "copied": "copied",
    "changed": "changed",
    "unchanged": "unchanged",
}


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _fetch_pr_files(repository: str, pr_number: int) -> list[FileChange]:
    """Fetch the complete, paginated list of changed files for one PR.

    Using the GitHub API (rather than a local ``git diff``) means the
    classification always matches GitHub's own base/head computation for the
    PR, independent of checkout depth, force-pushes, or multi-commit PRs, and
    natively reports add/remove/modify/rename/copy status.
    """
    files: list[FileChange] = []
    page = 1
    while True:
        result = subprocess.run(
            [
                "gh", "api",
                f"repos/{repository}/pulls/{pr_number}/files",
                "-X", "GET",
                "-f", f"per_page=100",
                "-f", f"page={page}",
            ],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"gh api failed (exit {result.returncode}): {result.stderr.strip()[:500]}")
        batch = json.loads(result.stdout)
        if not isinstance(batch, list):
            raise RuntimeError(f"unexpected gh api response shape: {type(batch).__name__}")
        for entry in batch:
            status = _GITHUB_STATUS_MAP.get(entry.get("status"), entry.get("status") or "unknown")
            files.append(
                FileChange(
                    status=status,
                    path=entry["filename"],
                    previous_path=entry.get("previous_filename"),
                )
            )
        if len(batch) < 100:
            break
        page += 1
        if page > 100:  # 10,000 files; treat as suspicious rather than loop forever
            raise RuntimeError("too many paginated results; refusing to continue")
    return files


def build_classification(
    *, event_name: str, repository: str | None, pr_number: str | None, force_full: bool,
) -> Classification:
    if force_full:
        return classify((), diff_complete=False, force_full=True)

    if event_name != "pull_request":
        return Classification(
            "full",
            f"event {event_name!r} is not a pull_request; full validation always runs on pushes and manual runs",
            (), False,
        )

    if not repository or not pr_number or not pr_number.strip().isdigit():
        return Classification(
            "full", "missing repository or pull request number; cannot classify reliably", (), False,
        )

    try:
        files = _fetch_pr_files(repository, int(pr_number))
    except Exception as error:  # noqa: BLE001 - any failure degrades to full, never aborts
        return Classification("full", f"could not retrieve changed files: {error}", (), False)

    return classify(files, diff_complete=True)


def _write_github_output(classification: Classification) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    targets = " ".join(pytest_targets(classification))
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"route={classification.route}\n")
        handle.write(f"reason<<CLASSIFY_REASON_EOF\n{classification.reason}\nCLASSIFY_REASON_EOF\n")
        handle.write(f"pytest_targets={targets}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--pr-number", default=None)
    parser.add_argument("--force-full", default="")
    parser.add_argument("--output", type=Path, default=None, help="Write classification JSON here")
    args = parser.parse_args(argv)

    try:
        classification = build_classification(
            event_name=args.event_name,
            repository=args.repository,
            pr_number=args.pr_number,
            force_full=_truthy(args.force_full),
        )
    except Exception as error:  # noqa: BLE001 - classification must never abort the workflow
        classification = Classification("full", f"classification raised an unexpected error: {error}", (), False)

    payload = classification.to_dict()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)

    _write_github_output(classification)
    return 0  # A degraded classification is not a workflow failure; full validation covers it.


if __name__ == "__main__":
    sys.exit(main())
