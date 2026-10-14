#!/usr/bin/env python3
"""Create a read-only catalogue source artifact for a curated playlist batch."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classical_music.tidal_playlist import snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--country", default="NL")
    parser.add_argument(
        "--output", type=Path, default=Path("reports/tidal-playlist/source.json")
    )
    args = parser.parse_args()
    if "data" in args.output.resolve().parts or args.output.suffix != ".json":
        parser.error("Source snapshots must be JSON outside canonical data/")
    try:
        report = snapshot(args.playlist, limit=args.limit, country=args.country)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "playlist": report["playlist"]["attributes"]["name"],
                "fetched_items": report["fetched_item_count"],
                "source_complete": report["source_complete"],
                "canonical_files_written": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
