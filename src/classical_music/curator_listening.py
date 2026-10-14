"""Issue-triggered comparison playlists from reviewed import candidates.

The issue comment is a durable operational journal, not a second catalogue.
Only a newly created comparison playlist can receive tracks. Source playlists
and canonical decisions are never changed by this module.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from uuid import UUID, uuid5, NAMESPACE_URL

REPO = 'LuHoo/classical_music'
ISSUES = f'https://github.com/{REPO}/issues/'
LABEL = 'phase-2-curator-workflow'
MARKER = 'curator-listening-playlist:v1'
TRUSTED = {'OWNER', 'MEMBER', 'COLLABORATOR'}
BATCH_SIZE = 20


def require(condition, message):
    if not condition:
        raise ValueError(message)


def trusted(document):
    user = document.get('user', {})
    return (document.get('author_association') in TRUSTED or
            user.get('login') == 'github-actions[bot]' and user.get('type') == 'Bot')


def eligible(issue):
    return ('pull_request' not in issue and issue.get('state') == 'open' and trusted(issue)
            and LABEL in {label['name'] for label in issue.get('labels', [])})


def read_json(path):
    return json.loads(path.read_text())


def metadata(body):
    matches = re.findall(r'<!--\s*curator-choice\s+(\{.*?\})\s*-->', body or '', re.S)
    require(len(matches) <= 1, 'Multiple curator-choice metadata blocks')
    return json.loads(matches[0]) if matches else None


def manifest_path(root, value):
    relative = Path(value)
    require(not relative.is_absolute() and '..' not in relative.parts and
            relative.as_posix().startswith('reports/playlist-import/') and relative.suffix == '.json',
            'Manifest must be a JSON file under reports/playlist-import')
    path = root / relative
    require(path.resolve().is_relative_to((root / 'reports/playlist-import').resolve()), 'Manifest escapes import directory')
    return path


def reviewed_choice(root, issue):
    """Resolve an existing issue binding, or an explicit pre-creation Work binding."""
    hint = metadata(issue.get('body'))
    url = ISSUES + str(issue['number'])
    matches = []
    for path in sorted((root / 'reports/playlist-import').rglob('*.json')):
        manifest = read_json(path)
        if not isinstance(manifest, dict):
            continue
        for key in ('recommendation_choices', 'resolved_choices'):
            for choice in manifest.get(key, []):
                if choice.get('issue_url') == url:
                    matches.append((path, manifest, choice, key))
    if not matches and hint:
        path = manifest_path(root, hint['manifest'])
        manifest = read_json(path)
        for choice in manifest.get('recommendation_choices', []):
            if choice['work_id'] == hint['work_id']:
                require(choice.get('issue_url') in (None, '', url), 'Choice belongs to another issue')
                matches.append((path, manifest, choice, 'recommendation_choices'))
    require(len(matches) == 1, 'No unique reviewed choice available; commit/register its manifest or add curator-choice metadata')
    path, manifest, choice, key = matches[0]
    require(key == 'recommendation_choices' and not choice.get('decision'), 'Choice is already resolved')
    if hint:
        require(manifest_path(root, hint['manifest']) == path and hint['work_id'] == choice['work_id'],
                'Issue metadata conflicts with its registered choice')
    return path, manifest, choice


def names(performers):
    return ', '.join(p['name'] if isinstance(p, dict) else p for p in performers)


def candidate(label, unit):
    tracks = unit['tracks']
    require(isinstance(tracks, list) and tracks and all(isinstance(t, dict) and
            re.fullmatch(r'[0-9]+', str(t.get('id', ''))) for t in tracks), 'Candidate has missing/invalid track IDs')
    performers = names(unit.get('performers') or unit.get('candidate_performers') or [])
    require(performers, 'Candidate has no reviewed performers')
    return {'label': label, 'performers': performers,
            'track_ids': [str(t['id']) for t in tracks], 'excerpt': unit.get('excerpt')}


def build_plan(root, issue):
    path, manifest, choice = reviewed_choice(root, issue)
    unit_ids = [u['unit_id'] for u in manifest['units'] if u.get('unit_id')]
    require(len(unit_ids) == len(set(unit_ids)), 'Duplicate source unit_id values')
    by_id = {u['unit_id']: u for u in manifest['units'] if u.get('unit_id')}
    require(len(choice['units']) == len(set(choice['units'])), 'Repeated candidate unit')
    aliases = choice.get('choice_aliases', {})
    require(all(uid in choice['units'] for uid in aliases.values()), 'Alias points outside the reviewed choice')
    candidates, represented = [], set()
    for uid in choice['units']:
        require(uid in by_id, f'Candidate {uid} needs a stable unit_id in the existing manifest')
        unit = by_id[uid]
        require(unit.get('work_id') == choice['work_id'], 'Candidate belongs to another Work')
        label = next((k for k in sorted(aliases) if aliases[k] == uid), uid)
        candidates.append(candidate(label, unit))
        if unit.get('performance_id'):
            represented.add(unit['performance_id'])
    # An existing recommendation may be outside this source playlist. Its one
    # listening anchor cannot safely stand in for a complete multi-movement work.
    for pid in choice.get('existing_performances', []):
        if pid in represented:
            continue
        evidence = choice.get('existing_performance_tracks', {}).get(pid)
        require(evidence and evidence.get('reviewed_complete') is True and evidence.get('source'),
                f'Existing recommendation {pid} needs reviewed_complete tracks and source evidence in existing_performance_tracks')
        require(re.fullmatch(r'[a-z0-9-]+', pid), 'Invalid Performance ID')
        from ruamel.yaml import YAML
        perf = YAML(typ='safe').load((root / 'data/performances' / (pid + '.yaml')).read_text())
        require(perf['work_id'] == choice['work_id'], 'Existing recommendation belongs to another Work')
        candidates.append(candidate('existing', dict(performers=perf['performers'], tracks=evidence['tracks'], excerpt=perf.get('excerpt'))))
    require(len(candidates) >= 2, 'A comparison needs at least two reviewed candidates')
    require(sum(len(c['track_ids']) for c in candidates) <= 500, 'Comparison exceeds 500 tracks; review before creating it')
    protected = set()
    for source_path in (root / 'reports/playlist-import').rglob('*.json'):
        doc = read_json(source_path)
        if isinstance(doc, dict):
            source = doc.get('source', {})
            pid = source.get('playlist_id') or source.get('url', '').rsplit('/playlist/', 1)[-1]
            if pid:
                protected.add(pid)
    plan = {'issue': issue['number'], 'issue_url': ISSUES + str(issue['number']),
            'manifest': str(path.relative_to(root)), 'work_id': choice['work_id'],
            'work': choice['title'], 'composer': choice['composer'],
            'candidates': candidates, 'protected_playlist_ids': sorted(protected)}
    plan['sha256'] = hashlib.sha256(json.dumps({k: v for k, v in plan.items() if k != 'protected_playlist_ids'}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    plan['name'] = f"Curator #{issue['number']} — {choice['composer']} — {choice['title']}"[:100]
    plan['description'] = f"{plan['issue_url']}\nComparison plan SHA256: {plan['sha256']}"
    return plan


def track_ids(plan):
    return [tid for c in plan['candidates'] for tid in c['track_ids']]


def find_journal(comments):
    found = []
    for comment in comments:
        if not trusted(comment):
            continue
        matches = re.findall(r'<!-- ' + re.escape(MARKER) + r'\n(.*?)\n-->', comment.get('body', ''), re.S)
        for match in matches:
            found.append((comment['id'], json.loads(match)))
    require(len(found) <= 1, 'Multiple automation journals; reconcile comments before retrying')
    return found[0] if found else (None, None)


def comment_body(state, plan=None):
    lines = ['### Luisterplaylist voor curatorvergelijking', '']
    if state['phase'] == 'preview':
        lines.append('Voorbeeld: er wordt niets aangemaakt of opgeslagen.')
    elif state['phase'] == 'verified':
        lines.append(f"[Open de luisterplaylist](https://tidal.com/playlist/{state['playlist_id']})")
    elif state.get('playlist_id'):
        lines.append('De luisterplaylist wordt gevuld en gecontroleerd. Nog niet gereed voor vergelijking.')
    else:
        lines.append('De luisterplaylist is aangevraagd en wordt voorbereid.')
    if state.get('notice'):
        lines += ['', state['notice']]
    if plan:
        lines += ['', f"{plan['composer']} — {plan['work']}", '', '| Keuze | Uitvoering | Playlisttracks |', '|---|---|---|']
        start = 1
        for c in plan['candidates']:
            end = start + len(c['track_ids']) - 1
            label = c['label'].replace('|', '\\|')
            performers = c['performers'].replace('|', '\\|')
            excerpt = f" ({c['excerpt']})" if c.get('excerpt') else ''
            span = str(start) if start == end else f'{start}–{end}'
            lines.append(f'| {label} | {performers}{excerpt} | {span} |')
            start = end + 1
        lines += ['', 'Alle brontracks staan per uitvoering bij elkaar, in de vastgelegde volgorde. '
                  'De bronplaylists en curatorbeslissing zijn niet gewijzigd.']
    lines += ['', '<!-- ' + MARKER, json.dumps(state, sort_keys=True, ensure_ascii=False), '-->']
    return '\n'.join(lines)


def verify_target(snapshot, plan, pid):
    require(str(UUID(pid)) == pid and pid not in plan['protected_playlist_ids'], 'Refusing to write a source/invalid playlist')
    resource = snapshot['playlist']
    attrs = resource.get('attributes', {})
    require(resource['id'] == pid and attrs.get('name') == plan['name'] and
            attrs.get('description') == plan['description'], 'Comparison playlist identity/plan marker mismatch')
    items = snapshot['items']
    require(attrs.get('numberOfItems') == len(items), 'Incomplete comparison playlist snapshot')
    require(all(item['type'] == 'tracks' for item in items), 'Unexpected non-track in comparison playlist')
    return [str(item['id']) for item in items]


def provision(client, plan, state, save, *, recover_playlist_id=None):
    """Persist before each mutation; recover applied batches by exact live order."""
    state = deepcopy(state)
    require(state.get('plan_sha256') == plan['sha256'], 'Reviewed candidates changed; inspect the existing playlist/journal')
    if state['phase'] == 'verified':
        return state
    key = lambda operation: str(uuid5(NAMESPACE_URL, plan['issue_url'] + '/' + plan['sha256'] + '/' + operation))
    expected = track_ids(plan)
    if recover_playlist_id:
        require(state['phase'] == 'creating' and not state.get('playlist_id'), 'Recovery is only for an uncertain creation')
        require(str(UUID(recover_playlist_id)) == recover_playlist_id and
                recover_playlist_id not in plan['protected_playlist_ids'], 'Invalid/source recovery playlist')
        verify_target(client.snapshot(recover_playlist_id), plan, recover_playlist_id)
        state.update(phase='created', playlist_id=recover_playlist_id, offset=0)
        save(state)
    if state['phase'] == 'prepared':
        state.update(phase='creating', offset=0)
        save(state)
        response = client.request('/playlists', 'POST', {'data': {'type': 'playlists', 'attributes': {
            'name': plan['name'], 'description': plan['description'], 'accessType': 'UNLISTED'}}},
            idempotency_key=key('create'))
        pid = response['data']['id']
        require(str(UUID(pid)) == pid and pid not in plan['protected_playlist_ids'], 'Invalid/source playlist returned by create')
        state.update(phase='created', playlist_id=pid)
        save(state)
    require(state['phase'] in ('created', 'adding'),
            'Creation outcome is uncertain. Inspect TIDAL and recover the matching playlist ID; do not blindly create another')
    pid = state['playlist_id']
    live = verify_target(client.snapshot(pid), plan, pid)
    offset = state['offset']
    require(isinstance(offset, int) and 0 <= offset <= len(expected), 'Invalid journal offset')
    if state['phase'] == 'adding':
        end = min(offset + BATCH_SIZE, len(expected))
        require(live == expected[:end], 'Previous append outcome is uncertain or incomplete; inspect it before further writes')
        offset = end
        state.update(phase='created', offset=offset)
        save(state)
    require(live == expected[:offset], 'Comparison playlist changed; refusing to append')
    while offset < len(expected):
        end = min(offset + BATCH_SIZE, len(expected))
        state.update(phase='adding', offset=offset)
        save(state)
        client.request(f'/playlists/{pid}/relationships/items', 'POST', {
            'data': [{'type': 'tracks', 'id': tid} for tid in expected[offset:end]],
            'meta': {'onDuplicates': 'ADD'}}, idempotency_key=key(f'append-{offset}'))
        live = verify_target(client.snapshot(pid), plan, pid)
        require(live == expected[:end], 'Append verification failed; no further writes')
        offset = end
        state.update(phase='created', offset=offset)
        save(state)
    state.update(phase='verified')
    state.pop('notice', None)
    save(state)
    return state
