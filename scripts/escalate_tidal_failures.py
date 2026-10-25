#!/usr/bin/env python3
"""Open or update one issue per problematic Tidal URL; never a recommendation.

Reads the latest maintenance report plus the rotation ledger. A confirmed
unavailable URL escalates immediately; a stubbornly uncertain URL escalates
after repeated rounds. Existing open issues are updated instead of duplicated.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, build_opener

from classical_music.tidal_maintenance import (
    ESCALATION_LABEL,
    comment_body,
    escalation_actions,
    issue_body,
    load_state,
    marker,
)

LABEL_DESCRIPTION = (
    "Recommended Tidal URL no longer resolves; curator review of the link required"
)
LABEL_COLOR = "d73a4a"
API_VERSION = "2022-11-28"
MAX_RESPONSE_BYTES = 4_000_000


def api(token: str, url: str, data: dict | None = None, method: str | None = None):
    request = Request(
        url,
        method=method or ("POST" if data is not None else "GET"),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": API_VERSION,
        },
        data=json.dumps(data).encode() if data is not None else None,
    )
    try:
        with build_opener().open(request, timeout=30) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("GitHub API response exceeds size limit")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        if exc.code == 404 and data is None:
            return {}
        raise ValueError(
            f"GitHub API call failed (HTTP {exc.code}) for {url}"
        ) from None
    except OSError:
        raise ValueError("GitHub API call failed (network error)") from None


def ensure_label(token: str, repo: str) -> None:
    if api(token, f"https://api.github.com/repos/{repo}/labels/{ESCALATION_LABEL}") == {}:
        api(
            token,
            f"https://api.github.com/repos/{repo}/labels",
            {
                "name": ESCALATION_LABEL,
                "color": LABEL_COLOR,
                "description": LABEL_DESCRIPTION,
            },
        )


def open_issues(token: str, repo: str) -> list[dict]:
    issues = api(
        token,
        "https://api.github.com/repos/"
        + repo
        + "/issues?labels="
        + quote(ESCALATION_LABEL)
        + "&state=open&per_page=100",
    )
    if not isinstance(issues, list):
        raise ValueError("GitHub API did not return an issue list")
    return [i for i in issues if isinstance(i, dict) and "pull_request" not in i]


def escalate(token: str, repo: str, actions: list[dict]) -> dict:
    ensure_label(token, repo)
    existing = open_issues(token, repo)
    created, commented, skipped = [], [], []
    for action in actions:
        match = next(
            (i for i in existing if marker(action["url"]) in str(i.get("body", ""))),
            None,
        )
        if match is None:
            issue = api(
                token,
                f"https://api.github.com/repos/{repo}/issues",
                {
                    "title": f"Tidal-URL onbereikbaar: {action['performance_id']}",
                    "body": issue_body(action),
                    "labels": [ESCALATION_LABEL],
                },
            )
            created.append(issue.get("html_url", action["url"]))
        elif isinstance(match.get("number"), int):
            api(
                token,
                f"https://api.github.com/repos/{repo}/issues/{match['number']}/comments",
                {"body": comment_body(action)},
            )
            commented.append(match.get("html_url", action["url"]))
        else:
            skipped.append(action["url"])
    return {"created": created, "commented": commented, "skipped": skipped}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("reports/tidal-maintenance/latest.json")
    )
    parser.add_argument(
        "--state", type=Path, default=Path("reports/tidal-maintenance/state.json")
    )
    parser.add_argument("--repo", default="LuHoo/classical_music")
    parser.add_argument(
        "--uncertain-after",
        type=int,
        default=3,
        help="Escalate uncertain URLs after this many consecutive rounds",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show planned actions without API calls"
    )
    args = parser.parse_args(argv)
    if args.uncertain_after < 1:
        parser.error("uncertain-after must be at least 1")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token and not args.dry_run:
        parser.error("GITHUB_TOKEN is required unless --dry-run is used")
    try:
        report = json.loads(args.report.read_text())
        state = (
            load_state(args.state)
            if args.state.exists()
            else {"version": 1, "urls": {}}
        )
        actions = escalation_actions(
            report, state, uncertain_after=args.uncertain_after
        )
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Escalation failed while reading local inputs: {exc}\n")
    summary = {"actions": len(actions), "urls": [a["url"] for a in actions]}
    if args.dry_run:
        print(json.dumps({**summary, "dry_run": True, "detail": actions}))
        return 0
    try:
        result = escalate(token, args.repo, actions)
    except ValueError as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps({**summary, **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
