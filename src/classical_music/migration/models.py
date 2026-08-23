from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ReviewReason(StrEnum):
    VERSION_REVISION = "version_revision"
    ARRANGEMENT_ORCHESTRATION = "arrangement_orchestration"
    COMPLETION_RECONSTRUCTION = "completion_reconstruction"
    SUITE_EXCERPT_DERIVED = "suite_excerpt_derived"
    MULTIPLE_TIDAL_LINKS = "multiple_tidal_links"
    UNCERTAIN_MATCH = "uncertain_match"


@dataclass(slots=True)
class SourceLocation:
    source_file: str
    line_number: int
    heading_path: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SourceRecord:
    source_id: str
    location: SourceLocation
    raw_markdown: str
    gem_marker: bool
    work_text: str
    date_text: str | None
    category: str | None
    tidal_links: list[str] = field(default_factory=list)
    performer_text: str | None = None
    gramophone_issue: str | None = None


@dataclass(slots=True)
class WorkCandidate:
    id: str
    work_group_id: str
    composer_id: str
    title: str
    gem: bool = False
    source_file: str | None = None
    source_line: int | None = None


@dataclass(slots=True)
class PerformanceCandidate:
    id: str
    work_id: str
    performer_text: str
    tidal_url: str
    gramophone_issue: str | None = None
    source_file: str | None = None
    source_line: int | None = None


@dataclass(slots=True)
class ReviewClassification:
    reason: ReviewReason
    confidence: float
    notes: str
