#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from classical_music.validation import DataValidator  # noqa: E402


app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(json_output: bool = typer.Option(False, "--json", help="Emit JSON report.")) -> None:
    validator = DataValidator(repository_root=ROOT)
    report = validator.run()

    if json_output:
        payload = {
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "info_count": report.info_count,
            "findings": [finding.model_dump() for finding in report.findings],
        }
        print(json.dumps(payload, indent=2))
    else:
        table = Table(title="Canonical Data Validation")
        table.add_column("Severity", no_wrap=True)
        table.add_column("Rule")
        table.add_column("File")
        table.add_column("Message")

        for finding in report.findings:
            table.add_row(
                finding.severity,
                finding.rule_id,
                finding.file,
                finding.message,
            )

        console.print(table)
        console.print(
            f"Errors: {report.error_count} | Warnings: {report.warning_count} | Info: {report.info_count}"
        )

    raise typer.Exit(code=1 if report.has_errors else 0)


if __name__ == "__main__":
    app()
