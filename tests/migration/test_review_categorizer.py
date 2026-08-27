"""Test review categorization logic."""

from __future__ import annotations

import pytest

from classical_music.migration.review_categorizer import (
    ReviewCategory,
    categorize_review_items,
    review_summary,
)


def test_categorize_safe_item():
    """Test categorization of item with no issues."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Test Work",
            "classifications": [],
        }
    ]
    
    categorized = categorize_review_items(items, {})
    assert len(categorized) == 1
    assert categorized[0].category == ReviewCategory.SAFE
    assert not categorized[0].action_required


def test_categorize_unchanged_matched_item():
    """Test categorization of item matched to existing entity."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Symphony No. 1",
            "classifications": [],
        }
    ]
    matched = {"test-1": "existing-entity-id"}
    
    categorized = categorize_review_items(items, matched)
    assert len(categorized) == 1
    assert categorized[0].category == ReviewCategory.UNCHANGED
    assert categorized[0].matched_entity_id == "existing-entity-id"
    assert not categorized[0].action_required


def test_categorize_background_metadata_gaps():
    """Test that metadata gaps are categorized as background."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Test Work",
            "classifications": [
                {"reason": "missing_musicbrainz_id", "confidence": 0.9, "notes": ""},
                {"reason": "missing_tidal_link", "confidence": 0.8, "notes": ""},
            ],
        }
    ]
    
    categorized = categorize_review_items(items, {})
    assert len(categorized) == 1
    assert categorized[0].category == ReviewCategory.BACKGROUND
    assert not categorized[0].action_required


def test_categorize_consequential_identity_ambiguity():
    """Test that identity ambiguity requires curator action."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Ambiguous Work",
            "classifications": [
                {"reason": "work_identity_unclear", "confidence": 0.7, "notes": ""},
            ],
        }
    ]
    
    categorized = categorize_review_items(items, {})
    assert len(categorized) == 1
    assert categorized[0].category == ReviewCategory.CONSEQUENTIAL
    assert categorized[0].action_required


def test_review_summary_stats():
    """Test review summary statistics."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Work 1",
            "classifications": [],
        },
        {
            "source_id": "test-2",
            "source_file": "docs/test.md",
            "source_line": 20,
            "work_text": "Work 2",
            "classifications": [
                {"reason": "missing_musicbrainz_id", "confidence": 0.9, "notes": ""},
            ],
        },
        {
            "source_id": "test-3",
            "source_file": "docs/test.md",
            "source_line": 30,
            "work_text": "Work 3",
            "classifications": [
                {"reason": "person_ambiguous", "confidence": 0.8, "notes": ""},
            ],
        },
    ]
    matched = {"test-1": "existing-1"}
    
    categorized = categorize_review_items(items, matched)
    summary = review_summary(categorized)
    
    assert summary["total_items"] == 3
    assert summary["by_category"]["unchanged"] == 1  # Matched
    assert summary["by_category"]["safe"] == 0
    assert summary["by_category"]["background"] == 1  # Metadata gap
    assert summary["by_category"]["consequential"] == 1  # Identity issue
    assert summary["consequential_count"] == 1
    assert len(summary["consequential_items"]) == 1


def test_review_summary_identifies_consequential_items():
    """Test that review summary correctly identifies consequential items."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Revision vs Separate?",
            "classifications": [
                {"reason": "revision_vs_separate", "confidence": 0.7, "notes": ""},
            ],
        }
    ]
    
    categorized = categorize_review_items(items, {})
    summary = review_summary(categorized)
    
    assert summary["consequential_count"] == 1
    assert len(summary["consequential_items"]) == 1
    assert summary["consequential_items"][0]["source_id"] == "test-1"
    assert "Revision vs Separate" in summary["consequential_items"][0]["work_text"]
