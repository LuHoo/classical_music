"""Curator decisions retain originals, arrangements and explicit excerpt coverage."""
import json
import re
from pathlib import Path

from classical_music.publication_site import PublicationSiteGenerator
from classical_music.tidal_maintenance import resource

ROOT = Path(__file__).resolve().parents[1]


def test_decisions_match_recommendations_and_publication(tmp_path, canonical_records):
    report = json.loads((ROOT / 'reports/curator-decisions/original-arrangement-2026-10-04.json').read_text())
    performances = canonical_records['performances']
    records = list(performances.values())
    # Generated pages belong in the test's temporary directory, never in the checkout.
    generated = PublicationSiteGenerator(ROOT, tmp_path / 'publication').generate()
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
            # Decision records keep the historical URL form (legacy http/www
            # and browse/...?u variants); the publication pages carry the
            # canonical form. Match on Tidal resource identity, not string.
            target = resource(selection['tidal_url'])
            assert target is not None
            hrefs = re.findall(r'href="(https?://[^"]+)"', page)
            assert any(
                resource(href) == target for href in hrefs
            ), f"{selection['tidal_url']} not anchored canonically on the page"
            assert perf['profile'] in page
        for unit in decision['source_units']:
            perf = performances[unit['performance_id']]
            assert perf.get('excerpt') == unit.get('excerpt')
            if unit.get('excerpt'):
                assert unit['excerpt'] in page
            assert unit['positions'] == [t['position'] for t in unit['tracks']]
            assert all(t['id'] and t['item_id'] and t['isrc'] for t in unit['tracks'])
