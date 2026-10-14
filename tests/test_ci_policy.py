"""Tests for the CI validation-route classifier (issue #308).

Covers the scenario table from the issue plus the additional edge cases the
repository's actual layout introduces (renames across the allowlist boundary,
unknown statuses, and force-full overrides).
"""

from __future__ import annotations

import pytest

from classical_music.ci_policy import (
    CURATOR_REGRESSION_TESTS,
    Classification,
    FileChange,
    classify,
    concurrency_group,
    pytest_targets,
)


def added(path: str) -> FileChange:
    return FileChange(status="added", path=path)


def modified(path: str) -> FileChange:
    return FileChange(status="modified", path=path)


def removed(path: str) -> FileChange:
    return FileChange(status="removed", path=path)


def renamed(old: str, new: str) -> FileChange:
    return FileChange(status="renamed", path=new, previous_path=old)


class TestScenarioTable:
    """One test per row of the issue's required scenario table."""

    def test_modification_of_allowlisted_curator_data_file_is_data_only(self):
        result = classify([modified("reports/curator-decisions/issue-246.json")], diff_complete=True)
        assert result.route == "data-only"

    def test_addition_of_allowlisted_data_file_is_data_only(self):
        result = classify([added("data/performances/new-performance.yaml")], diff_complete=True)
        assert result.route == "data-only"

    def test_deletion_of_allowlisted_data_file_is_data_only(self):
        result = classify([removed("data/work-groups/example.yaml")], diff_complete=True)
        assert result.route == "data-only"

    def test_rename_within_approved_data_paths_is_data_only(self):
        result = classify(
            [renamed("data/works/old-name.yaml", "data/works/new-name.yaml")], diff_complete=True
        )
        assert result.route == "data-only"

    def test_rename_from_data_to_code_is_full(self):
        result = classify(
            [renamed("data/works/example.yaml", "src/classical_music/example.py")], diff_complete=True
        )
        assert result.route == "full"

    def test_rename_from_code_to_data_is_full(self):
        result = classify(
            [renamed("src/classical_music/example.py", "data/works/example.yaml")], diff_complete=True
        )
        assert result.route == "full"

    def test_modification_of_application_code_is_full(self):
        result = classify([modified("src/classical_music/curator.py")], diff_complete=True)
        assert result.route == "full"

    def test_modification_of_a_schema_is_full(self):
        result = classify([modified("docs/architecture/minimal-yaml-schemas.md")], diff_complete=True)
        assert result.route == "full"

    def test_dependency_changes_are_full(self):
        result = classify([modified("pyproject.toml")], diff_complete=True)
        assert result.route == "full"

    def test_github_workflow_changes_are_full(self):
        result = classify([modified(".github/workflows/validate.yml")], diff_complete=True)
        assert result.route == "full"

    def test_test_code_or_fixture_changes_are_full(self):
        result = classify([modified("tests/test_curator.py")], diff_complete=True)
        assert result.route == "full"

    def test_test_fixture_json_changes_are_full(self):
        result = classify([modified("tests/fixtures/curator/pending-choices.json")], diff_complete=True)
        assert result.route == "full"

    def test_mixed_data_and_code_changes_are_full(self):
        result = classify(
            [modified("data/performances/example.yaml"), modified("src/classical_music/curator.py")],
            diff_complete=True,
        )
        assert result.route == "full"

    def test_unknown_file_path_is_full(self):
        result = classify([modified("something/unexpected.yaml")], diff_complete=True)
        assert result.route == "full"

    def test_new_directory_not_in_allowlist_is_full(self):
        result = classify([added("data-experiments/new.yaml")], diff_complete=True)
        assert result.route == "full"

    def test_empty_diff_is_full(self):
        result = classify([], diff_complete=True)
        assert result.route == "full"

    def test_missing_diff_is_full(self):
        result = classify([modified("data/persons/example.yaml")], diff_complete=False)
        assert result.route == "full"

    def test_incomplete_diff_is_full(self):
        # diff_complete=False models "we could not prove the diff is the full story".
        result = classify([modified("data/persons/example.yaml")], diff_complete=False)
        assert result.route == "full"

    def test_git_diff_failure_is_full(self):
        # Represented the same way as any unreliable change set: diff_complete=False.
        result = classify([], diff_complete=False)
        assert result.route == "full"

    def test_unknown_git_status_is_full(self):
        result = classify([FileChange(status="exotic", path="data/persons/example.yaml")], diff_complete=True)
        assert result.route == "full"

    def test_manual_forced_full_validation_is_full(self):
        result = classify([modified("data/persons/example.yaml")], diff_complete=True, force_full=True)
        assert result.route == "full"
        assert "explicitly requested" in result.reason


class TestAllowlistBoundaries:
    def test_non_yaml_file_under_data_is_not_allowlisted(self):
        result = classify([added("data/persons/notes.txt")], diff_complete=True)
        assert result.route == "full"

    def test_playlist_import_json_is_allowlisted(self):
        result = classify(
            [modified("reports/playlist-import/chamber/snapshot-2026-10-04.json")], diff_complete=True
        )
        assert result.route == "data-only"

    def test_playlist_import_generated_markdown_is_allowlisted(self):
        result = classify(
            [modified("reports/playlist-import/best-classical/window-333-1998.md")], diff_complete=True
        )
        assert result.route == "data-only"

    def test_curator_decisions_batch_status_is_allowlisted(self):
        result = classify([modified("reports/curator-decisions/batch-status.json")], diff_complete=True)
        assert result.route == "data-only"

    def test_similarly_named_but_different_directory_is_not_allowlisted(self):
        # "reports/curator-decisions-archive/..." must not match the "reports/curator-decisions/" prefix.
        result = classify([modified("reports/curator-decisions-archive/old.json")], diff_complete=True)
        assert result.route == "full"

    def test_docs_are_not_allowlisted(self):
        result = classify([modified("docs/bruckner.md")], diff_complete=True)
        assert result.route == "full"

    def test_side_materials_are_not_allowlisted(self):
        result = classify([modified("side materials/Music collection/Grove/Schubert.doc")], diff_complete=True)
        assert result.route == "full"

    def test_generated_legacy_is_not_allowlisted(self):
        result = classify(
            [modified("generated/legacy/grouped-works/johann-sebastian-bach/works.yaml")], diff_complete=True
        )
        assert result.route == "full"

    def test_multiple_allowlisted_files_across_directories_is_data_only(self):
        result = classify(
            [
                modified("data/persons/bach.yaml"),
                added("data/performances/new.yaml"),
                modified("reports/playlist-import/piano/snapshot-2026-10-04.json"),
                modified("reports/curator-decisions/issue-240.json"),
            ],
            diff_complete=True,
        )
        assert result.route == "data-only"


class TestPytestTargets:
    def test_data_only_route_selects_the_curator_regression_subset(self):
        result = classify([modified("data/persons/bach.yaml")], diff_complete=True)
        assert pytest_targets(result) == CURATOR_REGRESSION_TESTS

    def test_full_route_selects_no_explicit_targets(self):
        result = classify([modified("src/classical_music/curator.py")], diff_complete=True)
        assert pytest_targets(result) == ()

    def test_curator_regression_tests_are_real_files(self):
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[1]
        missing = [path for path in CURATOR_REGRESSION_TESTS if not (root / path).is_file()]
        assert not missing, f"CURATOR_REGRESSION_TESTS references missing files: {missing}"


class TestClassificationSerialization:
    def test_to_dict_round_trips_essential_fields(self):
        result = classify([renamed("data/works/a.yaml", "data/works/b.yaml")], diff_complete=True)
        payload = result.to_dict()
        assert payload["route"] == "data-only"
        assert payload["diff_complete"] is True
        assert payload["changed_files"] == [
            {"status": "renamed", "path": "data/works/b.yaml", "previous_path": "data/works/a.yaml"}
        ]


class TestIncompleteFileRecordsAreRejected:
    """Reproductions from the PR #314 review: a record must not vacuously pass
    because its missing path is filtered out of the evidence used."""

    def test_empty_path_is_rejected(self):
        result = classify([FileChange(status="modified", path="")], diff_complete=True)
        assert result.route == "full"
        assert "invalid file path" in result.reason

    def test_whitespace_only_path_is_rejected(self):
        result = classify([FileChange(status="modified", path="   ")], diff_complete=True)
        assert result.route == "full"

    def test_path_with_surrounding_whitespace_is_rejected(self):
        result = classify([FileChange(status="modified", path=" data/persons/bach.yaml")], diff_complete=True)
        assert result.route == "full"

    def test_null_path_is_rejected(self):
        result = classify([FileChange(status="modified", path=None)], diff_complete=True)  # type: ignore[arg-type]
        assert result.route == "full"

    def test_absolute_path_is_rejected(self):
        result = classify([FileChange(status="modified", path="/data/persons/bach.yaml")], diff_complete=True)
        assert result.route == "full"

    def test_dot_dot_segment_is_rejected(self):
        result = classify([FileChange(status="modified", path="data/../secrets.yaml")], diff_complete=True)
        assert result.route == "full"

    def test_renamed_without_previous_path_is_rejected(self):
        result = classify([FileChange(status="renamed", path="data/a.yaml")], diff_complete=True)
        assert result.route == "full"
        assert "missing a valid previous path" in result.reason

    def test_renamed_with_empty_previous_path_is_rejected(self):
        result = classify(
            [FileChange(status="renamed", path="data/a.yaml", previous_path="")], diff_complete=True
        )
        assert result.route == "full"

    def test_renamed_with_whitespace_previous_path_is_rejected(self):
        result = classify(
            [FileChange(status="renamed", path="data/a.yaml", previous_path="   ")], diff_complete=True
        )
        assert result.route == "full"

    def test_copied_without_previous_path_is_rejected(self):
        result = classify([FileChange(status="copied", path="data/a.yaml")], diff_complete=True)
        assert result.route == "full"

    def test_valid_rename_within_allowlist_still_passes(self):
        result = classify(
            [FileChange(status="renamed", path="data/works/new.yaml", previous_path="data/works/old.yaml")],
            diff_complete=True,
        )
        assert result.route == "data-only"

    def test_rename_across_boundary_data_to_code_still_rejected(self):
        result = classify(
            [FileChange(status="renamed", path="src/classical_music/x.py", previous_path="data/works/old.yaml")],
            diff_complete=True,
        )
        assert result.route == "full"

    def test_rename_across_boundary_code_to_data_still_rejected(self):
        result = classify(
            [FileChange(status="renamed", path="data/works/new.yaml", previous_path="src/classical_music/x.py")],
            diff_complete=True,
        )
        assert result.route == "full"

    def test_invalid_record_alongside_otherwise_valid_records_still_fails_closed(self):
        result = classify(
            [
                modified("data/persons/bach.yaml"),
                FileChange(status="modified", path=""),
                modified("data/performances/new.yaml"),
            ],
            diff_complete=True,
        )
        assert result.route == "full"

    def test_invalid_record_is_preserved_in_the_evidence_list(self):
        """An invalid record must not disappear from changed_files/to_dict()."""
        change = FileChange(status="modified", path="")
        result = classify([change], diff_complete=True)
        assert change in result.changed_files
        assert result.to_dict()["changed_files"] == [
            {"status": "modified", "path": "", "previous_path": None}
        ]


class TestConcurrencyGroup:
    """PR #314 review finding 4: non-PR events must never share a group.

    This is a static mirror of ``validate.yml``'s ``concurrency.group``
    expression (see that module-level docstring), not proof of GitHub's
    actual scheduling behaviour. It proves the *invariant* the expression is
    meant to encode: same PR shares one group; every other run gets a group
    unique to that run attempt.
    """

    def test_repeated_pushes_to_the_same_pr_share_one_group(self):
        first = concurrency_group(pr_number=350, run_id="1001", run_attempt="1")
        second = concurrency_group(pr_number=350, run_id="1002", run_attempt="1")
        assert first == second

    def test_two_different_pull_requests_get_different_groups(self):
        pr_350 = concurrency_group(pr_number=350, run_id="1001", run_attempt="1")
        pr_351 = concurrency_group(pr_number=351, run_id="1001", run_attempt="1")
        assert pr_350 != pr_351

    def test_three_non_pr_runs_on_the_same_ref_all_get_distinct_groups(self):
        run_a = concurrency_group(pr_number=None, run_id="5001", run_attempt="1")
        run_b = concurrency_group(pr_number=None, run_id="5002", run_attempt="1")
        run_c = concurrency_group(pr_number=None, run_id="5003", run_attempt="1")
        assert len({run_a, run_b, run_c}) == 3

    def test_a_rerun_attempt_of_the_same_non_pr_run_gets_a_distinct_group(self):
        attempt_1 = concurrency_group(pr_number=None, run_id="5001", run_attempt="1")
        attempt_2 = concurrency_group(pr_number=None, run_id="5001", run_attempt="2")
        assert attempt_1 != attempt_2

    def test_non_pr_groups_cannot_collide_with_pr_groups(self):
        # A PR number and a run_id can coincide numerically; the prefixes must
        # still make the two namespaces disjoint.
        pr_group = concurrency_group(pr_number=5001, run_id="irrelevant", run_attempt="1")
        run_group = concurrency_group(pr_number=None, run_id="5001", run_attempt="1")
        assert pr_group != run_group


