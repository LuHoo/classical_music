#!/usr/bin/env python3
"""Local OAuth+PKCE login; token stays in memory; run the disposable pilot or explicitly approved repairs."""
import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError

from playlist_live_pilot import main as run_pilot
from classical_music.tidal_auth import NoAuthRedirects

REDIRECT_URI = 'http://127.0.0.1:8765/callback'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-id', default=os.environ.get('TIDAL_CLIENT_ID', ''))
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--repair-spartacus', action='store_true', help='Apply the 29 approved Spartacus replacements')
    modes.add_argument('--repair-one-second', action='store_true', help='Apply the 108 approved one-second duration differences')
    modes.add_argument('--repair-confirmed', action='store_true', help='Apply the 609 approved occurrences to Best Classical')
    args = parser.parse_args()
    if not args.client_id:
        parser.error('Supply the public TIDAL Client ID using --client-id or TIDAL_CLIENT_ID')
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    state = secrets.token_urlsafe(32)
    callback = {}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log callback URLs containing authorization codes.
        def do_GET(self):
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query)
            if parsed.path != '/callback':
                self.send_error(404)
                return
            valid = hmac.compare_digest(query.get('state',[''])[0], state)
            if not valid:
                self.send_error(400, 'Invalid OAuth state')
                return
            callback.update(code=query.get('code',[''])[0], error=query.get('error',[''])[0])
            self.send_response(200)
            self.send_header('Content-Type','text/plain; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.end_headers()
            self.wfile.write(b'Login received. You can close this tab; see the terminal for the test result.')
    with HTTPServer(('127.0.0.1',8765),Handler) as server:
        server.timeout = 10
        url = 'https://login.tidal.com/authorize?' + urlencode({
            'response_type':'code', 'client_id':args.client_id, 'redirect_uri':REDIRECT_URI,
            'scope':'playlists.read playlists.write', 'state':state,
            'code_challenge':challenge, 'code_challenge_method':'S256'})
        print('Opening TIDAL login. Required registered redirect URI: ' + REDIRECT_URI)
        if args.repair_spartacus:
            print('Applying the 29 approved Spartacus replacements to Best Classical after fresh validation.')
        elif args.repair_one_second:
            print('Applying the 108 approved one-second replacements to Best Classical after fresh validation.')
        elif args.repair_confirmed:
            print('Applying the 609 approved replacements to Best Classical after fresh validation.')
        else:
            print('The test uses a temporary unlisted playlist; Best Classical will not be modified.')
        if not webbrowser.open(url):
            print('Open this login link on this computer: ' + url)
        deadline = time.monotonic()+600
        while not callback and time.monotonic()<deadline:
            server.handle_request()
    if not callback.get('code') or callback.get('error'):
        raise ValueError('TIDAL authorization failed or timed out')
    headers = {'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'}
    secret = os.environ.get('TIDAL_CLIENT_SECRET','')
    if secret:
        headers['Authorization'] = 'Basic ' + base64.b64encode((args.client_id+':'+secret).encode()).decode()
    req = Request('https://auth.tidal.com/v1/oauth2/token',method='POST',headers=headers,
        data=urlencode({'grant_type':'authorization_code','client_id':args.client_id,
                       'code':callback['code'],'redirect_uri':REDIRECT_URI,'code_verifier':verifier}).encode())
    try:
        with build_opener(NoAuthRedirects()).open(req,timeout=20) as response:
            raw = response.read(64001)
    except HTTPError as exc:
        raise ValueError(f'OAuth token exchange failed (HTTP {exc.code})') from None
    except (URLError,OSError):
        raise ValueError('OAuth token exchange failed (network error)') from None
    if len(raw)>64000:
        raise ValueError('Invalid OAuth token response')
    doc = json.loads(raw)
    token = doc.get('access_token')
    if not isinstance(token,str) or not token or any(c.isspace() for c in token) or str(doc.get('token_type','')).lower()!='bearer':
        raise ValueError('Invalid OAuth token response')
    granted = doc.get('scope')
    if granted is not None and 'playlists.write' not in granted.split():
        raise ValueError('TIDAL did not grant playlists.write')
    prior = os.environ.get('TIDAL_USER_ACCESS_TOKEN')
    os.environ['TIDAL_USER_ACCESS_TOKEN']=token
    try:
        if args.repair_confirmed or args.repair_one_second or args.repair_spartacus:
            from repair_tidal_playlist import main as run_repair
            return run_repair(['--spartacus'] if args.repair_spartacus else (['--duration-one-second'] if args.repair_one_second else []))
        return run_pilot(['--test-write'])
    finally:
        if prior is None:
            os.environ.pop('TIDAL_USER_ACCESS_TOKEN',None)
        else:
            os.environ['TIDAL_USER_ACCESS_TOKEN']=prior


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError,OSError) as exc:
        raise SystemExit('Local TIDAL login failed: '+str(exc))
