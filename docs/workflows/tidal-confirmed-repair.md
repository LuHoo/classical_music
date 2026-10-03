# Apply the approved Best Classical replacements

Lucas authorized the 609 CONFIRMED occurrences in `reports/tidal-maintenance/full-playlist-scan-2026-10-03.json`. The 364 REVIEW and 66 NOT_FOUND occurrences are outside this repair.

From the existing `classical_music-tidal-pilot` worktree on the Mac:

```sh
git fetch origin issue-64-tidal-link-maintenance
git merge --ff-only origin/issue-64-tidal-link-maintenance
python3 scripts/tidal_playlist_login.py --client-id ldZgGfK4yL66Llw9 --repair-confirmed
```

The OAuth app must have `playlists.read` and `playlists.write` enabled and the registered redirect URI `http://127.0.0.1:8765/callback`. The user token remains in memory. The default login command without `--repair-confirmed` still runs only the disposable write pilot. No user token is available to the remote development session, so publication of this script does not itself execute the source playlist changes.

Before writing, the script reads all 5518 live occurrences and verifies the original modification marker, exact approved positions and occurrence IDs. It rechecks the streaming replacement catalogue against the same ISRC, normalized title, exact duration and credited artist overlap; a changed or ambiguous candidate stops execution before any writes. The actual approved plan forms 111 contiguous groups, each containing at most 50 occurrences.

A local journal at `reports/tidal-maintenance/confirmed-repair-local.json` stores the complete pre-write snapshot and each group request state and insertion response. Each group is inserted before its original first occurrence, with duplicates explicitly allowed. The insertion response must contain every expected replacement and distinct new occurrence IDs before the original occurrence IDs are deleted. Intermediate modification markers and item counts are checked. The final full snapshot must match the expected track order and every expected occurrence ID, retaining all unselected occurrences.

The API does not offer an atomic compare-and-swap for this sequence. Avoid editing the playlist in another application while repair is running. Keep the Mac awake and the terminal open until the final result. Success prints `status: passed`, `replaced_occurrences: 609`, `final_item_count: 5518`, and `order_verified: true`.

If interrupted or stopped, preserve the journal and do not delete it to retry. An uncertain insertion or deletion may already have reached TIDAL. The script refuses a second run when the journal exists, preventing blind repeated insertion. Inspect the journal and a fresh live snapshot to reconcile any partial result before continuing. The pre-write snapshot is an audit backup; unavailable original tracks may not be re-addable, so it is not a guarantee of automatic rollback. Neither tokens nor authorization codes are written to the journal.

Validation: 20 focused tests cover the scanner, disposable pilot and repair, including preservation of an unselected duplicate, exact order, missing insertion IDs, partial deletion failure, existing-journal refusal, stale approval, moved occurrences and changed catalogue identity. Standalone script syntax is compatible with Python 3.9.
