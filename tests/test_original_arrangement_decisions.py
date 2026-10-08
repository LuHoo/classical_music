"""Curator decisions retain originals, arrangements and explicit excerpt coverage."""
import json
from pathlib import Path

from ruamel.yaml import YAML

from classical_music.publication_site import PublicationSiteGenerator

ROOT = Path(__file__).resolve().parents[1]


def test_decisions_match_recommendations_and_publication():
    report = json.loads((ROOT / 'reports/curator-decisions/original-arrangement-2026-10-04.json').read_text())
    yaml = YAML(typ='safe')
    records = [yaml.load(path.read_text()) for path in (ROOT / 'data/performances').glob('*.yaml')]
    performances = {p['id']: p for p in records}
    generated = PublicationSiteGenerator(ROOT).generate()
    assert len(report['decisions']) == 15
    for decision in report['decisions']:
        assert decision['decision_comment'].startswith(decision['issue_url'] + '#issuecomment-')
        selected = decision['performances']
        actual = [p for p in records if p['work_id'] == decision['work_id']]
        assert {p['id'] for p in actual} == {p['performance_id'] for p in selected}
        assert len({p['profile'] for p in actual}) == len(actual) == 2
        page = (generated.output_dir / 'works' / (decision['work_id'] + '.md')).read_text()
        for selection in selected:
            perf = performances[selection['performance_id']]
            assert perf['profile'] == selection['profile']
            assert perf['source']['curator_decision'] == decision['decision_comment']
            assert selection['tidal_url'].replace('http://', 'https://') in page or selection['tidal_url'] in page
            assert perf['profile'] in page
        for unit in decision['source_units']:
            perf = performances[unit['performance_id']]
            assert perf.get('excerpt') == unit.get('excerpt')
            if unit.get('excerpt'):
                assert unit['excerpt'] in page
            assert unit['positions'] == [t['position'] for t in unit['tracks']]
            assert all(t['id'] and t['item_id'] and t['isrc'] for t in unit['tracks'])
