#!/usr/bin/env python3
"""Classify a pull request's changed files into a CI validation route (issue #308).

Usage (inside GitHub Actions):

    GH_TOKEN=... python scripts/classify_pr_changes.py \\
        --event-name "$GITHUB_EVENT_NAME" \\
        --repository "$GITHUB_REPOSITORY" \\
        --pr-number "${{ github.event.pull_request.number }}" \\
        --expected-head-sha "${{ github.event.pull_request.head.sha }}" \\
        --expected-base-sha "${{ github.event.pull_request.base.sha }}" \\
        --force-full "${{ inputs.force_full }}" \\
        --output ci-metrics/classification.json

Deliberately uses ``github.event.pull_request.head.sha``/``base.sha``, not
``github.sha``: for ``pull_request`` events, ``github.sha`` is the synthetic
merge commit Actions checks out, not the PR's actual head commit.

Writes the classification JSON (plus an ``evidence`` block proving which
revisions and file counts the decision was based on) to ``--output`` and,
when ``GITHUB_OUTPUT`` is set, the ``route``, ``reason`` and space-joined
``pytest_targets`` step outputs.

This script degrades to the full route and exits 0 on any failure to obtain
a reliable, complete change list (missing token, API error, non-JSON
response, pull_request context without a PR number, revision mismatch, a
files-list that cannot be proven complete, and so on). It never raises: a
classification failure must never abort the workflow, because the full
route is always safe.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
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

#: GitHub's documented hard cap: "Responses include a maximum of 3000 files."
#: https://docs.github.com/en/rest/pulls/pulls#list-pull-requests-files
#: Above this, the files-list endpoint cannot return the complete diff, so
#: completeness can never be proven and the full route must be used.
MAX_PROVABLE_FILES = 3000
_PAGE_SIZE = 100


@dataclass
class ApiEvidence:
    """What the classification's completeness and revision claims rest on.

    Kept separate from the pure ``Classification`` dataclass in
    ``ci_policy``, which has no concept of GitHub API revisions or pagination.
    """

    expected_head_sha: str | None = None
    expected_base_sha: str | None = None
    observed_head_sha_before: str | None = None
    observed_base_sha_before: str | None = None
    observed_head_sha_after: str | None = None
    observed_base_sha_after: str | None = None
    changed_files_reported: int | None = None
    changed_files_fetched: int | None = None


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _require_field(metadata: object, *path: str) -> object:
    cursor = metadata
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            raise RuntimeError(f"PR metadata is missing expected field {'.'.join(path)!r}")
        cursor = cursor[key]
    return cursor


def _fetch_pr_metadata(repository: str, pr_number: int) -> dict:
    """Fetch the single PR resource (not the paginated file list)."""
    result = subprocess.run(
        ["gh", "api", f"repos/{repository}/pulls/{pr_number}"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api (pull request metadata) failed (exit {result.returncode}): {result.stderr.strip()[:500]}")
    metadata = json.loads(result.stdout)
    if not isinstance(metadata, dict):
        raise RuntimeError(f"unexpected gh api response shape for PR metadata: {type(metadata).__name__}")
    return metadata


def _fetch_pr_files_page(repository: str, pr_number: int, page: int) -> list[dict]:
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repository}/pulls/{pr_number}/files",
            "-X", "GET",
            "-f", "per_page=" + str(_PAGE_SIZE),
            "-f", f"page={page}",
        ],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api (pull request files) failed (exit {result.returncode}): {result.stderr.strip()[:500]}")
    batch = json.loads(result.stdout)
    if not isinstance(batch, list):
        raise RuntimeError(f"unexpected gh api response shape for pull request files: {type(batch).__name__}")
    return batch


def _fetch_pr_evidence(
    repository: str, pr_number: int, expected_head_sha: str | None, expected_base_sha: str | None,
) -> tuple[list[FileChange], ApiEvidence]:
    """Fetch changed files for one PR with proof of completeness and revision match.

    Raises on any uncertainty: missing/invalid metadata, a revision mismatch
    (before or after pagination), an unprovable file count (missing,
    mismatched, duplicated, or exceeding GitHub's documented 3000-file cap),
    or an API failure. Using the REST API (rather than a local ``git diff``)
    means the classification always matches GitHub's own base/head
    computation for the PR, independent of checkout depth or force-pushes.
    """
    if not expected_head_sha or not expected_base_sha:
        raise RuntimeError("missing expected head/base revision for this run; cannot verify the diff applies to it")

    evidence = ApiEvidence(expected_head_sha=expected_head_sha, expected_base_sha=expected_base_sha)

    before = _fetch_pr_metadata(repository, pr_number)
    evidence.observed_head_sha_before = str(_require_field(before, "head", "sha"))
    evidence.observed_base_sha_before = str(_require_field(before, "base", "sha"))
    changed_files_reported = _require_field(before, "changed_files")
    if not isinstance(changed_files_reported, int) or changed_files_reported < 0:
        raise RuntimeError(f"PR metadata reports an invalid changed_files count: {changed_files_reported!r}")
    evidence.changed_files_reported = changed_files_reported

    if evidence.observed_head_sha_before != expected_head_sha or evidence.observed_base_sha_before != expected_base_sha:
        raise RuntimeError(
            "PR head/base revision does not match this run's expected revisions "
            f"(expected head={expected_head_sha} base={expected_base_sha}, "
            f"observed head={evidence.observed_head_sha_before} base={evidence.observed_base_sha_before})"
        )

    if changed_files_reported > MAX_PROVABLE_FILES:
        raise RuntimeError(
            f"PR reports {changed_files_reported} changed files, exceeding the files-list API's "
            f"documented {MAX_PROVABLE_FILES}-file cap; completeness cannot be proven"
        )

    entries: list[dict] = []
    page = 1
    while True:
        batch = _fetch_pr_files_page(repository, pr_number, page)
        entries.extend(batch)
        if len(batch) < _PAGE_SIZE:
            break
        page += 1
        if page > (MAX_PROVABLE_FILES // _PAGE_SIZE) + 1:
            raise RuntimeError("too many paginated results; refusing to continue")

    evidence.changed_files_fetched = len(entries)
    filenames = [entry.get("filename") for entry in entries]
    duplicates = [name for name, count in Counter(filenames).items() if count > 1]
    if duplicates:
        raise RuntimeError(f"duplicate filenames in paginated results, pagination is unreliable: {duplicates[:5]}")
    if len(entries) != changed_files_reported:
        raise RuntimeError(
            f"fetched {len(entries)} file record(s) but the PR reports {changed_files_reported}; "
            "the file list cannot be proven complete"
        )

    after = _fetch_pr_metadata(repository, pr_number)
    evidence.observed_head_sha_after = str(_require_field(after, "head", "sha"))
    evidence.observed_base_sha_after = str(_require_field(after, "base", "sha"))
    changed_files_after = _require_field(after, "changed_files")
    if (
        evidence.observed_head_sha_after != expected_head_sha
        or evidence.observed_base_sha_after != expected_base_sha
        or changed_files_after != changed_files_reported
    ):
        raise RuntimeError(
            "PR metadata changed while fetching its file list; the diff may no longer be the one "
            f"being validated (before: head={evidence.observed_head_sha_before} "
            f"files={changed_files_reported}; after: head={evidence.observed_head_sha_after} "
            f"files={changed_files_after})"
        )

    files = [
        FileChange(
            status=str(_GITHUB_STATUS_MAP.get(str(entry.get("status")), str(entry.get("status") or "unknown"))),
            path=str(entry.get("filename") or ""),
            previous_path=entry.get("previous_filename"),
        )
        for entry in entries
    ]
    return files, evidence


def build_classification(
    *,
    event_name: str,
    repository: str | None,
    pr_number: str | None,
    expected_head_sha: str | None,
    expected_base_sha: str | None,
    force_full: bool,
) -> tuple[Classification, ApiEvidence]:
    if force_full:
        return classify((), diff_complete=False, force_full=True), ApiEvidence()

    if event_name != "pull_request":
        return Classification(
            "full",
            f"event {event_name!r} is not a pull_request; full validation always runs on pushes and manual runs",
            (), False,
        ), ApiEvidence()

    if not repository or not pr_number or not pr_number.strip().isdigit():
        return Classification(
            "full", "missing repository or pull request number; cannot classify reliably", (), False,
        ), ApiEvidence()

    try:
        files, evidence = _fetch_pr_evidence(repository, int(pr_number), expected_head_sha, expected_base_sha)
    except Exception as error:  # noqa: BLE001 - any failure degrades to full, never aborts
        return Classification("full", f"could not retrieve changed files: {error}", (), False), ApiEvidence(
            expected_head_sha=expected_head_sha, expected_base_sha=expected_base_sha,
        )

    return classify(files, diff_complete=True), evidence


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
    parser.add_argument("--expected-head-sha", default=None,
                         help="github.event.pull_request.head.sha for this run; NOT github.sha.")
    parser.add_argument("--expected-base-sha", default=None,
                         help="github.event.pull_request.base.sha for this run.")
    parser.add_argument("--force-full", default="")
    parser.add_argument("--output", type=Path, default=None, help="Write classification JSON here")
    args = parser.parse_args(argv)

    try:
        classification, evidence = build_classification(
            event_name=args.event_name,
            repository=args.repository,
            pr_number=args.pr_number,
            expected_head_sha=args.expected_head_sha,
            expected_base_sha=args.expected_base_sha,
            force_full=_truthy(args.force_full),
        )
    except Exception as error:  # noqa: BLE001 - classification must never abort the workflow
        classification = Classification("full", f"classification raised an unexpected error: {error}", (), False)
        evidence = ApiEvidence(expected_head_sha=args.expected_head_sha, expected_base_sha=args.expected_base_sha)

    payload = classification.to_dict()
    payload["evidence"] = asdict(evidence)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)

    _write_github_output(classification)
    return 0  # A degraded classification is not a workflow failure; full validation covers it.


if __name__ == "__main__":
    sys.exit(main())

