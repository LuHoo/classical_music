#!/usr/bin/env python3
"""Measure a command without masking failure; write logs and provenance using stdlib."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time


def capture(command):
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def environment():
    cpu = Path('/proc/cpuinfo')
    model = next((line.split(':', 1)[1].strip() for line in cpu.read_text().splitlines()
                  if line.startswith('model name')), None) if cpu.exists() else platform.processor()
    return dict(python=sys.version, platform=platform.platform(), cpu_count=os.cpu_count(), cpu_model=model,
                commit=capture(['git', 'rev-parse', 'HEAD']),
                repository_tree=capture(['git', 'rev-parse', 'HEAD^{tree}']),
                worktree_status=capture(['git', 'status', '--porcelain']),
                data_tree=capture(['git', 'rev-parse', 'HEAD:data']),
                source_tree=capture(['git', 'rev-parse', 'HEAD:src']),
                tests_tree=capture(['git', 'rev-parse', 'HEAD:tests']),
                dependencies=capture([sys.executable, '-m', 'pip', 'freeze']),
                ci={name: os.environ.get(name) for name in (
                    'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_SHA', 'GITHUB_EVENT_NAME',
                    'RUNNER_OS', 'RUNNER_ARCH', 'ImageOS', 'ImageVersion')},
                workers=1, dependency_cache='disabled in validate.yml')


def measure(command, output, label):
    output.mkdir(parents=True, exist_ok=True)
    info = dict(label=label, command=command, environment=environment(),
                started_at=datetime.now(timezone.utc).isoformat(), status='running')
    report = output / (label + '.json')
    report.write_text(json.dumps(info, indent=2) + '\n')
    started = time.perf_counter()
    code = 1
    try:
        with (output / (label + '.log')).open('w') as log:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1)
            try:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    print(line, end='', flush=True)
                code = process.wait()
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
    finally:
        info.update(seconds=time.perf_counter() - started, exit_code=code,
                    finished_at=datetime.now(timezone.utc).isoformat(), status='completed')
        report.write_text(json.dumps(info, indent=2) + '\n')
    return code if code >= 0 else 128 - code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('ci-metrics'))
    parser.add_argument('--label', required=True, choices=['pytest', 'validator-human', 'validator-json'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('A command is required after --')
    return measure(command, args.output, args.label)


if __name__ == '__main__':
    sys.exit(main())
