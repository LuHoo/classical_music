# Best Classical: canonical import of 120 selected tracks

The curator authorised applying the prepared 33 Performances on 2026-10-02.
All 106 records from `prepared-120.yaml` have been installed under `data/`:
9 composer Persons, 32 Work Groups, 32 Works and 33 Performances.
Shostakovich's Violin Concerto No. 2 reuses its existing Work.

`imported-120.json` records the applied IDs, paths and verification results.
The preparation files remain unchanged as historical identification evidence;
their `prepared_not_imported` status describes that earlier step. The import
manifest is the current application status. Performance source references to
`prepared-120.json` intentionally preserve the original track-level provenance.

The canonical records match the approved proposal exactly. Existing canonical
files remain unchanged in this step. Each imported Performance and its selected
Tidal link is present in generated publication data. The partial Sibelius
Symphony No. 3 and Notre Dame selections retain their explicit excerpt labels.
Virtanen's Three Late Fragments remains the explicitly attributed realised set,
not a completed Sibelius Symphony No. 8. Poulenc's Concert champêtre retains
the piano profile.

Within playlist positions 34–333, the final disposition is:

| Disposition | Tracks | Performances |
|---|---:|---:|
| Existing recommendations, retained | 142 | 33 |
| New recommendations, now installed | 120 | 33 |
| Bruckner, deferred separately (279–315) | 37 | — |
| Boundary track 333, deferred separately | 1 | — |
| Total | 300 | |

No Bruckner entity is added or changed, and track 333 (Tidal ID 284454595)
is excluded. No additional album tracks are accepted. The original first-batch
three additions remain on this branch, giving 36 new Performances across the
draft PR. Empty API rights lists remain uncertainty rather than proof of
unavailability; the curator's reported playback is preserved as evidence.

Canonical and publication checks run against the actual repository after
installation. The full test suite and generated HTML/link checks run once in
the draft PR's GitHub Actions checks. The branch is not merged or deployed.
