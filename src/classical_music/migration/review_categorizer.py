"""
Review categorization: Classify migration review items for curator action.

This module categorizes review items based on ReviewReason classifications:
- safe: Matched to existing entity or no review reasons
- unchanged: Already matched to canonical entity (no action needed)
- background: Non-actionable classifications (Principle 16)
- consequential: Identity gates requiring curator review (Principle 4)

Real ReviewReason classifications:
- VERSION_REVISION: "revised version" text → identity gate (consequential)
- ARRANGEMENT_ORCHESTRATION: "orchestrated by" → identity gate (consequential)
- COMPLETION_RECONSTRUCTION: "completed by" → identity gate (consequential)
- SUITE_EXCERPT_DERIVED: "excerpt from" → identity gate (consequential)
- MULTIPLE_TIDAL_LINKS: Multiple Tidal URLs → background (pick first)
- UNCERTAIN_MATCH: Low confidence → background (no strong signal)

Principle 4: Identity gates require curator decision.
Principle 16: Distinguish errors/gates/background suspicions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from classical_music.migration.models import ReviewReason


class ReviewCategory(Enum):
    """Classification of review outcomes."""

    SAFE = "safe"  # No issues; can migrate confidently
    UNCHANGED = "unchanged"  # Already in canonical form (no action)
    BACKGROUND = "background"  # Non-actionable (demand-driven authority lookup)
    CONSEQUENTIAL = "consequential"  # Identity gate (requires curator decision)


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

    Based on actual ReviewReason classifications from real classifier.

    Returns: (category, rationale, action_required)
    """

    # If matched to existing entity, it's unchanged (no action needed)
    if matched_id:
        return (
            ReviewCategory.UNCHANGED,
            f"Matched to existing entity: {matched_id}",
            False,
        )

    # If no classifications, it's safe
    if not classifications:
        return (
            ReviewCategory.SAFE,
            "No review issues identified; ready for canonical migration",
            False,
        )

    # Extract reason values
    reasons = {c.get("reason") for c in classifications}

    # Identity gates: All of these require curator decision
    # (Principle 4: Identity gates require review)
    identity_gates = {
        ReviewReason.VERSION_REVISION,  # "rev." or "revised" text
        ReviewReason.ARRANGEMENT_ORCHESTRATION,  # "arr." or "arranged" text
        ReviewReason.COMPLETION_RECONSTRUCTION,  # "completed by" text
        ReviewReason.SUITE_EXCERPT_DERIVED,  # "excerpt from" or "suite" text
    }

    if any(r in identity_gates for r in reasons):
        # At least one identity gate found
        gate_reasons = [r for r in reasons if r in identity_gates]
        return (
            ReviewCategory.CONSEQUENTIAL,
            f"Identity gate(s) found: {', '.join(str(r) for r in gate_reasons)}. "
            f"Curator must decide if content represents distinct work or variant.",
            True,
        )

    # Background: Non-actionable classifications
    # (Principle 16: Background suspicions are not escalated)
    background_reasons = {
        ReviewReason.MULTIPLE_TIDAL_LINKS,  # Can pick first; not a defect
        ReviewReason.UNCERTAIN_MATCH,  # Low confidence; but still worth including
    }

    if all(r in background_reasons for r in reasons):
        return (
            ReviewCategory.BACKGROUND,
            f"Non-actionable classification(s): {', '.join(str(r) for r in reasons)}. "
            f"These do not block migration.",
            False,
        )

    # Safe: Minor issues that don't block migration
    return (
        ReviewCategory.SAFE,
        f"Has classification(s) but can migrate: {', '.join(str(r) for r in reasons)}",
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
