from __future__ import annotations

import re

from .models import ReviewClassification, ReviewReason, SourceRecord


RULES: list[tuple[ReviewReason, re.Pattern[str], float, str]] = [
    (
        ReviewReason.VERSION_REVISION,
        re.compile(r"\brev\.?|revised|version\b", flags=re.IGNORECASE),
        0.9,
        "Source text suggests revision/version split.",
    ),
    (
        ReviewReason.ARRANGEMENT_ORCHESTRATION,
        re.compile(r"\barr\.?|arrangement|orchestrated|orchestration\b", flags=re.IGNORECASE),
        0.9,
        "Source text suggests arrangement or orchestration boundary.",
    ),
    (
        ReviewReason.COMPLETION_RECONSTRUCTION,
        re.compile(r"completed by|completion|reconstruction|unfinished", flags=re.IGNORECASE),
        0.92,
        "Source text suggests completion/reconstruction handling.",
    ),
    (
        ReviewReason.SUITE_EXCERPT_DERIVED,
        re.compile(r"suite from|excerpt from|overture|arias?|selection", flags=re.IGNORECASE),
        0.82,
        "Source text suggests suite/excerpt-derived identity.",
    ),
]


def classify_review_reason(record: SourceRecord) -> list[ReviewClassification]:
    text_parts = [record.work_text, record.raw_markdown]
    if record.performer_text:
        text_parts.append(record.performer_text)
    blob = " ".join(text_parts)

    findings: list[ReviewClassification] = []

    for reason, pattern, confidence, notes in RULES:
        if pattern.search(blob):
            findings.append(
                ReviewClassification(
                    reason=reason,
                    confidence=confidence,
                    notes=notes,
                )
            )

    if len(record.tidal_links) > 1:
        findings.append(
            ReviewClassification(
                reason=ReviewReason.MULTIPLE_TIDAL_LINKS,
                confidence=0.95,
                notes="Entry contains multiple Tidal URLs.",
            )
        )

    if not findings:
        findings.append(
            ReviewClassification(
                reason=ReviewReason.UNCERTAIN_MATCH,
                confidence=0.55,
                notes="No strong automatic classification; manual matching advised.",
            )
        )

    findings.sort(key=lambda item: item.confidence, reverse=True)
    return findings
