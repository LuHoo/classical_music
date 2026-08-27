"""Test entity matcher functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from classical_music.migration.entity_matcher import EntityMatcher, normalize_title


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


def test_entity_matcher_loads_canonical_data(data_root: Path):
    """Test that EntityMatcher loads canonical entities."""
    matcher = EntityMatcher(data_root)
    
    # Verify counts
    assert len(matcher.works) > 0
    assert len(matcher.work_groups) > 0
    assert len(matcher.persons) > 0


def test_entity_matcher_find_bruckner_work(data_root: Path):
    """Test finding existing Bruckner work by composer and title."""
    matcher = EntityMatcher(data_root)
    
    # Try to find Bruckner Symphony No. 1
    # Use canonical composer_id from data/
    work = matcher.find_work(
        "anton-bruckner",
        'Symphony No. 1 in C minor "Das kecke Beserl"'
    )
    assert work is not None
    assert "bruckner" in work.entity_id.lower()
    assert "symphony" in work.entity_id.lower()


def test_entity_matcher_composer_mapping(data_root: Path):
    """Test doc slug to canonical composer_id mapping."""
    matcher = EntityMatcher(data_root)
    
    # Slug "bruckner" should resolve to "anton-bruckner"
    canonical_id = matcher.resolve_composer_id("bruckner")
    assert canonical_id == "anton-bruckner"


def test_entity_matcher_find_returns_none_for_unknown(data_root: Path):
    """Test that find_work returns None for non-existent works."""
    matcher = EntityMatcher(data_root)
    
    # Try to find work that doesn't exist
    work = matcher.find_work(
        "anton-bruckner",
        "Nonexistent Work"
    )
    assert work is None


def test_matches_summary(data_root: Path):
    """Test matches_summary() returns correct counts."""
    matcher = EntityMatcher(data_root)
    summary = matcher.matches_summary()
    
    assert "works" in summary
    assert "work_groups" in summary
    assert "persons" in summary
    assert "performances" in summary
    
    # Rough sanity checks
    assert summary["works"] > 0
    assert summary["work_groups"] > 0


# Pytest fixture to provide data_root path
@pytest.fixture
def data_root() -> Path:
    """Return path to test data directory."""
    return Path(__file__).resolve().parents[2] / "data"
