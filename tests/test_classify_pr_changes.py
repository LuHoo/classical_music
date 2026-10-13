"""Script-level tests for scripts/classify_pr_changes.py (issue #308).

These exercise the GitHub-event handling and GH API failure modes that the
pure classifier in ``classical_music.ci_policy`` does not see directly.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("classify_pr_changes", ROOT / "scripts/classify_pr_changes.py")
classify_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classify_script)


def _completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["gh"], returncode=returncode, stdout=stdout, stderr=stderr)


class TestBuildClassification:
    def test_push_event_is_always_full_without_calling_gh(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called for non-pull_request events")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result = classify_script.build_classification(
            event_name="push", repository="LuHoo/classical_music", pr_number=None, force_full=False,
        )
        assert result.route == "full"
        assert not result.diff_complete

    def test_workflow_dispatch_is_always_full(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called for workflow_dispatch")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result = classify_script.build_classification(
            event_name="workflow_dispatch", repository="LuHoo/classical_music", pr_number=None, force_full=False,
        )
        assert result.route == "full"

    def test_force_full_short_circuits_even_for_pull_request(self, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("gh api must not be called when force_full is set")

        monkeypatch.setattr(classify_script.subprocess, "run", fail_if_called)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=True,
        )
        assert result.route == "full"
        assert "explicitly requested" in result.reason

    def test_missing_pr_number_on_pull_request_event_is_full(self):
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="", force_full=False,
        )
        assert result.route == "full"
        assert not result.diff_complete

    def test_non_numeric_pr_number_is_full(self):
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="abc", force_full=False,
        )
        assert result.route == "full"

    def test_missing_repository_is_full(self):
        result = classify_script.build_classification(
            event_name="pull_request", repository=None, pr_number="123", force_full=False,
        )
        assert result.route == "full"

    def test_successful_api_call_classifies_data_only(self, monkeypatch):
        payload = [
            {"status": "modified", "filename": "data/persons/bach.yaml"},
            {"status": "added", "filename": "reports/curator-decisions/issue-9.json"},
        ]

        def fake_run(args, **kwargs):
            assert args[:2] == ["gh", "api"]
            return _completed(json.dumps(payload))

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert result.route == "data-only"
        assert result.diff_complete

    def test_successful_api_call_with_code_change_is_full(self, monkeypatch):
        payload = [{"status": "modified", "filename": "src/classical_music/curator.py"}]

        def fake_run(args, **kwargs):
            return _completed(json.dumps(payload))

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert result.route == "full"

    def test_rename_is_reported_with_both_paths(self, monkeypatch):
        payload = [
            {"status": "renamed", "filename": "data/works/new.yaml", "previous_filename": "data/works/old.yaml"},
        ]

        def fake_run(args, **kwargs):
            return _completed(json.dumps(payload))

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert result.route == "data-only"
        assert result.changed_files[0].previous_path == "data/works/old.yaml"

    def test_gh_api_nonzero_exit_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            return _completed("", returncode=1, stderr="HTTP 403: rate limited")

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert result.route == "full"
        assert not result.diff_complete
        assert "could not retrieve changed files" in result.reason

    def test_gh_api_malformed_json_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            return _completed("not json")

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert result.route == "full"

    def test_gh_api_unexpected_shape_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            return _completed(json.dumps({"message": "not an array"}))

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert result.route == "full"

    def test_gh_api_timeout_degrades_to_full(self, monkeypatch):
        def fake_run(args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="gh", timeout=60)

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert result.route == "full"

    def test_pagination_collects_every_page(self, monkeypatch):
        first_page = [{"status": "modified", "filename": f"data/works/w{i}.yaml"} for i in range(100)]
        second_page = [{"status": "modified", "filename": "data/works/w100.yaml"}]
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            page = int(next(a for a in args if a.startswith("page=")).split("=")[1])
            return _completed(json.dumps(first_page if page == 1 else second_page))

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        result = classify_script.build_classification(
            event_name="pull_request", repository="LuHoo/classical_music", pr_number="123", force_full=False,
        )
        assert len(result.changed_files) == 101
        assert len(calls) == 2
        assert result.route == "data-only"


class TestMainAndOutputs:
    def test_main_never_raises_and_always_exits_zero(self, monkeypatch, tmp_path):
        def explode(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(classify_script, "build_classification", explode)
        output = tmp_path / "classification.json"
        exit_code = classify_script.main(
            ["--event-name", "pull_request", "--repository", "x/y", "--pr-number", "1", "--output", str(output)]
        )
        assert exit_code == 0
        payload = json.loads(output.read_text())
        assert payload["route"] == "full"
        assert "unexpected error" in payload["reason"]

    def test_github_output_contains_route_and_targets(self, monkeypatch, tmp_path):
        github_output = tmp_path / "github_output.txt"
        monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))

        def fake_run(args, **kwargs):
            return _completed(json.dumps([{"status": "modified", "filename": "data/persons/bach.yaml"}]))

        monkeypatch.setattr(classify_script.subprocess, "run", fake_run)
        classify_script.main(
            ["--event-name", "pull_request", "--repository", "x/y", "--pr-number", "1"]
        )
        content = github_output.read_text()
        assert "route=data-only" in content
        assert "pytest_targets=" in content
        assert "tests/test_chamber_import.py" in content

    def test_no_github_output_env_is_a_silent_no_op(self, monkeypatch):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        from classical_music.ci_policy import Classification

        # Must not raise when GITHUB_OUTPUT is unset (e.g. local invocation).
        classify_script._write_github_output(Classification("full", "test", (), False))
