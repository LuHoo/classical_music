import io
from copy import deepcopy
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from classical_music.tidal_playlist import API, Catalogue, playlist_id, snapshot

IDENTIFIER = "c11f614b-c011-43b2-be10-639f5cf7e5e3"
URL = f"https://tidal.com/playlist/{IDENTIFIER}"


def metadata(modified="2026-10-02T12:00:00Z"):
    return {
        "data": {
            "type": "playlists",
            "id": IDENTIFIER,
            "attributes": {
                "name": "Best Classical",
                "lastModifiedAt": modified,
            },
        }
    }


def page(ids, following=None):
    return {
        "data": [{"type": "tracks", "id": i} for i in ids],
        "included": [
            {"type": "tracks", "id": i, "attributes": {"title": i}} for i in ids
        ],
        "links": {"next": following},
    }


class Client:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        return deepcopy(self.responses.pop(0))


def test_snapshot_preserves_order_duplicates_and_pagination():
    client = Client(
        metadata(),
        page(["a", "b"], "?page%5Bcursor%5D=next"),
        page(["a", "c"]),
        metadata(),
    )
    result = snapshot(URL, client=client)
    assert [x["resource"]["id"] for x in result["items"]] == ["a", "b", "a", "c"]
    assert [x["position"] for x in result["items"]] == [1, 2, 3, 4]
    assert len(result["included"]) == 3
    assert result["source_complete"] is True
    assert "page%5Bcursor%5D=next" in client.urls[2]


def test_limit_does_not_offer_a_cursor_that_skips_unread_items():
    client = Client(metadata(), page(["a", "b", "c"], "?page[cursor]=next"), metadata())
    result = snapshot(URL, limit=2, client=client)
    assert result["fetched_item_count"] == 2
    assert result["source_complete"] is False
    assert result["next_page"] is None
    assert result["next_item_position"] == 3
    assert len(client.urls) == 3


def test_documented_root_relative_links_keep_country_and_nested_includes():
    following = f"/playlists/{IDENTIFIER}/relationships/items?page[cursor]=next"
    client = Client(metadata(), page(["a"], following), page(["b"]), metadata())
    assert snapshot(URL, client=client)["source_complete"]
    assert client.urls[2].startswith(
        f"{API}/playlists/{IDENTIFIER}/relationships/items?"
    )
    assert "countryCode=NL" in client.urls[2]
    assert "include=items" in client.urls[2]


@pytest.mark.parametrize(
    "following", ["https://evil.test/steal", f"{API}/tracks/1", "#fragment"]
)
def test_pagination_cannot_redirect_catalogue_credentials(following):
    client = Client(metadata(), page(["a"], following))
    with pytest.raises(ValueError, match="pagination"):
        snapshot(URL, client=client)
    assert len(client.urls) == 2


def test_repeated_pagination_is_refused():
    client = Client(
        metadata(), page(["a"], "?page[cursor]=same"), page(["b"], "?page[cursor]=same")
    )
    with pytest.raises(ValueError, match="pagination"):
        snapshot(URL, client=client)
    assert len(client.urls) == 3


def test_changed_playlist_is_not_an_importable_snapshot():
    client = Client(metadata(), page(["a"]), metadata("changed"))
    with pytest.raises(ValueError, match="changed"):
        snapshot(URL, client=client)


@pytest.mark.parametrize(
    "value",
    [
        "https://tidal.com.evil.test/playlist/" + IDENTIFIER,
        "https://tidal.com/playlist/" + IDENTIFIER + "?secret=1",
        "http://tidal.com/playlist/" + IDENTIFIER,
        "https://tidal.com/playlist/" + IDENTIFIER + "/extra",
    ],
)
def test_only_exact_playlist_source_urls_are_accepted(value):
    with pytest.raises(ValueError):
        playlist_id(value)


def test_canonical_playlist_uuid():
    assert playlist_id(URL) == IDENTIFIER
    assert playlist_id(IDENTIFIER.upper()) == IDENTIFIER


def test_rate_limit_retries_are_bounded_and_provider_errors_are_sanitized():
    response = io.BytesIO(b'{"data": []}')
    with patch("classical_music.tidal_playlist.time.sleep") as sleep:
        client = Catalogue("synthetic-token")
        with patch.object(
            client.opener,
            "open",
            side_effect=[
                HTTPError(API, 429, "secret", {"Retry-After": "3"}, None),
                response,
            ],
        ):
            assert client.get(API + "/tracks")["data"] == []
        assert [c.args[0] for c in sleep.call_args_list] == [2, 3, 2]
        with patch.object(
            client.opener, "open", side_effect=HTTPError(API, 429, "secret", {}, None)
        ) as opening:
            with pytest.raises(ValueError, match="HTTP 429") as err:
                client.get(API + "/tracks")
            assert opening.call_count == 3
            assert "secret" not in str(err.value)


@pytest.mark.parametrize("limit", [0, 201])
def test_source_fetch_is_bounded_before_any_request(limit):
    client = Client()
    with pytest.raises(ValueError, match="limit"):
        snapshot(URL, limit=limit, client=client)
    assert not client.urls
