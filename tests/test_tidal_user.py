"""Offline tests for the shared TIDAL user client error surfacing (#438).

The JSON:API error body explains why TIDAL rejected a request (field limits,
scopes); the wrapper must surface it instead of only the status code. The
existing prefix must stay intact so callers that branch on it keep working.
"""
import io
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from classical_music.tidal_user import Client


class FakeOpener:
    def __init__(self, error):
        self.error = error

    def open(self, req, timeout=None):
        raise self.error


def client_with(error):
    client = Client('token')
    client.opener = FakeOpener(error)
    return client


def http_error(code, body):
    return HTTPError('https://openapi.tidal.com/v2/playlists', code, 'err', {},
                     io.BytesIO(body.encode()))


class ErrorBodyTest(unittest.TestCase):
    def test_error_body_is_surfaced(self):
        body = ('{"errors":[{"code":"INVALID_REQUEST_BODY",'
                '"detail":"Size must be between 0 and 500",'
                '"source":{"pointer":"/data/attributes/description"}}]}')
        client = client_with(http_error(400, body))
        with self.assertRaises(ValueError) as ctx:
            client.request('/playlists', 'POST', {})
        message = str(ctx.exception)
        self.assertIn('API POST failed (HTTP 400)', message)
        self.assertIn('INVALID_REQUEST_BODY', message)
        self.assertIn('/data/attributes/description', message)

    def test_error_code_without_body_keeps_the_plain_message(self):
        client = client_with(http_error(404, ''))
        with self.assertRaises(ValueError) as ctx:
            client.request('/playlists/abc', 'GET')
        self.assertEqual(str(ctx.exception), 'API GET failed (HTTP 404)')

    def test_long_error_body_is_truncated(self):
        client = client_with(http_error(400, 'x' * 5000))
        with self.assertRaises(ValueError) as ctx:
            client.request('/playlists', 'POST', {})
        self.assertLessEqual(len(str(ctx.exception)), len('API POST failed (HTTP 400): ') + 500)


if __name__ == '__main__':
    unittest.main()
