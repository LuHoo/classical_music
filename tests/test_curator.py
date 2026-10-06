"""Curator decisions, safety boundaries and the PR #300 reference case."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest
from ruamel.yaml import YAML

from classical_music import curator
from classical_music.chamber_import import MANIFEST, check_inventory, occurrence_fingerprint

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def inventory():
    manifest = json.loads((ROOT / MANIFEST).read_text())
    yaml = YAML(typ='safe')
    data = {kind: {} for kind in ('persons', 'work-groups', 'works', 'performances')}
    for kind in data:
        for path in (ROOT / 'data' / kind).glob('*.yaml'):
            record = yaml.load(path.read_text())
            data[kind][record['id']] = record
    return manifest, data


def apply_to_inventory(changes, inventory):
    manifest, data = deepcopy(inventory)
    yaml = YAML(typ='safe')
    manifest = json.loads(changes[str(MANIFEST)])
    for path, content in changes.items():
        if path.startswith('data/performances/'):
            if content is None:
                del data['performances'][Path(path).stem]
            else:
                p = yaml.load(content)
                data['performances'][p['id']] = p
    check_inventory(manifest, data)
    return manifest, data


@pytest.mark.parametrize('issue,choice', [(246, 'C093'), (247, 'C331'), (242, 'C400'),
                                         (242, 'existing'), (257, 'existing'), (252, 'C230')])
def test_generic_selection_and_source_preservation(issue, choice, inventory):
    changes, record, _ = curator.plan_decision(ROOT, issue, choice, curator='Test', replace_existing=True)
    manifest, data = apply_to_inventory(changes, inventory)
    before = [t for u in inventory[0]['units'] for t in u['tracks']]
    after = [t for u in manifest['units'] for t in u['tracks']]
    assert before == after
    assert occurrence_fingerprint(before) == occurrence_fingerprint(after)
    resolved, done = curator.find_choice(manifest, issue)
    assert done and record['performance_id'] in data['performances']
    assert len([p for p in data['performances'].values() if p['work_id'] == resolved['work_id']]) == 1
    if issue == 252:
        assert data['performances'][record['performance_id']]['excerpt'] == 'Movements I and II only'
        assert record['replaced_performances']


@pytest.mark.parametrize('issue,choice,message', [(9999, 'A', 'registered'), (246, 'Z', 'Unknown'),
    (246, 'A', 'Unknown'), (240, 'B', 'different'), (244, 'C069', 'different'),
    (246, 'geen', 'Unknown'), (246, 'unresolved', 'Unknown')])
def test_reject_invalid_or_ambiguous_decisions(issue, choice, message):
    with pytest.raises(curator.CuratorError, match=message):
        curator.plan_decision(ROOT, issue, choice, curator='Test')


def test_replacement_requires_explicit_flag():
    with pytest.raises(curator.CuratorError, match='replace-existing'):
        curator.plan_decision(ROOT, 242, 'C035', curator='Test')


def test_wrong_issue_comment_rejected():
    with pytest.raises(curator.CuratorError, match='this issue'):
        curator.plan_decision(ROOT, 246, 'C093', curator='Test', decision_url=curator.ISSUES+'240#issuecomment-1')


def test_alias_does_not_depend_on_unit_order():
    manifest = json.loads((ROOT / MANIFEST).read_text())
    choice, _ = curator.find_choice(manifest, 240)
    choice['units'].reverse()
    assert curator.resolve_choice(choice, 'A') == 'C003'
    assert curator.resolve_choice(choice, 'b') == 'C287'


def test_240_retry_preserves_legacy_record():
    changes, record, _ = curator.plan_decision(ROOT, 240, 'A', curator='Test')
    assert changes == {}
    assert record['playlist_change']['removed_track_ids'] == ['12423579', '12423580', '12423581', '12423582']
    assert record['implementation_pr'].endswith('/300')


@pytest.fixture
def checkout(tmp_path):
    for directory in ('data', 'reports/curator-decisions', str(MANIFEST.parent)):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    return tmp_path


def tracked_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def reset_240(root):
    manifest = json.loads((root / MANIFEST).read_text())
    choice, _ = curator.find_choice(manifest, 240)
    pid = choice['decision']['performances'][0]['performance_id']
    manifest['resolved_choices'].remove(choice)
    choice['decision'] = None
    manifest['recommendation_choices'].append(choice)
    manifest['new_records'] = [r for r in manifest['new_records'] if r['id'] != pid]
    for u in manifest['units']:
        if u['unit_id'] in choice['units']:
            u.update(disposition='recommendation_choice', review_classification='curator_required', reason='Pending')
            u.pop('performance_id', None)
            u.pop('curator_decision', None)
    curator.refresh_summary(manifest)
    (root / MANIFEST).write_bytes(curator.json_bytes(manifest))
    (root / 'data/performances' / (pid + '.yaml')).unlink()


def test_pr300_preview_apply_retry_and_playlist_done(checkout):
    reset_240(checkout)
    before = tracked_bytes(checkout)
    output = curator.execute(checkout, 240, 'A', playlist_remove=True, curator='Lucas')
    assert tracked_bytes(checkout) == before
    assert 'Preview only' in output and 'Janet Hilton' in output and '12423582' in output
    curator.execute(checkout, 240, 'A', apply=True, playlist_remove=True, curator='Lucas')
    record_path = checkout / 'reports/curator-decisions/issue-240.json'
    record = json.loads(record_path.read_text())
    assert record['selected_units'] == ['C003'] and record['not_selected_units'] == ['C287']
    assert record['playlist_change']['status'] == 'pending'
    pid = record['performance_id']
    yaml = YAML(typ='safe')
    actual = yaml.load((checkout / 'data/performances' / (pid+'.yaml')).read_text())
    reference = yaml.load((ROOT / 'data/performances' / (pid+'.yaml')).read_text())
    actual['source']['curator_decision'] = reference['source']['curator_decision']
    assert actual == reference  # same canonical output as PR #300
    after = tracked_bytes(checkout)
    assert 'Already recorded' in curator.execute(checkout, 240, 'A', apply=True, curator='Lucas')
    assert tracked_bytes(checkout) == after
    with pytest.raises(curator.CuratorError, match='different'):
        curator.execute(checkout, 240, 'B', apply=True, curator='Lucas')
    with pytest.raises(curator.CuratorError, match='--note'):
        curator.execute(checkout, 240, 'playlist-done', apply=True, curator='Lucas')
    assert tracked_bytes(checkout) == after
    curator.execute(checkout, 240, 'playlist-done', curator='Lucas', note='Checked all four IDs and kept A')
    assert tracked_bytes(checkout) == after
    curator.execute(checkout, 240, 'playlist-done', apply=True, curator='Lucas', note='Checked all four IDs and kept A')
    action = json.loads(record_path.read_text())['playlist_change']
    assert action['status'] == 'done' and action['verification_type'] == 'curator_reported'
    assert action['removed_track_ids'] == ['12423579', '12423580', '12423581', '12423582']
    after = tracked_bytes(checkout)
    curator.execute(checkout, 240, 'playlist-done', apply=True, curator='Lucas')
    assert tracked_bytes(checkout) == after


def test_validation_failure_writes_nothing(checkout, monkeypatch):
    before = tracked_bytes(checkout)
    def fail(root):
        raise RuntimeError('Invalid staged publication')
    monkeypatch.setattr(curator, 'audit', fail)
    with pytest.raises(RuntimeError, match='Invalid staged'):
        curator.execute(checkout, 246, 'C093', apply=True, curator='Test')
    assert tracked_bytes(checkout) == before


def test_local_decision_record_must_match_manifest(checkout):
    changes, _, _ = curator.plan_decision(checkout, 246, 'C093', curator='Test')
    for path, content in changes.items():
        target = checkout / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    record_path = checkout / 'reports/curator-decisions/issue-246.json'
    record = json.loads(record_path.read_text())
    record['selected_units'] = ['C372']
    record_path.write_bytes(curator.json_bytes(record))
    with pytest.raises(AssertionError):
        curator.audit(checkout)


def test_apply_lock(checkout):
    (checkout / '.curator.lock').touch()
    with pytest.raises(curator.CuratorError, match='Another curator'):
        curator.execute(checkout, 246, 'C093', apply=True)
    assert (checkout / '.curator.lock').exists()


def test_concurrent_change_and_write_failure_rollback(tmp_path, monkeypatch):
    (tmp_path / 'a').write_bytes(b'old')
    with pytest.raises(curator.CuratorError, match='changed during'):
        curator.install_changes(tmp_path, {'a': b'new'}, {'a': b'stale'})
    original = curator.os.replace
    def fail_on_b(source, target):
        if target.name == 'b':
            raise OSError('disk failure')
        original(source, target)
    monkeypatch.setattr(curator.os, 'replace', fail_on_b)
    with pytest.raises(OSError, match='disk failure'):
        curator.install_changes(tmp_path, {'a': b'new', 'b': b'new'}, {'a': b'old', 'b': None})
    assert (tmp_path / 'a').read_bytes() == b'old'
    assert not (tmp_path / 'b').exists()


def test_paths_cannot_escape(tmp_path):
    with pytest.raises(curator.CuratorError, match='Unsafe'):
        curator.safe_path(tmp_path, '../../elsewhere')


def test_ambiguous_removal_ids_require_manual_review(tmp_path, inventory):
    manifest = deepcopy(inventory[0])
    units = {u['unit_id']: u for u in manifest['units']}
    units['C372']['tracks'][0]['id'] = units['C093']['tracks'][0]['id']
    (tmp_path / MANIFEST).parent.mkdir(parents=True)
    (tmp_path / MANIFEST).write_bytes(curator.json_bytes(manifest))
    (tmp_path / 'data/performances').mkdir(parents=True)
    with pytest.raises(curator.CuratorError, match='shares track IDs'):
        curator.plan_decision(tmp_path, 246, 'C093', curator='Test', playlist_remove=True)


def test_cli_defaults_to_preview_and_rejects_conflicting_modes(monkeypatch, capsys):
    calls = []
    def execute(*args, **kwargs):
        calls.append((args, kwargs))
        return 'preview'
    monkeypatch.setattr(curator, 'execute', execute)
    assert curator.main(['246', 'C093']) == 0
    assert calls[0][1]['apply'] is False
    with pytest.raises(SystemExit) as error:
        curator.main(['246', 'C093', '--dry-run', '--apply'])
    assert error.value.code == 2 and len(calls) == 1


def test_confirmation_requires_a_recorded_playlist_action(tmp_path):
    manifest = json.loads((ROOT / MANIFEST).read_text())
    choice, _ = curator.find_choice(manifest, 240)
    (tmp_path / MANIFEST).parent.mkdir(parents=True)
    (tmp_path / MANIFEST).write_bytes(curator.json_bytes(manifest))
    path = tmp_path / choice['decision']['implementation_record']
    path.parent.mkdir(parents=True)
    record = json.loads((ROOT / choice['decision']['implementation_record']).read_text())
    record.pop('playlist_change')
    path.write_bytes(curator.json_bytes(record))
    with pytest.raises(curator.CuratorError, match='No manual playlist'):
        curator.plan_playlist_done(tmp_path, 240, curator='Test', note='done')
