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
