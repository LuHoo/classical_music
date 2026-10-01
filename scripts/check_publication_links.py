#!/usr/bin/env python3
"""Fail a site build when a publication link has no generated HTML target."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from ruamel.yaml import YAML


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href" and value)


def check_links(site_dir: Path, baseurl: str) -> tuple[int, list[str]]:
    """Check collection navigation against actual Jekyll output, not source pages."""
    baseurl = baseurl.rstrip("/")
    prefix = baseurl + "/publication/"
    pages = sorted((site_dir / "publication").rglob("*.html"))
    if not pages:
        return 0, ["No generated publication HTML pages found."]
    failures: list[str] = []
    checked = 0
    for page in pages:
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for href in parser.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path.startswith(prefix):
                continue
            checked += 1
            relative = unquote(url.path[len(baseurl):]).lstrip("/")
            target = site_dir / relative
            if url.path.endswith("/"):
                target /= "index.html"
            if not target.is_file():
                failures.append(f"{page.relative_to(site_dir)}: {href} -> missing {relative}")
    return checked, sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=Path("_site"))
    parser.add_argument("--config", type=Path, default=Path("_config.yml"))
    args = parser.parse_args()
    config = YAML(typ="safe").load(args.config.read_text(encoding="utf-8")) or {}
    checked, failures = check_links(args.site_dir, config.get("baseurl", ""))
    if failures:
        print("Broken publication links:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"Checked {checked} publication links; all generated targets exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
