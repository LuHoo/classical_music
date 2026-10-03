import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
if not (SCRIPTS / 'repair_tidal_playlist.py').exists():
    SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))
import repair_tidal_playlist as repair


def fixture():
    items = [{'type': 'tracks', 'id': str(n), 'meta': {'itemId': 'old-' + str(n)}} for n in range(609)]
    # An unselected occurrence of the same track must survive.
    items.insert(2, {'type': 'tracks', 'id': '0', 'meta': {'itemId': 'untouched'}})
    rows = [{'status': 'CONFIRMED', 'position': pos, 'old_id': item['id'], 'item_id': item['meta']['itemId'], 'replacement_id': 'new-' + item['id']} for pos, item in enumerate(items, 1) if item['meta']['itemId'] != 'untouched']
    source = {'playlist': {'id': repair.PLAYLIST, 'attributes': {'lastModifiedAt': '0', 'numberOfItems': len(items)}}, 'items': items}
    report = {'playlist': copy.deepcopy(source['playlist']), 'country': 'NL', 'source_unchanged': True, 'rows': rows, 'total_occurrences': len(items)}
    return source, report


class FakeClient:
    def __init__(self, source, malformed=False, fail_delete=False):
        self.source = copy.deepcopy(source)
        self.malformed = malformed
        self.fail_delete = fail_delete
        self.deletes = 0
    def snapshot(self, playlist):
        return copy.deepcopy(self.source)
    def request(self, path, method='GET', body=None):
        if method == 'GET':
            return {'data': copy.deepcopy(self.source['playlist'])}
        items = self.source['items']
        if method == 'POST':
            pos = next(n for n, i in enumerate(items) if i['meta']['itemId'] == body['meta']['positionBefore'])
            added = [dict(i, meta={'itemId': 'added-' + i['id']}) for i in body['data']]
            items[pos:pos] = copy.deepcopy(added)
            response = {'data': added}
            if self.malformed:
                response['data'][0]['meta'] = {}
        else:
            self.deletes += 1
            if self.fail_delete:
                raise ValueError('injected deletion failure')
            remove = {i['meta']['itemId'] for i in body['data']}
            items[:] = [i for i in items if i['meta']['itemId'] not in remove]
            response = {}
        attrs = self.source['playlist']['attributes']
        attrs['numberOfItems'] = len(items)
        attrs['lastModifiedAt'] = str(int(attrs['lastModifiedAt']) + 1)
        return response


class RepairTests(unittest.TestCase):
    def run_repair(self, client, report, path):
        with patch.object(repair, 'validate_candidates'), patch('builtins.print'):
            repair.execute(client, report, path, None)
    def test_full_repair_preserves_order_and_unselected_duplicate(self):
        source, report = fixture()
        client = FakeClient(source)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'journal.json'
            self.run_repair(client, report, path)
            journal = json.loads(path.read_text())
            self.assertEqual(journal['status'], 'passed')
            self.assertEqual(journal['completed_occurrences'], 609)
            self.assertEqual(client.source['items'][2], source['items'][2])
            expected = [('tracks', 'new-' + i['id']) if i['meta']['itemId'] != 'untouched' else ('tracks', i['id']) for i in source['items']]
            self.assertEqual([(i['type'], i['id']) for i in client.source['items']], expected)
    def test_invalid_insert_response_never_deletes_old_occurrences(self):
        source, report = fixture()
        client = FakeClient(source, malformed=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'journal.json'
            with self.assertRaisesRegex(ValueError, 'not verified'):
                self.run_repair(client, report, path)
            self.assertEqual(client.deletes, 0)
            self.assertEqual(json.loads(path.read_text())['status'], 'stopped')
    def test_partial_failure_is_logged_and_rerun_refused(self):
        source, report = fixture()
        client = FakeClient(source, fail_delete=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'journal.json'
            with self.assertRaisesRegex(ValueError, 'injected'):
                self.run_repair(client, report, path)
            self.assertEqual(json.loads(path.read_text())['operations'][0]['state'], 'deleting')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                self.run_repair(client, report, path)
            self.assertEqual(client.deletes, 1)
    def test_catalogue_change_refused_before_writes(self):
        class Catalogue:
            resources = {}
            def tracks(self, field, values):
                return []
        row = {'position': 1, 'replacement_id': 'new', 'fingerprint': {'isrc': 'ABC', 'title': 'Work', 'duration_seconds': 60, 'artists': ['Artist']}}
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            repair.validate_candidates(Catalogue(), [row])

    def duration_fixture(self):
        source, report = fixture()
        for row in report['rows'][:108]:
            row['status'] = 'REVIEW'
            row['fingerprint'] = {'isrc': 'ISRC-' + row['old_id'], 'title': 'Work', 'duration_seconds': 60, 'artists': ['Artist']}
            row['candidates'] = [{'id': row['replacement_id'], 'duration': 'PT1M1S', 'checks': {'same_isrc': True, 'same_title': True, 'same_duration': False, 'artist_overlap': True}}]
        previous = {'status': 'passed', 'completed_occurrences': 609, 'final_snapshot': copy.deepcopy(source)}
        return source, report, previous

    def test_duration_batch_replaces_only_108_and_keeps_prior_snapshot(self):
        source, report, previous = self.duration_fixture()
        client = FakeClient(source)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'duration.json'
            with patch.object(repair, 'validate_candidates'), patch('builtins.print'):
                repair.execute(client, report, path, None, True, previous)
            journal = json.loads(path.read_text())
            self.assertEqual(journal['completed_occurrences'], 108)
            self.assertEqual(journal['status'], 'passed')
            self.assertEqual(client.source['items'][-1], source['items'][-1])
            self.assertEqual(client.source['items'][2], source['items'][2])
            self.assertEqual(previous['final_snapshot'], source)

    def test_duration_batch_refuses_changed_post_repair_snapshot(self):
        source, report, previous = self.duration_fixture()
        source['items'][-1]['id'] = 'unexpected'
        with self.assertRaisesRegex(ValueError, 'no longer matches'):
            repair.plan(report, source, True, previous)

    def test_duration_batch_requires_successful_prior_journal(self):
        source, report, previous = self.duration_fixture()
        previous['status'] = 'stopped'
        with self.assertRaisesRegex(ValueError, 'successful'):
            repair.plan(report, source, True, previous)

    def test_duration_batch_excludes_larger_or_other_differences(self):
        source, report, previous = self.duration_fixture()
        report['rows'][0]['candidates'][0]['duration'] = 'PT1M2S'
        report['rows'][1]['candidates'][0]['checks']['same_title'] = False
        self.assertEqual(len(repair.approved_rows(report, True)), 106)
        with self.assertRaisesRegex(ValueError, 'number'):
            repair.plan(report, source, True, previous)

    def test_duration_catalogue_recheck_refuses_two_second_difference(self):
        class Catalogue:
            resources = {('artists', 'a'): {'attributes': {'name': 'Artist'}}}
            def tracks(self, field, values):
                return [{'type': 'tracks', 'id': 'new', 'attributes': {'isrc': 'ISRC', 'title': 'Work', 'duration': 'PT1M2S', 'availability': ['STREAM']}, 'relationships': {'artists': {'data': [{'type': 'artists', 'id': 'a'}]}}}]
        row = {'position': 1, 'replacement_id': 'new', 'fingerprint': {'isrc': 'ISRC', 'title': 'Work', 'duration_seconds': 60, 'artists': ['Artist']}}
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            repair.validate_candidates(Catalogue(), [row], True)

    def spartacus_fixture(self):
        source, report = fixture()
        source['items'] = [{'type': 'tracks', 'id': str(n), 'meta': {'itemId': 'old-' + str(n)}} for n in range(1300)]
        source['playlist']['attributes']['numberOfItems'] = 1300
        report['total_occurrences'] = 1300
        report['rows'] = []
        for pos in range(1217, 1246):
            item = source['items'][pos-1]
            report['rows'].append({'status': 'REVIEW', 'position': pos, 'old_id': item['id'], 'item_id': item['meta']['itemId'], 'fingerprint': {'title': 'Spartacus (1968 Bolshoi version) (arr. Y. Grigorovich): Act I: Part ' + str(pos), 'isrc': 'ISRC-' + str(pos), 'duration_seconds': 60, 'artists': ['Choir']}, 'candidates': [{'id': 'new-' + item['id'], 'title': 'Spartacus, Act I: Part ' + str(pos) + ' (arr. Y. Grigorovich) [1968 Bolshoi Version]', 'duration': 'PT1M1S', 'checks': {'same_isrc': True, 'same_title': False, 'same_duration': False, 'artist_overlap': True}}]})
        previous = {'status': 'passed', 'completed_occurrences': 108, 'final_snapshot': copy.deepcopy(source)}
        return source, report, previous

    def test_spartacus_replaces_29_and_preserves_other_occurrences(self):
        source, report, previous = self.spartacus_fixture()
        client = FakeClient(source)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'spartacus.json'
            with patch.object(repair, 'validate_candidates'), patch('builtins.print'):
                repair.execute(client, report, path, None, False, previous, True)
            result = json.loads(path.read_text())
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['completed_occurrences'], 29)
            self.assertEqual(client.source['items'][:1216], source['items'][:1216])
            self.assertEqual(client.source['items'][1245:], source['items'][1245:])
            self.assertEqual(len(result['operations']), 1)

    def test_spartacus_rejects_different_movement_or_larger_duration(self):
        source, report, previous = self.spartacus_fixture()
        report['rows'][0]['candidates'][0]['title'] = 'Spartacus, Act I: Different movement (arr. Y. Grigorovich) [1968 Bolshoi Version]'
        report['rows'][1]['candidates'][0]['duration'] = 'PT1M2S'
        self.assertEqual(len(repair.approved_rows(report, False, True)), 27)
        with self.assertRaisesRegex(ValueError, 'number'):
            repair.plan(report, source, False, previous, True)

    def test_latest_journal_uses_latest_success_and_refuses_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('confirmed.json', 'duration.json', 'spartacus.json')]
            paths[0].write_text(json.dumps({'status': 'passed', 'finished_at': '2026-10-03T08:00:00Z', 'completed_occurrences': 609}))
            paths[1].write_text(json.dumps({'status': 'passed', 'finished_at': '2026-10-03T09:00:00Z', 'completed_occurrences': 108}))
            with patch.object(repair, 'JOURNAL', paths[0]), patch.object(repair, 'DURATION_JOURNAL', paths[1]), patch.object(repair, 'SPARTACUS_JOURNAL', paths[2]):
                self.assertEqual(repair.latest_successful_journal()['completed_occurrences'], 108)
                paths[2].write_text(json.dumps({'status': 'stopped'}))
                with self.assertRaisesRegex(ValueError, 'partial'):
                    repair.latest_successful_journal()

    def test_stale_approval_refused(self):
        source, report = fixture()
        source['playlist']['attributes']['lastModifiedAt'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'changed since approval'):
            repair.plan(report, source)
    def test_wrong_occurrence_position_refused(self):
        source, report = fixture()
        source['items'][0], source['items'][1] = source['items'][1], source['items'][0]
        with self.assertRaisesRegex(ValueError, 'position'):
            repair.plan(report, source)


if __name__ == '__main__':
    unittest.main()
