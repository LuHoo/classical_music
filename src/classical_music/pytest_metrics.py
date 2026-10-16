"""Opt-in pytest metrics; no test selection or changed validation semantics.

Enable with ``-p classical_music.pytest_metrics`` and ``CI_METRICS_DIR``.
Serial runs retain the original root artifact paths. In an explicit xdist run,
each worker writes below ``workers/<worker-id>/`` and the controller produces a
fail-closed merged session report at the root. Counts cover the process that
observed them, not child processes or replaced/mocked methods.
"""
from collections import Counter
import functools
import json
import os
from pathlib import Path

import pytest


class Metrics:
    def __init__(self, directory, worker_id='master'):
        self.worker_id = worker_id
        self.path = directory / 'test-phases.jsonl'
        directory.mkdir(parents=True, exist_ok=True)
        self.path.write_text('')
        self.counts = Counter()
        self.previous = Counter()
        self.originals = []

    def wrap(self, cls, name, counter):
        original = getattr(cls, name)
        @functools.wraps(original)
        def counted(*args, **kwargs):
            self.counts[counter] += 1
            return original(*args, **kwargs)
        self.originals.append((cls, name, original))
        setattr(cls, name, counted)

    def pytest_sessionstart(self, session):
        from ruamel.yaml import YAML
        from classical_music.publication_site import PublicationSiteGenerator
        self.wrap(YAML, 'load', 'yaml_loads')
        self.wrap(PublicationSiteGenerator, 'generate', 'publication_builds')

    def pytest_runtest_logstart(self, nodeid, location):
        self.previous = self.counts.copy()

    def pytest_runtest_logreport(self, report):
        delta = self.counts - self.previous
        self.previous = self.counts.copy()
        row = dict(nodeid=report.nodeid, phase=report.when, seconds=report.duration,
                   outcome=report.outcome, xfail=getattr(report, 'wasxfail', None),
               yaml_loads=delta['yaml_loads'], publication_builds=delta['publication_builds'],
               worker=self.worker_id)
        # Append after each phase so completed phases survive an interrupted run.
        with self.path.open('a') as handle:
            handle.write(json.dumps(row) + '\n')

    def pytest_sessionfinish(self, session, exitstatus):
        (self.path.parent / 'test-session.json').write_text(json.dumps(dict(
            exit_code=int(exitstatus), collected=session.testscollected,
            counts=dict(self.counts), worker=self.worker_id,
            counts_scope='current process; includes collection and setup'), indent=2) + '\n')
        self.restore()

    def restore(self):
        for cls, name, original in reversed(self.originals):
            setattr(cls, name, original)
        self.originals.clear()

    def pytest_unconfigure(self, config):
        self.restore()


class ParallelControllerMetrics:
    """Merge worker artifacts deterministically; missing/duplicate data is fatal.

    The controller does not wrap YAML or publication calls: it executes no
    tests, and counting both controller reports and worker reports would
    double-count phase data. It only verifies/merges worker-written artifacts
    after xdist has stopped them.
    """

    def __init__(self, directory, expected_workers):
        self.directory = directory
        self.expected_workers = expected_workers

    def pytest_sessionfinish(self, session, exitstatus):
        workers_dir = self.directory / 'workers'
        worker_dirs = sorted(path for path in workers_dir.glob('gw*') if path.is_dir())
        rows = []
        sessions = []
        errors = []

        if len(worker_dirs) != self.expected_workers:
            errors.append(f'expected {self.expected_workers} worker directories, found {len(worker_dirs)}')

        for worker_dir in worker_dirs:
            phases_path = worker_dir / 'test-phases.jsonl'
            session_path = worker_dir / 'test-session.json'
            if not phases_path.exists() or not session_path.exists():
                errors.append(f'missing metrics artifact for {worker_dir.name}')
                continue
            try:
                worker_rows = [json.loads(line) for line in phases_path.read_text().splitlines()]
                worker_session = json.loads(session_path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f'unreadable metrics artifact for {worker_dir.name}: {exc}')
                continue
            if worker_session.get('worker') != worker_dir.name:
                errors.append(f'worker identity mismatch for {worker_dir.name}')
            rows.extend(worker_rows)
            sessions.append(worker_session)

        keys = [(row.get('nodeid'), row.get('phase')) for row in rows]
        if len(keys) != len(set(keys)):
            errors.append('duplicate nodeid/phase records across workers')
        nodeids = {row.get('nodeid') for row in rows if row.get('nodeid')}
        if session.testscollected != len(nodeids):
            errors.append(f'collected {session.testscollected} nodeids but merged artifacts contain {len(nodeids)}')

        merged_counts = Counter()
        for worker_session in sessions:
            merged_counts.update(worker_session.get('counts', {}))
        complete = not errors
        merged = dict(
            exit_code=int(exitstatus), collected=session.testscollected,
            counts=dict(merged_counts), workers=[worker.get('worker') for worker in sessions],
            complete=complete, errors=errors,
            counts_scope='merged worker processes; includes worker collection and setup',
        )
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / 'test-phases.jsonl').write_text(
            ''.join(json.dumps(row) + '\n' for row in rows)
        )
        (self.directory / 'test-session.json').write_text(json.dumps(merged, indent=2) + '\n')
        if errors:
            # xdist would normally already return nonzero on worker crashes;
            # make missing/truncated metrics fail even if its own exit was 0.
            session.exitstatus = pytest.ExitCode.INTERNAL_ERROR


def pytest_configure(config):
    directory = os.environ.get('CI_METRICS_DIR')
    if directory:
        root = Path(directory)
        if hasattr(config, 'workerinput'):
            worker_id = config.workerinput['workerid']
            config.pluginmanager.register(Metrics(root / 'workers' / worker_id, worker_id),
                                          'canonical-ci-metrics-' + worker_id)
        elif getattr(config.option, 'numprocesses', 0):
            config.pluginmanager.register(
                ParallelControllerMetrics(root, int(config.option.numprocesses)),
                'canonical-ci-metrics-controller',
            )
        else:
            config.pluginmanager.register(Metrics(root), 'canonical-ci-metrics')
