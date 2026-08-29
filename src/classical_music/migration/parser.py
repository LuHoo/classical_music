from __future__ import annotations

import re
from pathlib import Path

from .models import SourceLocation, SourceRecord
from .entity_matcher import extract_catalogue_number


HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)\s*$")
WORK_RE = re.compile(r"^(?P<gem>💎|\[gem\])?\s*\*\*(?P<title>.+?)\*\*(?P<tail>.*)$")
# Match version/revision/date in parentheses, excluding gramophone issues (MM/YYYY)
# Negative lookahead (?!\d{1,2}/\d{4}(?:\)|$)) prevents matching (09/2024) format
DATE_RE = re.compile(r"\((?P<date>(?!\d{1,2}/\d{4}(?:\)|$))([^)]+))\)")
URL_RE = re.compile(r"https?://[^\s)]+")
PERFORMER_RE = re.compile(r"\[[^\]]*?\*(?P<performers>.+?)\*[^\]]*?\]\((?P<url>https?://[^)]+)\)")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")
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

        performers: str | None = None
        performer_match = PERFORMER_RE.search(line)
        if performer_match:
            performers = performer_match.group("performers").strip()
        
        # Remove recording links from tail before looking for date
        # This avoids matching parentheses in URLs like (http://...)
        tail_without_links = MARKDOWN_LINK_RE.sub("", tail)
        
        # Look for dates only in the tail without URLs.
        date_match = DATE_RE.search(tail_without_links)
        date_text = date_match.group("date").strip() if date_match else None

        parenthetical_texts = [
            match.group("date").strip()
            for match in DATE_RE.finditer(tail_without_links)
        ]
        identity_parentheticals = [
            text
            for text in parenthetical_texts
            if text != date_text and not GRAMOPHONE_RE.fullmatch(f"({text})")
        ]

        # Preserve date and version/arrangement descriptors in work_text for
        # identity resolution. The source document often stores curated Work
        # boundary information in trailing parentheses after the recording link.
        work_text = title
        if date_text:
            work_text = f"{title} ({date_text})"
        for descriptor in identity_parentheticals:
            work_text = f"{work_text} ({descriptor})"

        issue_match = GRAMOPHONE_RE.search(line)
        gramophone_issue = _normalize_gramophone_issue(issue_match.group("issue")) if issue_match else None

        links = URL_RE.findall(line)

        source_id = f"{file_path.stem}:{line_number}"
        common = {
            "location": SourceLocation(
                source_file=str(file_path.as_posix()),
                line_number=line_number,
                heading_path=heading_path.copy(),
            ),
            "raw_markdown": line.strip(),
            "gem_marker": gem_marker,
            "category": heading_path[-1] if heading_path else None,
            "tidal_links": [url for url in links if "tidal.com" in url],
            "performer_text": performers,
            "gramophone_issue": gramophone_issue,
        }

        # A legacy collective Prokofiev line describes two juvenile Works. Keep
        # this generic enough for explicit "two juvenile" source phrasing while
        # preserving the original source line for the authority gate.
        juvenile_symphonies = re.search(
            r"two\s+juvenile:\s*Symphony\s*\((?P<first>\d{4})\)\s+and\s+Symphony\s*\((?P<second>\d{4})\)",
            tail,
            re.IGNORECASE,
        )
        if normalize_title_for_parser(title) == "symphonies" and juvenile_symphonies:
            for index, year in enumerate(
                (juvenile_symphonies.group("first"), juvenile_symphonies.group("second")),
                start=1,
            ):
                records.append(
                    SourceRecord(
                        source_id=f"{source_id}:{index}",
                        work_text=f"Symphony ({year})",
                        date_text=year,
                        catalogue=None,
                        **common,
                    )
                )
            continue

        records.append(
            SourceRecord(
                source_id=source_id,
                work_text=work_text,
                date_text=date_text,
                catalogue=extract_catalogue_number(f"{title} {tail}"),
                **common,
            )
        )

    return records


def _normalize_gramophone_issue(issue: str | None) -> str | None:
    if issue is None:
        return None
    month, year = issue.split("/")
    return f"{year}-{month}"


def normalize_title_for_parser(title: str) -> str:
    return re.sub(r"\s+", " ", title.casefold().strip())
