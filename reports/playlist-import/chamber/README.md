# Chamber — complete source intake

All **1,368 source occurrences** from the complete 4 October 2026 [snapshot](https://github.com/LuHoo/classical_music/actions/runs/37201308716) are accounted for. The playlist ends at position 1368; there is no unprocessed tail. Source duration: 137h 53m 36s. The curator explicitly authorised one full-playlist import.

| Result | Work/recording groups | Source occurrences |
|---|---:|---:|
| import_new | 293 | 935 |
| reuse_existing | 92 | 318 |
| recommendation_choice | 21 | 66 |
| not_selected | 1 | 3 |
| identity_unresolved | 18 | 46 |

New canonical records: {'persons': 27, 'work-groups': 279, 'works': 291, 'performances': 293}. Reuse covers 91 existing Performances. Groups are not unique Work counts: separate versions, alternative readings and two reused Brahms song excerpts are counted separately.

## Curator choices

**12 pending Work-level decisions**; eight original/arrangement decisions have been implemented with explicit profiles. Respond in an issue or the import chat with the issue number plus a C-code (or `existing`, `geen`, `unresolved` where offered). One answer covers all movements. A short explanation is needed only for doubt, exceptions or an additional comparison profile.

Undecided alternatives are excluded from canonical Performance data. Accepted originals and arrangements occupy distinct explicit profiles; existing listening links remain unchanged. Neither playlist order nor ISRC similarity selects a preferred interpretation. An issue is not permission to apply a choice automatically.

| Issue | Composer — Work | Candidates |
|---|---|---|
| [#240](https://github.com/LuHoo/classical_music/issues/240) | Arthur Bliss — Clarinet Quintet, F. 20 | C003, C287 |
| [#242](https://github.com/LuHoo/classical_music/issues/242) | Johannes Brahms — Piano Quartet No. 3 in C Minor, Op. 60 | C035, C400; existing |
| [#243](https://github.com/LuHoo/classical_music/issues/243) | Johannes Brahms — Piano Quartet No. 2 in A Major, Op. 26 | C036, C401; existing |
| [#244](https://github.com/LuHoo/classical_music/issues/244) | César Franck — Violin Sonata in A Major, FWV 8 | C069, C098  **Resolved: both, distinct profiles** |
| [#245](https://github.com/LuHoo/classical_music/issues/245) | Camille Saint-Saëns — Le Carnaval des Animaux, R. 125 | C073; existing  **Resolved: both, distinct profiles** |
| [#246](https://github.com/LuHoo/classical_music/issues/246) | Jacques Ibert — Trois pièces brèves | C093, C372 |
| [#247](https://github.com/LuHoo/classical_music/issues/247) | Albert Roussel — Divertissement, Op. 6 | C108, C325, C331 |
| [#248](https://github.com/LuHoo/classical_music/issues/248) | Arnold Schoenberg — Verklärte Nacht, Op. 4 (Steuermann piano trio arrangement) | C170, C278 |
| [#249](https://github.com/LuHoo/classical_music/issues/249) | Johann Sebastian Bach — Violin Sonata No. 3 in C Major, BWV 1005 (Excerpts Arr. J. Lindberg for Lute) | C204, C359; existing  **Resolved: both, distinct profiles** |
| [#250](https://github.com/LuHoo/classical_music/issues/250) | Johann Sebastian Bach — Violin Sonata No. 1 in G Minor, BWV 1001 (Arr. J. Lindberg for Lute) | C207, C361; existing  **Resolved: both, distinct profiles** |
| [#251](https://github.com/LuHoo/classical_music/issues/251) | Johann Sebastian Bach — Violin Partita No. 2 in D Minor, BWV 1004 | C208, C363; existing  **Resolved: both, distinct profiles** |
| [#241](https://github.com/LuHoo/classical_music/issues/241) | Wolfgang Amadeus Mozart — Serenade in C Minor, K. 388 | C210, C298 |
| [#252](https://github.com/LuHoo/classical_music/issues/252) | Igor Stravinsky — Octet | C230, C307; existing |
| [#253](https://github.com/LuHoo/classical_music/issues/253) | César Franck — Piano Quintet in F Minor, FWV 7 | C276, C364 |
| [#254](https://github.com/LuHoo/classical_music/issues/254) | Bohuslav Martinů — Cello Sonata No. 1, H. 277 | C282, C337 **Resolved: C337** |
| [#255](https://github.com/LuHoo/classical_music/issues/255) | Bohuslav Martinů — Cello Sonata No. 2, H. 286 | C284, C339 |
| [#256](https://github.com/LuHoo/classical_music/issues/256) | Bohuslav Martinů — Cello Sonata No. 3, H. 340 | C286, C340 |
| [#257](https://github.com/LuHoo/classical_music/issues/257) | Igor Stravinsky — Concerto in E-Flat Major, K060 "Dumbarton Oaks" | C302; existing |
| [#258](https://github.com/LuHoo/classical_music/issues/258) | Johann Sebastian Bach — Goldberg Variations, BWV 988 | C402; existing  **Resolved: both, distinct profiles** |
| [#259](https://github.com/LuHoo/classical_music/issues/259) | Johann Sebastian Bach — Orchestral Suite No. 3, BWV 1068 | C406; existing  **Resolved: both, distinct profiles** |
| [#260](https://github.com/LuHoo/classical_music/issues/260) | Johann Sebastian Bach — Keyboard Concerto No. 5, BWV 1056 | C417; existing  **Resolved: both, distinct profiles** |

## Evidence gaps

18 groups remain outside canonical data pending source/version research. These are **authority_evidence_required**, not demands for listening decisions. [Research issue #261](https://github.com/LuHoo/classical_music/issues/261) and [concrete research list](identity-research.md). All raw titles, artists, track IDs, ISRCs, positions and reasons are in the [machine-readable manifest](snapshot-2026-10-04.json). No decision or track is silently dropped.

## Traceability and limits

- The live snapshot is authoritative for membership and order. The older spreadsheet is corroborating Work evidence, joined by exact ID or unique ISRC; it does not supply 2026 positions.
- Duplicate occurrences and non-adjacent movements are preserved. Raw titles remain beside reviewed identities. Excerpts are explicit; unselected album tracks are not inferred.
- Attribution corrections include Bartók’s solo violin sonata and Koechlin’s nocturnes. Label/artist evidence corrects the Webern arrangement of Schönberg Op. 9; specific arrangements and reconstructions receive their own Works within the known family.
- Exact trusted tracks/ISRCs, and documented same-release matches with compatible Work identity, support reuse. The manifest retains that evidence, including older anchors that point to another Work on the same album. These anchors are not silently rewritten by this import.
- NL usage-rule evidence is retained separately from musical acceptance. No successful playback is claimed. This import does not alter the Tidal playlist.
- Source artifact is not committed. The manifest preserves identifiers and source fingerprints without API credentials.

## Verification

Run `python scripts/check_chamber_import.py` for full occurrence coverage, one-recommendation gates, canonical references and generated public links/excerpts. Run the canonical validator and test suite as usual. See [review and validation notes](review.md).

## Original and arrangement decisions — 4 October 2026

Lucas extended the decision in #287 to other original/arrangement comparisons. Issues #244, #245, #249–#251 and #258–#260 are resolved in `resolved_choices`, with decision-comment URLs, explicit profiles, all source tracks and unchanged excerpt coverage. [Implementation report](../../curator-decisions/original-arrangement-2026-10-04.json) also covers the seven Mendelssohn Piano decisions (#286–#292). Undecided comparisons within the same profile remain pending.

## C337 decision — 5 October 2026

Issue #254 selects Vilém Vlček and Denis Linnik for all three movements of Martinů’s Cello Sonata No. 1, H. 277. C282 remains traceable as not selected. See the [decision record](../../curator-decisions/c337-2026-10-05.json).
