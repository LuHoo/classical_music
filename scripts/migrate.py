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

from classical_music.migration.entity_matcher import EntityMatcher  # noqa: E402
from classical_music.migration.models import PerformanceCandidate, WorkCandidate  # noqa: E402
from classical_music.migration.parser import parse_composer_markdown  # noqa: E402
from classical_music.migration.review_categorizer import (  # noqa: E402
    categorize_review_items,
    review_summary,
)
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
    review_items = []  # Will contain items with identity_result (not classifications)
    matched_entities: dict[str, str] = {}  # source_id → canonical_entity_id

    # Load existing canonical entities for matching
    entity_matcher = EntityMatcher(ROOT / "data")
    matcher_summary = entity_matcher.matches_summary()
    console.print(f"Loaded {matcher_summary['works']} canonical works for matching")

    for source_path in selected_files:
        if not source_path.exists():
            console.print(f"Skipping missing source file: {source_path}")
            continue

        composer_slug = source_path.stem
        records = parse_composer_markdown(source_path)

        for record in records:
            work_group_id, work_id = stable_work_ids(composer_slug, record.work_text)
            
            # Resolve doc slug to canonical composer_id (fails closed - no fallback)
            canonical_composer_id = entity_matcher.resolve_composer_id(composer_slug)
            if not canonical_composer_id:
                # Composer not found in canonical data
                # This is treated as BACKGROUND_ONLY/UNRESOLVED for identity
                console.print(f"[yellow]Warning: Unknown composer slug '{composer_slug}' in {source_path.name}[/yellow]")
                canonical_composer_id = None
            
            # Two-stage entity matching: candidate discovery + identity resolution
            candidates = (
                entity_matcher.find_work_candidates(canonical_composer_id, record.work_text)
                if canonical_composer_id
                else []
            )
            
            # Resolve work identity using candidates and version evidence
            identity_result = entity_matcher.resolve_work_identity(
                record.work_text, canonical_composer_id, candidates
            )
            
            # Use identity result to determine work_id and matched status
            if identity_result.matched_work_id:
                matched_entities[record.source_id] = identity_result.matched_work_id
                work_id = identity_result.matched_work_id
            
            # Create work candidate (even if unresolved, for curator review)
            if work_id not in works:
                works[work_id] = WorkCandidate(
                    id=work_id,
                    work_group_id=work_group_id,
                    composer_id=canonical_composer_id or composer_slug,  # Use slug if canonical not found
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

            # Add review item with identity resolution result
            review_items.append(
                {
                    "source_id": record.source_id,
                    "source_file": record.location.source_file,
                    "source_line": record.location.line_number,
                    "work_text": record.work_text,
                    "identity_result": identity_result,  # WorkIdentityResult object
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
    
    # Categorize review items for better curator summaries
    # (review_items already have WorkIdentityResult objects)
    categorized_items = categorize_review_items(review_items)
    review_stats = review_summary(categorized_items)
    
    # Convert identity results to JSON-serializable dicts for summary
    review_items_for_json = []
    for item in review_items:
        identity_result = item["identity_result"]
        review_items_for_json.append({
            "source_id": item["source_id"],
            "source_file": item["source_file"],
            "source_line": item["source_line"],
            "work_text": item["work_text"],
            "identity_result": {
                "status": identity_result.status.value,
                "matched_work_id": identity_result.matched_work_id,
                "candidates_count": identity_result.candidates_count,
                "evidence_used": identity_result.evidence_used,
                "rationale": identity_result.rationale,
                "requires_curator_action": identity_result.requires_curator_action,
            }
        })
    
    summary = {
        "dry_run": dry_run,
        "works": [asdict(item) for item in sorted(works.values(), key=lambda x: x.id)],
        "performances": [
            asdict(item) for item in sorted(performances.values(), key=lambda x: x.id)
        ],
        "review_items": review_items_for_json,
        "review_summary": review_stats,
        "matched_entities": matched_entities,
        "written_files": [str(path.relative_to(ROOT)) for path in written_paths],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    console.print(f"Works candidates: {len(works)}")
    console.print(f"Performance candidates: {len(performances)}")
    console.print(f"Matched to existing: {len(matched_entities)}")
    console.print(f"Review summary: {review_stats['by_category']}")
    console.print(f"Consequential items (curator action): {review_stats['consequential_count']}")
    console.print(f"Summary: {summary_path}")
    if dry_run:
        console.print("Dry run: no canonical preview files were written.")
    else:
        console.print(f"Wrote {len(written_paths)} preview canonical YAML files.")


if __name__ == "__main__":
    app()
