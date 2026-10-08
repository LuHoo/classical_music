#!/usr/bin/env python3
"""Create one issue's comparison playlist; preview by default, no AI involved."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from classical_music.curator_listening import (
    REPO, LABEL, eligible, build_plan, find_journal, comment_body, provision, require)
from classical_music.tidal_auth import NoAuthRedirects, user_access_token
from classical_music.tidal_user import Client


class GitHub:
    def __init__(self, token):
        require(token, 'GITHUB_TOKEN is required to read the issue and maintain its playlist comment')
        self.token = token
        self.opener = build_opener(NoAuthRedirects())

    def request(self, path, method='GET', body=None):
        require(path.startswith('/issues'), 'Unexpected GitHub API path')
        request = Request(f'https://api.github.com/repos/{REPO}' + path, method=method,
            headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
                     'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'},
            data=json.dumps(body).encode() if body is not None else None)
        try:
            with self.opener.open(request, timeout=20) as response:
                raw = response.read(4_000_001)
            require(len(raw) <= 4_000_000, 'GitHub response too large')
            return json.loads(raw)
        except HTTPError as exc:
            raise ValueError(f'GitHub request failed (HTTP {exc.code})') from None
        except (URLError, OSError):
            raise ValueError('GitHub request failed (network error)') from None

    def pages(self, path):
        results = []
        separator = '&' if '?' in path else '?'
        for page in range(1, 101):
            rows = self.request(f'{path}{separator}per_page=100&page={page}')
            require(isinstance(rows, list), 'Invalid GitHub pagination response')
            results.extend(rows)
            if len(rows) < 100:
                return results
        raise ValueError('GitHub pagination limit exceeded')

    def issue(self, number):
        return self.request(f'/issues/{number}')

    def comments(self, number):
        return self.pages(f'/issues/{number}/comments')

    def save_comment(self, number, comment_id, body):
        path = f'/issues/comments/{comment_id}' if comment_id else f'/issues/{number}/comments'
        return self.request(path, 'PATCH' if comment_id else 'POST', {'body': body})['id']


def run(root, github, number, *, apply=False, recover_playlist_id=None, client_factory=None):
    require(number > 0, 'Issue number must be positive')
    issue = github.issue(number)
    if not eligible(issue):
        return 'Skipped: not an open, trusted curator issue.'
    comment_id, state = find_journal(github.comments(number))
    if state:
        require(state.get('issue') == number, 'Journal belongs to another issue')
    if state and state['phase'] == 'verified':
        return 'Already created: https://tidal.com/playlist/' + state['playlist_id']
    plan = None
    def save(value):
        nonlocal comment_id
        comment_id = github.save_comment(number, comment_id, comment_body(value, plan))
    try:
        plan = build_plan(root, issue)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        if apply:
            pending = state or {'phase': 'awaiting_manifest', 'issue': number}
            pending['notice'] = 'Nog geen volledige, eenduidige vergelijkingsgegevens: ' + str(exc)
            save(pending)
        raise
    if not apply:
        require(not recover_playlist_id, 'Recovery requires --apply')
        return comment_body({'phase': 'preview', 'issue': number, 'plan_sha256': plan['sha256']}, plan)
    if not state or state['phase'] == 'awaiting_manifest':
        state = {'phase': 'prepared', 'issue': number, 'plan_sha256': plan['sha256']}
        save(state)
    require(state.get('plan_sha256') == plan['sha256'], 'Candidate plan changed; review the existing journal before retrying')
    latest = deepcopy_state(state)
    def checkpoint(value):
        nonlocal latest
        save(value)
        latest = deepcopy_state(value)
    try:
        client = client_factory() if client_factory else Client(user_access_token())
        result = provision(client, plan, state, checkpoint, recover_playlist_id=recover_playlist_id)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        latest['notice'] = ('Automatisch aanmaken is gestopt: ' + str(exc) +
            '. Zie docs/workflows/curator-listening-playlists.md voor login of herstel.')
        save(latest)
        raise
    return 'Verified comparison playlist: https://tidal.com/playlist/' + result['playlist_id']


def deepcopy_state(state):
    return json.loads(json.dumps(state))


def discover(github, event, event_name, dispatch_issue=None):
    """Push retries only prior requests; never backfill all old curator issues."""
    if event_name == 'issues':
        issue = event['issue']
        return [issue['number']] if eligible(issue) else []
    if event_name == 'workflow_dispatch':
        number = int(dispatch_issue)
        require(number > 0, 'Issue number must be positive')
        return [number]
    if event_name == 'push':
        result = []
        for issue in github.pages('/issues?' + urlencode({'state': 'open', 'labels': LABEL})):
            if eligible(issue):
                _, state = find_journal(github.comments(issue['number']))
                if state and state['phase'] != 'verified':
                    result.append(issue['number'])
        return result
    raise ValueError('Unsupported workflow event')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('issue', type=int, nargs='?')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--recover-playlist-id')
    parser.add_argument('--discover', action='store_true')
    args = parser.parse_args(argv)
    try:
        require(os.environ.get('GITHUB_REPOSITORY', REPO) == REPO, 'This workflow belongs to ' + REPO)
        github = GitHub(os.environ.get('GITHUB_TOKEN', ''))
        if args.discover:
            event = read_event()
            issues = discover(github, event, os.environ['GITHUB_EVENT_NAME'], os.environ.get('INPUT_ISSUE'))
            with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                output.write('issues=' + json.dumps(issues) + '\n')
            print(f'{len(issues)} curator issue(s) ready for processing.')
        else:
            require(args.issue is not None, 'Supply an issue number')
            print(run(ROOT, github, args.issue, apply=args.apply, recover_playlist_id=args.recover_playlist_id))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f'curator playlist: {exc}\n')
    return 0


def read_event():
    return json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())


if __name__ == '__main__':
    raise SystemExit(main())
