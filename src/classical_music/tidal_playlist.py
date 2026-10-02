"""Read a bounded playlist source snapshot; never write canonical recommendations."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, build_opener
from uuid import UUID

from classical_music.tidal_auth import NoAuthRedirects, access_token

API = "https://openapi.tidal.com/v2"
MAX_RESPONSE_BYTES = 4_000_000
INCLUDE = "items,items.artists,items.albums,items.credits,items.usageRules"


def playlist_id(value: str) -> str:
    """Accept an exact public playlist URL or UUID, not an arbitrary request URL."""
    if "://" in value:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "tidal.com"
            or not parsed.path.startswith("/playlist/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Expected a https://tidal.com/playlist/<UUID> URL")
        value = parsed.path.removeprefix("/playlist/").rstrip("/")
    try:
        return str(UUID(value))
    except ValueError:
        raise ValueError("Expected a Tidal playlist UUID") from None


class Catalogue:
    def __init__(self, token: str):
        self.token = token
        self.opener = build_opener(NoAuthRedirects())

    def get(self, url: str) -> dict:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "openapi.tidal.com":
            raise ValueError("Refusing to send catalogue credentials to another host")
        request = Request(
            url,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.api+json",
            },
        )
        for attempt in range(3):
            # Catalogue endpoints have a small per-app request budget.
            time.sleep(2)
            try:
                with self.opener.open(request, timeout=20) as response:
                    raw = response.read(MAX_RESPONSE_BYTES + 1)
                break
            except HTTPError as exc:
                if exc.code == 429 and attempt < 2:
                    try:
                        delay = min(
                            30, max(2, int(exc.headers.get("Retry-After", "5")))
                        )
                    except (ValueError, AttributeError):
                        delay = 5
                    time.sleep(delay)
                    continue
                raise ValueError(
                    f"Playlist catalogue request failed (HTTP {exc.code})"
                ) from None
            except (URLError, OSError):
                raise ValueError(
                    "Playlist catalogue request failed (network error)"
                ) from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Catalogue response exceeded the snapshot size limit")
        try:
            document = json.loads(raw)
            if not isinstance(document, dict) or "data" not in document:
                raise ValueError
        except (ValueError, UnicodeError):
            raise ValueError("Invalid catalogue response") from None
        return document


def snapshot(value: str, *, limit: int = 100, country: str = "NL", client=None) -> dict:
    if not 1 <= limit <= 500:
        raise ValueError("Track limit must be between 1 and 500")
    if len(country) != 2 or not country.isascii() or not country.isalpha():
        raise ValueError("Expected a two-letter country code")
    country = country.upper()
    identifier = playlist_id(value)
    client = client or Catalogue(access_token())
    metadata_url = f"{API}/playlists/{identifier}?{urlencode({'countryCode': country})}"
    metadata = client.get(metadata_url)["data"]
    if (
        not isinstance(metadata, dict)
        or metadata.get("id") != identifier
        or metadata.get("type") != "playlists"
    ):
        raise ValueError("Playlist identity does not match the requested source")
    modified = metadata.get("attributes", {}).get("lastModifiedAt")
    if not isinstance(modified, str) or not modified:
        raise ValueError("Playlist has no modification marker; stable snapshot refused")
    path = f"/v2/playlists/{identifier}/relationships/items"
    next_url = (
        "https://openapi.tidal.com"
        + path
        + "?"
        + urlencode({"countryCode": country, "include": INCLUDE})
    )
    seen = set()
    items = []
    included = {}
    truncated = False
    while next_url and len(items) < limit:
        parsed = urlsplit(next_url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "openapi.tidal.com"
            or parsed.path != path
            or parsed.fragment
            or next_url in seen
        ):
            raise ValueError(
                f"Invalid or repeated playlist pagination link "
                f"(host={parsed.netloc}, path={parsed.path})"
            )
        seen.add(next_url)
        document = client.get(next_url)
        page = document["data"]
        if not isinstance(page, list):
            raise ValueError("Invalid playlist items response")  # noqa: TRY004 - malformed remote document
        remaining = limit - len(items)
        items.extend(page[:remaining])
        truncated = len(page) > remaining
        for resource in document.get("included", []):
            if resource.get("type") in {
                "tracks",
                "albums",
                "artists",
                "credits",
                "usageRules",
            }:
                included[(resource["type"], resource["id"])] = resource
        following = document.get("links", {}).get("next")
        if isinstance(following, dict):
            following = following.get("href")
        next_url = urljoin(next_url, following) if following else None
        if next_url:
            # Tidal documents root-relative links without the API version.
            target = urlsplit(next_url)
            query = dict(parse_qsl(target.query, keep_blank_values=True))
            if query.get("countryCode", country).upper() != country:
                raise ValueError("Playlist pagination changed the requested country")
            query.setdefault("countryCode", country)
            query.setdefault("include", INCLUDE)
            next_url = urlunsplit(
                (
                    target.scheme,
                    target.netloc,
                    path if target.path == path.removeprefix("/v2") else target.path,
                    urlencode(query),
                    target.fragment,
                )
            )
        if not page and next_url:
            raise ValueError("Empty playlist page has a continuation")
    after = client.get(metadata_url)["data"]
    if (
        not isinstance(after, dict)
        or after.get("id") != identifier
        or after.get("type") != "playlists"
        or modified != after.get("attributes", {}).get("lastModifiedAt")
    ):
        raise ValueError("Playlist changed during snapshot; retry before importing")
    return {
        "schema_version": 1,
        "fetched_at": datetime.now(UTC).isoformat(),
        "country_code": country,
        "source_url": f"https://tidal.com/playlist/{identifier}",
        "playlist": metadata,
        "items": [{"position": n, "resource": item} for n, item in enumerate(items, 1)],
        "included": list(included.values()),
        "source_complete": not (truncated or next_url),
        "fetched_item_count": len(items),
        # If the limit cuts through a page, its next link skips unread items.
        # Resume the eventual import by the recorded item position, not this link.
        "next_page": None if truncated else next_url,
        "next_item_position": len(items) + 1 if truncated or next_url else None,
    }
