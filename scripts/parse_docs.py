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

from classical_music.migration.parser import parse_composer_markdown  # noqa: E402


app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(composer: list[str] = typer.Option([], "--composer"), all_files: bool = typer.Option(False, "--all")) -> None:
    docs_root = ROOT / "docs"
    if not all_files and not composer:
        raise typer.BadParameter("Use --all or provide at least one --composer value.")

    file_paths: list[Path]
    if all_files:
        file_paths = sorted(path for path in docs_root.glob("*.md") if path.name != "index.md")
    else:
        file_paths = sorted(docs_root / f"{name}.md" for name in composer)

    records = []
    for path in file_paths:
        if not path.exists():
            console.print(f"Skipping missing file: {path}")
            continue
        records.extend(parse_composer_markdown(path))

    payload = [asdict(record) for record in records]
    output_path = ROOT / "generated" / "migration" / "source-records.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    console.print(f"Parsed {len(records)} source records.")
    console.print(f"Wrote {output_path}")


if __name__ == "__main__":
    app()
