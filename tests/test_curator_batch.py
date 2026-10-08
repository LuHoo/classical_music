"""Deterministic batch safety tests: no live issue, Git or network dependencies."""
import json

import pytest

from classical_music import curator as core, curator_batch as batch
from classical_music.chamber_import import MANIFEST


@pytest.fixture
def repository(tmp_path):
    (tmp_path / 'data/performances').mkdir(parents=True)
    manifest = dict(source={'name': 'Test', 'url': 'https://tidal.com/playlist/test'},
                    units=[], recommendation_choices=[], resolved_choices=[], new_records=[],
                    changed_existing=[], summary={s: {} for s in
                        ('import_new', 'reuse_existing', 'recommendation_choice', 'not_selected')})
    for issue, codes in ((9001, ('C001', 'C002')), (9002, ('C003', 'C004'))):
        choice = dict(issue_url=core.ISSUES + str(issue), work_id=f'work-{issue}',
                      composer='Test', title=f'Work {issue}', units=list(codes),
                      existing_performances=[], decision=None)
        manifest['recommendation_choices'].append(choice)
        for code in codes:
            number = int(code[1:])
            manifest['units'].append(dict(unit_id=code, work_id=choice['work_id'],
                curator_issue=choice['issue_url'], disposition='recommendation_choice',
                positions=[number], performers=[{'name': 'Test pianist', 'role': 'piano'}],
                tracks=[{'id': str(number), 'position': number, 'album_titles': ['Test album']}]))
    core.refresh_summary(manifest)
    (tmp_path / MANIFEST).parent.mkdir(parents=True)
    (tmp_path / MANIFEST).write_bytes(core.json_bytes(manifest))
    text = '\n'.join(f'| {s} | 0 | 0 |' for s in manifest['summary'])
    text += '\nNew canonical records: {}. Reuse covers 0 existing Performances.\n'
    text += '**2 pending Work-level decisions**\n'
    text += '\n'.join(f'| [#{i}]({core.ISSUES}{i}) | Test | A, B |' for i in (9001, 9002))
    (tmp_path / MANIFEST.parent / 'README.md').write_text(text)
    return tmp_path


def files(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def status(root):
    return json.loads((root / batch.STATUS).read_text())


@pytest.fixture
def finish_checks(monkeypatch):
    calls = []
    def validate(root, report):
        calls.append('validate')
        page = root / 'publication/works/test.md'
        page.parent.mkdir(parents=True)
        page.write_text('Validated publication')
        return [str(MANIFEST)]
    def tests(root, report):
        calls.append('tests')
        return 'batch regressions passed'
    monkeypatch.setattr(batch, 'validate_batch', validate)
    monkeypatch.setattr(batch, 'run_regressions', tests)
    return calls


def test_default_saves_multiple_decisions_and_finish_checks_once(repository, finish_checks):
    for issue, code in ((9001, 'C001'), (9002, 'C004')):
        result = batch.record_decision(repository, issue, code)
        assert 'nog niet eindgecontroleerd' in result and './curator finish' in result
        record = json.loads((repository / f'reports/curator-decisions/issue-{issue}.json').read_text())
        assert record['curator'] == 'LAH'
    assert finish_checks == []
    assert status(repository)['status'] == 'pending' and status(repository)['issues'] == [9001, 9002]
    assert not (repository / 'publication').exists()
    assert 'Finish geslaagd' in batch.finish(repository)
    assert finish_checks == ['validate', 'tests']
    assert status(repository)['status'] == 'validated'
    assert status(repository)['inputs_sha256'] == batch.fingerprint(batch.snapshot(repository))
    assert (repository / 'publication/works/test.md').read_text() == 'Validated publication'


def test_dry_run_never_writes_or_validates(repository, finish_checks):
    before = files(repository)
    assert 'Preview only' in batch.record_decision(repository, 9001, 'C001', apply=False)
    assert files(repository) == before and finish_checks == []


def test_retry_is_noop_and_conflicting_choice_fails(repository):
    batch.record_decision(repository, 9001, 'C001', curator='Other')
    before = files(repository)
    assert 'Already recorded' in batch.record_decision(repository, 9001, 'C001')
    assert files(repository) == before
    with pytest.raises(core.CuratorError, match='different'):
        batch.record_decision(repository, 9001, 'C002')
    assert files(repository) == before


def test_next_decision_clears_previous_validation_stamp(repository, finish_checks):
    batch.record_decision(repository, 9001, 'C001')
    batch.finish(repository)
    batch.record_decision(repository, 9002, 'C003')
    assert status(repository)['status'] == 'pending'
    assert 'inputs_sha256' not in status(repository)


@pytest.mark.parametrize('failed_step', ['validate_batch', 'run_regressions'])
def test_failed_finish_preserves_decisions_and_old_publication(repository, finish_checks, monkeypatch, failed_step):
    batch.record_decision(repository, 9001, 'C001')
    original = batch.snapshot(repository)
    page = repository / 'publication/old.md'
    page.parent.mkdir()
    page.write_text('old publication')
    def fail(*args):
        raise core.CuratorError('Expected validation failure')
    monkeypatch.setattr(batch, failed_step, fail)
    with pytest.raises(core.CuratorError, match='Expected validation failure'):
        batch.finish(repository)
    assert batch.snapshot(repository) == original
    assert page.read_text() == 'old publication'
    assert not (repository / 'publication/works/test.md').exists()
    assert status(repository)['status'] == 'failed'
    assert not (repository / '.curator.lock').exists()


def test_finish_accepts_preexisting_decisions_without_batch_file(repository, finish_checks):
    assert 'Finish geslaagd' in batch.finish(repository)
    assert status(repository)['status'] == 'validated'


def test_changes_during_finish_prevent_success(repository, finish_checks, monkeypatch):
    batch.record_decision(repository, 9001, 'C001')
    def tests(*args):
        (repository / MANIFEST.parent / 'README.md').write_text('Concurrent edit')
        return 'passed'
    monkeypatch.setattr(batch, 'run_regressions', tests)
    with pytest.raises(core.CuratorError, match='inputs changed'):
        batch.finish(repository)
    assert status(repository)['status'] == 'failed'
    assert not (repository / 'publication').exists()


def test_mutating_tests_cannot_validate_different_data(repository, finish_checks, monkeypatch):
    def tests(stage, report):
        (stage / MANIFEST).write_text('{}')
        return 'passed'
    monkeypatch.setattr(batch, 'run_regressions', tests)
    with pytest.raises(core.CuratorError, match='Tests changed'):
        batch.finish(repository)
    assert status(repository)['status'] == 'failed'


@pytest.mark.parametrize('action', ['record', 'finish'])
def test_batch_lock_blocks_parallel_writers(repository, action):
    (repository / '.curator.lock').touch()
    with pytest.raises(core.CuratorError, match='Another curator'):
        if action == 'record':
            batch.record_decision(repository, 9001, 'C001')
        else:
            batch.finish(repository)
    assert (repository / '.curator.lock').exists()


def test_entry_rolls_back_on_write_failure(repository, monkeypatch):
    before = files(repository)
    original = core.os.replace
    def fail(source, target):
        if target.name == 'batch-status.json':
            raise OSError('Disk failure')
        return original(source, target)
    monkeypatch.setattr(core.os, 'replace', fail)
    with pytest.raises(OSError, match='Disk failure'):
        batch.record_decision(repository, 9001, 'C001')
    assert files(repository) == before


def test_playlist_confirmation_is_deferred_too(repository, finish_checks):
    batch.record_decision(repository, 9001, 'C001', playlist_remove=True)
    batch.record_decision(repository, 9001, 'playlist-done', note='Checked IDs')
    record = json.loads((repository / 'reports/curator-decisions/issue-9001.json').read_text())
    assert record['playlist_change']['status'] == 'done'
    assert record['playlist_change']['confirmed_by'] == 'LAH'
    assert finish_checks == []


def test_cli_defaults_overrides_dry_run_and_finish(monkeypatch):
    calls = []
    monkeypatch.setattr(batch, 'record_decision', lambda *a, **kw: calls.append((a, kw)) or 'saved')
    monkeypatch.setattr(batch, 'finish', lambda *a, **kw: calls.append(('finish', kw)) or 'finished')
    core.main(['9001', 'C001'])
    assert calls[-1][1]['apply'] is True and calls[-1][1]['curator'] == 'LAH'
    core.main(['9001', 'C001', '--dry-run', '--curator', 'Other'])
    assert calls[-1][1]['apply'] is False and calls[-1][1]['curator'] == 'Other'
    core.main(['9001', 'C001', '--apply'])
    assert calls[-1][1]['apply'] is True
    core.main(['finish'])
    assert calls[-1][0] == 'finish'
    before = len(calls)
    for args in (['finish', 'C001'], ['finish', '--dry-run'], ['finish', '--apply'], ['0', 'C001'],
                 ['9001'], ['9001', 'C001', '--apply', '--dry-run']):
        with pytest.raises(SystemExit) as exc:
            core.main(args)
        assert exc.value.code == 2
    assert len(calls) == before


def test_runner_uses_same_interpreter_and_reports_failure(repository, monkeypatch):
    from types import SimpleNamespace
    test = repository / batch.TESTS[0]
    test.parent.mkdir(parents=True)
    test.write_text('')
    seen = []
    def run(command, **kwargs):
        seen.append((command, kwargs))
        return SimpleNamespace(returncode=1, stdout='assertion failed', stderr='')
    monkeypatch.setattr(batch.subprocess, 'run', run)
    with pytest.raises(core.CuratorError, match='assertion failed'):
        batch.run_regressions(repository, lambda message: None)
    assert seen[0][0][:3] == [batch.sys.executable, '-m', 'pytest']
    assert seen[0][1]['cwd'] == repository


def test_validation_shares_one_build_and_checks_reused_links(repository, monkeypatch):
    from types import SimpleNamespace
    calls = []
    output = repository / 'publication'
    (output / 'works').mkdir(parents=True)
    page = output / 'works/reused.md'
    page.write_text('https://tidal.com/track/123')
    manifest_path = repository / MANIFEST
    manifest = json.loads(manifest_path.read_text())
    manifest['resolved_choices'] = [{'work_id': 'reused', 'decision': {
        'performances': [{'tidal_url': 'https://tidal.com/track/123'}]}}]
    manifest_path.write_bytes(core.json_bytes(manifest))
    generated = SimpleNamespace(output_dir=output)
    class Generator:
        def __init__(self, root):
            pass
        def generate(self):
            calls.append('build')
            return generated
    def audit(root, *, data, generated):
        calls.append('audit')
        assert generated.output_dir == output
        assert 'performances' in data
    monkeypatch.setattr(batch, 'PublicationSiteGenerator', Generator)
    monkeypatch.setattr(batch, 'import_module', lambda name: SimpleNamespace(audit=audit))
    batch.validate_batch(repository, lambda text: None)
    assert calls == ['build', 'audit']
    page.write_text('Missing selected link')
    with pytest.raises(core.CuratorError, match='Selected recommendation missing'):
        batch.validate_batch(repository, lambda text: None)
