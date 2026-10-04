# Chamber import review

## Scope and decisions

Reviewed the complete source from run 37201308716 against `main` at `f03bf06`.
All 1,368 live occurrences are retained, including non-adjacent movement groups;
there is no unprocessed suffix. The source has 1,368 distinct track IDs. The older
spreadsheet is joined by identity, not row position. All retained raw track IDs,
item IDs, ISRCs, titles, artists, durations and albums were compared back to the
fetched snapshot.

The import adds 283 accepted Performances and reuses 91 existing Performances
across 92 groups. It creates 291 Works, 279 Work Groups and 27 composer Persons.
It does not edit or delete existing canonical records. 32 alternative-performance
groups covering 91 tracks are withheld behind 21 Work-level curator issues
(#240–#260). A further 18 source/version cases covering 46 tracks are retained
in the concrete research list in #261. These are explicit unresolved intake,
not accepted recommendations or silently skipped tracks.

## Adversarial identity review

- Compared each candidate against canonical Work/catalogue and recording
  references before writing. Repeated performers alone did not establish reuse.
  Trusted tracks, exact ISRC joins, and corroborated same-album/compatible-Work
  matches are retained in each reuse unit's `recording_evidence`.
- Checked plausible new-vs-existing title collisions independently of the initial
  catalogue matcher. The additional Lutosławski Dance Preludes family collision
  was resolved: the 1954 clarinet/piano Work shares the existing family with the
  1955 orchestral version. Publisher evidence supports the distinct versions.
- Corrected source misattributions (Bartók solo violin sonata, Koechlin nocturnes)
  and the Steuermann/Webern arranger error in the Schönberg Op. 9 tracks using
  independent evidence. Raw source titles remain in the manifest.
- Separated Barber's discarded original finale from the revised quartet and
  labelled it as an excerpt. No unselected movements were added. Also checked
  Bach recital fragments, Brahms song excerpts and Stravinsky's incomplete Octet.
- Kept known artistic versions distinct (including the Kenner–Dombek Chopin
  reductions, Linos arrangements, Loeffler reconstruction and Triebensee suite).
  Practical transcriptions of an existing Work remain comparison candidates;
  a profile exception requires an explicit curator decision.
- Reused compatible interpretations despite misleading legacy album-opening
  track anchors (including Beethoven quartets and Hindemith Op. 24/2). Those
  older anchors are documented, not silently modified by this import.
- Preserved unresolved questions about mixed adaptations, early opus numbering,
  incomplete source credits and unclear Work boundaries outside canonical data.
  Research must repeat the collision check before any later import.

## Verification

- Canonical validator with all newly added IDs activated: **0 errors, 0 action
  required, 115 background warnings**. No remaining warning concerns a new ID.
- Import inventory audit: every source occurrence assigned exactly once; source
  identity fingerprint, canonical references, evidence requirements, explicit
  excerpts and all pending-choice gates checked.
- Public generation: all imported links and excerpt labels checked against the
  generated Work pages; canonical publication references pass validation.
- Regression tests cover accidental source deduplication, missing/changed source
  identities, wrong-Work reuse and an unapproved alternative entering canonical
  recommendations. Full-suite and Jekyll outcomes are recorded in the PR.

NL catalogue rules advertise subscription streaming for 1,058 occurrences;
310 have no subscription streaming rule. These are catalogue observations, not
playback tests, and do not override the user's musical acceptance. No OAuth
credentials, playback claims or Tidal writes are part of this import.
