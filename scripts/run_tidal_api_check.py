#!/usr/bin/env python3
"""Bounded, report-only authenticated catalogue and recovery-endpoint pilot."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from classical_music.tidal_auth import access_token
from classical_music.tidal_maintenance import TidalAPI, Transport
from classical_music.tidal_maintenance import main as check_links

# These accepted collection links were independently checked against Tidal's
# public JSON-LD on 2026-10-02. The ISRC is independent of our API adapter.
TRACK = "https://tidal.com/track/401810404"
TRACK_ISRC = "GBLLH2588619"
ALBUM = "https://tidal.com/album/187335103"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/tidal-maintenance/latest.json")
    )
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 50:
        parser.error("Pilot limit must be between 1 and 50")
    try:
        token = access_token()
        api = TidalAPI(Transport(), token, "NL")
        track = api.identity(TRACK)
        if track.get("isrc") != TRACK_ISRC:
            raise ValueError(
                "Track API identity disagrees with independently observed ISRC"
            )
        album = api.identity(ALBUM)
        if not album.get("barcodeId"):
            raise ValueError("Album API did not supply a barcode")
        for url, identity in [(TRACK, track), (ALBUM, album)]:
            if url not in api.candidates(url, identity):
                raise ValueError(
                    "Exact-identifier API search did not return the known resource"
                )
        print(
            json.dumps(
                {
                    "authenticated_resource_checks": 2,
                    "exact_identifier_search_checks": 2,
                    "country": "NL",
                }
            )
        )
        # Keep the token within this process, never in a file or command argument.
        previous = os.environ.get("TIDAL_ACCESS_TOKEN")
        os.environ["TIDAL_ACCESS_TOKEN"] = token
        try:
            return check_links(
                [
                    "--use-api",
                    "--country",
                    "NL",
                    "--limit",
                    str(args.limit),
                    "--output",
                    str(args.output),
                ]
            )
        finally:
            if previous is None:
                os.environ.pop("TIDAL_ACCESS_TOKEN", None)
            else:
                os.environ["TIDAL_ACCESS_TOKEN"] = previous
    except ValueError as exc:
        parser.exit(2, f"Tidal API pilot failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
