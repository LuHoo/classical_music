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
