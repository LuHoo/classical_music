# TIDAL live playlist and write pilot

This stage reads the current Best Classical playlist through the official API and builds an occurrence-aware replacement plan for the 23 reported tracks. It never modifies Best Classical. The original ISRC and duration come from the existing CSV export. Live positions are resolved by track ID rather than assuming the export's positions remain current.

## Official API contract

Specification consulted: https://tidal-music.github.io/tidal-api-reference/tidal-api-oas.json (version 1.10.148, 2026-10-03).

- GET `/playlists/{id}` and GET `/playlists/{id}/relationships/items` accept client credentials for publicly accessible playlists. Cursor pages are read in `itemIndex` order; `lastModifiedAt` is checked before and after the snapshot.
- POST and DELETE `/playlists/{id}/relationships/items` require user authorization. Third-party scope: `playlists.write`. Listing a user's playlists uses `playlists.read`. INTERNAL scopes `r_usr` and `w_usr` are not requested.
- An occurrence is identified by `meta.itemId`, not merely by track ID. Inserting uses `meta.positionBefore`; deletion includes the old occurrence's `meta.itemId`. Duplicate policy is explicitly `ADD`.
- PATCH of items is an occurrence movement operation; it is not a whole-playlist replacement endpoint.
- Built-in `replacement` and `replaceMedia` are currently labelled BETA/Internal-only and are not used.

The write pilot creates one temporary UNLISTED playlist with `[Geysir, Gran Partita I, Geysir]`. It inserts Gran Partita I before the first Geysir, verifies the resulting order, removes only that first Geysir occurrence, and verifies `[Gran Partita I, Gran Partita I, Geysir]`. The temporary playlist is then deleted. If insertion cannot be verified, the old occurrence is not removed. A cleanup failure is reported as a failed pilot.

## One-time local TIDAL login

App client credentials do not authorize writes to the user's playlists. There was no `TIDAL_USER_ACCESS_TOKEN` configured in the Actions run. The remaining live write test needs the user's interactive authorization; it cannot be obtained from the app secret alone.

On your computer:

1. In the existing app's TIDAL Developer settings, register the exact redirect URI `http://127.0.0.1:8765/callback`. Enable the supported user authorization-code/PKCE flow and the `playlists.read` and `playlists.write` permissions if the dashboard requires explicit scope configuration.
2. Use a separate checkout of the pilot branch. From an existing repository checkout:

```bash
git fetch origin issue-64-tidal-link-maintenance
git worktree add --detach ../classical_music-tidal-pilot origin/issue-64-tidal-link-maintenance
cd ../classical_music-tidal-pilot
python3 scripts/tidal_playlist_login.py --client-id YOUR_PUBLIC_CLIENT_ID
```

Python 3.9 or newer is supported by these standalone standard-library scripts. The repository package's separate Python >=3.13 requirement does not apply to running this pilot directly. The Client ID is public; do not paste a client secret or token into a chat. If the app requires confidential-client authentication during token exchange, `TIDAL_CLIENT_SECRET` can be supplied securely in your local environment; it is never printed.

3. Complete the TIDAL login and consent in the browser on that computer. The loopback callback validates OAuth state; PKCE binds the code exchange. The token stays in the process's memory. It is not written to disk, printed, or uploaded. The login script then runs the disposable write pilot automatically.

The local result is `reports/tidal-maintenance/playlist-live-pilot.json`. It contains playlist metadata, item IDs, the replacement plan, and test outcomes, but no tokens. Do not commit a full personal playlist snapshot without deciding to do so. No persistent refresh token is stored in this pilot.

## Validation and scope

Five automated tests cover duplicate preservation, video handling, occurrence-specific insertion/deletion, refusal to delete an old occurrence after an incorrect insertion, source-playlist isolation, temporary-playlist cleanup, credential host validation, and abort on a concurrent playlist change.

```bash
python3 -m unittest discover -s tests -p test_playlist_live_pilot.py
```

The live API read and the local unit tests are distinct from an authenticated live write. A successful read-only Actions run does not prove write permission. Replacing tracks in Best Classical remains a subsequent stage after the disposable test; this pilot has no command that mutates the source playlist.
