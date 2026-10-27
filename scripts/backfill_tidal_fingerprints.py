#!/usr/bin/env python3
"""Backfill Tidal identity fingerprints for canonical URLs that lack one.

Operational only: this script reads canonical performance YAML files and
writes a persistent ledger under reports/tidal-maintenance/. It never
modifies canonical data, never selects or creates a recommendation, and
never promotes a replacement URL. The ledger exists so that the hourly
link-check round can recover a removed URL from its ISRC (track) or
barcode (album) even when the URL dies before the rotation ever saw it
alive (the #392/#393 pattern: "original identity fingerprint
unavailable; no replacement search").
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from classical_music.tidal_auth import access_token
from classical_music.tidal_maintenance import (
    TidalAPI,
    Transport,
    check_url,
    inventory,
    link_entries,
)

LEDGER_VERSION = 1
QUEUE_PREVIEW = 10


def has_identifier(entry: dict) -> bool:
    return bool((entry or {}).get("isrc") or (entry or {}).get("barcodeId"))


def load_ledger(path: Path) -> dict:
    """Load the fingerprint ledger; an absent file starts a fresh ledger."""
    if not path.exists():
        return {"version": LEDGER_VERSION, "fingerprints": {}}
    try:
        doc = json.loads(path.read_text())
    except ValueError:
        raise ValueError("Fingerprint ledger is not valid JSON") from None
    if (
        not isinstance(doc, dict)
        or doc.get("version") != LEDGER_VERSION
        or not isinstance(doc.get("fingerprints"), dict)
    ):
        raise ValueError("Fingerprint ledger must be a JSON object with a fingerprints mapping")
    for url, entry in doc["fingerprints"].items():
        if not isinstance(url, str) or not isinstance(entry, dict):
            raise ValueError("Fingerprint ledger has a malformed entry")
    return doc


def adopt_round_fingerprints(ledger: dict, report_path: Path) -> int:
    """Adopt fingerprints recorded by check_tidal_links rounds (latest.json)."""
    if not report_path.exists():
        return 0
    try:
        report = json.loads(report_path.read_text())
    except ValueError:
        raise ValueError("Previous round report is not valid JSON") from None
    recorded = report.get("fingerprints") if isinstance(report, dict) else None
    if not isinstance(recorded, dict):
        return 0
    fingerprints = ledger["fingerprints"]
    adopted = 0
    for url, identity in recorded.items():
        if not isinstance(url, str) or not isinstance(identity, dict):
            raise ValueError("Round report has a malformed fingerprint entry")
        known = fingerprints.get(url) or {}
        if has_identifier(identity) and not has_identifier(known):
            fingerprints[url] = {**known, **identity}
            adopted += 1
    return adopted


def canonical_urls(root: Path) -> list[str]:
    records = inventory(root)
    return sorted({url for url, _ in url_references(records).items()})


def url_references(records: list[tuple[Path, dict]]) -> dict[str, list[dict]]:
    """Map each canonical Tidal URL to the performances that reference it."""
    refs: dict[str, list[dict]] = {}
    for path, record in records:
        for entry in link_entries(record):
            url = entry.get("url")
            if not url:
                continue
            refs.setdefault(url, []).append(
                {
                    "performance": record.get("id"),
                    "work": record.get("work_id"),
                    "file": path.name,
                }
            )
    return dict(sorted(refs.items()))


def select_due(urls: list[str], ledger: dict, limit: int) -> list[str]:
    """URLs without an identifier, never-attempted first, then least recent."""
    if limit < 1:
        raise ValueError("Backfill limit must be at least 1")
    known = ledger["fingerprints"]
    pending = [url for url in urls if not has_identifier(known.get(url) or {})]
    return sorted(
        pending,
        key=lambda url: (
            0 if not (known.get(url) or {}).get("last_checked") else 1,
            (known.get(url) or {}).get("last_checked", ""),
            url,
        ),
    )[:limit]


def capture(url: str, transport: Transport, api: TidalAPI | None, now: str) -> dict:
    """Capture one fingerprint; a failed attempt is recorded, never fatal."""
    if api is not None:
        try:
            identity = api.identity(url)
        except ValueError:
            identity = {}
        if has_identifier(identity):
            return {**identity, "last_checked": now}
    # Unauthenticated page fallback: JSON-LD identity may still carry the ISRC.
    check = check_url(url, transport, now)
    entry = {**check.identity, "status": check.status, "last_checked": now}
    return entry


def run(
    root: Path,
    transport: Transport,
    *,
    ledger_path: Path,
    report_path: Path | None = None,
    api: TidalAPI | None = None,
    limit: int = 60,
) -> dict:
    ledger = load_ledger(ledger_path)
    adopted = adopt_round_fingerprints(ledger, report_path) if report_path else 0
    records = inventory(root)
    refs = url_references(records)
    urls = sorted(refs)
    now = datetime.now(UTC).isoformat()
    selected = select_due(urls, ledger, limit)
    captured = 0
    for url in selected:
        entry = capture(url, transport, api, now)
        ledger["fingerprints"][url] = entry
        if has_identifier(entry):
            captured += 1
    known = sum(1 for e in ledger["fingerprints"].values() if has_identifier(e))

    def pending_entry(url: str) -> dict:
        return ledger["fingerprints"].get(url) or {}

    status_counts: dict[str, int] = {}
    for url in urls:
        entry = pending_entry(url)
        if has_identifier(entry):
            continue
        status = entry.get("status") or "never-attempted"
        status_counts[status] = status_counts.get(status, 0) + 1
    unavailable = [
        {"url": url, "performances": refs[url]}
        for url in urls
        if pending_entry(url).get("status") == "unavailable" and not has_identifier(pending_entry(url))
    ]
    next_up = [
        {
            "url": url,
            "status": pending_entry(url).get("status") or "never-attempted",
            "last_checked": pending_entry(url).get("last_checked") or "-",
        }
        for url in select_due(urls, ledger, QUEUE_PREVIEW)
    ]
    summary = {
        "checked_at": now,
        "total_unique_urls": len(urls),
        "known_fingerprints": known,
        "adopted_from_round": adopted,
        "attempted": len(selected),
        "captured": captured,
        "remaining": len(urls) - known,
        "pending_status_counts": status_counts,
        "unavailable": unavailable,
        "next_up": next_up,
    }
    if ledger_path.resolve().is_relative_to((root / "data").resolve()):
        raise ValueError("Fingerprint ledger must live outside canonical data/")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    ledger_path.with_suffix(".md").write_text(markdown(summary))
    return summary


def markdown(summary: dict) -> str:
    lines = [
        "# Tidal fingerprint backfill",
        "",
        f"Checked: {summary['checked_at']}",
        f"Known fingerprints: {summary['known_fingerprints']} / {summary['total_unique_urls']}",
        f"This run: attempted {summary['attempted']}, captured {summary['captured']},"
        f" adopted from round report {summary['adopted_from_round']}",
        f"Remaining without fingerprint: {summary['remaining']}",
        "",
        "Operational only: fingerprints enable recovery; nothing is promoted automatically.",
        "",
        "## Pending URLs by status",
        "",
    ]
    for status, count in sorted(summary["pending_status_counts"].items()):
        lines.append(f"- {status}: {count}")
    lines += ["", f"## Confirmed unavailable ({len(summary['unavailable'])})", ""]
    if summary["unavailable"]:
        lines.append(
            "Dead anchors without a fingerprint. Fix candidates: check these"
            " performances and repair or replace the URL."
        )
        for item in summary["unavailable"]:
            lines.append(f"- {item['url']}")
            for ref in item["performances"]:
                lines.append(
                    f"  - performance `{ref['performance']}`"
                    f" (work `{ref['work']}`, file `{ref['file']}`)"
                )
    else:
        lines.append("None: no pending canonical URL has status `unavailable`.")
    lines += ["", f"## Next up ({len(summary['next_up'])})", ""]
    for item in summary["next_up"]:
        lines.append(
            f"- {item['url']} — {item['status']}, last checked {item['last_checked']}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--state",
        type=Path,
        default=Path("reports/tidal-maintenance/fingerprints.json"),
        help="Persistent fingerprint ledger JSON",
    )
    parser.add_argument(
        "--round-report",
        type=Path,
        default=Path("reports/tidal-maintenance/latest.json"),
        help="Previous check_tidal_links report to adopt fingerprints from",
    )
    parser.add_argument("--country", default="NL")
    parser.add_argument("--use-api", action="store_true", help="Query the official API for identifiers")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--limit", type=int, default=60, help="Maximum URLs to attempt per run")
    args = parser.parse_args(argv)
    if args.state.suffix != ".json" or args.state.resolve().is_relative_to(
        (args.repo_root / "data").resolve()
    ):
        parser.error("State must be a .json ledger outside canonical data/")
    if args.limit < 1:
        parser.error("Backfill limit must be at least 1")
    if args.timeout <= 0 or args.delay < 0 or not re.fullmatch("[A-Z]{2}", args.country):
        parser.error("Invalid timeout, delay or country")
    try:
        token = access_token() if args.use_api else ""
    except ValueError as exc:
        parser.error(str(exc))
    try:
        transport = Transport(args.timeout, args.delay)
        api = TidalAPI(transport, token, args.country) if args.use_api else None
        summary = run(
            args.repo_root,
            transport,
            ledger_path=args.state,
            report_path=args.round_report,
            api=api,
            limit=args.limit,
        )
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Fingerprint backfill failed: {exc}\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
