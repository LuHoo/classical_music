"""Explicit intake adapters; issue discovery never guesses curator choices.

New intake families register a pattern and supply their own audit/report adapter.
The decision engine operates on reviewed unit IDs, not playlist titles or order.
"""
from collections import Counter
from dataclasses import dataclass
import json
import re

from classical_music.chamber_import import decision_reference, validate_decision_records


@dataclass(frozen=True)
class Intake:
    key: str
    pattern: str
    format: str
    audit_module: str

    def report(self, manifest_path):
        return (manifest_path.with_suffix('.md') if self.format == 'window'
                else manifest_path.parent / 'README.md')

    def audit(self, root, manifest_path):
        from importlib import import_module
        module = import_module(self.audit_module)
        audit = module.audit_decisions if self.format == 'window' else module.audit
        return audit(root / manifest_path, root) if self.format == 'window' else audit(root)


INTAKES = (
    Intake('chamber', 'chamber/snapshot-2026-10-04.json', 'snapshot', 'classical_music.chamber_import'),
    Intake('piano', 'piano/snapshot-2026-10-04.json', 'snapshot', 'classical_music.piano_import'),
    Intake('best-classical', 'best-classical/window-*.json', 'window', 'classical_music.best_classical_import'),
)


def locate(root, issue):
    url = f'https://github.com/LuHoo/classical_music/issues/{issue}'
    matches = []
    for intake in INTAKES:
        for path in sorted((root / 'reports/playlist-import').glob(intake.pattern)):
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError('Manifest escapes repository')
            manifest = json.loads(path.read_text())
            for key in ('recommendation_choices', 'resolved_choices'):
                for choice in manifest.get(key, []):
                    if choice.get('issue_url') == url:
                        matches.append((intake, path.relative_to(root), manifest))
    if len(matches) != 1:
        raise ValueError(f'Issue #{issue} must identify exactly one registered curator choice; found {len(matches)}. '
                         'Best Classical legacy windows require reviewed issue/unit registration first.')
    return matches[0]


def refresh_window(manifest):
    units = manifest['units']
    counts = manifest['counts']
    counts['track_dispositions'] = dict(Counter(u['disposition'] for u in units for _ in u['tracks']))
    counts['unit_dispositions'] = dict(Counter(u['disposition'] for u in units))
    counts['new_records'] = dict(Counter(r.get('entity', r.get('entity_type')) for r in manifest['new_records']))
    counts['changed_existing'] = len(manifest['changed_existing'])
    counts['existing_performances_unique'] = len({u['performance_id'] for u in units
                                                if u['disposition'] == 'reuse_existing'})


def update_report(text, manifest, intake):
    """Keep historical window narrative; put clearly labelled current totals first."""
    if intake.format != 'window':
        raise ValueError('Expected window report')
    start, end = '<!-- curator-current:start -->', '<!-- curator-current:end -->'
    lines = [start, '## Current curator status', '',
             'The original import report below is historical. Current dispositions and decisions:', '',
             '| Result | Units | Source occurrences |', '|---|---:|---:|']
    for status, count in manifest['counts']['unit_dispositions'].items():
        lines.append(f"| {status} | {count} | {manifest['counts']['track_dispositions'][status]} |")
    lines += ['', f"New canonical records: {manifest['counts']['new_records']}.", '']
    for choice in manifest.get('resolved_choices', []):
        lines.append(f"- {choice['issue_url']}: {', '.join(choice['decision']['selected_units']) or 'existing'}")
    lines += [end, '']
    text = re.sub(re.escape(start) + r'.*?' + re.escape(end) + r'\s*', '', text, flags=re.S)
    return '\n'.join(lines) + '\n' + text


def validate_choices(manifest, data, root):
    """Extra choice invariants for legacy windows, including local decision evidence."""
    all_choices = manifest.get('recommendation_choices', []) + manifest.get('resolved_choices', [])
    assert len({c['work_id'] for c in all_choices}) == len(all_choices), 'Repeated Work choice'
    by_id = {u['unit_id']: u for u in manifest['units'] if u.get('unit_id')}
    assert len(by_id) == sum(bool(u.get('unit_id')) for u in manifest['units']), 'Duplicate unit IDs'
    covered_rejections = set()
    for choice in all_choices:
        assert len(set(choice['units'])) == len(choice['units'])
        units = [by_id[uid] for uid in choice['units']]
        assert all(u['work_id'] == choice['work_id'] and u['curator_issue'] == choice['issue_url'] for u in units)
        assert {u.get('unit_id') for u in manifest['units'] if u.get('work_id') == choice['work_id']} == set(choice['units'])
        actual = {p['id'] for p in data['performances'].values() if p['work_id'] == choice['work_id']}
        decision = choice.get('decision')
        if choice in manifest.get('recommendation_choices', []):
            assert decision is None and actual == set(choice['existing_performances'])
            continue
        assert decision['choice'] == 'selected_performance'
        assert len(decision['performances']) == 1
        assert actual == {p['performance_id'] for p in decision['performances']}
        assert {u['unit_id'] for u in units if u['disposition'] in ('import_new', 'reuse_existing')} == set(decision['selected_units'])
        assert {u['unit_id'] for u in units if u['disposition'] == 'not_selected'} == set(decision['not_selected_units'])
        reference = decision_reference(decision)
        assert reference and (reference.startswith(choice['issue_url'] + '#issuecomment-') or
                              reference == decision.get('implementation_record') and reference.startswith('reports/curator-decisions/'))
        for unit in units:
            assert unit['curator_decision'] == reference
            if unit['disposition'] == 'import_new':
                perf = data['performances'][unit['performance_id']]
                assert perf['source']['curator_decision'] == reference
                assert perf['source']['file'] == decision['implementation_report']
            if unit['disposition'] == 'not_selected':
                covered_rejections.add(unit['unit_id'])
    assert {u.get('unit_id') for u in manifest['units'] if u['disposition'] == 'not_selected'} == covered_rejections
    validate_decision_records(manifest, root)
