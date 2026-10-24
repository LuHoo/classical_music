# Best Classical: read-only scale probe, positions 34–333

## Scope and evidence

Requested on 2026-10-02 at 17:01 Europe/Amsterdam. Exactly 300 playlist
occurrences after batch 001; no canonical files changed, no recommendations
accepted/replaced, no playback test. This is triage, not a completed import.

Source: https://tidal.com/playlist/c11f614b-c011-43b2-be10-639f5cf7e5e3

Live run: https://github.com/LuHoo/classical_music/actions/runs/37024628787

Reader commit: `4ca8eaeebfc5559288da197fb5639625c497a927`.
Artifact: `11234681152`, 333 ordered source occurrences, expires 2026-10-16.
Playlist modification marker remained `2026-10-02T12:06:31.897Z` before/after.
All first 33 track IDs and ISRCs independently agree with batch-001.json.
The extra prefix is boundary verification, not part of the 300-track analysis.

## Measurements

| Measurement | Result |
|---|---:|
| Selected positions | 34–333 |
| Tracks / distinct track IDs / distinct ISRCs | 300 / 300 / 300 |
| Repeated track occurrences within this window | 0 |
| Missing track titles / missing usage-rule resources | 0 / 0 |
| Provisional work/interpretation units | 77 |
| Units with an exact canonical track or album link anchor | 28 |
| Individual tracks with an exact canonical track link | 12 |
| Such tracks linked by multiple canonical Performances | 4 |
| NL subscription STREAM indicated | 261 |
| NL subscription STREAM not indicated (empty rights lists) | 39 |
| Live authentication + catalogue read | 40.87 seconds |
| Local index, grouping and candidate ranking | 8.99 seconds |

The API read ran from 15:06:41.758 to 15:07:22.627 UTC. The local timing
includes loading canonical YAML and title/performer shortlist ranking. It does
not include implementation, human-equivalent review, external identity research,
canonical writing or publication validation. End-to-end task time is separately
reported on handoff; it must not be confused with the 50-second machine path.

## Initial workload assessment

Manual review of the grouped titles against canonical composer/Work inventory
separates 32 units whose Works are absent, 35 units with recognisable existing
Work-level counterparts, and 10 Bruckner version/edition units requiring a
version-aware comparison. These are triage categories, not 77 certified distinct
Works or verified Performance decisions.

The 32 absent-Work units comprise Pärt's Tabula Rasa (1), Zemlinsky (3),
Bartók's Wooden Prince and Dance Suite (2), Sibelius (8), Schubert (2),
Martinů (2), Rachmaninoff (2), Geysir (1), Schmidt (5), Vaughan Williams (2),
and Poulenc (4). Canonical Pärt and Bartók Persons already exist; other composer
identities and the attribution of Geysir require confirmation before import.
Within the existing-Work category, Shostakovich Violin Concerto No. 2 is present
as a Work but has no canonical Performance: it is not an existing recommendation
to skip. Thus absent Works and absent Performances must be counted separately.

No new unit is labelled **import-ready**: this probe deliberately did not perform
the external authority, recording/session and coverage checks required for
canonical additions. The 28 link-anchored units are the best first verification
queue, not 28 automatically proven duplicates. Additional existing interpretations
can be recognised from album siblings and repository evidence, but that resolver
is not implemented here. Title ranking is only a shortlist and often produces
wrong first candidates; no score authorises a canonical write.

## Why the existing link index is insufficient

Four exact track IDs are shared by different Work recommendations:

| Source position | Canonical Performances sharing the source track link |
|---|---|
| 76 | Beethoven Symphonies 6, 7, 8 and 9 |
| 156 | Shostakovich Symphony 9 and Hamlet suite |
| 188 | Shostakovich King Lear, Festive Overture and Symphony 7 |
| 333 | Hindemith Kammermusik 1, 2, 3 and Kleine Kammermusik |

These are pre-existing source-link ambiguities, not four curator choices. Match
the Work/catalogue identity first, then the interpretation; a shared album/track
anchor is not movement coverage evidence. No legacy URL has been modified.

## Bounded review exceptions

- Alternating vocal soloists and changing artist order fragmented the initial
  grouping into 117 units. Grouping by album + provisional Work stem, with two
  explicitly source-specific grouping corrections, reduces this to 77. This
  demonstrates why one track or one artist tuple cannot equal one Work.
- Sibelius's three late fragments explicitly name Virtanen's completion. Do not
  turn them into an ordinary symphony using a general-Work fallback.
- Bruckner units preserve WAB, version and edition labels. Positions 303–306 and
  position 307 have different source labels; the latter is the Volksfest finale,
  not evidence of a complete second performance. Composer revision/edition
  identity remains unresolved until the authority comparison is made.
- Shostakovich Lady Macbeth contributes only Passacaglia; King Lear contributes
  selected incidental music. Parent Work and excerpt handling must be checked.
- Position 333 begins Hindemith Kammermusik No. 1. The 300-track boundary cuts
  this group; do not label the recommendation complete or infer later selections.
- Thirty-nine tracks have empty NL usage-rule rights, not missing resources.
  This means STREAM availability is not established for the configured app and
  country. It does not prove universal unavailability or invalidate curation.

## Scaling conclusion

API retrieval and a single local catalogue pass are not the bottleneck. At this
sample's ratio, 3,000 musical units correspond to roughly 11,700 source tracks;
that is an illustration, not an estimate of the user's actual playlist sizes.
The present reader remains bounded to 500 prefix items and is not a resumable
whole-library importer. Linear API extrapolation is not a delivery-time promise.

The expensive step is identity/coverage/recording verification for missing or
ambiguous units. A defensible total import estimate cannot be derived from a
read-only probe without measuring a representative set of those cases. The
next implementation should use one reusable inventory, cached recording evidence,
version-aware Work resolution and aggregated exceptions. Do not repeat a full
test/publication build per ten Works, nor do independent web research for each
movement. No additional import or research batch is started by this report.

## Reproduction

Run `scripts/analyse_tidal_scale.py <source.json> --output
reports/tidal-playlist/scale/triage.json` from this branch. Raw source and generated
triage remain ignored; the retained compact inventory is scale-300-inventory.json.
The script's two position-based grouping corrections apply only to this verified
Best Classical snapshot. It is not a general-purpose musicological resolver.
