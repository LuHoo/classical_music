#!/usr/bin/env python3
"""Audit the reviewed Best Classical window without API access or canonical writes."""

import json
from collections import Counter
from html import escape
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]


from classical_music.publication_site import PublicationSiteGenerator


def audit(manifest_path: Path, root: Path = ROOT) -> dict:
    root = root.resolve()
    manifest = json.loads(manifest_path.read_text())
    window = manifest["window"]
    units = manifest["units"]
    positions = [p for unit in units for p in unit["positions"]]
    assert sorted(positions) == list(range(window["start"], window["end"] + 1))
    assert len(positions) == window["selected_tracks"] == window["end"] - window["start"] + 1
    yaml = YAML(typ="safe")
    data = {}
    for entity in ("persons", "work-groups", "works", "performances"):
        data[entity] = {}
        for path in (root / "data" / entity).rglob("*.yaml"):
            record = yaml.load(path.read_text())
            assert record["id"] not in data[entity], record["id"]
            data[entity][record["id"]] = record
    new_ids = {r["id"] for r in manifest["new_records"]}
    manifest_file = str(manifest_path.resolve().relative_to(root))
    changed_ids = {r["id"] for r in manifest["changed_existing"]}
    for performance in data["performances"].values():
        if performance.get("source", {}).get("file") == manifest_file:
            assert performance["id"] in new_ids | changed_ids, performance["id"]
    for record in manifest["new_records"] + manifest["changed_existing"]:
        if record.get("action") == "removed_by_curator":
            assert record["id"] not in data[record.get("entity", record.get("entity_type"))]
            continue
        saved = yaml.load((root / record["path"]).read_text())
        assert saved["id"] == record["id"]
    from classical_music.playlist_choices import validate_choices
    validate_choices(manifest, data, root)
    generated = PublicationSiteGenerator(root).generate()
    counts = Counter()
    new_performances = set()
    reused_performances = set()
    for unit in units:
        status = unit["disposition"]
        counts[status] += len(unit["positions"])
        assert [t["position"] for t in unit["tracks"]] == unit["positions"]
        assert all(t["id"] and t["title"] and t["isrc"] for t in unit["tracks"])
        if status in {"identity_unresolved", "excluded_nonmusical"}:
            assert not unit.get("performance_id") and unit["reason"]
            continue
        work = data["works"][unit["work_id"]]
        composer = data["persons"][work["composer_id"]]
        assert composer["name"] == unit["composer"], (unit["positions"], composer)
        assert work["work_group_id"] in data["work-groups"]
        if status == "not_selected":
            assert not unit.get("performance_id")
            continue
        if status == "recommendation_choice":
            assert not unit.get("performance_id") and unit["reason"]
            assert not any(
                perf["work_id"] == work["id"] and perf["id"] in new_ids
                for perf in data["performances"].values()
            )
            continue
        performance = data["performances"][unit["performance_id"]]
        assert performance["work_id"] == work["id"]
        assert performance["performers"]
        page = (generated.output_dir / "works" / f"{work['id']}.md").read_text()
        if status == "import_new":
            assert performance["id"] in new_ids
            new_performances.add(performance["id"])
            expected_url = "https://tidal.com/track/" + unit.get("listening_track_id", unit["tracks"][0]["id"])
            assert performance["links"]["tidal"]["url"] == expected_url
            assert expected_url in page
            assert performance.get("excerpt") == unit.get("excerpt")
            if unit.get("excerpt"):
                assert escape(unit["excerpt"]) in page
            assert performance.get("version_assignment") == unit.get(
                "version_assignment"
            )
            assert "year" not in performance  # Release dates are not session dates.
            source = work.get("source", {})
            independent_url = source.get("url", "")
            independent_file = source.get("file", "")
            assert (
                independent_url and "tidal.com" not in independent_url
            ) or (
                (independent_file.startswith("docs/") or independent_file.startswith("side materials/"))
                and (root / independent_file).is_file()
            ), (unit["positions"], source)
        else:
            assert status == "reuse_existing" and unit["evidence"]
            if match := unit.get("recording_match"):
                assert match["selected_positions"]
                selected = [t for t in unit["tracks"] if t["position"] in match["selected_positions"]]
                assert len(selected) == len(match["selected_positions"])
                if match["match"] == "exact_recording_isrc":
                    assert all(t["isrc"] == match["reference_isrc"] for t in selected)
                elif match["match"] == "exact_trusted_track":
                    assert all(t["id"] == match["reference_track_id"] for t in selected)
                else:
                    assert match["match"] == "trusted_album_and_compatible_catalogue"
                    assert all(match["reference_album_id"] in t["album_ids"] for t in selected)
            if performance["id"] in changed_ids and unit.get("excerpt"):
                assert performance.get("excerpt") == unit["excerpt"]
                assert escape(unit["excerpt"]) in page
            reused_performances.add(performance["id"])
    assert dict(counts) == manifest["counts"]["track_dispositions"]
    assert len(new_performances) == manifest["counts"]["new_records"]["performances"]
    assert (
        len(reused_performances)
        == manifest["counts"].get("existing_performances_unique", manifest["counts"]["unit_dispositions"]["reuse_existing"])
    )
    if manifest["source"].get("source_complete") and window["end"] == manifest["source"]["playlist_tracks"]:
        assert manifest["next_boundary"] is None
    else:
        assert manifest["next_boundary"]["position"] == window["end"] + 1
    return {
        "selected_tracks": len(positions),
        "track_dispositions": dict(counts),
        "new_performances_verified": len(new_performances),
        "existing_performances_verified": len(reused_performances),
        "public_links_and_excerpts_verified": True,
        "publication_pages": generated.page_count,
        "publication_composers": generated.composer_count,
        "publication_works": generated.work_count,
    }


def audit_decisions(manifest_path: Path, root: Path = ROOT) -> dict:
    """Validate registered decisions without re-auditing historical unrelated imports.

Legacy windows can refer to recommendations removed by subsequent reviewed work.
The standalone audit remains strict; the CLI validates current registered choices,
window accounting and the complete current canonical/publication dataset.
"""
    from classical_music.playlist_choices import validate_choices
    root = root.resolve()
    manifest = json.loads(manifest_path.read_text())
    units, window = manifest['units'], manifest['window']
    positions = [p for u in units for p in u['positions']]
    assert sorted(positions) == list(range(window['start'], window['end'] + 1))
    assert len(positions) == window['selected_tracks']
    assert dict(Counter(u['disposition'] for u in units)) == manifest['counts']['unit_dispositions']
    assert dict(Counter(u['disposition'] for u in units for _ in u['tracks'])) == manifest['counts']['track_dispositions']
    for unit in units:
        assert unit['positions'] == [t['position'] for t in unit['tracks']]
    yaml = YAML(typ='safe')
    data = {}
    for kind in ('persons', 'work-groups', 'works', 'performances'):
        data[kind] = {}
        for path in (root / 'data' / kind).glob('*.yaml'):
            record = yaml.load(path.read_text())
            assert record['id'] not in data[kind]
            data[kind][record['id']] = record
    validate_choices(manifest, data, root)
    generated = PublicationSiteGenerator(root).generate()
    by_id = {u['unit_id']: u for u in units if u.get('unit_id')}
    for choice in manifest.get('resolved_choices', []):
        for uid in choice['units']:
            unit = by_id[uid]
            work = data['works'][unit['work_id']]
            assert data['persons'][work['composer_id']]['name'] == unit['composer']
            assert work['work_group_id'] in data['work-groups']
            assert all(t['id'] and t['title'] and t['isrc'] for t in unit['tracks'])
            if unit['disposition'] == 'not_selected':
                assert not unit.get('performance_id')
                continue
            perf = data['performances'][unit['performance_id']]
            assert perf['work_id'] == work['id'] and perf['performers']
            if unit['disposition'] == 'import_new':
                assert perf['id'] in {r['id'] for r in manifest['new_records']}
                assert perf['links']['tidal']['url'] == 'https://tidal.com/track/' + unit.get('listening_track_id', unit['tracks'][0]['id'])
                assert perf.get('excerpt') == unit.get('excerpt')
                assert perf.get('profile') == unit.get('profile')
                assert perf.get('version_assignment') == unit.get('version_assignment')
                assert perf['source']['file'] == str(manifest_path.resolve().relative_to(root))
                source = work.get('source', {})
                assert (source.get('url') and 'tidal.com' not in source['url']) or (
                    source.get('file', '').startswith(('docs/', 'side materials/')) and
                    (root / source['file']).is_file()), 'Missing independent Work evidence'
                page = (generated.output_dir / 'works' / (work['id'] + '.md')).read_text()
                assert perf['links']['tidal']['url'] in page
                if unit.get('excerpt'):
                    assert escape(unit['excerpt']) in page
    return {'window_occurrences': len(positions), 'registered_choices': 'passed',
            'canonical_and_publication_checks': 'passed'}
