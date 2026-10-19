#!/usr/bin/env python3
"""Register one earmarked TIDAL album as candidate recording; comparison playlist per already-recommended work.

Default is apply: it writes the proposed ``data/recordings/`` YAML file and, for
works that already have a recommendation, creates a TIDAL comparison playlist
(current recommendation first, then the new candidate). Use ``--dry-run`` to
preview the full YAML and playlist plan without writing anything. The script
never edits GitHub issues and performs no mutating TIDAL calls other than
playlist creation, and only in apply mode.

Matching evidence per track (never guessing): canonical work title or alias
contained in title/version text, or a shared catalogue token (D, BWV, RV, Op,
Hob, Sz, K, ...) with composer evidence from album artists, track artists or
composer credits. Existing recommendations are read from the published
``docs/*.md`` pages (via their TIDAL track anchors), from performances marked
``recommended: true`` and from ``data/recordings/`` entries with status
``recommended``.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ruamel.yaml import YAML

from classical_music.tidal_auth import access_token, user_access_token
from classical_music.tidal_user import Client as UserClient

ALBUM_URL = re.compile(
    r'https://(?:listen\.)?tidal\.com/(?:browse/)?album/([0-9]+)(/u)?$')
COUNTRY = 'NL'
BATCH_SIZE = 50
TRACK_URL = re.compile(r'(?:https?://)?(?:www\.)?tidal\.com/track/([0-9]+)/?$')
DOC_TRACK_LINK = re.compile(
    r'\[[^\]]*\]\(\s*(?:https?://)?(?:www\.)?tidal\.com/track/([0-9]+)/?[^\)]*\)')
CATALOGUE = re.compile(
    r'\b(D|Op|BWV|RV|Hob|KV|K|Sz|AV|TrV|L|S|WWV|MWV|Anh)\.?\s*'
    r'([IVXLC]+[a-z]?)?\s*([0-9]+[a-z]?)(?:\s*:\s*([0-9]+[a-z]?))?',
    re.IGNORECASE)

yaml = YAML()
yaml.default_flow_style = False


def require(condition, message):
    if not condition:
        raise ValueError(message)


def norm(value):
    """Casefold, drop punctuation, collapse whitespace: robust containment matching."""
    value = unicodedata.normalize('NFKD', value or '').casefold()
    value = ''.join(c for c in value if c.isalnum() or c.isspace())
    return re.sub(r'\s+', ' ', value).strip()


def slugify(value, max_length=64):
    value = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', value.casefold()).strip('-')
    require(slug, 'Could not derive a recording ID from the album title')
    return slug[:max_length].strip('-')


def album_id(url):
    """Accept the exact TIDAL album URL forms; fail closed on anything else."""
    match = ALBUM_URL.fullmatch(url.strip()) if isinstance(url, str) else None
    require(match, 'Expected a TIDAL album URL: https://tidal.com/browse/album/<id> '
                   '(or https://tidal.com/album/<id>, optionally with the /u share suffix)')
    return match.group(1)


def album_url(identifier):
    return f'https://tidal.com/browse/album/{identifier}'


def catalogue_tokens(text):
    """Stable catalogue identifiers in a text: D. 940 -> d940, Hob. Ia:7 -> hobia7."""
    tokens = set()
    for match in CATALOGUE.finditer(text or ''):
        prefix, section, number, sub = match.groups()
        token = prefix.casefold() + (section or '').casefold() + number.casefold()
        if sub:
            token += ':' + sub.casefold()
        tokens.add(token)
    return tokens


class CatalogClient(UserClient):
    """GET-only catalogue client restricted to one album and its related catalogue reads."""

    def __init__(self, token, album):
        super().__init__(token)
        self.album = album

    def request(self, path, method='GET', body=None, *, idempotency_key=None):
        require(method == 'GET', 'The album fetcher cannot make write requests')
        require(not body and not idempotency_key, 'The album fetcher cannot carry a request body')
        if path.startswith('https://'):
            parsed = urlsplit(path)
            require(parsed.scheme == 'https' and parsed.netloc == 'openapi.tidal.com', 'Unexpected album URL host')
            path = parsed.path
        require(path.startswith('/v2/albums/' + self.album) or
                (path.startswith('/v2/artists?') and 'filter[id]' in path),
                'Unexpected catalogue request path')
        # The shared wrapper already prefixes its base URL with /v2, so the
        # /v2-prefixed catalogue path must not be passed through verbatim.
        return super().request(path.removeprefix('/v2'), 'GET')

    def try_request(self, path):
        """Return the document, or None when the endpoint answers HTTP 404."""
        try:
            return self.request(path)
        except ValueError as exc:
            if 'HTTP 404' in str(exc):
                return None
            raise


def album_document(client, identifier):
    # The album document itself accepts no include parameter; artists are read
    # separately via the documented artists relationship endpoint.
    document = client.request(f'/v2/albums/{identifier}?countryCode={COUNTRY}')
    data = document.get('data')
    require(isinstance(data, dict) and data.get('id') == identifier and data.get('type') == 'albums',
            'Album response does not identify the requested album')
    attributes = data.get('attributes') or {}
    title = attributes.get('title')
    require(isinstance(title, str) and title.strip(), 'Album response has no title')
    release = attributes.get('releaseDate')
    year = int(str(release)[:4]) if re.match(r'\d{4}', str(release or '')) else None
    artist_ids = [row.get('id') for row in (data.get('relationships', {}).get('artists', {}).get('data') or [])]
    return {'id': identifier, 'title': title.strip(), 'year': year,
            'label': attributes.get('copyright') or None, 'artists': artist_names(client, identifier, artist_ids)}


def artist_names(client, identifier, artist_ids):
    """Album artists via the artists relationship, with a catalogue filter fallback."""
    artist_ids = [aid for aid in artist_ids if isinstance(aid, str) and aid]
    if not artist_ids:
        return []
    document = client.try_request(
        f'/v2/albums/{identifier}/relationships/artists?countryCode={COUNTRY}&include=artists')
    if document is not None:
        included = {(r.get('type'), r.get('id')): r for r in document.get('included', []) if isinstance(r, dict)}
        names = []
        for aid in artist_ids:
            name = (included.get(('artists', aid)) or {}).get('attributes', {}).get('name')
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
        if names:
            return names
    document = client.try_request('/v2/artists?' +
                                  urlencode({'countryCode': COUNTRY, 'filter[id]': ','.join(artist_ids)}))
    require(document is not None, 'Album artists are unavailable through both catalogue routes')
    names = {}
    for row in document.get('data') or []:
        if isinstance(row, dict) and row.get('type') == 'artists':
            name = (row.get('attributes') or {}).get('name')
            if isinstance(name, str) and name.strip():
                names[str(row.get('id'))] = name.strip()
    return [names[aid] for aid in artist_ids if aid in names]


def _track_row(row, included):
    """Collect title, version, artist names and credit names (role -> names) for one item."""
    track_id = row.get('id')
    merged = included.get(('tracks', track_id)) or {}
    attributes = dict(row.get('attributes') or {})
    attributes.update(merged.get('attributes') or {})
    title = attributes.get('title')
    require(isinstance(title, str) and title.strip(), f'Album item {track_id} has no title')
    version = attributes.get('version')
    names = []
    for link in ((row.get('relationships') or {}).get('artists', {}).get('data') or
                 (merged.get('relationships') or {}).get('artists', {}).get('data') or []):
        resource = included.get(('artists', link.get('id')))
        name = (resource or {}).get('attributes', {}).get('name')
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
    credits = {}
    for link in ((row.get('relationships') or {}).get('credits', {}).get('data') or
                 (merged.get('relationships') or {}).get('credits', {}).get('data') or []):
        resource = included.get(('credits', link.get('id'))) or {}
        credit = resource.get('attributes') or {}
        role = credit.get('type') or credit.get('role')
        name = credit.get('name') or credit.get('artist')
        if isinstance(role, str) and isinstance(name, str) and name.strip():
            credits.setdefault(role.strip(), []).append(name.strip())
    return {'id': str(track_id), 'title': title.strip(),
            'version': version.strip() if isinstance(version, str) and version.strip() else None,
            'artists': names, 'credits': credits}


ITEMS_INCLUDES = ('items,items.artists,items.credits', 'items,items.artists')


def album_tracks(client, identifier):
    """Follow bounded album item pages; collect track resources with artists and credits."""
    base = f'/v2/albums/{identifier}/relationships/items'
    for include in ITEMS_INCLUDES:
        document = client.try_request(f'{base}?countryCode={COUNTRY}&include={include}')
        if document is not None:
            return _collect_items(client, base, document, include)
    raise ValueError('Album items are unavailable with the documented include combinations')


def _collect_items(client, base, document, include):
    tracks, seen = [], set()
    for _ in range(50):
        page = document.get('data')
        require(isinstance(page, list), 'Invalid album items response')
        included = {(r.get('type'), r.get('id')): r for r in document.get('included', []) if isinstance(r, dict)}
        for row in page:
            require(isinstance(row, dict) and row.get('type') == 'tracks', 'Unexpected non-track album item')
            tracks.append(_track_row(row, included))
        following = document.get('links', {}).get('next')
        if isinstance(following, dict):
            following = following.get('href')
        if not following:
            require(tracks, 'Album has no tracks')
            return tracks
        require(following not in seen, 'Repeated album pagination link')
        seen.add(following)
        following_path = urlsplit(following)
        require(following_path.netloc == 'openapi.tidal.com' and
                (following_path.path == base or following_path.path == base.removeprefix('/v2')),
                'Unexpected album pagination target')
        query = dict(parse_qsl(following_path.query))
        query.setdefault('countryCode', COUNTRY)
        query['include'] = include
        document = client.request(f'{base}?{urlencode(query)}')
    raise ValueError('Album pagination limit exceeded')


def read_yaml(path):
    return yaml.load(Path(path).read_text(encoding='utf-8'))


def load_works(root):
    """Canonical works: id, title, aliases and composer_id."""
    works = []
    for path in sorted((Path(root) / 'data/works').glob('*.yaml')):
        data = read_yaml(path)
        if not isinstance(data, dict):
            continue
        wid, title = data.get('id'), data.get('title')
        if not wid or not title:
            continue
        aliases = [a for a in (data.get('aliases') or []) if isinstance(a, str)]
        works.append({'id': wid, 'title': title, 'aliases': aliases, 'composer_id': data.get('composer_id')})
    return works


def load_persons(root):
    """Composer/person names keyed by canonical person ID."""
    persons = {}
    for path in sorted((Path(root) / 'data/persons').glob('*.yaml')):
        data = read_yaml(path)
        if isinstance(data, dict) and data.get('id') and data.get('name'):
            persons[data['id']] = data['name']
    return persons


def load_performers(root):
    """Canonical performing artists: id -> (canonical_name, role)."""
    performers = {}
    for path in sorted((Path(root) / 'data/artists').glob('*.yaml')):
        data = read_yaml(path)
        for entry in (data.get('artists') or []) if isinstance(data, dict) else []:
            if isinstance(entry, dict) and entry.get('id') and entry.get('canonical_name'):
                role = entry.get('type')
                performers[entry['id']] = (entry['canonical_name'], role)
    return performers


def role_for(artist_type):
    return {'conductor': 'conductor', 'orchestra': 'orchestra', 'choir': 'choir',
            'soloist': 'soloists', 'singer': 'soloists', 'ensemble': 'orchestra'}.get(artist_type, 'artists')


def track_id_from_url(url):
    match = TRACK_URL.fullmatch((url or '').strip())
    return match.group(1) if match else None


def tidal_track_of(data):
    """Safely read links.tidal.url from a hand-maintained document."""
    links = data.get('links') if isinstance(data, dict) else None
    tidal = links.get('tidal') if isinstance(links, dict) else None
    url = tidal.get('url') if isinstance(tidal, dict) else None
    return track_id_from_url(url)


def composer_evidence(track, album_artists, persons, album_title=''):
    """Canonical composer IDs suggested by names around the track, or by the
    album title (family-name token, e.g. "Schubert: Four Hands")."""
    names = list(album_artists) + list(track['artists'])
    for role_names in track.get('credits', {}).values():
        names.extend(role_names)
    normalized = {norm(name) for name in names}
    evidence = {pid for pid, name in persons.items() if norm(name) in normalized}
    title_tokens = set(norm(album_title or '').split())
    for pid, name in persons.items():
        family = norm(name).split()[-1] if norm(name).split() else ''
        if family and len(family) > 3 and family in title_tokens:
            evidence.add(pid)
    return evidence


def work_matches(track, work, composers):
    """Match evidence: title/alias containment, or a shared catalogue token."""
    if work['composer_id'] not in composers:
        return False
    text = ' '.join(filter(None, [track['title'], track['version']]))
    normalized = norm(text)
    if norm(work['title']) in normalized or any(norm(a) in normalized for a in work['aliases']):
        return True
    return bool(catalogue_tokens(text) & (catalogue_tokens(work['title']) |
                                          {token for alias in work['aliases'] for token in catalogue_tokens(alias)}))


def match_works(tracks, works, persons, album_artists, album_title=''):
    """Map every track to exactly one canonical work, or mark it ambiguous/unknown."""
    matches = []
    for position, track in enumerate(tracks, 1):
        composers = composer_evidence(track, album_artists, persons, album_title)
        hits = [w for w in works if work_matches(track, w, composers)]
        entry = {'track': track, 'position': position, 'work': None, 'state': 'unknown',
                 'composers': composers}
        if len(hits) == 1:
            entry.update(work=hits[0], state='matched')
        elif hits:
            entry.update(state='ambiguous', candidates=sorted(h['id'] for h in hits))
        matches.append(entry)
    return matches


def assign_artists(tracks, album_artists, performers):
    """Map performer names to canonical IDs by exact normalized name; keep the rest as raw text."""
    roles = {}
    unmatched = []
    seen = set()
    for name in list(album_artists) + [n for track in tracks for n in track['artists']]:
        if name in seen:
            continue
        seen.add(name)
        hits = [pid for pid, (canonical, _role) in performers.items() if norm(canonical) == norm(name)]
        if len(hits) == 1:
            roles.setdefault(role_for(performers[hits[0]][1]), []).append(hits[0])
        else:
            unmatched.append(name)
    return roles, unmatched


def build_recording(root, album, matches, roles, unmatched_artists, today, recording_id=None):
    """Assemble the recording document: candidates per work, unevaluated entries otherwise."""
    works = []
    for entry in matches:
        if entry['state'] != 'matched':
            continue
        work = entry['work']
        if works and works[-1]['work_id'] == work['id']:
            works[-1]['tracks'].append(entry)
            continue
        works.append({'work_id': work['id'], 'tracks': [entry]})
    entries = []
    for work in works:
        first = work['tracks'][0]
        entry = {'work_id': work['work_id'], 'status': 'candidate',
                 'track': {'number': first['position'], 'title': first['track']['title']}}
        if len(work['tracks']) > 1:
            entry['notes'] = ('Spans album tracks ' +
                              ', '.join(str(t['position']) for t in work['tracks']) + '.')
        entries.append(entry)
    ambiguous, unknown = [], []
    for entry in matches:
        if entry['state'] == 'ambiguous':
            for wid in entry['candidates']:
                entries.append({'work_id': wid,
                                'track': {'number': entry['position'], 'title': entry['track']['title']},
                                'notes': 'Unmatched (ambiguous track): no status assigned.'})
            ambiguous.append(entry)
        elif entry['state'] == 'unknown':
            unknown.append(entry)
    recording = {'id': recording_id or slugify(album['title']),
                 'title': album['title'], 'label': album['label'], 'year': album['year'],
                 'artists': roles or None, 'works': entries,
                 'links': {'tidal': {'url': album_url(album['id']),
                                     'status': 'active', 'last_checked': today}}}
    notes = []
    if unmatched_artists:
        notes.append('Unmatched artists: ' + ', '.join(unmatched_artists))
    if unknown:
        notes.append('Unmatched tracks without canonical work: ' +
                     ', '.join(f"{e['position']}. {e['track']['title']}" for e in unknown))
    if notes:
        recording['notes'] = ' | '.join(notes)
    unmatched = [{'track': e['track'], 'state': e['state'], 'candidates': e.get('candidates', [])}
                 for e in ambiguous + unknown]
    return recording, unmatched


def unmatched_track_details(matches, persons):
    """Per unmatched track: title, version, catalogue tokens and composer evidence.

    This is evidence for the curator, not a match: the tokens and composer names
    show which ``data/works/`` definitions are missing; no canonical IDs are
    invented here.
    """
    details = []
    for entry in matches:
        if entry['state'] == 'matched':
            continue
        track = entry['track']
        text = ' '.join(filter(None, [track['title'], track['version']]))
        details.append({'position': entry['position'], 'title': track['title'],
                        'version': track['version'],
                        'catalogue_tokens': sorted(catalogue_tokens(text)),
                        'composers': sorted(persons.get(pid, pid) for pid in entry['composers']),
                        'state': entry['state'],
                        'candidates': entry.get('candidates', [])})
    return details


def performance_track_index(root):
    """TIDAL track ID -> work_id from canonical performances."""
    index = {}
    for path in sorted((Path(root) / 'data/performances').glob('*.yaml')):
        data = read_yaml(path)
        if not isinstance(data, dict):
            continue
        track = tidal_track_of(data)
        wid = data.get('work_id')
        if track and wid:
            index[track] = wid
    return index


def doc_recommendations(root, works, performance_index):
    """Published recommendations from docs/*.md: TIDAL track anchors with work attribution."""
    recommendations, unattributed = {}, []
    for path in sorted((Path(root) / 'docs').glob('*.md')):
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            for track in DOC_TRACK_LINK.findall(line):
                wid = performance_index.get(track)
                if not wid:
                    hits = [w['id'] for w in works if catalogue_tokens(line) & (
                        catalogue_tokens(w['title']) | {t for a in w['aliases'] for t in catalogue_tokens(a)})]
                    wid = hits[0] if len(hits) == 1 else None
                if not wid:
                    unattributed.append(f'{path.name}:{number} (track {track})')
                    continue
                entry = recommendations.setdefault(wid, {'track_ids': [], 'sources': []})
                if track not in entry['track_ids']:
                    entry['track_ids'].append(track)
                entry['sources'].append(f'{path.name}:{number}')
    return recommendations, unattributed


def existing_recommendations(root, works=None):
    """work_id -> {'track_ids': [...], 'sources': [...]} for every current recommendation."""
    found = {}
    works = works if works is not None else load_works(root)

    def add(wid, track, source):
        require(wid, f'{source} is recommended without a work_id')
        entry = found.setdefault(wid, {'track_ids': [], 'sources': []})
        if track and track not in entry['track_ids']:
            entry['track_ids'].append(track)
        entry['sources'].append(source)

    for path in sorted((Path(root) / 'data/performances').glob('*.yaml')):
        data = read_yaml(path)
        if not isinstance(data, dict) or data.get('recommended') is not True:
            continue
        track = tidal_track_of(data)
        add(data.get('work_id'), track, path.name)
    for path in sorted((Path(root) / 'data/recordings').glob('*.y*ml')):
        if path.name == 'README.md':
            continue
        data = read_yaml(path)
        if not isinstance(data, dict):
            continue
        for entry in data.get('works') or []:
            if not isinstance(entry, dict) or entry.get('status') != 'recommended':
                continue
            link = (entry.get('links') or {}).get('tidal') if isinstance(entry.get('links'), dict) else None
            if not isinstance(link, dict):
                link = (data.get('links') or {}).get('tidal') if isinstance(data.get('links'), dict) else None
            add(entry.get('work_id'),
                track_id_from_url(link.get('url') if isinstance(link, dict) else None), path.name)
    doc_found, unattributed = doc_recommendations(root, works, performance_track_index(root))
    for wid, entry in doc_found.items():
        target = found.setdefault(wid, {'track_ids': [], 'sources': []})
        for track in entry['track_ids']:
            if track not in target['track_ids']:
                target['track_ids'].append(track)
        target['sources'].extend(entry['sources'])
    return found, unattributed


def playlist_plan(root, album, recording, matches, recommendations, today):
    """One comparison playlist per matched work that already has a recommendation."""
    plans = []
    for entry in recording['works']:
        wid = entry['work_id']
        if wid not in recommendations or entry.get('status') != 'candidate':
            continue
        current = recommendations[wid]
        candidate_ids = [m['track']['id'] for m in matches
                         if m['state'] == 'matched' and m['work']['id'] == wid]
        require(candidate_ids, f'Work {wid} matched without candidate tracks')
        name = f"Earmarked {today} — {wid} — {album['title']}"[:100]
        plans.append({'work_id': wid, 'name': name,
                      'description': f"Candidate comparison for {album_url(album['id'])} "
                                      f"(current recommendation: {', '.join(current['sources'])})",
                      'current_track_ids': current['track_ids'], 'candidate_track_ids': candidate_ids,
                      'current_sources': current['sources']})
    return plans


def provision_playlist(client, plan):
    """Create one comparison playlist: current recommendation first, then the candidate."""
    expected = plan['current_track_ids'] + plan['candidate_track_ids']
    created = client.request('/playlists', 'POST', {'data': {'type': 'playlists', 'attributes': {
        'name': plan['name'], 'description': plan['description'], 'accessType': 'UNLISTED'}}})
    pid = created['data']['id']
    require(re.fullmatch(r'[0-9a-f-]{36}', str(pid)), 'Invalid playlist ID returned by create')
    for offset in range(0, len(expected), BATCH_SIZE):
        client.request(f'/playlists/{pid}/relationships/items', 'POST', {
            'data': [{'type': 'tracks', 'id': tid} for tid in expected[offset:offset + BATCH_SIZE]],
            'meta': {'onDuplicates': 'ADD'}})
    snapshot = client.snapshot(pid)
    live = [str(item['id']) for item in snapshot['items']]
    require(live == expected, 'Comparison playlist does not match the plan; inspect it in TIDAL')
    return f'https://tidal.com/playlist/{pid}'


def recording_path(root, recording):
    return Path(root) / 'data/recordings' / (recording['id'] + '.yml')


def write_recording(root, recording, *, update_existing=False):
    path = recording_path(root, recording)
    if path.exists() and not update_existing:
        raise ValueError(f'Recording ID already exists: {path.name}; use --update-existing to extend it, '
                         'or pass --recording-id with a new unique slug')
    document = {key: value for key, value in recording.items() if value is not None}
    if path.exists() and update_existing:
        existing = read_yaml(path)
        if not isinstance(existing, dict):
            raise ValueError(f'Existing recording file is not a mapping: {path.name}')
        if (existing.get('links', {}).get('tidal', {}).get('url')
                != recording['links']['tidal']['url']):
            raise ValueError(f'{path.name} belongs to another album; refusing to merge')
        known = {entry.get('work_id') for entry in existing.get('works') or []}
        existing['works'] = list(existing.get('works') or [])
        for entry in document['works']:
            if entry['work_id'] not in known:
                existing['works'].append(entry)
        existing['links'] = recording['links']
        document = existing
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        yaml.dump(document, handle)
    return path


def run(root, url, *, dry_run=False, recording_id=None, update_existing=False,
        read_client=None, user_client_factory=None, today=None):
    from datetime import date
    today = today or date.today().isoformat()
    identifier = album_id(url)
    root = Path(root)
    works, persons, performers = load_works(root), load_persons(root), load_performers(root)
    require(works and persons, 'Canonical data is missing or empty; refusing to guess')
    client = read_client or CatalogClient(access_token(), identifier)
    album = album_document(client, identifier)
    tracks = album_tracks(client, identifier)
    matches = match_works(tracks, works, persons, album['artists'], album.get('title', ''))
    roles, unmatched_artists = assign_artists(tracks, album['artists'], performers)
    recording, unmatched_tracks = build_recording(root, album, matches, roles, unmatched_artists, today, recording_id)
    if not recording['works'] and not dry_run:
        raise ValueError('No track could be related to canonical works; refusing to write anything. '
                         'Re-run with --dry-run for the per-track report of missing work definitions.')
    recommendations, unattributed = existing_recommendations(root, works)
    plans = [p for p in playlist_plan(root, album, recording, matches, recommendations, today)
             if p['current_track_ids']]
    work_lines = []
    for entry in recording['works']:
        if entry.get('status') == 'candidate':
            if entry['work_id'] in {p['work_id'] for p in plans}:
                action = ('candidate; comparison playlist planned (existing recommendation: '
                          + ', '.join(next(p['current_sources'] for p in plans
                                           if p['work_id'] == entry['work_id'])) + ')')
            elif entry['work_id'] in recommendations:
                action = ('candidate; existing recommendation has no TIDAL track anchor, '
                          'no comparison playlist')
            else:
                action = 'candidate; no existing recommendation, no playlist'
        else:
            action = 'unevaluated work entry (no status); see notes'
        work_lines.append({'work_id': entry['work_id'], 'action': action})
    report = {'album': f"{album['title']} ({album_url(identifier)})",
              'recording_id': recording['id'],
              'works': work_lines,
              'playlist_plans': [{'work_id': p['work_id'], 'name': p['name'],
                                  'current_tracks': p['current_track_ids'],
                                  'candidate_tracks': p['candidate_track_ids']} for p in plans],
              'unmatched_tracks': [{'title': u['track']['title'], 'state': u['state'],
                                    'candidates': u.get('candidates', [])} for u in unmatched_tracks],
              'unmatched_track_details': unmatched_track_details(matches, persons),
              'unmatched_artists': unmatched_artists,
              'unattributed_recommendation_lines': unattributed}
    output = {'recording': recording, 'report': report, 'dry_run': dry_run}
    if dry_run:
        output['note'] = ('Dry run: nothing written, no playlist created. '
                          'Re-run without --dry-run to apply.')
        if not recording['works']:
            output['note'] = ('Dry run: no track could be related to canonical works; nothing to '
                              'register yet. See the per-track report above for the missing work '
                              'definitions; add the works under data/works/, then re-run.')
        return output
    written = write_recording(root, recording, update_existing=update_existing)
    created = []
    if plans:
        factory = user_client_factory or (lambda: UserClient(user_access_token()))
        user_client = factory()
        for plan in plans:
            created.append({'work_id': plan['work_id'], 'url': provision_playlist(user_client, plan)})
    output['written'] = str(written.relative_to(root))
    output['playlists'] = created
    for entry in output['report']['playlist_plans']:
        entry['playlist_url'] = next(p['url'] for p in created if p['work_id'] == entry['work_id'])
    return output


def dump_yaml(recording):
    """Render the proposed recording document exactly as it would be written."""
    import io
    document = {key: value for key, value in recording.items() if value is not None}
    handle = io.StringIO()
    yaml.dump(document, handle)
    return handle.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('album_url', help='TIDAL album URL, e.g. https://tidal.com/browse/album/<id> '
                                          '(or tidal.com/album/<id>, optionally with /u)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show the proposed recording YAML and playlist plan without writing anything')
    parser.add_argument('--recording-id', help='Override the derived recording ID slug')
    parser.add_argument('--update-existing', action='store_true',
                        help='Allow extending an existing recording file for the same album URL')
    args = parser.parse_args(argv)
    try:
        result = run(ROOT, args.album_url, dry_run=args.dry_run,
                     recording_id=args.recording_id, update_existing=args.update_existing)
    except ValueError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    report = result['report']
    print(f"Album: {report['album']}")
    print(f"Recording ID: {report['recording_id']}")
    for entry in report['works']:
        print(f"  {entry['work_id']}: {entry['action']}")
    for entry in report.get('playlist_plans', []):
        line = f"  {entry['work_id']}: comparison playlist"
        if entry.get('playlist_url'):
            line += f" {entry['playlist_url']}"
        else:
            line += (f" planned (current {len(entry['current_tracks'])} track(s), "
                     f"candidate {len(entry['candidate_tracks'])} track(s))")
        print(line)
    for entry in report['unmatched_tracks']:
        detail = f" [{', '.join(entry['candidates'])}]" if entry['candidates'] else ''
        print(f"  UNMATCHED ({entry['state']}): {entry['title']}{detail}")
    if report['unmatched_artists']:
        print('  Unmatched artists (raw text in notes): ' + ', '.join(report['unmatched_artists']))
    if not report['works'] and report.get('unmatched_track_details'):
        print('  No track could be related to canonical works; per-track report:')
        for entry in report['unmatched_track_details']:
            version = f" (version: {entry['version']})" if entry['version'] else ''
            tokens = ', '.join(entry['catalogue_tokens']) or 'none'
            composers = ', '.join(entry['composers']) or 'no composer evidence found'
            print(f"    {entry['position']}. {entry['title']}{version}")
            print(f"       catalogue tokens: {tokens}; composer evidence: {composers}")
    if report['unattributed_recommendation_lines']:
        print('  Recommendation lines without a canonical work attribution: '
              + ', '.join(report['unattributed_recommendation_lines']))
    if result['dry_run']:
        print('--- Proposed data/recordings YAML ---')
        print(dump_yaml(result['recording']), end='')
        print('--- End of proposed YAML ---')
        print(result['note'])
    if result.get('written'):
        print(f"Written: {result['written']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())


