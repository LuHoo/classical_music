"""Comparison planning, issue hook, no duplicates and recovery without live writes."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from classical_music import curator_listening as listening
from classical_music import tidal_auth

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('comparison_script', ROOT / 'scripts/create_curator_listening_playlist.py')
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)
PID = 'e3a7cb9b-f246-48d0-b0a6-000000000246'


def issue(number=246, **overrides):
    return dict(number=number, state='open', body='', author_association='OWNER',
                user={'login': 'LuHoo'}, labels=[{'name': listening.LABEL}], **overrides)


class FakeGitHub:
    def __init__(self, doc=None):
        self.doc = doc or issue()
        self.saved = []
        self.comments_list = []

    def issue(self, number):
        assert number == self.doc['number']
        return self.doc

    def comments(self, number):
        return deepcopy(self.comments_list)

    def save_comment(self, number, comment_id, body):
        assert comment_id in (None, 1)
        self.saved.append(body)
        self.comments_list = [dict(id=1, user={'login': 'github-actions[bot]', 'type': 'Bot'},
                                  author_association='NONE', body=body)]
        return 1


class FakeTidal:
    def __init__(self, *, fail_create=False, fail_append=False, append_applied=True):
        self.created = 0
        self.calls = []
        self.items = []
        self.attributes = {}
        self.fail_create = fail_create
        self.fail_append = fail_append
        self.append_applied = append_applied

    def request(self, path, method='GET', body=None, *, idempotency_key=None):
        assert method == 'POST'  # This feature never deletes or replaces tracks.
        assert idempotency_key
        self.calls.append((path, deepcopy(body), idempotency_key))
        if path == '/playlists':
            self.created += 1
            self.attributes = body['data']['attributes']
            if self.fail_create:
                self.fail_create = False
                raise ValueError('Creation response lost')
            return {'data': {'id': PID}}
        assert path == f'/playlists/{PID}/relationships/items'
        assert body['meta']['onDuplicates'] == 'ADD'
        if not self.fail_append or self.append_applied:
            self.items.extend(deepcopy(body['data']))
        if self.fail_append:
            self.fail_append = False
            raise ValueError('Append response lost')
        return {'data': body['data']}

    def snapshot(self, pid):
        assert pid == PID
        attrs = dict(self.attributes, numberOfItems=len(self.items))
        return {'playlist': {'id': PID, 'attributes': attrs}, 'items': deepcopy(self.items)}


def state(plan):
    return dict(phase='prepared', issue=plan['issue'], plan_sha256=plan['sha256'])


def test_chamber_and_piano_plans_use_registered_units_and_movement_order():
    chamber = listening.build_plan(ROOT, issue())
    assert [c['label'] for c in chamber['candidates']] == ['C093', 'C372']
    assert listening.track_ids(chamber) == ['59657141', '59657142', '59657143', '198744929', '198744930', '198744931']
    piano = listening.build_plan(ROOT, issue(263))
    assert piano['manifest'].startswith('reports/playlist-import/piano/')
    assert [c['label'] for c in piano['candidates']] == ['P078', 'P081']
    assert all(c['track_ids'] for c in piano['candidates'])


def test_known_aliases_are_not_inferred():
    plan = listening.build_plan(ROOT, issue(241))
    assert [c['label'] for c in plan['candidates']] == ['A', 'B']
    assert plan['candidates'][0]['track_ids'][0] == '269512251'


def test_existing_recommendation_is_not_duplicated():
    plan = listening.build_plan(ROOT, issue(242))
    assert [c['label'] for c in plan['candidates']] == ['C035', 'C400']
    with pytest.raises(ValueError, match='reviewed_complete'):
        listening.build_plan(ROOT, issue(257))


def synthetic_manifest(root, *, existing=False):
    path = root / 'reports/playlist-import/best-classical/review.json'
    path.parent.mkdir(parents=True)
    manifest = {'source': {'playlist_id': 'original'}, 'units': [
        {'unit_id': 'BC001', 'work_id': 'work', 'candidate_performers': ['First'],
         'tracks': [{'id': '1'}, {'id': '2'}]},
        {'unit_id': 'BC002', 'work_id': 'work', 'candidate_performers': ['Second'],
         'tracks': [{'id': '3'}, {'id': '4'}]}],
        'recommendation_choices': [{'work_id': 'work', 'title': 'Work', 'composer': 'Composer',
                                    'units': ['BC001', 'BC002'], 'existing_performances': [], 'decision': None}]}
    if existing:
        manifest['recommendation_choices'][0]['existing_performances'] = ['old']
        manifest['recommendation_choices'][0]['existing_performance_tracks'] = {
            'old': {'reviewed_complete': True, 'source': 'verified album tracklist',
                    'tracks': [{'id': '5'}, {'id': '6'}]}}
        performance = root / 'data/performances/old.yaml'
        performance.parent.mkdir(parents=True)
        performance.write_text('id: old\nwork_id: work\nperformers:\n  - name: Existing\n')
    path.write_text(json.dumps(manifest))
    hint = {'manifest': str(path.relative_to(root)), 'work_id': 'work'}
    doc = issue(900)
    doc['body'] = '<!-- curator-choice ' + json.dumps(hint) + ' -->'
    return doc, path


def test_new_issue_can_bind_before_its_number_is_in_manifest(tmp_path):
    doc, _ = synthetic_manifest(tmp_path, existing=True)
    plan = listening.build_plan(tmp_path, doc)
    assert listening.track_ids(plan) == ['1', '2', '3', '4', '5', '6']
    assert plan['candidates'][-1]['label'] == 'existing'


def test_hint_cannot_hijack_another_issue_or_escape_imports(tmp_path):
    doc, path = synthetic_manifest(tmp_path)
    manifest = json.loads(path.read_text())
    manifest['recommendation_choices'][0]['issue_url'] = listening.ISSUES + '901'
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='another issue'):
        listening.build_plan(tmp_path, doc)
    with pytest.raises(ValueError, match='Manifest must'):
        listening.manifest_path(tmp_path, '../../secret.json')


def test_full_create_updates_one_comment_and_retry_is_noop():
    gh, tidal = FakeGitHub(), FakeTidal()
    assert 'Verified' in script.run(ROOT, gh, 246, apply=True, client_factory=lambda: tidal)
    assert tidal.created == 1 and len(tidal.items) == 6
    assert len(gh.comments_list) == 1
    assert 'https://tidal.com/playlist/' + PID in gh.comments_list[0]['body']
    assert '| C093 | Pro Arte Wind Quintet | 1–3 |' in gh.comments_list[0]['body']
    assert '| C372 | Ensemble Arabesques | 4–6 |' in gh.comments_list[0]['body']
    calls = deepcopy(tidal.calls)
    assert 'Already created' in script.run(ROOT, gh, 246, apply=True, client_factory=lambda: pytest.fail('No API call on completed retry'))
    assert tidal.calls == calls


def test_preview_needs_no_tidal_login_and_writes_nothing():
    gh = FakeGitHub()
    text = script.run(ROOT, gh, 246, client_factory=lambda: pytest.fail('Preview cannot call TIDAL'))
    assert 'Pro Arte Wind Quintet' in text and gh.saved == []
    assert 'niets aangemaakt of opgeslagen' in text


@pytest.mark.parametrize('alter', [lambda x: x.update(author_association='NONE'),
                                  lambda x: x.update(state='closed'), lambda x: x.update(labels=[]),
                                  lambda x: x.update(pull_request={})])
def test_non_curator_untrusted_closed_and_pr_events_do_not_write(alter):
    doc = issue()
    alter(doc)
    gh = FakeGitHub(doc)
    assert 'Skipped' in script.run(ROOT, gh, 246, apply=True)
    assert not gh.saved


def test_missing_manifest_is_queued_without_tidal_calls():
    gh = FakeGitHub(issue(900))
    with pytest.raises(ValueError, match='No unique'):
        script.run(ROOT, gh, 900, apply=True, client_factory=lambda: pytest.fail('No plan, no TIDAL'))
    _, journal = listening.find_journal(gh.comments_list)
    assert journal['phase'] == 'awaiting_manifest'


def test_lost_create_response_requires_explicit_recovery():
    plan = listening.build_plan(ROOT, issue())
    saved = []
    tidal = FakeTidal(fail_create=True)
    with pytest.raises(ValueError, match='response lost'):
        listening.provision(tidal, plan, state(plan), lambda s: saved.append(deepcopy(s)))
    assert saved[-1]['phase'] == 'creating'
    with pytest.raises(ValueError, match='uncertain'):
        listening.provision(tidal, plan, saved[-1], lambda s: saved.append(deepcopy(s)))
    assert tidal.created == 1
    result = listening.provision(tidal, plan, saved[-1], lambda s: saved.append(deepcopy(s)), recover_playlist_id=PID)
    assert result['phase'] == 'verified' and tidal.created == 1


def test_lost_append_response_is_recovered_by_live_order_without_duplicates():
    plan = listening.build_plan(ROOT, issue())
    plan['candidates'][0]['track_ids'] = ['1'] * 25  # Preserve repeated occurrences.
    saved = []
    tidal = FakeTidal(fail_append=True)
    with pytest.raises(ValueError, match='response lost'):
        listening.provision(tidal, plan, state(plan), lambda s: saved.append(deepcopy(s)))
    assert saved[-1]['phase'] == 'adding'
    result = listening.provision(tidal, plan, saved[-1], lambda s: saved.append(deepcopy(s)))
    assert result['phase'] == 'verified'
    assert [t['id'] for t in tidal.items] == listening.track_ids(plan)
    assert len({call[2] for call in tidal.calls}) == len(tidal.calls)


def test_unknown_append_outcome_is_not_blindly_retried():
    plan = listening.build_plan(ROOT, issue())
    saved = []
    tidal = FakeTidal(fail_append=True, append_applied=False)
    with pytest.raises(ValueError):
        listening.provision(tidal, plan, state(plan), lambda s: saved.append(deepcopy(s)))
    calls = len(tidal.calls)
    with pytest.raises(ValueError, match='uncertain'):
        listening.provision(tidal, plan, saved[-1], lambda s: saved.append(deepcopy(s)))
    assert len(tidal.calls) == calls


def test_external_edit_and_source_playlist_are_never_overwritten():
    plan = listening.build_plan(ROOT, issue())
    tidal = FakeTidal()
    tidal.attributes = {'name': plan['name'], 'description': plan['description']}
    tidal.items = [{'type': 'tracks', 'id': '999'}]
    journal = dict(state(plan), phase='created', playlist_id=PID, offset=0)
    with pytest.raises(ValueError, match='changed'):
        listening.provision(tidal, plan, journal, lambda s: None)
    plan['protected_playlist_ids'].append(PID)
    with pytest.raises(ValueError, match='source'):
        listening.provision(tidal, plan, journal, lambda s: None)
    assert not tidal.calls


def test_manifest_push_only_retries_previously_requested_playlists():
    gh = FakeGitHub()
    requested = issue(263)
    gh.pages = lambda path: [issue(246), requested]
    gh.comments = lambda number: [dict(id=1, author_association='OWNER', body=listening.comment_body(
        {'phase': 'awaiting_manifest', 'issue': 263}))] if number == 263 else []
    assert script.discover(gh, {}, 'push') == [263]
    assert script.discover(gh, {'issue': issue()}, 'issues') == [246]


def test_untrusted_forged_journal_is_ignored():
    comment = dict(id=1, author_association='NONE', user={'login': 'stranger'},
                   body=listening.comment_body({'phase': 'verified', 'playlist_id': PID}))
    assert listening.find_journal([comment]) == (None, None)


def test_missing_user_grant_cannot_fall_back_to_client_credentials(monkeypatch):
    monkeypatch.delenv('TIDAL_USER_ACCESS_TOKEN', raising=False)
    monkeypatch.delenv('TIDAL_USER_REFRESH_TOKEN', raising=False)
    monkeypatch.setenv('TIDAL_CLIENT_ID', 'application')
    monkeypatch.setenv('TIDAL_CLIENT_SECRET', 'secret')
    monkeypatch.setattr(tidal_auth, 'build_opener', lambda *a: pytest.fail('Do not use app-only grant'))
    with pytest.raises(ValueError, match='TIDAL_USER_REFRESH_TOKEN'):
        tidal_auth.user_access_token()


def test_refresh_request_scope_and_secret_redaction(monkeypatch, capsys):
    monkeypatch.delenv('TIDAL_USER_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('TIDAL_USER_REFRESH_TOKEN', 'refresh-secret')
    monkeypatch.setenv('TIDAL_CLIENT_ID', 'app')
    monkeypatch.setenv('TIDAL_CLIENT_SECRET', 'secret')
    monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, maximum): return json.dumps({'access_token': 'user-token', 'token_type': 'Bearer', 'scope': 'playlists.read playlists.write'}).encode()
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == tidal_auth.TOKEN_URL
            assert b'grant_type=refresh_token' in request.data
            assert b'refresh-secret' in request.data
            return Response()
    monkeypatch.setattr(tidal_auth, 'build_opener', lambda *a: Opener())
    assert tidal_auth.user_access_token() == 'user-token'
    assert not capsys.readouterr().out


def test_login_setup_pipes_refresh_grant_without_exposing_it(monkeypatch, capsys):
    import tidal_playlist_login as login
    calls = []
    monkeypatch.setattr(login.subprocess, 'run', lambda args, **kwargs: calls.append((args, kwargs)))
    login.save_curator_grant({'refresh_token': 'private-refresh'})
    args, kwargs = calls[0]
    assert 'private-refresh' not in ' '.join(args)
    assert kwargs['input'] == 'private-refresh' and kwargs['capture_output']
    assert 'private-refresh' not in capsys.readouterr().out
    with pytest.raises(ValueError, match='no secret saved'):
        login.save_curator_grant({})


def test_issue_before_manifest_is_completed_after_manifest_arrives(tmp_path):
    gh = FakeGitHub(issue(900))
    tidal = FakeTidal()
    with pytest.raises(ValueError, match='No unique'):
        script.run(tmp_path, gh, 900, apply=True, client_factory=lambda: pytest.fail('Do not create a partial playlist'))
    _, path = synthetic_manifest(tmp_path)
    manifest = json.loads(path.read_text())
    manifest['recommendation_choices'][0]['issue_url'] = listening.ISSUES + '900'
    path.write_text(json.dumps(manifest))
    assert 'Verified' in script.run(tmp_path, gh, 900, apply=True, client_factory=lambda: tidal)
    assert len(gh.comments_list) == 1 and tidal.created == 1
    assert [i['id'] for i in tidal.items] == ['1', '2', '3', '4']


def test_missing_login_preserves_prepared_request_for_retry():
    gh = FakeGitHub()
    def no_login():
        raise ValueError('Configure TIDAL_USER_REFRESH_TOKEN')
    with pytest.raises(ValueError, match='REFRESH_TOKEN'):
        script.run(ROOT, gh, 246, apply=True, client_factory=no_login)
    _, journal = listening.find_journal(gh.comments_list)
    assert journal['phase'] == 'prepared' and 'playlist_id' not in journal
    tidal = FakeTidal()
    script.run(ROOT, gh, 246, apply=True, client_factory=lambda: tidal)
    assert tidal.created == 1


def test_changed_plan_is_not_applied_to_existing_playlist(monkeypatch):
    gh = FakeGitHub()
    plan = listening.build_plan(ROOT, issue())
    gh.save_comment(246, None, listening.comment_body(state(plan), plan))
    changed = dict(plan, sha256='different')
    monkeypatch.setattr(script, 'build_plan', lambda *args: changed)
    with pytest.raises(ValueError, match='Candidate plan changed'):
        script.run(ROOT, gh, 246, apply=True, client_factory=lambda: pytest.fail('No mutation'))


def test_incomplete_snapshot_and_wrong_plan_marker_fail():
    plan = listening.build_plan(ROOT, issue())
    snapshot = {'playlist': {'id': PID, 'attributes': {'name': plan['name'],
                'description': plan['description'], 'numberOfItems': 1}}, 'items': []}
    with pytest.raises(ValueError, match='Incomplete'):
        listening.verify_target(snapshot, plan, PID)
    snapshot['playlist']['attributes']['description'] = 'unrelated playlist'
    with pytest.raises(ValueError, match='identity'):
        listening.verify_target(snapshot, plan, PID)


@pytest.mark.parametrize('response', [
    {'access_token': 'private-access', 'token_type': 'Bearer', 'scope': 'playlists.read'},
    {'access_token': 'private-access', 'token_type': 'Bearer', 'scope': 'playlists.read playlists.write', 'refresh_token': 'new-private-refresh'},
])
def test_insufficient_scope_or_rotated_grant_is_not_used(response, monkeypatch, capsys):
    monkeypatch.delenv('TIDAL_USER_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('TIDAL_USER_REFRESH_TOKEN', 'private-refresh')
    monkeypatch.setenv('TIDAL_CLIENT_ID', 'app')
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, maximum): return json.dumps(response).encode()
    class Opener:
        def open(self, request, timeout): return Response()
    monkeypatch.setattr(tidal_auth, 'build_opener', lambda *a: Opener())
    with pytest.raises(ValueError) as error:
        tidal_auth.user_access_token()
    assert 'private' not in str(error.value) + capsys.readouterr().out


def test_workflow_uses_trusted_default_branch_and_serializes_per_issue():
    from ruamel.yaml import YAML
    workflow = YAML(typ='safe').load((ROOT / '.github/workflows/curator-listening-playlist.yml').read_text())
    assert workflow['on']['issues']['types'] == ['opened', 'reopened', 'labeled', 'edited']
    assert 'pull_request_target' not in workflow['on']
    assert workflow['jobs']['discover']['permissions']['issues'] == 'read'
    job = workflow['jobs']['playlist']
    assert job['concurrency']['cancel-in-progress'] is False
    assert 'matrix.issue' in job['concurrency']['group']
    assert job['steps'][0]['with']['ref'] == '${{ github.event.repository.default_branch }}'
    assert job['steps'][0]['with']['persist-credentials'] is False


@pytest.fixture(scope='module', autouse=True)
def fixed_pending_choices(pending_curator_repository):
    """Production decisions must not change the preconditions of these tests."""
    import sys
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(sys.modules[__name__], 'ROOT', pending_curator_repository)
        yield
