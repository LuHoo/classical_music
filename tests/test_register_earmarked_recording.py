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
    """tracks: (id, title, artists) or (id, title, artists, version, credits)."""
    data, included = [], []
    for position, spec in enumerate(tracks, 1):
        tid, title, artists = spec[0], spec[1], spec[2]
        version = spec[3] if len(spec) > 3 else None
        credits = spec[4] if len(spec) > 4 else {}
        attributes = {'title': title}
        if version:
            attributes['version'] = version
        data.append({'id': tid, 'type': 'tracks'})
        included.append({'type': 'tracks', 'id': tid, 'attributes': attributes,
                         'relationships': {'artists': {'data': [{'type': 'artists', 'id': f't{tid}{n}'}
                                                                for n in range(len(artists))]},
                                            'credits': {'data': [{'type': 'credits', 'id': f'c{tid}{n}'}
                                                                 for n in range(len(credits))]}}})
        for n, name in enumerate(artists):
            included.append({'type': 'artists', 'id': f't{tid}{n}', 'attributes': {'name': name}})
        for n, (role, names) in enumerate(credits.items()):
            included.append({'type': 'credits', 'id': f'c{tid}{n}',
                             'attributes': {'type': role, 'name': names}})
    return {'data': data, 'included': included}


class FakeCatalogClient:
    """Read-only catalogue double: rejects unexpected requests like the real wrapper."""

    def __init__(self, album_document, pages, album=ALBUM):
        self.album = album
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
        if path == f'/v2/albums/{self.album}?countryCode=NL&include=artists':
            return self.album_document
        if path.startswith(f'/v2/albums/{self.album}/relationships/items?'):
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
        (self.root / 'docs').mkdir()
        for name in ('data/works/w1.yaml', 'data/works/w2.yaml', 'data/persons/p1.yaml',
                     'data/artists/performers.yaml', 'data/performances/perf1.yaml',
                     'data/performances/perf2.yaml', 'docs/composer.md'):
            Path(self.root, name).touch()
        self.documents = {
            str(self.root / 'data/works/w1.yaml'): {
                'id': 'work-a', 'title': 'Symphonie fantastique', 'composer_id': 'hector-berlioz'},
            str(self.root / 'data/works/w2.yaml'): {
                'id': 'work-b', 'title': 'Harold en Italie', 'composer_id': 'hector-berlioz'},
            str(self.root / 'data/persons/p1.yaml'): {'id': 'hector-berlioz', 'name': 'Hector Berlioz'},
            str(self.root / 'data/artists/performers.yaml'): {'artists': [
                {'id': 'bernard-haitink', 'canonical_name': 'Bernard Haitink', 'type': 'conductor'},
                {'id': 'royal-concertgebouw-orchestra', 'canonical_name': 'Royal Concertgebouw Orchestra',
                 'type': 'orchestra'}]},
            str(self.root / 'data/performances/perf1.yaml'): {
                'id': 'perf1', 'work_id': 'work-a', 'recommended': True,
                'performers': [{'name': 'Bernard Haitink'}],
                'links': {'tidal': {'url': 'https://tidal.com/track/111'}}},
            str(self.root / 'data/performances/perf2.yaml'): {
                'id': 'perf2', 'work_id': 'work-b', 'recommended': True, 'performers': [{'name': 'Someone'}]},
        }
        (self.root / 'docs/composer.md').write_text(
            'D 940, Fantasy in F minor for piano duet (1828, first published as Op. 103) '
            '[*Murray Perahia, Radu Lupu*](http://www.tidal.com/track/111)\n', encoding='utf-8')
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

    def run_script(self, **kwargs):
        self.client.reset()
        kwargs.setdefault('read_client', self.client)
        return reg.run(self.root, ALBUM_URL, today='2026-10-18', **kwargs)

    def test_album_url_validation_is_fail_closed(self):
        for bad in ['', 'https://tidal.com/browse/album/', 'https://tidal.com/browse/album/12/x',
                    'http://tidal.com/browse/album/12', 'https://open.tidal.com/albums/12',
                    'https://tidal.com/browse/album/12?x=1', 'not a url',
                    'https://tidal.com/album/12/v', 'https://tidal.com/track/12']:
            with self.assertRaises(ValueError):
                reg.album_id(bad)
        self.assertEqual(reg.album_id(ALBUM_URL), ALBUM)
        self.assertEqual(reg.album_id(f'https://tidal.com/album/{ALBUM}'), ALBUM)
        self.assertEqual(reg.album_id(f'https://tidal.com/album/{ALBUM}/u'), ALBUM)
        self.assertEqual(reg.album_id(f'https://listen.tidal.com/album/{ALBUM}'), ALBUM)

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
        self.assertEqual(result['written'], 'data/recordings/test-album.yml')
        plan = result['report']['playlist_plans'][0]
        self.assertEqual(plan['work_id'], 'work-a')
        self.assertTrue(plan['playlist_url'].startswith('https://tidal.com/playlist/'))
        playlist = user.playlists[plan['playlist_url'].rsplit('/', 1)[-1]]
        self.assertEqual(playlist['items'], ['111', '222', '223'])
        saved = self._read_yaml(self.root / 'data/recordings/test-album.yml')
        self.assertEqual(saved['id'], 'test-album')
        self.assertEqual(saved['links']['tidal']['url'], ALBUM_URL)
        self.assertEqual(saved['links']['tidal']['status'], 'active')
        self.assertEqual(saved['links']['tidal']['last_checked'], '2026-10-18')

    def test_published_doc_recommendation_is_detected_with_track_anchor(self):
        recommendations, unattributed = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        self.assertEqual(recommendations['work-a']['track_ids'], ['111'])
        self.assertEqual(recommendations['work-a']['sources'],
                         ['perf1.yaml', 'composer.md:1'])
        self.assertEqual(unattributed, [])
        self.assertIn('work-b', recommendations)

    def test_doc_recommendation_line_without_attribution_is_reported(self):
        (self.root / 'docs/composer.md').write_text(
            'Some vague recommendation line [*Names*](http://www.tidal.com/track/999)\n',
            encoding='utf-8')
        recommendations, unattributed = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        doc_only = {w for w in recommendations
                    if any(s.startswith('docs/') for s in recommendations[w]['sources'])}
        self.assertEqual(doc_only, set())
        self.assertEqual(unattributed, ['composer.md:1 (track 999)'])

    def test_recommendation_without_track_anchor_gets_no_playlist(self):
        result = self.run_script(dry_run=True)
        plans = result['report']['playlist_plans']
        # work-b is recommended without a TIDAL track anchor: no plan is produced for it.
        self.assertNotIn('work-b', [p['work_id'] for p in plans])
        self.assertEqual(plans[0]['current_tracks'], ['111'])

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


class SchubertCase(unittest.TestCase):
    """The real Schubert: Four Hands album structure: bare movement titles, work in the
    version attribute, composer only in credits, performers not in canonical data."""

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'persons', 'artists', 'performances', 'recordings'):
            (self.root / 'data' / name).mkdir(parents=True)
        (self.root / 'docs').mkdir()
        works = ('data/works/franz-schubert-fantasie-in-f-minor-d-940.yaml',)
        persons = ('data/persons/franz-schubert.yaml',)
        performances = ('data/performances/franz-schubert-fantasie-in-f-minor-d-940-piano-p384.yaml',)
        for name in works + persons + performances + ('data/artists/performers.yaml', 'docs/schubert.md'):
            Path(self.root, name).touch()
        self.documents = {
            str(self.root / works[0]): {
                'id': 'franz-schubert-fantasie-in-f-minor-d-940',
                'composer_id': 'franz-schubert', 'title': 'Fantasie in F Minor, D. 940'},
            str(self.root / persons[0]): {'id': 'franz-schubert', 'name': 'Franz Schubert'},
            str(self.root / performances[0]): {
                'id': 'p384', 'work_id': 'franz-schubert-fantasie-in-f-minor-d-940',
                'performers': [{'name': 'Murray Perahia', 'role': 'piano'},
                               {'name': 'Radu Lupu', 'role': 'piano'}],
                'links': {'tidal': {'url': 'https://tidal.com/track/75254187'}}},
            str(self.root / 'data/artists/performers.yaml'): {'artists': []},
        }
        (self.root / 'docs/schubert.md').write_text(
            'D 940, Fantasy in F minor for piano duet (1828, first published as Op. 103) '
            '[*Murray Perahia, Radu Lupu*](http://www.tidal.com/track/75254187)\n', encoding='utf-8')
        self._read_yaml = reg.read_yaml

        def read(path):
            path = str(path)
            return self.documents[path] if path in self.documents else self._read_yaml(path)

        reg.read_yaml = read
        credits = {'Composer': 'Franz Schubert'}
        album = album_doc(title='Schubert: Four Hands',
                         artists=('Bertrand Chamayou', 'Leif Ove Andsnes'))
        album['data']['id'] = '461772235'
        self.album_id = '461772235'
        self.client = FakeCatalogClient(album, [item_page([
            ('461772236', 'I. Allegro molto moderato', ('Bertrand Chamayou', 'Leif Ove Andsnes'),             'Fantasia in F Minor, D. 940, Op. 103', credits),
            ('461772237', 'II. Largo', ('Bertrand Chamayou', 'Leif Ove Andsnes'),
             'Fantasia in F Minor, D. 940, Op. 103', credits),
            ('461772238', 'III. Allegro vivace', ('Bertrand Chamayou', 'Leif Ove Andsnes'),
             'Fantasia in F Minor, D. 940, Op. 103', credits),
            ('461772239', 'IV. Finale. Allegro molto moderato', ('Bertrand Chamayou', 'Leif Ove Andsnes'),
             'Fantasia in F Minor, D. 940, Op. 103', credits),
            ('461772240', 'Allegro in A Minor, D. 947, Op. posth. 144 "Lebensstürme"',
             ('Bertrand Chamayou', 'Leif Ove Andsnes'), None, credits),
            ('461772241', 'Fugue in E Minor, D. 952, Op. posth. 152',
             ('Bertrand Chamayou', 'Leif Ove Andsnes'), None, credits),
            ('461772242', 'Rondo in A Major, D. 951, Op. 107',
             ('Bertrand Chamayou', 'Leif Ove Andsnes'), None, credits),
        ])], album='461772235')

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def run_script(self, **kwargs):
        self.client.reset()
        kwargs.setdefault('read_client', self.client)
        return reg.run(self.root, 'https://tidal.com/album/461772235/u',
                       today='2026-10-18', **kwargs)

    def test_movements_match_via_version_and_catalogue_token(self):
        result = self.run_script(dry_run=True)
        candidates = [e for e in result['recording']['works'] if e.get('status') == 'candidate']
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['work_id'], 'franz-schubert-fantasie-in-f-minor-d-940')
        self.assertEqual(candidates[0]['track']['number'], 1)
        self.assertIn('Spans album tracks 1, 2, 3, 4', candidates[0]['notes'])

    def test_missing_canonical_works_stay_raw_notes(self):
        result = self.run_script(dry_run=True)
        notes = result['recording']['notes']
        self.assertIn('Lebensstürme', notes)
        self.assertIn('Fugue in E Minor', notes)
        self.assertIn('Rondo in A Major', notes)
        self.assertEqual(len(result['report']['unmatched_tracks']), 3)
        self.assertTrue(all(u['state'] == 'unknown' for u in result['report']['unmatched_tracks']))

    def test_published_recommendation_yields_comparison_playlist_plan(self):
        result = self.run_script(dry_run=True)
        plans = result['report']['playlist_plans']
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]['work_id'], 'franz-schubert-fantasie-in-f-minor-d-940')
        self.assertEqual(plans[0]['current_tracks'], ['75254187'])
        self.assertEqual(plans[0]['candidate_tracks'],
                         ['461772236', '461772237', '461772238', '461772239'])

    def test_apply_creates_playlist_and_yaml(self):
        user = FakeUserClient()
        result = self.run_script(user_client_factory=lambda: user)
        self.assertEqual(result['written'], 'data/recordings/schubert-four-hands.yml')
        url = result['report']['playlist_plans'][0]['playlist_url']
        playlist = user.playlists[url.rsplit('/', 1)[-1]]
        self.assertEqual(playlist['items'],
                         ['75254187', '461772236', '461772237', '461772238', '461772239'])
        self.assertIn('Unmatched artists: Bertrand Chamayou, Leif Ove Andsnes',
                      self._read_yaml(self.root / 'data/recordings/schubert-four-hands.yml')['notes'])
        self.assertIn('Earmarked 2026-10-18', playlist['name'])

    def test_catalogue_tokens(self):
        self.assertEqual(reg.catalogue_tokens('Fantasia in F Minor, D. 940, Op. 103'),
                         {'d940', 'op103'})
        self.assertEqual(reg.catalogue_tokens('Hob. Ia:7'), set())
        self.assertEqual(reg.catalogue_tokens('Sinfonie Nr. 4 op. 120'), {'op120'})


class ReportCase(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(reg.slugify('Berlioz: Symphonie fantastique'), 'berlioz-symphonie-fantastique')
        with self.assertRaises(ValueError):
            reg.slugify('???')


if __name__ == '__main__':
    unittest.main()
