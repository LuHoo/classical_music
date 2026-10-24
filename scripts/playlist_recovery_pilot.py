#!/usr/bin/env python3
"""Read-only, bounded recovery test against an existing playlist CSV snapshot."""
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from classical_music.tidal_auth import access_token
from classical_music.tidal_maintenance import TidalAPI, Transport

OUTPUT = Path('reports/tidal-maintenance/playlist-recovery.json')
SOURCE = Path('side materials/Music collection/Best Classical.csv')


def main():
    report = {'checked_at': datetime.now(UTC).isoformat(), 'country': 'NL',
              'source': str(SOURCE), 'source_is_live_playlist': False,
              'playlist_mutations': 0, 'rows': []}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    def save():
        OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    try:
        api = TidalAPI(Transport(), access_token(), 'NL')
        with SOURCE.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        def inspect(position):
            source = rows[position - 1]
            old_id = source['trackId']
            isrc = source['isrc']
            result = {'position_in_export': position, 'old_id': old_id,
                      'title': source['title'], 'artist': source['artist'],
                      'album': source['album'], 'export_isrc': isrc,
                      'export_duration': source['duration'], 'candidates': []}
            report['rows'].append(result)
            try:
                doc = api.request('tracks/' + old_id, {})
                result['old_api_resource'] = doc['data']
            except ValueError as exc:
                result['old_api_error'] = str(exc)
            try:
                doc = api.request('tracks', {'filter[isrc]': isrc})
                result['search_has_next_page'] = bool(doc.get('links', {}).get('next'))
                for item in doc['data']:
                    if item.get('type') != 'tracks' or not str(item.get('id', '')).isdigit():
                        continue
                    candidate = api.request('tracks/' + item['id'], {})['data']
                    attrs = candidate.get('attributes', {})
                    result['candidates'].append({'id': candidate['id'],
                        'same_isrc': attrs.get('isrc') == isrc,
                        'attributes': attrs, 'relationships': candidate.get('relationships', {})})
                result['matching_ids'] = [c['id'] for c in result['candidates'] if c['same_isrc']]
            except ValueError as exc:
                result['search_error'] = str(exc)
            # Catalogue existence in NL is not proof of account-level playback.
            result['playback_verified'] = False
            save()
            return result
        first = inspect(139)
        known = api.request('tracks/283191456', {})['data']
        report['known_replacement'] = known
        report['first_test_passed'] = (
            known.get('attributes', {}).get('isrc') == first['export_isrc']
            and '283191456' in first.get('matching_ids', [])
            and not first.get('search_has_next_page', True))
        save()
        if not report['first_test_passed']:
            print('Geysir recovery not established; remaining 22 tracks not queried.')
            return 2
        for pos in list(range(140, 147)) + list(range(345, 360)):
            inspect(pos)
        print(json.dumps({'first_test_passed': True, 'tracks_checked': len(report['rows']),
                          'playlist_mutations': 0}))
        return 0
    except ValueError as exc:
        report['error'] = str(exc)
        save()
        print('Recovery pilot failed: ' + str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
