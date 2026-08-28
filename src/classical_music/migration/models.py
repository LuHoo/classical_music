from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum



class WorkIdentityResolution(StrEnum):
    """Result of resolving a source Work to canonical identity."""

    MATCHED = "matched"  # One specific canonical Work established
    NEW_IDENTITY = "new_identity"  # Positive evidence supports new Work
    UNRESOLVED = "unresolved"  # Cannot safely establish identity
    AUTHORITY_EVIDENCE_REQUIRED = "authority_evidence_required"
    BACKGROUND_ONLY = "background_only"  # Only non-identity metadata gap


class PerformanceIdentityResolution(StrEnum):
    """Result of resolving a source Performance to canonical identity."""

    MATCHED_EXISTING = "matched_existing"  # Canonical Performance identified
    NEW_PERFORMANCE = "new_performance"  # Positive evidence for new Performance
    UNRESOLVED = "unresolved"  # Cannot safely establish identity


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
    catalogue: str | None = None
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


@dataclass(slots=True)
class WorkIdentityResult:
    """Result of identity resolution for a source Work."""

    status: WorkIdentityResolution
    matched_work_id: str | None = None
    candidates_count: int = 0
    evidence_used: list[str] = field(default_factory=list)
    rationale: str = ""
    requires_curator_action: bool = False


@dataclass(slots=True)
class PerformanceIdentityResult:
    """Result of identity resolution for a source Performance."""

    status: PerformanceIdentityResolution
    matched_performance_id: str | None = None
    candidates_count: int = 0
    evidence_used: list[str] = field(default_factory=list)
    rationale: str = ""
    requires_curator_action: bool = False
    performance_profile: str | None = None  # Preserve profile from matched Performance
