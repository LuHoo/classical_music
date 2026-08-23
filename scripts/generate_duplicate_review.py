#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

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


def build_work_group_clusters(root: Path) -> list[dict[str, Any]]:
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
            }
        )

    clusters: list[dict[str, Any]] = []
    for (composer, title_norm), items in sorted(groups.items()):
        if len(items) < 2:
            continue

        catalogues = {item["catalogue"] for item in items if item["catalogue"]}
        merge_candidate = len(catalogues) <= 1

        clusters.append(
            {
                "composer": composer,
                "title_norm": title_norm,
                "items": items,
                "auto_recommendation": "merge-candidate" if merge_candidate else "manual-review",
            }
        )

    return clusters


def build_work_clusters(root: Path) -> list[dict[str, Any]]:
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
            recommendation = "merge-candidate"
        else:
            recommendation = "manual-review"

        clusters.append(
            {
                "composer": composer,
                "title_norm": title_norm,
                "items": items,
                "auto_recommendation": recommendation,
            }
        )

    return clusters


def write_report(root: Path, output_path: Path) -> None:
    wg_clusters = build_work_group_clusters(root)
    w_clusters = build_work_clusters(root)

    lines: list[str] = []
    lines.append("# Duplicate Review List (2026-08-23)")
    lines.append("")
    lines.append("This report groups all potential duplicates with counterpart records.")
    lines.append("Automatic recommendation uses distinctive metadata, not numeric ID suffixes.")
    lines.append("")
    lines.append("Review instruction:")
    lines.append("- Set `verdict` to `merge` or `keep`.")
    lines.append("- If `merge`, set `keeper_if_merge` to the surviving entity_id.")
    lines.append("- Add one-line rationale.")
    lines.append("")

    lines.append("## DUP-002 Work Group Duplicates")
    lines.append("")
    lines.append(f"Clusters: {len(wg_clusters)}")
    lines.append("")

    for index, cluster in enumerate(wg_clusters, start=1):
        lines.append(
            f"{index}. duplicate key: composer={cluster['composer']} | title={cluster['title_norm']}"
        )
        lines.append(f"   auto_recommendation: {cluster['auto_recommendation']}")
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

    lines.append("## DUP-003 Work Duplicates")
    lines.append("")
    lines.append(f"Clusters: {len(w_clusters)}")
    lines.append("")

    for index, cluster in enumerate(w_clusters, start=1):
        lines.append(
            f"{index}. duplicate key: composer={cluster['composer']} | title={cluster['title_norm']}"
        )
        lines.append(f"   auto_recommendation: {cluster['auto_recommendation']}")
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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "reports" / "validation" / "duplicate-review-2026-08-23.md"
    write_report(root, output)
    print(output)


if __name__ == "__main__":
    main()
