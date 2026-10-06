"""Obtain an ephemeral catalogue token without logging app credentials."""

from __future__ import annotations

import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
MAX_TOKEN_RESPONSE_BYTES = 64_000


class NoAuthRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Tidal authentication endpoint redirected; request refused")


def access_token() -> str:
    """Prefer an explicit token; otherwise use the app client-credentials flow."""
    supplied = os.environ.get("TIDAL_ACCESS_TOKEN", "")
    if supplied:
        return supplied
    client_id = os.environ.get("TIDAL_CLIENT_ID", "")
    client_secret = os.environ.get("TIDAL_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError(
            "API access requires TIDAL_ACCESS_TOKEN or both "
            "TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET"
        )
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = Request(
        TOKEN_URL,
        data=urlencode({"grant_type": "client_credentials"}).encode(),
        headers={
            "Authorization": "Basic " + credentials,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with build_opener(NoAuthRedirects()).open(req, timeout=15) as response:
            raw = response.read(MAX_TOKEN_RESPONSE_BYTES + 1)
            if response.status != 200 or len(raw) > MAX_TOKEN_RESPONSE_BYTES:
                raise ValueError("Invalid Tidal token response")
    except HTTPError as exc:
        raise ValueError(f"Tidal authentication failed (HTTP {exc.code})") from None
    except (URLError, OSError):
        raise ValueError("Tidal authentication failed (network error)") from None
    try:
        doc = json.loads(raw)
        token = doc.get("access_token") if isinstance(doc, dict) else None
        if (
            not isinstance(token, str)
            or not token
            or any(c.isspace() for c in token)
            or str(doc.get("token_type", "")).lower() != "bearer"
        ):
            raise ValueError("Invalid Tidal token response")
    except (ValueError, UnicodeError):
        # Do not include the response body or provider error text in any log.
        raise ValueError("Invalid Tidal token response") from None
    if os.environ.get("GITHUB_ACTIONS") == "true":
        # The runner consumes this command and redacts the ephemeral credential.
        print("::add-mask::" + token)
    return token


def user_access_token() -> str:
    """Use a user token or refresh a user's grant; never substitute an app token."""
    supplied = os.environ.get('TIDAL_USER_ACCESS_TOKEN', '')
    if supplied:
        if any(c.isspace() for c in supplied):
            raise ValueError('Invalid TIDAL user access token')
        return supplied
    refresh = os.environ.get('TIDAL_USER_REFRESH_TOKEN', '')
    client_id = os.environ.get('TIDAL_CLIENT_ID', '')
    if not refresh or not client_id:
        raise ValueError('Configure TIDAL_USER_REFRESH_TOKEN with the curator playlist login command')
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
    secret = os.environ.get('TIDAL_CLIENT_SECRET', '')
    if secret:
        headers['Authorization'] = 'Basic ' + base64.b64encode(f'{client_id}:{secret}'.encode()).decode()
    request = Request(TOKEN_URL, method='POST', headers=headers, data=urlencode({
        'grant_type': 'refresh_token', 'refresh_token': refresh, 'client_id': client_id}).encode())
    try:
        with build_opener(NoAuthRedirects()).open(request, timeout=20) as response:
            raw = response.read(MAX_TOKEN_RESPONSE_BYTES + 1)
        if len(raw) > MAX_TOKEN_RESPONSE_BYTES:
            raise ValueError('Invalid user token response')
        doc = json.loads(raw)
        token = doc.get('access_token')
        if (not isinstance(token, str) or not token or any(c.isspace() for c in token)
                or str(doc.get('token_type', '')).lower() != 'bearer'
                or not {'playlists.read', 'playlists.write'}.issubset(doc.get('scope', '').split())):
            raise ValueError('Invalid user token response or missing playlist read/write scopes')
        if doc.get('refresh_token', refresh) != refresh:
            raise ValueError('TIDAL rotated the refresh grant; repeat the local login setup')
    except HTTPError as exc:
        raise ValueError(f'TIDAL user login needs renewal (HTTP {exc.code})') from None
    except (URLError, OSError):
        raise ValueError('TIDAL user token refresh failed (network error)') from None
    except (json.JSONDecodeError, UnicodeError, AttributeError, TypeError):
        raise ValueError('Invalid user token response') from None
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print('::add-mask::' + token)
    return token
