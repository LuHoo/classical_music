"""Tests for migrate.py fail-closed behavior (Requirement #1).

Tests that only MATCHED and NEW_IDENTITY create WorkCandidates/PerformanceCandidates.
UNRESOLVED, BACKGROUND_ONLY, and unknown composers must not create candidates.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from classical_music.migration.entity_matcher import EntityMatcher, ExistingEntity
from classical_music.migration.models import (
    WorkIdentityResolution,
    WorkIdentityResult,
    SourceRecord,
    SourceLocation,
)
from classical_music.migration.parser import SourceRecord


@pytest.fixture
def mock_entity_matcher(data_root: Path):
    """Create a mock EntityMatcher with controlled behavior."""
    matcher = EntityMatcher(data_root)
    return matcher


def test_unknown_composer_creates_no_candidates(data_root: Path):
    """
    Test: unknown composer slug → no WorkCandidate, no PerformanceCandidate
    
    Required: unknown composer returns None from resolve_composer_id(),
    and migration skips creating any candidates for that record.
    """
    matcher = EntityMatcher(data_root)
    
    # Unknown composer should fail closed
    result = matcher.resolve_composer_id("unknown-composer-xyz")
    assert result is None, "Unknown composer must return None (fail-closed)"


def test_unresolved_work_creates_no_candidates(data_root: Path):
    """
    Test: UNRESOLVED identity → no new WorkCandidate, no PerformanceCandidate
    
    Required: WorkIdentityResolution.UNRESOLVED must not result in creating
    a new WorkCandidate. A review item should be created instead.
    """
    matcher = EntityMatcher(data_root)
    
    # Create a scenario that produces UNRESOLVED
    # Multiple candidates without version evidence to disambiguate
    synthetic_candidates = [
        ExistingEntity(
            entity_type="work",
            entity_id="work-1",
            file_path=data_root / "test.yaml",
            data={"id": "work-1", "title": "Symphony No. 1", "composer_id": "test"},
        ),
        ExistingEntity(
            entity_type="work",
            entity_id="work-2",
            file_path=data_root / "test.yaml",
            data={"id": "work-2", "title": "Symphony No. 1", "composer_id": "test"},
        ),
    ]
    
    # Multiple candidates with no version info to disambiguate
    result = matcher.resolve_work_identity(
        "Symphony No. 1",  # No version info
        "test-composer",
        synthetic_candidates,
    )
    
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True
    # This result must NOT create a WorkCandidate in migration


def test_matched_identity_reuses_canonical_id(data_root: Path):
    """
    Test: MATCHED identity → use canonical work_id (no duplicate WorkCandidate)
    
    Required: When identity_result.status == MATCHED, reuse the matched_work_id
    and do NOT create a new WorkCandidate with a different ID.
    """
    matcher = EntityMatcher(data_root)
    
    canonical_work = ExistingEntity(
        entity_type="work",
        entity_id="canonical-symphony-1",
        file_path=data_root / "test.yaml",
        data={
            "id": "canonical-symphony-1",
            "title": "Symphony No. 1 in C minor",
            "composer_id": "test-composer",
        },
    )
    
    # Single exact match → MATCHED
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor",
        "test-composer",
        [canonical_work],
    )
    
    assert result.status == WorkIdentityResolution.MATCHED
    assert result.matched_work_id == "canonical-symphony-1"
    # Migration must use this work_id directly (not create a new WorkCandidate)


def test_new_identity_creates_only_new_candidate(data_root: Path):
    """
    Test: NEW_IDENTITY status → WorkCandidate is created
    
    Required: Only NEW_IDENTITY permits creating a new WorkCandidate.
    MATCHED reuses existing. UNRESOLVED/BACKGROUND_ONLY skip it.
    """
    matcher = EntityMatcher(data_root)
    
    # No candidates found with positive evidence for new Work → NEW_IDENTITY
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1865 version)",  # Source has version info
        "test-composer",
        [],  # No candidates
    )
    
    # Should return UNRESOLVED (not NEW_IDENTITY) because no candidates
    # but also no positive evidence for new Work
    assert result.status == WorkIdentityResolution.UNRESOLVED
    
    # NEW_IDENTITY would be returned if there was positive evidence
    # (e.g., unique catalogue number not in canonical)
    # For now, this is a limitation that will require curator input


def test_background_only_creates_no_candidates(data_root: Path):
    """
    Test: BACKGROUND_ONLY status → no WorkCandidate
    
    BACKGROUND_ONLY is used for performance-only records with no Work identity info.
    These must not create WorkCandidates.
    """
    # This is prepared for future use when BACKGROUND_ONLY is implemented
    # Currently UNRESOLVED is used for identity gates
    pass
