"""Try to falsify availability and identity decisions, without network access."""

import json
import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from classical_music.tidal_maintenance import (
    Check,
    Response,
    TidalAPI,
    apply_updates,
    check_url,
    inventory,
    main,
    markdown,
    recover,
    resource,
    run,
)

NOW = "2026-10-02T09:00:00+00:00"
OLD = "https://tidal.com/track/123"
NEW = "https://tidal.com/track/456"
ISRC = "GBLLH2588619"


def page(url=OLD, isrc=ISRC, title="Concerto: I. Presto"):
    kind = resource(url)[0]
    doc = {
        "@type": "MusicRecording" if kind == "track" else "MusicAlbum",
        "url": url,
        "name": title,
    }
    if isrc:
        doc["isrcCode"] = isrc
    return f'<link rel="canonical" href="{url}"><script type="application/ld+json">{json.dumps(doc)}</script>'


class Fake:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, headers=None):
        self.calls.append(url)
        return self.responses[url]


def fixture(root, *, url=OLD, profile=None, list_links=False, name="one"):
    record = {
        "id": name,
        "work_id": "work1",
        "performers": [{"name": "Accepted Ensemble"}],
        "keep_looking": True,
        "notes": "Trusted editorial meaning",
    }
    if profile:
        record["profile"] = profile
    record["links"] = (
        [
            {"platform": "tidal", "url": url},
            {"platform": "spotify", "url": "https://example.com"},
        ]
        if list_links
        else {"tidal": {"url": url}}
    )
    path = root / "data/performances" / f"{name}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    YAML().dump(record, path)
    return path


@pytest.mark.parametrize(
    "url",
    [
        "https://tidal.com.evil.test/track/1",
        "https://tidal.com/login",
        "https://user@tidal.com/track/1",
        "https://tidal.com:8888/track/1",
        "file:///track/1",
    ],
)
def test_unsupported_targets_not_fetched(url):
    t = Fake({})
    assert check_url(url, t, NOW).status == "uncertain"
    assert not t.calls


def test_normalizes_legacy_urls_without_changing_resource():
    url = "http://www.tidal.com/browse/track/123"
    t = Fake({OLD: Response(200, OLD, page())})
    c = check_url(url, t, NOW)
    assert c.status == "redirect"
    assert c.replacement_url == OLD
    assert c.evidence == "Same Tidal resource ID"


@pytest.mark.parametrize("code", [401, 403, 429, 500, 503, 0])
def test_blocks_and_network_errors_are_not_dead_links(code):
    assert check_url(OLD, Fake({OLD: Response(code, OLD)}), NOW).status == "uncertain"


@pytest.mark.parametrize("code", [404, 410])
def test_http_missing(code):
    assert check_url(OLD, Fake({OLD: Response(code, OLD)}), NOW).status == "unavailable"


def test_soft404_and_generic_app_shell():
    missing = '<meta property="og:title" content="Not Found - TIDAL"><meta property="og:description" content="The requested content could not be found on TIDAL.">'
    assert (
        check_url(OLD, Fake({OLD: Response(200, OLD, missing)}), NOW).status
        == "unavailable"
    )
    assert (
        check_url(
            OLD, Fake({OLD: Response(200, OLD, "<title>TIDAL</title>")}), NOW
        ).status
        == "uncertain"
    )


def test_wrong_resource_structured_data_does_not_prove_availability():
    assert (
        check_url(
            OLD,
            Fake(
                {
                    OLD: Response(
                        200,
                        OLD,
                        page(NEW).replace(f'<link rel="canonical" href="{NEW}">', ""),
                    )
                }
            ),
            NOW,
        ).status
        == "uncertain"
    )


def test_changed_id_redirect_needs_independent_old_evidence():
    t = Fake({OLD: Response(200, NEW, page(NEW))})
    c = check_url(OLD, t, NOW)
    assert c.status == "uncertain"
    assert not c.replacement_url


def test_exact_isrc_recovery_and_ambiguous_matches():
    t = Fake({NEW: Response(200, NEW, page(NEW))})
    c = recover(
        Check(OLD, "unavailable", NOW, "HTTP 404"), {"isrc": ISRC}, None, t, [NEW]
    )
    assert c.replacement_url == NEW
    assert c.status == "redirect"
    # Same artist/title with a different ISRC is a different interpretation.
    t.responses[NEW] = Response(200, NEW, page(NEW, "GBLLH2588620"))
    c = recover(
        Check(OLD, "unavailable", NOW, "HTTP 404"), {"isrc": ISRC}, None, t, [NEW]
    )
    assert not c.replacement_url
    second = "https://tidal.com/track/789"
    t.responses[NEW] = Response(200, NEW, page(NEW))
    t.responses[second] = Response(200, second, page(second))
    c = recover(
        Check(OLD, "unavailable", NOW, "HTTP 404"),
        {"isrc": ISRC},
        None,
        t,
        [NEW, second],
    )
    assert c.status == "uncertain"
    assert "Multiple identity matches" in c.reason
    assert not c.replacement_url


def test_cannot_replace_album_with_track_or_title_match():
    album = "https://tidal.com/album/1"
    t = Fake({NEW: Response(200, NEW, page(NEW))})
    c = recover(
        Check(album, "unavailable", NOW, "HTTP 404"),
        {"title": "Concerto"},
        None,
        t,
        [NEW],
    )
    assert not c.replacement_url
    assert not t.calls


def test_shared_links_inventory_and_history_do_not_promote(tmp_path):
    p = fixture(tmp_path)
    fixture(tmp_path, name="two", list_links=True)
    before = p.read_bytes()
    t = Fake({OLD: Response(404, OLD)})
    candidates = [
        {"work_id": "work1", "profile": None, "url": NEW, "source": "issue:example"},
        {"work_id": "work1", "profile": "piano", "url": "wrong-category"},
    ]
    report = run(tmp_path, t, candidates=candidates)
    assert t.calls == [OLD]
    assert len(report["performances"]) == 2
    assert all(
        r["previous_candidates"] == candidates[:1] for r in report["performances"]
    )
    assert "no recommendation changed" in markdown(report)
    assert p.read_bytes() == before
    assert report["updated_files"] == 0


def test_recovery_apply_changes_only_locator_in_both_yaml_shapes(tmp_path):
    paths = [fixture(tmp_path), fixture(tmp_path, name="two", list_links=True)]
    before = [YAML(typ="safe").load(p.read_text()) for p in paths]
    prior = {"checks": [{"url": OLD, "identity": {"isrc": ISRC}}]}
    t = Fake({OLD: Response(404, OLD), NEW: Response(200, NEW, page(NEW))})
    report = run(tmp_path, t, previous=prior, recovery_urls={OLD: [NEW]}, apply=True)
    assert report["updated_files"] == 2
    for path, old in zip(paths, before):
        new = YAML(typ="safe").load(path.read_text())
        if isinstance(old["links"], list):
            old["links"][0]["url"] = NEW
        else:
            old["links"]["tidal"]["url"] = NEW
        assert new == old
        assert "status" not in path.read_text()


def test_stale_fingerprint_not_reused_for_changed_locator(tmp_path):
    fixture(tmp_path, url=NEW)
    t = Fake({NEW: Response(404, NEW)})
    report = run(
        tmp_path, t, previous={"checks": [{"url": OLD, "identity": {"isrc": ISRC}}]}
    )
    assert report["checks"][0]["identity"] == {}
    assert not report["checks"][0]["replacement_url"]


def test_keeps_original_snapshot_through_unverified_changed_id(tmp_path):
    fixture(tmp_path)
    t = Fake(
        {
            OLD: Response(200, NEW, page(NEW, "GBLLH2588620")),
            NEW: Response(200, NEW, page(NEW, "GBLLH2588620")),
        }
    )
    r = run(
        tmp_path, t, previous={"checks": [{"url": OLD, "identity": {"isrc": ISRC}}]}
    )
    assert r["checks"][0]["identity"]["isrc"] == ISRC
    assert not r["checks"][0]["replacement_url"]


def test_concurrent_edit_refused_before_any_writes(tmp_path):
    first = fixture(tmp_path)
    second = fixture(tmp_path, name="two")
    records = inventory(tmp_path)
    second.write_text(second.read_text() + "\nnotes2: external edit\n")
    original = first.read_bytes()
    with pytest.raises(ValueError, match="changed during check"):
        apply_updates(
            tmp_path,
            records,
            {OLD: Check(OLD, "redirect", NOW, "", replacement_url=NEW)},
        )
    assert first.read_bytes() == original


def test_api_filters_country_caches_and_recovers_album_barcode(tmp_path):
    album, replacement = "https://tidal.com/album/12", "https://tidal.com/album/34"
    base = "https://openapi.tidal.com/v2/"
    resource_data = lambda rid: {
        "data": {
            "id": rid,
            "type": "albums",
            "attributes": {"barcodeId": "0196589525444", "title": "Accepted album"},
        }
    }
    search = base + "albums?countryCode=NL&filter%5BbarcodeId%5D=0196589525444"
    t = Fake(
        {
            album: Response(404, album),
            replacement: Response(200, replacement, page(replacement)),
            base + "albums/12?countryCode=NL": Response(
                200, "", json.dumps(resource_data("12"))
            ),
            base + "albums/34?countryCode=NL": Response(
                200, "", json.dumps(resource_data("34"))
            ),
            search: Response(
                200, "", json.dumps({"data": [resource_data("34")["data"]]})
            ),
        }
    )
    fixture(tmp_path, url=album)
    api = TidalAPI(t, "secret-not-to-persist", "NL")
    report = run(tmp_path, t, api=api)
    assert report["checks"][0]["replacement_url"] == replacement
    assert "secret-not-to-persist" not in json.dumps(report)
    api.identity(album)
    assert t.calls.count(base + "albums/12?countryCode=NL") == 1


def test_api_partial_result_cannot_establish_uniqueness():
    url = "https://openapi.tidal.com/v2/tracks?countryCode=NL&filter%5Bisrc%5D=" + ISRC
    api = TidalAPI(
        Fake(
            {
                url: Response(
                    200, "", json.dumps({"data": [], "links": {"next": "other-page"}})
                )
            }
        ),
        "secret",
        "NL",
    )
    with pytest.raises(ValueError, match="paginated"):
        api.candidates(OLD, {"isrc": ISRC})


def test_api_missing_credentials_is_explicit(monkeypatch):
    monkeypatch.delenv("TIDAL_ACCESS_TOKEN", raising=False)
    with pytest.raises(SystemExit) as e:
        main(["--use-api"])
    assert e.value.code == 2


def test_legacy_album_track_path_preserves_track_identity():
    url = "https://tidal.com/album/12/track/123"
    assert resource(url) == ("track", "123")
    c = check_url(url, Fake({OLD: Response(200, OLD, page())}), NOW)
    assert c.status == "redirect" and c.replacement_url == OLD


def test_malformed_port_and_empty_input_not_fetched():
    assert resource("https://tidal.com:bad/track/123") is None
    assert resource(None) is None


def test_partial_run_retains_unchecked_fingerprints(tmp_path):
    fixture(tmp_path)
    snapshot = {"fingerprints": {NEW: {"isrc": ISRC}}}
    r = run(
        tmp_path, Fake({OLD: Response(200, OLD, page())}), previous=snapshot, limit=1
    )
    assert r["fingerprints"][NEW]["isrc"] == ISRC
    assert r["fingerprints"][OLD]["isrc"] == ISRC


def test_missing_snapshot_cannot_use_candidate_title_only(tmp_path):
    fixture(tmp_path)
    t = Fake({OLD: Response(404, OLD)})
    r = run(tmp_path, t, recovery_urls={OLD: [NEW]})
    assert r["checks"][0]["status"] == "unavailable"
    assert not r["checks"][0]["replacement_url"]
    assert t.calls == [OLD]


@pytest.mark.parametrize("history", ["invalid", {}])
def test_invalid_candidate_history_rejected(tmp_path, history):
    fixture(tmp_path)
    with pytest.raises(ValueError, match="Previous candidates"):
        run(tmp_path, Fake({}), candidates=history)


def test_no_inventory_directory_is_configuration_error(tmp_path):
    with pytest.raises(ValueError, match="Repository root"):
        run(tmp_path, Fake({}))


@pytest.mark.parametrize("output", ["report.md", "data/reports.json"])
def test_output_cannot_overwrite_markdown_or_canonical_data(tmp_path, output):
    with pytest.raises(SystemExit) as e:
        main(["--repo-root", str(tmp_path), "--output", str(tmp_path / output)])
    assert e.value.code == 2


def test_external_redirect_is_refused_before_following():
    from urllib.request import Request

    from classical_music.tidal_maintenance import SafeRedirects

    with pytest.raises(ValueError, match="supported Tidal"):
        SafeRedirects().redirect_request(
            Request(OLD), None, 302, "Moved", {}, "https://example.com/track/123"
        )


def test_url_update_preserves_comments_and_quoted_editorial_fields(tmp_path):
    path = fixture(tmp_path)
    text = path.read_text().replace(
        "notes: Trusted editorial meaning",
        'notes: "Trusted editorial meaning" # retained explanation',
    )
    path.write_text("# curator header\n" + text)
    t = Fake({OLD: Response(200, OLD, page())})
    # Equivalent legacy HTTP locator is the only changed canonical value.
    path.write_text(path.read_text().replace(OLD, "http://www.tidal.com/track/123"))
    r = run(tmp_path, t, apply=True)
    assert r["updated_files"] == 1
    assert "# curator header" in path.read_text()
    assert '"Trusted editorial meaning" # retained explanation' in path.read_text()


# --- Hourly rotation ledger and escalation (issue #64) ---

import subprocess
import sys

from classical_music.tidal_maintenance import (
    comment_body,
    escalation_actions,
    issue_body,
    load_state,
    marker,
    merge_state,
    select_due,
)

SECOND = "https://tidal.com/track/999"


def _ledger(
    url=OLD,
    status="unavailable",
    strikes=1,
    checked="2026-10-01T00:00:00+00:00",
):
    return {
        "version": 1,
        "urls": {
            url: {"last_checked": checked, "status": status, "strikes": strikes}
        },
    }


def _round_report(url=OLD, status="unavailable", reason="HTTP 404", now=NOW):
    return {
        "checks": [
            {
                "url": url,
                "status": status,
                "reason": reason,
                "last_checked": now,
                "final_url": "",
                "replacement_url": "",
                "evidence": "",
                "identity": {},
            }
        ],
        "performances": [
            {
                "performance_id": "one",
                "work_id": "work1",
                "profile": None,
                "path": "data/performances/one.yaml",
                "url": url,
                "status": status,
                "last_checked": now,
            }
        ],
    }


def test_select_due_prefers_never_checked_then_least_recent():
    state = _ledger(url=SECOND, status="ok", strikes=0)
    state["urls"][OLD] = {
        "last_checked": "2026-09-01T00:00:00+00:00",
        "status": "ok",
        "strikes": 0,
    }
    fresh = "https://tidal.com/track/777"
    assert select_due([SECOND, OLD, fresh], state, 3) == [fresh, OLD, SECOND]
    with pytest.raises(ValueError, match="at least 1"):
        select_due([OLD], state, 0)


def test_merge_state_counts_consecutive_problems_and_resets_on_status_change():
    merged = merge_state(_ledger(url=OLD, status="unavailable", strikes=2), _round_report(status="unavailable"))
    assert merged["urls"][OLD]["strikes"] == 3
    merged = merge_state(merged, _round_report(status="ok"))
    assert merged["urls"][OLD]["strikes"] == 0
    assert merged["urls"][OLD]["status"] == "ok"
    report = _round_report(status="redirect")
    report["checks"][0]["replacement_url"] = NEW
    merged = merge_state(_ledger(url=OLD, status="ok", strikes=0), report)
    assert merged["urls"][NEW] == merged["urls"][OLD]


def test_load_state_rejects_malformed_ledgers(tmp_path):
    absent = tmp_path / "absent.json"
    assert load_state(absent) == {"version": 1, "urls": {}}
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_state(bad)
    bad.write_text("[]")
    with pytest.raises(ValueError, match="urls mapping"):
        load_state(bad)
    bad.write_text(
        json.dumps(
            {
                "version": 1,
                "urls": {
                    OLD: {"last_checked": NOW, "status": "ok"},
                },
            }
        )
    )
    with pytest.raises(ValueError, match="malformed URL entry"):
        load_state(bad)
    bad.write_text(
        json.dumps(
            {
                "version": 1,
                "urls": {
                    OLD: {"last_checked": NOW, "status": "ok", "strikes": -1},
                },
            }
        )
    )
    with pytest.raises(ValueError, match="malformed URL entry"):
        load_state(bad)


def test_run_only_checks_requested_urls_and_rejects_unknown(tmp_path):
    fixture(tmp_path)
    fixture(tmp_path, name="two", url=NEW)
    t = Fake({OLD: Response(200, OLD, page())})
    r = run(tmp_path, t, only=[OLD])
    assert t.calls == [OLD]
    assert r["checked_unique_urls"] == 1
    with pytest.raises(ValueError, match="unknown Tidal URLs"):
        run(tmp_path, Fake({}), only=["https://tidal.com/track/404404"])


def test_cli_rotation_checks_least_recently_checked(tmp_path, monkeypatch):
    fixture(tmp_path)
    fixture(tmp_path, name="two", url=NEW)
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps(_ledger(url=NEW, status="ok", strikes=0))
    )
    t = Fake({OLD: Response(200, OLD, page())})
    monkeypatch.setattr(
        "classical_music.tidal_maintenance.Transport", lambda *a, **k: t
    )
    code = main(
        [
            "--repo-root", str(tmp_path),
            "--output", str(tmp_path / "latest.json"),
            "--state", str(state),
            "--limit", "1",
        ]
    )
    assert code == 0
    assert t.calls == [OLD]
    merged = load_state(state)
    assert merged["urls"][OLD]["status"] == "ok"
    assert merged["urls"][NEW]["status"] == "ok"


def test_cli_state_requires_limit_and_stays_outside_canonical_data(tmp_path):
    fixture(tmp_path)
    for argv in (
        [
            "--repo-root", str(tmp_path),
            "--output", str(tmp_path / "o.json"),
            "--state", str(tmp_path / "s.json"),
        ],
        [
            "--repo-root", str(tmp_path),
            "--output", str(tmp_path / "o.json"),
            "--state", str(tmp_path / "data" / "s.json"),
            "--limit", "1",
        ],
        [
            "--repo-root", str(tmp_path),
            "--output", str(tmp_path / "o.json"),
            "--state", str(tmp_path / "s.txt"),
            "--limit", "1",
        ],
    ):
        with pytest.raises(SystemExit) as e:
            main(argv)
        assert e.value.code == 2


def test_escalation_thresholds_separate_missing_from_stubborn_uncertainty():
    assert len(
        escalation_actions(
            _round_report(status="unavailable"), _ledger(url=OLD, status="unavailable", strikes=1)
        )
    ) == 1
    assert len(
        escalation_actions(
            _round_report(status="uncertain"), _ledger(url=OLD, status="uncertain", strikes=3)
        )
    ) == 1
    assert (
        escalation_actions(
            _round_report(status="uncertain"), _ledger(url=OLD, status="uncertain", strikes=2)
        )
        == []
    )
    assert (
        escalation_actions(
            _round_report(status="ok"), _ledger(url=OLD, status="ok", strikes=9)
        )
        == []
    )
    with pytest.raises(ValueError, match="uncertain_after"):
        escalation_actions(_round_report(), _ledger(url=OLD), uncertain_after=0)


def test_issue_and_comment_bodies_are_dutch_curator_reviews():
    state = _ledger(url=OLD, status="unavailable", strikes=2)
    action = escalation_actions(_round_report(), state)[0]
    assert marker(OLD) == "<!-- tidal-link: " + OLD + " -->"
    body = issue_body(action)
    assert body.startswith(marker(OLD))
    assert "`one`" in body
    assert "data/performances/one.yaml" in body
    assert "geen enkele kandidaat wordt automatisch gepromoveerd" in body
    comment = comment_body(action)
    assert comment.startswith(marker(OLD))
    assert "opeenvolgende problemen: 2" in comment


def test_escalate_script_dry_run_needs_no_token_and_reports_actions(tmp_path):
    root = Path(__file__).resolve().parents[1]
    report = tmp_path / "latest.json"
    report.write_text(json.dumps(_round_report()))
    state = tmp_path / "state.json"
    state.write_text(json.dumps(_ledger()))
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    script = root / "scripts" / "escalate_tidal_failures.py"
    out = subprocess.run(
        [sys.executable, str(script), "--report", str(report), "--state", str(state), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert out.returncode == 0, out.stderr
    payload = json.loads(out.stdout)
    assert payload["actions"] == 1
    assert payload["urls"] == [OLD]
    assert payload["dry_run"] is True
    denied = subprocess.run(
        [sys.executable, str(script), "--report", str(report), "--state", str(state)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert denied.returncode == 2
    assert "GITHUB_TOKEN" in denied.stderr
