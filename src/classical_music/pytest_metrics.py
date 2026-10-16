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

    @staticmethod
    def validate_rows(worker, rows):
        """Return evidence errors for the pytest report lifecycle of one worker."""
        errors = []
        reports = {}
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                errors.append(f'{worker} record {index} is not an object')
                continue
            nodeid = row.get('nodeid')
            phase = row.get('phase')
            outcome = row.get('outcome')
            if not isinstance(nodeid, str) or not nodeid:
                errors.append(f'{worker} record {index} has invalid nodeid')
                continue
            if phase not in {'setup', 'call', 'teardown'}:
                errors.append(f'{worker} record {index} has invalid phase')
                continue
            if outcome not in {'passed', 'failed', 'skipped'}:
                errors.append(f'{worker} record {index} has invalid outcome')
            if row.get('worker') != worker:
                errors.append(f'{worker} record {index} has wrong worker identity')
            if not isinstance(row.get('seconds'), (int, float)) or row['seconds'] < 0:
                errors.append(f'{worker} record {index} has invalid duration')
            for counter in ('yaml_loads', 'publication_builds'):
                if not isinstance(row.get(counter), int) or row[counter] < 0:
                    errors.append(f'{worker} record {index} has invalid {counter}')
            reports.setdefault(nodeid, []).append((phase, outcome))

        for nodeid, reports_for_nodeid in reports.items():
            phases = [phase for phase, _ in reports_for_nodeid]
            if len(phases) != len(set(phases)):
                errors.append(f'{worker} has duplicate phase records for {nodeid}')
                continue
            if not phases or phases[0] != 'setup' or phases[-1] != 'teardown':
                errors.append(f'{worker} has incomplete lifecycle for {nodeid}')
                continue
            setup_outcome = reports_for_nodeid[0][1]
            expected = ['setup', 'call', 'teardown'] if setup_outcome == 'passed' else ['setup', 'teardown']
            if phases != expected:
                errors.append(f'{worker} has invalid phase order for {nodeid}')
        return errors

    def pytest_sessionfinish(self, session, exitstatus):
        workers_dir = self.directory / 'workers'
        worker_dirs = sorted(path for path in workers_dir.iterdir() if path.is_dir()) if workers_dir.exists() else []
        rows = []
        sessions = []
        errors = []
        expected_names = {f'gw{index}' for index in range(self.expected_workers)}
        actual_names = {path.name for path in worker_dirs}

        if actual_names != expected_names:
            errors.append(f'expected workers {sorted(expected_names)}, found {sorted(actual_names)}')

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
            if not isinstance(worker_session, dict):
                errors.append(f'invalid session metadata for {worker_dir.name}')
                continue
            if worker_session.get('worker') != worker_dir.name:
                errors.append(f'worker identity mismatch for {worker_dir.name}')
            if not isinstance(worker_session.get('collected'), int) or worker_session['collected'] < 0:
                errors.append(f'invalid collected count for {worker_dir.name}')
            if worker_session.get('exit_code') not in range(6):
                errors.append(f'invalid exit code for {worker_dir.name}')
            if not isinstance(worker_session.get('counts'), dict):
                errors.append(f'invalid counters for {worker_dir.name}')
            elif any(not isinstance(value, int) or value < 0 for value in worker_session['counts'].values()):
                errors.append(f'invalid counter value for {worker_dir.name}')
            if exitstatus == 0 and worker_session.get('exit_code') != 0:
                errors.append(f'completed controller has failed worker {worker_dir.name}')
            errors.extend(self.validate_rows(worker_dir.name, worker_rows))
            rows.extend(worker_rows)
            sessions.append(worker_session)

        valid_rows = [row for row in rows if isinstance(row, dict)]
        keys = [(row.get('nodeid'), row.get('phase')) for row in valid_rows]
        if len(keys) != len(set(keys)):
            errors.append('duplicate nodeid/phase records across workers')
        nodeids = {row.get('nodeid') for row in valid_rows if row.get('nodeid')}
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
