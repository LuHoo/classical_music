"""Tests for review categorizer with WorkIdentityResult."""

import pytest
from classical_music.migration.models import (
    WorkIdentityResolution,
    WorkIdentityResult,
)
from classical_music.migration.review_categorizer import (
    ReviewCategory,
    _classify_by_identity,
    categorize_review_items,
)


class TestClassifyByIdentity:
    """Test identity result classification."""

    def test_matched_identity_is_unchanged(self):
        """Matched identity should be UNCHANGED (no action needed)."""
        result = WorkIdentityResult(
            status=WorkIdentityResolution.MATCHED,
            matched_work_id="test-work-123",
            candidates_count=1,
            evidence_used="exact_title_match",
            rationale="Title matches existing work exactly",
            requires_curator_action=False,
        )

        category, rationale, action_required = _classify_by_identity(result)

        assert category == ReviewCategory.UNCHANGED
        assert "test-work-123" in rationale
        assert action_required is False

    def test_new_identity_is_safe(self):
        """NEW_IDENTITY should be SAFE (positive evidence)."""
        result = WorkIdentityResult(
            status=WorkIdentityResolution.NEW_IDENTITY,
            matched_work_id=None,
            candidates_count=0,
            evidence_used="unique_catalogue_number",
            rationale="Work with this catalogue number does not exist in canonical",
            requires_curator_action=False,
        )

        category, rationale, action_required = _classify_by_identity(result)

        assert category == ReviewCategory.SAFE
        assert action_required is False

    def test_unresolved_identity_is_consequential(self):
        """UNRESOLVED should be CONSEQUENTIAL (curator decision needed)."""
        result = WorkIdentityResult(
            status=WorkIdentityResolution.UNRESOLVED,
            matched_work_id=None,
            candidates_count=3,
            evidence_used="partial_title_match",
            rationale="3 candidates found but no version evidence to disambiguate",
            requires_curator_action=True,
        )

        category, rationale, action_required = _classify_by_identity(result)

        assert category == ReviewCategory.CONSEQUENTIAL
        assert action_required is True

    def test_background_only_is_background(self):
        """BACKGROUND_ONLY should be BACKGROUND (no identity info)."""
        result = WorkIdentityResult(
            status=WorkIdentityResolution.BACKGROUND_ONLY,
            matched_work_id=None,
            candidates_count=0,
            evidence_used="",
            rationale="Only performance background available, no work identity",
            requires_curator_action=False,
        )

        category, rationale, action_required = _classify_by_identity(result)

        assert category == ReviewCategory.BACKGROUND
        assert action_required is False

    def test_unknown_identity_status_fails_closed(self):
        """Unknown identity statuses must not fall through to SAFE."""
        result = WorkIdentityResult(
            status="future_identity_status",
            matched_work_id=None,
            candidates_count=0,
            evidence_used=[],
            rationale="Unexpected status from resolver",
            requires_curator_action=False,
        )

        category, rationale, action_required = _classify_by_identity(result)

        assert category == ReviewCategory.CONSEQUENTIAL
        assert "future_identity_status" in rationale
        assert action_required is True


class TestCategorizeReviewItems:
    """Test batch categorization of review items."""

    def test_categorize_mixed_results(self):
        """Test categorizing items with different resolution statuses."""
        items = [
            {
                "source_id": "bach-001",
                "source_file": "tests/fixtures/bach.yaml",
                "source_line": 10,
                "work_text": "Invention No. 1 in C",
                "identity_result": WorkIdentityResult(
                    status=WorkIdentityResolution.MATCHED,
                    matched_work_id="bach-invention-1",
                    candidates_count=1,
                    evidence_used="exact_match",
                    rationale="",
                    requires_curator_action=False,
                ),
            },
            {
                "source_id": "unknown-001",
                "source_file": "tests/fixtures/unknown.yaml",
                "source_line": 25,
                "work_text": "Symphony in X major",
                "identity_result": WorkIdentityResult(
                    status=WorkIdentityResolution.UNRESOLVED,
                    matched_work_id=None,
                    candidates_count=2,
                    evidence_used="partial_match",
                    rationale="Found 2 candidates, unable to disambiguate",
                    requires_curator_action=True,
                ),
            },
        ]

        categorized = categorize_review_items(items)

        assert len(categorized) == 2
        assert categorized[0].category == ReviewCategory.UNCHANGED
        assert categorized[0].matched_entity_id == "bach-invention-1"
        assert categorized[1].category == ReviewCategory.CONSEQUENTIAL
        assert categorized[1].action_required is True

    def test_categorize_new_identity_items(self):
        """Test NEW_IDENTITY categorization."""
        items = [
            {
                "source_id": "new-001",
                "source_file": "fixtures.yaml",
                "source_line": 50,
                "work_text": "Symphony in Z major",
                "identity_result": WorkIdentityResult(
                    status=WorkIdentityResolution.NEW_IDENTITY,
                    matched_work_id=None,
                    candidates_count=0,
                    evidence_used="unique_composition",
                    rationale="No existing work with this profile",
                    requires_curator_action=False,
                ),
            },
        ]

        categorized = categorize_review_items(items)

        assert len(categorized) == 1
        assert categorized[0].category == ReviewCategory.SAFE
        assert categorized[0].action_required is False

    def test_categorize_background_only(self):
        """Test BACKGROUND_ONLY categorization."""
        items = [
            {
                "source_id": "perf-001",
                "source_file": "fixtures.yaml",
                "source_line": 100,
                "work_text": "Unknown performance",
                "identity_result": WorkIdentityResult(
                    status=WorkIdentityResolution.BACKGROUND_ONLY,
                    matched_work_id=None,
                    candidates_count=0,
                    evidence_used="",
                    rationale="Could not identify work, only have performance data",
                    requires_curator_action=False,
                ),
            },
        ]

        categorized = categorize_review_items(items)

        assert len(categorized) == 1
        assert categorized[0].category == ReviewCategory.BACKGROUND
        assert categorized[0].action_required is False
