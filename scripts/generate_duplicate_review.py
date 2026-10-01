#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import re
import argparse

from ruamel.yaml import YAML


yaml = YAML(typ="safe")


def load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        loaded = yaml.load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return loaded if isinstance(loaded, dict) else None


def compact_catalogue(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    parts = []
    for key in sorted(value.keys()):
        v = value[key]
        if isinstance(v, str) and v.strip():
            parts.append(f"{key}:{v.strip()}")
    return ", ".join(parts)


def normalize_id_for_duplicate_check(entity_id: str) -> str:
    # Remove numeric duplicate suffixes like -2-group or -3-work for grouping/keeper logic.
    normalized = re.sub(r"-\d+-(group|work)$", r"-\1", entity_id)
    return normalized


def choose_keeper(items: list[dict[str, Any]]) -> str:
    # Prefer non-numbered canonical id if present, otherwise shortest stable id.
    non_numbered = [item["id"] for item in items if normalize_id_for_duplicate_check(item["id"]) == item["id"]]
    if non_numbered:
        return sorted(non_numbered, key=lambda v: (len(v), v))[0]
    return sorted((item["id"] for item in items), key=lambda v: (len(v), v))[0]


def build_work_group_clusters(
    root: Path, activated_ids: set[str] | None = None
) -> list[dict[str, Any]]:
    activated_ids = activated_ids or set()
    groups: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for file_path in sorted((root / "data" / "work-groups").glob("*.yaml")):
        data = load_yaml(file_path)
        if not data:
            continue

        composer = str(data.get("composer_id") or "").strip().lower()
        title_norm = str(data.get("title") or "").strip().lower()
        if not composer or not title_norm:
            continue

        source = data.get("source") if isinstance(data.get("source"), dict) else {}
        groups[(composer, title_norm)].append(
            {
                "id": str(data.get("id") or ""),
                "file": file_path.as_posix(),
                "title": str(data.get("title") or ""),
                "catalogue": compact_catalogue(data.get("catalogue")),
                "source_line": str(source.get("line") or ""),
                "source_file": str(source.get("file") or ""),
            }
        )

    clusters: list[dict[str, Any]] = []
    for (composer, title_norm), items in sorted(groups.items()):
        if len(items) < 2:
            continue

        catalogues = {item["catalogue"] for item in items if item["catalogue"]}

        # Auto-merge when all non-source semantics match.
        semantic_fingerprint = {
            (item["title"].strip().lower(), item["catalogue"].strip().lower())
            for item in items
        }
        can_auto_merge = len(semantic_fingerprint) == 1 and len(catalogues) <= 1
        keeper = choose_keeper(items)

        status = (
            "action_required"
            if any(item["id"] in activated_ids for item in items)
            else "background_suspicion"
        )
        clusters.append(
            {
                "composer": composer,
                "title_norm": title_norm,
                "items": items,
                "auto_recommendation": "auto-merge" if can_auto_merge else "manual-review",
                "status": "auto_resolved" if can_auto_merge else status,
                "review_required": status == "action_required",
                "suggested_keeper": keeper,
            }
        )

    return clusters


def build_work_clusters(
    root: Path, activated_ids: set[str] | None = None
) -> list[dict[str, Any]]:
    activated_ids = activated_ids or set()
    groups: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for file_path in sorted((root / "data" / "works").rglob("*.yaml")):
        data = load_yaml(file_path)
        if not data:
            continue

        composer = str(data.get("composer_id") or "").strip().lower()
        title_norm = str(data.get("title") or "").strip().lower()
        if not composer or not title_norm:
            continue

        source = data.get("source") if isinstance(data.get("source"), dict) else {}
        groups[(composer, title_norm)].append(
            {
                "id": str(data.get("id") or ""),
                "file": file_path.as_posix(),
                "title": str(data.get("title") or ""),
                "work_group_id": str(data.get("work_group_id") or ""),
                "catalogue": compact_catalogue(data.get("catalogue")),
                "date_text": str(data.get("date_text") or ""),
                "source_line": str(source.get("line") or ""),
            }
        )

    clusters: list[dict[str, Any]] = []
    for (composer, title_norm), items in sorted(groups.items()):
        if len(items) < 2:
            continue

        group_ids = {item["work_group_id"] for item in items if item["work_group_id"]}
        catalogues = {item["catalogue"] for item in items if item["catalogue"]}

        # If work_group_id differs but catalogues are the same, these are often version rows
        # that should be kept as separate Works while merging Work Groups.
        if len(group_ids) > 1 and len(catalogues) <= 1:
            recommendation = "keep-work-review-group-merge"
        elif len(group_ids) == 1 and len(catalogues) <= 1:
            recommendation = "auto-merge"
        else:
            recommendation = "manual-review"

        keeper = choose_keeper(items)

        status = (
            "action_required"
            if any(item["id"] in activated_ids for item in items)
            else "background_suspicion"
        )
        clusters.append(
            {
                "composer": composer,
                "title_norm": title_norm,
                "items": items,
                "auto_recommendation": recommendation,
                "status": "auto_resolved" if recommendation == "auto-merge" else status,
                "review_required": status == "action_required",
                "suggested_keeper": keeper,
            }
        )

    return clusters


def write_report(
    root: Path, output_path: Path, activated_ids: set[str] | None = None
) -> None:
    wg_clusters = build_work_group_clusters(root, activated_ids)
    w_clusters = build_work_clusters(root, activated_ids)

    lines: list[str] = []
    lines.append("# Duplicate Review List (2026-08-23)")
    lines.append("")
    lines.append("This report groups all potential duplicates with counterpart records.")
    lines.append("Automatic recommendation uses distinctive metadata, not numeric ID suffixes.")
    lines.append("")
    lines.append("Action Required sections contain only explicitly activated identity gates.")
    lines.append("Background Suspicion sections are deferred and do not require curator action.")
    lines.append("Automatically Resolved sections document safe machine classifications.")
    lines.append("")

    auto_wg = [cluster for cluster in wg_clusters if cluster["status"] == "auto_resolved"]
    manual_wg = [cluster for cluster in wg_clusters if cluster["review_required"]]
    background_wg = [cluster for cluster in wg_clusters if cluster["status"] == "background_suspicion"]

    lines.append("## DUP-002 Work Group Duplicates")
    lines.append("")
    lines.append(f"Clusters: {len(wg_clusters)}")
    lines.append(f"Auto-merge clusters: {len(auto_wg)}")
    lines.append(f"Action required clusters: {len(manual_wg)}")
    lines.append(f"Background suspicion clusters: {len(background_wg)}")
    lines.append(f"Automatically resolved clusters: {len(auto_wg)}")
    lines.append("")

    lines.append("### Automatically Resolved")
    lines.append("")
    for index, cluster in enumerate(auto_wg, start=1):
        lines.append(
            f"{index}. duplicate key: composer={cluster['composer']} | title={cluster['title_norm']}"
        )
        lines.append(f"   auto_recommendation: {cluster['auto_recommendation']}")
        lines.append(f"   suggested_keeper: {cluster['suggested_keeper']}")
        lines.append("   counterparts:")
        for item_idx, item in enumerate(cluster["items"], start=1):
            file_rel = Path(item["file"]).relative_to(root).as_posix()
            lines.append(f"   - [{item_idx}] entity_id: {item['id']}")
            lines.append(f"     file: {file_rel}")
            lines.append(f"     title: {item['title']}")
            lines.append(f"     catalogue: {item['catalogue']}")
            lines.append(f"     source_line: {item['source_line']}")
        lines.append("   action: auto-merge")
        lines.append("")

    lines.append("### Action Required")
    lines.append("")
    for index, cluster in enumerate(manual_wg, start=1):
        lines.append(
            f"{index}. duplicate key: composer={cluster['composer']} | title={cluster['title_norm']}"
        )
        lines.append(f"   auto_recommendation: {cluster['auto_recommendation']}")
        lines.append(f"   suggested_keeper: {cluster['suggested_keeper']}")
        lines.append("   counterparts:")
        for item_idx, item in enumerate(cluster["items"], start=1):
            file_rel = Path(item["file"]).relative_to(root).as_posix()
            lines.append(f"   - [{item_idx}] entity_id: {item['id']}")
            lines.append(f"     file: {file_rel}")
            lines.append(f"     title: {item['title']}")
            lines.append(f"     catalogue: {item['catalogue']}")
            lines.append(f"     source_line: {item['source_line']}")
        lines.append("   verdict: [merge|keep]")
        lines.append("   keeper_if_merge: [entity_id]")
        lines.append("   rationale:")
        lines.append("")

    lines.append("### Background Suspicion")
    lines.append("")
    for index, cluster in enumerate(background_wg, start=1):
        ids = ", ".join(item["id"] for item in cluster["items"])
        lines.append(
            f"{index}. composer={cluster['composer']} | title={cluster['title_norm']} | "
            f"entities={ids}"
        )
    lines.append("")

    auto_w = [cluster for cluster in w_clusters if cluster["status"] == "auto_resolved"]
    manual_w = [cluster for cluster in w_clusters if cluster["review_required"]]
    background_w = [cluster for cluster in w_clusters if cluster["status"] == "background_suspicion"]

    lines.append("## DUP-003 Work Duplicates")
    lines.append("")
    lines.append(f"Clusters: {len(w_clusters)}")
    lines.append(f"Auto-merge clusters: {len(auto_w)}")
    lines.append(f"Action required clusters: {len(manual_w)}")
    lines.append(f"Background suspicion clusters: {len(background_w)}")
    lines.append(f"Automatically resolved clusters: {len(auto_w)}")
    lines.append("")

    lines.append("### Automatically Resolved")
    lines.append("")
    for index, cluster in enumerate(auto_w, start=1):
        lines.append(
            f"{index}. duplicate key: composer={cluster['composer']} | title={cluster['title_norm']}"
        )
        lines.append(f"   auto_recommendation: {cluster['auto_recommendation']}")
        lines.append(f"   suggested_keeper: {cluster['suggested_keeper']}")
        lines.append("   counterparts:")
        for item_idx, item in enumerate(cluster["items"], start=1):
            file_rel = Path(item["file"]).relative_to(root).as_posix()
            lines.append(f"   - [{item_idx}] entity_id: {item['id']}")
            lines.append(f"     file: {file_rel}")
            lines.append(f"     title: {item['title']}")
            lines.append(f"     work_group_id: {item['work_group_id']}")
            lines.append(f"     catalogue: {item['catalogue']}")
            lines.append(f"     date_text: {item['date_text']}")
            lines.append(f"     source_line: {item['source_line']}")
        lines.append("   action: auto-merge")
        lines.append("")

    lines.append("### Action Required")
    lines.append("")
    for index, cluster in enumerate(manual_w, start=1):
        lines.append(
            f"{index}. duplicate key: composer={cluster['composer']} | title={cluster['title_norm']}"
        )
        lines.append(f"   auto_recommendation: {cluster['auto_recommendation']}")
        lines.append(f"   suggested_keeper: {cluster['suggested_keeper']}")
        lines.append("   counterparts:")
        for item_idx, item in enumerate(cluster["items"], start=1):
            file_rel = Path(item["file"]).relative_to(root).as_posix()
            lines.append(f"   - [{item_idx}] entity_id: {item['id']}")
            lines.append(f"     file: {file_rel}")
            lines.append(f"     title: {item['title']}")
            lines.append(f"     work_group_id: {item['work_group_id']}")
            lines.append(f"     catalogue: {item['catalogue']}")
            lines.append(f"     date_text: {item['date_text']}")
            lines.append(f"     source_line: {item['source_line']}")
        lines.append("   verdict: [merge|keep]")
        lines.append("   keeper_if_merge: [entity_id]")
        lines.append("   rationale:")
        lines.append("")

    lines.append("### Background Suspicion")
    lines.append("")
    for index, cluster in enumerate(background_w, start=1):
        ids = ", ".join(item["id"] for item in cluster["items"])
        lines.append(
            f"{index}. composer={cluster['composer']} | title={cluster['title_norm']} | "
            f"entities={ids}"
        )
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--identity-gate-id",
        action="append",
        default=[],
        help="Activate identity review for a specific changed entity ID.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / "reports" / "validation" / "duplicate-review-2026-08-23.md"
    write_report(root, output, set(args.identity_gate_id))
    print(output)


if __name__ == "__main__":
    main()
