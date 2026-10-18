import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if not (SCRIPTS / 'register_earmarked_recording.py').exists():
    SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / 'src'))

import register_earmarked_recording as reg


ALBUM = '987654'
ALBUM_URL = f'https://tidal.com/browse/album/{ALBUM}'


def album_doc(title='Test Album', artists=('Hector Berlioz', 'Royal Concertgebouw Orchestra')):
    included = [{'type': 'artists', 'id': f'a{n}', 'attributes': {'name': name}}
                for n, name in enumerate(artists)]
    return {'data': {'id': ALBUM, 'type': 'albums',
                     'attributes': {'title': title, 'releaseDate': '1994-01-01',
                                    'copyright': 'Philips'},
                     'relationships': {'artists': {'data': [{'type': 'artists', 'id': f'a{n}'}
                                                             for n in range(len(artists))]}}},
            'included': included}


def item_page(tracks):
    data, included = [], []
    for position, (tid, title, artists) in enumerate(tracks, 1):
        data.append({'id': tid, 'type': 'tracks'})
        included.append({'type': 'tracks', 'id': tid, 'attributes': {'title': title},
                         'relationships': {'artists': {'data': [{'type': 'artists', 'id': f't{tid}{n}'}
                                                                for n in range(len(artists))]}}})
        for n, name in enumerate(artists):
            included.append({'type': 'artists', 'id': f't{tid}{n}', 'attributes': {'name': name}})
    return {'data': data, 'included': included}


class FakeCatalogClient:
    """Read-only catalogue double: rejects unexpected requests like the real wrapper."""

    def __init__(self, album_document, pages):
        self.album_document = album_document
        self._pages = list(pages)
        self.reset()

    def reset(self):
        self.pages = list(self._pages)
        self.calls = []

    def request(self, path, method='GET', body=None, *, idempotency_key=None):
        self.calls.append((method, path))
        if method != 'GET' or body is not None:
            raise ValueError('The album fetcher cannot make write requests')
        if path == f'/v2/albums/{ALBUM}?countryCode=NL&include=artists':
            return self.album_document
        if path.startswith(f'/v2/albums/{ALBUM}/relationships/items?'):
            if not self.pages:
                raise ValueError('Unexpected extra album page request')
            return self.pages.pop(0)
        raise ValueError('Unexpected album request path: ' + path)


class FakeUserClient:
    """Playlist double: records mutations and snapshots exactly what was added."""

    def __init__(self):
        self.playlists = {}
        self.mutations = []

    def request(self, path, method='GET', body=None, *, idempotency_key=None):
        if method == 'POST' and path == '/playlists':
            self.mutations.append(('create', body))
            pid = f'00000000-0000-0000-0000-{len(self.playlists) + 1:012d}'
            self.playlists[pid] = {'name': body['data']['attributes']['name'],
                                   'description': body['data']['attributes']['description'], 'items': []}
            return {'data': {'id': pid}}
        if method == 'POST' and '/relationships/items' in path:
            pid = path.split('/')[2]
            self.mutations.append(('add', pid, body))
            self.playlists[pid]['items'].extend(row['id'] for row in body['data'])
            return {}
        raise ValueError('Unexpected user client request: ' + method + ' ' + path)

    def snapshot(self, pid):
        return {'playlist': {'id': pid, 'attributes': dict(self.playlists[pid],
                                                            numberOfItems=len(self.playlists[pid]['items']))},
                'items': [{'id': tid, 'type': 'tracks'} for tid in self.playlists[pid]['items']]}


class FixtureCase(unittest.TestCase):
    """Canonical data is injected through read_yaml; no ruamel parsing of fixture files."""

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'persons', 'artists', 'performances', 'recordings'):
            (self.root / 'data' / name).mkdir(parents=True)
        self.documents = {}
        (self.root / 'data/works/w1.yaml').touch()
        (self.root / 'data/works/w2.yaml').touch()
        (self.root / 'data/persons/p1.yaml').touch()
        (self.root / 'data/artists/performers.yaml').touch()
        (self.root / 'data/performances/perf1.yaml').touch()
        (self.root / 'data/performances/perf2.yaml').touch()
        self.documents[str(self.root / 'data/works/w1.yaml')] = {
            'id': 'work-a', 'title': 'Symphonie fantastique', 'composer_id': 'hector-berlioz'}
        self.documents[str(self.root / 'data/works/w2.yaml')] = {
            'id': 'work-b', 'title': 'Harold en Italie', 'composer_id': 'hector-berlioz'}
        self.documents[str(self.root / 'data/persons/p1.yaml')] = {'id': 'hector-berlioz', 'name': 'Hector Berlioz'}
        self.documents[str(self.root / 'data/artists/performers.yaml')] = {'artists': [
            {'id': 'bernard-haitink', 'canonical_name': 'Bernard Haitink', 'type': 'conductor'},
            {'id': 'royal-concertgebouw-orchestra', 'canonical_name': 'Royal Concertgebouw Orchestra',
             'type': 'orchestra'}]}
        self.documents[str(self.root / 'data/performances/perf1.yaml')] = {
            'id': 'perf1', 'work_id': 'work-a', 'recommended': True,
            'performers': [{'name': 'Bernard Haitink'}],
            'links': {'tidal': {'url': 'https://tidal.com/track/111'}}}
        self.documents[str(self.root / 'data/performances/perf2.yaml')] = {
            'id': 'perf2', 'work_id': 'work-b', 'recommended': True, 'performers': [{'name': 'Someone'}]}
        self._read_yaml = reg.read_yaml

        def read(path):
            path = str(path)
            if path in self.documents:
                return self.documents[path]
            return self._read_yaml(path)

        reg.read_yaml = read
        self.client = FakeCatalogClient(album_doc(), [item_page([
            ('222', 'Symphonie fantastique: I. Rêveries', ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
            ('223', 'Symphonie fantastique: II. Un bal', ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
            ('224', 'Harold en Italie', ('Hector Berlioz', 'Unknown Soprano')),
        ])])

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def tracks(self):
        return reg.album_tracks(self.client, ALBUM)

    def run_script(self, **kwargs):
        self.client.reset()
        kwargs.setdefault('read_client', self.client)
        return reg.run(self.root, ALBUM_URL, today='2026-10-18', **kwargs)

    def test_album_url_validation_is_fail_closed(self):
        for bad in ['', 'https://tidal.com/browse/album/', 'https://tidal.com/browse/album/12/x',
                    'http://tidal.com/browse/album/12', 'https://open.tidal.com/albums/12',
                    'https://tidal.com/browse/album/12?x=1', 'not a url']:
            with self.assertRaises(ValueError):
                reg.album_id(bad)
        self.assertEqual(reg.album_id(ALBUM_URL), ALBUM)

    def test_matched_candidate_without_recommendation_gets_no_playlist(self):
        result = self.run_script(dry_run=True)
        candidates = {e['work_id']: e for e in result['recording']['works'] if e.get('status') == 'candidate'}
        self.assertEqual(set(candidates), {'work-a', 'work-b'})
        plan_ids = [p['work_id'] for p in result['report']['playlist_plans']]
        self.assertEqual(plan_ids, ['work-a'])
        self.assertEqual(list((self.root / 'data/recordings').glob('*.y*ml')), [])

    def test_consecutive_tracks_of_one_work_collapse(self):
        result = self.run_script(dry_run=True)
        entry = next(e for e in result['recording']['works'] if e['work_id'] == 'work-a')
        self.assertEqual(entry['track']['number'], 1)
        self.assertIn('Spans album tracks 1, 2', entry['notes'])

    def test_unmatched_artist_is_raw_text_and_known_artist_is_canonical(self):
        result = self.run_script(dry_run=True)
        artists = result['recording']['artists']
        self.assertNotIn('conductor', artists)
        self.assertEqual(artists['orchestra'], ['royal-concertgebouw-orchestra'])
        self.assertIn('Unknown Soprano', result['recording']['notes'])
        self.assertIn('Hector Berlioz', result['recording']['notes'])

    def test_dry_run_never_writes_or_creates_playlists(self):
        def factory():
            raise AssertionError('Dry run must not create a user client')

        result = self.run_script(dry_run=True, user_client_factory=factory)
        self.assertTrue(result['dry_run'])
        self.assertNotIn('written', result)
        self.assertEqual(list((self.root / 'data/recordings').glob('*.y*ml')), [])

    def test_apply_writes_candidate_and_comparison_playlist(self):
        user = FakeUserClient()
        result = self.run_script(user_client_factory=lambda: user)
        self.assertEqual(result['written'], f'data/recordings/test-album.yml')
        plan = result['report']['playlist_plans'][0]
        self.assertEqual(plan['work_id'], 'work-a')
        self.assertTrue(plan['playlist_url'].startswith('https://tidal.com/playlist/'))
        playlist = user.playlists[plan['playlist_url'].rsplit('/', 1)[-1]]
        self.assertEqual(playlist['items'], ['111', '222', '223'])
        saved = reg.yaml.load((self.root / 'data/recordings/test-album.yml').read_text())
        self.assertEqual(saved['id'], 'test-album')
        self.assertEqual(saved['links']['tidal']['url'], ALBUM_URL)
        self.assertEqual(saved['links']['tidal']['status'], 'active')
        self.assertEqual(saved['links']['tidal']['last_checked'], '2026-10-18')

    def test_recommendation_without_track_anchor_gets_no_playlist(self):
        result = self.run_script(dry_run=True)
        plan = next(p for p in result['report']['playlist_plans'])
        # work-b is recommended without a TIDAL track anchor: no plan is produced for it.
        self.assertNotIn('work-b', [p['work_id'] for p in result['report']['playlist_plans']])
        self.assertEqual(plan['current_tracks'], ['111'])

    def test_ambiguous_track_is_unevaluated_and_reported(self):
        self.documents[str(self.root / 'data/works/w1.yaml')] = {
            'id': 'work-a', 'title': 'Symphonie', 'composer_id': 'hector-berlioz'}
        self.documents[str(self.root / 'data/works/w2.yaml')] = {
            'id': 'work-c', 'title': 'Symphonie fantastique', 'composer_id': 'hector-berlioz',
            'aliases': ['Symphonie']}
        result = self.run_script(dry_run=True)
        unevaluated = [e for e in result['recording']['works'] if 'status' not in e]
        self.assertTrue(unevaluated)
        self.assertTrue(all(e['work_id'] in ('work-a', 'work-c') for e in unevaluated))
        candidates = {e['work_id'] for e in result['recording']['works'] if e.get('status') == 'candidate'}
        self.assertNotIn('work-a', candidates)
        unmatched = result['report']['unmatched_tracks']
        self.assertTrue(any(u['state'] == 'ambiguous' for u in unmatched))

    def test_existing_recording_file_is_never_silently_overwritten(self):
        path = self.root / 'data/recordings/test-album.yml'
        path.write_text('id: test-album\ntitle: Other release\nworks: []\n')
        with self.assertRaises(ValueError):
            self.run_script(user_client_factory=lambda: FakeUserClient())
        self.documents[str(path)] = {'id': 'test-album', 'title': 'Other release',
                                     'works': [], 'links': {'tidal': {'url': ALBUM_URL}}}
        user = FakeUserClient()
        result = self.run_script(update_existing=True, user_client_factory=lambda: user)
        saved = self.documents[str(path)]
        self.assertIn('work-a', [e['work_id'] for e in saved['works']])

    def test_update_existing_refuses_a_different_album(self):
        path = self.root / 'data/recordings/test-album.yml'
        self.documents[str(path)] = {'id': 'test-album', 'title': 'Other release', 'works': [],
                                     'links': {'tidal': {'url': 'https://tidal.com/browse/album/1'}}}
        path.write_text('id: test-album\n')
        with self.assertRaises(ValueError):
            self.run_script(update_existing=True, user_client_factory=lambda: FakeUserClient())

    def test_catalog_client_rejects_writes_and_foreign_paths(self):
        client = reg.CatalogClient('token', ALBUM)
        with self.assertRaises(ValueError):
            client.request('/v2/playlists', 'POST', {})
        with self.assertRaises(ValueError):
            client.request('/v2/albums/' + '1' * 20 + '?countryCode=NL')


class ReportCase(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(reg.slugify('Berlioz: Symphonie fantastique'), 'berlioz-symphonie-fantastique')
        with self.assertRaises(ValueError):
            reg.slugify('???')


if __name__ == '__main__':
    unittest.main()
