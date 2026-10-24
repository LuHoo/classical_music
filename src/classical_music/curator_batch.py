"""Fast local decisions and one explicit, offline batch validation boundary."""
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timezone
import hashlib
from importlib import import_module
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from ruamel.yaml import YAML

from classical_music import curator as core
from classical_music.playlist_choices import INTAKES
from classical_music.publication_site import PublicationSiteGenerator

STATUS = 'reports/curator-decisions/batch-status.json'
# Deterministic batch regressions use synthetic fixtures, never assume a real
# curator issue is still pending. They mock finish's runner to avoid recursion.
TESTS = ('tests/test_curator_batch.py',)


@contextmanager
def writer_lock(root):
    path = root / '.curator.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise core.CuratorError('Another curator apply/finish is running (.curator.lock).') from exc
    try:
        yield
    finally:
        os.close(fd)
        path.unlink(missing_ok=True)


def snapshot(root):
    result = core.input_snapshot(root)
    result.pop(STATUS, None)
    # Code/test changes during finish also invalidate its success stamp.
    for directory in ('src', 'scripts', 'tests'):
        for path in (root / directory).rglob('*.py'):
            result[str(path.relative_to(root))] = path.read_bytes()
    for name in ('pyproject.toml', 'curator'):
        if (root / name).exists():
            result[name] = (root / name).read_bytes()
    return result


def fingerprint(inputs):
    digest = hashlib.sha256()
    for name, content in sorted(inputs.items()):
        digest.update(name.encode() + b'\0' + hashlib.sha256(content).digest())
    return digest.hexdigest()


def status_bytes(root):
    path = core.safe_path(root, STATUS)
    return path.read_bytes() if path.exists() else None


def read_status(content):
    if content is None:
        return {'schema_version': 1, 'issues': []}
    state = json.loads(content)
    core.require(state.get('schema_version') == 1 and isinstance(state.get('issues'), list),
                 'Unsupported batch status; review it manually.')
    return state


def record_decision(root, issue, token, *, apply=True, curator='LAH', decision_url=None,
                    replace_existing=False, playlist_remove=False, note=None, progress=None):
    core.require(__debug__, 'Run without Python -O; audit assertions must remain enabled.')
    core.require(curator and curator.strip(), 'Curator identity is required.')
    root = root.resolve()
    report = progress or (lambda message: None)
    report('Beslissing lokaal vastleggen; eindcontrole volgt met ./curator finish.' if apply else
           'Preview: alleen het wijzigingsplan; niets opslaan, geen eindcontrole.')

    def plan_and_install():
        baseline = snapshot(root)
        before_status = status_bytes(root)
        if token == 'playlist-done':
            core.require(not (decision_url or replace_existing or playlist_remove),
                         'Decision flags do not apply to playlist-done.')
            changes, record, message = core.plan_playlist_done(root, issue, curator=curator, note=note)
        else:
            core.require(not note, '--note is only for playlist-done.')
            changes, record, message = core.plan_decision(root, issue, token, curator=curator,
                decision_url=decision_url, replace_existing=replace_existing, playlist_remove=playlist_remove)
        if not changes:
            return message + '\n' + core.manual_instructions(record) + '\nNa je laatste wijziging: ./curator finish'
        files = list(changes)
        if apply:
            state = read_status(before_status)
            # Do not carry an old validation stamp forward after another decision.
            state = dict(schema_version=1, status='pending',
                         issues=sorted(set(state['issues']) | {issue}),
                         updated_at=datetime.now(timezone.utc).isoformat())
            changes[STATUS] = core.json_bytes(state)
            core.require(snapshot(root) == baseline, 'Repository inputs changed while planning; rerun.')
            expected = dict(baseline)
            for name in changes:
                expected.setdefault(name, None)
            expected[STATUS] = before_status
            core.install_changes(root, changes, expected)
        return ('Opgeslagen, nog niet eindgecontroleerd: ' if apply else 'Preview only: ') + message + '\n' + \
            '\n'.join(('  DELETE ' if changes[p] is None else '  WRITE ') + p for p in files) + \
            '\n' + core.manual_instructions(record) + '\nVolgende beslissing invoeren, of afronden met: ./curator finish'

    if apply:
        with writer_lock(root):
            return plan_and_install()
    return plan_and_install()


def validate_batch(stage, report):
    """All registered intake checks share one current canonical/publication build."""
    yaml = YAML(typ='safe')
    data = {}
    report('Canonieke gegevens laden')
    for kind in ('persons', 'work-groups', 'works', 'performances'):
        data[kind] = {}
        for path in (stage / 'data' / kind).rglob('*.yaml'):
            record = yaml.load(path.read_text())
            core.require(record['id'] not in data[kind], 'Duplicate canonical ID: ' + record['id'])
            data[kind][record['id']] = record
    report('Canonieke publicatie controleren en eenmaal opbouwen')
    with redirect_stdout(io.StringIO()):
        generated = PublicationSiteGenerator(stage).generate()
    checked = []
    for intake in INTAKES:
        module = import_module(intake.audit_module)
        for path in sorted((stage / 'reports/playlist-import').glob(intake.pattern)):
            report('Broninventaris, beslisrecords en publicatielinks controleren: ' + str(path.relative_to(stage)))
            with redirect_stdout(io.StringIO()):
                if intake.format == 'window':
                    module.audit_decisions(path, stage, data=data, generated=generated)
                else:
                    module.audit(stage, data=data, generated=generated)
            manifest = json.loads(path.read_text())
            for choice in manifest.get('resolved_choices', []):
                performances = (choice.get('decision') or {}).get('performances', [])
                if performances:
                    page = (generated.output_dir / 'works' / (choice['work_id'] + '.md')).read_text()
                    for performance in performances:
                        core.require(performance['tidal_url'] in page,
                                     'Selected recommendation missing from publication: ' + choice['work_id'])
            checked.append(str(path.relative_to(stage)))
    core.require(checked, 'No registered intake manifests found; finish cannot validate this repository.')
    return checked


def run_regressions(stage, report):
    report('Gerichte batchregressietests uitvoeren')
    core.require(all((stage / name).is_file() for name in TESTS), 'Batch regression tests are missing.')
    env = dict(os.environ, PYTHONPATH=str(stage / 'src'), PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTEST_ADDOPTS', None)
    command = [sys.executable, '-m', 'pytest', *TESTS, '-q', '-o', 'addopts=', '-p', 'no:cacheprovider']
    result = subprocess.run(command, cwd=stage, env=env, capture_output=True, text=True)
    core.require(result.returncode == 0, 'Batch tests failed; decisions remain pending.\n' +
                 (result.stdout + result.stderr)[-12000:])
    return result.stdout.strip()


def publication_snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in (root / 'publication').rglob('*.md')}


def finish(root, *, progress=None):
    core.require(__debug__, 'Run without Python -O; audit assertions must remain enabled.')
    root = root.resolve()
    report = progress or (lambda message: None)
    with writer_lock(root):
        baseline = snapshot(root)
        before = status_bytes(root)
        old = read_status(before)
        publication_before = publication_snapshot(root)
        state = dict(schema_version=1, status='pending', issues=old['issues'],
                     updated_at=datetime.now(timezone.utc).isoformat())
        pending = core.json_bytes(state)
        core.install_changes(root, {STATUS: pending}, {STATUS: before})
        try:
            report('Eindcontrole starten; beslissingen blijven bewaard als een controle faalt')
            with tempfile.TemporaryDirectory(prefix='curator-finish-') as folder:
                stage = Path(folder).resolve()
                for relative, content in baseline.items():
                    path = core.safe_path(stage, relative)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                checked = validate_batch(stage, report)
                # Validation does not authorize tests to alter the validated inputs.
                core.require(snapshot(stage) == baseline, 'Validation changed its inputs; finish aborted.')
                generated = publication_snapshot(stage)
                tests = run_regressions(stage, report)
                core.require(snapshot(stage) == baseline and publication_snapshot(stage) == generated,
                             'Tests changed the validated files; finish aborted.')
                core.require(snapshot(root) == baseline, 'Repository inputs changed during finish; rerun finish.')
                core.require(publication_snapshot(root) == publication_before,
                             'Publication changed during finish; rerun finish.')
                state.update(status='validated', validated_at=datetime.now(timezone.utc).isoformat(),
                             inputs_sha256=fingerprint(baseline), manifests=checked,
                             tests=list(TESTS), test_result=tests)
                changes = {p: content for p, content in generated.items() if publication_before.get(p) != content}
                changes.update({p: None for p in publication_before if p not in generated})
                changes[STATUS] = core.json_bytes(state)
                expected = dict(baseline)
                expected.update(publication_before)
                expected.update({p: None for p in changes if p not in expected})
                expected[STATUS] = pending
                report('Gecontroleerde publicatie en eindrapport opslaan')
                core.install_changes(root, changes, expected)
            return ('Finish geslaagd: brongegevens, beslisrecords, publicatie en batchtests gecontroleerd.\n' +
                    tests + '\nReview nu git status en git diff; commit en push zelf.\nRapport: ' + STATUS)
        except BaseException as exc:
            state.update(status='failed', error=str(exc) or type(exc).__name__)
            # Leave user/concurrent edits to the status file intact.
            if status_bytes(root) == pending:
                core.install_changes(root, {STATUS: core.json_bytes(state)}, {STATUS: pending})
            raise
