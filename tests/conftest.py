"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def data_root() -> Path:
    """Return path to data directory for canonical entity loading."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture(scope="session")
def pending_curator_repository(tmp_path_factory):
    """Restore only fixed test scenarios in a disposable fixture, never live data.

    The reviewed input is checked in: tests need neither Git history nor network.
    Unrelated current catalogue records remain available to the inventory audits.
    """
    import json
    import shutil
    from ruamel.yaml import YAML
    from classical_music import curator

    source = Path(__file__).resolve().parents[1]
    root = tmp_path_factory.mktemp("pending-curator-fixture")
    for directory in ('data', 'reports/playlist-import', 'reports/curator-decisions',
                      'docs', 'side materials', '.github'):
        shutil.copytree(source / directory, root / directory)
    scenarios = json.loads((source / 'tests/fixtures/curator/pending-choices.json').read_text())
    yaml = YAML(typ='safe')
    for scenario in scenarios['manifests']:
        path = root / scenario['path']
        manifest = json.loads(path.read_text())
        urls = {c['issue_url'] for c in scenario['choices']}
        works = {c['work_id'] for c in scenario['choices']}
        removed = set()
        for performance in (root / 'data/performances').glob('*.yaml'):
            record = yaml.load(performance.read_text())
            if record['work_id'] in works:
                removed.add(record['id'])
                performance.unlink()
        for name, content in scenario['performances'].items():
            (root / name).write_text(content)
        for key in ('recommendation_choices', 'resolved_choices'):
            manifest[key] = [c for c in manifest[key] if c.get('issue_url') not in urls]
        manifest['recommendation_choices'].extend(scenario['choices'])
        units = {u['unit_id']: u for u in scenario['units']}
        manifest['units'] = [units.get(u['unit_id'], u) for u in manifest['units']]
        restored = {r['id'] for r in scenario['new_records']}
        manifest['new_records'] = [r for r in manifest['new_records']
                                   if r['id'] not in removed | restored]
        manifest['new_records'].extend(scenario['new_records'])
        curator.refresh_summary(manifest)
        path.write_bytes(curator.json_bytes(manifest))
        (path.parent / 'README.md').write_text(scenario['readme'])
        for url in urls:
            (root / 'reports/curator-decisions' / ('issue-' + url.rsplit('/', 1)[1] + '.json')).unlink(missing_ok=True)
    return root
