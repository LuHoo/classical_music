"""Installation metadata exceptions must not hide source or data changes."""
import importlib.util
import json
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / 'scripts/installation_provenance.py'
    spec = importlib.util.spec_from_file_location('audit', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize('status', ['M src/classical_music/pytest_metrics.py',
    ' M data/test.yaml', '?? arbitrary', 'D src/classical_music.egg-info/PKG-INFO',
    'M  src/classical_music.egg-info/PKG-INFO'])
def test_rejects_unrelated_or_staged_changes(status):
    assert not module().allowed_status(status)


def test_records_before_after_and_rejects_later_drift(tmp_path, monkeypatch):
    m = module()
    state = {'status': '', 'hashes': dict.fromkeys(m.FILES, 'before')}
    monkeypatch.setattr(m, 'git', lambda *args: state['status'] if args[0] == 'status'
                        else 'commit' if args[0] == 'rev-parse' else 'metadata diff')
    monkeypatch.setattr(m, 'hashes', lambda: state['hashes'].copy())
    path = tmp_path / 'installation.json'
    m.record(True, path)
    state['status'] = 'M ' + m.FILES[0]
    state['hashes'][m.FILES[0]] = 'after'
    m.record(False, path)
    assert m.current_evidence(path)['verified'] is True
    state['hashes'][m.FILES[0]] = 'later modification'
    with pytest.raises(ValueError, match='no longer matches'):
        m.current_evidence(path)
    state['status'] = 'M data/changed.yaml'
    with pytest.raises(ValueError, match='outside'):
        m.record(False, path)


def test_dirty_initial_checkout_is_rejected(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'git', lambda *args: 'dirty')
    with pytest.raises(ValueError, match='clean checkout'):
        m.record(True, tmp_path / 'installation.json')
