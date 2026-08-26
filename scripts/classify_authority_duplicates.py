#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from classical_music.authority import (  # noqa: E402
    AuthorityCandidate,
    CatalogueIdentifier,
    DuplicateCluster,
    WorkIdentity,
    classify_duplicate_cluster,
)


yaml = YAML(typ="safe")


def load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        loaded = yaml.load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return loaded if isinstance(loaded, dict) else None


def catalogue_identifiers(data: dict[str, Any]) -> tuple[CatalogueIdentifier, ...]:
    raw = data.get("catalogue")
    if not isinstance(raw, dict):
        return ()
    return tuple(
        CatalogueIdentifier(str(key), str(value))
        for key, value in sorted(raw.items())
        if isinstance(value, str) and value.strip()
    )


def authority_candidates(data: dict[str, Any]) -> tuple[AuthorityCandidate, ...]:
    candidates: list[AuthorityCandidate] = []
    external_ids = data.get("external_ids")
    if isinstance(external_ids, dict):
        mbid = external_ids.get("musicbrainz") or external_ids.get("musicbrainz_work_id")
        if mbid:
            candidates.append(AuthorityCandidate("musicbrainz", str(mbid)))
    musicbrainz = data.get("musicbrainz_work_id")
    if musicbrainz:
        candidates.append(AuthorityCandidate("musicbrainz", str(musicbrainz)))
    return tuple(candidates)


def relationship_types(data: dict[str, Any]) -> tuple[str, ...]:
    raw = data.get("relationships")
    if not isinstance(raw, list):
        return ()
    return tuple(str(item.get("type")) for item in raw if isinstance(item, dict) and item.get("type"))


def to_work_identity(path: Path, data: dict[str, Any]) -> WorkIdentity:
    return WorkIdentity(
        work_id=str(data.get("id") or path.stem),
        composer_id=str(data.get("composer_id") or ""),
        title=str(data.get("title") or ""),
        work_group_id=str(data.get("work_group_id") or data.get("id") or ""),
        catalogues=catalogue_identifiers(data),
        authority_candidates=authority_candidates(data),
        relationship_types=relationship_types(data),
    )


def load_entities(directory: Path) -> list[tuple[Path, WorkIdentity]]:
    entities = []
    for path in sorted(directory.glob("*.yaml")):
        data = load_yaml(path)
        if not data:
            continue
        identity = to_work_identity(path, data)
        if identity.composer_id and identity.title:
            entities.append((path, identity))
    return entities


def group_duplicate_candidates(
    entities: list[tuple[Path, WorkIdentity]],
    rule_id: str,
    activated_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    activated_ids = activated_ids or set()
    grouped: dict[tuple[str, str], list[tuple[Path, WorkIdentity]]] = {}
    for path, identity in entities:
        grouped.setdefault((identity.composer_id, identity.normalized_title), []).append((path, identity))

    results = []
    for (composer_id, normalized_title), items in sorted(grouped.items()):
        if len(items) < 2:
            continue
        cluster = DuplicateCluster(rule_id, tuple(identity for _, identity in items))  # type: ignore[arg-type]
        evidence = classify_duplicate_cluster(cluster)
        status = (
            "auto_resolved"
            if not evidence.curator_review_required
            else (
                "action_required"
                if any(identity.work_id in activated_ids for _, identity in items)
                else "background_suspicion"
            )
        )
        results.append(
            {
                "rule_id": rule_id,
                "composer_id": composer_id,
                "normalized_title": normalized_title,
                "classification": evidence.classification,
                "confidence": evidence.confidence,
                "curator_review_required": evidence.curator_review_required,
                "evidence": list(evidence.evidence),
                "authority_ids": list(evidence.authority_ids),
                "proposed_action": evidence.proposed_action,
                "status": status,
                "items": [
                    {
                        "id": identity.work_id,
                        "file": path.relative_to(ROOT).as_posix(),
                        "title": identity.title,
                        "work_group_id": identity.work_group_id,
                        "catalogues": sorted(identity.normalized_catalogues),
                        "musicbrainz_ids": sorted(identity.musicbrainz_ids),
                        "relationship_types": list(identity.relationship_types),
                    }
                    for path, identity in items
                ],
            }
        )
    return results


def render_markdown(results: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    lines = [
        "# Authority-Aware Duplicate Classification",
        "",
        "This report classifies duplicate-looking records using local catalogue metadata and existing authority identifiers.",
        "It does not merge, delete, renumber, or reassign canonical data.",
        "Unactivated unresolved clusters are background suspicions and do not require curator action.",
        "",
        "## Summary",
        "",
    ]
    for status in ["action_required", "background_suspicion", "auto_resolved"]:
        lines.append(f"- {status}: {counts.get(status, 0)}")

    lines.extend(["", "## Clusters", ""])
    for result in results:
        lines.append(f"### {result['rule_id']} | {result['composer_id']} | {result['normalized_title']}")
        lines.append("")
        lines.append(f"- classification: `{result['classification']}`")
        lines.append(f"- status: `{result['status']}`")
        lines.append(f"- confidence: `{result['confidence']}`")
        lines.append(f"- curator_review_required: `{str(result['curator_review_required']).lower()}`")
        lines.append(f"- proposed_action: `{result['proposed_action']}`")
        if result["authority_ids"]:
            lines.append(f"- authority_ids: {', '.join(f'`{value}`' for value in result['authority_ids'])}")
        for evidence in result["evidence"]:
            lines.append(f"- evidence: {evidence}")
        lines.append("")
        lines.append("| ID | File | Catalogues | MusicBrainz IDs |")
        lines.append("| --- | --- | --- | --- |")
        for item in result["items"]:
            catalogues = ", ".join(f"`{value}`" for value in item["catalogues"]) or ""
            mbids = ", ".join(f"`{value}`" for value in item["musicbrainz_ids"]) or ""
            lines.append(f"| `{item['id']}` | `{item['file']}` | {catalogues} | {mbids} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify duplicate-looking records using authority-aware evidence")
    parser.add_argument("--json-output", type=Path, default=ROOT / "reports/verification/authority-duplicate-classification.json")
    parser.add_argument("--markdown-output", type=Path, default=ROOT / "reports/verification/authority-duplicate-classification.md")
    parser.add_argument("--identity-gate-id", action="append", default=[])
    args = parser.parse_args()

    results = []
    activated_ids = set(args.identity_gate_id)
    results.extend(group_duplicate_candidates(load_entities(ROOT / "data/work-groups"), "DUP-002", activated_ids))
    results.extend(group_duplicate_candidates(load_entities(ROOT / "data/works"), "DUP-003", activated_ids))

    payload = {
        "run_context": {
            "authority_mode": "local_catalogue_and_existing_ids",
            "non_destructive": True,
            "live_network_required": False,
        },
        "clusters": results,
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(results) + "\n", encoding="utf-8")

    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
