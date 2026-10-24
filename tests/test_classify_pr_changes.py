"""Script-level tests for scripts/classify_pr_changes.py (issue #308).

These exercise the GitHub-event handling and GH API failure modes that the
pure classifier in ``classical_music.ci_policy`` does not see directly:
completeness proof for the paginated file list (PR #314 review finding 1)
and revision binding to the run's expected head/base SHAs (finding 2).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("classify_pr_changes", ROOT / "scripts/classify_pr_changes.py")
classify_script = importlib.util.module_from_spec(spec)
sys.modules["classify_pr_changes"] = classify_script  # dataclass() resolves annotations via sys.modules
spec.loader.exec_module(classify_script)

HEAD = "1111111111111111111111111111111111111111"
BASE = "2222222222222222222222222222222222222222"


def _completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["gh"], returncode=returncode, stdout=stdout, stderr=stderr)


def _metadata(head_sha=HEAD, base_sha=BASE, changed_files=1) -> dict:
    return {"head": {"sha": head_sha}, "base": {"sha": base_sha}, "changed_files": changed_files}


def _dispatcher(metadata_sequence, pages_by_number):
    """A fake ``subprocess.run`` distinguishing metadata calls from file-page calls.

    ``metadata_sequence`` is consumed in order on each metadata call (so a
    test can supply a different "before" and "after" response); the last
    value repeats once exhausted. ``pages_by_number`` maps page number to the
    list of file entries for that page.
    """
    calls: list[list[str]] = []
    metadata_iter = iter(metadata_sequence)
    last = [None]

    def fake_run(args, **kwargs):
        calls.append(args)
        if args[2].endswith("/files"):
            page = int(next(a for a in args if a.startswith("page=")).split("=")[1])
            return _completed(json.dumps(pages_by_number.get(page, [])))
        value = next(metadata_iter, None)
        if value is not None:
            last[0] = value
        return _completed(json.dumps(last[0]))

    return fake_run, calls


def _classify(monkeypatch, fake_run, **overrides):
    monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
    kwargs = dict(
        event_name="pull_request", repository="LuHoo/classical_music", pr_number="123",
        expected_head_sha=HEAD, expected_base_sha=BASE, force_full=False,
    )
    kwargs.update(overrides)
    return classify_script.build_classification(**kwargs)


class TestEventRouting:
    def test_push_event_is_always_full_without_calling_gh(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called for non-pull_request events")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result, evidence = classify_script.build_classification(
            event_name="push", repository="LuHoo/classical_music", pr_number=None,
            expected_head_sha=None, expected_base_sha=None, force_full=False,
        )
        assert result.route == "full"
        assert not result.diff_complete

    def test_workflow_dispatch_is_always_full(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called for workflow_dispatch")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result, _ = classify_script.build_classification(
            event_name="workflow_dispatch", repository="LuHoo/classical_music", pr_number=None,
            expected_head_sha=None, expected_base_sha=None, force_full=False,
        )
        assert result.route == "full"

    def test_force_full_short_circuits_even_for_pull_request(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called when force_full is set")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result, _ = _classify(monkeypatch, fail_if_called, force_full=True)
        assert result.route == "full"
        assert "explicitly requested" in result.reason

    def test_missing_pr_number_on_pull_request_event_is_full(self):
        result, _ = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="",
            expected_head_sha=HEAD, expected_base_sha=BASE, force_full=False,
        )
        assert result.route == "full"
        assert not result.diff_complete

    def test_non_numeric_pr_number_is_full(self):
        result, _ = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="abc",
            expected_head_sha=HEAD, expected_base_sha=BASE, force_full=False,
        )
        assert result.route == "full"

    def test_missing_repository_is_full(self):
        result, _ = classify_script.build_classification(
            event_name="pull_request", repository=None, pr_number="123",
            expected_head_sha=HEAD, expected_base_sha=BASE, force_full=False,
        )
        assert result.route == "full"


class TestSuccessfulClassification:
    def test_successful_api_call_classifies_data_only(self, monkeypatch):
        pages = {1: [
            {"status": "modified", "filename": "data/persons/bach.yaml"},
            {"status": "added", "filename": "reports/curator-decisions/issue-9.json"},
        ]}
        fake_run, calls = _dispatcher([_metadata(changed_files=2)], pages)
        result, evidence = _classify(monkeypatch, fake_run)
        assert result.route == "data-only"
        assert result.diff_complete
        assert evidence.changed_files_reported == 2
        assert evidence.changed_files_fetched == 2

    def test_successful_api_call_with_code_change_is_full(self, monkeypatch):
        pages = {1: [{"status": "modified", "filename": "src/classical_music/curator.py"}]}
        fake_run, _ = _dispatcher([_metadata(changed_files=1)], pages)
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"

    def test_rename_is_reported_with_both_paths(self, monkeypatch):
        pages = {1: [
            {"status": "renamed", "filename": "data/works/new.yaml", "previous_filename": "data/works/old.yaml"},
        ]}
        fake_run, _ = _dispatcher([_metadata(changed_files=1)], pages)
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "data-only"
        assert result.changed_files[0].previous_path == "data/works/old.yaml"

    def test_pagination_collects_every_page(self, monkeypatch):
        first_page = [{"status": "modified", "filename": f"data/works/w{i}.yaml"} for i in range(100)]
        second_page = [{"status": "modified", "filename": "data/works/w100.yaml"}]
        fake_run, calls = _dispatcher([_metadata(changed_files=101)], {1: first_page, 2: second_page})
        result, evidence = _classify(monkeypatch, fake_run)
        assert len(result.changed_files) == 101
        assert evidence.changed_files_fetched == 101
        assert result.route == "data-only"
        file_calls = [c for c in calls if c[2].endswith("/files")]
        assert len(file_calls) == 2

    def test_exact_multiple_of_page_size_requires_a_terminating_short_page(self, monkeypatch):
        """100 files exactly: page 1 is full (100), page 2 must be fetched and found empty
        to terminate pagination; the reported count (100) must match what was fetched."""
        first_page = [{"status": "modified", "filename": f"data/works/w{i}.yaml"} for i in range(100)]
        fake_run, calls = _dispatcher([_metadata(changed_files=100)], {1: first_page, 2: []})
        result, evidence = _classify(monkeypatch, fake_run)
        assert result.route == "data-only"
        assert evidence.changed_files_fetched == 100
        file_calls = [c for c in calls if c[2].endswith("/files")]
        assert len(file_calls) == 2  # page 2 was actually requested, not assumed empty


class TestCompletenessProof:
    """PR #314 review finding 1: a short/empty page alone does not prove completeness."""

    def test_early_empty_page_with_mismatched_count_degrades_to_full(self, monkeypatch):
        # Simulated silent truncation: metadata claims many files, but the API
        # (or a flaky response) returns nothing after page 1.
        first_page = [{"status": "modified", "filename": f"data/works/w{i}.yaml"} for i in range(50)]
        fake_run, _ = _dispatcher([_metadata(changed_files=2999)], {1: first_page, 2: []})
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert not result.diff_complete

    def test_thirty_pages_then_empty_page_with_mismatched_metadata_count_is_full(self, monkeypatch):
        # Reproduction from the review: 30 pages of 100 allowed files, then an
        # empty page, previously accepted as data-only with diff_complete=True.
        pages = {
            page: [{"status": "modified", "filename": f"data/works/w{page}_{i}.yaml"} for i in range(100)]
            for page in range(1, 31)
        }
        pages[31] = []
        # Metadata under-reports the true fetched count; must still fail closed.
        fake_run, _ = _dispatcher([_metadata(changed_files=2999)], pages)
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert "cannot be proven complete" in result.reason or "exceeding" in result.reason

    def test_duplicate_filenames_across_pages_degrade_to_full(self, monkeypatch):
        # Page 1 must be full (100 items) to trigger fetching page 2 at all;
        # page 2 repeats one filename from page 1.
        first_page = [{"status": "modified", "filename": f"data/works/w{i}.yaml"} for i in range(100)]
        second_page = [{"status": "modified", "filename": "data/works/w0.yaml"}]
        fake_run, _ = _dispatcher([_metadata(changed_files=100)], {1: first_page, 2: second_page})
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert "duplicate" in result.reason.lower()

    def test_missing_changed_files_metadata_degrades_to_full(self, monkeypatch):
        metadata = {"head": {"sha": HEAD}, "base": {"sha": BASE}}  # no changed_files key
        fake_run, _ = _dispatcher([metadata], {1: []})
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"

    def test_non_integer_changed_files_metadata_degrades_to_full(self, monkeypatch):
        metadata = {"head": {"sha": HEAD}, "base": {"sha": BASE}, "changed_files": "many"}
        fake_run, _ = _dispatcher([metadata], {1: []})
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"

    def test_count_mismatch_between_metadata_and_fetched_files_is_full(self, monkeypatch):
        pages = {1: [{"status": "modified", "filename": "data/works/w0.yaml"}]}
        fake_run, _ = _dispatcher([_metadata(changed_files=5)], pages)
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert "fetched 1 file record" in result.reason

    def test_exactly_3000_files_is_attempted(self, monkeypatch):
        def make_page(page_number):
            return [{"status": "modified", "filename": f"data/works/w{page_number}_{i}.yaml"} for i in range(100)]

        all_pages = {page: make_page(page) for page in range(1, 31)}
        all_pages[31] = []
        fake_run, calls = _dispatcher([_metadata(changed_files=3000)], all_pages)
        result, evidence = _classify(monkeypatch, fake_run)
        assert evidence.changed_files_reported == 3000
        assert result.route == "data-only"

    def test_more_than_3000_files_is_rejected_without_pagination(self, monkeypatch):
        calls_made = []

        def fake_run(args, **kwargs):
            calls_made.append(args)
            return _completed(json.dumps(_metadata(changed_files=3001)))

        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert "3000" in result.reason
        # Only the metadata call happened; pagination must not even start.
        file_calls = [c for c in calls_made if c[2].endswith("/files")]
        assert not file_calls

    def test_larger_diff_with_code_file_outside_fetched_portion_is_full(self, monkeypatch):
        # The code file is "missing" from what was fetched (simulated truncation);
        # the count mismatch this produces must still fail closed, never silently
        # proceed as if only the fetched (incomplete) portion were the whole diff.
        pages = {1: [{"status": "modified", "filename": "data/persons/bach.yaml"}]}
        fake_run, _ = _dispatcher([_metadata(changed_files=2)], pages)
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"


class TestRevisionBinding:
    """PR #314 review finding 2: classification must be bound to this run's revisions."""

    def test_matching_revisions_classify_normally(self, monkeypatch):
        pages = {1: [{"status": "modified", "filename": "data/persons/bach.yaml"}]}
        fake_run, _ = _dispatcher([_metadata(head_sha=HEAD, base_sha=BASE, changed_files=1)], pages)
        result, evidence = _classify(monkeypatch, fake_run)
        assert result.route == "data-only"
        assert evidence.observed_head_sha_before == HEAD
        assert evidence.observed_base_sha_before == BASE

    def test_mismatched_head_revision_is_full(self, monkeypatch):
        other_head = "9" * 40
        fake_run, _ = _dispatcher([_metadata(head_sha=other_head, base_sha=BASE, changed_files=1)], {1: []})
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert not result.diff_complete

    def test_mismatched_base_revision_is_full(self, monkeypatch):
        other_base = "8" * 40
        fake_run, _ = _dispatcher([_metadata(head_sha=HEAD, base_sha=other_base, changed_files=1)], {1: []})
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"

    def test_revision_changing_during_pagination_is_full(self, monkeypatch):
        before = _metadata(head_sha=HEAD, base_sha=BASE, changed_files=1)
        after = _metadata(head_sha="3" * 40, base_sha=BASE, changed_files=1)
        pages = {1: [{"status": "modified", "filename": "data/persons/bach.yaml"}]}
        fake_run, _ = _dispatcher([before, after], pages)
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert "changed while fetching" in result.reason

    def test_changed_files_count_changing_during_pagination_is_full(self, monkeypatch):
        before = _metadata(head_sha=HEAD, base_sha=BASE, changed_files=1)
        after = _metadata(head_sha=HEAD, base_sha=BASE, changed_files=2)
        pages = {1: [{"status": "modified", "filename": "data/persons/bach.yaml"}]}
        fake_run, _ = _dispatcher([before, after], pages)
        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"

    def test_missing_expected_revisions_is_full_without_any_api_call(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called without expected revisions")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result, _ = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123",
            expected_head_sha=None, expected_base_sha=None, force_full=False,
        )
        assert result.route == "full"
        assert not result.diff_complete

    def test_missing_expected_head_only_is_full(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called without both expected revisions")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result, _ = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123",
            expected_head_sha=None, expected_base_sha=BASE, force_full=False,
        )
        assert result.route == "full"

    def test_rerun_of_old_run_after_pr_changed_is_full(self, monkeypatch):
        """A re-run reuses the original (now stale) event context; the live PR
        has since moved to a new head. The stale expected head must not match."""
        stale_expected_head = "7" * 40
        current_live_head = HEAD
        fake_run, calls = _dispatcher(
            [_metadata(head_sha=current_live_head, base_sha=BASE, changed_files=1)], {1: []}
        )
        result, _ = _classify(monkeypatch, fake_run, expected_head_sha=stale_expected_head)
        assert result.route == "full"
        # Must fail before even attempting pagination.
        file_calls = [c for c in calls if c[2].endswith("/files")]
        assert not file_calls


class TestApiFailureModes:
    def test_gh_api_nonzero_exit_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            return _completed("", returncode=1, stderr="HTTP 403: rate limited")

        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"
        assert not result.diff_complete
        assert "could not retrieve changed files" in result.reason

    def test_gh_api_malformed_json_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            return _completed("not json")

        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"

    def test_gh_api_unexpected_shape_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            return _completed(json.dumps(["not", "a", "dict"]))

        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"

    def test_gh_api_timeout_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="gh", timeout=60)

        result, _ = _classify(monkeypatch, fake_run)
        assert result.route == "full"


class TestMainAndOutputs:
    def test_main_never_raises_and_always_exits_zero(self, monkeypatch, tmp_path):
        def explode(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(classify_script, "build_classification", explode)
        output = tmp_path / "classification.json"
        exit_code = classify_script.main(
            ["--event-name", "pull_request", "--repository", "x/y", "--pr-number", "1",
             "--expected-head-sha", HEAD, "--expected-base-sha", BASE, "--output", str(output)]
        )
        assert exit_code == 0
        payload = json.loads(output.read_text())
        assert payload["route"] == "full"
        assert "unexpected error" in payload["reason"]

    def test_github_output_contains_route_and_targets(self, monkeypatch, tmp_path):
        github_output = tmp_path / "github_output.txt"
        monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
        fake_run, _ = _dispatcher(
            [_metadata(changed_files=1)], {1: [{"status": "modified", "filename": "data/persons/bach.yaml"}]}
        )
        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        classify_script.main(
            ["--event-name", "pull_request", "--repository", "x/y", "--pr-number", "1",
             "--expected-head-sha", HEAD, "--expected-base-sha", BASE]
        )
        content = github_output.read_text()
        assert "route=data-only" in content
        assert "pytest_targets=" in content
        assert "tests/test_chamber_import.py" in content

    def test_output_json_includes_evidence_block(self, monkeypatch, tmp_path):
        fake_run, _ = _dispatcher(
            [_metadata(changed_files=1)], {1: [{"status": "modified", "filename": "data/persons/bach.yaml"}]}
        )
        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        output = tmp_path / "classification.json"
        classify_script.main(
            ["--event-name", "pull_request", "--repository", "x/y", "--pr-number", "1",
             "--expected-head-sha", HEAD, "--expected-base-sha", BASE, "--output", str(output)]
        )
        payload = json.loads(output.read_text())
        assert payload["evidence"]["expected_head_sha"] == HEAD
        assert payload["evidence"]["changed_files_reported"] == 1
        assert payload["evidence"]["changed_files_fetched"] == 1

    def test_no_github_output_env_is_a_silent_no_op(self, monkeypatch):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        from classical_music.ci_policy import Classification

        # Must not raise when GITHUB_OUTPUT is unset (e.g. local invocation).
        classify_script._write_github_output(Classification("full", "test", (), False))

