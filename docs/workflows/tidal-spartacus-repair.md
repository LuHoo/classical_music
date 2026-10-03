# Approved Spartacus replacement batch

On 3 October 2026 Lucas approved replacement of the 29 Best Classical occurrences at original positions 1217–1245. He supplied the new album URL https://tidal.com/album/285244428/u. The verified scan already contains the proposed individual replacement IDs. Direct retrieval of the album page was unavailable, so this approval is implemented against those exact track candidates rather than an unverified album-wide import.

The original and candidate tracks have identical ISRCs across all 29 occurrences. Movement titles and sequence are identical after removing the relocated `Spartacus`, Grigorovich arrangement and 1968 Bolshoi version labels. Seventeen durations are identical and twelve are one second longer. Original credits contain RIAS Kammerchor; candidate credits additionally name Deutsches Symphonie-Orchester Berlin and Michail Jurowski. All 29 were REVIEW cases because the title layout changed; none belongs to the separately approved 108 one-second-only cases.

Run from the same Mac worktree:

```sh
git fetch origin issue-64-tidal-link-maintenance
git merge --ff-only origin/issue-64-tidal-link-maintenance
python3 scripts/tidal_playlist_login.py --client-id ldZgGfK4yL66Llw9 --repair-spartacus
```

This command applies only the 29 approved Spartacus occurrences. It can run after the 609 batch or after both the 609 and 108 batches. For either additional batch, the repair runner now selects the latest successful local journal by its completion timestamp; any existing incomplete journal blocks execution until reconciled. This also allows the 108 batch to run after Spartacus. The full current snapshot must match the selected prior final snapshot, including track order, occurrence IDs and modification marker. No prior journal is overwritten.

A fresh catalogue search must still identify exactly one streaming NL candidate per original ISRC with the approved track ID. The candidate's movement text must match after the specific label relocation, its artist credits must overlap, and its duration must equal the original or be exactly one second longer. The approved group contains precisely positions 1217–1245 and no other REVIEW tracks. Candidate title changes beyond the approved formatting difference stop the batch.

The 29 occurrences form one insertion group. After checking the insertion response and the new occurrence IDs, only the 29 original occurrence IDs are removed. The final full ordered snapshot is verified. The new local journal is `reports/tidal-maintenance/spartacus-repair-local.json`; success prints `replaced_occurrences: 29`, `final_item_count: 5518`, `order_verified: true` and `status: passed`. Keep the Mac awake and avoid concurrent playlist edits. If stopped, preserve the journal and do not retry by deleting it. This process is not an atomic transaction and does not guarantee re-addition of unavailable original tracks.

Validation: all 28 focused tests passed, including a full 29-occurrence replacement, preservation of unaffected occurrences, refusal of a changed movement or larger duration difference, selection of the latest successful journal and refusal of incomplete prior repair journals. The real report was checked against a simulated post-609 snapshot: exactly 29 occurrences, one group, positions 1217–1245. Python 3.9 syntax compatibility was checked. Publication does not execute TIDAL writes; local user OAuth is required.
