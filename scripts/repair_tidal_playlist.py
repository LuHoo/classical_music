#!/usr/bin/env python3
"""Apply explicitly approved batches from the verified NL scan."""
import argparse
import copy
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from playlist_live_pilot import Client, PLAYLIST
from scan_tidal_playlist import ScannerClient, assess, seconds

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/tidal-maintenance/full-playlist-scan-2026-10-03.json'
JOURNAL = ROOT / 'reports/tidal-maintenance/confirmed-repair-local.json'
DURATION_JOURNAL = ROOT / 'reports/tidal-maintenance/duration-one-second-repair-local.json'


def save(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def identity(item):
    return item['type'], item['id'], item.get('meta', {}).get('itemId')


def one_second_match(fingerprint, candidate):
    checks = candidate['checks']
    duration = seconds(candidate.get('duration'))
    old_duration = fingerprint.get('duration_seconds')
    return (checks.get('same_isrc') and checks.get('same_title') and checks.get('artist_overlap')
            and not checks.get('same_duration') and duration is not None and old_duration is not None
            and abs(duration - old_duration) == 1)


def approved_rows(report, duration_batch=False):
    if not duration_batch:
        return [r for r in report['rows'] if r['status'] == 'CONFIRMED']
    return [dict(r, replacement_id=r['candidates'][0]['id']) for r in report['rows']
            if r['status'] == 'REVIEW' and len(r['candidates']) == 1
            and one_second_match(r['fingerprint'], r['candidates'][0])]


def plan(report, source, duration_batch=False, previous=None):
    if report.get('playlist', {}).get('id') != PLAYLIST or report.get('country') != 'NL' or not report.get('source_unchanged'):
        raise ValueError('Unexpected or unstable approval report')
    rows = approved_rows(report, duration_batch)
    total = 108 if duration_batch else 609
    if len(rows) != total or len({r['item_id'] for r in rows}) != total:
        raise ValueError('Unexpected number of distinct approved occurrences')
    baseline = report['playlist']
    if duration_batch:
        if not previous or previous.get('status') != 'passed' or previous.get('completed_occurrences') != 609:
            raise ValueError('The successful 609-replacement journal is required')
        final = previous.get('final_snapshot', {})
        if [identity(i) for i in source['items']] != [identity(i) for i in final.get('items', [])]:
            raise ValueError('Playlist no longer matches the successful 609-replacement snapshot')
        baseline = final.get('playlist', {})
    if len(source['items']) != report['total_occurrences'] or source['playlist']['attributes']['lastModifiedAt'] != baseline.get('attributes', {}).get('lastModifiedAt'):
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
    if sum(map(len, groups)) != total:
        raise ValueError('Some approved occurrences are missing')
    ids = [identity(i)[2] for i in source['items']]
    if not all(ids) or len(set(ids)) != len(ids):
        raise ValueError('Missing or duplicate occurrence IDs')
    return rows, groups


def validate_candidates(client, rows, duration_batch=False):
    isrcs = list(dict.fromkeys(r['fingerprint']['isrc'] for r in rows))
    candidates = []
    for offset in range(0, len(isrcs), 20):
        candidates.extend(client.tracks('isrc', isrcs[offset:offset+20]))
    for row in rows:
        status, matches = assess(row['fingerprint'], candidates, client.resources)
        valid = (len(matches) == 1 and (one_second_match(row['fingerprint'], matches[0]) if duration_batch else status == 'CONFIRMED'))
        if not valid or matches[0]['id'] != row['replacement_id']:
            raise ValueError('Replacement catalogue identity changed at position ' + str(row['position']))


def execute(client, report, path, catalogue, duration_batch=False, previous=None):
    if path.exists():
        raise ValueError('A repair journal already exists. Do not repeat writes blindly; inspect this journal before continuing: ' + str(path))
    source = client.snapshot(PLAYLIST)
    rows, groups = plan(report, source, duration_batch, previous)
    total = len(rows)
    validate_candidates(catalogue, rows, duration_batch)
    journal = {'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'prepared',
               'approved_occurrences': total, 'batch': 'duration_one_second' if duration_batch else 'confirmed', 'completed_occurrences': 0,
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
            print(json.dumps({'replaced': journal['completed_occurrences'], 'total': total}), flush=True)
        final = client.snapshot(PLAYLIST)
        journal['final_snapshot'] = final
        if [identity(i) for i in final['items']] != [identity(i) for i in expected]:
            raise ValueError('Final occurrence/order comparison failed; inspect journal')
        journal['status'] = 'passed'
        journal['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(path, journal)
        print(json.dumps({'status': 'passed', 'replaced_occurrences': total, 'final_item_count': len(final['items']), 'order_verified': True, 'journal': str(path)}))
    except Exception as exc:
        journal['status'] = 'stopped'
        journal['error'] = str(exc)
        save(path, journal)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path)
    parser.add_argument('--duration-one-second', action='store_true', help='Apply only the 108 explicitly approved one-second differences')
    args = parser.parse_args(argv)
    token = os.environ.get('TIDAL_USER_ACCESS_TOKEN', '')
    if not token:
        raise ValueError('Local user OAuth login is required')
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    previous = json.loads(JOURNAL.read_text(encoding='utf-8')) if args.duration_one_second else None
    path = args.journal or (DURATION_JOURNAL if args.duration_one_second else JOURNAL)
    execute(Client(token), report, path, ScannerClient(token), args.duration_one_second, previous)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit('Repair stopped: ' + str(exc))
