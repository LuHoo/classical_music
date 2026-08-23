from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["error", "warning", "info"]


class ValidationFinding(BaseModel):
    rule_id: str
    severity: Severity
    file: str
    message: str
    entity_type: str | None = None
    entity_id: str | None = None
    field: str | None = None


class ValidationReport(BaseModel):
    findings: list[ValidationFinding] = Field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "info")

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0
