import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if not (SCRIPTS / 'create_work.py').exists():
    SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / 'src'))

import register_earmarked_recording as reg
import create_work as cw


class FakeSuggestionClient:
    """Canned MusicBrainz double: never touches the network."""

    def __init__(self, suggestions=None, fail=False):
        self.suggestions = suggestions if suggestions is not None else [
            {'title': 'Violin Concerto', 'musicbrainz_work_id': 'w1', 'source': 'musicbrainz',
             'composers': [{'name': 'Richard Strauss', 'musicbrainz_artist_id': 'a1'}]}]
        self.fail = fail
        self.queries = []

    def work_suggestions(self, text, limit=3):
        self.queries.append(text)
        if self.fail:
            raise OSError('External lookups unavailable')
        return self.suggestions


class CreateWorkCase(unittest.TestCase):
    """Canonical data is injected through read_yaml; apply writes real files."""

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'work-groups', 'persons'):
            (self.root / 'data' / name).mkdir(parents=True)
        for name in ('data/works/w1.yaml', 'data/works/w2.yaml',
                     'data/persons/p1.yaml', 'data/persons/p2.yaml'):
            Path(self.root, name).touch()
        self.documents = {
            str(self.root / 'data/works/w1.yaml'): {
                'id': 'richard-strauss-don-juan', 'title': 'Don Juan',
                'composer_id': 'richard-strauss', 'catalogue_values': []},
            str(self.root / 'data/works/w2.yaml'): {
                'id': '388053797e01483593f1e62c6dd407ab-rhapsody-no-1',
                'title': 'Rhapsody No. 1 for violin and orchestra (1929 revision)',
                'composer_id': '388053797e01483593f1e62c6dd407ab', 'catalogue_values': []},
            str(self.root / 'data/persons/p1.yaml'): {'id': 'richard-strauss', 'name': 'Richard Strauss'},
            str(self.root / 'data/persons/p2.yaml'): {
                'id': '388053797e01483593f1e62c6dd407ab', 'name': 'Béla Bartók'},
        }
        self._read_yaml = reg.read_yaml

        def read(path):
            path = str(path)
            if path in self.documents:
                return self.documents[path]
            return self._read_yaml(path)

        reg.read_yaml = read

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def mint(self, **kwargs):
        kwargs.setdefault('title', 'Violin Concerto in D Minor, Op. 8')
        kwargs.setdefault('composer', 'Richard Strauss')
        kwargs.setdefault('catalogue_entries', cw.parse_catalogue_entries(['Op. 8', 'TrV 110']))
        kwargs.setdefault('source_url', 'https://tidal.com/browse/album/557059316')
        kwargs.setdefault('suggest_client', FakeSuggestionClient())
        return cw.run_mint(self.root, **kwargs)

    def test_parse_catalogue_entry(self):
        self.assertEqual(cw.parse_catalogue_entry('Sz. 87'), ('sz', 'Sz. 87'))
        self.assertEqual(cw.parse_catalogue_entry('Op. 8'), ('op', 'Op. 8'))
        self.assertEqual(cw.parse_catalogue_entry('BWV 1052'), ('bwv', 'BWV 1052'))
        with self.assertRaises(ValueError):
            cw.parse_catalogue_entry('Something else')
        with self.assertRaises(ValueError):
            cw.parse_catalogue_entry('Op. 8 and more')
        with self.assertRaises(ValueError):
            cw.parse_catalogue_entries(['Op. 8', 'Op. 9'])

    def test_composer_must_resolve_to_exactly_one_person(self):
        with self.assertRaises(ValueError):
            self.mint(composer='Arnold Schoenberg')
        # Name and ID both resolve; accents are normalized away.
        self.assertEqual(
            cw.resolve_composer(reg.load_persons(self.root), 'Béla Bartók'),
            '388053797e01483593f1e62c6dd407ab')
        self.assertEqual(
            cw.resolve_composer(reg.load_persons(self.root), 'richard-strauss'),
            'richard-strauss')

    def test_mint_preview_derives_ids_and_writes_nothing(self):
        result = self.mint()
        self.assertEqual(result['work_id'], 'richard-strauss-violin-concerto-in-d-minor-op-8')
        self.assertEqual(result['work_group_id'],
                         'richard-strauss-violin-concerto-in-d-minor-op-8-group')
        self.assertIn('id: richard-strauss-violin-concerto-in-d-minor-op-8', result['work_yaml'])
        self.assertIn('catalogue:', result['work_yaml'])
        self.assertIn("op: Op. 8", result['work_yaml'])
        self.assertIn('tidal.com/browse/album/557059316', result['work_yaml'])
        self.assertIn('richard-strauss-violin-concerto-in-d-minor-op-8-group', result['group_yaml'])
        self.assertFalse(result['apply'])
        self.assertEqual(sorted(p.name for p in (self.root / 'data/works').glob('*')),
                          ['w1.yaml', 'w2.yaml'])
        self.assertEqual(list((self.root / 'data/work-groups').glob('*')), [])

    def test_mint_apply_writes_work_and_group(self):
        result = self.mint(apply=True)
        self.assertEqual(result['written'], [
            'data/work-groups/richard-strauss-violin-concerto-in-d-minor-op-8-group.yaml',
            'data/works/richard-strauss-violin-concerto-in-d-minor-op-8.yaml'])
        saved = reg.read_yaml(self.root / 'data/works' / 'richard-strauss-violin-concerto-in-d-minor-op-8.yaml')
        self.assertEqual(saved['composer_id'], 'richard-strauss')
        self.assertEqual(saved['work_group_id'],
                         'richard-strauss-violin-concerto-in-d-minor-op-8-group')
        self.assertEqual(saved['catalogue'], {'op': 'Op. 8', 'trv': 'TrV 110'})
        self.assertEqual(saved['source']['url'], 'https://tidal.com/browse/album/557059316')
        group = reg.read_yaml(self.root / 'data/work-groups' / 'richard-strauss-violin-concerto-in-d-minor-op-8-group.yaml')
        self.assertEqual(group['title'], 'Violin Concerto in D Minor, Op. 8')

    def test_slug_override_and_existing_group(self):
        (self.root / 'data/work-groups/existing-group.yaml').touch()
        self.documents[str(self.root / 'data/work-groups/existing-group.yaml')] = {
            'id': 'existing-group', 'composer_id': 'richard-strauss', 'title': 'Existing'}
        result = self.mint(slug='violin-concerto', work_group_id='existing-group')
        self.assertEqual(result['work_id'], 'richard-strauss-violin-concerto')
        self.assertIsNone(result['group_yaml'])
        self.assertIn('work_group_id: existing-group', result['work_yaml'])

    def test_existing_group_must_exist(self):
        with self.assertRaises(ValueError):
            self.mint(work_group_id='missing-group')

    def test_existing_work_id_blocks_mint(self):
        with self.assertRaises(ValueError):
            self.mint(slug='don-juan')

    def test_shared_catalogue_token_blocks_mint_in_favour_of_enrichment(self):
        # The live Sz. 87 case: an existing Bartók work carries BB 94b; minting a
        # second work that also claims Sz. 87 would duplicate it.
        self.documents[str(self.root / 'data/works/w2.yaml')] = {
            'id': '388053797e01483593f1e62c6dd407ab-rhapsody-no-1',
            'title': 'Rhapsody No. 1 for violin and orchestra (1929 revision)',
            'composer_id': '388053797e01483593f1e62c6dd407ab',
            'catalogue': {'bb': 'BB 94b'}, 'catalogue_values': ['BB 94b']}
        with self.assertRaises(ValueError) as caught:
            self.mint(title='Rhapsody No. 1', composer='Béla Bartók',
                      catalogue_entries=cw.parse_catalogue_entries(['Sz. 87', 'BB 94b']))
        self.assertIn('--enrich', str(caught.exception))
        self.assertIn('388053797e01483593f1e62c6dd407ab-rhapsody-no-1', str(caught.exception))

    def test_title_containment_is_a_warning_not_a_blocker(self):
        result = self.mint()  # "Violin Concerto in D Minor, Op. 8" contains no existing title
        self.assertEqual(result['title_warnings'], [])
        # A new "Don Juan (early version)" overlaps the existing "Don Juan" title.
        result = self.mint(title='Don Juan, early version', slug='don-juan-early',
                           catalogue_entries=[])
        warnings = result['title_warnings']
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['work_id'], 'richard-strauss-don-juan')

    def test_source_is_mandatory(self):
        with self.assertRaises(ValueError):
            self.mint(source_url=None)

    def test_musicbrainz_suggestions_are_advisory_only(self):
        result = self.mint()
        self.assertTrue(result['external_suggestions'])
        self.assertNotIn('musicbrainz', result['work_yaml'])
        # Explicitly confirmed MBID is stored as evidence, nothing else.
        result = self.mint(musicbrainz_work_id='00000000-0000-0000-0000-000000000001')
        self.assertIn("musicbrainz: 00000000-0000-0000-0000-000000000001", result['work_yaml'])
        with self.assertRaises(ValueError):
            self.mint(musicbrainz_work_id='not-a-mbid')

    def test_suggestions_fail_open(self):
        result = self.mint(suggest_client=FakeSuggestionClient(fail=True))
        self.assertIsNone(result['external_suggestions'])

    def test_apply_never_overwrites_existing_files(self):
        path = self.root / 'data/works' / 'richard-strauss-violin-concerto-in-d-minor-op-8.yaml'
        path.write_text('id: taken\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.mint(apply=True)


class EnrichCase(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp())
        for name in ('works', 'work-groups', 'persons'):
            (self.root / 'data' / name).mkdir(parents=True)
        self.path = self.root / 'data/works' / '388053797e01483593f1e62c6dd407ab-rhapsody.yaml'
        self.path.write_text(
            'id: 388053797e01483593f1e62c6dd407ab-rhapsody\n'
            'work_group_id: 388053797e01483593f1e62c6dd407ab-rhapsody-group\n'
            'composer_id: 388053797e01483593f1e62c6dd407ab\n'
            'title: Rhapsody No. 1 for violin and orchestra (1929 revision)\n'
            'catalogue:\n  bb: BB 94b\n'
            'version: 1929 revision for violin and orchestra\n',
            encoding='utf-8')
        self._read_yaml = reg.read_yaml

    def tearDown(self):
        reg.read_yaml = self._read_yaml

    def enrich(self, **kwargs):
        kwargs.setdefault('work_id', '388053797e01483593f1e62c6dd407ab-rhapsody')
        kwargs.setdefault('catalogue_entries', cw.parse_catalogue_entries(['Sz. 87']))
        return cw.run_enrich(self.root, **kwargs)

    def test_unknown_work_fails_closed(self):
        with self.assertRaises(ValueError):
            self.enrich(work_id='nope')

    def test_enrich_needs_something_to_do(self):
        with self.assertRaises(ValueError):
            self.enrich(catalogue_entries=[], aliases=[])

    def test_enrich_preview_shows_change_and_writes_nothing(self):
        result = self.enrich()
        self.assertEqual(result['changes'], ['catalogue sz: Sz. 87'])
        self.assertIn('sz: Sz. 87', result['work_yaml'])
        self.assertIn('bb: BB 94b', result['work_yaml'])
        self.assertFalse(result['apply'])
        saved = reg.read_yaml(self.path)
        self.assertEqual(saved['catalogue'], {'bb': 'BB 94b'})

    def test_enrich_apply_adds_catalogue_value(self):
        result = self.enrich(apply=True)
        self.assertEqual(result['written'], 'data/works/388053797e01483593f1e62c6dd407ab-rhapsody.yaml')
        saved = reg.read_yaml(self.path)
        self.assertEqual(saved['catalogue'], {'bb': 'BB 94b', 'sz': 'Sz. 87'})
        self.assertEqual(saved['title'], 'Rhapsody No. 1 for violin and orchestra (1929 revision)')
        # The missing Sz. 87 token is exactly what the earmarked matcher needs.
        self.assertIn('sz87', reg.catalogue_tokens('Sz. 87') & reg.work_catalogue_tokens(
            {'title': saved['title'], 'aliases': saved.get('aliases', []),
             'catalogue_values': list(saved['catalogue'].values())}))

    def test_enrich_refuses_conflicting_catalogue_key(self):
        with self.assertRaises(ValueError) as caught:
            self.enrich(catalogue_entries=cw.parse_catalogue_entries(['BB 94b']), apply=True)
        self.assertIn('review the file manually', str(caught.exception))

    def test_enrich_same_value_is_reported_and_apply_is_a_no_op(self):
        result = self.enrich(catalogue_entries=cw.parse_catalogue_entries(['BB 94b']))
        self.assertEqual(result['changes'], [])
        self.assertEqual(result['unchanged'], ['catalogue bb: BB 94b'])
        with self.assertRaises(ValueError):
            self.enrich(catalogue_entries=cw.parse_catalogue_entries(['BB 94b']), apply=True)

    def test_enrich_aliases(self):
        result = self.enrich(catalogue_entries=[], aliases=['Rhapsody No. 1, Sz. 87'], apply=True)
        self.assertEqual(result['changes'], ['alias Rhapsody No. 1, Sz. 87'])
        saved = reg.read_yaml(self.path)
        self.assertEqual(saved['aliases'], ['Rhapsody No. 1, Sz. 87'])


class RunDispatchCase(unittest.TestCase):
    def test_enrich_mode_rejects_mint_arguments(self):
        with self.assertRaises(ValueError):
            cw.run(None, enrich='work-id', title='A Title')
        with self.assertRaises(ValueError):
            cw.run(None, enrich='work-id', source_url='https://example.com')
        with self.assertRaises(ValueError):
            cw.run(None)
        with self.assertRaises(ValueError):
            cw.run(None, title='A Title')


if __name__ == '__main__':
    unittest.main()
