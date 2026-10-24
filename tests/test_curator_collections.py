"""Cross-collection decisions with real snapshots; no Git or network writes."""
import json
from pathlib import Path
import shutil

import pytest
from ruamel.yaml import YAML

from classical_music import curator
from classical_music.playlist_choices import locate
from classical_music.curator_listening import build_plan

ROOT = Path(__file__).resolve().parents[1]
PIANO = Path('reports/playlist-import/piano/snapshot-2026-10-04.json')
WINDOW = Path('reports/playlist-import/best-classical/window-333-1998.json')


@pytest.fixture
def checkout(tmp_path):
    for directory in ('data', 'reports/playlist-import', 'reports/curator-decisions', 'docs', 'side materials'):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    return tmp_path


def write(root, path, document):
    (root / path).write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')


def register_window(root):
    """A reviewed registration fixture, not a decision or fabricated real issue."""
    manifest = json.loads((root / WINDOW).read_text())
    units = [u for u in manifest['units'] if u['positions'] in ([1749], [1754])]
    assert len(units) == 2 and len({u['work_id'] for u in units}) == 1
    for index, unit in enumerate(units):
        unit['unit_id'] = f'BC{index + 1:03}'
        unit['curator_issue'] = curator.ISSUES + '9999'
        # Legacy credited names need reviewed structured performers.
        unit['performers'] = [{'name': name} for name in unit['credited_artists']]
    choice = dict(work_id=units[0]['work_id'], title=units[0]['title'], composer=units[0]['composer'],
                  units=[u['unit_id'] for u in units], existing_performances=[],
                  choice_aliases={'A': 'BC001', 'B': 'BC002'}, issue_url=curator.ISSUES+'9999', decision=None)
    manifest['recommendation_choices'] = [choice]
    write(root, WINDOW, manifest)
    return manifest


def test_piano_preview_apply_batch_retry_and_completion(checkout):
    before = curator.input_snapshot(checkout)
    assert 'Preview only' in curator.execute(checkout, 263, 'P078', curator='Test', playlist_remove=True)
    assert curator.input_snapshot(checkout) == before
    curator.execute(checkout, 263, 'P078', curator='Test', playlist_remove=True, apply=True)
    curator.execute(checkout, 264, 'P182', curator='Test', apply=True)
    after = curator.input_snapshot(checkout)
    assert 'Already recorded' in curator.execute(checkout, 263, 'P078', curator='Test', apply=True)
    assert after == curator.input_snapshot(checkout)
    curator.execute(checkout, 263, 'playlist-done', curator='Test', note='Checked IDs', apply=True)
    manifest = json.loads((checkout / PIANO).read_text())
    assert not manifest['recommendation_choices'] and len(manifest['version_choice_issues']) == 1
    assert '1 pending Work-level issues' in (checkout / PIANO.parent / 'README.md').read_text()
    assert [u['tracks'] for u in manifest['units']] == [u['tracks'] for u in json.loads(before[str(PIANO)])['units']]


def test_best_classical_registered_window_apply_and_listening(checkout):
    before = register_window(checkout)
    plan = build_plan(checkout, {'number': 9999, 'body': ''})
    assert len(plan['candidates']) == 2
    assert 'Preview only' in curator.execute(checkout, 9999, 'A', curator='Test', playlist_remove=True)
    assert json.loads((checkout / WINDOW).read_text()) == before
    curator.execute(checkout, 9999, 'A', curator='Test', playlist_remove=True, apply=True)
    after = json.loads((checkout / WINDOW).read_text())
    assert [u['tracks'] for u in after['units']] == [u['tracks'] for u in before['units']]
    assert after['counts']['track_dispositions']['not_selected'] == 1
    assert not after['recommendation_choices']
    assert 'Current curator status' in (checkout / WINDOW.with_suffix('.md')).read_text()
    curator.execute(checkout, 9999, 'playlist-done', curator='Test', note='Checked both IDs', apply=True)
    assert 'Already recorded' in curator.execute(checkout, 9999, 'A', apply=True)


def test_duplicate_issue_across_collections_rejected(checkout):
    manifest = json.loads((checkout / PIANO).read_text())
    manifest['recommendation_choices'][0]['issue_url'] = curator.ISSUES + '246'
    write(checkout, PIANO, manifest)
    with pytest.raises(ValueError, match='found 2'):
        curator.execute(checkout, 246, 'C093', apply=True)


def test_unregistered_and_research_cases_fail_closed():
    for issue in (9999, 293):
        with pytest.raises(ValueError, match='registered'):
            locate(ROOT, issue)


def test_piano_listening_anchor_preserved(checkout):
    manifest = json.loads((checkout / PIANO).read_text())
    unit = next(u for u in manifest['units'] if u['unit_id'] == 'P182')
    unit['listening_track_id'] = unit['tracks'][-1]['id']
    write(checkout, PIANO, manifest)
    changes, record, _ = curator.plan_decision(checkout, 264, 'P182', curator='Test')
    perf = YAML(typ='safe').load(changes[f"data/performances/{record['performance_id']}.yaml"])
    assert perf['links']['tidal']['url'].endswith('/' + unit['tracks'][-1]['id'])


def test_best_classical_cross_window_candidates_blocked(checkout):
    manifest = register_window(checkout)
    other_path = WINDOW.parent / 'window-1999-4000.json'
    other = json.loads((checkout / other_path).read_text())
    other['units'].append(dict(work_id=manifest['recommendation_choices'][0]['work_id'], disposition='recommendation_choice'))
    write(checkout, other_path, other)
    with pytest.raises(ValueError, match='another window'):
        curator.plan_decision(checkout, 9999, 'A', curator='Test')


def test_best_classical_shared_track_in_other_window_blocks_removal(checkout):
    manifest = register_window(checkout)
    rejected = next(u for u in manifest['units'] if u.get('unit_id') == 'BC002')
    other_path = WINDOW.parent / 'window-1999-4000.json'
    other = json.loads((checkout / other_path).read_text())
    other['units'][0]['tracks'][0]['id'] = rejected['tracks'][0]['id']
    write(checkout, other_path, other)
    with pytest.raises(ValueError, match='shares track IDs'):
        curator.plan_decision(checkout, 9999, 'A', curator='Test', playlist_remove=True)


def test_validation_of_another_intake_sees_concurrent_changes(checkout, monkeypatch):
    original = curator.audit
    def change_other_intake(stage):
        original(stage)
        path = checkout / PIANO
        path.write_text(path.read_text() + '\n')
    monkeypatch.setattr(curator, 'audit', change_other_intake)
    with pytest.raises(ValueError, match='inputs changed'):
        curator.execute(checkout, 246, 'C093', curator='Test', apply=True)
    assert not (checkout / 'reports/curator-decisions/issue-246.json').exists()


@pytest.fixture(scope='module', autouse=True)
def fixed_pending_choices(pending_curator_repository):
    """Production decisions must not change the preconditions of these tests."""
    import sys
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(sys.modules[__name__], 'ROOT', pending_curator_repository)
        yield
