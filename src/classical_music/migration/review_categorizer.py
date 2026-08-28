"""
Review categorization: Classify migration review items for curator action.

This module categorizes review items based on WorkIdentityResult from entity_matcher:
- safe: Matched to existing entity or confirmed new identity
- unchanged: Already matched to canonical entity (no action needed)
- background: No identity information available (Principle 16)
- consequential: Unresolved identity requiring curator review (Principle 4)

WorkIdentityResolution status mapping:
- MATCHED: Existing canonical entity identified → unchanged
- NEW_IDENTITY: Positive evidence for new Work → safe (no curator action on identity)
- UNRESOLVED: No clear identity evidence → consequential (requires curator decision)
- AUTHORITY_EVIDENCE_REQUIRED: Repository evidence insufficient, authority gate before curator
- BACKGROUND_ONLY: Performance background only → background (not identity-affecting)

Principle 4: Unresolved identities require curator decision.
Principle 16: Distinguish actual issues from background info.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from classical_music.migration.models import (
    WorkIdentityResolution,
    WorkIdentityResult,
)


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
    items_with_identity_results: list[dict[str, Any]],
) -> list[CategorizedReviewItem]:
    """
    Categorize review items based on identity resolution results.

    Args:
        items_with_identity_results: List of dicts with keys:
            - source_id, source_file, source_line, work_text (source location info)
            - identity_result: WorkIdentityResult from entity_matcher

    Returns:
        List of CategorizedReviewItem with categories and rationales
    """
    categorized = []

    for item in items_with_identity_results:
        source_id = item["source_id"]
        identity_result: WorkIdentityResult = item["identity_result"]

        # Determine category based on identity resolution status
        category, rationale, action_required = _classify_by_identity(
            identity_result
        )

        categorized.append(
            CategorizedReviewItem(
                source_id=source_id,
                source_file=item["source_file"],
                source_line=item["source_line"],
                work_text=item["work_text"],
                category=category,
                rationale=rationale,
                matched_entity_id=identity_result.matched_work_id,
                action_required=action_required,
            )
        )

    return categorized


def _classify_by_identity(
    identity_result: WorkIdentityResult,
) -> tuple[ReviewCategory, str, bool]:
    """
    Determine category based on identity resolution status.

    Maps WorkIdentityResult status to ReviewCategory:
    - MATCHED → unchanged (no action needed)
    - NEW_IDENTITY → safe (positive evidence, can migrate)
    - UNRESOLVED → consequential (requires curator decision)
    - BACKGROUND_ONLY → background (no identity info)

    Returns: (category, rationale, action_required)
    """

    status = identity_result.status

    if status == WorkIdentityResolution.MATCHED:
        return (
            ReviewCategory.UNCHANGED,
            f"Matched to existing canonical work: {identity_result.matched_work_id}. "
            f"Evidence: {identity_result.evidence_used}",
            False,
        )

    if status == WorkIdentityResolution.NEW_IDENTITY:
        return (
            ReviewCategory.SAFE,
            f"Clear evidence for new identity. "
            f"Evidence: {identity_result.evidence_used}. "
            f"Rationale: {identity_result.rationale}",
            False,
        )

    if status == WorkIdentityResolution.UNRESOLVED:
        return (
            ReviewCategory.CONSEQUENTIAL,
            f"Unresolved identity. {identity_result.rationale} "
            f"Curator must decide based on available evidence.",
            identity_result.requires_curator_action,
        )

    if status == WorkIdentityResolution.AUTHORITY_EVIDENCE_REQUIRED:
        return (
            ReviewCategory.BACKGROUND,
            f"Authority evidence required before curator escalation. "
            f"Rationale: {identity_result.rationale}",
            False,
        )

    if status == WorkIdentityResolution.BACKGROUND_ONLY:
        return (
            ReviewCategory.BACKGROUND,
            f"No identity information (background context only). "
            f"Rationale: {identity_result.rationale}",
            False,
        )

    # Fallback (should not reach)
    return (
        ReviewCategory.SAFE,
        f"Unknown status: {status}",
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
