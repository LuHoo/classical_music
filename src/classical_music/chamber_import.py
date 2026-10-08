#!/usr/bin/env python3
"""Read-only audit of the complete, reviewed Chamber source intake."""
from __future__ import annotations

import hashlib
import json
from html import escape
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]
from classical_music.publication_site import PublicationSiteGenerator

MANIFEST = Path('reports/playlist-import/chamber/snapshot-2026-10-04.json')


def occurrence_fingerprint(tracks: list[dict]) -> str:
    rows = [[t['position'], t['item_id'], t['id'], t['isrc']]
            for t in sorted(tracks, key=lambda t: t['position'])]
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()


def decision_reference(decision: dict) -> str:
    return decision.get('comment_url') or decision.get('decision_record', '')


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
    resolved = {c['work_id']: c for c in manifest.get('resolved_choices', [])}
    assert not set(choices) & set(resolved), 'Resolved choice still pending'
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
        if status == 'not_selected':
            assert u['work_id'] in resolved and not u.get('performance_id'), 'Unselected candidate became a recommendation'
            decision = resolved[u['work_id']]['decision']
            assert decision['choice'] == 'selected_performance'
            assert u['unit_id'] in decision['not_selected_units']
            assert u['curator_decision'] == decision_reference(decision), 'Missing curator decision'
            assert u['reason'] and u['review_classification'] == 'curator_not_selected'
            continue
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
            assert len([p for p in data['performances'].values() if p['work_id'] == work['id'] and p.get('profile') == perf.get('profile')]) == 1, 'Competing recommendation added without a decision'
            if work['id'] in resolved:
                decision = resolved[work['id']]['decision']
                assert u['curator_decision'] == decision_reference(decision), 'Missing curator decision'
                assert perf['source']['curator_decision'] == decision_reference(decision)
                assert u.get('profile') == perf.get('profile')
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
    for choice in resolved.values():
        decision = choice['decision']
        assert decision['choice'] in ('both_distinct_profiles', 'selected_performance')
        assert (decision_reference(decision).startswith(choice['issue_url'] + '#issuecomment-') or
                decision_reference(decision) == decision.get('implementation_record') and
                decision_reference(decision).startswith('reports/curator-decisions/')), 'Missing curator decision'
        matching = [u for u in units if u.get('work_id') == choice['work_id']]
        assert {u['unit_id'] for u in matching} == set(choice['units'])
        if decision['choice'] == 'selected_performance':
            assert {u['unit_id'] for u in matching if u['disposition'] in ('import_new', 'reuse_existing')} == set(decision['selected_units'])
            assert {u['unit_id'] for u in matching if u['disposition'] == 'not_selected'} == set(decision['not_selected_units'])
            assert len(decision['performances']) == 1
        else:
            assert all(u['disposition'] in ('import_new', 'reuse_existing') for u in matching)
        assigned = decision['performances']
        assert len({p['profile'] for p in assigned}) == len(assigned), 'Duplicate comparison profile'
        actual = [p for p in data['performances'].values() if p['work_id'] == choice['work_id']]
        assert {p['id'] for p in actual} == {p['performance_id'] for p in assigned}, 'Decision and recommendations differ'
        for p in assigned:
            assert data['performances'][p['performance_id']].get('profile') == p['profile']


def validate_decision_records(manifest: dict, root: Path) -> None:
    """Validate local CLI evidence without regenerating unchanged publication."""
    for choice in manifest.get('resolved_choices', []):
        decision = choice['decision']
        if decision.get('decision_record'):
            relative = Path(decision['decision_record'])
            assert not relative.is_absolute() and '..' not in relative.parts
            record = json.loads((root / relative).read_text())
            assert record['issue_url'] == choice['issue_url']
            assert record.get('comment_url') == decision.get('comment_url')
            assert record['selected_units'] == decision['selected_units']
            assert record['not_selected_units'] == decision['not_selected_units']
            assert record['decision_source'] == 'curator_cli' and record['curator']
            assert record['performance_id'] == decision['performances'][0]['performance_id']
            action = record.get('playlist_change')
            if action:
                assert action['playlist_url'] == manifest['source']['url']
                units = {u['unit_id']: u for u in manifest['units']}
                rejected = [units[uid] for uid in decision['not_selected_units']]
                assert action['planned_removed_track_ids'] == [t['id'] for u in rejected for t in u['tracks']]
                assert [a['unit_id'] for a in action['actions']] == decision['not_selected_units']
                for item, unit in zip(action['actions'], rejected):
                    assert item['track_ids'] == [t['id'] for t in unit['tracks']]
                    assert item['performers'] == unit['performers']
                assert action['preserved_selected_track_ids'] == [
                    t['id'] for uid in decision['selected_units'] for t in units[uid]['tracks']]
                assert not set(action['planned_removed_track_ids']) & set(action['preserved_selected_track_ids'])
                assert action['status'] in ('pending', 'done')
                if action['status'] == 'done':
                    assert action['removed_track_ids'] == action['planned_removed_track_ids']
                    assert action['confirmed_by'] and action['verification']
                    assert action['verification_type'] == 'curator_reported'


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
    validate_decision_records(manifest, root)
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
