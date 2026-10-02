"""Operational Tidal link checks; never select or create a recommendation."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ruamel.yaml import YAML

MAX_BYTES = 2_000_000
HOSTS = {"tidal.com", "www.tidal.com", "listen.tidal.com"}


def resource(url: str) -> tuple[str, str] | None:
    """Only known public Tidal album/track URL shapes are fetched."""
    try:
        p = urlsplit(url)
        port = p.port
    except (ValueError, TypeError, AttributeError):
        return None
    if (
        p.scheme not in {"http", "https"}
        or p.hostname not in HOSTS
        or p.username
        or p.password
    ):
        return None
    if port not in {None, 80, 443}:
        return None
    nested = re.fullmatch(r"/(?:browse/)?album/\d+/track/(\d+)/?", p.path)
    if nested:
        return ("track", nested[1])
    m = re.fullmatch(r"/(?:browse/)?(album|track)/(\d+)/?", p.path)
    return (m[1], m[2]) if m else None


def normalized(url: str) -> str:
    key = resource(url)
    if not key:
        raise ValueError(f"Unsupported Tidal URL: {url}")
    return f"https://tidal.com/{key[0]}/{key[1]}"


class SafeRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not follow login, unrelated domains, or arbitrary API redirects.
        if not resource(newurl):
            raise ValueError("Redirect left supported Tidal album/track URLs")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass
class Response:
    code: int
    url: str
    body: str = ""
    error: str = ""


class Transport:
    def __init__(self, timeout: float = 15, delay: float = 0.5):
        self.timeout, self.delay = timeout, delay
        self.opener = build_opener(SafeRedirects())
        self.last_request = 0.0
        self.responses: dict[str, Response] = {}

    def get(self, url: str, headers: dict | None = None) -> Response:
        if url in self.responses:
            return self.responses[url]
        pause = self.delay - (time.monotonic() - self.last_request)
        if pause > 0:
            time.sleep(pause)
        self.last_request = time.monotonic()
        req = Request(
            url,
            headers={
                "User-Agent": "ClassicalMusic-LinkMaintenance/1.0",
                **(headers or {}),
            },
        )
        try:
            with self.opener.open(req, timeout=self.timeout) as r:
                raw = r.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    return Response(
                        r.status, r.url, error="Response exceeds size limit"
                    )
                result = Response(
                    r.status, r.url, raw.decode("utf-8", errors="replace")
                )
                self.responses[url] = result
                return result
        except HTTPError as e:
            return Response(e.code, url, error=f"HTTP {e.code}")
        except (URLError, OSError, ValueError) as e:
            # Never include exception text: it may contain authentication details.
            return Response(0, url, error=type(e).__name__)


class Page(HTMLParser):
    def __init__(self, body: str):
        super().__init__()
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.documents: list[dict] = []
        self.script: list[str] | None = None
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            self.meta[a.get("property") or a.get("name", "")] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        if tag == "script" and a.get("type") == "application/ld+json":
            self.script = []

    def handle_data(self, text):
        if self.script is not None:
            self.script.append(text)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            try:
                value = json.loads("".join(self.script))
                self.documents.extend(value if isinstance(value, list) else [value])
            except (ValueError, TypeError):
                pass
            self.script = None

    def identity(self, key: tuple[str, str]) -> dict:
        expected = "MusicRecording" if key[0] == "track" else "MusicAlbum"
        for doc in self.documents:
            if not isinstance(doc, dict):
                continue
            if (
                doc.get("@type") == expected
                and resource(doc.get("url", doc.get("@id", ""))) == key
            ):
                result = {"title": doc.get("name", "")}
                if key[0] == "track" and re.fullmatch(
                    r"[A-Z]{2}[A-Z0-9]{3}\d{7}", str(doc.get("isrcCode", ""))
                ):
                    result["isrc"] = doc["isrcCode"]
                return result
        return {}


@dataclass
class Check:
    url: str
    status: str
    last_checked: str
    reason: str
    final_url: str = ""
    replacement_url: str = ""
    evidence: str = ""
    identity: dict = field(default_factory=dict)


def check_url(url: str, transport: Transport, now: str) -> Check:
    key = resource(url)
    if key is None:
        return Check(url, "uncertain", now, "Unsupported URL shape; no request made")
    r = transport.get(normalized(url))
    if r.code in {404, 410}:
        return Check(url, "unavailable", now, f"HTTP {r.code}", r.url)
    if r.error or r.code != 200 or resource(r.url) is None:
        return Check(url, "uncertain", now, r.error or f"HTTP {r.code}", r.url)
    page = Page(r.body)
    if (
        page.meta.get("og:title") == "Not Found - TIDAL"
        and page.meta.get("og:description")
        == "The requested content could not be found on TIDAL."
    ):
        return Check(
            url, "unavailable", now, "Tidal content-not-found page (HTTP 200)", r.url
        )
    target = urljoin(r.url, page.canonical) if page.canonical else r.url
    target_key = resource(target)
    if target_key is None:
        return Check(url, "uncertain", now, "Unrecognised canonical target", r.url)
    identity = page.identity(target_key)
    # Content metadata must describe the specific resource, not a generic app shell.
    og_key = resource(page.meta.get("og:url", ""))
    og_type = "music.song" if target_key[0] == "track" else "music.album"
    available = bool(identity.get("title")) or (
        og_key == target_key
        and page.meta.get("og:type") == og_type
        and bool(page.meta.get("og:title"))
    )
    if not available:
        return Check(
            url, "uncertain", now, "No resource-specific content metadata", r.url
        )
    if target_key != key:
        return Check(
            url,
            "uncertain",
            now,
            "Changed resource ID requires identity evidence",
            normalized(target),
            identity=identity,
        )
    changed = target != url or r.url != url
    return Check(
        url,
        "redirect" if changed else "ok",
        now,
        "Resource-specific Tidal metadata",
        normalized(target),
        normalized(target) if changed else "",
        "Same Tidal resource ID" if changed else "",
        identity,
    )


class TidalAPI:
    """Optional official API. Token supplied by environment, never persisted."""

    def __init__(self, transport: Transport, token: str, country: str):
        self.transport, self.token, self.country = transport, token, country
        self.cache: dict[str, dict] = {}

    def request(self, path: str, params: dict) -> dict:
        url = (
            "https://openapi.tidal.com/v2/"
            + path
            + "?"
            + urlencode({"countryCode": self.country, **params})
        )
        if url not in self.cache:
            r = self.transport.get(
                url,
                {
                    "Authorization": "Bearer " + self.token,
                    "Accept": "application/vnd.api+json",
                },
            )
            if r.error or r.code != 200:
                raise ValueError(f"Tidal API unavailable (HTTP {r.code})")
            try:
                value = json.loads(r.body)
                if not isinstance(value, dict) or "data" not in value:
                    raise ValueError
            except ValueError:
                raise ValueError("Invalid Tidal API response") from None
            self.cache[url] = value
        return self.cache[url]

    def identity(self, url: str) -> dict:
        kind, rid = resource(url)
        data = self.request(f"{kind}s/{rid}", {}).get("data")
        if (
            not isinstance(data, dict)
            or data.get("id") != rid
            or data.get("type") != kind + "s"
        ):
            return {}
        a = data.get("attributes", {})
        field = "isrc" if kind == "track" else "barcodeId"
        identifier = a.get(field)
        valid = re.fullmatch(
            r"[A-Z]{2}[A-Z0-9]{3}\d{7}" if kind == "track" else r"\d{12,13}",
            str(identifier or ""),
        )
        return {field: identifier, "title": a.get("title", "")} if valid else {}

    def candidates(self, url: str, identity: dict) -> list[str]:
        kind, _ = resource(url)
        field = "isrc" if kind == "track" else "barcodeId"
        if not identity.get(field):
            return []
        doc = self.request(kind + "s", {f"filter[{field}]": identity[field]})
        # A partial result set cannot establish uniqueness. No unbounded pagination.
        if doc.get("links", {}).get("next"):
            raise ValueError(
                "Recovery result is paginated; identity remains unresolved"
            )
        items = doc.get("data")
        if not isinstance(items, list):
            raise ValueError("Invalid Tidal API search response")  # noqa: TRY004 -- invalid protocol value
        return sorted(
            {
                f"https://tidal.com/{kind}/{x['id']}"
                for x in items
                if isinstance(x, dict)
                and x.get("type") == kind + "s"
                and str(x.get("id", "")).isdigit()
                and x.get("attributes", {}).get(field) == identity[field]
            }
        )


def same_identity(kind: str, old: dict, new: dict) -> bool:
    field = "isrc" if kind == "track" else "barcodeId"
    return bool(old.get(field)) and old.get(field) == new.get(field)


def recover(
    check: Check,
    old: dict,
    api: TidalAPI | None,
    transport: Transport,
    candidates: list[str],
) -> Check:
    kind, _ = resource(check.url)
    targets = list(candidates)
    if check.final_url and resource(check.final_url) != resource(check.url):
        targets.append(check.final_url)
    try:
        if api:
            targets.extend(api.candidates(check.url, old))
    except ValueError as e:
        check.reason += "; " + str(e)
        return check
    matches: dict[str, Check] = {}
    for target in sorted(set(targets)):
        if (
            not resource(target)
            or resource(target)[0] != kind
            or resource(target) == resource(check.url)
        ):
            continue
        candidate = check_url(target, transport, check.last_checked)
        if candidate.status not in {"ok", "redirect"}:
            continue
        identity = candidate.identity
        if api:
            try:
                identity = {**identity, **api.identity(candidate.final_url)}
            except ValueError:
                continue
        if same_identity(kind, old, identity):
            candidate.identity = identity
            matches[candidate.final_url] = candidate
    if len(matches) == 1:
        target, candidate = next(iter(matches.items()))
        check.status = "redirect"
        check.replacement_url = target
        check.evidence = (
            "Exact "
            + ("ISRC" if kind == "track" else "album barcode")
            + " match against original URL evidence"
        )
        check.reason = "Same Performance found under a replacement Tidal URL"
        check.identity = candidate.identity
    elif targets:
        check.status = "uncertain"
        check.reason += "; " + (
            "Multiple identity matches"
            if matches
            else "No verified replacement among investigated URLs"
        )
    return check


def link_entries(record: dict) -> list[dict]:
    links = record.get("links", {})
    if isinstance(links, list):
        return [
            x
            for x in links
            if isinstance(x, dict) and x.get("platform", "").lower() == "tidal"
        ]
    if isinstance(links, dict):
        tidal = links.get("tidal", {})
        return [tidal] if isinstance(tidal, dict) and tidal.get("url") else []
    return []


def inventory(root: Path) -> list[tuple[Path, dict]]:
    if not (root / "data/performances").is_dir():
        raise ValueError("Repository root has no data/performances directory")
    yaml = YAML(typ="safe")
    return [
        (p, yaml.load(p.read_text()))
        for p in sorted((root / "data/performances").glob("*.yaml"))
    ]


def apply_updates(
    root: Path, records: list[tuple[Path, dict]], checks: dict[str, Check]
) -> int:
    """Re-read and round-trip only URLs; stage every edit before writing any file."""
    edits = []
    for path, before in records:
        yaml = YAML()
        yaml.preserve_quotes = True
        current = yaml.load(path.read_text())
        if current != before:
            raise ValueError(
                f"Canonical file changed during check: {path.relative_to(root)}"
            )
        changed = False
        for entry in link_entries(current):
            check = checks.get(entry.get("url"))
            if (
                check
                and check.status == "redirect"
                and check.replacement_url
                and check.replacement_url != entry["url"]
            ):
                entry["url"] = check.replacement_url
                changed = True
        if changed:
            out = StringIO()
            yaml.dump(current, out)
            edits.append((path, out.getvalue()))
    for path, text in edits:
        path.write_text(text, encoding="utf-8")
    return len(edits)


def run(
    root: Path,
    transport: Transport,
    *,
    previous: dict | None = None,
    api: TidalAPI | None = None,
    recovery_urls: dict | None = None,
    candidates: list[dict] | None = None,
    limit: int | None = None,
    apply: bool = False,
) -> dict:
    if previous is not None and not isinstance(previous, dict):
        raise ValueError("Previous report must be a JSON object")
    if recovery_urls is not None and (
        not isinstance(recovery_urls, dict)
        or any(
            not isinstance(value, list)
            or any(not isinstance(url, str) for url in value)
            for value in recovery_urls.values()
        )
    ):
        raise ValueError("Recovery URLs must map each original URL to a list of URLs")
    if candidates is not None and (
        not isinstance(candidates, list)
        or any(not isinstance(candidate, dict) for candidate in candidates)
    ):
        raise ValueError("Previous candidates must be a JSON list of objects")
    records = inventory(root)
    urls = sorted(
        {
            entry["url"]
            for _, record in records
            for entry in link_entries(record)
            if entry.get("url")
        }
    )
    if limit is not None:
        urls = urls[:limit]
    now = datetime.now(UTC).isoformat()
    prior = {c["url"]: c for c in (previous or {}).get("checks", [])}
    fingerprints = dict((previous or {}).get("fingerprints", {}))
    for url, c in prior.items():
        if c.get("identity"):
            fingerprints[url] = c["identity"]
    checks: dict[str, Check] = {}
    for url in urls:
        check = check_url(url, transport, now)
        if resource(url):
            # Previous evidence is bound to this exact original URL, not Performance ID alone.
            old = fingerprints.get(url, {})
            if check.status in {"ok", "redirect"} and resource(
                check.final_url
            ) == resource(url):
                old = check.identity
            if api:
                try:
                    original = api.identity(url)
                    old = {**old, **original}
                except ValueError as e:
                    check.reason += "; " + str(e)
            if check.status in {"ok", "redirect"}:
                check.identity = old
            if check.status in {"unavailable", "uncertain"} and (
                old.get("isrc") or old.get("barcodeId")
            ):
                check = recover(
                    check, old, api, transport, (recovery_urls or {}).get(url, [])
                )
            elif check.status in {"unavailable", "uncertain"}:
                check.reason += (
                    "; original identity fingerprint unavailable; no replacement search"
                )
            # Keep the last verified fingerprint through outages, never fingerprint an unverified redirect.
            if not check.identity or check.status not in {"ok", "redirect"}:
                check.identity = old
        if check.identity:
            fingerprints[url] = check.identity
            if check.replacement_url:
                fingerprints[check.replacement_url] = check.identity
        checks[url] = check
    rows = []
    for path, record in records:
        for entry in link_entries(record):
            url = entry.get("url")
            if url not in checks:
                continue
            check = checks[url]
            row = {
                "performance_id": record["id"],
                "work_id": record["work_id"],
                "profile": record.get("profile"),
                "path": str(path.relative_to(root)),
                "url": url,
                "status": check.status,
                "last_checked": now,
            }
            if check.status == "unavailable":
                row["availability_note"] = "no longer available at this Tidal URL"
                row["previous_candidates"] = [
                    c
                    for c in (candidates or [])
                    if c.get("work_id") == record["work_id"]
                    and c.get("profile") == record.get("profile")
                ]
            rows.append(row)
    updated = apply_updates(root, records, checks) if apply else 0
    return {
        "version": 1,
        "checked_at": now,
        "country": api.country if api else None,
        "total_unique_urls": len(
            {e["url"] for _, r in records for e in link_entries(r) if e.get("url")}
        ),
        "checked_unique_urls": len(checks),
        "summary": dict(Counter(c.status for c in checks.values())),
        "updated_files": updated,
        "fingerprints": fingerprints,
        "checks": [vars(c) for c in checks.values()],
        "performances": rows,
    }


def markdown(report: dict) -> str:
    lines = [
        "# Tidal link maintenance",
        "",
        f"Checked: {report['checked_at']}",
        f"URLs: {report['checked_unique_urls']} / {report['total_unique_urls']}; updated files: {report['updated_files']}",
        f"Status: {report['summary']}",
        "",
        "`ok` means a resource page exists; it does not guarantee regional playback rights.",
        "Recommendations remain canonical, including when a URL is unavailable.",
        "",
        "## Links requiring attention or safely redirected",
        "",
    ]
    by_url = {c["url"]: c for c in report["checks"]}
    for row in report["performances"]:
        check = by_url[row["url"]]
        if check["status"] == "ok":
            continue
        lines += [
            f"- {row['performance_id']} (`{row['path']}`): **{check['status']}** — {check['reason']}",
            f"  URL: {check['url']}",
        ]
        if check["replacement_url"]:
            lines.append(
                f"  Replacement: {check['replacement_url']} ({check['evidence']})"
            )
        if check["status"] == "unavailable":
            lines.append(
                "  No longer available at this Tidal URL; no recommendation changed."
            )
            prior = row.get("previous_candidates", [])
            lines.append(
                "  Previous candidates (context only): "
                + (
                    json.dumps(prior, ensure_ascii=False)
                    if prior
                    else "none in supplied history; not searched or promoted"
                )
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument(
        "--output", type=Path, default=Path("reports/tidal-maintenance/latest.json")
    )
    p.add_argument(
        "--previous",
        type=Path,
        help="Previous checker report for identity fingerprints",
    )
    p.add_argument(
        "--recovery-urls",
        type=Path,
        help="JSON mapping old URL to candidate replacement URLs",
    )
    p.add_argument(
        "--previous-candidates",
        type=Path,
        help="JSON list of previous candidates with work_id/profile",
    )
    p.add_argument("--country", default="NL")
    p.add_argument(
        "--use-api",
        action="store_true",
        help="Use official API with TIDAL_ACCESS_TOKEN",
    )
    p.add_argument("--timeout", type=float, default=15)
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--limit", type=int, help="Check only the first N unique URLs")
    p.add_argument(
        "--apply", action="store_true", help="Write verified URL replacements only"
    )
    a = p.parse_args(argv)
    if a.output.suffix != ".json" or a.output.resolve().is_relative_to(
        (a.repo_root / "data").resolve()
    ):
        p.error("Output must be a .json report outside canonical data/")
    if (
        a.timeout <= 0
        or a.delay < 0
        or (a.limit is not None and a.limit < 1)
        or not re.fullmatch("[A-Z]{2}", a.country)
    ):
        p.error("Invalid timeout, delay, limit or country")
    token = os.environ.get("TIDAL_ACCESS_TOKEN", "")
    if a.use_api and not token:
        p.error("--use-api requires TIDAL_ACCESS_TOKEN")

    def read(path):
        return json.loads(path.read_text()) if path else None

    try:
        transport = Transport(a.timeout, a.delay)
        report = run(
            a.repo_root,
            transport,
            previous=read(a.previous or (a.output if a.output.exists() else None)),
            recovery_urls=read(a.recovery_urls),
            candidates=read(a.previous_candidates),
            api=TidalAPI(transport, token, a.country) if a.use_api else None,
            limit=a.limit,
            apply=a.apply,
        )
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        a.output.with_suffix(".md").write_text(markdown(report))
    except (ValueError, OSError) as e:
        p.exit(2, f"Link maintenance failed: {e}\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "total_unique_urls",
                    "checked_unique_urls",
                    "summary",
                    "updated_files",
                )
            }
        )
    )
    return 0
