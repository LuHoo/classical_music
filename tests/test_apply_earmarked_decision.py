"""Offline tests for scripts/apply_earmarked_decision.py (earmarked decision route, #316/#318).

Run offline: PYTHONPATH=<repo>/src:<stubs> python3 -m unittest tests.test_apply_earmarked_decision
The fixture reproduces the chamber intake vocabulary; promote tests run the real
chamber_import inventory audit on the modified fixture to prove ./curator
finish compatibility.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / 'scripts' / 'apply_earmarked_decision.py'
FIXTURE_MANIFEST = 'reports/playlist-import/chamber/snapshot-2026-10-04.json'

WORK = 'test-composer-fantasy-in-f-minor'
OTHER = 'test-composer-rondo-in-a-major'
P384 = WORK + '-piano-p384'
NEW_PID = WORK + '-earmarked-cha'


def track(position, ident, title):
    return {'position': position, 'id': ident, 'item_id': 'item-' + ident,
            'title': title, 'isrc': 'ISRC' + ident, 'duration': 'PT1M',
            'artists': ['Murray Perahia'], 'album_titles': ['Test Album'],
            'album_ids': ['1']}


def build_fixture(root: Path):
    (root / 'data/works').mkdir(parents=True)
    (root / 'data/work-groups').mkdir(parents=True)
    (root / 'data/persons').mkdir(parents=True)
    (root / 'data/performances').mkdir(parents=True)
    (root / 'data/recordings').mkdir(parents=True)
    (root / 'docs').mkdir(parents=True)
    (root / 'reports/curator-decisions').mkdir(parents=True)
    (root / 'reports/playlist-import/chamber').mkdir(parents=True)
    (root / 'data/work-groups' / f'{WORK}-group.yaml').write_text(
        f"id: {WORK}-group\ncomposer_id: test-composer\ntitle: Fantasy in F Minor\n")
    (root / 'data/work-groups' / f'{OTHER}-group.yaml').write_text(
        f"id: {OTHER}-group\ncomposer_id: test-composer\ntitle: Rondo in A Major\n")
    (root / 'data/works' / f'{WORK}.yaml').write_text(
        f"id: {WORK}\nwork_group_id: {WORK}-group\ncomposer_id: test-composer\n"
        "title: Fantasy in F Minor\nsource:\n  file: docs/test.md\n  line: '1'\n")
    (root / 'data/works' / f'{OTHER}.yaml').write_text(
        f"id: {OTHER}\nwork_group_id: {OTHER}-group\ncomposer_id: test-composer\n"
        "title: Rondo in A Major\nsource:\n  file: docs/test.md\n  line: '2'\n")
    (root / 'data/persons' / 'test-composer.yaml').write_text(
        "id: test-composer\nname: Test Composer\n")
    (root / 'data/performances' / f'{P384}.yaml').write_text(
        f"id: {P384}\nwork_id: {WORK}\nperformers:\n  - name: Murray Perahia\n    role: piano\n"
        "links:\n  tidal:\n    url: https://tidal.com/track/75254187\n"
        "release:\n  album_title: 'Test Album'\n"
        f"source:\n  file: {FIXTURE_MANIFEST}\n  url: https://tidal.com/playlist/x\n")
    (root / 'data/performances' / f'{OTHER}-piano-p078.yaml').write_text(
        f"id: {OTHER}-piano-p078\nwork_id: {OTHER}\nperformers:\n  - name: Other Pianist\n    role: piano\n"
        "links:\n  tidal:\n    url: https://tidal.com/track/11111111\n"
        f"source:\n  file: {FIXTURE_MANIFEST}\n")
    (root / 'data/recordings' / 'test-recording.yml').write_text(
        "id: test-recording\ntitle: 'Test: Recording'\nlabel: Test Label\nyear: 2026\n"
        f"works:\n- work_id: {WORK}\n  status: candidate\n  track:\n    number: 1\n"
        "    title: 'Fantasy in F Minor: I. Allegro'\n  notes: Spans album tracks 1, 2, 3, 4.\n"
        f"- work_id: {OTHER}\n  status: candidate\n  track:\n    number: 5\n"
        "    title: 'Rondo in A Major'\n")
    (root / 'docs' / 'test.md').write_text(
        f"# Test Composer\n\nFantasy in F Minor [*Murray Perahia, Radu Lupu*]"
        "(http://www.tidal.com/track/75254187)\n\nRondo [*Other Pianist*](https://tidal.com/track/11111111)\n")

    def unit(unit_id, work_id, disposition, performance_id, position, ident, title):
        return {'unit_id': unit_id, 'composer': 'Test Composer', 'composer_id': 'test-composer',
                'title': title, 'positions': [position],
                'disposition': disposition, 'work_id': work_id,
                'performance_id': performance_id,
                'performers': [{'name': 'Murray Perahia'}],
                'tracks': [track(position, ident, title)],
                'evidence': [{'file': 'docs/test.md', 'line': '1'}]}

    units = [
        unit('P384', WORK, 'import_new', P384, 1, '75254187', 'Fantasy in F Minor'),
        unit('P078', OTHER, 'import_new', OTHER + '-piano-p078', 2, '11111111', 'Rondo in A Major'),
    ]
    rows = [[t['position'], t['item_id'], t['id'], t['isrc']]
            for u in units for t in u['tracks']]
    manifest = {
        'schema_version': 1,
        'source': {'playlist_id': 'x', 'name': 'Piano', 'source_complete': True,
                   'track_count': 2,
                   'ordered_occurrences_sha256': hashlib.sha256(
                       json.dumps(rows, separators=(',', ':')).encode()).hexdigest()},
        'summary': {'import_new': {'units': 2, 'track_occurrences': 2,
                                    'distinct_performances': 2},
                    'not_selected': {'units': 0, 'track_occurrences': 0,
                                     'distinct_performances': 0}},
        'new_records': [
            {'id': P384, 'entity': 'performances', 'path': f'data/performances/{P384}.yaml'},
            {'id': OTHER + '-piano-p078', 'entity': 'performances',
             'path': f'data/performances/{OTHER}-piano-p078.yaml'}],
        'changed_existing': [],
        'recommendation_choices': [],
        'resolved_choices': [],
        'version_choice_issues': [],
        'units': units,
    }
    (root / FIXTURE_MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n')
    (root / 'reports/curator-decisions' / 'batch-status.json').write_text(json.dumps(
        {'schema_version': 1, 'status': 'validated', 'issues': [250],
         'updated_at': '2026-01-01T00:00:00+00:00'}, indent=2) + '\n')
    return manifest


def run_script(root: Path, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), '319', '--work', WORK, *args],
        cwd=root, capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join(
            p for p in [os.environ.get('PYTHONPATH'), str(REPO / 'src')] if p)))


def load_yaml(root: Path, relative: str):
    sys.path.insert(0, str(REPO / 'src'))
    from ruamel.yaml import YAML
    return YAML(typ='safe').load((root / relative).read_text())


class PromoteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / 'repo'
        self.root.mkdir()
        self.manifest = build_fixture(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_promote_applies_and_audit_passes(self):
        result = run_script(self.root, '--choice', 'CHA',
                            '--performer', 'Bertrand Chamayou (piano)',
                            '--performer', 'Leif Ove Andsnes (piano)',
                            '--track-url', 'https://tidal.com/track/461772236',
                            '--album-title', 'Schubert: Four Hands')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / f'data/performances/{NEW_PID}.yaml').is_file())
        self.assertFalse((self.root / f'data/performances/{P384}.yaml').exists())

        perf = load_yaml(self.root, f'data/performances/{NEW_PID}.yaml')
        self.assertEqual(perf['id'], NEW_PID)
        self.assertEqual(perf['work_id'], WORK)
        self.assertEqual([p['name'] for p in perf['performers']],
                         ['Bertrand Chamayou', 'Leif Ove Andsnes'])
        self.assertEqual(perf['links']['tidal']['url'],
                         'https://tidal.com/track/461772236')

        doc = (self.root / 'docs/test.md').read_text()
        self.assertIn('[*Bertrand Chamayou, Leif Ove Andsnes*]'
                      '(http://www.tidal.com/track/461772236)', doc)
        self.assertNotIn('75254187', doc)

        recording = load_yaml(self.root, 'data/recordings/test-recording.yml')
        entry = next(e for e in recording['works'] if e['work_id'] == WORK)
        self.assertEqual(entry['status'], 'recommended')
        self.assertEqual(entry['links']['tidal']['url'],
                         'https://tidal.com/track/461772236')
        self.assertIn('Curator decision #319', entry['notes'])
        self.assertIn('Spans album tracks', entry['notes'])
        other = next(e for e in recording['works'] if e['work_id'] == OTHER)
        self.assertEqual(other['status'], 'candidate')

        record = json.loads((self.root /
                             'reports/curator-decisions/issue-319.json').read_text())
        self.assertEqual(record['issue_url'],
                         'https://github.com/LuHoo/classical_music/issues/319')
        self.assertEqual(record['decision_source'], 'curator_cli')
        self.assertEqual(record['choice'], 'CHA')
        self.assertEqual(record['not_selected_units'], ['P384'])
        self.assertEqual(record['performance_id'], NEW_PID)
        self.assertEqual(record['replaced_performances'][0]['id'], P384)

        status = json.loads((self.root / 'reports/curator-decisions' /
                             'batch-status.json').read_text())
        self.assertEqual(status['status'], 'pending')
        self.assertEqual(status['issues'], [250, 319])

        manifest = json.loads((self.root / FIXTURE_MANIFEST).read_text())
        unit = next(u for u in manifest['units'] if u['unit_id'] == 'P384')
        self.assertEqual(unit['disposition'], 'not_selected')
        self.assertEqual(unit['review_classification'], 'curator_not_selected')
        self.assertEqual(unit['curator_decision'],
                         'reports/curator-decisions/issue-319.json')
        self.assertNotIn('performance_id', unit)
        self.assertEqual([r['id'] for r in manifest['new_records']],
                         [OTHER + '-piano-p078'])
        self.assertEqual(manifest['summary']['import_new'],
                         {'units': 1, 'track_occurrences': 1, 'distinct_performances': 1})
        self.assertEqual(manifest['summary']['not_selected'],
                         {'units': 1, 'track_occurrences': 1, 'distinct_performances': 0})
        self.assertEqual(manifest['changed_existing'][0]['action'], 'removed_by_curator')
        self.assertEqual(manifest['resolved_choices'][0]['work_id'], WORK)
        decision = manifest['resolved_choices'][0]['decision']
        self.assertEqual(decision['selected_units'], [])
        self.assertEqual(decision['not_selected_units'], ['P384'])
        self.assertEqual(decision['performances'][0]['performance_id'], NEW_PID)

        # Real chamber audit vocabulary must accept the updated fixture.
        sys.path.insert(0, str(REPO / 'src'))
        from classical_music import chamber_import
        from ruamel.yaml import YAML
        yaml = YAML(typ='safe')
        data = {}
        for kind in ('persons', 'work-groups', 'works', 'performances'):
            data[kind] = {}
            for path in (self.root / 'data' / kind).rglob('*.yaml'):
                loaded = yaml.load(path.read_text())
                data[kind][loaded['id']] = loaded
        chamber_import.check_inventory(manifest, data)
        chamber_import.validate_decision_records(manifest, self.root)

    def test_dry_run_writes_nothing(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = run_script(self.root, '--choice', 'CHA', '--performer', 'X (piano)',
                            '--track-url', 'https://tidal.com/track/461772236',
                            '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        after = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_refuses_twice(self):
        args = ('--choice', 'CHA', '--performer', 'X (piano)',
                '--track-url', 'https://tidal.com/track/461772236')
        self.assertEqual(run_script(self.root, *args).returncode, 0)
        second = run_script(self.root, *args)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn('already exists', second.stderr + second.stdout)

    def test_refuses_without_candidate_status(self):
        recording = self.root / 'data/recordings/test-recording.yml'
        recording.write_text(recording.read_text().replace(
            f'status: candidate\n  track:\n    number: 1', 'status: recommended\n  track:\n    number: 1', 1))
        result = run_script(self.root, '--choice', 'CHA', '--performer', 'X (piano)',
                            '--track-url', 'https://tidal.com/track/461772236')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('not candidate', result.stderr + result.stdout)

    def test_refuses_on_second_existing_performance(self):
        (self.root / f'data/performances/{WORK}-piano-p999.yaml').write_text(
            f"id: {WORK}-piano-p999\nwork_id: {WORK}\nperformers:\n  - name: Someone\n"
            "links:\n  tidal:\n    url: https://tidal.com/track/22222222\n")
        result = run_script(self.root, '--choice', 'CHA', '--performer', 'X (piano)',
                            '--track-url', 'https://tidal.com/track/461772236')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('profiled decision', result.stderr + result.stdout)

    def test_refuses_unsupported_manifest(self):
        manifest = json.loads((self.root / FIXTURE_MANIFEST).read_text())
        manifest.pop('changed_existing')
        (self.root / FIXTURE_MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n')
        result = run_script(self.root, '--choice', 'CHA', '--performer', 'X (piano)',
                            '--track-url', 'https://tidal.com/track/461772236')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unsupported manifest format', result.stderr + result.stdout)


class RejectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / 'repo'
        self.root.mkdir()
        build_fixture(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reject_keeps_existing(self):
        result = run_script(self.root, '--choice', 'existing')
        self.assertEqual(result.returncode, 0, result.stderr)
        recording = load_yaml(self.root, 'data/recordings/test-recording.yml')
        entry = next(e for e in recording['works'] if e['work_id'] == WORK)
        self.assertEqual(entry['status'], 'not_selected')
        self.assertTrue((self.root / f'data/performances/{P384}.yaml').is_file())
        self.assertFalse((self.root / f'data/performances/{NEW_PID}.yaml').exists())
        record = json.loads((self.root / 'reports/curator-decisions/issue-319.json').read_text())
        self.assertEqual(record['choice'], 'existing')
        self.assertEqual(record['performance_id'], P384)
        manifest = json.loads((self.root / FIXTURE_MANIFEST).read_text())
        self.assertEqual(manifest['summary']['import_new']['units'], 2)


BOUND_RECORDING = (
    "id: test-recording\ntitle: 'Test: Recording'\nlabel: Test Label\nyear: 2026\n"
    "works:\n"
    f"- work_id: {{WORK}}\n  status: candidate\n  issue: 319\n"
    "  track:\n    number: 1\n    title: 'Fantasy in F Minor: I. Allegro'\n"
    "  track_ids:\n  - '22222222'\n  - '22222223'\n"
    "  performers:\n  - Murray Perahia (piano)\n"
    "  notes: Spans album tracks 1, 2, 3, 4.\n"
    f"- work_id: {{OTHER}}\n  status: candidate\n  track:\n    number: 5\n"
    "    title: 'Rondo in A Major'\n"
)


class CuratorCliEarmarkedTest(unittest.TestCase):
    """./curator <issue> <choice> resolves the earmarked binding (#342-volg):
    register_earmarked_recording.py --issue/--work writes issue, track_ids and
    reviewed performers on the candidate entry; record_decision derives the
    candidate from that binding and delegates to apply_earmarked_decision."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / 'repo'
        self.root.mkdir()
        build_fixture(self.root)
        (self.root / 'data/recordings' / 'test-recording.yml').write_text(
            BOUND_RECORDING.replace('{WORK}', WORK).replace('{OTHER}', OTHER))
        import shutil
        (self.root / 'scripts').mkdir(exist_ok=True)
        shutil.copy(SCRIPT, self.root / 'scripts' / 'apply_earmarked_decision.py')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def record(self, issue, token, **kwargs):
        sys.path.insert(0, str(REPO / 'src'))
        from classical_music import curator_batch as batch
        return batch.record_decision(self.root, issue, token, **kwargs)

    def decision_record(self):
        return json.loads((self.root / 'reports/curator-decisions/issue-319.json').read_text())

    def test_promote_via_curator_cli(self):
        message = self.record(319, 'naive', apply=True)
        self.assertIn('Opgeslagen', message)
        performance = load_yaml(self.root, f'data/performances/{WORK}-earmarked-naive.yaml')
        self.assertEqual(performance['links']['tidal']['url'],
                         'https://tidal.com/track/22222222')
        self.assertEqual(performance['performers'],
                         [{'name': 'Murray Perahia', 'role': 'piano'}])
        self.assertEqual(self.decision_record()['decision_source'], 'curator_cli')
        status = json.loads(
            (self.root / 'reports/curator-decisions/batch-status.json').read_text())
        self.assertEqual(status['status'], 'pending')
        self.assertIn(319, status['issues'])

    def test_reject_via_curator_cli_keeps_existing(self):
        self.record(319, 'existing', apply=True)
        record = self.decision_record()
        self.assertEqual(record['requested_choice'], 'existing')
        self.assertFalse((self.root / f'data/performances/{WORK}-earmarked-existing.yaml').exists())

    def test_decision_url_becomes_evidence(self):
        url = 'https://github.com/LuHoo/classical_music/issues/319#issuecomment-1'
        self.record(319, 'naive', apply=True, decision_url=url)
        self.assertIn(url, self.decision_record()['evidence'])

    def test_unbound_issue_fails_closed(self):
        with self.assertRaises((ValueError, AssertionError)) as ctx:
            self.record(320, 'naive', apply=True)
        self.assertIn('no earmarked candidate binding', str(ctx.exception))
        self.assertIn('register_earmarked_recording.py', str(ctx.exception))

    def test_binding_without_reviewed_performers_fails_closed(self):
        (self.root / 'data/recordings' / 'test-recording.yml').write_text(
            BOUND_RECORDING.replace('{WORK}', WORK).replace('{OTHER}', OTHER)
            .replace("  performers:\n  - Murray Perahia (piano)\n", ""))
        with self.assertRaises((ValueError, AssertionError)) as ctx:
            self.record(319, 'naive', apply=True)
        self.assertIn('lacks reviewed performers', str(ctx.exception))
        self.assertIn('--update-existing', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
