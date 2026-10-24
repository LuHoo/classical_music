#!/usr/bin/env python3
"""Summarize recorded phases, including partial or failed pytest sessions."""
import argparse
from collections import Counter
import json
from pathlib import Path


def summarize(directory):
    lines = ['## CI measurements', '', 'Command durations exclude queue, setup and artifact upload.', '',
             '| Command | Seconds | Peak RSS (KiB) | Exit |', '|---|---:|---:|---:|']
    for name in ('classify', 'validator', 'validator-human', 'validator-json', 'pytest'):
        path = directory / (name + '.json')
        if path.exists():
            data = json.loads(path.read_text())
            memory = data.get('memory') or {}
            lines.append(f"| {name} | {data.get('seconds', 'incomplete')} | "
                         f"{memory.get('peak_rss_kib', 'unavailable')} | "
                         f"{data.get('exit_code', 'incomplete')} |")
    path = directory / 'test-phases.jsonl'
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                lines.append('\nIncomplete phase record omitted (interrupted write).')
    outcomes = Counter((r['phase'], r['outcome']) for r in rows)
    lines += ['', 'Phase outcomes: ' + ', '.join(f'{phase}/{outcome}={count}' for (phase, outcome), count in sorted(outcomes.items()))]
    session = directory / 'test-session.json'
    lines += ['', ('Session: ' + session.read_text().strip()) if session.exists()
              else 'No completed pytest session report: skipped, interrupted, or startup failed.']
    for phase in ('setup', 'call', 'teardown'):
        lines += ['', f'### Slowest {phase} phases', '', '| Test | Seconds | YAML loads | Publication builds |',
                  '|---|---:|---:|---:|']
        for row in sorted((r for r in rows if r['phase'] == phase), key=lambda r: r['seconds'], reverse=True)[:30]:
            name = row['nodeid'].replace('|', '\\|').replace('\n', ' ')
            lines.append(f"| `{name}` | {row['seconds']:.4f} | {row['yaml_loads']} | {row['publication_builds']} |")
    lines += ['', 'Peak RSS is sampled Linux process-tree RSS and is a lower bound, not runner-wide memory.',
              'Counts are current-process calls, including failed calls; child-process and mocked calls are not fully attributed.',
              'Full logs, JUnit, coverage, environment and phase records are in the ci-metrics artifact.']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(summarize(args.directory), end='')
