"""Regression checks for occurrence accounting and the curator gate."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('piano_audit', ROOT / 'scripts/check_piano_import.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture(scope='module')
def inventory(canonical_records):
    """Real manifest plus the complete real catalog, parsed once per session.

    check_inventory asserts collection-wide properties, so the complete record
    set is required; only the repeated parsing is removed.
    """
    manifest = json.loads((ROOT / audit.MANIFEST).read_text())
    return manifest, {kind: dict(records) for kind, records in canonical_records.items()}


def _work_dispositions(manifest):
    """work_id -> set of dispositions; units without a work_id are skipped,
    matching the audit's u.get('work_id') access pattern."""
    dispositions = {}
    for u in manifest['units']:
        if u.get('work_id'):
            dispositions.setdefault(u['work_id'], set()).add(u['disposition'])
    return dispositions


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


def test_raw_metadata_cannot_be_silently_rewritten(inventory):
    manifest, data = inventory
    manifest['units'][0]['tracks'][0]['title'] = 'Another composition'
    with pytest.raises(AssertionError, match='Raw source metadata changed'):
        audit.check_inventory(manifest, data)


def test_ornamented_nocturne_stays_in_same_curator_choice(inventory):
    manifest, _ = inventory
    units = {u['unit_id']: u for u in manifest['units']}
    assert units['P314']['work_id'] == units['P565']['work_id'] == units['P586']['work_id']
    assert units['P314']['disposition'] == 'import_new'
    assert all(units[c]['disposition'] == 'not_selected' for c in ['P565', 'P586'])
    assert len({units[c]['curator_issue'] for c in ['P314', 'P565', 'P586']}) == 1
    assert len({units[c]['curator_decision'] for c in ['P314', 'P565', 'P586']}) == 1


def test_unlisted_candidate_cannot_bypass_manifest_gate(inventory):
    manifest, data = deepcopy(inventory)
    unit = next(u for u in manifest['units'] if u['disposition'] == 'recommendation_choice')
    data['performances']['unlisted'] = {'id': 'unlisted', 'work_id': unit['work_id']}
    with pytest.raises(AssertionError, match='Pending curator choice leaked'):
        audit.check_inventory(manifest, data)


def test_nonadjacent_movements_keep_selected_opening_anchor(inventory):
    manifest, _ = inventory
    units = {u['unit_id']: u for u in manifest['units']}
    for code in ['P141', 'P265', 'P266', 'P466', 'P699', 'P701']:
        u = units[code]
        assert u['listening_track_id'] in {t['id'] for t in u['tracks']}
        assert u['listening_track_id'] != u['tracks'][0]['id']


def test_rejected_alternative_cannot_reappear_as_recommendation(inventory):
    manifest, data = deepcopy(inventory)
    # The competing-recommendation gate fires from a work's active imported
    # unit, so the rejected alternative must share its work with an
    # import_new unit (e.g. the nocturne alternatives). Issue #319 created
    # the first not_selected unit whose work has no active unit anymore
    # (removed_by_curator); that scenario is covered by the test below.
    dispositions = _work_dispositions(manifest)
    unit = next(u for u in manifest['units']
                if u.get('work_id')
                and u['disposition'] == 'not_selected'
                and 'import_new' in dispositions[u['work_id']])
    data['performances']['unapproved-alternative'] = {'id': 'unapproved-alternative', 'work_id': unit['work_id']}
    with pytest.raises(AssertionError, match='Competing recommendation'):
        audit.check_inventory(manifest, data)


def test_rejected_alternative_of_resolved_decision_cannot_reappear(inventory):
    manifest, data = deepcopy(inventory)
    # Regression for #319: a work whose recommendation was replaced by a
    # resolved curator decision (unit not_selected via removed_by_curator,
    # no active unit left) must also reject a smuggled-in competing
    # performance — via the resolved-decision check.
    dispositions = _work_dispositions(manifest)
    resolved_works = {c['work_id'] for c in manifest['resolved_choices']}
    unit = next(u for u in manifest['units']
                if u.get('work_id')
                and u['disposition'] == 'not_selected'
                and u['work_id'] in resolved_works
                and not (dispositions[u['work_id']] & {'import_new', 'reuse_existing'}))
    data['performances']['unapproved-alternative'] = {'id': 'unapproved-alternative', 'work_id': unit['work_id']}
    with pytest.raises(AssertionError, match='Decision and recommendations differ'):
        audit.check_inventory(manifest, data)


def test_selected_recording_requires_its_curator_decision(inventory):
    manifest, data = deepcopy(inventory)
    choice = next(c for c in manifest['resolved_choices'] if c['decision']['choice'] == 'selected_performance')
    unit = next(u for u in manifest['units'] if u['unit_id'] in choice['decision']['selected_units'])
    unit['curator_decision'] = None
    with pytest.raises(AssertionError, match='Missing curator decision'):
        audit.check_inventory(manifest, data)
