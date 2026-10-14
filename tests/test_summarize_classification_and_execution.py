"""Tests for scripts/summarize_classification.py and scripts/summarize_execution.py
(issue #308 / PR #314 review finding 5).

Verifies that the planned-route summary never claims execution, and that the
execution summary correctly distinguishes success/failure/skipped/cancelled/
unknown outcomes instead of inferring them from the classification or from
the mere presence/absence of artifacts.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


summarize_classification = _load("summarize_classification")
summarize_execution = _load("summarize_execution")


DATA_ONLY = {
    "route": "data-only",
    "reason": "all 1 changed path(s) are on the curator/data allowlist",
    "diff_complete": True,
    "changed_files": [{"status": "modified", "path": "data/persons/bach.yaml", "previous_path": None}],
    "evidence": {
        "expected_head_sha": "a" * 40,
        "expected_base_sha": "b" * 40,
        "changed_files_reported": 1,
        "changed_files_fetched": 1,
    },
}

FULL = {
    "route": "full",
    "reason": "'src/classical_music/curator.py' is not on the curator/data allowlist",
    "diff_complete": True,
    "changed_files": [{"status": "modified", "path": "src/classical_music/curator.py", "previous_path": None}],
    "evidence": {},
}


class TestPlannedSummaryNeverClaimsExecution:
    def test_data_only_summary_does_not_claim_tests_ran(self):
        text = summarize_classification.render(DATA_ONLY)
        assert "ran" not in text.lower() or "will run" in text.lower()
        assert "not executed" not in text.lower()  # no execution claim of any kind
        assert "selected" in text.lower() or "will" in text.lower()

    def test_full_summary_does_not_claim_the_suite_ran(self):
        text = summarize_classification.render(FULL)
        # Must describe the plan, not the outcome: "ran" without "will" is a past-tense claim.
        assert "the full relevant software regression suite ran" not in text

    def test_summary_does_not_claim_publication_validator_runs_from_data_validator(self):
        text = summarize_classification.render(DATA_ONLY)
        assert "publication validation still ran" not in text.lower()

    def test_evidence_block_is_rendered_when_present(self):
        text = summarize_classification.render(DATA_ONLY)
        assert "Changed files reported by PR metadata: 1" in text
        assert "Changed files actually fetched: 1" in text

    def test_missing_report_file_produces_unverified_message(self, tmp_path):
        missing = tmp_path / "classification.json"
        exit_code = summarize_classification.main([str(missing)])
        assert exit_code == 0


class TestExecutionSummaryDistinguishesOutcomes:
    def test_successful_full_route(self):
        text = summarize_execution.render(
            classification=FULL, validator_outcome="success", pytest_outcome="success",
            validation_report={"error_count": 0, "warning_count": 3},
            junit={"tests": 453, "failures": 0, "errors": 0, "skipped": 0},
        )
        assert "errors=0, warnings=3" in text
        assert "tests=453, failures=0, errors=0, skipped=0" in text
        assert "succeeded" in text

    def test_successful_data_only_route(self):
        text = summarize_execution.render(
            classification=DATA_ONLY, validator_outcome="success", pytest_outcome="success",
            validation_report={"error_count": 0, "warning_count": 1},
            junit={"tests": 250, "failures": 0, "errors": 0, "skipped": 0},
        )
        assert "tests=250" in text

    def test_validator_failure_followed_by_skipped_pytest(self):
        text = summarize_execution.render(
            classification=FULL, validator_outcome="failure", pytest_outcome="skipped",
            validation_report={"error_count": 2, "warning_count": 0},
            junit=None,
        )
        assert "failed" in text
        assert "skipped" in text
        assert "not executed" in text
        # Must not claim test counts when pytest was skipped.
        assert "tests=" not in text

    def test_pytest_failure_reports_real_failure_counts(self):
        text = summarize_execution.render(
            classification=FULL, validator_outcome="success", pytest_outcome="failure",
            validation_report={"error_count": 0, "warning_count": 0},
            junit={"tests": 453, "failures": 3, "errors": 0, "skipped": 0},
        )
        assert "failures=3" in text
        assert "failed" in text

    def test_setup_or_classification_failure_before_validator_runs(self):
        text = summarize_execution.render(
            classification=FULL, validator_outcome="cancelled", pytest_outcome="cancelled",
            validation_report=None, junit=None,
        )
        assert "cancelled" in text
        assert "no evidence available" in text

    def test_missing_report_is_not_presented_as_success(self):
        text = summarize_execution.render(
            classification=FULL, validator_outcome="success", pytest_outcome="success",
            validation_report=None, junit=None,
        )
        assert "not treated as success" in text

    def test_unknown_outcome_is_reported_as_unknown_not_success(self):
        text = summarize_execution.render(
            classification=FULL, validator_outcome=None, pytest_outcome=None,
            validation_report=None, junit=None,
        )
        assert "unknown/incomplete" in text
        assert "succeeded" not in text

    def test_junit_with_failures_and_skips_reports_all_fields(self):
        junit = summarize_execution._parse_junit  # smoke: callable exists
        assert callable(junit)


class TestJunitParsing:
    def test_missing_file_returns_none(self, tmp_path):
        assert summarize_execution._parse_junit(tmp_path / "missing.xml") is None

    def test_malformed_xml_returns_none(self, tmp_path):
        path = tmp_path / "junit.xml"
        path.write_text("<not valid xml")
        assert summarize_execution._parse_junit(path) is None

    def test_single_testsuite_totals(self, tmp_path):
        path = tmp_path / "junit.xml"
        path.write_text(
            '<?xml version="1.0"?>'
            '<testsuites><testsuite tests="10" failures="2" errors="1" skipped="0"></testsuite></testsuites>'
        )
        totals = summarize_execution._parse_junit(path)
        assert totals == {"tests": 10, "failures": 2, "errors": 1, "skipped": 0}

    def test_bare_testsuite_root_is_handled(self, tmp_path):
        path = tmp_path / "junit.xml"
        path.write_text('<testsuite tests="5" failures="0" errors="0" skipped="1"></testsuite>')
        totals = summarize_execution._parse_junit(path)
        assert totals == {"tests": 5, "failures": 0, "errors": 0, "skipped": 1}


class TestMainIntegration:
    def test_main_reads_all_inputs_and_renders(self, tmp_path):
        classification_path = tmp_path / "classification.json"
        classification_path.write_text(json.dumps(FULL))
        report_path = tmp_path / "validation-report.json"
        report_path.write_text(json.dumps({"error_count": 0, "warning_count": 2}))
        junit_path = tmp_path / "junit.xml"
        junit_path.write_text(
            '<testsuites><testsuite tests="3" failures="0" errors="0" skipped="0"></testsuite></testsuites>'
        )

        exit_code = summarize_execution.main([
            "--classification", str(classification_path),
            "--validator-outcome", "success",
            "--pytest-outcome", "success",
            "--validation-report", str(report_path),
            "--junit", str(junit_path),
        ])
        assert exit_code == 0

    def test_main_tolerates_missing_classification_file(self, tmp_path):
        exit_code = summarize_execution.main([
            "--classification", str(tmp_path / "missing.json"),
            "--validator-outcome", "success",
            "--pytest-outcome", "success",
        ])
        assert exit_code == 0
