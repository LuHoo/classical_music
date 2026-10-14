# Listening playlists when curator issues are opened

The **Curator listening playlist** workflow creates one separate, unlisted TIDAL
playlist for each new, registered comparison issue. It groups all recorded
movements of the first candidate, then the second, and so on. The issue receives
one comment containing the playlist link and a table of candidates, performers
and track ranges. Existing source playlists and curator decisions are unchanged.
No AI model or AI tokens are involved in creation, verification or retries.

## Activation

Merge the workflow into the default branch. GitHub already needs the existing
`TIDAL_CLIENT_ID` and `TIDAL_CLIENT_SECRET` app secrets. In addition, a user must
authorize `playlists.read playlists.write`; app-only catalogue access cannot
create a user's playlist. Authorize the **same TIDAL app** once on your computer:

```bash
# gh must be logged in with permission to set this repository's secrets.
# TIDAL_CLIENT_ID is the public client ID of the app already configured in GitHub.
.venv/bin/python scripts/tidal_playlist_login.py --setup-curator-playlists \
  --client-id "$TIDAL_CLIENT_ID"
```

The app must have `http://127.0.0.1:8765/callback` registered as its redirect URI.
If your app requires a client secret for login, supply `TIDAL_CLIENT_SECRET` in
the local environment as for the existing login script. The browser asks you to
log in. The refresh grant is piped directly to `gh secret set` as
`TIDAL_USER_REFRESH_TOKEN`; it is never printed, put in command arguments or
written to a local file. This setup does not run the existing disposable pilot
or any repair operation.

The workflow refreshes a user access token for each run. An expired/revoked grant,
missing write scope or unexpected refresh-token rotation stops before playlist
creation and asks for renewed setup. It never substitutes an app-only token.
See [TIDAL authorization](https://developer.tidal.com/documentation/api-sdk/api-sdk-authorization)
for the user authorization and refresh flows.

## Which issues run automatically?

- An open issue with the existing `phase-2-curator-workflow` label, created by a
  repository owner, member or collaborator (or the GitHub Actions bot).
- Events: issue opened, reopened, labeled or edited. Other issues and PRs are
  skipped, and secrets are not needed for the discovery job.
- The issue number resolves to exactly one pending `recommendation_choices`
  entry in an existing JSON manifest under `reports/playlist-import/`.
- If the issue is created before its binding reaches `main`, the comment records
  a waiting request. A later manifest push retries these waiting requests.
  Existing issues without a request are **not** backfilled automatically.

A new issue can also bind to an already committed pending Work before its issue
number has been added to the manifest. Include this block in its body:

```html
<!-- curator-choice {"manifest":"reports/playlist-import/piano/snapshot-2026-10-04.json","work_id":"the-reviewed-work-id"} -->
```

The referenced choice must have no other issue binding. The metadata cannot
supply arbitrary tracks: the script always reads reviewed candidates from the
committed manifest. A mismatch, missing Work or multiple matching choices fails
with an explanation in the issue's single automation comment.

If another GitHub workflow creates an issue using `GITHUB_TOKEN`, GitHub normally
suppresses downstream issue-event workflows ([GitHub token behavior](https://docs.github.com/en/actions/concepts/security/github_token)). That producer must explicitly
call this script as its next step or dispatch **Curator listening playlist**
after creating the issue. Local `gh issue create` with a user login triggers the
normal issue event.

## Collections and complete candidates

Planning is independent of Chamber: current Chamber and Piano choices use the
same manifest fields. A Best Classical choice can be registered in its existing
window manifest with `recommendation_choices` and stable `unit_id` values for
the competing units; `candidate_performers` is supported as well as `performers`.
There is no second candidate database or inference from free-form issue text.
The decision CLI supports Chamber, Piano and registered Best Classical window
choices. See the [User Manual](scripts-user-manual.md) for registration requirements
and the separate limits of listening and applying decisions.

A/B labels are taken only from explicit `choice_aliases`; otherwise the reviewed
unit codes are shown. Movement order, duplicate occurrences and stated excerpts
are preserved. The automation never expands an excerpt into guessed movements.
At least two candidates are required; more than 500 tracks require review.

An existing recommendation already represented by a source unit appears once.
If it is outside the source snapshot, its single canonical listening anchor is
insufficient evidence for a whole work. Supply its verified complete track list
inside the same choice entry, for example:

```json
"existing_performance_tracks": {
  "canonical-performance-id": {
    "reviewed_complete": true,
    "source": "reference used to verify the complete movement sequence",
    "tracks": [{"id": "12345"}, {"id": "12346"}]
  }
}
```

The canonical Performance supplies its performers and Work identity. Until the
full list is available, the workflow reports the evidence gap and creates no
partial comparison playlist. For example, the current #257 needs this evidence;
#246 and #263 already have their two candidates' source tracks.

## Preview, retry and recovery

The script itself defaults to preview. The issue hook supplies `--apply` because
opening a registered curator issue requests its comparison playlist.

```bash
# Local preview: reads GitHub and committed source data; no TIDAL calls or writes.
GITHUB_TOKEN="$(gh auth token)" .venv/bin/python \
  scripts/create_curator_listening_playlist.py 246

# After merging and authorizing: create/retry an existing issue explicitly.
gh workflow run curator-listening-playlist.yml \
  --repo LuHoo/classical_music -f issue_number=246
```

The machine-readable section of the issue comment is an operational journal:
`awaiting_manifest → prepared → creating → created → adding → verified`.
It contains no credentials and does not change acceptance in the import data.
The workflow serializes all runs for a given issue. Only trusted automation or
maintainer comments can supply the journal; multiple journals stop processing.

Before each TIDAL mutation, the script saves the intended operation. It uses
stable idempotency keys and verifies the playlist's name, plan marker, item
count and exact track sequence after adding each batch. The link is marked
ready only when every candidate track is verified. A completed retry is a no-op.
Changed candidates, unexpected content, missing tracks or a source-playlist ID
stop processing rather than replacing/deleting anything.

If a create response was lost, another playlist is **not** blindly created.
Inspect TIDAL for the `Curator #<issue>` playlist with the matching issue URL and
plan marker. Recover that known UUID through the workflow's
`recover_playlist_id` input. The script verifies its identity before adding:

```bash
gh workflow run curator-listening-playlist.yml \
  --repo LuHoo/classical_music -f issue_number=246 \
  -f recover_playlist_id=THE_VERIFIED_COMPARISON_PLAYLIST_UUID
```

A lost append response can be recovered automatically when a fresh snapshot
shows exactly the expected completed batch. Otherwise the workflow stops for
inspection; it does not retry an uncertain append blindly. After verifying that
no append happened and no request remains in flight, a maintainer may restore
the journal phase from `adding` to `created` at the same offset and dispatch it
again. Never reset or delete a journal just to bypass an unexplained mismatch.

Listen and decide as usual afterwards. These playlists are not automatically
removed when an issue closes, and this workflow does not execute the later
source-playlist removal described in a curator decision.

## Verification

```bash
.venv/bin/python -m pytest tests/test_curator_listening.py \
  tests/test_playlist_live_pilot.py tests/test_repair_tidal_playlist.py \
  tests/test_tidal_auth.py tests/test_tidal_playlist_auth.py --no-cov
```

Tests use fake API clients: real source playlists are never modified by tests.
They cover Chamber/Piano/Best Classical planning, existing recordings, missing
movement evidence, untrusted issues/journals, preview, duplicate triggers,
lost create/append responses, recovery, altered playlists and credential setup.
An end-to-end live run additionally requires the user's grant and the merged
workflow; unit tests do not claim live API verification.
