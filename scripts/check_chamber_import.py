#!/usr/bin/env python3
"""Read-only audit of the complete, reviewed Chamber source intake."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from html import escape
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from classical_music.publication_site import PublicationSiteGenerator

MANIFEST = Path('reports/playlist-import/chamber/snapshot-2026-10-04.json')


def occurrence_fingerprint(tracks: list[dict]) -> str:
    rows = [[t['position'], t['item_id'], t['id'], t['isrc']]
            for t in sorted(tracks, key=lambda t: t['position'])]
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()


def check_inventory(manifest: dict, data: dict) -> None:
    units = manifest['units']
    source = manifest['source']
    tracks = [t for u in units for t in u['tracks']]
    assert source['source_complete'] is True
    assert sorted(t['position'] for t in tracks) == list(range(1, source['track_count'] + 1)), 'Missing/duplicated source occurrence'
    assert occurrence_fingerprint(tracks) == source['ordered_occurrences_sha256'], 'Source identity/order changed'
    assert len({u['unit_id'] for u in units}) == len(units)
    new_ids = {r['id'] for r in manifest['new_records']}
    new_performance_ids = {r['id'] for r in manifest['new_records'] if r['entity'] == 'performances'}
    choices = {c['work_id']: c for c in manifest['recommendation_choices']}
    used_new = set()
    for u in units:
        assert u['positions'] == [t['position'] for t in u['tracks']]
        assert all(t['id'] and t['isrc'] and t['title'] and t['item_id'] for t in u['tracks'])
        status = u['disposition']
        assert status in manifest['summary']
        if status == 'identity_unresolved':
            assert not u.get('work_id') and not u.get('performance_id')
            assert u['reason'] and u['review_classification'] == 'authority_evidence_required'
            continue
        work = data['works'][u['work_id']]
        assert work['composer_id'] == u['composer_id']
        assert work['composer_id'] in data['persons']
        assert work['work_group_id'] in data['work-groups']
        if work['id'] in choices:
            choice = choices[work['id']]
            assert u['unit_id'] in choice['units']
            assert choice['decision'] is None and u['curator_issue'] == choice['issue_url']
            assert not any(p['work_id'] == work['id'] and p['id'] in new_ids for p in data['performances'].values()), 'Pending curator choice leaked into recommendations'
        if status == 'recommendation_choice':
            assert u['work_id'] in choices and not u.get('performance_id')
            assert u['reason'] and u['review_classification'] == 'curator_required'
            continue
        perf = data['performances'][u['performance_id']]
        assert perf['work_id'] == work['id'], 'Recording assigned to the wrong Work'
        if status == 'import_new':
            assert perf['id'] in new_performance_ids
            used_new.add(perf['id'])
            assert len([p for p in data['performances'].values() if p['work_id'] == work['id']]) == 1, 'Competing recommendation added without a decision'
            assert perf['source']['file'] == str(MANIFEST)
            assert perf['links']['tidal']['url'] == 'https://tidal.com/track/' + u['tracks'][0]['id']
            assert perf.get('excerpt') == u.get('excerpt')
            assert perf['performers'] and 'year' not in perf
            evidence = work.get('source', {}) if work['id'] in new_ids else u['evidence'][0]
            assert (evidence.get('url') and 'tidal.com' not in evidence['url']) or evidence.get('file', '').startswith(('docs/', 'side materials/')), 'Missing independent Work evidence'
        else:
            assert status == 'reuse_existing' and perf['id'] not in new_ids
            assert u.get('recording_evidence'), 'Reuse requires recording evidence'
    assert used_new == new_performance_ids, 'Orphan or missing imported Performance'
    for status, summary in manifest['summary'].items():
        selected = [u for u in units if u['disposition'] == status]
        assert summary == {'units': len(selected), 'track_occurrences': sum(len(u['positions']) for u in selected), 'distinct_performances': len({u['performance_id'] for u in selected if u.get('performance_id')})}
    for choice in choices.values():
        matching = [u for u in units if u.get('work_id') == choice['work_id']]
        assert {u['unit_id'] for u in matching} == set(choice['units'])
        assert any(u['disposition'] == 'recommendation_choice' for u in matching)
        assert choice['issue_url'].startswith('https://github.com/LuHoo/classical_music/issues/')


def audit(root: Path = ROOT) -> dict:
    manifest = json.loads((root / MANIFEST).read_text())
    yaml = YAML(typ='safe')
    data = {}
    for kind in ('persons', 'work-groups', 'works', 'performances'):
        data[kind] = {}
        for path in (root / 'data' / kind).rglob('*.yaml'):
            record = yaml.load(path.read_text())
            assert record['id'] not in data[kind]
            data[kind][record['id']] = record
    check_inventory(manifest, data)
    for record in manifest['new_records']:
        assert yaml.load((root / record['path']).read_text())['id'] == record['id']
    generated = PublicationSiteGenerator(root).generate()
    for u in manifest['units']:
        if u['disposition'] != 'import_new':
            continue
        page = (generated.output_dir / 'works' / (u['work_id'] + '.md')).read_text()
        assert 'https://tidal.com/track/' + u['tracks'][0]['id'] in page
        if u.get('excerpt'):
            assert escape(u['excerpt']) in page
    return {'source_occurrences': manifest['source']['track_count'], 'dispositions': manifest['summary'], 'curator_issues': len(manifest['recommendation_choices']), 'canonical_and_publication_checks': 'passed', 'publication_works': generated.work_count}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
