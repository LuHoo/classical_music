#!/usr/bin/env python3
"""Compare at least three complete matching CI artifact directories, fail on mismatch.

Each directory must also contain run.json from `gh run view ID --json jobs,createdAt`.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import statistics


def seconds(start, end):
    return (datetime.fromisoformat(end.replace('Z', '+00:00')) -
            datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds()


def compare(paths):
    if len(paths) < 3:
        raise ValueError('At least three comparable CI runs are required.')
    identities = set()
    reference = None
    rows = []
    for path in paths:
        measured = json.loads((path / 'pytest.json').read_text())
        session = json.loads((path / 'test-session.json').read_text())
        run = json.loads((path / 'run.json').read_text())
        env = measured['environment']
        identity = (env['ci']['GITHUB_RUN_ID'], env['ci']['GITHUB_RUN_ATTEMPT'])
        if not all(identity) or identity in identities:
            raise ValueError('Missing or duplicated CI run identity.')
        identities.add(identity)
        if env['worktree_status']:
            raise ValueError('Dirty checkout: committed tree IDs do not describe the measured files.')
        if measured['exit_code'] or session['exit_code']:
            raise ValueError('Failed runs are diagnostic evidence, not a successful baseline.')
        phases = [json.loads(line) for line in (path / 'test-phases.jsonl').read_text().splitlines()]
        signature = dict(environment={key: env[key] for key in (
            'python', 'platform', 'cpu_count', 'cpu_model', 'data_tree', 'source_tree',
            'tests_tree', 'repository_tree', 'dependencies', 'workers', 'dependency_cache')},
            image={key: env['ci'][key] for key in ('RUNNER_OS', 'RUNNER_ARCH', 'ImageOS', 'ImageVersion')},
            command=measured['command'], collected=session['collected'],
            outcomes=sorted((p['nodeid'], p['phase'], p['outcome'], p['xfail']) for p in phases))
        if reference is not None and signature != reference:
            raise ValueError('Inputs, environment, command or test outcomes differ; do not pool these runs.')
        reference = signature
        jobs = run['jobs']
        job = next(j for j in jobs if j['name'] == 'validate')
        if job['conclusion'] != 'success':
            raise ValueError('Validation job did not succeed.')
        rows.append(dict(run=identity, pytest_seconds=measured['seconds'],
                         job_seconds=seconds(job['startedAt'], job['completedAt']),
                         queue_seconds=seconds(run['createdAt'], job['startedAt']),
                         runner_minutes=sum(seconds(j['startedAt'],j['completedAt']) for j in jobs)/60))
    summary = {key: dict(median=statistics.median(row[key] for row in rows),
                        minimum=min(row[key] for row in rows), maximum=max(row[key] for row in rows))
               for key in ('pytest_seconds','job_seconds','queue_seconds','runner_minutes')}
    return dict(runs=rows, summary=summary, provenance=reference,
                note='Runner minutes are elapsed job time, not billing-adjusted credits. Queue includes scheduling delay.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(compare(args.directories), indent=2))
    except (ValueError, KeyError, OSError, StopIteration) as exc:
        parser.exit(2, f'Cannot establish baseline: {exc}\n')
