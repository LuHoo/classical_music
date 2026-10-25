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


def album_doc_for(album, title='Test Album', artists=('Hector Berlioz', 'Royal Concertgebouw Orchestra')):
    """album_doc with a chosen album ID (for an existing recommendation's album)."""
    document = album_doc(title, artists)
    document['data']['id'] = album
    return document


def item_page(tracks):
    """tracks: (id, title, artists), (id, title, artists, version) or
    (id, title, artists, version, credits) or (id, title, artists, version,
    credits, isrc)."""
    data, included = [], []
    for position, spec in enumerate(tracks, 1):
        tid, title, artists = spec[0], spec[1], spec[2]
        version = spec[3] if len(spec) > 3 else None
        credits = (spec[4] if len(spec) > 4 else {}) or {}
        isrc = spec[5] if len(spec) > 5 else None
        attributes = {'title': title}
        if version:
            attributes['version'] = version
        if isrc:
            attributes['isrc'] = isrc
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

    def __init__(self, album_document, pages, album=ALBUM, *, artists_route='relationship',
                 items_include='items,items.artists,items.credits', track_albums=None):
        self.album = album
        self.album_document = album_document
        self._pages = list(pages)
        self.artists_route = artists_route
        self.items_include = items_include
        self.track_albums = track_albums or {}
        self.reset()

    def reset(self):
        self.pages = list(self._pages)
        self.calls = []

    def request(self, path, method='GET', body=None, *, idempotency_key=None):
        self.calls.append((method, path))
        if method != 'GET' or body is not None:
            raise ValueError('The album fetcher cannot make write requests')
        if path.startswith('/v2/tracks/') and 'include=albums' in path:
            track = path.split('/v2/tracks/', 1)[1].split('?', 1)[0]
            if track not in self.track_albums:
                raise ValueError('Unexpected track request: ' + path)
            return {'data': {'id': track, 'type': 'tracks',
                            'relationships': {'albums': {'data': [{'type': 'albums',
                                                                   'id': self.track_albums[track]}]}}},
                    'included': []}
        if path == f'/v2/albums/{self.album}?countryCode=NL':
            return self.album_document
        if path == f'/v2/albums/{self.album}/relationships/artists?countryCode=NL&include=artists':
            if self.artists_route == 'filter':
                raise ValueError('HTTP 404')
            if self.artists_route == 'both':
                raise ValueError('HTTP 404')
            return {'data': [], 'included': self.album_document.get('included', [])}
        if path.startswith('/v2/artists?') and ('filter[id]=' in path or 'filter%5Bid%5D=' in path):
            if self.artists_route not in ('filter', 'both'):
                raise ValueError('Unexpected artists filter request: ' + path)
            return {'data': self.album_document.get('included', [])}
        if path.startswith(f'/v2/albums/{self.album}/relationships/items?'):
            include = path.rsplit('include=', 1)[-1]
            if 'next' in path or include == self.items_include:
                if not self.pages:
                    raise ValueError('Unexpected extra album page request')
                return self.pages.pop(0)
            raise ValueError('HTTP 404')
        raise ValueError('Unexpected album request path: ' + path)

    def try_request(self, path):
        try:
            return self.request(path)
        except ValueError as exc:
            if 'HTTP 404' in str(exc):
                return None
            raise


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


class FakeSuggestionClient:
    """Canned MusicBrainz double: never touches the network."""

    def __init__(self, suggestions=None, fail=False, isrc_suggestions=None):
        self.suggestions = suggestions if suggestions is not None else [
            {'title': 'Lebensstürme', 'musicbrainz_work_id': 'w1', 'source': 'musicbrainz',
             'composers': [{'name': 'Franz Schubert', 'musicbrainz_artist_id': 'a1'}]}]
        self.fail = fail
        self.isrc_suggestions = isrc_suggestions if isrc_suggestions is not None else []
        self.queries = []
        self.isrc_queries = []

    def work_suggestions(self, text, limit=3):
        self.queries.append(text)
        if self.fail:
            raise OSError('External lookups unavailable')
        return self.suggestions

    def recording_work_suggestions(self, isrc, limit=3):
        self.isrc_queries.append(isrc)
        if self.fail:
            raise OSError('External lookups unavailable')
        return self.isrc_suggestions


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
        # The existing recommendation (anchor track 111) lives on its own album
        # '777' with two movements; the comparison playlist needs both.
        self.recommendation_client = FakeCatalogClient(album_doc_for('777'), [item_page([
            ('111', 'Symphonie fantastique: I. Rêveries',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
            ('112', 'Symphonie fantastique: II. Un bal',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
        ])], album='777')
        self.client = FakeCatalogClient(album_doc(), [item_page([
            ('222', 'Symphonie fantastique: I. Rêveries', ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
            ('223', 'Symphonie fantastique: II. Un bal', ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
            ('224', 'Harold en Italie', ('Hector Berlioz', 'Unknown Soprano')),
        ])], track_albums={'111': '777'})

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def run_script(self, **kwargs):
        self.client.reset()
        self.recommendation_client.reset()
        kwargs.setdefault('read_client', self.client)
        kwargs.setdefault('catalog_factory', lambda album: self.recommendation_client)
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

    def test_apply_writes_candidate_and_reports_playlist_plan(self):
        user = FakeUserClient()
        result = self.run_script(user_client_factory=lambda: user)
        self.assertEqual(result['written'], 'data/recordings/test-album.yml')
        self.assertEqual(result['playlists'], [])
        plan = result['report']['playlist_plans'][0]
        self.assertEqual(plan['work_id'], 'work-a')
        self.assertIsNone(plan['playlist_url'])
        self.assertIsNone(plan['name'])
        self.assertIn('re-run with --issue', result['report']['playlist_notice'])
        saved = self._read_yaml(self.root / 'data/recordings/test-album.yml')
        self.assertEqual(saved['id'], 'test-album')
        self.assertEqual(saved['links']['tidal']['url'], ALBUM_URL)
        self.assertEqual(saved['links']['tidal']['status'], 'active')
        self.assertEqual(saved['links']['tidal']['last_checked'], '2026-10-18')

    def test_issue_work_creates_named_playlist_with_complete_recordings(self):
        user = FakeUserClient()
        result = self.run_script(issue=316, work='work-a', user_client_factory=lambda: user)
        plan = result['report']['playlist_plans'][0]
        self.assertEqual(plan['work_id'], 'work-a')
        url = plan['playlist_url']
        playlist = user.playlists[url.rsplit('/', 1)[-1]]
        # Current recommendation as its complete recording (both movements of
        # album 777), then the complete candidate recording (#316 feedback).
        self.assertEqual(playlist['items'], ['111', '112', '222', '223'])
        self.assertEqual(playlist['name'], 'Curator 2026-10-18 Issue #316')
        self.assertIn('issues/316', playlist['description'])

    def test_published_doc_recommendation_is_detected_with_track_anchor(self):
        recommendations, unattributed, breakdown = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        self.assertEqual(recommendations['work-a']['track_ids'], ['111'])
        self.assertEqual(recommendations['work-a']['sources'],
                         ['perf1.yaml', 'composer.md:1'])
        self.assertEqual(unattributed, [])
        self.assertEqual(breakdown, [])
        self.assertIn('work-b', recommendations)

    def test_doc_recommendation_line_without_attribution_is_reported(self):
        (self.root / 'docs/composer.md').write_text(
            'Some vague recommendation line [*Names*](http://www.tidal.com/track/999)\n',
            encoding='utf-8')
        recommendations, unattributed, breakdown = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        doc_only = {w for w in recommendations
                    if any(s.startswith('docs/') for s in recommendations[w]['sources'])}
        self.assertEqual(doc_only, set())
        self.assertEqual(unattributed, ['composer.md:1 (track 999)'])
        self.assertEqual(breakdown, [{'category': 'no-canonical-work', 'count': 1,
                                      'examples': ['composer.md:1 (track 999)']}])

    def test_catalogue_field_matches_doc_line_without_title_tokens(self):
        """The catalogue map (not the title) carries the docs line's number (#323)."""
        self.documents[str(self.root / 'data/works/w1.yaml')] = {
            'id': 'work-a', 'title': 'Symphonie fantastique', 'composer_id': 'hector-berlioz',
            'catalogue': {'bwv': 'BWV 1046.2'}}
        (self.root / 'docs/composer.md').write_text(
            '# Hector Berlioz\n\nConcert [*Names*](http://www.tidal.com/track/555), BWV 1046.2\n',
            encoding='utf-8')
        recommendations, unattributed, _ = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        self.assertIn('work-a', recommendations)
        self.assertEqual(recommendations['work-a']['sources'], ['perf1.yaml', 'composer.md:3'])
        self.assertEqual(unattributed, [])

    def test_page_heading_composer_evidence_disambiguates_tokens(self):
        """A token shared across composers resolves via the page heading (#323)."""
        self.documents[str(self.root / 'data/works/w2.yaml')] = {
            'id': 'work-b', 'title': 'Harold en Italie', 'composer_id': 'hector-berlioz',
            'catalogue': {'opus': 'Op. 21'}}
        (self.root / 'data/works/w3.yaml').touch()
        (self.root / 'data/persons/p2.yaml').touch()
        self.documents[str(self.root / 'data/works/w3.yaml')] = {
            'id': 'work-c', 'title': 'Diversions', 'composer_id': 'benjamin-britten',
            'catalogue': {'opus': 'Op. 21'}}
        self.documents[str(self.root / 'data/persons/p2.yaml')] = {
            'id': 'benjamin-britten', 'name': 'Benjamin Britten'}
        (self.root / 'docs/composer.md').write_text(
            '# Benjamin Britten\n\nDiversions [*Names*](http://www.tidal.com/track/555), Op. 21\n',
            encoding='utf-8')
        recommendations, unattributed, _ = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        self.assertIn('work-c', recommendations)
        self.assertEqual(recommendations['work-c']['sources'], ['composer.md:3'])
        self.assertNotIn('composer.md:3', recommendations['work-b']['sources'])
        self.assertEqual(unattributed, [])

    def test_title_containment_matches_doc_line_with_composer_evidence(self):
        """Without any catalogue tokens, a unique title containment match in the
        composer's pool attributes the line (#323)."""
        (self.root / 'docs/composer.md').write_text(
            '# Hector Berlioz\n\nSomething about Harold en Italie for viola '
            '[*Names*](http://www.tidal.com/track/555)\n', encoding='utf-8')
        recommendations, unattributed, _ = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        self.assertIn('work-b', recommendations)
        self.assertEqual(unattributed, [])

    def test_ambiguous_doc_line_is_classified_not_attributed(self):
        """Several candidates after composer narrowing stay unattributed, as
        'ambiguous-match' (#323)."""
        self.documents[str(self.root / 'data/works/w2.yaml')] = {
            'id': 'work-b', 'title': 'Harold en Italie', 'composer_id': 'hector-berlioz',
            'aliases': ['Symphonie']}
        self.documents[str(self.root / 'data/works/w1.yaml')] = {
            'id': 'work-a', 'title': 'Symphonie fantastique', 'composer_id': 'hector-berlioz',
            'aliases': ['Symphonie']}
        (self.root / 'docs/composer.md').write_text(
            '# Hector Berlioz\n\nSymphonie on one line '
            '[*Names*](http://www.tidal.com/track/555)\n', encoding='utf-8')
        recommendations, unattributed, breakdown = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        self.assertEqual(unattributed, ['composer.md:3 (track 555)'])
        self.assertEqual(breakdown, [{'category': 'ambiguous-match', 'count': 1,
                                      'examples': ['composer.md:3 (track 555)']}])
        # only the performance source, never the ambiguous docs line
        self.assertEqual(recommendations['work-a']['sources'], ['perf1.yaml'])
        self.assertEqual(recommendations['work-b']['sources'], ['perf2.yaml'])

    def test_page_without_composer_heading_fails_closed_on_ambiguity(self):
        """No heading evidence: a shared token across composers stays unattributed."""
        self.documents[str(self.root / 'data/works/w2.yaml')] = {
            'id': 'work-b', 'title': 'Harold en Italie', 'composer_id': 'hector-berlioz',
            'catalogue': {'opus': 'Op. 21'}}
        (self.root / 'data/works/w3.yaml').touch()
        (self.root / 'data/persons/p2.yaml').touch()
        self.documents[str(self.root / 'data/works/w3.yaml')] = {
            'id': 'work-c', 'title': 'Diversions', 'composer_id': 'benjamin-britten',
            'catalogue': {'opus': 'Op. 21'}}
        self.documents[str(self.root / 'data/persons/p2.yaml')] = {
            'id': 'benjamin-britten', 'name': 'Benjamin Britten'}
        (self.root / 'docs/composer.md').write_text(
            'No heading here\n\nSomething, Op. 21 [*Names*](http://www.tidal.com/track/555)\n',
            encoding='utf-8')
        recommendations, unattributed, breakdown = reg.existing_recommendations(
            self.root, reg.load_works(self.root))
        self.assertEqual(unattributed, ['composer.md:3 (track 555)'])
        self.assertEqual(breakdown[0]['category'], 'ambiguous-match')
        self.assertNotIn('composer.md:3', recommendations['work-b']['sources'])
        # Without heading evidence neither work receives the line as a recommendation.
        self.assertNotIn('work-c', recommendations)

    def test_recommendation_without_track_anchor_gets_no_playlist(self):
        result = self.run_script(dry_run=True)
        plans = result['report']['playlist_plans']
        # work-b is recommended without a TIDAL track anchor: no plan is produced for it.
        self.assertNotIn('work-b', [p['work_id'] for p in plans])
        # work-a's single anchor expands to its complete recording on album 777.
        self.assertEqual(plans[0]['current_tracks'], ['111', '112'])

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

    def test_album_label_flattens_copyright_object(self):
        # TIDAL returns the copyright as an object; the recording schema stores
        # a plain label string (live album 518875626 rendered 'label: {text: CPO}').
        doc = album_doc()
        doc['data']['attributes']['copyright'] = {'text': ' CPO '}
        client = FakeCatalogClient(doc, [item_page([
            ('222', 'Symphonie fantastique: I. Rêveries',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra'))])])
        self.assertEqual(reg.album_document(client, ALBUM)['label'], 'CPO')


class SchubertCase(unittest.TestCase):
    """The real Schubert: Four Hands album structure: bare movement titles, work in the
    version attribute, no composer credits (title carries the composer family name),
    performers not in canonical data."""

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
        album = album_doc(title='Schubert: Four Hands',
                         artists=('Bertrand Chamayou', 'Leif Ove Andsnes'))
        album['data']['id'] = '461772235'
        self.album_id = '461772235'
        # TIDAL does not return composer credits on the real album, so this
        # case matches works purely through the album title ("Schubert").
        self.client = FakeCatalogClient(album, [item_page([
            ('461772236', 'I. Allegro molto moderato', ('Bertrand Chamayou', 'Leif Ove Andsnes'),             'Fantasia in F Minor, D. 940, Op. 103', None),
            ('461772237', 'II. Largo', ('Bertrand Chamayou', 'Leif Ove Andsnes'),
             'Fantasia in F Minor, D. 940, Op. 103', None),
            ('461772238', 'III. Allegro vivace', ('Bertrand Chamayou', 'Leif Ove Andsnes'),
             'Fantasia in F Minor, D. 940, Op. 103', None),
            ('461772239', 'IV. Finale. Allegro molto moderato', ('Bertrand Chamayou', 'Leif Ove Andsnes'),
             'Fantasia in F Minor, D. 940, Op. 103', None),
            ('461772240', 'Allegro in A Minor, D. 947, Op. posth. 144 "Lebensstürme"',
             ('Bertrand Chamayou', 'Leif Ove Andsnes'), None, None),
            ('461772241', 'Fugue in E Minor, D. 952, Op. posth. 152',
             ('Bertrand Chamayou', 'Leif Ove Andsnes'), None, None),
            ('461772242', 'Rondo in A Major, D. 951, Op. 107',
             ('Bertrand Chamayou', 'Leif Ove Andsnes'), None, None),
        ])], album='461772235')
        # The Perahia/Lupu recommendation (anchor 75254187) is a complete
        # four-movement recording on its own album '888'.
        self.recommendation_client = FakeCatalogClient(
            album_doc_for('888', title='Schubert: Fantasie in F minor',
                          artists=('Murray Perahia', 'Radu Lupu')),
            [item_page([
                ('75254187', 'I. Allegro molto moderato', ('Murray Perahia', 'Radu Lupu'),
                 'Fantasia in F Minor, D. 940, Op. 103', None),
                ('75254188', 'II. Largo', ('Murray Perahia', 'Radu Lupu'),
                 'Fantasia in F Minor, D. 940, Op. 103', None),
                ('75254189', 'III. Allegro vivace', ('Murray Perahia', 'Radu Lupu'),
                 'Fantasia in F Minor, D. 940, Op. 103', None),
                ('75254190', 'IV. Finale. Allegro molto moderato', ('Murray Perahia', 'Radu Lupu'),
                 'Fantasia in F Minor, D. 940, Op. 103', None),
            ])], album='888')
        self.client.track_albums = {'75254187': '888'}

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def run_script(self, **kwargs):
        self.client.reset()
        self.recommendation_client.reset()
        kwargs.setdefault('read_client', self.client)
        kwargs.setdefault('catalog_factory', lambda album: self.recommendation_client)
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
        # The single anchor expands to the complete current recording.
        self.assertEqual(plans[0]['current_tracks'],
                         ['75254187', '75254188', '75254189', '75254190'])
        self.assertEqual(plans[0]['candidate_tracks'],
                         ['461772236', '461772237', '461772238', '461772239'])

    def test_apply_creates_playlist_and_yaml(self):
        user = FakeUserClient()
        result = self.run_script(issue=246, work='franz-schubert-fantasie-in-f-minor-d-940',
                                 user_client_factory=lambda: user)
        self.assertEqual(result['written'], 'data/recordings/schubert-four-hands.yml')
        url = result['report']['playlist_plans'][0]['playlist_url']
        playlist = user.playlists[url.rsplit('/', 1)[-1]]
        self.assertEqual(playlist['items'],
                         ['75254187', '75254188', '75254189', '75254190',
                          '461772236', '461772237', '461772238', '461772239'])
        self.assertEqual(playlist['name'], 'Curator 2026-10-18 Issue #246')
        self.assertIn('Unmatched artists: Bertrand Chamayou, Leif Ove Andsnes',
                      self._read_yaml(self.root / 'data/recordings/schubert-four-hands.yml')['notes'])

    def test_items_fallback_without_credits_include(self):
        self.client.items_include = 'items,items.artists'
        result = self.run_script(dry_run=True)
        candidates = [e for e in result['recording']['works'] if e.get('status') == 'candidate']
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['work_id'], 'franz-schubert-fantasie-in-f-minor-d-940')

    def test_artists_filter_fallback(self):
        self.client.artists_route = 'filter'
        result = self.run_script(dry_run=True)
        self.assertEqual(result['recording']['title'], 'Schubert: Four Hands')

    def test_title_evidence_only_for_family_name(self):
        persons = {'p-schubert': 'Franz Schubert', 'p-other': 'Johann Schubert junior'}
        track = {'id': 'x', 'title': 'Anything', 'version': None, 'artists': [], 'credits': {}}
        # "Schubert junior" is not itself a canonical name, but its family name
        # matches; a name whose family token is not in the title is excluded.
        evidence = reg.composer_evidence(track, [], persons, 'Schubert: Four Hands')
        self.assertIn('p-schubert', evidence)
        self.assertNotIn('p-other', evidence)
        short = reg.composer_evidence(track, [], {'p-bach': 'Johann Bach'}, 'Bach: Works')
        self.assertIn('p-bach', short)
        self.assertEqual(reg.composer_evidence(track, [], {'p-x': 'Anna Al'}, 'Al: Works'), set())

    def test_catalogue_tokens(self):
        self.assertEqual(reg.catalogue_tokens('Fantasia in F Minor, D. 940, Op. 103'),
                         {'d940', 'op103'})
        self.assertEqual(reg.catalogue_tokens('Hob. Ia:7'), set())
        self.assertEqual(reg.catalogue_tokens('Sinfonie Nr. 4 op. 120'), {'op120'})


class ZeroMatchCase(unittest.TestCase):
    """Album whose works are not canonical yet: dry-run reports per track, apply stays fail-closed."""

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'persons', 'artists', 'performances', 'recordings'):
            (self.root / 'data' / name).mkdir(parents=True)
        (self.root / 'docs').mkdir()
        for name in ('data/works/w1.yaml', 'data/persons/p1.yaml', 'data/persons/p2.yaml',
                     'data/artists/performers.yaml', 'docs/composer.md'):
            Path(self.root, name).touch()
        self.documents = {
            # The only canonical work is by a composer absent from this album.
            str(self.root / 'data/works/w1.yaml'): {
                'id': 'work-a', 'title': 'Symphonie fantastique', 'composer_id': 'hector-berlioz'},
            str(self.root / 'data/persons/p1.yaml'): {'id': 'franz-schubert', 'name': 'Franz Schubert'},
            str(self.root / 'data/persons/p2.yaml'): {'id': 'maurice-ravel', 'name': 'Maurice Ravel'},
            str(self.root / 'data/artists/performers.yaml'): {'artists': []},
        }
        self._read_yaml = reg.read_yaml

        def read(path):
            path = str(path)
            return self.documents[path] if path in self.documents else self._read_yaml(path)

        reg.read_yaml = read
        # The album title carries the Schubert family name; none of its works is canonical yet.
        self.client = FakeCatalogClient(
            album_doc(title='Schubert: Piano Works', artists=('Jean-Yves Thibaudet',)),
            [item_page([
                ('501', 'Lebensstürme, D. 947', ('Jean-Yves Thibaudet',)),
                ('502', 'II. Largo', ('Jean-Yves Thibaudet', 'Maurice Ravel'),
                 'Fantasia in F Minor, D. 940, Op. 103'),
                ('503', 'Sonatine', ('Jean-Yves Thibaudet',)),
            ])])

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def run_script(self, **kwargs):
        self.client.reset()
        kwargs.setdefault('read_client', self.client)
        kwargs.setdefault('suggest_client', FakeSuggestionClient())
        return reg.run(self.root, ALBUM_URL, today='2026-10-18', **kwargs)

    def test_dry_run_reports_per_track_without_writing(self):
        result = self.run_script(dry_run=True)
        self.assertEqual(result['recording']['works'], [])
        details = result['report']['unmatched_track_details']
        self.assertEqual([d['position'] for d in details], [1, 2, 3])
        self.assertEqual(details[0]['title'], 'Lebensstürme, D. 947')
        self.assertIsNone(details[0]['version'])
        self.assertEqual(details[0]['catalogue_tokens'], ['d947'])
        self.assertEqual(details[0]['composers'], ['Franz Schubert'])
        self.assertEqual(details[1]['version'], 'Fantasia in F Minor, D. 940, Op. 103')
        self.assertEqual(details[1]['catalogue_tokens'], ['d940', 'op103'])
        self.assertEqual(details[1]['composers'], ['Franz Schubert', 'Maurice Ravel'])
        self.assertEqual(details[2]['catalogue_tokens'], [])
        self.assertIn('nothing to register', result['note'])
        self.assertIn('re-run', result['note'])
        self.assertEqual(list((self.root / 'data/recordings').glob('*.y*ml')), [])

    def test_dry_run_invents_no_work_ids(self):
        result = self.run_script(dry_run=True)
        self.assertEqual(result['report']['works'], [])
        self.assertEqual(result['recording']['works'], [])
        for entry in result['report']['unmatched_track_details']:
            self.assertEqual(entry['candidates'], [])
            self.assertEqual(entry['state'], 'unknown')

    def test_dry_run_creates_no_user_client(self):
        def factory():
            raise AssertionError('Dry run must not create a user client')

        self.run_script(dry_run=True, user_client_factory=factory)

    def test_apply_stays_fail_closed(self):
        with self.assertRaises(ValueError):
            self.run_script(user_client_factory=lambda: FakeUserClient())
        self.assertEqual(list((self.root / 'data/recordings').glob('*.y*ml')), [])

    def test_dry_run_adds_advisory_external_suggestions(self):
        fake = FakeSuggestionClient()
        result = self.run_script(dry_run=True, suggest_client=fake)
        details = result['report']['unmatched_track_details']
        for entry in details:
            self.assertEqual(entry['external_suggestions'][0]['composers'][0]['name'],
                             'Franz Schubert')
        # Version text is searched when present (it carries the work title);
        # identical search texts are looked up once.
        self.assertEqual(fake.queries, ['Lebensstürme, D. 947',
                                         'Fantasia in F Minor, D. 940, Op. 103',
                                         'Sonatine'])
        self.assertFalse(result['report']['external_suggestions_unavailable'])
        # Advisory only: suggestions never enter the recording document.
        self.assertEqual(result['recording']['works'], [])
        notes = result['recording'].get('notes') or ''
        self.assertNotIn('w1', notes)
        self.assertNotIn('Franz Schubert', notes)

    def test_external_suggestions_fail_open(self):
        fake = FakeSuggestionClient(fail=True)
        result = self.run_script(dry_run=True, suggest_client=fake)
        details = result['report']['unmatched_track_details']
        self.assertTrue(details)
        self.assertTrue(all(entry['external_suggestions'] is None for entry in details))
        self.assertTrue(result['report']['external_suggestions_unavailable'])
        self.assertIn('nothing to register', result['note'])
        self.assertEqual(list((self.root / 'data/recordings').glob('*.y*ml')), [])

    def test_external_suggestions_not_fetched_in_apply_mode(self):
        class Probing:
            def work_suggestions(self, text, limit=3):
                raise AssertionError('Suggestions are only consulted on zero-match dry runs')

        with self.assertRaises(ValueError):
            self.run_script(suggest_client=Probing())

    def test_suggestion_search_text_drops_movements_and_arrangements(self):
        self.assertEqual(
            reg.suggestion_search_text('The Unfortunate Traveller: I. Introduction. Allegro moderato'),
            'The Unfortunate Traveller')
        self.assertEqual(
            reg.suggestion_search_text('Movement for Strings in C Minor '
                                       '(Arr. for Chamber Orchestra by Percy Grainger)'),
            'Movement for Strings in C Minor')
        self.assertEqual(
            reg.suggestion_search_text('Prelude, Aria & Finale, Op. 25: III. Finale. Poco allegro'),
            'Prelude, Aria & Finale, Op. 25')
        self.assertEqual(reg.suggestion_search_text('Variations on an Air of Henry Purcell'),
                         'Variations on an Air of Henry Purcell')
        self.assertEqual(reg.suggestion_search_text(''), '')


class AttributionCase(unittest.TestCase):
    """Per-anchor docs attribution (#329): heading given-name evidence, the M
    catalogue prefix, most-specific titles, version-qualifier consistency and
    per-anchor segments. All fail-closed."""

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'persons', 'artists', 'performances', 'recordings'):
            (self.root / 'data' / name).mkdir(parents=True)
        (self.root / 'docs').mkdir()
        (self.root / 'docs/page.md').touch()
        self.documents = {}
        self._read_yaml = reg.read_yaml

        def read(path):
            path = str(path)
            return self.documents[path] if path in self.documents else self._read_yaml(path)

        reg.read_yaml = read

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def add_person(self, person_id, name):
        path = self.root / f'data/persons/{person_id}.yaml'
        path.touch()
        self.documents[str(path)] = {'id': person_id, 'name': name}

    def add_work(self, work_id, title, composer_id, **extra):
        path = self.root / f'data/works/{work_id}.yaml'
        path.touch()
        document = {'id': work_id, 'title': title, 'composer_id': composer_id}
        document.update(extra)
        self.documents[str(path)] = document

    def set_page(self, heading, lines):
        body = heading + '\n\n' + '\n'.join(lines) + '\n'
        (self.root / 'docs/page.md').write_text(body, encoding='utf-8')

    def attribute(self):
        return reg.existing_recommendations(self.root)

    def test_heading_given_name_short_form_matches(self):
        self.add_person('niels-wilhelm-gade', 'Niels Wilhelm Gade')
        self.add_person('carl-nielsen', 'Carl Nielsen')
        self.add_work('gade-symphony-4', 'Symphony No. 4 in E major, Op. 20', 'niels-wilhelm-gade')
        self.add_work('nielsen-quintet', 'Wind Quintet, Op. 20', 'carl-nielsen')
        self.set_page('# Niels Gade', [
            '**Symphony No. 4 in E major**, Op. 20 [*DNRSO*](http://www.tidal.com/track/400)'])
        found, unattributed, _ = self.attribute()
        self.assertEqual(found['gade-symphony-4']['track_ids'], ['400'])
        self.assertEqual(unattributed, [])

    def test_heading_transliteration_stays_fail_closed(self):
        self.add_person('sergei-rachmaninoff', 'Sergei Rachmaninoff')
        self.add_person('johannes-brahms', 'Johannes Brahms')
        self.add_work('rach-vocalise', 'Vocalise, Op. 34 No. 14', 'sergei-rachmaninoff')
        self.add_work('brahms-quintet', 'Piano Quintet in F minor, Op. 34', 'johannes-brahms')
        self.set_page('# Sergej Rachmaninov', [
            '**Vocalise** Op. 34/14 [*Murphy*](http://www.tidal.com/track/900)'])
        found, unattributed, breakdown = self.attribute()
        self.assertEqual(found, {})
        self.assertEqual(unattributed, ['page.md:3 (track 900)'])
        self.assertEqual(breakdown[0]['category'], 'ambiguous-match')

    def test_catalogue_m_prefix_distinguishes_ravel_versions(self):
        self.assertEqual(reg.catalogue_tokens('Le Tombeau de Couperin, M. 68a'), {'m68a'})
        self.add_person('maurice-ravel', 'Maurice Ravel')
        self.add_work('ravel-tombeau-piano', 'Le Tombeau de Couperin, M. 68', 'maurice-ravel')
        self.add_work('ravel-tombeau-orchestral', 'Le tombeau de Couperin, M. 68a', 'maurice-ravel')
        self.set_page('# Maurice Ravel', [
            '**Le Tombeau de Couperin**, M. 68a (1919) [*RSPO, Oramo*](http://www.tidal.com/track/500)'])
        found, unattributed, _ = self.attribute()
        self.assertEqual(found['ravel-tombeau-orchestral']['track_ids'], ['500'])
        self.assertEqual(unattributed, [])

    def test_most_specific_title_beats_generic_titles(self):
        self.add_person('paul-hindemith', 'Paul Hindemith')
        self.add_work('hindemith-piano-concerto', 'Piano Concerto', 'paul-hindemith')
        self.add_work('hindemith-concerto-flute', 'Concerto', 'paul-hindemith')
        self.add_work('hindemith-concerto-trumpet', 'Concerto', 'paul-hindemith')
        self.set_page('# Paul Hindemith', [
            '**Piano Concerto** (1945) [*Mauser, Frankfurt RSO*](http://www.tidal.com/track/600)'])
        found, unattributed, _ = self.attribute()
        self.assertEqual(found['hindemith-piano-concerto']['track_ids'], ['600'])
        self.assertEqual(unattributed, [])

    def test_version_qualifier_evidence_decides_between_versions(self):
        self.add_person('camille-saint-saens', 'Camille Saint-Saëns')
        self.add_work('romance-cello-orchestra', 'Romance in F major, Op. 36 (version for cello and orchestra)',
                      'camille-saint-saens')
        self.add_work('romance-horn-piano', 'Romance, Op. 36 (horn and piano version)', 'camille-saint-saens')
        self.set_page('# Camille Saint-Saëns', [
            '**Romance in F major**, Op. 36, R. 195 for horn (or cello) and orchestra (1874) '
            '[*Müller-Schott, DSO Berlin*](http://www.tidal.com/track/700)'])
        found, unattributed, _ = self.attribute()
        self.assertEqual(found['romance-cello-orchestra']['track_ids'], ['700'])
        self.assertEqual(unattributed, [])

    def test_multi_anchor_line_attributes_each_anchor_to_its_segment(self):
        self.add_person('arnold-schoenberg', 'Arnold Schoenberg')
        self.add_work('verklarte-nacht-sextet', 'Verklärte Nacht, Op. 4 (string sextet)', 'arnold-schoenberg')
        self.add_work('verklarte-nacht-trio', 'Verklärte Nacht, Op. 4 (Steuermann piano trio arrangement)',
                      'arnold-schoenberg')
        self.set_page('# Arnold Schoenberg', [
            '💎 **Verklärte Nacht**, Op. 4 (1899) [string sextet: *Janine Jansen*]'
            '(http://www.tidal.com/track/800) [piano trio: *Linos Piano Trio*]'
            '(http://www.tidal.com/track/801) [chamber ensemble: *Het Collectief*]'
            '(http://www.tidal.com/track/802)'])
        found, unattributed, breakdown = self.attribute()
        self.assertEqual(found['verklarte-nacht-sextet']['track_ids'], ['800'])
        self.assertEqual(found['verklarte-nacht-trio']['track_ids'], ['801'])
        self.assertEqual(unattributed, ['page.md:3 (track 802)'])
        self.assertEqual(breakdown[0]['category'], 'ambiguous-match')

    def test_multi_anchor_line_with_one_work_attributes_all_anchors(self):
        self.add_person('hector-berlioz', 'Hector Berlioz')
        self.add_work('harold', 'Harold en Italie', 'hector-berlioz')
        self.set_page('# Hector Berlioz', [
            '**Harold en Italie** [*Haitink*](http://www.tidal.com/track/100) '
            '[*Dohnányi*](http://www.tidal.com/track/101)'])
        found, unattributed, _ = self.attribute()
        self.assertEqual(found['harold']['track_ids'], ['100', '101'])
        self.assertEqual(unattributed, [])

    def test_qualifier_exclusion_of_all_candidates_stays_ambiguous(self):
        self.add_person('maurice-ravel', 'Maurice Ravel')
        self.add_work('ravel-piano', 'Le Tombeau de Couperin, M. 68 (piano original)', 'maurice-ravel')
        self.add_work('ravel-orchestral', 'Le Tombeau de Couperin, M. 68 (orchestral version)', 'maurice-ravel')
        self.set_page('# Maurice Ravel', [
            '**Le Tombeau de Couperin**, M. 68 [*Unknown Quartet*](http://www.tidal.com/track/501)'])
        found, unattributed, breakdown = self.attribute()
        self.assertEqual(found, {})
        self.assertEqual(unattributed, ['page.md:3 (track 501)'])
        self.assertEqual(breakdown[0]['category'], 'ambiguous-match')


class CanonizeCase(unittest.TestCase):
    """Canonization as part of album registration (#327): unique ISRC-chain
    work + canonical composer evidence -> proposed work; --canonize writes it
    and promotes the track in the same run. Fail-closed otherwise."""

    ISRC = 'NLB341600123'

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'persons', 'artists', 'performances', 'recordings'):
            (self.root / 'data' / name).mkdir(parents=True)
        (self.root / 'docs').mkdir()
        for name in ('data/works/w1.yaml', 'data/persons/p1.yaml',
                     'data/artists/performers.yaml', 'docs/composer.md'):
            Path(self.root, name).touch()
        self.documents = {
            str(self.root / 'data/works/w1.yaml'): {
                'id': 'work-a', 'title': 'Symphonie fantastique', 'composer_id': 'hector-berlioz'},
            str(self.root / 'data/persons/p1.yaml'): {'id': 'franz-schubert', 'name': 'Franz Schubert'},
            str(self.root / 'data/artists/performers.yaml'): {'artists': []},
        }
        self._read_yaml = reg.read_yaml

        def read(path):
            path = str(path)
            return self.documents[path] if path in self.documents else self._read_yaml(path)

        reg.read_yaml = read
        self.client = FakeCatalogClient(
            album_doc(title='Schubert: Piano Works', artists=('Jean-Yves Thibaudet',)),
            [item_page([('501', 'Lebensstürme, D. 947',
                         ('Jean-Yves Thibaudet',), None, None, self.ISRC)])])
        self.suggest = FakeSuggestionClient(isrc_suggestions=[{
            'title': 'Lebensstürme, D. 947', 'musicbrainz_work_id': 'mbw-947',
            'musicbrainz_recording_id': 'mbr-1',
            'composers': [{'name': 'Franz Schubert', 'musicbrainz_artist_id': 'mba-1'}],
            'wikidata_url': 'https://www.wikidata.org/entity/Q123456',
            'source': 'musicbrainz-isrc'}])

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def run_script(self, **kwargs):
        self.client.reset()
        kwargs.setdefault('read_client', self.client)
        kwargs.setdefault('suggest_client', self.suggest)
        return reg.run(self.root, ALBUM_URL, today='2026-10-18', **kwargs)

    def works_dir(self):
        return list((self.root / 'data/works').glob('franz-schubert-lebenssturme*.yaml'))

    def test_dry_run_proposes_new_work_from_isrc_chain(self):
        result = self.run_script(dry_run=True)
        proposals = result['report']['proposed_works']
        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal['work_id'], 'franz-schubert-lebenssturme-d-947')
        self.assertEqual(proposal['composer_id'], 'franz-schubert')
        self.assertEqual(proposal['catalogue'], {'d': 'D. 947'})
        self.assertEqual(proposal['evidence']['isrc'], self.ISRC)
        self.assertEqual(proposal['evidence']['musicbrainz_work_id'], 'mbw-947')
        self.assertEqual(proposal['evidence']['musicbrainz_recording_id'], 'mbr-1')
        self.assertEqual(proposal['evidence']['wikidata_url'],
                         'https://www.wikidata.org/entity/Q123456')
        self.assertEqual(proposal['evidence']['label'], 'Philips')
        # Advisory only: nothing written on a dry run.
        self.assertEqual(self.works_dir(), [])
        self.assertEqual(list((self.root / 'data/recordings').glob('*.y*ml')), [])
        self.assertIn('--canonize', result['note'])

    def test_dry_run_canonize_writes_nothing(self):
        result = self.run_script(dry_run=True, canonize=True)
        self.assertEqual(self.works_dir(), [])
        self.assertEqual(result['report']['canonized_works'], [])
        self.assertTrue(result['report']['proposed_works'])

    def test_apply_without_canonize_stays_fail_closed(self):
        with self.assertRaises(ValueError):
            self.run_script(user_client_factory=lambda: FakeUserClient())
        self.assertEqual(self.works_dir(), [])

    def test_canonize_writes_work_and_promotes_track(self):
        user = FakeUserClient()
        result = self.run_script(canonize=True, user_client_factory=lambda: user)
        work_path = self.root / 'data/works/franz-schubert-lebenssturme-d-947.yaml'
        self.assertTrue(work_path.exists())
        saved_work = self._read_yaml(work_path)
        self.assertEqual(saved_work['id'], 'franz-schubert-lebenssturme-d-947')
        self.assertEqual(saved_work['title'], 'Lebensstürme, D. 947')
        self.assertEqual(saved_work['composer_id'], 'franz-schubert')
        self.assertEqual(saved_work['catalogue'], {'d': 'D. 947'})
        self.assertNotIn('evidence', saved_work)
        self.assertEqual(result['report']['canonized_works'],
                         ['data/works/franz-schubert-lebenssturme-d-947.yaml'])
        candidates = [e for e in result['recording']['works'] if e.get('status') == 'candidate']
        self.assertEqual([c['work_id'] for c in candidates], ['franz-schubert-lebenssturme-d-947'])
        self.assertEqual(result['report']['unmatched_track_details'], [])
        self.assertTrue((self.root / 'data/recordings/schubert-piano-works.yml').exists())

    def test_canonize_refuses_to_overwrite_an_existing_work(self):
        # The work file exists on disk but is not canonical data (no title):
        # the proposal is generated anyway and must refuse to overwrite it.
        path = self.root / 'data/works/franz-schubert-lebenssturme-d-947.yaml'
        path.write_text('id: existing\n')
        with self.assertRaises(ValueError):
            self.run_script(canonize=True, user_client_factory=lambda: FakeUserClient())
        self.assertEqual(list((self.root / 'data/recordings').glob('*.y*ml')), [])
        self.assertEqual(path.read_text(), 'id: existing\n')

    def test_no_proposal_when_composer_is_not_canonical(self):
        self.suggest.isrc_suggestions = [{
            'title': 'Lebensstürme, D. 947', 'musicbrainz_work_id': 'mbw-947',
            'musicbrainz_recording_id': 'mbr-1',
            'composers': [{'name': 'Anton Webern', 'musicbrainz_artist_id': 'mba-2'}],
            'source': 'musicbrainz-isrc'}]
        result = self.run_script(dry_run=True)
        self.assertEqual(result['report']['proposed_works'], [])
        with self.assertRaises(ValueError) as ctx:
            self.run_script(canonize=True, user_client_factory=lambda: FakeUserClient())
        self.assertIn('no safe work proposal', str(ctx.exception))

    def test_no_proposal_without_isrc_or_with_several_matching_works(self):
        # Track without an ISRC: no chain, no proposal.
        self.client = FakeCatalogClient(
            album_doc(title='Schubert: Piano Works', artists=('Jean-Yves Thibaudet',)),
            [item_page([('501', 'Lebensstürme, D. 947', ('Jean-Yves Thibaudet',))])])
        result = self.run_script(dry_run=True)
        self.assertEqual(result['report']['proposed_works'], [])
        self.assertEqual(self.suggest.isrc_queries, [])
        # Two ISRC-chain works with the same composer: ambiguous, no proposal.
        self.client = FakeCatalogClient(
            album_doc(title='Schubert: Piano Works', artists=('Jean-Yves Thibaudet',)),
            [item_page([('501', 'Lebensstürme, D. 947',
                         ('Jean-Yves Thibaudet',), None, None, self.ISRC)])])
        self.suggest.isrc_suggestions = [
            {'title': 'Lebensstürme, D. 947', 'musicbrainz_work_id': 'mbw-1',
             'musicbrainz_recording_id': 'mbr-1',
             'composers': [{'name': 'Franz Schubert'}], 'source': 'musicbrainz-isrc'},
            {'title': 'Lebensstürme, D. 947', 'musicbrainz_work_id': 'mbw-2',
             'musicbrainz_recording_id': 'mbr-2',
             'composers': [{'name': 'Franz Schubert'}], 'source': 'musicbrainz-isrc'}]
        result = self.run_script(dry_run=True)
        self.assertEqual(result['report']['proposed_works'], [])

    def test_null_suggestion_client_fails_open_for_isrc_chain(self):
        result = self.run_script(dry_run=True,
                                 suggest_client=reg.NullSuggestionClient())
        self.assertEqual(result['report']['proposed_works'], [])
        self.assertIn('nothing to register', result['note'])


class CannedMusicBrainzClient(reg.SuggestionClient):
    """SuggestionClient with canned fetch responses; never touches the network."""

    def __init__(self, search_response, detail_responses):
        super().__init__()
        self.search_response = search_response
        self.detail_responses = list(detail_responses)

    def fetch(self, url, **kwargs):
        if 'query=' in url:
            return self.search_response
        return self.detail_responses.pop(0)


class ReportCase(unittest.TestCase):
    def test_work_suggestions_drop_movement_duplicates(self):
        # MusicBrainz returns the work and its movement parts; the parts add no
        # new evidence and must not crowd out the limit (live album 518875626).
        client = CannedMusicBrainzClient(
            {'works': [
                {'id': 'w-parent', 'title': 'Prelude, Aria & Finale, Op. 25'},
                {'id': 'w-mov', 'title': 'Prelude, Aria & Finale, Op. 25: III. Finale. Poco allegro'},
                {'id': 'w-other', 'title': 'Something Else Entirely'},
            ]},
            [{'relations': [{'type': 'composer',
                             'artist': {'id': 'a1', 'name': 'William Mathias'}}]},
             {'relations': []}])
        hits = client.work_suggestions('Prelude, Aria & Finale, Op. 25')
        self.assertEqual([h['musicbrainz_work_id'] for h in hits], ['w-parent', 'w-other'])
        self.assertEqual(hits[0]['composers'][0]['name'], 'William Mathias')
        self.assertEqual(hits[1]['composers'], [])

    def test_slugify(self):
        self.assertEqual(reg.slugify('Berlioz: Symphonie fantastique'), 'berlioz-symphonie-fantastique')
        with self.assertRaises(ValueError):
            reg.slugify('???')


class CursorCatalogClient(FakeCatalogClient):
    """FakeCatalogClient that also serves the cursor-based follow-up page (#340)."""

    def request(self, path, method='GET', body=None, *, idempotency_key=None):
        if path.startswith(f'/v2/albums/{self.album}/relationships/items?') \
                and 'page%5Bcursor%5D' in path:
            if not self.pages:
                raise ValueError('Unexpected extra album page request')
            return self.pages.pop(0)
        return super().request(path, method, body, idempotency_key=idempotency_key)


class PaginationCase(FixtureCase):
    """TIDAL v2 returns relative next hrefs (no scheme, no host, no /v2);
    pagination follows them while staying fail-closed (#340)."""

    def cursor_pages(self, next_href):
        page1 = item_page([
            ('222', 'Symphonie fantastique: I. Rêveries',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
        ])
        page1['links'] = {'next': next_href}
        page2 = item_page([
            ('223', 'Symphonie fantastique: II. Un bal',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
        ])
        return CursorCatalogClient(album_doc(), [page1, page2])

    def test_relative_next_link_is_followed(self):
        # Live form observed 2026-10-24 on album 87860696: relative next href
        # without scheme, host and /v2 prefix, cursor-based.
        self.client = self.cursor_pages(
            f'/albums/{ALBUM}/relationships/items?countryCode=NL&page%5Bcursor%5D=abc')
        result = self.run_script(dry_run=True)
        candidates = {e['work_id']: e for e in result['recording']['works']
                      if e.get('status') == 'candidate'}
        self.assertIn('work-a', candidates)
        self.assertEqual(candidates['work-a']['notes'], 'Spans album tracks 1, 2.')

    def test_absolute_next_link_still_followed(self):
        self.client = self.cursor_pages(
            f'https://openapi.tidal.com/v2/albums/{ALBUM}/relationships/items?page%5Bcursor%5D=abc')
        result = self.run_script(dry_run=True)
        self.assertIn('work-a', {e['work_id'] for e in result['recording']['works']})

    def test_foreign_album_pagination_target_stays_fail_closed(self):
        page1 = item_page([
            ('222', 'Symphonie fantastique: I. Rêveries',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
        ])
        page1['links'] = {'next': '/albums/111111/relationships/items?page%5Bcursor%5D=abc'}
        client = FakeCatalogClient(album_doc(), [page1])
        with self.assertRaises(ValueError) as ctx:
            reg.run(self.root, ALBUM_URL, dry_run=True, read_client=client, today='2026-10-24')
        self.assertIn('pagination', str(ctx.exception))


class PlaylistIssueCase(FixtureCase):
    """Comparison playlists are created per issue (--issue + --work), named
    "Curator <date> Issue #<nr>", with the current recommendation as its
    complete recording. Fail-closed on half flags, unbound works and
    fragmentary anchors (#316 feedback)."""

    def test_issue_binding_is_written_to_the_recording(self):
        # --issue/--work binds the candidate for ./curator <issue> <choice>:
        # issue number, candidate track IDs in album order, reviewed performers.
        result = self.run_script(issue=316, work='work-a', user_client_factory=lambda: FakeUserClient())
        saved = self._read_yaml(self.root / 'data/recordings/test-album.yml')
        entry = next(e for e in saved['works'] if e['work_id'] == 'work-a')
        self.assertEqual(entry['issue'], 316)
        self.assertEqual(entry['track_ids'], ['222', '223'])
        self.assertIn('Royal Concertgebouw Orchestra (orchestra)', entry['performers'])
        self.assertIn('Hector Berlioz', entry['performers'])
        # Other candidates stay untouched.
        other = next(e for e in saved['works'] if e['work_id'] == 'work-b')
        self.assertNotIn('issue', other)

    def test_update_existing_replaces_the_bound_entry(self):
        # First run without --issue leaves the entry unbound; a re-run with
        # --issue/--work --update-existing replaces it with the bound entry.
        self.run_script(user_client_factory=lambda: FakeUserClient())
        self.run_script(issue=316, work='work-a', update_existing=True,
                        user_client_factory=lambda: FakeUserClient())
        saved = self._read_yaml(self.root / 'data/recordings/test-album.yml')
        bound = [e for e in saved['works'] if e.get('issue')]
        self.assertEqual(len(bound), 1)
        self.assertEqual(bound[0]['work_id'], 'work-a')
        self.assertEqual(bound[0]['track_ids'], ['222', '223'])
        self.assertEqual([e['work_id'] for e in saved['works'] if e['work_id'] == 'work-b'],
                         ['work-b'])

    def test_without_issue_no_playlist_is_created(self):
        def factory():
            raise AssertionError('A run without --issue must not create a user client')
        result = self.run_script(user_client_factory=factory)
        self.assertEqual(result['playlists'], [])
        self.assertIn('re-run with --issue', result['report']['playlist_notice'])

    def test_issue_and_work_are_supplied_together(self):
        with self.assertRaises(ValueError):
            self.run_script(issue=316, user_client_factory=lambda: FakeUserClient())
        with self.assertRaises(ValueError):
            self.run_script(work='work-a', user_client_factory=lambda: FakeUserClient())

    def test_issue_work_without_playlist_on_this_album_fails_closed(self):
        # work-b is recommended without a TIDAL track anchor: binding an issue
        # to it must fail instead of silently creating nothing.
        with self.assertRaises(ValueError) as ctx:
            self.run_script(issue=316, work='work-b', user_client_factory=lambda: FakeUserClient())
        self.assertIn('no comparison playlist', str(ctx.exception))

    def test_fragmentary_anchor_skips_playlist_with_report(self):
        # The anchor's album serves tracks that match nothing: expansion must
        # refuse a fragment and skip the playlist, without failing the run.
        broken = FakeCatalogClient(album_doc_for('777'), [item_page([
            ('111', 'Something Else Entirely', ('Murray Perahia',))])], album='777')
        result = self.run_script(dry_run=True, catalog_factory=lambda album: broken)
        self.assertEqual(result['report']['playlist_plans'], [])
        self.assertEqual(len(result['report']['playlist_errors']), 1)
        self.assertIn('fragmentary', result['report']['playlist_errors'][0]['error'])
        self.assertEqual(result['report']['playlist_errors'][0]['work_id'], 'work-a')

    def test_consolidation_anchor_on_candidate_album_lists_tracks_once(self):
        # The existing anchor sits on the candidate's own album (Biondi-style
        # consolidation): the comparison lists the recording once.
        self.documents[str(self.root / 'data/performances/perf1.yaml')] = {
            'id': 'perf1', 'work_id': 'work-a', 'recommended': True,
            'performers': [{'name': 'Hector Berlioz'}],
            'links': {'tidal': {'url': 'https://tidal.com/track/222'}}}
        (self.root / 'docs/composer.md').write_text('', encoding='utf-8')
        self.client.track_albums = {'222': ALBUM}
        candidate_album = FakeCatalogClient(album_doc(), [item_page([
            ('222', 'Symphonie fantastique: I. Rêveries',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
            ('223', 'Symphonie fantastique: II. Un bal',
             ('Hector Berlioz', 'Royal Concertgebouw Orchestra')),
        ])])
        user = FakeUserClient()
        result = self.run_script(issue=212, work='work-a', catalog_factory=lambda album: candidate_album,
                                user_client_factory=lambda: user)
        url = result['report']['playlist_plans'][0]['playlist_url']
        self.assertEqual(user.playlists[url.rsplit('/', 1)[-1]]['items'], ['222', '223'])
        self.assertEqual(user.playlists[url.rsplit('/', 1)[-1]]['name'],
                         'Curator 2026-10-18 Issue #212')

    def test_script_tail_is_intact(self):
        # Hotfix-regressie (#342): een afgebroken push verwijderde ooit de
        # entry-point van het script; het bestand moet eindigen op de guard.
        source = (Path(__file__).resolve().parents[1]
                  / 'scripts/register_earmarked_recording.py').read_text(encoding='utf-8')
        self.assertIn("if __name__ == '__main__':", source)
        self.assertTrue(source.rstrip().endswith('sys.exit(main())'))



class VariantCase(unittest.TestCase):
    """Movement variants with a parenthetical 'with ... from <catalogue>' marker
    (#350, Biondi RV 179a on Vol. 71): the variant take is skipped -- no
    ambiguous second work, one clean candidate, bindings and comparison
    playlists without the variant, on both the candidate and the current side."""

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'persons', 'artists', 'performances', 'recordings'):
            (self.root / 'data' / name).mkdir(parents=True)
        (self.root / 'docs').mkdir()
        for name in ('data/works/w1.yaml', 'data/works/w2.yaml', 'data/persons/p1.yaml',
                     'data/artists/performers.yaml', 'data/performances/perf1.yaml',
                     'docs/composer.md'):
            Path(self.root, name).touch()
        self.documents = {
            str(self.root / 'data/works/w1.yaml'): {
                'id': 'work-a', 'title': 'Violin Concerto, RV 179a',
                'composer_id': 'antonio-vivaldi', 'catalogue': {'rv': 'RV 179a'}},
            str(self.root / 'data/works/w2.yaml'): {
                'id': 'work-b',
                'title': 'Concerto for violin and double string orchestra, RV 581',
                'composer_id': 'antonio-vivaldi', 'catalogue': {'rv': 'RV 581'}},
            str(self.root / 'data/persons/p1.yaml'): {
                'id': 'antonio-vivaldi', 'name': 'Antonio Vivaldi'},
            str(self.root / 'data/artists/performers.yaml'): {'artists': []},
            str(self.root / 'data/performances/perf1.yaml'): {
                'id': 'perf1', 'work_id': 'work-a', 'recommended': True,
                'performers': [{'name': 'Fabio Biondi'}],
                'links': {'tidal': {'url': 'https://tidal.com/track/301'}}},
        }
        (self.root / 'docs/composer.md').write_text('', encoding='utf-8')
        self._read_yaml = reg.read_yaml

        def read(path):
            path = str(path)
            if path in self.documents:
                return self.documents[path]
            return self._read_yaml(path)

        reg.read_yaml = read
        tracks = [
            ('301', 'Violin Concerto in C Major, RV 179a: I. Allegro ma poco',
             ('Fabio Biondi',)),
            ('302', 'Violin Concerto in C Major, RV 179a: II. Largo',
             ('Fabio Biondi',)),
            ('303', 'Violin Concerto in C Major, RV 179a: II. Largo '
                    '(with original ornementation from RV 581)', ('Fabio Biondi',)),
            ('304', 'Violin Concerto in C Major, RV 179a: III. Allegro',
             ('Fabio Biondi',)),
        ]
        album = album_doc(title='Vivaldi: Concerti per violino XI',
                          artists=('Fabio Biondi', 'Europa Galante'))
        # The anchor (track 301) sits on the candidate's own album
        # (Biondi-style consolidation): both clients serve the same album --
        # the read client for the candidate side, the catalog factory for the
        # anchor expansion, which refetches the album as a separate client.
        def client_for_album():
            return FakeCatalogClient(album, [item_page(tracks)],
                                     track_albums={'301': ALBUM})
        self.client = client_for_album()
        self.recommendation_client = client_for_album()

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def run_script(self, **kwargs):
        self.client.reset()
        self.recommendation_client.reset()
        kwargs.setdefault('read_client', self.client)
        kwargs.setdefault('catalog_factory', lambda album: self.recommendation_client)
        return reg.run(self.root, ALBUM_URL, today='2026-10-18', **kwargs)

    def test_variant_marker_detection_is_explicit(self):
        self.assertEqual(reg.variant_provenance(
            'Violin Concerto in C Major, RV 179a: II. Largo '
            '(with original ornementation from RV 581)'),
            'with original ornementation from RV 581')
        # Arrangement and version qualifiers are not variant markers.
        self.assertIsNone(reg.variant_provenance(
            'II. Largo (Arr. for Chamber Orchestra by Percy Grainger)'))
        self.assertIsNone(reg.variant_provenance('Romance (version for cello and orchestra)'))
        self.assertIsNone(reg.variant_provenance('II. Largo (with notes from the editor)'))
        self.assertIsNone(reg.variant_provenance('II. Largo with piano'))

    def test_variant_take_is_skipped_and_reported(self):
        result = self.run_script(dry_run=True)
        candidates = {e['work_id']: e for e in result['recording']['works']
                      if e.get('status') == 'candidate'}
        self.assertEqual(set(candidates), {'work-a'})
        self.assertEqual(candidates['work-a']['notes'], 'Spans album tracks 1, 2, 4.')
        # No unevaluated entry: RV 581 never entered the recording.
        self.assertFalse([e for e in result['recording']['works'] if 'status' not in e])
        self.assertNotIn('work-b', {e['work_id'] for e in result['recording']['works']})
        self.assertIn('Skipped variant tracks: 3.', result['recording']['notes'])
        variants = [u for u in result['report']['unmatched_tracks']
                    if u['state'] == 'variant']
        self.assertEqual(len(variants), 1)
        self.assertIn('ornementation', variants[0]['title'])
        # The comparison plan keeps the variant out of both sides.
        plan = result['report']['playlist_plans'][0]
        self.assertEqual(plan['current_tracks'], ['301', '302', '304'])
        self.assertEqual(plan['candidate_tracks'], ['301', '302', '304'])

    def test_variant_stays_out_of_binding_and_consolidation_playlist(self):
        user = FakeUserClient()
        result = self.run_script(issue=212, work='work-a',
                                 user_client_factory=lambda: user)
        self.assertEqual(result['written'], 'data/recordings/vivaldi-concerti-per-violino-xi.yml')
        saved = self._read_yaml(self.root / 'data/recordings/vivaldi-concerti-per-violino-xi.yml')
        entry = next(e for e in saved['works'] if e['work_id'] == 'work-a')
        self.assertEqual(entry['track_ids'], ['301', '302', '304'])
        url = result['report']['playlist_plans'][0]['playlist_url']
        playlist = user.playlists[url.rsplit('/', 1)[-1]]
        # The anchor sits on the candidate's own album (Biondi-style
        # consolidation): the recording is listed once, without the variant.
        self.assertEqual(playlist['items'], ['301', '302', '304'])
        self.assertEqual(playlist['name'], 'Curator 2026-10-18 Issue #212')

if __name__ == '__main__':
    unittest.main()
