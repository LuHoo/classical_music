#!/usr/bin/env python3
"""Register one earmarked TIDAL album as candidate recording; comparison playlist per already-recommended work.

Default is apply: it writes the proposed ``data/recordings/`` YAML file and, for
works that already have a recommendation, creates a TIDAL comparison playlist
(current recommendation first — as its complete recording, every track of the
anchor album matched to the same work — then the new candidate). Use ``--dry-run``
to preview the full YAML and playlist plan without writing anything. The script
never edits GitHub issues and performs no mutating TIDAL calls other than
playlist creation, and only in apply mode.

Playlists are only created with ``--issue <nr> --work <work-id>`` (one run per
curator comparison issue); they are named ``Curator <date> Issue #<nr>``.

With --canonize, tracks without a canonical work are canonized as part of the
registration (#327): a new ``data/works/`` definition is written when the ISRC
chain (ISRC -> MusicBrainz recording -> work, advisory) yields exactly one
work whose composer is the unique canonical person evidenced around the track.
Without --canonize such proposals stay advisory in the report.

Matching evidence per track (never guessing): canonical work title or alias
contained in title/version text, or a shared catalogue token (D, BWV, RV, Op,
Hob, Sz, K, ...) with composer evidence from album artists, track artists or
composer credits. Variant takes marked 'with ... from <catalogue>' in a parenthetical
(e.g. 'II. Largo (with original ornamentation from RV 581)', #350) are skipped
entirely: never a candidate, binding or playlist track; they are reported as
SKIPPED VARIANT. Existing recommendations are read from the published
``docs/*.md`` pages (via their TIDAL track anchors), from performances marked
``recommended: true`` and from ``data/recordings/`` entries with status
``recommended``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

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
    r'\b(D|Op|BWV|RV|Hob|KV|K|Sz|AV|TrV|L|S|M|WWV|MWV|Anh)\.?\s*'
    r'([IVXLC]+[a-z]?)?\s*([0-9]+[a-z]?)(?:\s*:\s*([0-9]+[a-z]?))?',
    re.IGNORECASE)

MUSICBRAINZ_WORK = 'https://musicbrainz.org/ws/2/work'
MUSICBRAINZ_RECORDING = 'https://musicbrainz.org/ws/2/recording'
MAX_SUGGESTION_BYTES = 400_000
SUGGESTION_HEADERS = {
    'User-Agent': 'LuHoo/classical_music register_earmarked_recording (curator tool; '
                  'read-only MusicBrainz work lookups)'}

yaml = YAML()
yaml.default_flow_style = False


def require(condition, message):
    if not condition:
        raise ValueError(message)


class NoSuggestionRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('MusicBrainz endpoint redirected; request refused')


def suggestion_search_text(title):
    """Work-level search text for external lookups: drop movement numbers and
    parenthesized arrangement notes, keep the work title itself."""
    text = re.sub(r'\([^)]*\)', ' ', title or '')
    text = text.split(':')[0]
    text = re.sub(r'\s+', ' ', text).strip(' ,.-')
    return text or (title or '').strip()


def attach_external_suggestions(report, *, suggest_client=None):
    """Fill advisory MusicBrainz suggestions into the per-track report of a
    zero-match album. Fail-open: lookups never block the dry-run, and the
    suggestions never touch the recording document."""
    suggest = suggest_client if suggest_client is not None else SuggestionClient()
    seen = {}
    for entry in report['unmatched_track_details']:
        # The version attribute usually carries the work title when the track
        # title is a bare movement; search the work-level text.
        text = suggestion_search_text(entry['version'] or entry['title'])
        if text not in seen:
            try:
                seen[text] = suggest.work_suggestions(text)
            except (ValueError, OSError):
                seen[text] = None
        entry['external_suggestions'] = seen[text]
        # ISRC-chain work evidence (#327): advisory, per track, fail-open.
        if entry.get('isrc'):
            try:
                entry['isrc_work_suggestions'] = suggest.recording_work_suggestions(entry['isrc'])
            except (ValueError, OSError):
                entry['isrc_work_suggestions'] = None
    report['external_suggestions_unavailable'] = any(value is None for value in seen.values())
    return report


class SuggestionClient:
    """Read-only MusicBrainz work lookups for the zero-match dry-run report.

    Advisory evidence only: suggestions appear in the report and never in the
    recording document, and they never create or determine canonical identities
    (identifier policy: external identifiers are evidence, not identity).
    Anonymous MusicBrainz access is paced to one request per second.
    """

    def __init__(self, timeout=20, min_interval=1.0):
        self.timeout = timeout
        self.min_interval = min_interval
        self._last_request = None

    def fetch(self, url, _attempt=0, _max_attempts=3):
        if self._last_request is not None:
            waited = time.monotonic() - self._last_request
            if waited < self.min_interval:
                time.sleep(self.min_interval - waited)
        request = Request(url, headers=dict(SUGGESTION_HEADERS))
        try:
            with build_opener(NoSuggestionRedirects()).open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_SUGGESTION_BYTES + 1)
                if len(raw) > MAX_SUGGESTION_BYTES:
                    raise ValueError('Oversized MusicBrainz response')
        except HTTPError as exc:
            # MusicBrainz answers 429/503 under load; paced exponential backoff,
            # then fail (fail-open: the dry-run report simply continues without
            # suggestions for this search text).
            if exc.code in (429, 503) and _attempt + 1 < _max_attempts:
                time.sleep(2 * (2 ** _attempt))
                return self.fetch(url, _attempt=_attempt + 1, _max_attempts=_max_attempts)
            raise ValueError(f'MusicBrainz lookup failed (HTTP {exc.code})') from None
        finally:
            self._last_request = time.monotonic()
        try:
            return json.loads(raw)
        except (UnicodeError, json.JSONDecodeError):
            raise ValueError('Invalid MusicBrainz response') from None

    def work_detail(self, work_id):
        """Composer and Wikidata relations of one MusicBrainz work (advisory
        evidence; external identifiers are evidence, not identity)."""
        detail = self.fetch(
            f'{MUSICBRAINZ_WORK}/{work_id}?inc=artist-rels+url-rels&fmt=json')
        composers = [{'name': (rel.get('artist') or {}).get('name'),
                      'musicbrainz_artist_id': (rel.get('artist') or {}).get('id')}
                     for rel in (detail.get('relations') or [])
                     if rel.get('type') == 'composer' and (rel.get('artist') or {}).get('name')]
        wikidata = None
        for rel in detail.get('relations') or []:
            if rel.get('type') == 'wikidata':
                resource = ((rel.get('url') or {}).get('resource') or '')
                if resource.startswith(('http://www.wikidata.org/entity/',
                                         'https://www.wikidata.org/entity/')):
                    wikidata = resource
        return {'composers': composers, 'wikidata_url': wikidata}

    def work_suggestions(self, text, limit=3):
        """Up to `limit` MusicBrainz works matching the work text, with composer
        relations where the work states them. Exact title matches rank first."""
        query = urlencode({'query': f'work:"{text}"', 'fmt': 'json', 'limit': 5})
        document = self.fetch(f'{MUSICBRAINZ_WORK}?{query}')
        candidates = [work for work in (document.get('works') or [])
                      if isinstance(work, dict) and work.get('id') and work.get('title')]
        target = norm(text)

        def rank(work):
            title = norm(work['title'])
            if title == target:
                return (0, len(title))
            if title in target or target in title:
                return (1, len(title))
            return (2, len(title))

        suggestions = []
        for work in sorted(candidates, key=rank)[:limit]:
            # Drop movement-level duplicates: MusicBrainz lists both the work
            # ("Prelude, Aria and Finale, op. 25") and its movement parts
            # ("... op. 25: III. Finale"); the parts add no new evidence.
            prefix = norm(work['title'].split(':')[0]).strip()
            if any(prefix and (norm(kept['title']) == prefix or norm(kept['title']) in prefix)
                   for kept in suggestions):
                continue
            detail = self.work_detail(work['id'])
            suggestions.append({'title': work['title'],
                                'musicbrainz_work_id': work['id'],
                                'composers': detail['composers'],
                                'wikidata_url': detail['wikidata_url'],
                                'source': 'musicbrainz'})
        return suggestions

    def recording_work_suggestions(self, isrc, limit=3):
        """Work evidence via the ISRC chain (#327): ISRC -> MusicBrainz
        recording -> works. Advisory only; the ISRC identifies a recording,
        never a work — the chain provides evidence, not identity."""
        require(isinstance(isrc, str) and isrc.strip(), 'Expected a non-empty ISRC')
        query = urlencode({'query': f'isrc:{isrc.strip()}', 'fmt': 'json', 'limit': 5})
        document = self.fetch(f'{MUSICBRAINZ_RECORDING}?{query}')
        recording_ids = [rec.get('id') for rec in (document.get('recordings') or [])
                         if isinstance(rec, dict) and rec.get('id')]
        works, seen = [], set()
        for recording_id in recording_ids:
            detail = self.fetch(
                f'{MUSICBRAINZ_RECORDING}/{recording_id}?inc=work-rels&fmt=json')
            for rel in detail.get('relations') or []:
                work = rel.get('work') or {}
                if rel.get('type') != 'work' or not work.get('id') or not work.get('title'):
                    continue
                if work['id'] in seen:
                    continue
                seen.add(work['id'])
                info = self.work_detail(work['id'])
                works.append({'title': work['title'],
                              'musicbrainz_work_id': work['id'],
                              'musicbrainz_recording_id': recording_id,
                              'composers': info['composers'],
                              'wikidata_url': info['wikidata_url'],
                              'source': 'musicbrainz-isrc'})
            if len(works) >= limit:
                break
        return works[:limit]


class NullSuggestionClient:
    """Explicit opt-out: --no-external-lookups keeps the dry-run fully offline."""

    def work_suggestions(self, text, limit=3):
        raise OSError('External lookups disabled')

    def recording_work_suggestions(self, isrc, limit=3):
        raise OSError('External lookups disabled')


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
                path.startswith('/v2/tracks/') or
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
    copyright = attributes.get('copyright')
    # TIDAL may return the copyright as an object ({'text': ...}); the recording
    # schema stores a plain label string.
    if isinstance(copyright, dict):
        copyright = copyright.get('text')
    if not isinstance(copyright, str):
        copyright = None
    return {'id': identifier, 'title': title.strip(), 'year': year,
            'label': copyright.strip() if copyright and copyright.strip() else None,
            'artists': artist_names(client, identifier, artist_ids)}


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
    isrc = attributes.get('isrc')
    return {'id': str(track_id), 'title': title.strip(),
            'version': version.strip() if isinstance(version, str) and version.strip() else None,
            'isrc': isrc.strip() if isinstance(isrc, str) and isrc.strip() else None,
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
        # TIDAL v2 returns the next href either absolute on openapi.tidal.com
        # or relative without scheme, host and /v2 prefix (#340); either form
        # must still point at this album's own items endpoint.
        require(following_path.netloc in ('', 'openapi.tidal.com') and
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
    """Canonical works: id, title, aliases, composer_id and catalogue values.

    The catalogue map (e.g. ``bwv: BWV 1046.2``) is carried as string values:
    published docs lines carry catalogue numbers that often live only in this
    field, not in the work title (#323).
    """
    works = []
    for path in sorted((Path(root) / 'data/works').glob('*.yaml')):
        data = read_yaml(path)
        if not isinstance(data, dict):
            continue
        wid, title = data.get('id'), data.get('title')
        if not wid or not title:
            continue
        aliases = [a for a in (data.get('aliases') or []) if isinstance(a, str)]
        catalogue = data.get('catalogue')
        if isinstance(catalogue, dict):
            catalogue_values = [str(v) for v in catalogue.values() if v is not None]
        elif catalogue:
            catalogue_values = [str(catalogue)]
        else:
            catalogue_values = []
        works.append({'id': wid, 'title': title, 'aliases': aliases,
                      'composer_id': data.get('composer_id'),
                      'catalogue_values': catalogue_values})
    return works


def page_composer_index(docs_dir, persons):
    """docs page name -> canonical person IDs implied by its '# Name' heading.

    Every docs/*.md page is a composer page; the heading is the composer
    evidence for its recommendation lines (#323). Heading matching (#329): the
    heading's family name (last name token) must equal the person's family
    name and, when the heading states given names, at least one given-name
    token must be shared ('Niels Gade' -> 'Niels Wilhelm Gade'). Headings that
    match nobody this strictly fall back to full-name containment. Pages whose
    heading matches no canonical person yield an empty set: fail-closed, the
    attribution then only accepts unambiguous catalogue-token matches.
    """
    index = {}
    for path in sorted(Path(docs_dir).glob('*.md')):
        heading = ''
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.startswith('# '):
                heading = line[2:].strip()
                break
        composers = set()
        if heading:
            heading_tokens = norm(heading).lower().split()
            for pid, name in persons.items():
                person_tokens = norm(name).lower().split()
                if not heading_tokens or not person_tokens:
                    continue
                given = set(heading_tokens[:-1]) & set(person_tokens[:-1])
                if heading_tokens[-1] == person_tokens[-1] and (
                        len(heading_tokens) == 1 or given):
                    composers.add(pid)
            if not composers:
                normalized = norm(heading).lower()
                for pid, name in persons.items():
                    candidate = norm(name).lower()
                    if candidate and (candidate in normalized or normalized in candidate):
                        composers.add(pid)
        index[path.name] = composers
    return index


def work_match_pool(works, composers):
    """Works narrowed by composer evidence; without evidence all works."""
    if not composers:
        return list(works)
    return [w for w in works if w.get('composer_id') in composers]


def work_catalogue_tokens(work):
    """Catalogue tokens of a work: title, aliases and catalogue-field values."""
    tokens = catalogue_tokens(work['title'])
    tokens |= {token for alias in work['aliases'] for token in catalogue_tokens(alias)}
    for value in work.get('catalogue_values') or []:
        tokens |= catalogue_tokens(value)
    return tokens



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


def variant_provenance(text):
    """A parenthetical variant marker naming another work's catalogue number,
    e.g. 'II. Largo (with original ornementation from RV 581)': the track is a
    variant take of one movement carrying material from another work (#350).
    Curator-approved skip: a variant take is not part of the work's canonical
    track sequence. Detection is explicit and conservative -- the parenthesis
    must contain the words 'with' and 'from' plus a catalogue number; movement
    numbers, arrangements and version qualifiers are never guessed at."""
    for paren in re.findall(r'\(([^()]*)\)', text or ''):
        lowered = paren.casefold()
        if (re.search(r'\bwith\b', lowered) and re.search(r'\bfrom\b', lowered)
                and catalogue_tokens(paren)):
            return paren
    return None


def match_works(tracks, works, persons, album_artists, album_title=''):
    """Map every track to exactly one canonical work, or mark it ambiguous/unknown.
    Variant takes (a parenthetical 'with ... from <catalogue>' marker, #350) are
    skipped: state 'variant', never a candidate, binding or playlist track."""
    matches = []
    for position, track in enumerate(tracks, 1):
        variant_text = ' '.join(filter(None, [track['title'], track.get('version')]))
        marker = variant_provenance(variant_text)
        if marker:
            matches.append({'track': track, 'position': position, 'work': None,
                            'state': 'variant', 'variant': marker, 'composers': set()})
            continue
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
    ambiguous, unknown, variants = [], [], []
    for entry in matches:
        if entry['state'] == 'ambiguous':
            for wid in entry['candidates']:
                entries.append({'work_id': wid,
                                'track': {'number': entry['position'], 'title': entry['track']['title']},
                                'notes': 'Unmatched (ambiguous track): no status assigned.'})
            ambiguous.append(entry)
        elif entry['state'] == 'variant':
            variants.append(entry)
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
    if variants:
        notes.append('Skipped variant tracks: ' +
                     ', '.join(f"{e['position']}. {e['track']['title']}" for e in variants))
    if notes:
        recording['notes'] = ' | '.join(notes)
    unmatched = [{'track': e['track'], 'state': e['state'], 'candidates': e.get('candidates', []),
                  'variant': e.get('variant')}
                 for e in ambiguous + unknown + variants]
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
                        'version': track['version'], 'isrc': track.get('isrc'),
                        'catalogue_tokens': sorted(catalogue_tokens(text)),
                        'composers': sorted(persons.get(pid, pid) for pid in entry['composers']),
                        'state': entry['state'],
                        'candidates': entry.get('candidates', [])})
    return details


def catalogue_labels(text):
    """Catalogue map for a proposed work: raw numbers from the track text,
    keyed by normalized prefix (D. 940 -> {'d': 'D. 940'}, BWV 1046.2 -> ...)."""
    labels = {}
    for match in CATALOGUE.finditer(text or ''):
        prefix, section, number, sub = match.groups()
        key = prefix.casefold().rstrip('.')
        labels.setdefault(key, match.group(0).strip())
    return labels


def build_work_proposals(matches, persons, album, suggest_client):
    """Fail-closed canonization proposals for tracks without a canonical work
    (#327): one MusicBrainz work from the ISRC chain, whose composer is the
    unique canonical person evidenced around the track. No proposal when the
    composer is not canonical yet (persons are never invented), when several
    composers remain, or when the chain yields no single-matching work.
    Proposals are drafts for curator approval via --canonize; nothing is
    written without it, and canonical work IDs are always derived slugs."""
    proposals = []
    for entry in matches:
        if entry['state'] != 'unknown':
            continue
        track = entry['track']
        isrc = track.get('isrc')
        composer_ids = entry['composers']
        if not isrc or len(composer_ids) != 1:
            continue
        pid = next(iter(composer_ids))
        name = persons.get(pid)
        if not name:
            continue
        try:
            suggestions = suggest_client.recording_work_suggestions(isrc)
        except (ValueError, OSError):
            continue
        matching = [s for s in suggestions
                    if s.get('composers')
                    and {norm(c['name']) for c in s['composers']} == {norm(name)}]
        if len(matching) != 1:
            continue
        suggestion = matching[0]
        text = ' '.join(filter(None, [track['title'], track['version']]))
        proposal = {'work_id': slugify(f'{name} {suggestion["title"]}', max_length=96),
                    'title': suggestion['title'],
                    'composer_id': pid,
                    'catalogue': catalogue_labels(text) or None,
                    'aliases': [],
                    'evidence': {'isrc': isrc,
                                 'musicbrainz_work_id': suggestion['musicbrainz_work_id'],
                                 'musicbrainz_recording_id': suggestion.get('musicbrainz_recording_id'),
                                 'wikidata_url': suggestion.get('wikidata_url'),
                                 'track_title': track['title'],
                                 'label': album.get('label')}}
        proposals.append(proposal)
    return proposals


def write_work(root, proposal):
    """Write one proposed work definition; refuse to overwrite anything."""
    path = Path(root) / 'data/works' / (proposal['work_id'] + '.yaml')
    require(not path.exists(),
            f'Work file already exists: {path.name}; refusing to overwrite it')
    document = {'id': proposal['work_id']}
    document.update({key: value for key, value in proposal.items()
                     if key not in ('work_id', 'evidence') and value is not None})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        yaml.dump(document, handle)
    return path


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


def containment_hits(pool, text):
    """Works whose title or an alias is contained in the text."""
    normalized = norm(text)
    return [w for w in pool
            if norm(w['title']) in normalized
            or any(norm(alias) in normalized for alias in w['aliases'])]


def most_specific(hits):
    """Drop works whose title lies fully inside another hit's title (#329):
    a generic title contained in a more specific candidate is not evidence
    ('Concerto' inside 'Piano Concerto'). Fail-closed: if every hit would be
    dropped, the original set is returned."""
    if len(hits) > 1:
        specific = [w for w in hits
                    if not any(other is not w
                                and norm(other['title']) != norm(w['title'])
                                and norm(w['title']) in norm(other['title'])
                                for other in hits)]
        if specific:
            return specific
    return hits


VERSION_STOPWORDS = {'version', 'arrangement', 'original', 'revised', 'edition',
                     'for', 'and', 'or', 'the', 'in', 'of', 'with', 'a', 'no'}


def version_qualifier_words(title):
    """Content words a docs line must contain to support a titled version.

    Parenthetical qualifiers in a work title name the version, arrangement or
    instrumentation ('version for cello and orchestra', 'Steuermann piano
    trio arrangement', 'string sextet'). Lowercase content words are required
    evidence; capitalized proper names and generic version words are not."""
    required = set()
    for qualifier in re.findall(r'\(([^()]*)\)', title or ''):
        for word in qualifier.split():
            if word.islower() and word not in VERSION_STOPWORDS:
                required.add(norm(word))
    return required


def qualifier_consistent(hits, text):
    """Version-qualifier consistency (#329): versions are separate canonical
    works and not interchangeable, so among remaining candidates a work is
    dropped when its titled version is contradicted: every required qualifier
    word must appear in the line (or the anchor's own segment). Fail-closed:
    if every candidate is excluded, the original set is returned."""
    if len(hits) <= 1:
        return hits
    words = set(norm(text).split())
    consistent = [w for w in hits if version_qualifier_words(w['title']) <= words]
    return consistent or hits


def doc_recommendations(root, works, performance_index, page_composers=None):
    """Published recommendations from docs/*.md: TIDAL track anchors with work
    attribution, with a per-category breakdown for unattributed lines (#323).

    Attribution order, per anchor (#329): (1) canonical performance with the
    track; (2) a unique catalogue-token match (title, aliases and the work's
    catalogue field) among the composer's works implied by the page heading;
    (3) a unique title/alias containment match in the anchor's own segment of
    the line, then in the whole line. Candidates left ambiguous by (2)/(3) are
    narrowed by most-specific-title and version-qualifier consistency. Lines
    with several anchors attribute each anchor against the text segment that
    introduces it, so versioned recordings on one line (original first, then
    arrangements) get their own evidence. Anything else is unattributed and
    classified as 'no-canonical-work' (no candidate at all) or 'ambiguous-match'
    (several candidates remain).
    """
    recommendations, unattributed = {}, []
    breakdown = {}
    for path in sorted((Path(root) / 'docs').glob('*.md')):
        composers = (page_composers or {}).get(path.name, set())
        pool = work_match_pool(works, composers)
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            anchors = list(DOC_TRACK_LINK.finditer(line))
            line_tokens = catalogue_tokens(line)
            token_hits = [w for w in pool if line_tokens & work_catalogue_tokens(w)]
            line_containment = qualifier_consistent(
                most_specific(containment_hits(pool, line)), line)
            segment_start = 0
            for anchor in anchors:
                track = anchor.group(1)
                # The anchor's evidence segment runs up to and including its
                # own markdown label: '[string sextet: …](url)' carries the
                # version label inside the anchor itself.
                segment = line[segment_start:anchor.end()]
                segment_start = anchor.end()
                wid = performance_index.get(track)
                if not wid:
                    hits = [w['id'] for w in token_hits]
                    if len(hits) != 1:
                        narrowed = qualifier_consistent(token_hits, segment)
                        if len(narrowed) == 1:
                            hits = [narrowed[0]['id']]
                    if len(hits) != 1:
                        segment_hits = qualifier_consistent(
                            most_specific(containment_hits(pool, segment)), segment)
                        if len(segment_hits) == 1:
                            hits = [segment_hits[0]['id']]
                        elif len(hits) != 1:
                            if len(line_containment) == 1:
                                hits = [line_containment[0]['id']]
                    if len(hits) != 1:
                        any_candidate = (token_hits or line_containment
                                        or containment_hits(pool, segment))
                        category = 'no-canonical-work' if not any_candidate else 'ambiguous-match'
                        entry = breakdown.setdefault(category, [])
                        entry.append(f'{path.name}:{number} (track {track})')
                        unattributed.append(f'{path.name}:{number} (track {track})')
                        continue
                    wid = hits[0]
                entry = recommendations.setdefault(wid, {'track_ids': [], 'sources': []})
                if track not in entry['track_ids']:
                    entry['track_ids'].append(track)
                entry['sources'].append(f'{path.name}:{number}')
    ordered = [{'category': category, 'count': len(lines), 'examples': lines[:3]}
               for category, lines in sorted(breakdown.items())]
    return recommendations, unattributed, ordered


def existing_recommendations(root, works=None):
    """work_id -> {'track_ids': [...], 'sources': [...]} for every current
    recommendation; plus unattributed docs lines and their category breakdown."""
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
    doc_found, unattributed, breakdown = doc_recommendations(
        root, works, performance_track_index(root),
        page_composer_index(Path(root) / 'docs', load_persons(root)))
    for wid, entry in doc_found.items():
        target = found.setdefault(wid, {'track_ids': [], 'sources': []})
        for track in entry['track_ids']:
            if track not in target['track_ids']:
                target['track_ids'].append(track)
        target['sources'].extend(entry['sources'])
    return found, unattributed, breakdown


def track_album_id(client, track_id):
    """The unique album behind an existing recommendation's anchor track; fail-closed."""
    document = client.try_request(f'/v2/tracks/{track_id}?countryCode={COUNTRY}&include=albums')
    require(document is not None, f'Track {track_id} is unavailable through the catalogue')
    data = document.get('data')
    require(isinstance(data, dict) and data.get('type') == 'tracks'
            and str(data.get('id')) == str(track_id),
            f'Track response does not identify track {track_id}')
    related = (data.get('relationships') or {}).get('albums', {}).get('data') or []
    ids = [row.get('id') for row in related if isinstance(row, dict) and row.get('id')]
    if not ids:
        ids = [row.get('id') for row in document.get('included', [])
               if isinstance(row, dict) and row.get('type') == 'albums' and row.get('id')]
    require(len(ids) == 1,
            f'Track {track_id} has no unique album; refusing a fragmentary comparison playlist')
    return str(ids[0])


def expand_current_tracks(read_client, catalog_factory, anchor_ids, work, persons):
    """The complete current recording(s) behind the recommendation anchors.

    A docs or performance anchor is a single track; a multi-movement work
    needs its complete recording in a comparison playlist (the issue-bound
    listening playlists already refuse to let one anchor stand in for a
    complete work). The anchor track's album is fetched and every track
    matched to the same canonical work is included, in album order.
    Fail-closed: the anchor itself must match again on its own album,
    otherwise the comparison would silently present a fragment.
    """
    expanded, seen = [], set()
    for anchor in anchor_ids:
        album = track_album_id(read_client, anchor)
        client = catalog_factory(album)
        document = album_document(client, album)
        tracks = album_tracks(client, album)
        matches = match_works(tracks, [work], persons, document['artists'],
                              document.get('title', ''))
        ids = [m['track']['id'] for m in matches
               if m['state'] == 'matched' and m['work']['id'] == work['id']]
        require(anchor in ids,
                f"Anchor track {anchor} does not match {work['id']} on its own album; "
                'refusing a fragmentary comparison playlist')
        for tid in ids:
            if tid not in seen:
                seen.add(tid)
                expanded.append(tid)
    return expanded


def bind_issue(recording, matches, roles, performers, issue, work):
    """Bind one curator comparison issue to its candidate work entry (#342-volg).

    ``./curator <issue> <choice>`` needs the binding that this run established:
    the issue number on the candidate entry, the candidate track IDs in album
    order, and reviewed performers derived from the canonical performers
    registry (registry name + registry role; unknown artists stay raw).
    """
    entries = [e for e in recording['works'] if e.get('work_id') == work]
    require(entries, f'--work {work} is not a candidate on this recording')
    require(len(entries) == 1 and entries[0].get('status') == 'candidate',
            f'--work {work} is not a single candidate work entry on this recording')
    track_ids = [m['track']['id'] for m in matches
                 if m['state'] == 'matched' and m['work']['id'] == work]
    require(track_ids, f'--work {work} has no matched candidate tracks')
    names = []
    for m in matches:
        if m['state'] == 'matched' and m['work']['id'] == work:
            for name in m['track']['artists']:
                if name not in names:
                    names.append(name)
    reviewed = []
    for name in names:
        hits = [pid for pid, (canonical, _role) in performers.items()
                if norm(canonical) == norm(name)]
        if len(hits) == 1:
            pid = hits[0]
            category = next((cat for cat, ids in roles.items() if pid in ids), None)
            reviewed.append(f"{performers[pid][0]} ({category})" if category
                            else performers[pid][0])
        else:
            reviewed.append(name)
    require(reviewed, f'--work {work} has no candidate performers to review')
    entry = entries[0]
    entry['issue'] = issue
    entry['track_ids'] = track_ids
    entry['performers'] = reviewed
    return entry


def playlist_plan(root, album, recording, matches, recommendations, today, *,
                  issue=None, work=None, read_client=None, catalog_factory=None,
                  works=None, persons=None):
    """One comparison playlist per matched work that already has a recommendation.

    The current recommendation enters the playlist as its complete recording
    (the anchor track's album, every track matched to the same work), not as
    the single anchored track. With issue/work only the issue's work is
    planned, named "Curator <date> Issue #<nr>"; without an issue the plans
    are report-only and the caller is told how to create the playlist.
    Expansion failures are reported per work (playlist_errors) and never
    silently produce a fragmentary playlist.
    """
    works = works if works is not None else load_works(root)
    persons = persons if persons is not None else load_persons(root)
    by_id = {w['id']: w for w in works}
    plans, errors = [], []
    for entry in recording['works']:
        wid = entry['work_id']
        if wid not in recommendations or entry.get('status') != 'candidate':
            continue
        if issue is not None and wid != work:
            continue
        current = recommendations[wid]
        candidate_ids = [m['track']['id'] for m in matches
                         if m['state'] == 'matched' and m['work']['id'] == wid]
        require(candidate_ids, f'Work {wid} matched without candidate tracks')
        current_ids = list(current['track_ids'])
        if current_ids and read_client is not None:
            try:
                current_ids = expand_current_tracks(read_client, catalog_factory,
                                                    current_ids, by_id[wid], persons)
            except ValueError as exc:
                errors.append({'work_id': wid, 'error': str(exc)})
                continue
        description = (f"Candidate comparison for {album_url(album['id'])} "
                       f"(current recommendation: {', '.join(current['sources'])})")
        if issue is not None:
            description = f'https://github.com/LuHoo/classical_music/issues/{issue}\n' + description
        plans.append({'work_id': wid, 'issue': issue,
                      'name': f"Curator {today} Issue #{issue}" if issue is not None else None,
                      'description': description,
                      'current_track_ids': current_ids, 'candidate_track_ids': candidate_ids,
                      'current_sources': current['sources']})
    return plans, errors


def provision_playlist(client, plan):
    """Create one comparison playlist: current recommendation first, then the candidate.

    Duplicate track IDs are kept once, in first-seen order: when the existing
    anchor already sits on the candidate's own album (consolidation), the
    recording must not appear twice in its own comparison.
    """
    expected = []
    for tid in plan['current_track_ids'] + plan['candidate_track_ids']:
        if tid not in expected:
            expected.append(tid)
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
            elif entry.get('issue'):
                # Issue-bound entries carry the reviewed binding (issue,
                # track_ids, performers): a re-run with --issue/--work replaces
                # the older entry instead of leaving it unbound (#355). An
                # older file can carry the same work more than once (pre-#351
                # matching artifacts: one candidate plus one unevaluated entry
                # from an ambiguous track); assigning the new entry to every
                # occurrence would plant the same dict at two positions, which
                # ruamel dumps as an anchor/alias pair and the curator then
                # correctly refuses as a double binding. Replace the first
                # occurrence and drop the duplicates.
                indices = [index for index, old in enumerate(existing['works'])
                           if old.get('work_id') == entry['work_id']]
                existing['works'][indices[0]] = entry
                for index in reversed(indices[1:]):
                    del existing['works'][index]
        existing['links'] = recording['links']
        document = existing
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        yaml.dump(document, handle)
    return path


def run(root, url, *, dry_run=False, recording_id=None, update_existing=False,
        read_client=None, user_client_factory=None, today=None, suggest_client=None,
        canonize=False, issue=None, work=None, catalog_factory=None):
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
    # Canonization proposals (#327): new works are canonized as part of
    # registering the album, not as a separate manual step. Proposals are
    # fail-closed (unique ISRC-chain work + canonical composer evidence) and
    # are only written with --canonize.
    proposals, canonized = [], []
    if (canonize or dry_run) and any(m['state'] != 'matched' for m in matches):
        suggest = suggest_client if suggest_client is not None else SuggestionClient()
        proposals = build_work_proposals(matches, persons, album, suggest)
        if canonize and not dry_run and proposals:
            written_paths = [write_work(root, proposal) for proposal in proposals]
            canonized = [str(path.relative_to(root)) for path in written_paths]
            works = load_works(root)
            matches = match_works(tracks, works, persons, album['artists'], album.get('title', ''))
            recording, unmatched_tracks = build_recording(
                root, album, matches, roles, unmatched_artists, today, recording_id)
    if not recording['works'] and not dry_run:
        raise ValueError('No track could be related to canonical works; refusing to write anything. '
                         'Re-run with --dry-run for the per-track report of missing work definitions.'
                         + (' Canonization (--canonize) found no safe work proposal for the '
                            'remaining tracks.' if canonize else ''))
    if issue is not None:
        bind_issue(recording, matches, roles, performers, issue, work)
    recommendations, unattributed, breakdown = existing_recommendations(root, works)
    require((issue is None) == (work is None),
            '--issue and --work are supplied together: the issue number names the '
            'comparison playlist, the work ID binds it to this issue')
    if issue is not None:
        require(isinstance(issue, int) and issue > 0, 'Issue number must be positive')
    plans, playlist_errors = playlist_plan(
        root, album, recording, matches, recommendations, today,
        issue=issue, work=work, read_client=client,
        catalog_factory=catalog_factory
        or (lambda album_id: CatalogClient(access_token(), album_id)),
        works=works, persons=persons)
    plans = [p for p in plans if p['current_track_ids']]
    if issue is not None and not plans and not any(e['work_id'] == work for e in playlist_errors):
        raise ValueError(f'Issue #{issue} work {work} has no comparison playlist on this album: '
                         'the work must be a matched candidate with an existing recommendation '
                         'carrying a TIDAL track anchor')
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
              'playlist_plans': [{'work_id': p['work_id'], 'issue': p['issue'], 'name': p['name'],
                                  'current_tracks': p['current_track_ids'],
                                  'candidate_tracks': p['candidate_track_ids']} for p in plans],
              'playlist_errors': playlist_errors,
              'unmatched_tracks': [{'title': u['track']['title'], 'state': u['state'],
                                    'candidates': u.get('candidates', []),
                                    'variant': u.get('variant')} for u in unmatched_tracks],
              'unmatched_track_details': unmatched_track_details(matches, persons),
              'unmatched_artists': unmatched_artists,
              'unattributed_recommendation_lines': unattributed,
              'unattributed_breakdown': breakdown,
              'proposed_works': proposals,
              'canonized_works': canonized}
    output = {'recording': recording, 'report': report, 'dry_run': dry_run}
    if dry_run and not recording['works'] and report['unmatched_track_details']:
        attach_external_suggestions(report, suggest_client=suggest_client)
    if dry_run:
        output['note'] = ('Dry run: nothing written, no playlist created. '
                          'Re-run without --dry-run to apply.')
        if not recording['works']:
            output['note'] = ('Dry run: no track could be related to canonical works; nothing to '
                              'register yet. See the per-track report above for the missing work '
                              'definitions; add the works under data/works/, then re-run.')
            if proposals:
                output['note'] = ('Dry run: no track could be related to canonical works yet; '
                                  'see the proposed work definitions above (advisory). Apply with '
                                  '--canonize to canonize them as part of the registration and '
                                  're-run.')
        return output
    written = write_recording(root, recording, update_existing=update_existing)
    created = []
    if plans and issue is not None:
        factory = user_client_factory or (lambda: UserClient(user_access_token()))
        user_client = factory()
        for plan in plans:
            created.append({'work_id': plan['work_id'], 'url': provision_playlist(user_client, plan)})
    output['written'] = str(written.relative_to(root))
    output['playlists'] = created
    if plans and issue is None:
        report['playlist_notice'] = ('Comparison playlist(s) planned but not created: re-run with '
                                     '--issue <nr> --work <work-id> to create the playlist for one issue')
    for entry in output['report']['playlist_plans']:
        if created:
            entry['playlist_url'] = next(p['url'] for p in created if p['work_id'] == entry['work_id'])
        else:
            entry['playlist_url'] = None
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
    parser.add_argument('--no-external-lookups', action='store_true',
                        help='Skip the advisory MusicBrainz suggestions in the zero-match dry-run report')
    parser.add_argument('--verbose-unattributed', action='store_true',
                        help='Print every unattributed docs recommendation line instead of a summary')
    parser.add_argument('--canonize', action='store_true',
                        help='Canonize proposed new works (unique ISRC-chain MusicBrainz work with '
                             'canonical composer evidence) as part of this registration; without '
                             'this flag proposals are advisory only')
    parser.add_argument('--issue', type=int,
                        help='Issue number of the curator comparison issue; names the playlist '
                             '"Curator <date> Issue #<nr>" and creates it only for --work')
    parser.add_argument('--work',
                        help='Canonical work ID bound to the issue; with --issue the comparison '
                             'playlist is created only for this work')
    args = parser.parse_args(argv)
    try:
        result = run(ROOT, args.album_url, dry_run=args.dry_run,
                     recording_id=args.recording_id, update_existing=args.update_existing,
                     suggest_client=NullSuggestionClient() if args.no_external_lookups else None,
                     canonize=args.canonize, issue=args.issue, work=args.work)
    except ValueError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print_report(result, verbose_unattributed=args.verbose_unattributed)
    return 0


def print_report(result, *, verbose_unattributed=False):
    """Print the human-readable report of a run() result (CLI stdout).

    Standalone function (#352): the print path is exercised by the tests with
    fake results, so a report key mismatch crashes in CI instead of in the
    curator's terminal.
    """
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
        if entry.get('name'):
            line += f" — {entry['name']}"
        print(line)
    for entry in report.get('playlist_errors') or []:
        print(f"  PLAYLIST SKIPPED ({entry['work_id']}): {entry['error']}")
    notice = report.get('playlist_notice')
    if notice:
        print(f"  {notice}")
    for entry in report['unmatched_tracks']:
        if entry['state'] == 'variant':
            print(f"  SKIPPED VARIANT: {entry['title']} ({entry['variant']})")
            continue
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
            suggestions = entry.get('external_suggestions')
            if suggestions:
                print('       external suggestions (advisory, MusicBrainz — never canonical):')
                for hit in suggestions:
                    composers = ', '.join(c['name'] for c in hit['composers'])
                    print(f"         - {hit['title']} (musicbrainz work {hit['musicbrainz_work_id']})"
                          f" — composer: {composers or 'not stated on the work'}")
            elif suggestions is None:
                print('       external suggestions: unavailable (lookup failed or disabled)')
    if report['unattributed_recommendation_lines']:
        if verbose_unattributed:
            print('  Recommendation lines without a canonical work attribution: '
                  + ', '.join(report['unattributed_recommendation_lines']))
        else:
            print(f"  Unattributed docs recommendation lines: {len(report['unattributed_recommendation_lines'])}"
                  ' (re-run with --verbose-unattributed for the full list)')
            for entry in report['unattributed_breakdown']:
                examples = '; '.join(entry['examples'])
                print(f"    {entry['category']}: {entry['count']}"
                      + (f' — e.g. {examples}' if examples else ''))
    for proposal in report.get('proposed_works') or []:
        print(f"  Proposed new work (advisory): {proposal['work_id']}")
        print(f"    evidence: ISRC {proposal['evidence']['isrc']}"
              f" (musicbrainz work {proposal['evidence']['musicbrainz_work_id']}"
              + (f", recording {proposal['evidence']['musicbrainz_recording_id']}"
                 if proposal['evidence'].get('musicbrainz_recording_id') else '')
              + (f", wikidata {proposal['evidence']['wikidata_url']}"
                 if proposal['evidence'].get('wikidata_url') else '')
              + f", label: {proposal['evidence'].get('label') or 'unknown'})")
    if result['dry_run'] and report.get('proposed_works'):
        for proposal in report['proposed_works']:
            print(f"--- Proposed data/works/{proposal['work_id']}.yaml (apply with --canonize) ---")
            print(dump_yaml({key: value for key, value in proposal.items()
                             if key != 'evidence' and value is not None}), end='')
            print('--- End of proposed work ---')
    if report.get('canonized_works'):
        print('  Canonized new works: ' + ', '.join(report['canonized_works']))
    if result['dry_run']:
        print('--- Proposed data/recordings YAML ---')
        print(dump_yaml(result['recording']), end='')
        print('--- End of proposed YAML ---')
        print(result['note'])
    if result.get('written'):
        print(f"Written: {result['written']}")


if __name__ == '__main__':
    sys.exit(main())
