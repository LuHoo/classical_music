"""
Review categorization: Classify migration review items for curator action.

This module categorizes review items as:
- safe: Can be safely migrated to canonical (identity clear, matched existing)
- unchanged: Already in canonical form (no action needed)
- background: Non-actionable metadata gaps or improvements (Principle 16)
- consequential: Unresolved identity decisions (requires curator attention)

Principle 16: Distinguish errors, identity gates and background suspicions.
Only consequential items should be escalated to curator.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReviewCategory(Enum):
    """Classification of review outcomes."""

    SAFE = "safe"  # Can migrate confidently
    UNCHANGED = "unchanged"  # Already in canonical form
    BACKGROUND = "background"  # Non-actionable metadata
    CONSEQUENTIAL = "consequential"  # Requires curator decision


@dataclass(frozen=True)
class CategorizedReviewItem:
    """A review item with its category and rationale."""

    source_id: str
    source_file: str
    source_line: int
    work_text: str
    category: ReviewCategory
    rationale: str
    matched_entity_id: str | None = None
    action_required: bool = False


def categorize_review_items(
    review_items: list[dict[str, Any]],
    matched_entities: dict[str, str],  # source_id → canonical_entity_id
) -> list[CategorizedReviewItem]:
    """
    Categorize review items based on classifications and matches.

    Args:
        review_items: List of review items from migration-summary.json
        matched_entities: Map of source_id → existing canonical entity_id (if matched)

    Returns:
        List of CategorizedReviewItem with categories and rationales
    """
    categorized = []

    for item in review_items:
        source_id = item["source_id"]
        matched_id = matched_entities.get(source_id)
        classifications = item.get("classifications", [])

        # Determine category based on classifications and matches
        category, rationale, action_required = _classify_item(
            item, classifications, matched_id
        )

        categorized.append(
            CategorizedReviewItem(
                source_id=source_id,
                source_file=item["source_file"],
                source_line=item["source_line"],
                work_text=item["work_text"],
                category=category,
                rationale=rationale,
                matched_entity_id=matched_id,
                action_required=action_required,
            )
        )

    return categorized


def _classify_item(
    item: dict[str, Any],
    classifications: list[dict[str, Any]],
    matched_id: str | None,
) -> tuple[ReviewCategory, str, bool]:
    """
    Determine category, rationale and action_required for a single item.

    Returns: (category, rationale, action_required)
    """

    # If matched to existing entity, it's either unchanged or safe
    if matched_id:
        return (
            ReviewCategory.UNCHANGED,
            f"Matched to existing entity: {matched_id}",
            False,
        )

    # Analyze classifications to determine category
    if not classifications:
        return (
            ReviewCategory.SAFE,
            "No issues identified; ready for canonical migration",
            False,
        )

    # Check for consequential issues
    reasons = {c.get("reason") for c in classifications}

    # Consequential: Person/Work identity ambiguity
    if any(
        reason in ("person_ambiguous", "work_identity_unclear", "revision_vs_separate")
        for reason in reasons
    ):
        return (
            ReviewCategory.CONSEQUENTIAL,
            f"Unresolved identity decision: {', '.join(sorted(reasons))}",
            True,
        )

    # Background: Authority/metadata gaps (not actionable)
    if all(
        reason
        in (
            "missing_musicbrainz_id",
            "missing_gramophone_reference",
            "missing_tidal_link",
            "source_format_improvement",
            "metadata_incomplete",
        )
        for reason in reasons
    ):
        return (
            ReviewCategory.BACKGROUND,
            f"Non-actionable metadata: {', '.join(sorted(reasons))}. "
            "Authority lookup is demand-driven; external ID absence is not a defect.",
            False,
        )

    # Safe: Minor/non-blocking issues
    return (
        ReviewCategory.SAFE,
        f"Has minor issues but can migrate: {', '.join(sorted(reasons))}",
        False,
    )


def review_summary(categorized: list[CategorizedReviewItem]) -> dict[str, Any]:
    """
    Generate summary statistics for categorized review items.

    Returns dictionary with counts and breakdown by category.
    """
    by_category = {}
    for category in ReviewCategory:
        count = sum(1 for item in categorized if item.category == category)
        by_category[category.value] = count

    consequential = [
        item for item in categorized if item.category == ReviewCategory.CONSEQUENTIAL
    ]

    return {
        "total_items": len(categorized),
        "by_category": by_category,
        "consequential_count": len(consequential),
        "action_required_count": sum(1 for item in categorized if item.action_required),
        "consequential_items": [
            {
                "source_id": item.source_id,
                "source_file": item.source_file,
                "source_line": item.source_line,
                "work_text": item.work_text,
                "rationale": item.rationale,
            }
            for item in consequential
        ],
    }
