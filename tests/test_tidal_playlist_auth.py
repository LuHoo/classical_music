"""Authentication tests use synthetic credentials, never repository secrets."""

import base64
import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from classical_music.tidal_auth import TOKEN_URL, NoAuthRedirects, access_token


@pytest.fixture(autouse=True)
def clean_credentials(monkeypatch):
    for name in (
        "TIDAL_ACCESS_TOKEN",
        "TIDAL_CLIENT_ID",
        "TIDAL_CLIENT_SECRET",
        "GITHUB_ACTIONS",
    ):
        monkeypatch.delenv(name, raising=False)


def response(doc):
    r = io.BytesIO(json.dumps(doc).encode())
    r.status = 200
    return r


def app_credentials(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "synthetic-id")
    monkeypatch.setenv("TIDAL_CLIENT_SECRET", "synthetic-secret")


def test_explicit_token_needs_no_app_request(monkeypatch):
    monkeypatch.setenv("TIDAL_ACCESS_TOKEN", "synthetic-token")
    with patch("classical_music.tidal_auth.build_opener") as opener:
        assert access_token() == "synthetic-token"
        opener.assert_not_called()


def test_client_credentials_request_and_no_stdout(monkeypatch, capsys):
    app_credentials(monkeypatch)
    with patch("classical_music.tidal_auth.build_opener") as opener:
        opener.return_value.open.return_value = response(
            {"access_token": "synthetic-token", "token_type": "Bearer"}
        )
        assert access_token() == "synthetic-token"
        req = opener.return_value.open.call_args.args[0]
        assert req.full_url == TOKEN_URL
        assert req.method == "POST"
        assert req.data == b"grant_type=client_credentials"
        expected = base64.b64encode(b"synthetic-id:synthetic-secret").decode()
        assert req.get_header("Authorization") == "Basic " + expected
        assert opener.return_value.open.call_args.kwargs["timeout"] == 15
    assert capsys.readouterr().out == ""


def test_github_runner_masks_generated_token(monkeypatch, capsys):
    app_credentials(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with patch("classical_music.tidal_auth.build_opener") as opener:
        opener.return_value.open.return_value = response(
            {"access_token": "synthetic-token", "token_type": "Bearer"}
        )
        access_token()
    assert capsys.readouterr().out == "::add-mask::synthetic-token\n"


@pytest.mark.parametrize(
    "doc",
    [
        {"access_token": "secret\nINJECTED", "token_type": "Bearer"},
        {"access_token": "", "token_type": "Bearer"},
        {"access_token": "synthetic-token", "token_type": "Basic"},
        {"error_description": "synthetic-secret"},
        ["synthetic-secret"],
    ],
)
def test_invalid_token_documents_never_echo_secrets(monkeypatch, doc):
    app_credentials(monkeypatch)
    with patch("classical_music.tidal_auth.build_opener") as opener:
        opener.return_value.open.return_value = response(doc)
        with pytest.raises(ValueError) as err:
            access_token()
    assert str(err.value) == "Invalid Tidal token response"


@pytest.mark.parametrize(
    "error",
    [
        HTTPError(TOKEN_URL, 401, "synthetic-secret", None, None),
        URLError("synthetic-secret"),
    ],
)
def test_authentication_errors_are_sanitized(monkeypatch, error):
    app_credentials(monkeypatch)
    with patch("classical_music.tidal_auth.build_opener") as opener:
        opener.return_value.open.side_effect = error
        with pytest.raises(ValueError) as err:
            access_token()
    assert "synthetic-secret" not in str(err.value)
    assert "authentication failed" in str(err.value)


def test_authentication_redirect_refused():
    with pytest.raises(ValueError, match="redirected"):
        NoAuthRedirects().redirect_request(
            Request(TOKEN_URL), None, 302, "", {}, "https://example.com"
        )


def test_incomplete_app_credentials_rejected(monkeypatch):
    monkeypatch.setenv("TIDAL_CLIENT_ID", "synthetic-id")
    with pytest.raises(
        ValueError, match="both TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET"
    ):
        access_token()
