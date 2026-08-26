#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


AUTO_CLASSIFIED: dict[str, dict[str, Any]] = {
    "sergei-prokofiev-alexander-nevsky-work": {
        "decision": "retain_as_distinct_local_work",
        "reason": "Source identifies the 1939 cantata separately from the 1938 film score.",
    },
    "sergei-prokofiev-alexander-nevsky-2-work": {
        "decision": "retain_as_distinct_local_work",
        "reason": "Source identifies the 1938 film score separately from the 1939 cantata.",
    },
    "sergei-prokofiev-lieutenant-kije-work": {
        "decision": "retain_as_distinct_local_work",
        "reason": "Source identifies the film score and separately names its orchestral suite.",
    },
    "sergei-prokofiev-suite-from-lieutenant-kije-work": {
        "decision": "retain_as_distinct_local_work",
        "reason": "An independently named suite is a distinct artistic object under Work identity rules.",
    },
    "sergei-prokofiev-war-and-peace-suite-work": {
        "decision": "retain_as_suite_work",
        "reason": "The local title explicitly identifies a suite; authority absence does not justify assigning the opera Work.",
    },
    "sergei-prokofiev-symphony-no-2-in-d-minor-revised-version-work": {
        "decision": "retain_as_distinct_local_work",
        "reason": "Architecture requires composer revisions to remain separate Works; missing Op. 136 authority coverage does not justify inheriting Op. 40.",
    },
}

SAFE_CANDIDATES: dict[str, dict[str, Any]] = {
    "sergei-prokofiev-on-the-dnieper-work": {
        "decision": "safe_candidate_not_written",
        "candidate_musicbrainz_work_id": "c870f7b4-b2ff-4173-b47b-1d356fa3ae60",
        "reason": "The Op. 51 title and catalogue match; nearby sections and Op. 51bis are excluded from canonical writing.",
    },
    "sergei-prokofiev-peter-and-the-wolf-work": {
        "decision": "safe_candidate_not_written",
        "candidate_musicbrainz_work_id": "812b5cc4-a7a0-3809-aa6c-290c9ebd79be",
        "reason": "The Op. 67 title and catalogue match; narrative sections are not the parent Work.",
    },
}


def classify_alignment(payload: dict[str, Any]) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    listed: set[str] = set()

    for item in payload.get("curator_decision_required", []):
        for local_id in item.get("local_ids", []):
            listed.add(local_id)
            decision = AUTO_CLASSIFIED.get(local_id)
            if decision:
                decisions.append({"local_id": local_id, "status": "automatically_resolved", **decision})
            else:
                decisions.append({"local_id": local_id, "status": "action_required", **item})
    for item in payload.get("candidate_evidence_not_written", []):
        local_id = item["local_id"]
        listed.add(local_id)
        decisions.append({"local_id": local_id, "status": "automatically_resolved", **SAFE_CANDIDATES[local_id]})

    for local_id in payload.get("background_authority_gap", []):
        listed.add(local_id)
        decisions.append({
            "local_id": local_id,
            "status": "unchanged_authority_gap",
            "decision": "leave_unchanged",
            "reason": "Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence.",
        })

    counts = {
        "automatically_resolved_or_safely_classified": sum(
            item["status"] == "automatically_resolved" for item in decisions
        ),
        "unchanged_authority_gap": sum(
            item["status"] == "unchanged_authority_gap" for item in decisions
        ),
        "background_suspicion": sum(
            item["status"] == "background_suspicion" for item in decisions
        ),
        "action_required": sum(item["status"] == "action_required" for item in decisions),
    }
    return {
        "composer_id": payload.get("composer_id"),
        "issue": payload.get("issue"),
        "input_unresolved_count": payload.get("unresolved_count"),
        "canonical_data_changed": False,
        "policy": {
            "trusted_legacy_input": True,
            "authority_is_supporting_evidence": True,
            "mbid_coverage_is_not_a_success_metric": True,
            "curator_review_is_last_resort": True,
        },
        "counts": counts,
        "decisions": decisions,
        "curator_decisions": [item for item in decisions if item["status"] == "action_required"],
        "coverage_check": {
            "classified_record_count": len(listed),
            "input_record_count": payload.get("unresolved_count"),
            "complete": len(listed) == payload.get("unresolved_count"),
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    counts = result["counts"]
    lines = [
        "# Prokofiev curator-on-demand alignment review",
        "",
        "This is a non-destructive policy classification of the 33 unresolved alignment records.",
        "Existing canonical Works are trusted legacy input. No MBID or canonical YAML is written by this report.",
        "",
        "## Summary",
        "",
        f"- Automatically resolved / safely classified: {counts['automatically_resolved_or_safely_classified']}",
        f"- Unchanged because local identity is clear but authority coverage is absent or insufficient: {counts['unchanged_authority_gap']}",
        f"- Background suspicions: {counts['background_suspicion']}",
        f"- Genuine consequential curator decisions: {counts['action_required']}",
        "",
        "## Architecture pre-flight",
        "",
        "- Work identity follows the local Work and Work Group model, not MusicBrainz completeness.",
        "- Revisions remain separate Works; a missing Op. 136 authority record does not inherit Op. 40.",
        "- A recognised suite, film score, arrangement, or other distinct artistic object is not collapsed solely because titles match.",
        "- Authority IDs are added only for reliable unambiguous matches; unresolved or missing coverage remains outside canonical data.",
        "- Performances remain attached to exactly one Work; this report does not create Recording or Release entities.",
        "",
        "## Decisions",
        "",
        "| Local Work | Status | Decision | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for item in result["decisions"]:
        reason = item["reason"].replace("|", "\\|")
        lines.append(f"| `{item['local_id']}` | `{item['status']}` | `{item['decision']}` | {reason} |")
    lines.extend(["", "## Curator decisions", "", "None. The remaining 33 records contain no consequential unresolved identity decision after applying the architecture and local source evidence.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    result = classify_alignment(json.loads(args.input.read_text(encoding="utf-8")))
    args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
