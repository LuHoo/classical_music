#!/usr/bin/env python3
"""Report-only full playlist availability scan with conservative ISRC recovery."""
import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl, urljoin, quote

from playlist_live_pilot import Client, PLAYLIST, API
from classical_music.tidal_auth import access_token


def normalized(value):
    value = unicodedata.normalize('NFKD', value).casefold()
    return ''.join(c for c in value if c.isalnum())


def seconds(value):
    if not isinstance(value, str):
        return None
    if re.fullmatch(r'\d+s', value):
        return int(value[:-1])
    m = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?', value)
    if not m or not any(m.groups()):
        return None
    return sum(float(v or 0)*f for v,f in zip(m.groups(), [3600,60,1]))


class ScannerClient(Client):
    def __init__(self, token):
        super().__init__(token)
        self.resources = {}

    def request(self, path, method='GET', body=None):
        if method != 'GET':
            raise ValueError('The full scanner cannot make write requests')
        if '/relationships/items' in path:
            p = urlsplit(path)
            query = dict(parse_qsl(p.query))
            query['include'] = 'items,items.artists,items.albums'
            path = urlunsplit((p.scheme,p.netloc,p.path,urlencode(query),p.fragment))
        doc = super().request(path)
        data = doc.get('data', [])
        if isinstance(data, dict):
            data = [data]
        for item in list(data) + doc.get('included', []):
            if item.get('type') in {'tracks','artists','albums'} and isinstance(item.get('attributes'),dict):
                self.resources[(item['type'],item['id'])] = item
        return doc

    def tracks(self, field, values):
        """Follow bounded catalogue pages; do not assume 20 ISRCs yield <=20 hits."""
        params = {'countryCode':'NL', 'include':'artists,albums', 'filter['+field+']':','.join(values)}
        next_url = API + '/tracks?' + urlencode(params)
        seen, results = set(), []
        for _ in range(100):
            if not next_url:
                return results
            if next_url in seen:
                raise ValueError('Repeated catalogue pagination link')
            seen.add(next_url)
            doc = self.request(next_url)
            if not isinstance(doc.get('data'),list):
                raise ValueError('Invalid tracks response')
            results.extend(doc['data'])
            link = doc.get('links',{}).get('next')
            if isinstance(link,dict):
                link = link.get('href')
            next_url = urljoin(next_url,link) if link else None
            if next_url:
                p = urlsplit(next_url)
                if p.scheme!='https' or p.netloc!='openapi.tidal.com' or p.path not in {'/tracks','/v2/tracks'} or p.fragment:
                    raise ValueError('Unexpected catalogue pagination target')
                query=dict(parse_qsl(p.query))
                for key,value in params.items():
                    if key in query and query[key]!=value:
                        raise ValueError('Catalogue pagination changed query scope')
                    query.setdefault(key,value)
                next_url=urlunsplit((p.scheme,p.netloc,'/v2/tracks',urlencode(query),''))
        raise ValueError('Catalogue search exceeded page limit')


def artists(resource, resources):
    links = resource.get('relationships',{}).get('artists',{}).get('data',[])
    if not isinstance(links,list):
        return []
    return [resources.get(('artists',i['id']),{}).get('attributes',{}).get('name','') for i in links]


def fingerprint(resource, archived, resources):
    attrs = (resource or {}).get('attributes',{})
    if not any(attrs.get(k) for k in ['isrc','title','duration']):
        resource = None
    result = {'isrc':attrs.get('isrc'), 'title':attrs.get('title'), 'duration_seconds':seconds(attrs.get('duration')), 'artists':artists(resource or {},resources), 'source':'live_catalogue'}
    if archived:
        for target, source in [('isrc','isrc'),('title','title')]:
            if not result[target]:
                result[target]=archived.get(source)
                result['source']='live_and_export' if resource else 'csv_export'
        if result['duration_seconds'] is None:
            result['duration_seconds']=seconds(archived.get('duration'))
            result['source']='live_and_export' if resource else 'csv_export'
        if not any(result['artists']):
            result['artists']=[archived.get('artist','')]
            result['source']='live_and_export' if resource else 'csv_export'
    return result


def assess(old, candidates, resources):
    matches=[]
    for candidate in candidates:
        a=candidate.get('attributes',{})
        if candidate.get('type')!='tracks' or a.get('isrc')!=old.get('isrc') or 'STREAM' not in a.get('availability',[]):
            continue
        names=artists(candidate,resources)
        old_names={normalized(n) for n in old.get('artists',[]) if n}
        new_names={normalized(n) for n in names if n}
        checks={'same_isrc':True, 'same_title':bool(old.get('title')) and normalized(a.get('title',''))==normalized(old['title']),
                'same_duration':old.get('duration_seconds') is not None and seconds(a.get('duration'))==old['duration_seconds'],
                'artist_overlap':bool(old_names & new_names)}
        matches.append({'id':candidate['id'], 'url':'https://tidal.com/track/'+candidate['id'], 'title':a.get('title'),
                        'duration':a.get('duration'), 'artists':names, 'checks':checks})
    # Even one strong match is not automatically selected among multiple manifestations.
    if len(matches)==1 and all(matches[0]['checks'].values()):
        return 'CONFIRMED',matches
    return ('REVIEW' if matches else 'NOT_FOUND'),matches


def scan(client, snapshot, archived):
    items=snapshot['items']
    ids=list(dict.fromkeys(i['id'] for i in items if i['type']=='tracks'))
    pending=[rid for rid in ids if not isinstance(client.resources.get(('tracks',rid),{}).get('attributes',{}).get('availability'),list)]
    errors={}
    bulk_errors=[]
    for start in range(0,len(pending),20):
        batch=pending[start:start+20]
        try:
            client.tracks('id',batch)
        except ValueError as exc:
            bulk_errors.append({'ids':batch,'error':str(exc)})
            # Individual checks below can resolve a failed bulk lookup.
    missing=[rid for rid in ids if not isinstance(client.resources.get(('tracks',rid),{}).get('attributes',{}).get('availability'),list) and rid not in errors]
    absent=set()
    def check_missing(rid):
        # Two bounded read-only workers; each uses its own HTTP opener and cache.
        local=ScannerClient(client.token) if isinstance(client,ScannerClient) else client
        try:
            local.request('/tracks/'+quote(rid,safe='')+'?'+urlencode({'countryCode':'NL','include':'artists,albums'}))
            return rid,local.resources,None
        except ValueError as exc:
            return rid,{},str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(check_missing,rid) for rid in missing]
        for n,future in enumerate(as_completed(futures),1):
            rid,resources,error=future.result()
            client.resources.update(resources)
            if error=='API GET failed (HTTP 404)': absent.add(rid)
            elif error: errors[rid]=error
            if n%100==0:
                print(json.dumps({'missing_ids_checked':n,'total_missing_ids':len(missing)}),flush=True)
    unavailable={}
    uncertain={}
    available=set()
    for rid in ids:
        resource=client.resources.get(('tracks',rid))
        availability=(resource or {}).get('attributes',{}).get('availability')
        if rid in errors:
            uncertain[rid]=errors[rid]
        elif rid in absent:
            unavailable[rid]='HTTP_404_NL'
        elif isinstance(availability,list):
            if 'STREAM' in availability:available.add(rid)
            else:unavailable[rid]='NO_STREAM_NL'
        else: uncertain[rid]='MISSING_AVAILABILITY_METADATA'
    fingerprints={rid:fingerprint(client.resources.get(('tracks',rid)),archived.get(rid),client.resources) for rid in unavailable}
    isrcs=list(dict.fromkeys(f['isrc'] for f in fingerprints.values() if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{3}\d{7}',str(f.get('isrc') or ''))))
    candidates,search_errors={},{}
    for start in range(0,len(isrcs),20):
        batch=isrcs[start:start+20]
        try:
            found=client.tracks('isrc',batch)
            for resource in found:
                code=resource.get('attributes',{}).get('isrc')
                candidates.setdefault(code,{})[resource['id']]=resource
        except ValueError as exc:
            for code in batch:search_errors[code]=str(exc)
    rows=[]
    for position,item in enumerate(items,1):
        rid=item['id']
        if item['type']!='tracks':
            rows.append({'position':position,'old_id':rid,'status':'UNSUPPORTED_MEDIA','type':item['type']})
            continue
        if rid in available:continue
        row={'position':position,'old_id':rid,'item_id':item.get('meta',{}).get('itemId'),'old_url':'https://tidal.com/track/'+rid}
        if rid in uncertain:
            row.update(status='UNCERTAIN',reason=uncertain[rid])
        else:
            old=fingerprints[rid];row.update(fingerprint=old,availability_reason=unavailable[rid])
            if not old.get('isrc') or not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{3}\d{7}',old['isrc']):
                row.update(status='MISSING_FINGERPRINT',candidates=[])
            elif old['isrc'] in search_errors:
                row.update(status='UNCERTAIN_SEARCH',reason=search_errors[old['isrc']],candidates=[])
            else:
                status,matches=assess(old,list(candidates.get(old['isrc'],{}).values()),client.resources)
                row.update(status=status,candidates=matches)
                if status=='CONFIRMED' and row['item_id']:
                    row['replacement_id']=matches[0]['id']
                elif status=='CONFIRMED':
                    row.update(status='REVIEW',reason='Missing occurrence itemId')
        rows.append(row)
    return {'total_occurrences':len(items),'available_occurrences':sum(i['type']=='tracks' and i['id'] in available for i in items),
            'unavailable_occurrences':sum(i['type']=='tracks' and i['id'] in unavailable for i in items),
            'uncertain_occurrences':sum(i['type']=='tracks' and i['id'] in uncertain for i in items),
            'status_counts':dict(Counter(r['status'] for r in rows)), 'bulk_lookup_errors':bulk_errors, 'rows':rows}


def render(report):
    lines=['# Full TIDAL playlist scan','','Checked: '+report['checked_at'],'','Report only. Source playlist mutations: 0.','']
    if report.get('error'):
        return '\n'.join(lines+['Scan aborted: '+report['error'],''])
    summary={k:report[k] for k in ['total_occurrences','available_occurrences','unavailable_occurrences','uncertain_occurrences','status_counts']}
    lines+=['```json',json.dumps(summary,indent=2),'```','','CONFIRMED requires one streaming candidate with identical ISRC, normalized title, exact duration, and an overlapping credited artist. REVIEW and missing-data cases remain unchanged. Transient API errors are uncertainty, not proof of unavailability. Catalogue availability for NL does not verify playback on the user account.','','| Position | Status | Old track | Replacement |','|---:|---|---|---|']
    for row in report['rows']:
        title=row.get('fingerprint',{}).get('title') or row['old_id']
        title=title.replace('|','/').replace('\n',' ')
        replacement='https://tidal.com/track/'+row['replacement_id'] if row.get('replacement_id') else '—'
        lines.append(f"| {row['position']} | {row['status']} | {title} ([{row['old_id']}]({row.get('old_url','')})) | {replacement} |")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('reports/tidal-maintenance/full-playlist-scan.json'))
    args=parser.parse_args()
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'country':'NL','source_playlist_mutations':0}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        client=ScannerClient(access_token())
        known_ids={'283191456','283191455'}
        if {r['id'] for r in client.tracks('id',sorted(known_ids))} != known_ids:
            raise ValueError('Bulk track-ID preflight did not return both known resources')
        if not known_ids.issubset({r['id'] for r in client.tracks('isrc',['GBYDS2000298','GBYDS2000299'])}):
            raise ValueError('Bulk ISRC preflight did not return both known resources')
        print('Bulk ID and ISRC preflight passed.',flush=True)
        snapshot=client.snapshot(PLAYLIST)
        report['playlist']=snapshot['playlist']
        expected=snapshot['playlist'].get('attributes',{}).get('numberOfItems')
        if expected is not None and len(snapshot['items'])!=expected:
            raise ValueError('Snapshot count differs from playlist metadata')
        with Path('side materials/Music collection/Best Classical.csv').open(encoding='utf-8-sig',newline='') as f:
            archived={r['trackId']:r for r in csv.DictReader(f)}
        report.update(scan(client,snapshot,archived))
        # Verify source did not change while checking resources and searching replacements.
        after=client.request('/playlists/'+PLAYLIST+'?countryCode=NL')['data']
        if after.get('attributes',{}).get('lastModifiedAt')!=snapshot['playlist']['attributes']['lastModifiedAt']:
            raise ValueError('Playlist changed during scan; report must not be applied')
        report['source_unchanged']=True
        print(json.dumps({k:v for k,v in report.items() if k not in {'rows','playlist'}},ensure_ascii=False))
        return 0
    except (ValueError,KeyError,TypeError) as exc:
        report['error']=str(exc)
        print('Full playlist scan failed: '+str(exc),file=sys.stderr)
        return 2
    finally:
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        args.output.with_suffix('.md').write_text(render(report))


if __name__=='__main__':
    raise SystemExit(main())
