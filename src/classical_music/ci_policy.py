"""CI validation-route policy (issue #308).

Classifies the files changed by a pull request into one of two execution
routes for ``.github/workflows/validate.yml``:

``data-only``
    Every changed path belongs to the curator/data allowlist below. The data
    route still runs full canonical and publication validation against the
    complete current dataset; it only narrows which pytest files run.

``full``
    Anything else: code, tests, schemas, dependencies, workflows, unknown
    paths, mixed changes, or any situation where the change set could not be
    established reliably.

Fail-safe invariant
--------------------
``classify()`` returns ``data-only`` only when ``diff_is_complete`` is true,
at least one file changed, and every changed path (including both sides of a
rename) is explicitly allowlisted. Any ambiguity, unknown git status, empty
or missing diff, or non-allowlisted path defaults to ``full``. This module
contains no logic that can silently widen the allowlist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Sequence

#: Git/GitHub change statuses this policy understands. Anything else is unknown.
KNOWN_STATUSES = frozenset({"added", "modified", "removed", "renamed", "copied", "changed", "unchanged"})

#: (path prefix, allowed suffixes) pairs. A path qualifies for data-only only
#: when it starts with one of these prefixes AND has one of the allowed
#: suffixes. New directories are not eligible until added here deliberately.
_ALLOWLIST: tuple[tuple[str, frozenset[str]], ...] = (
    ("data/", frozenset({".yaml"})),
    ("reports/playlist-import/", frozenset({".json", ".md"})),
    ("reports/curator-decisions/", frozenset({".json"})),
)


def _is_allowlisted(path: str) -> bool:
    """Whether one path qualifies for the data-only route on its own."""
    normalized = PurePosixPath(path)
    suffix = normalized.suffix.lower()
    posix = normalized.as_posix()
    return any(
        posix.startswith(prefix) and suffix in suffixes and not posix.endswith("/")
        for prefix, suffixes in _ALLOWLIST
    )


@dataclass(frozen=True)
class FileChange:
    """One changed path, in GitHub's own change-status vocabulary.

    ``previous_path`` is set for renames and copies; both ``path`` and
    ``previous_path`` must be allowlisted for a rename to qualify.
    """

    status: str
    path: str
    previous_path: str | None = None

    def paths(self) -> tuple[str, ...]:
        return tuple(p for p in (self.path, self.previous_path) if p)


@dataclass(frozen=True)
class Classification:
    """The routing decision and the evidence it was based on."""

    route: str  # "data-only" or "full"
    reason: str
    changed_files: tuple[FileChange, ...] = field(default_factory=tuple)
    diff_complete: bool = True

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "reason": self.reason,
            "diff_complete": self.diff_complete,
            "changed_files": [
                {"status": c.status, "path": c.path, "previous_path": c.previous_path}
                for c in self.changed_files
            ],
        }


def classify(
    changed_files: Sequence[FileChange],
    *,
    diff_complete: bool,
    force_full: bool = False,
    force_full_reason: str = "full validation was explicitly requested",
) -> Classification:
    """Classify a change set into a validation route.

    Args:
        changed_files: Every file the PR touched, in GitHub's change-status
            vocabulary. Must be the complete set; a partial list must be
            reported via ``diff_complete=False`` instead of silently omitting
            entries.
        diff_complete: Whether ``changed_files`` is known to be complete and
            trustworthy. False for any failure, timeout, pagination gap, or
            non-pull_request event where no reliable per-file diff exists.
        force_full: Operator override (manual workflow_dispatch) that always
            selects the full route regardless of the change set.
        force_full_reason: Message used when ``force_full`` is set.
    """
    changed_files = tuple(changed_files)

    if force_full:
        return Classification("full", force_full_reason, changed_files, diff_complete)

    if not diff_complete:
        return Classification(
            "full", "diff could not be established reliably; defaulting to full validation",
            changed_files, diff_complete,
        )

    if not changed_files:
        return Classification("full", "no changed files were reported", changed_files, diff_complete)

    for change in changed_files:
        if change.status not in KNOWN_STATUSES:
            return Classification(
                "full", f"unrecognized git change status {change.status!r} for {change.path!r}",
                changed_files, diff_complete,
            )
        for path in change.paths():
            if not _is_allowlisted(path):
                return Classification(
                    "full", f"{path!r} is not on the curator/data allowlist",
                    changed_files, diff_complete,
                )

    return Classification(
        "data-only",
        f"all {len(changed_files)} changed path(s) are on the curator/data allowlist",
        changed_files, diff_complete,
    )


#: Pytest targets run on the data-only route, matching the #307 guarantee matrix:
#: chamber/piano/best-classical ingestion, curator decision/rollback/lock
#: semantics, source preservation, the shared catalog snapshot and its
#: consumers (adapter/validator/site), parser and entity-matcher identity
#: resolution, fail-closed migration gates, and canonical validation rules.
#: Tidal-API, Jekyll-config and authority-duplicate-report tests are not
#: curator/data guarantees and stay in the full route only.
CURATOR_REGRESSION_TESTS: tuple[str, ...] = (
    "tests/test_catalog_snapshot.py",
    "tests/test_chamber_import.py",
    "tests/test_curator.py",
    "tests/test_curator_batch.py",
    "tests/test_curator_collections.py",
    "tests/test_curator_listening.py",
    "tests/test_original_arrangement_decisions.py",
    "tests/test_piano_import.py",
    "tests/test_prokofiev_alignment_policy.py",
    "tests/test_publication_adapter.py",
    "tests/test_publication_links.py",
    "tests/test_publication_site.py",
    "tests/test_publication_validator.py",
    "tests/test_suite_isolation.py",
    "tests/migration/test_entity_matcher.py",
    "tests/migration/test_migrate_failclosed.py",
    "tests/migration/test_parser.py",
    "tests/validation/test_validator.py",
)


def pytest_targets(classification: Classification) -> tuple[str, ...]:
    """Pytest positional arguments for the selected route.

    An empty tuple means "run pytest with its configured default discovery",
    i.e. the full suite from ``pyproject.toml``'s ``testpaths``.
    """
    if classification.route == "data-only":
        return CURATOR_REGRESSION_TESTS
    return ()
