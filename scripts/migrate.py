#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import typer
from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from classical_music.migration.classifier import classify_review_reason  # noqa: E402
from classical_music.migration.models import PerformanceCandidate, WorkCandidate  # noqa: E402
from classical_music.migration.parser import parse_composer_markdown  # noqa: E402
from classical_music.migration.writer import (  # noqa: E402
    stable_performance_id,
    stable_work_ids,
    write_canonical_preview,
)


app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    composer: list[str] = typer.Option([], "--composer", help="Composer slug from docs/<slug>.md"),
    all_files: bool = typer.Option(False, "--all", help="Process all composer files in docs/"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Parse and classify without writing output files."),
) -> None:
    if not all_files and not composer:
        raise typer.BadParameter("Use --all or provide at least one --composer value.")

    docs_root = ROOT / "docs"
    selected_files: list[Path]
    if all_files:
        selected_files = sorted(path for path in docs_root.glob("*.md") if path.name != "index.md")
    else:
        selected_files = sorted(docs_root / f"{name}.md" for name in composer)

    works: dict[str, WorkCandidate] = {}
    performances: dict[str, PerformanceCandidate] = {}
    review_items = []

    for source_path in selected_files:
        if not source_path.exists():
            console.print(f"Skipping missing source file: {source_path}")
            continue

        composer_slug = source_path.stem
        records = parse_composer_markdown(source_path)

        for record in records:
            work_group_id, work_id = stable_work_ids(composer_slug, record.work_text)
            if work_id not in works:
                works[work_id] = WorkCandidate(
                    id=work_id,
                    work_group_id=work_group_id,
                    composer_id=composer_slug,
                    title=record.work_text,
                    gem=record.gem_marker,
                    source_file=record.location.source_file,
                    source_line=record.location.line_number,
                )
            elif record.gem_marker:
                works[work_id].gem = True

            if record.performer_text and record.tidal_links:
                perf_id = stable_performance_id(work_id, record.performer_text)
                if perf_id not in performances:
                    performances[perf_id] = PerformanceCandidate(
                        id=perf_id,
                        work_id=work_id,
                        performer_text=record.performer_text,
                        tidal_url=record.tidal_links[0],
                        gramophone_issue=record.gramophone_issue,
                        source_file=record.location.source_file,
                        source_line=record.location.line_number,
                    )

            classifications = classify_review_reason(record)
            review_items.append(
                {
                    "source_id": record.source_id,
                    "source_file": record.location.source_file,
                    "source_line": record.location.line_number,
                    "work_text": record.work_text,
                    "classifications": [
                        {
                            "reason": entry.reason.value,
                            "confidence": entry.confidence,
                            "notes": entry.notes,
                        }
                        for entry in classifications
                    ],
                }
            )

    output_root = ROOT / "generated" / "migration" / "canonical-preview"
    written_paths = write_canonical_preview(
        output_root=output_root,
        works=works.values(),
        performances=performances.values(),
        dry_run=dry_run,
    )

    summary_path = ROOT / "generated" / "migration" / "migration-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "dry_run": dry_run,
        "works": [asdict(item) for item in sorted(works.values(), key=lambda x: x.id)],
        "performances": [
            asdict(item) for item in sorted(performances.values(), key=lambda x: x.id)
        ],
        "review_items": review_items,
        "written_files": [str(path.relative_to(ROOT)) for path in written_paths],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    console.print(f"Works candidates: {len(works)}")
    console.print(f"Performance candidates: {len(performances)}")
    console.print(f"Review items: {len(review_items)}")
    console.print(f"Summary: {summary_path}")
    if dry_run:
        console.print("Dry run: no canonical preview files were written.")
    else:
        console.print(f"Wrote {len(written_paths)} preview canonical YAML files.")


if __name__ == "__main__":
    app()
