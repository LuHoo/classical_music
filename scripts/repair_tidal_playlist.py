#!/usr/bin/env python3
"""Apply only the 609 explicitly approved occurrences from the verified NL scan."""
import argparse
import copy
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from playlist_live_pilot import Client, PLAYLIST
from scan_tidal_playlist import ScannerClient, assess

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/tidal-maintenance/full-playlist-scan-2026-10-03.json'
JOURNAL = ROOT / 'reports/tidal-maintenance/confirmed-repair-local.json'


def save(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def identity(item):
    return item['type'], item['id'], item.get('meta', {}).get('itemId')


def plan(report, source):
    if report.get('playlist', {}).get('id') != PLAYLIST or report.get('country') != 'NL' or not report.get('source_unchanged'):
        raise ValueError('Unexpected or unstable approval report')
    rows = [r for r in report['rows'] if r['status'] == 'CONFIRMED']
    if len(rows) != 609 or len({r['item_id'] for r in rows}) != 609:
        raise ValueError('Expected exactly 609 distinct approved occurrences')
    if len(source['items']) != report['total_occurrences'] or source['playlist']['attributes']['lastModifiedAt'] != report['playlist']['attributes']['lastModifiedAt']:
        raise ValueError('Playlist changed since approval; a new scan is required')
    selected = {r['item_id']: r for r in rows}
    groups = []
    active = []
    for position, item in enumerate(source['items'], 1):
        row = selected.get(item.get('meta', {}).get('itemId'))
        if row:
            if identity(item) != ('tracks', row['old_id'], row['item_id']) or row['position'] != position or row['replacement_id'] == row['old_id']:
                raise ValueError('Approved occurrence no longer matches its position')
            active.append(row)
        if active and (not row or len(active) == 50):
            groups.append(active)
            active = []
    if active:
        groups.append(active)
    if sum(map(len, groups)) != 609:
        raise ValueError('Some approved occurrences are missing')
    ids = [identity(i)[2] for i in source['items']]
    if not all(ids) or len(set(ids)) != len(ids):
        raise ValueError('Missing or duplicate occurrence IDs')
    return rows, groups


def validate_candidates(client, rows):
    isrcs = list(dict.fromkeys(r['fingerprint']['isrc'] for r in rows))
    candidates = []
    for offset in range(0, len(isrcs), 20):
        candidates.extend(client.tracks('isrc', isrcs[offset:offset+20]))
    for row in rows:
        status, matches = assess(row['fingerprint'], candidates, client.resources)
        if status != 'CONFIRMED' or matches[0]['id'] != row['replacement_id']:
            raise ValueError('Replacement catalogue identity changed at position ' + str(row['position']))


def execute(client, report, path, catalogue):
    if path.exists():
        raise ValueError('A repair journal already exists. Do not repeat writes blindly; inspect this journal before continuing: ' + str(path))
    source = client.snapshot(PLAYLIST)
    rows, groups = plan(report, source)
    validate_candidates(catalogue, rows)
    journal = {'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'prepared',
               'approved_occurrences': 609, 'completed_occurrences': 0,
               'backup': source, 'operations': []}
    save(path, journal)
    expected = copy.deepcopy(source['items'])
    marker = source['playlist']['attributes']['lastModifiedAt']
    endpoint = '/playlists/' + PLAYLIST + '/relationships/items'
    def metadata():
        resource = client.request('/playlists/' + PLAYLIST + '?countryCode=NL')['data']
        if resource['id'] != PLAYLIST:
            raise ValueError('Unexpected playlist metadata')
        return resource['attributes']
    def check_current(count):
        attrs = metadata()
        if attrs.get('lastModifiedAt') != marker or attrs.get('numberOfItems') != count:
            raise ValueError('Concurrent playlist change detected; stopping')
    try:
        for group in groups:
            check_current(len(expected))
            op = {'rows': group, 'state': 'inserting'}
            journal['operations'].append(op)
            journal['status'] = 'running'
            save(path, journal)
            inserted = client.request(endpoint, 'POST', {
                'data': [{'type': 'tracks', 'id': r['replacement_id']} for r in group],
                'meta': {'positionBefore': group[0]['item_id'], 'onDuplicates': 'ADD'}})
            op['response'] = inserted
            save(path, journal)  # Preserve the response even if validation fails.
            added = inserted.get('data', [])
            ids = [identity(i)[2] for i in added]
            if inserted.get('meta', {}).get('skipped') or [(i.get('type'), i.get('id')) for i in added] != [('tracks', r['replacement_id']) for r in group] or not all(ids) or len(set(ids)) != len(ids) or set(ids) & {identity(i)[2] for i in expected}:
                raise ValueError('Insertion response not verified; old occurrences retained')
            op['state'] = 'inserted'
            save(path, journal)
            attrs = metadata()
            if attrs.get('numberOfItems') != len(expected) + len(group):
                raise ValueError('Unexpected count after insertion; old occurrences retained')
            marker = attrs['lastModifiedAt']
            check_current(len(expected) + len(group))
            op['state'] = 'deleting'
            save(path, journal)
            client.request(endpoint, 'DELETE', {'data': [
                {'type': 'tracks', 'id': r['old_id'], 'meta': {'itemId': r['item_id']}} for r in group]})
            start = next(n for n, i in enumerate(expected) if identity(i)[2] == group[0]['item_id'])
            expected[start:start+len(group)] = added
            op['state'] = 'deleted'
            journal['completed_occurrences'] += len(group)
            save(path, journal)
            attrs = metadata()
            if attrs.get('numberOfItems') != len(expected):
                raise ValueError('Unexpected count after deletion')
            marker = attrs['lastModifiedAt']
            print(json.dumps({'replaced': journal['completed_occurrences'], 'total': 609}), flush=True)
        final = client.snapshot(PLAYLIST)
        journal['final_snapshot'] = final
        if [identity(i) for i in final['items']] != [identity(i) for i in expected]:
            raise ValueError('Final occurrence/order comparison failed; inspect journal')
        journal['status'] = 'passed'
        journal['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(path, journal)
        print(json.dumps({'status': 'passed', 'replaced_occurrences': 609, 'final_item_count': len(final['items']), 'order_verified': True, 'journal': str(path)}))
    except Exception as exc:
        journal['status'] = 'stopped'
        journal['error'] = str(exc)
        save(path, journal)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, default=JOURNAL)
    args = parser.parse_args(argv)
    token = os.environ.get('TIDAL_USER_ACCESS_TOKEN', '')
    if not token:
        raise ValueError('Local user OAuth login is required')
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    execute(Client(token), report, args.journal, ScannerClient(token))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit('Repair stopped: ' + str(exc))
