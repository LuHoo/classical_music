"""Regression checks for occurrence accounting and the curator gate."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('chamber_audit', ROOT / 'scripts/check_chamber_import.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture(scope='module')
def inventory():
    manifest = json.loads((ROOT / audit.MANIFEST).read_text())
    yaml = YAML(typ='safe')
    data = {}
    for kind in ('persons', 'work-groups', 'works', 'performances'):
        records = [yaml.load(p.read_text()) for p in (ROOT / 'data' / kind).glob('*.yaml')]
        data[kind] = {r['id']: r for r in records}
    return manifest, data


def test_complete_snapshot_and_curator_gates(inventory):
    audit.check_inventory(*inventory)


def test_source_occurrences_are_not_deduplicated_by_track_id():
    tracks = [{'position': n, 'item_id': f'item-{n}', 'id': 'same-recording', 'isrc': 'same-isrc'} for n in [1, 2]]
    assert audit.occurrence_fingerprint(tracks) != audit.occurrence_fingerprint(tracks[:1])
    assert audit.occurrence_fingerprint(tracks) == audit.occurrence_fingerprint(list(reversed(tracks)))


def test_missing_source_track_fails(inventory):
    manifest, data = inventory
    manifest = deepcopy(manifest)
    manifest['units'][0]['tracks'].pop()
    with pytest.raises(AssertionError, match='source occurrence'):
        audit.check_inventory(manifest, data)


def test_changed_track_identity_fails_even_with_same_position(inventory):
    manifest, data = inventory
    manifest = deepcopy(manifest)
    manifest['units'][0]['tracks'][0]['id'] = 'different-recording'
    with pytest.raises(AssertionError, match='Source identity/order changed'):
        audit.check_inventory(manifest, data)


def test_pending_choice_cannot_become_a_recommendation(inventory):
    manifest, data = deepcopy(inventory)
    unit = next(u for u in manifest['units'] if u['disposition'] == 'recommendation_choice')
    data['performances']['unapproved'] = {'id': 'unapproved', 'work_id': unit['work_id']}
    manifest['new_records'].append({'id': 'unapproved', 'entity': 'performances'})
    with pytest.raises(AssertionError, match='Pending curator choice leaked'):
        audit.check_inventory(manifest, data)


def test_reuse_must_match_the_work_not_just_a_track(inventory):
    manifest, data = deepcopy(inventory)
    unit = next(u for u in manifest['units'] if u['disposition'] == 'reuse_existing')
    data['performances'][unit['performance_id']]['work_id'] = 'another-work'
    with pytest.raises(AssertionError, match='wrong Work'):
        audit.check_inventory(manifest, data)
