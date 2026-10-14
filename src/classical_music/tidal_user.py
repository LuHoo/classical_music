"""User-authorized TIDAL client shared by playlist operations and the pilot."""
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit, parse_qsl, urlunsplit
from urllib.request import Request, build_opener
from uuid import uuid4

from classical_music.tidal_auth import NoAuthRedirects

API = 'https://openapi.tidal.com/v2'


class Client:
    def __init__(self, token):
        self.token = token
        self.opener = build_opener(NoAuthRedirects())

    def request(self, path, method='GET', body=None, *, idempotency_key=None):
        url = path if path.startswith('https://') else API + path
        p = urlsplit(url)
        if p.scheme != 'https' or p.netloc != 'openapi.tidal.com' or not p.path.startswith('/v2/') or p.fragment:
            raise ValueError('Unexpected API URL; credentials not sent')
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.api+json'}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode()
            headers['Content-Type'] = 'application/vnd.api+json'
        if method != 'GET':
            headers['Idempotency-Key'] = idempotency_key or str(uuid4())
        req = Request(url, data=payload, headers=headers, method=method)
        for attempt in range(3):
            time.sleep(0.5)
            try:
                with self.opener.open(req, timeout=20) as response:
                    raw = response.read(4_000_001)
                if len(raw) > 4_000_000:
                    raise ValueError('API response exceeded size limit')
                return json.loads(raw) if raw else {}
            except HTTPError as exc:
                if exc.code == 429 and attempt < 2:
                    time.sleep(5)
                    continue
                raise ValueError(f'API {method} failed (HTTP {exc.code})') from None
            except (URLError, OSError):
                raise ValueError('API network request failed') from None

    def snapshot(self, playlist):
        base = '/playlists/' + playlist
        before = self.request(base + '?countryCode=NL')['data']
        marker = before.get('attributes', {}).get('lastModifiedAt')
        if not marker:
            raise ValueError('Missing playlist modification marker')
        path = '/v2' + base + '/relationships/items'
        next_url = API + base + '/relationships/items?' + urlencode({'countryCode': 'NL', 'sort': 'itemIndex'})
        items, seen = [], set()
        for page_number in range(1000):
            if not next_url:
                break
            if next_url in seen:
                raise ValueError('Repeated pagination link')
            seen.add(next_url)
            page = self.request(next_url)
            if not isinstance(page.get('data'), list):
                raise ValueError('Invalid playlist page')
            items.extend(page['data'])
            if (page_number + 1) % 100 == 0:
                print(json.dumps({'pages_read': page_number + 1, 'items_read': len(items)}), flush=True)
            if len(items) > 10000:
                raise ValueError('Playlist exceeded 10000-item pilot limit')
            following = page.get('links', {}).get('next')
            if isinstance(following, dict):
                following = following.get('href')
            next_url = urljoin(next_url, following) if following else None
            if next_url:
                p = urlsplit(next_url)
                if p.scheme != 'https' or p.netloc != 'openapi.tidal.com' or p.path not in {path, path.removeprefix('/v2')} or p.fragment:
                    raise ValueError('Unexpected playlist pagination target')
                query = dict(parse_qsl(p.query))
                if query.get('countryCode', 'NL') != 'NL' or query.get('sort', 'itemIndex') != 'itemIndex':
                    raise ValueError('Pagination changed country or order')
                query.update(countryCode='NL', sort='itemIndex')
                next_url = urlunsplit((p.scheme, p.netloc, path, urlencode(query), ''))
        if next_url:
            raise ValueError('Playlist exceeded page limit')
        after = self.request(base + '?countryCode=NL')['data']
        if before['id'] != playlist or after['id'] != playlist or marker != after.get('attributes', {}).get('lastModifiedAt'):
            raise ValueError('Playlist changed while reading; retry')
        return {'playlist': before, 'items': items}
