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
import threading
import time


def capture(command):
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def requested_workers(command):
    """Return the explicit pytest-xdist worker count, or 1 for serial commands.

    The CI experiment deliberately uses ``-n 2`` rather than ``auto``. An
    unparseable worker value remains provenance rather than being guessed, so
    comparison tooling cannot silently treat it as serial.
    """
    for index, argument in enumerate(command):
        if argument in ('-n', '--numprocesses') and index + 1 < len(command):
            value = command[index + 1]
        elif argument.startswith('-n') and argument != '-n':
            value = argument[2:]
        elif argument.startswith('--numprocesses='):
            value = argument.split('=', 1)[1]
        else:
            continue
        try:
            return int(value)
        except ValueError:
            return value
    return 1


def environment(command=(), evidence_path=None):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'installation_provenance', Path(__file__).with_name('installation_provenance.py'))
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    current_evidence = audit.current_evidence
    # Reading the audited evidence is deliberately fail-closed: a mismatch
    # aborts the measurement rather than producing incomparable provenance.
    # Tests that exercise measure() itself must pass their own evidence_path
    # so they never consult (or depend on the cleanliness of) the real
    # repository checkout, whose state legitimately drifts while the
    # measured suite runs.
    installation = current_evidence(
        evidence_path if evidence_path is not None else Path('ci-metrics/installation.json'))
    cpu = Path('/proc/cpuinfo')
    model = next((line.split(':', 1)[1].strip() for line in cpu.read_text().splitlines()
                  if line.startswith('model name')), None) if cpu.exists() else platform.processor()
    return dict(python=sys.version, platform=platform.platform(), cpu_count=os.cpu_count(), cpu_model=model,
                installation_provenance=installation,
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
                workers=requested_workers(command), dependency_cache='disabled in validate.yml')


def process_tree_rss_kib(root_pid):
    """Return current Linux RSS for a process and its descendants, or None."""
    proc = Path('/proc')
    if not proc.exists():
        return None
    processes = {}
    for path in proc.iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = dict(line.split(':', 1) for line in (path / 'status').read_text().splitlines()
                          if ':' in line)
            processes[int(path.name)] = (int(fields['PPid'].strip()),
                                         int(fields.get('VmRSS', '0 kB').split()[0]))
        except (FileNotFoundError, KeyError, PermissionError, ValueError):
            continue
    descendants = {root_pid}
    while True:
        children = {pid for pid, (parent, _) in processes.items() if parent in descendants}
        if children <= descendants:
            return sum(processes.get(pid, (0, 0))[1] for pid in descendants)
        descendants.update(children)


class ProcessTreeMemory:
    """Sample aggregate Linux process-tree RSS while a measured command runs."""
    interval_seconds = 0.2

    def __init__(self, root_pid):
        self.root_pid = root_pid
        self.peak_rss_kib = 0
        self.samples = 0
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        while not self.stopped.is_set():
            rss = process_tree_rss_kib(self.root_pid)
            if rss is None:
                return
            self.peak_rss_kib = max(self.peak_rss_kib, rss)
            self.samples += 1
            self.stopped.wait(self.interval_seconds)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.thread.join()
        if self.samples:
            return dict(peak_rss_kib=self.peak_rss_kib, samples=self.samples,
                        interval_seconds=self.interval_seconds,
                        scope='sampled Linux RSS for measured process and descendants; lower bound')
        return dict(peak_rss_kib=None, samples=0, interval_seconds=self.interval_seconds,
                    scope='unavailable outside Linux /proc')


def measure(command, output, label, evidence_path=None):
    output.mkdir(parents=True, exist_ok=True)
    info = dict(label=label, command=command, environment=environment(command, evidence_path),
                started_at=datetime.now(timezone.utc).isoformat(), status='running')
    report = output / (label + '.json')
    report.write_text(json.dumps(info, indent=2) + '\n')
    started = time.perf_counter()
    code = 1
    memory = None
    try:
        with (output / (label + '.log')).open('w') as log:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1)
            sampler = ProcessTreeMemory(process.pid)
            sampler.start()
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
                memory = sampler.stop()
    finally:
        info.update(seconds=time.perf_counter() - started, exit_code=code,
                    finished_at=datetime.now(timezone.utc).isoformat(), status='completed', memory=memory)
        report.write_text(json.dumps(info, indent=2) + '\n')
    return code if code >= 0 else 128 - code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('ci-metrics'))
    parser.add_argument('--label', required=True,
                        choices=['pytest', 'validator', 'classify', 'validator-human', 'validator-json'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('A command is required after --')
    return measure(command, args.output, args.label)


if __name__ == '__main__':
    sys.exit(main())
