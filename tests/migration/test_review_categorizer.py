"""Test review categorization logic."""

from __future__ import annotations

import pytest

from classical_music.migration.models import ReviewReason
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
    """Test that MULTIPLE_TIDAL_LINKS is categorized as background."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Test Work",
            "classifications": [
                {
                    "reason": ReviewReason.MULTIPLE_TIDAL_LINKS,
                    "confidence": 0.95,
                    "notes": "Multiple Tidal URLs",
                },
            ],
        }
    ]

    categorized = categorize_review_items(items, {})
    assert len(categorized) == 1
    assert categorized[0].category == ReviewCategory.BACKGROUND
    assert not categorized[0].action_required


def test_categorize_consequential_identity_ambiguity():
    """Test that identity gates require curator action."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Revised Version",
            "classifications": [
                {
                    "reason": ReviewReason.VERSION_REVISION,
                    "confidence": 0.9,
                    "notes": "",
                },
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
                {"reason": ReviewReason.MULTIPLE_TIDAL_LINKS, "confidence": 0.95, "notes": ""},
            ],
        },
        {
            "source_id": "test-3",
            "source_file": "docs/test.md",
            "source_line": 30,
            "work_text": "Work 3",
            "classifications": [
                {"reason": ReviewReason.ARRANGEMENT_ORCHESTRATION, "confidence": 0.9, "notes": ""},
            ],
        },
    ]
    matched = {"test-1": "existing-1"}

    categorized = categorize_review_items(items, matched)
    summary = review_summary(categorized)

    assert summary["total_items"] == 3
    assert summary["by_category"]["unchanged"] == 1  # Matched
    assert summary["by_category"]["safe"] == 0
    assert summary["by_category"]["background"] == 1  # MULTIPLE_TIDAL_LINKS
    assert summary["by_category"]["consequential"] == 1  # ARRANGEMENT_ORCHESTRATION
    assert summary["consequential_count"] == 1
    assert len(summary["consequential_items"]) == 1


def test_review_summary_identifies_consequential_items():
    """Test that review summary correctly identifies consequential items."""
    items = [
        {
            "source_id": "test-1",
            "source_file": "docs/test.md",
            "source_line": 10,
            "work_text": "Revised Version",
            "classifications": [
                {
                    "reason": ReviewReason.VERSION_REVISION,
                    "confidence": 0.9,
                    "notes": "",
                },
            ],
        }
    ]

    categorized = categorize_review_items(items, {})
    summary = review_summary(categorized)

    assert summary["consequential_count"] == 1
    assert len(summary["consequential_items"]) == 1
    assert summary["consequential_items"][0]["source_id"] == "test-1"
    assert "Revised Version" in summary["consequential_items"][0]["work_text"]


def test_integration_parser_classifier_categorizer():
    """Integration test: Real parser → classifier → categorizer pipeline."""
    from pathlib import Path

    from classical_music.migration.classifier import classify_review_reason
    from classical_music.migration.parser import parse_composer_markdown

    # Get path to Bruckner docs
    docs_root = Path(__file__).resolve().parents[2] / "docs"
    bruckner_path = docs_root / "bruckner.md"

    if not bruckner_path.exists():
        pytest.skip(f"Test docs not found at {bruckner_path}")

    # Parse actual Bruckner doc
    records = parse_composer_markdown(bruckner_path)
    assert len(records) > 0, "Bruckner doc should have records"

    # Run each record through classifier
    items_for_categorizer = []
    for record in records[:5]:  # Test first 5 records
        classifications = classify_review_reason(record)

        items_for_categorizer.append(
            {
                "source_id": record.source_id,
                "source_file": record.location.source_file,
                "source_line": record.location.line_number,
                "work_text": record.work_text,
                "classifications": [
                    {
                        "reason": c.reason.value,
                        "confidence": c.confidence,
                        "notes": c.notes,
                    }
                    for c in classifications
                ],
            }
        )

    # Categorize the results
    categorized = categorize_review_items(items_for_categorizer, {})
    summary = review_summary(categorized)

    # Verify structure
    assert summary["total_items"] == len(items_for_categorizer)
    assert "by_category" in summary
    assert all(k in summary["by_category"] for k in ["safe", "unchanged", "background", "consequential"])

    # Every item should be categorized
    total_categorized = sum(summary["by_category"].values())
    assert total_categorized == summary["total_items"]
