# Apply the 108 approved one-second duration replacements

On 3 October 2026 Lucas explicitly approved the 108 REVIEW cases in the verified full scan whose sole mismatch is exactly one second of duration. The ISRC, normalized title and credited artist overlap match, and each original ISRC has one streaming candidate in NL. The preceding 609 CONFIRMED replacements have been executed successfully; Lucas supplied `status: passed`, `replaced_occurrences: 609`, `final_item_count: 5518`, and `order_verified: true`.

Run from the same Mac worktree used for the successful repair:

```sh
git fetch origin issue-64-tidal-link-maintenance
git merge --ff-only origin/issue-64-tidal-link-maintenance
python3 scripts/tidal_playlist_login.py --client-id ldZgGfK4yL66Llw9 --repair-one-second
```

The successful local journal `reports/tidal-maintenance/confirmed-repair-local.json` is required. The script reads its final snapshot and compares every live occurrence ID, track ID, type and the playlist modification marker before any writes. It also checks the selected 108 original positions and occurrence IDs against the scan. This baseline accounts for the 609 completed replacements rather than incorrectly requiring the original pre-repair modification marker.

The script rechecks all 108 candidates in NL: there must still be exactly one streaming candidate under the same ISRC, with the approved ID, matching normalized title and credited artist overlap, and exactly one second of duration difference. It cannot include the remaining 256 REVIEW cases or 66 NOT_FOUND cases. The plan has 71 contiguous groups containing at most six occurrences.

The new journal is `reports/tidal-maintenance/duration-one-second-repair-local.json`. The 609-replacement journal is read only and remains intact. The new journal records a full pre-write snapshot and each insertion response and deletion state. The existing insert-before, occurrence-specific delete, duplicate preservation, concurrency marker and item-count checks apply. Final verification compares the entire ordered sequence of track IDs and occurrence IDs, including all unselected items.

Keep the Mac awake and avoid editing Best Classical during execution. The API operations are not an atomic transaction. Success prints `status: passed`, `replaced_occurrences: 108`, `final_item_count: 5518` and `order_verified: true`. No user OAuth token is persisted. The remote development session cannot execute the source writes without the local user login.

If stopped or interrupted, preserve both journals; do not delete the new journal and retry. The script refuses to repeat a batch whose journal exists because an uncertain write may already have reached TIDAL. Reconcile the logged request states against a fresh snapshot before further writes.

Validation: all 25 focused scanner, disposable pilot and repair tests passed, including the new 108-item batch, preservation of unselected occurrences and the prior journal, exclusion of other mismatches, stale post-609 snapshots, unsuccessful prior journals and a candidate whose duration changed to two seconds. The actual report was checked against a simulated post-609 snapshot to confirm exactly 108 selections and 71 groups. Standalone script syntax was checked for Python 3.9 compatibility. These checks do not constitute a live execution of the 108 replacements.
