from __future__ import annotations

import re
from pathlib import Path

from .models import SourceLocation, SourceRecord


HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)\s*$")
WORK_RE = re.compile(r"^(?P<gem>💎|\[gem\])?\s*\*\*(?P<title>.+?)\*\*(?P<tail>.*)$")
DATE_RE = re.compile(r"\((?P<date>[^)]*\d[^)]*)\)")
URL_RE = re.compile(r"https?://[^\s)]+")
PERFORMER_RE = re.compile(r"\[\*(?P<performers>.+?)\*\]\((?P<url>https?://[^)]+)\)")
GRAMOPHONE_RE = re.compile(r"\((?P<issue>\d{2}/\d{4})\)")


def parse_composer_markdown(file_path: Path) -> list[SourceRecord]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    heading_path: list[str] = []
    records: list[SourceRecord] = []

    for line_number, line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            depth = max(0, level - 2)
            heading_path = heading_path[:depth]
            heading_path.append(heading_text)
            continue

        work_match = WORK_RE.match(line.strip())
        if not work_match:
            continue

        title = work_match.group("title").strip()
        tail = work_match.group("tail") or ""
        gem_marker = bool(work_match.group("gem"))

        date_match = DATE_RE.search(line)
        date_text = date_match.group("date").strip() if date_match else None

        performers: str | None = None
        performer_match = PERFORMER_RE.search(line)
        if performer_match:
            performers = performer_match.group("performers").strip()

        issue_match = GRAMOPHONE_RE.search(line)
        gramophone_issue = _normalize_gramophone_issue(issue_match.group("issue")) if issue_match else None

        links = URL_RE.findall(line)

        source_id = f"{file_path.stem}:{line_number}"
        records.append(
            SourceRecord(
                source_id=source_id,
                location=SourceLocation(
                    source_file=str(file_path.as_posix()),
                    line_number=line_number,
                    heading_path=heading_path.copy(),
                ),
                raw_markdown=line.strip(),
                gem_marker=gem_marker,
                work_text=title,
                date_text=date_text,
                category=heading_path[-1] if heading_path else None,
                tidal_links=[url for url in links if "tidal.com" in url],
                performer_text=performers,
                gramophone_issue=gramophone_issue,
            )
        )

    return records


def _normalize_gramophone_issue(issue: str | None) -> str | None:
    if issue is None:
        return None
    month, year = issue.split("/")
    return f"{year}-{month}"
