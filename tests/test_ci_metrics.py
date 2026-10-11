"""Failure propagation and timing instrumentation, using tiny subprocess suites."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('code', [0, 7])
def test_command_preserves_output_exit_and_metadata(tmp_path, code):
    module = load_script('measure_ci')
    assert module.measure([sys.executable, '-c', f'print("evidence"); raise SystemExit({code})'], tmp_path, 'pytest') == code
    data = json.loads((tmp_path / 'pytest.json').read_text())
    assert data['exit_code'] == code and data['seconds'] >= 0
    assert data['environment']['data_tree']
    assert (tmp_path / 'pytest.log').read_text().strip() == 'evidence'


def test_failed_setup_call_skip_and_counters_are_reported(tmp_path):
    suite = tmp_path / 'test_sample.py'
    suite.write_text('''import pytest
from ruamel.yaml import YAML
@pytest.fixture
def broken():
    raise ValueError('setup failure')
def test_setup(broken): pass
def test_failed():
    assert False
@pytest.mark.skip(reason='intentional')
def test_skipped(): pass
def test_yaml():
    assert YAML(typ='safe').load('a: 1') == {'a': 1}
''')
    metrics = tmp_path / 'metrics'
    env = dict(os.environ, CI_METRICS_DIR=str(metrics), PYTHONPATH=str(ROOT / 'src'),
               PYTEST_ADDOPTS='', PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-m', 'pytest', str(suite), '-p', 'classical_music.pytest_metrics',
        '-o', 'addopts=', '-p', 'no:cacheprovider', '--junitxml='+str(metrics/'junit.xml')],
        cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 1, result.stdout + result.stderr
    rows = [json.loads(line) for line in (metrics/'test-phases.jsonl').read_text().splitlines()]
    assert any(r['phase']=='setup' and r['outcome']=='failed' for r in rows)
    assert any(r['phase']=='call' and r['outcome']=='failed' for r in rows)
    assert any(r['outcome']=='skipped' for r in rows)
    assert sum(r['yaml_loads'] for r in rows) == 1
    session = json.loads((metrics/'test-session.json').read_text())
    assert session['exit_code'] == 1 and session['collected'] == 4
    assert (metrics/'junit.xml').exists()
    summary = load_script('summarize_ci_metrics').summarize(metrics)
    assert 'setup/failed=1' in summary and 'call/failed=1' in summary
    assert 'Slowest teardown' in summary


def test_summary_handles_missing_and_partial_results(tmp_path):
    module = load_script('summarize_ci_metrics')
    assert 'No completed pytest' in module.summarize(tmp_path)
    (tmp_path/'test-phases.jsonl').write_text('{"partial":')
    assert 'Incomplete phase record' in module.summarize(tmp_path)


def test_counter_wrappers_preserve_failures_and_restore(tmp_path):
    from classical_music.pytest_metrics import Metrics
    class Builder:
        def generate(self):
            raise ValueError('invalid publication')
    original = Builder.generate
    metrics = Metrics(tmp_path)
    metrics.wrap(Builder, 'generate', 'publication_builds')
    with pytest.raises(ValueError, match='invalid publication'):
        Builder().generate()
    assert metrics.counts['publication_builds'] == 1
    metrics.restore()
    assert Builder.generate is original


def test_baseline_refuses_small_sample():
    with pytest.raises(ValueError, match='three'):
        load_script('compare_ci_baseline').compare([])


def test_workflow_keeps_full_suite_and_failure_artifacts():
    from ruamel.yaml import YAML
    workflow = YAML(typ='safe').load((ROOT/'.github/workflows/validate.yml').read_text())
    steps = workflow['jobs']['validate']['steps']
    tests = next(s for s in steps if s['name']=='Run tests')
    assert '--durations=30' in tests['run'] and '--junitxml=' in tests['run']
    assert '|| true' not in tests['run'] and 'continue-on-error' not in tests
    assert '--cov-report=xml:' in tests['run']
    artifacts = next(s for s in steps if s['name']=='Upload test measurements')
    assert artifacts['if'] == 'always()'


def test_baseline_compares_three_matching_runs_and_rejects_drift(tmp_path):
    module = load_script('compare_ci_baseline')
    directories = []
    for number, duration in enumerate((10, 20, 30), start=1):
        path = tmp_path / str(number)
        path.mkdir()
        directories.append(path)
        env = dict.fromkeys(('python', 'platform', 'cpu_count', 'cpu_model', 'data_tree', 'source_tree',
                             'tests_tree', 'repository_tree', 'dependencies', 'workers', 'dependency_cache'), 'same')
        env['worktree_status'] = ''
        env['ci'] = dict(GITHUB_RUN_ID=str(number), GITHUB_RUN_ATTEMPT='1',
                         RUNNER_OS='Linux', RUNNER_ARCH='X64', ImageOS='ubuntu24', ImageVersion='same')
        (path/'pytest.json').write_text(json.dumps(dict(environment=env, exit_code=0, seconds=duration, command=['pytest'])))
        (path/'test-session.json').write_text(json.dumps(dict(exit_code=0, collected=1)))
        (path/'test-phases.jsonl').write_text(json.dumps(dict(nodeid='test_a', phase='call',outcome='passed',xfail=None))+'\n')
        (path/'run.json').write_text(json.dumps(dict(createdAt='2026-10-11T00:00:00Z', jobs=[dict(
            name='validate', conclusion='success', startedAt='2026-10-11T00:00:02Z', completedAt='2026-10-11T00:01:02Z')])))
    report = module.compare(directories)
    assert report['summary']['pytest_seconds'] == dict(median=20, minimum=10, maximum=30)
    assert report['summary']['job_seconds']['median'] == 60
    assert report['summary']['queue_seconds']['median'] == 2
    data = json.loads((directories[2]/'pytest.json').read_text())
    data['environment']['data_tree'] = 'changed'
    (directories[2]/'pytest.json').write_text(json.dumps(data))
    with pytest.raises(ValueError, match='differ'):
        module.compare(directories)
