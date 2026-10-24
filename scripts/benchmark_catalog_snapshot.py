"""Benchmark catalog loading, publication validation and publication build.

Measurement-only harness for issue #306. It does not change production
behaviour: it temporarily wraps ``ruamel.yaml.YAML.load`` and the catalog
loading entry points to count invocations and accumulate parse time, runs the
requested scenarios, and writes a JSON report.

The harness is used to compare a baseline revision with the shared catalog
snapshot implementation. Run identical commands on both revisions.

Usage:
    python scripts/benchmark_catalog_snapshot.py --runs 3 --output ci-metrics/snapshot-benchmark.json
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import io
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


@dataclass
class Counters:
    """Counters collected for a single measured scenario run."""

    yaml_loads: int = 0
    distinct_yaml_files: int = 0
    catalog_loads: int = 0
    snapshot_loads: int = 0
    parse_seconds: float = 0.0
    wall_seconds: float = 0.0
    cpu_seconds: float = 0.0
    result: dict[str, Any] = field(default_factory=dict)


class Instrumentation:
    """Count YAML parses and catalog loads inside a measured region."""

    def __init__(self) -> None:
        self.yaml_loads = 0
        self.files: set[str] = set()
        self.parse_seconds = 0.0
        self.catalog_loads = 0
        self.snapshot_loads = 0
        self._restore: list[tuple[Any, str, Any]] = []

    def _wrap(self, owner: Any, name: str, make: Callable[[Any], Any]) -> None:
        original = getattr(owner, name)
        self._restore.append((owner, name, original))
        setattr(owner, name, make(original))

    def __enter__(self) -> "Instrumentation":
        from ruamel.yaml import YAML

        from classical_music.publication_adapter import PublicationDataAdapter

        def make_load(original: Any) -> Any:
            @functools.wraps(original)
            def counted(yaml_self: Any, stream: Any, *args: Any, **kwargs: Any) -> Any:
                self.yaml_loads += 1
                name = getattr(stream, "name", None)
                if name:
                    self.files.add(str(name))
                elif isinstance(stream, (str, Path)):
                    self.files.add(str(stream))
                started = time.perf_counter()
                try:
                    return original(yaml_self, stream, *args, **kwargs)
                finally:
                    self.parse_seconds += time.perf_counter() - started

            return counted

        def make_catalog_load(original: Any) -> Any:
            @functools.wraps(original)
            def counted(*args: Any, **kwargs: Any) -> Any:
                self.catalog_loads += 1
                return original(*args, **kwargs)

            return counted

        self._wrap(YAML, "load", make_load)
        self._wrap(PublicationDataAdapter, "load_canonical_data", make_catalog_load)

        try:
            from classical_music.catalog_snapshot import CatalogSnapshot
        except ImportError:
            # Baseline revision has no shared snapshot.
            pass
        else:

            def make_snapshot_load(original: Any) -> Any:
                @functools.wraps(original)
                def counted(*args: Any, **kwargs: Any) -> Any:
                    self.snapshot_loads += 1
                    return original(*args, **kwargs)

                return counted

            self._wrap(CatalogSnapshot, "load", make_snapshot_load)

        return self

    def __exit__(self, *exc: Any) -> None:
        for owner, name, original in reversed(self._restore):
            setattr(owner, name, original)
        self._restore.clear()


def _scenario_validate(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    from classical_music.publication_validator import PublicationValidator

    result = PublicationValidator(repo_root).validate()
    return {
        "passed": result.passed,
        "errors": result.error_count(),
        "warnings": result.warning_count(),
    }


def _scenario_build(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    from classical_music.publication_site import PublicationSiteGenerator

    result = PublicationSiteGenerator(repo_root, output_dir).generate(validate=False)
    return {
        "page_count": result.page_count,
        "composer_count": result.composer_count,
        "work_count": result.work_count,
    }


def _scenario_validate_and_build(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    from classical_music.publication_site import PublicationSiteGenerator

    result = PublicationSiteGenerator(repo_root, output_dir).generate(validate=True)
    return {
        "page_count": result.page_count,
        "composer_count": result.composer_count,
        "work_count": result.work_count,
    }


SCENARIOS: dict[str, Callable[[Path, Path], dict[str, Any]]] = {
    "validate": _scenario_validate,
    "build": _scenario_build,
    "validate+build": _scenario_validate_and_build,
}


def measure(scenario: str, repo_root: Path, quiet: bool) -> Counters:
    """Run one scenario once and return its counters."""
    runner = SCENARIOS[scenario]
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "publication"
        sink = io.StringIO() if quiet else sys.stdout
        with Instrumentation() as instrumentation:
            wall_start = time.perf_counter()
            cpu_start = time.process_time()
            with contextlib.redirect_stdout(sink):
                result = runner(repo_root, output_dir)
            wall = time.perf_counter() - wall_start
            cpu = time.process_time() - cpu_start

    return Counters(
        yaml_loads=instrumentation.yaml_loads,
        distinct_yaml_files=len(instrumentation.files),
        catalog_loads=instrumentation.catalog_loads,
        snapshot_loads=instrumentation.snapshot_loads,
        parse_seconds=instrumentation.parse_seconds,
        wall_seconds=wall,
        cpu_seconds=cpu,
        result=result,
    )


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _summarise(runs: list[Counters]) -> dict[str, Any]:
    def stats(values: list[float]) -> dict[str, float]:
        return {
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
        }

    return {
        "runs": [asdict(run) for run in runs],
        "yaml_loads": runs[0].yaml_loads,
        "distinct_yaml_files": runs[0].distinct_yaml_files,
        "catalog_loads": runs[0].catalog_loads,
        "snapshot_loads": runs[0].snapshot_loads,
        "parse_seconds": stats([run.parse_seconds for run in runs]),
        "wall_seconds": stats([run.wall_seconds for run in runs]),
        "cpu_seconds": stats([run.cpu_seconds for run in runs]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3, help="Repetitions per scenario")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=sorted(SCENARIOS),
        help="Scenario to measure; repeatable. Defaults to all scenarios.",
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, help="Write the JSON report to this path")
    parser.add_argument("--label", default="local", help="Free-form label for the report")
    parser.add_argument(
        "--verbose-scenario-output",
        action="store_true",
        help="Do not suppress stdout of the measured code",
    )
    args = parser.parse_args(argv)

    scenarios = args.scenario or sorted(SCENARIOS)
    report: dict[str, Any] = {
        "label": args.label,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "repo_root": str(args.repo_root),
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "data_tree": _git("rev-parse", "HEAD:data"),
            "dirty": bool(_git("status", "--porcelain")),
        },
        "runs_per_scenario": args.runs,
        "scenarios": {},
    }

    for scenario in scenarios:
        runs = [
            measure(scenario, args.repo_root, quiet=not args.verbose_scenario_output)
            for _ in range(args.runs)
        ]
        report["scenarios"][scenario] = _summarise(runs)
        summary = report["scenarios"][scenario]
        print(
            f"{scenario:16} yaml_loads={summary['yaml_loads']:>6} "
            f"distinct_files={summary['distinct_yaml_files']:>6} "
            f"catalog_loads={summary['catalog_loads']} "
            f"snapshot_loads={summary['snapshot_loads']} "
            f"parse_median={summary['parse_seconds']['median']:.2f}s "
            f"wall_median={summary['wall_seconds']['median']:.2f}s "
            f"cpu_median={summary['cpu_seconds']['median']:.2f}s",
            file=sys.stderr,
        )

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
