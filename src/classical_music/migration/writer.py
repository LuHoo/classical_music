from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ruamel.yaml import YAML

from .models import PerformanceCandidate, WorkCandidate


def slugify(value: str) -> str:
    cleaned = []
    previous_hyphen = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            previous_hyphen = False
        else:
            if not previous_hyphen:
                cleaned.append("-")
                previous_hyphen = True
    slug = "".join(cleaned).strip("-")
    return slug


def stable_work_ids(composer_slug: str, title: str) -> tuple[str, str]:
    base = slugify(f"{composer_slug}-{title}")
    return f"{base}-group", f"{base}-work"


def stable_performance_id(work_id: str, performer_text: str) -> str:
    return slugify(f"{work_id}-{performer_text}")


def write_canonical_preview(
    output_root: Path,
    works: Iterable[WorkCandidate],
    performances: Iterable[PerformanceCandidate],
    dry_run: bool,
) -> list[Path]:
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.allow_unicode = True

    written: list[Path] = []

    if dry_run:
        return written

    for work in sorted(works, key=lambda item: item.id):
        work_dir = output_root / "works"
        work_dir.mkdir(parents=True, exist_ok=True)
        path = work_dir / f"{work.id}.yaml"
        payload = {
            "id": work.id,
            "work_group_id": work.work_group_id,
            "composer_id": work.composer_id,
            "title": work.title,
        }
        if work.gem:
            payload["gem"] = True
        if work.source_file is not None or work.source_line is not None:
            payload["source"] = {
                "file": work.source_file,
                "line": str(work.source_line) if work.source_line is not None else None,
            }
        with path.open("w", encoding="utf-8") as handle:
            yaml.dump(payload, handle)
        written.append(path)

    for performance in sorted(performances, key=lambda item: item.id):
        perf_dir = output_root / "performances"
        perf_dir.mkdir(parents=True, exist_ok=True)
        path = perf_dir / f"{performance.id}.yaml"
        payload = {
            "id": performance.id,
            "work_id": performance.work_id,
            "performers": [{"name": performance.performer_text, "role": "performer"}],
            "links": {"tidal": {"url": performance.tidal_url}},
        }
        if performance.gramophone_issue:
            payload["reviews"] = {"gramophone": {"issue": performance.gramophone_issue}}
        if performance.source_file is not None or performance.source_line is not None:
            payload["source"] = {
                "file": performance.source_file,
                "line": str(performance.source_line)
                if performance.source_line is not None
                else None,
            }
        with path.open("w", encoding="utf-8") as handle:
            yaml.dump(payload, handle)
        written.append(path)

    return written
