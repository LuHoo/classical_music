"""Regression tests for scripts/validate_data.py's --json-output flag.

PR #314 review finding 5 explicitly requires proof that a validation failure
still writes the JSON report and returns a nonzero exit code, and that the
pre-existing --json flag stays compatible. A fake DataValidator is injected
so this never touches the real repository's canonical data.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_data", ROOT / "scripts/validate_data.py")
validate_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_data)

runner = CliRunner()


class FakeFinding:
    def __init__(self, **fields):
        fields.setdefault("status", None)
        self.__dict__.update(fields)
        self._fields = fields

    def model_dump(self):
        return dict(self._fields)


class FakeReport:
    def __init__(self, *, error_count, warning_count, findings):
        self.error_count = error_count
        self.warning_count = warning_count
        self.info_count = 0
        self.action_required_count = error_count
        self.background_suspicion_count = warning_count
        self.auto_resolved_count = 0
        self.findings = findings

    @property
    def has_errors(self):
        return self.error_count > 0


class FakeValidator:
    def __init__(self, *, report, repository_root=None):
        self._report = report

    def run(self, identity_gate_ids=None):
        return self._report


def _install_fake_validator(monkeypatch, report):
    def factory(repository_root=None):
        return FakeValidator(report=report, repository_root=repository_root)

    monkeypatch.setattr(validate_data, "DataValidator", factory)


class TestJsonOutputOnFailure:
    def test_failure_writes_json_and_returns_nonzero(self, monkeypatch, tmp_path):
        report = FakeReport(
            error_count=1, warning_count=0,
            findings=[FakeFinding(rule_id="SCH-001", severity="error", file="data/x.yaml", message="broken")],
        )
        _install_fake_validator(monkeypatch, report)

        output_path = tmp_path / "report.json"
        result = runner.invoke(validate_data.app, ["--json-output", str(output_path)])

        assert result.exit_code == 1
        assert output_path.exists(), "JSON report must be written even when validation fails"
        payload = json.loads(output_path.read_text())
        assert payload["error_count"] == 1

    def test_success_writes_json_and_returns_zero(self, monkeypatch, tmp_path):
        report = FakeReport(error_count=0, warning_count=2, findings=[])
        _install_fake_validator(monkeypatch, report)

        output_path = tmp_path / "report.json"
        result = runner.invoke(validate_data.app, ["--json-output", str(output_path)])

        assert result.exit_code == 0
        payload = json.loads(output_path.read_text())
        assert payload["warning_count"] == 2

    def test_json_output_coexists_with_console_table(self, monkeypatch, tmp_path):
        """--json-output must not suppress the human-readable table (no --json)."""
        report = FakeReport(
            error_count=0, warning_count=1,
            findings=[FakeFinding(rule_id="DUP-001", severity="warning", file="data/y.yaml", message="dup", status=None)],
        )
        _install_fake_validator(monkeypatch, report)

        output_path = tmp_path / "report.json"
        result = runner.invoke(validate_data.app, ["--json-output", str(output_path)])

        assert result.exit_code == 0
        assert "Canonical Data Validation" in result.stdout
        assert output_path.exists()


class TestJsonFlagStaysCompatible:
    def test_json_flag_prints_json_to_stdout(self, monkeypatch):
        report = FakeReport(error_count=0, warning_count=0, findings=[])
        _install_fake_validator(monkeypatch, report)

        result = runner.invoke(validate_data.app, ["--json"])

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["error_count"] == 0

    def test_json_flag_failure_still_returns_nonzero(self, monkeypatch):
        report = FakeReport(
            error_count=2, warning_count=0,
            findings=[FakeFinding(rule_id="X", severity="error", file="f", message="m")],
        )
        _install_fake_validator(monkeypatch, report)

        result = runner.invoke(validate_data.app, ["--json"])

        assert result.exit_code == 1
        payload = json.loads(result.stdout)
        assert payload["error_count"] == 2

    def test_json_and_json_output_can_be_combined(self, monkeypatch, tmp_path):
        report = FakeReport(error_count=0, warning_count=0, findings=[])
        _install_fake_validator(monkeypatch, report)
        output_path = tmp_path / "report.json"

        result = runner.invoke(validate_data.app, ["--json", "--json-output", str(output_path)])

        assert result.exit_code == 0
        json.loads(result.stdout)  # stdout is still valid JSON
        assert output_path.exists()
