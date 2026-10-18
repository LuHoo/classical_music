"""Record a clean checkout before pip, then narrowly audit generated metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

FILES = ('src/classical_music.egg-info/PKG-INFO',
         'src/classical_music.egg-info/SOURCES.txt',
         'src/classical_music.egg-info/requires.txt')


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def hashes():
    return {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in FILES}


def allowed_status(status):
    # strip() removes the first status line's leading space. Do not accept
    # additions, deletions, renames, staged changes, or arbitrary egg-info files.
    return all(line in {' M ' + name for name in FILES} | {'M ' + name for name in FILES}
               for line in status.splitlines())


def record(before, output):
    status = git('status', '--porcelain')
    head = git('rev-parse', 'HEAD')
    if before:
        if status:
            raise ValueError('Installation baseline must start from a clean checkout')
        result = dict(commit=head, before=hashes(), before_status=status)
    else:
        result = json.loads(output.read_text())
        if result['before_status'] or result['commit'] != head or not allowed_status(status):
            raise ValueError('Installation changed files outside the three generated metadata files')
        result.update(after=hashes(), after_status=status,
                      diff=git('diff', '--', *FILES), verified=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')


def current_evidence(output):
    if not output.exists():
        return None
    evidence = json.loads(output.read_text())
    if (evidence.get('verified') is not True or evidence.get('before_status') != ''
            or evidence.get('commit') != git('rev-parse', 'HEAD')
            or evidence.get('after_status') != git('status', '--porcelain')
            or not allowed_status(evidence.get('after_status', ''))
            or evidence.get('after') != hashes()):
        raise ValueError('Checkout no longer matches audited installation metadata')
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('ci-metrics/installation.json'))
    args = parser.parse_args()
    record(args.before, args.output)
