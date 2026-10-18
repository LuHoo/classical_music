"""End-to-end xdist checks for the opt-in CI metrics plugin."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def run_parallel_suite(tmp_path, files, *extra_args):
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    metrics = tmp_path / 'metrics'
    environment = dict(os.environ, CI_METRICS_DIR=str(metrics),
                       PYTHONPATH=os.pathsep.join((str(ROOT / 'src'), str(tmp_path))),
                       PYTEST_ADDOPTS='', PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-m', 'pytest', '-p', 'classical_music.pytest_metrics',
               '-o', 'addopts=', '-p', 'no:cacheprovider', '-n', '2', '--dist', 'load']
    command.extend(extra_args)
    return subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True), metrics


def test_real_xdist_merges_complete_metrics_and_coverage(tmp_path):
    result, metrics = run_parallel_suite(tmp_path, {
        'sample.py': 'def left(): return "left"\ndef right(): return "right"\n',
        'test_left.py': 'from sample import left\ndef test_left(): assert left() == "left"\n',
        'test_right.py': 'from sample import right\ndef test_right(): assert right() == "right"\n',
    }, '--cov=sample', '--cov-report=xml:coverage.xml')

    assert result.returncode == 0, result.stdout + result.stderr
    session = json.loads((metrics / 'test-session.json').read_text())
    assert session['complete'] is True
    assert session['errors'] == []
    assert session['workers'] == ['gw0', 'gw1']
    rows = [json.loads(line) for line in (metrics / 'test-phases.jsonl').read_text().splitlines()]
    assert {row['worker'] for row in rows} == {'gw0', 'gw1'}
    assert {row['phase'] for row in rows} == {'setup', 'call', 'teardown'}
    coverage = (tmp_path / 'coverage.xml').read_text()
    assert 'name="sample.py"' in coverage
    assert 'number="1" hits="1"' in coverage
    assert 'number="2" hits="1"' in coverage


def test_real_xdist_preserves_failure_lifecycles(tmp_path):
    outcomes = '''import pytest
@pytest.fixture
def broken_setup(): raise RuntimeError("setup")
@pytest.fixture
def broken_teardown():
    yield
    raise RuntimeError("teardown")
def test_setup(broken_setup): pass
def test_call(): assert False
def test_teardown(broken_teardown): pass
@pytest.mark.skip(reason="expected")
def test_skip(): pass
@pytest.mark.xfail(reason="expected")
def test_xfail(): assert False
'''
    result, metrics = run_parallel_suite(tmp_path, {'test_outcomes.py': outcomes})

    assert result.returncode == pytest.ExitCode.TESTS_FAILED, result.stdout + result.stderr
    session = json.loads((metrics / 'test-session.json').read_text())
    assert session['exit_code'] == pytest.ExitCode.TESTS_FAILED
    assert session['complete'] is True
    rows = [json.loads(line) for line in (metrics / 'test-phases.jsonl').read_text().splitlines()]
    phases = {}
    for row in rows:
        phases.setdefault(row['nodeid'], []).append((row['phase'], row['outcome']))
    assert phases['test_outcomes.py::test_setup'] == [('setup', 'failed'), ('teardown', 'passed')]
    assert phases['test_outcomes.py::test_skip'] == [('setup', 'skipped'), ('teardown', 'passed')]
    assert phases['test_outcomes.py::test_xfail'][1] == ('call', 'skipped')
    assert all(items[-1][0] == 'teardown' for items in phases.values())


def test_real_xdist_worker_crash_is_fail_closed(tmp_path):
    result, metrics = run_parallel_suite(tmp_path, {
        'test_crash.py': 'import os\ndef test_worker_crash(): os._exit(1)\n',
        'test_survives.py': 'def test_survives(): assert True\n',
    }, '--max-worker-restart=0')

    assert result.returncode != 0, result.stdout + result.stderr
    session = json.loads((metrics / 'test-session.json').read_text())
    assert session['complete'] is False
    assert session['errors']


def test_missing_worker_coverage_fails_even_when_all_tests_pass(tmp_path):
    result, metrics = run_parallel_suite(tmp_path, {
        'conftest.py': """import pytest
@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session, exitstatus):
    yield
    config = session.config
    if hasattr(config, 'workerinput') and config.workerinput['workerid'] == 'gw0':
        config.workeroutput.pop('cov_worker_node_id', None)
""",
        'sample.py': 'def value(): return 1\n',
        'test_sample.py': 'from sample import value\ndef test_a(): assert value() == 1\ndef test_b(): assert value() == 1\n',
    }, '--cov=sample', '--cov-report=xml:coverage.xml')
    assert '2 passed' in result.stdout, result.stdout + result.stderr
    assert result.returncode == pytest.ExitCode.INTERNAL_ERROR, result.stdout + result.stderr
    session = json.loads((metrics / 'test-session.json').read_text())
    assert session['exit_code'] == result.returncode
    assert session['complete'] is False
    assert any('missing worker coverage: gw0' in error for error in session['errors'])
