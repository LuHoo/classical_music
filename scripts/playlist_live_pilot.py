#!/usr/bin/env python3
"""Read a stable live playlist; optionally test writes on a temporary playlist only."""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from classical_music.tidal_auth import access_token

PLAYLIST = 'c11f614b-c011-43b2-be10-639f5cf7e5e3'


from classical_music.tidal_user import API, Client


def replaced_items(items, replacements):
    """Replace each occurrence without collapsing repeated track IDs."""
    return [{'type': item['type'], 'id': replacements.get(item['id'], item['id']) if item['type'] == 'tracks' else item['id']} for item in items]


def write_test(client):
    """Only a newly created disposable playlist can be mutated by this pilot."""
    a, b = '283191456', '283191455'
    created = client.request('/playlists', 'POST', {'data': {'type': 'playlists', 'attributes': {'name': 'Playlist repair API test ' + datetime.now(timezone.utc).isoformat(), 'accessType': 'UNLISTED'}}})
    pid = created['data']['id']
    if pid == PLAYLIST:
        raise ValueError('Test playlist unexpectedly equals source playlist')
    endpoint = '/playlists/' + pid + '/relationships/items'
    result = {'test_playlist_id': pid, 'source_playlist_mutations': 0}
    try:
        client.request(endpoint, 'POST', {'data': [{'type': 'tracks', 'id': x} for x in [a, b, a]], 'meta': {'onDuplicates': 'ADD'}})
        before = client.snapshot(pid)['items']
        if [i['id'] for i in before] != [a, b, a]:
            raise ValueError('Initial duplicate/order verification failed')
        first_item = before[0].get('meta', {}).get('itemId')
        if not first_item:
            raise ValueError('Missing occurrence itemId; deletion refused')
        client.request(endpoint, 'POST', {'data': [{'type': 'tracks', 'id': b}], 'meta': {'positionBefore': first_item, 'onDuplicates': 'ADD'}})
        added = client.snapshot(pid)['items']
        if [i['id'] for i in added] != [b, a, b, a] or added[1].get('meta', {}).get('itemId') != first_item:
            raise ValueError('Insert verification failed; old occurrence not removed')
        client.request(endpoint, 'DELETE', {'data': [{'type': 'tracks', 'id': a, 'meta': {'itemId': first_item}}]})
        after = client.snapshot(pid)['items']
        result['passed'] = [i['id'] for i in after] == [b, b, a]
        if not result['passed']:
            raise ValueError('Final occurrence/order verification failed')
        return result
    finally:
        client.request('/playlists/' + pid, 'DELETE')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-write', action='store_true', help='Requires a user-authorized token; writes only a disposable playlist')
    parser.add_argument('--output', type=Path, default=Path('reports/tidal-maintenance/playlist-live-pilot.json'))
    args = parser.parse_args(argv)
    token = os.environ.get('TIDAL_USER_ACCESS_TOKEN', '')
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'source_playlist_mutations': 0, 'user_token_present': bool(token)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        client = Client(token or access_token())
        source = client.snapshot(PLAYLIST)
        items = source['items']
        report['live_snapshot'] = source
        report['live_item_count'] = len(items)
        report['all_occurrences_have_item_ids'] = all(i.get('meta', {}).get('itemId') for i in items)
        report['duplicate_occurrences'] = sum(n-1 for n in Counter((i['type'],i['id']) for i in items).values())
        with Path('side materials/Music collection/Best Classical.csv').open(encoding='utf-8-sig', newline='') as f:
            exported = list(csv.DictReader(f))
        matches, plan = {}, []
        for pos in list(range(139,147)) + list(range(345,360)):
            old = exported[pos-1]
            doc = client.request('/tracks?' + urlencode({'countryCode':'NL', 'filter[isrc]':old['isrc']}))
            candidates = [c for c in doc['data'] if c.get('attributes',{}).get('isrc') == old['isrc'] and 'STREAM' in c.get('attributes',{}).get('availability',[])]
            occurrence_positions = [n for n,i in enumerate(items,1) if i['type']=='tracks' and i['id']==old['trackId']]
            row = {'export_position': pos, 'old_id':old['trackId'], 'isrc':old['isrc'], 'live_positions':occurrence_positions, 'candidate_ids':[c['id'] for c in candidates]}
            duration = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', candidates[0].get('attributes',{}).get('duration','')) if len(candidates)==1 else None
            same_duration = bool(duration) and sum(int(value or 0)*factor for value,factor in zip(duration.groups(),[3600,60,1])) == int(old['duration'].rstrip('s'))
            row['same_duration'] = same_duration
            if len(candidates)==1 and same_duration and not doc.get('links',{}).get('next'):
                matches[old['trackId']]=candidates[0]['id']
                row['replacement_id']=candidates[0]['id']
            plan.append(row)
        report['plan']=plan
        report['planned_order']=replaced_items(items,matches)
        report['planned_replacement_occurrences']=sum(i['type']=='tracks' and i['id'] in matches for i in items)
        report['write_test_status']='requires_user_authorization'
        if args.test_write:
            if not token:
                raise ValueError('A user-authorized TIDAL_USER_ACCESS_TOKEN is required for the disposable write test')
            report['write_test']=write_test(client)
            report['write_test_status']='passed'
        print(json.dumps({k:v for k,v in report.items() if k not in {'live_snapshot','plan','planned_order'}}, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError) as exc:
        report['error']=str(exc)
        print('Live playlist pilot failed: ' + str(exc), file=sys.stderr)
        return 2
    finally:
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
