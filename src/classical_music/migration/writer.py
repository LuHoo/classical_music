from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Iterable

from ruamel.yaml import YAML

from .models import PerformanceCandidate, WorkCandidate, WorkGroupCandidate


def slugify(value: str) -> str:
    value = (
        value.replace("♭", " flat ")
        .replace("♯", " sharp ")
        .replace("ß", "ss")
        .replace("–", "-")
        .replace("—", "-")
    )
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
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


def stable_work_ids_with_catalogue(
    composer_slug: str, title: str, catalogue: str | None
) -> tuple[str, str]:
    identity_text = f"{title} {catalogue}" if catalogue else title
    return stable_work_ids(composer_slug, identity_text)


def stable_performance_id(work_id: str, performer_text: str) -> str:
    return slugify(f"{work_id}-{performer_text}")


def is_brahms_curated_conductor_context(name: str) -> bool:
    lowered = name.casefold()
    return any(
        token in lowered
        for token in (
            "choir",
            "chorus",
            "orchestra",
            "orchestre",
            "philharmoniker",
            "sinfonieorchester",
            "symphoniker",
        )
    )


def performer_entries_from_text(performer_text: str) -> list[dict[str, str]]:
    names = [part.strip() for part in performer_text.split(",") if part.strip()]
    entries = []
    has_conducted_collective_before_last = any(
        is_brahms_curated_conductor_context(name) for name in names[:-1]
    )
    for index, name in enumerate(names):
        role = "performer"
        if index == len(names) - 1 and has_conducted_collective_before_last:
            role = "conductor"
        entries.append(
            {
                "artist_id": slugify(name),
                "name": name,
                "role": role,
            }
        )
    return entries


def write_canonical_preview(
    output_root: Path,
    work_groups: Iterable[WorkGroupCandidate],
    works: Iterable[WorkCandidate],
    performances: Iterable[PerformanceCandidate],
    dry_run: bool,
) -> list[Path]:
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    yaml.width = 4096

    written: list[Path] = []

    if dry_run:
        return written

    for group in sorted(work_groups, key=lambda item: item.id):
        group_dir = output_root / "work-groups"
        group_dir.mkdir(parents=True, exist_ok=True)
        path = group_dir / f"{group.id}.yaml"
        payload = {
            "id": group.id,
            "composer_id": group.composer_id,
            "title": group.title,
        }
        if group.catalogue:
            payload["catalogue"] = group.catalogue
        if group.source_file is not None or group.source_line is not None:
            payload["source"] = {
                "file": group.source_file,
                "line": str(group.source_line) if group.source_line is not None else None,
            }
        with path.open("w", encoding="utf-8") as handle:
            yaml.dump(payload, handle)
        written.append(path)

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
        if work.catalogue:
            payload["catalogue"] = work.catalogue
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
            "performers": performer_entries_from_text(performance.performer_text),
            "source_performer_text": performance.performer_text,
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
