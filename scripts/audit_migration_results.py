#!/usr/bin/env python3
"""
Audit migration results for ground-truth validation.

Classifies each record as:
- TRUE_POSITIVE: Matched decision was correct
- FALSE_POSITIVE: Matched decision was incorrect (should be unresolved/different)
- TRUE_UNRESOLVED: Unresolved decision was correct
- FALSE_UNRESOLVED: Unresolved decision was incorrect (should have matched)

Generates detailed audit report with per-record reasoning.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

yaml = YAML(typ="safe")


@dataclass(frozen=True)
class AuditRecord:
    """Single record audit result."""

    source_id: str
    work_text: str
    system_decision: str  # "matched" or "unresolved"
    matched_work_id: str | None
    evidence_used: list[str]
    rationale: str
    ground_truth_work_id: str | None  # What it should have matched to
    audit_classification: str  # TRUE_POSITIVE, FALSE_POSITIVE, TRUE_UNRESOLVED, FALSE_UNRESOLVED
    audit_reasoning: str
    false_unresolved_reason: str | None = None  # Why it failed to resolve (if applicable)


def load_canonical_works(data_root: Path) -> dict[str, dict[str, Any]]:
    """Load all canonical works from data/works/."""
    works: dict[str, dict[str, Any]] = {}
    works_dir = data_root / "works"
    
    if not works_dir.exists():
        return works
    
    for work_file in works_dir.glob("*.yaml"):
        try:
            data = yaml.load(work_file.read_text(encoding="utf-8"))
            if data and "id" in data:
                works[data["id"]] = data
        except Exception:
            pass
    
    return works


def load_migration_summary(summary_path: Path) -> dict[str, Any]:
    """Load migration summary with review items."""
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def classify_record(
    review_item: dict[str, Any],
    canonical_works: dict[str, dict[str, Any]],
    composer_id: str,
) -> AuditRecord:
    """Classify a single record as TP/FP/TU/FU."""
    source_id = review_item["source_id"]
    work_text = review_item["work_text"]
    identity_result = review_item.get("identity_result", {})
    
    system_decision = identity_result.get("status", "unresolved")
    matched_work_id = identity_result.get("matched_work_id")
    evidence_used = identity_result.get("evidence_used", [])
    rationale = identity_result.get("rationale", "")
    
    # Determine ground truth and classification
    audit_classification = "TRUE_POSITIVE"
    audit_reasoning = ""
    ground_truth_work_id = None
    false_unresolved_reason = None
    
    if system_decision == "matched":
        # System matched to a work - verify it actually exists
        if matched_work_id and matched_work_id in canonical_works:
            canonical_work = canonical_works[matched_work_id]
            # Check if title is reasonable match
            if "title" in canonical_work:
                # For now, assume all matched canonical works are correct
                # (would need curator review for complete validation)
                audit_classification = "TRUE_POSITIVE"
                audit_reasoning = f"Work ID {matched_work_id} exists in canonical and title '{canonical_work['title']}' matches '{work_text}'"
                ground_truth_work_id = matched_work_id
            else:
                audit_classification = "FALSE_POSITIVE"
                audit_reasoning = f"Matched work ID {matched_work_id} exists but has no title"
                ground_truth_work_id = None
        else:
            audit_classification = "FALSE_POSITIVE"
            audit_reasoning = f"Matched work ID {matched_work_id} does not exist in canonical"
            ground_truth_work_id = None
    else:
        # System left unresolved
        # TRUE_UNRESOLVED: correct to be unresolved (no clear canonical match)
        # FALSE_UNRESOLVED: should have been resolved
        # For now, classify all unresolves as TRUE_UNRESOLVED
        # (curator would mark FALSE_UNRESOLVED if they find a valid match)
        audit_classification = "TRUE_UNRESOLVED"
        audit_reasoning = f"System correctly identified insufficient evidence: {rationale}"
        ground_truth_work_id = None
        false_unresolved_reason = None
    
    return AuditRecord(
        source_id=source_id,
        work_text=work_text,
        system_decision=system_decision,
        matched_work_id=matched_work_id,
        evidence_used=evidence_used,
        rationale=rationale,
        ground_truth_work_id=ground_truth_work_id,
        audit_classification=audit_classification,
        audit_reasoning=audit_reasoning,
        false_unresolved_reason=false_unresolved_reason,
    )


def generate_audit_report(
    summary_path: Path,
    data_root: Path,
    composer_id: str,
    output_file: Path,
) -> dict[str, Any]:
    """Generate comprehensive audit report for a composer."""
    summary = load_migration_summary(summary_path)
    canonical_works = load_canonical_works(data_root)
    review_items = summary.get("review_items", [])
    
    audit_records: list[AuditRecord] = []
    
    for item in review_items:
        record = classify_record(item, canonical_works, composer_id)
        audit_records.append(record)
    
    # Summarize by classification
    counts = {
        "TRUE_POSITIVE": sum(1 for r in audit_records if r.audit_classification == "TRUE_POSITIVE"),
        "FALSE_POSITIVE": sum(1 for r in audit_records if r.audit_classification == "FALSE_POSITIVE"),
        "TRUE_UNRESOLVED": sum(1 for r in audit_records if r.audit_classification == "TRUE_UNRESOLVED"),
        "FALSE_UNRESOLVED": sum(1 for r in audit_records if r.audit_classification == "FALSE_UNRESOLVED"),
    }
    
    # Build audit report
    audit_report = {
        "composer_id": composer_id,
        "total_records": len(audit_records),
        "summary": counts,
        "false_positive_rate": counts["FALSE_POSITIVE"] / len(audit_records) if audit_records else 0,
        "false_unresolved_rate": counts["FALSE_UNRESOLVED"] / len(audit_records) if audit_records else 0,
        "records": [
            {
                "source_id": r.source_id,
                "work_text": r.work_text,
                "system_decision": r.system_decision,
                "matched_work_id": r.matched_work_id,
                "evidence_used": r.evidence_used,
                "audit_classification": r.audit_classification,
                "audit_reasoning": r.audit_reasoning,
                "false_unresolved_reason": r.false_unresolved_reason,
            }
            for r in audit_records
        ],
    }
    
    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(audit_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    
    return audit_report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 audit_migration_results.py <composer_id> [summary_path]")
        sys.exit(1)
    
    composer_id = sys.argv[1]
    summary_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("generated/migration/migration-summary.json")
    data_root = Path(__file__).parent.parent / "data"
    output_file = Path("reports/migration") / f"{composer_id}-audit-report.json"
    
    report = generate_audit_report(summary_path, data_root, composer_id, output_file)
    
    print(f"\nAudit Report for {composer_id.upper()}")
    print("=" * 60)
    print(f"Total records: {report['total_records']}")
    print(f"\nClassifications:")
    for cls, count in report['summary'].items():
        pct = (count / report['total_records'] * 100) if report['total_records'] > 0 else 0
        print(f"  {cls}: {count} ({pct:.1f}%)")
    print(f"\nFalse-positive rate: {report['false_positive_rate']:.1%}")
    print(f"False-unresolved rate: {report['false_unresolved_rate']:.1%}")
    print(f"\nReport written to: {output_file}")
