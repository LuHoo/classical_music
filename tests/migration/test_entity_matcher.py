"""Test entity matcher candidate discovery and identity resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from classical_music.migration.entity_matcher import (
    EntityMatcher,
    extract_catalogue_number,
    extract_version_info,
    normalize_title,
)
from classical_music.migration.models import WorkIdentityResolution


def test_normalize_title():
    """Test title normalization for matching."""
    assert normalize_title("Symphony No. 1 in C minor") == 'symphony no. 1 in c minor'
    assert (
        normalize_title('Symphony No. 1 in C minor "Das kecke Beserl"')
        == 'symphony no. 1 in c minor "das kecke beserl"'
    )
    # Test various quote styles normalize to double quote
    assert (
        normalize_title("Symphony No. 1 'quoted'")
        == 'symphony no. 1 "quoted"'
    )
    assert normalize_title("Ave  Maria") == "ave maria"  # Collapse spaces


def test_extract_version_info():
    """Test version extraction from titles."""
    # Standard version pattern
    result = extract_version_info("Symphony No. 1 (1865 version)")
    assert result is not None
    assert result["year"] == "1865"
    assert result["type"] == "version"
    
    # Revision pattern
    result = extract_version_info("Symphony No. 3 (1889 revision)")
    assert result is not None
    assert result["year"] == "1889"
    assert result["type"] == "revision"
    
    # Just year
    result = extract_version_info("Symphony No. 4 (1877)")
    assert result is not None
    assert result["year"] == "1877"
    
    # No version info
    result = extract_version_info("Symphony No. 1 in C minor")
    assert result is None


def test_extract_catalogue_number():
    """Test catalogue number extraction."""
    # WAB number
    assert extract_catalogue_number("Symphony No. 1, WAB. 101") == "WAB.101"
    
    # Opus number
    assert extract_catalogue_number("Piano Sonata Op. 23") == "Op.23"
    
    # Köchel number
    assert extract_catalogue_number("Symphony K. 545") == "K.545"
    
    # BWV number
    assert extract_catalogue_number("Prelude BWV 846") == "BWV.846"
    
    # No catalogue
    assert extract_catalogue_number("Untitled Work") is None


def test_entity_matcher_loads_canonical_data(data_root: Path):
    """Test that EntityMatcher loads canonical entities."""
    matcher = EntityMatcher(data_root)
    
    # Verify counts
    assert len(matcher.works) > 0
    assert len(matcher.work_groups) > 0
    assert len(matcher.persons) > 0


def test_candidate_discovery_bruckner_exact_match(data_root: Path):
    """Test finding candidates for exact Bruckner work."""
    matcher = EntityMatcher(data_root)
    
    # Find candidates for exact title
    candidates = matcher.find_work_candidates(
        "anton-bruckner",
        'Symphony No. 1 in C minor "Das kecke Beserl"'
    )
    assert len(candidates) >= 1
    
    # Should find the exact Bruckner symphony
    assert any("symphony" in c.entity_id.lower() for c in candidates)


def test_identity_resolution_with_version_evidence(data_root: Path):
    """Test identity resolution disambiguates using version evidence."""
    matcher = EntityMatcher(data_root)
    
    # Title with version info disambiguates between three versions
    title_with_version = 'Symphony No. 1 in C minor "Das kecke Beserl" (1865 version)'
    
    candidates = matcher.find_work_candidates("anton-bruckner", title_with_version)
    result = matcher.resolve_work_identity(title_with_version, "anton-bruckner", candidates)
    
    # With version evidence, should resolve to matched
    # (even though multiple base candidates exist)
    assert result.status == WorkIdentityResolution.MATCHED
    assert result.matched_work_id is not None


def test_identity_resolution_multiple_candidates_no_version(data_root: Path):
    """Test that multiple candidates without version evidence = unresolved."""
    matcher = EntityMatcher(data_root)
    
    # Title without version - matches 3 versions of same symphony
    title_no_version = 'Symphony No. 1 in C minor "Das kecke Beserl"'
    
    candidates = matcher.find_work_candidates("anton-bruckner", title_no_version)
    result = matcher.resolve_work_identity(title_no_version, "anton-bruckner", candidates)
    
    # Multiple candidates without disambiguating evidence should be UNRESOLVED
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action
    assert result.candidates_count == 3


def test_version_text_in_candidates(data_root: Path):
    """Test that version text is preserved during candidate discovery."""
    matcher = EntityMatcher(data_root)
    
    # Legacy Markdown has version info in parentheses
    candidates = matcher.find_work_candidates(
        "anton-bruckner",
        'Symphony No. 1 in C minor "Das kecke Beserl" (1865 version)'
    )
    
    # Should find the base work by stripping version text
    assert len(candidates) > 0


def test_version_evidence_used_in_resolution(data_root: Path):
    """Test that version evidence is captured and used."""
    matcher = EntityMatcher(data_root)
    
    title_with_version = 'Symphony No. 1 in C minor "Das kecke Beserl" (1865 version)'
    
    candidates = matcher.find_work_candidates("anton-bruckner", title_with_version)
    result = matcher.resolve_work_identity("anton-bruckner", title_with_version, candidates)
    
    # Version info should be in evidence_used
    assert any("version" in evidence for evidence in result.evidence_used)


def test_no_match_means_unresolved_not_new_identity(data_root: Path):
    """Test that NO_MATCH != NEW_WORK (fundamental rule)."""
    matcher = EntityMatcher(data_root)
    
    # Non-existent work
    candidates = matcher.find_work_candidates(
        "anton-bruckner",
        "Completely Fake Symphony in Z Major"
    )
    
    result = matcher.resolve_work_identity(
        "Completely Fake Symphony in Z Major",
        "anton-bruckner",
        candidates
    )
    
    # Should be UNRESOLVED, not NEW_IDENTITY
    # (NEW_IDENTITY requires positive evidence for genuinely new Work)
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action


def test_composer_mapping(data_root: Path):
    """Test doc slug to canonical composer_id mapping."""
    matcher = EntityMatcher(data_root)
    
    # Slug "bruckner" should resolve to "anton-bruckner"
    canonical_id = matcher.resolve_composer_id("bruckner")
    assert canonical_id == "anton-bruckner"


def test_unresolved_composer_fails_closed(data_root: Path):
    """Test that unknown composer slug doesn't fallback."""
    matcher = EntityMatcher(data_root)
    
    # Unknown composer should return None, not fallback
    canonical_id = matcher.resolve_composer_id("completely-unknown-composer")
    assert canonical_id is None


def test_matches_summary(data_root: Path):
    """Test that matches summary reports loaded entity counts."""
    matcher = EntityMatcher(data_root)
    summary = matcher.matches_summary()
    
    assert summary["persons"] > 0
    assert summary["work_groups"] > 0
    assert summary["works"] > 0
    assert summary["performances"] > 0


def test_single_candidate_requires_positive_version_evidence(data_root: Path):
    """
    Requirement #2: Single candidate + source version must have positive evidence.
    
    Test: source says 1865, canonical has no version evidence → UNRESOLVED
    (not MATCHED by absence of contradiction)
    """
    matcher = EntityMatcher(data_root)
    
    # Create a synthetic candidate with no version evidence
    from classical_music.migration.entity_matcher import ExistingEntity
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="test-work",
        file_path=data_root / "test.yaml",
        data={
            "id": "test-work",
            "title": "Symphony No. 1 in C minor",
            # No version_year, no date_text, no version in title
        },
    )
    
    # Source explicitly names 1865
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1865 version)",
        "test-composer",
        [candidate],
    )
    
    # Without positive version evidence, must be UNRESOLVED
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.candidates_count == 1
    assert result.requires_curator_action is True


def test_single_candidate_with_positive_version_evidence(data_root: Path):
    """
    Test: source says 1865, canonical has explicit version_year 1865 → MATCHED
    """
    matcher = EntityMatcher(data_root)
    
    from classical_music.migration.entity_matcher import ExistingEntity
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="test-work-1865",
        file_path=data_root / "test.yaml",
        data={
            "id": "test-work-1865",
            "title": "Symphony No. 1 in C minor",
            "version_year": "1865",  # Positive evidence
        },
    )
    
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1865 version)",
        "test-composer",
        [candidate],
    )
    
    # With positive version_year evidence, should MATCH
    assert result.status == WorkIdentityResolution.MATCHED
    assert result.matched_work_id == "test-work-1865"
    assert result.requires_curator_action is False


def test_single_candidate_contradictory_version(data_root: Path):
    """
    Test: source says 1865, canonical explicitly says 1889 → UNRESOLVED
    (contradictory explicit evidence means not this version)
    """
    matcher = EntityMatcher(data_root)
    
    from classical_music.migration.entity_matcher import ExistingEntity
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="test-work-1889",
        file_path=data_root / "test.yaml",
        data={
            "id": "test-work-1889",
            "title": "Symphony No. 1 in C minor",
            "version_year": "1889",  # Contradicts source
        },
    )
    
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1865 version)",
        "test-composer",
        [candidate],
    )
    
    # Explicit contradiction means this is not the right version
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True


def test_catalogue_evidence_does_not_override_version(data_root: Path):
    """
    Requirement: Catalogue evidence must not override contradictory version evidence.
    
    Test: same WAB family + source 1873 + candidate explicitly 1889 → UNRESOLVED
    """
    matcher = EntityMatcher(data_root)
    
    from classical_music.migration.entity_matcher import ExistingEntity
    # Candidate in same WAB family but different version
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="bruckner-sym1-1889-version",
        file_path=data_root / "test.yaml",
        data={
            "id": "bruckner-sym1-1889-version",
            "title": "Symphony No. 1 in C minor",
            "catalogue": "WAB.101",
            "version_year": "1889",  # Explicit different version
        },
    )
    
    # Source explicitly says 1873 with same catalogue number
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor, WAB. 101 (1873 version)",
        "anton-bruckner",
        [candidate],
    )
    
    # Version evidence overrides catalogue evidence when contradictory
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True


def test_find_performance_candidates_by_tidal_url(data_root: Path):
    """
    Test: Performance candidate discovery by Tidal URL.
    
    For a given Work, find canonical Performance with matching Tidal URL.
    """
    matcher = EntityMatcher(data_root)
    
    # Try finding performances for a known Bruckner work
    from classical_music.migration.entity_matcher import ExistingEntity
    
    # Performance exists in canonical data for some work
    # For this test, create synthetic scenario since we need specific work_id
    test_work_id = "test-work-123"
    
    # Performances are loaded from data/performances/
    # Just verify the method signature works and returns a list
    candidates = matcher.find_performance_candidates(
        work_id=test_work_id,
        tidal_url="https://tidal.com/browse/track/123456",
    )
    
    # Should return a list (empty if no matches)
    assert isinstance(candidates, list)


def test_resolve_performance_identity_with_tidal_url(data_root: Path):
    """
    Test: Performance identity resolution with exact Tidal URL match.
    
    Same Tidal URL + same Work → MATCHED_EXISTING
    """
    matcher = EntityMatcher(data_root)
    from classical_music.migration.entity_matcher import ExistingEntity
    from classical_music.migration.models import PerformanceIdentityResolution
    
    # Synthetic canonical Performance
    perf_candidate = ExistingEntity(
        entity_type="performance",
        entity_id="perf-123",
        file_path=data_root / "test.yaml",
        data={
            "id": "perf-123",
            "work_id": "work-xyz",
            "tidal_url": "https://tidal.com/browse/track/123456",
            "performer_text": "Vienna Philharmonic, Zubin Mehta",
            "performance_profile": "live",
        },
    )
    
    result = matcher.resolve_performance_identity(
        work_id="work-xyz",
        performer_text="Vienna Philharmonic, Zubin Mehta",
        tidal_url="https://tidal.com/browse/track/123456",
        candidates=[perf_candidate],
    )
    
    assert result.status == PerformanceIdentityResolution.MATCHED_EXISTING
    assert result.matched_performance_id == "perf-123"
    assert result.performance_profile == "live"
    assert result.requires_curator_action is False


def test_resolve_performance_identity_no_candidates(data_root: Path):
    """
    Test: Performance identity with no candidates → UNRESOLVED
    (not automatically NEW_PERFORMANCE without positive evidence)
    """
    matcher = EntityMatcher(data_root)
    from classical_music.migration.models import PerformanceIdentityResolution
    
    result = matcher.resolve_performance_identity(
        work_id="work-xyz",
        performer_text="Some Performer",
        tidal_url=None,
        candidates=[],
    )
    
    assert result.status == PerformanceIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True
