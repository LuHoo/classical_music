"""Opt-in serial pytest metrics; no test selection or changed validation semantics.

Enable with -p classical_music.pytest_metrics and CI_METRICS_DIR.
Counts cover the current process, not child processes or replaced/mocked methods.
"""
from collections import Counter
import functools
import json
import os
from pathlib import Path

import pytest


class Metrics:
    def __init__(self, directory):
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
                   yaml_loads=delta['yaml_loads'], publication_builds=delta['publication_builds'])
        # Append after each phase so completed phases survive an interrupted run.
        with self.path.open('a') as handle:
            handle.write(json.dumps(row) + '\n')

    def pytest_sessionfinish(self, session, exitstatus):
        (self.path.parent / 'test-session.json').write_text(json.dumps(dict(
            exit_code=int(exitstatus), collected=session.testscollected,
            counts=dict(self.counts), counts_scope='current process; includes collection and setup'), indent=2) + '\n')
        self.restore()

    def restore(self):
        for cls, name, original in reversed(self.originals):
            setattr(cls, name, original)
        self.originals.clear()

    def pytest_unconfigure(self, config):
        self.restore()


def pytest_configure(config):
    directory = os.environ.get('CI_METRICS_DIR')
    if directory:
        if hasattr(config, 'workerinput') or getattr(config.option, 'numprocesses', 0):
            raise pytest.UsageError('CI metrics baseline requires serial pytest; parallel support is issue #309.')
        config.pluginmanager.register(Metrics(Path(directory)), 'canonical-ci-metrics')
