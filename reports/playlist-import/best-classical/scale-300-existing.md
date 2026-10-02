# Best Classical: existing-Performance review of positions 34–333

The curator authorised step 1 only on 2026-10-02 at 18:17 Europe/Amsterdam,
with a maximum 15-minute budget. This report completes duplicate triage using
the retained live source. No new API read, external recording search, canonical
addition/replacement, link repair, or full publication build was needed.

Main was checked remotely and remained `f3c1e24faf0dfc4edada28bbcd6fa77245ca7de9`.
The raw source SHA-256, exact track IDs/ISRCs, canonical target IDs, original URLs,
album relationships, performers and repository evidence pointers are retained
in `scale-300-existing.json`. Source run:
https://github.com/LuHoo/classical_music/actions/runs/37024628787

## Decisions

| Outcome | Units | Selected tracks |
|---|---:|---:|
| Existing interpretation confirmed; skip creating a duplicate | 33 | 142 |
| Absent Work; composition/recording identity still needs import review | 32 | 117 |
| Existing Work without a canonical Performance: Shostakovich Violin Concerto 2 | 1 | 3 |
| Bruckner version/edition comparison reserved for step 3 | 10 | 37 |
| Hindemith Kammermusik 1 starts at the last selected track; boundary deferred | 1 | 1 |
| **Total** | **77** | **300** |

Fourteen of the 33 confirmed existing interpretations have their own canonical
track URL inside the selected movement group, with compatible Work/catalogue
and performer evidence. Nineteen use an explicit matching canonical album URL
or a canonical anchor track whose source relationship resolves to the same album.
The trusted recommendation supplies Work and interpretation identity; the album
association supplies release evidence. Same title/performer names alone were
never treated as proof of the same recording. No fuzzy ranking was accepted as
a decision. Every selected group's catalogue number, where canonical metadata
provides one, was checked against its source title.

The source prefix deliberately supplies only the selected tracks. Skipping a
duplicate means its accepted interpretation already exists; it does not assert
that all parent-Work movements are selected. No album sibling outside the
playlist is imported or treated as accepted curation.

## Confirmed existing interpretations

| Positions | Work | Interpretation |
|---|---|---|
| 70–72 | Mozart Piano Concerto 9, K.271 | Lars Vogt / Orchestre de Chambre de Paris |
| 73–75 | Mozart Piano Concerto 24, K.491 | Lars Vogt / Orchestre de Chambre de Paris |
| 76–80 | Beethoven Symphony 6, Op.68 | Le Concert des Nations / Jordi Savall |
| 81–84 | Beethoven Symphony 7, Op.92 | Same |
| 85–88 | Beethoven Symphony 8, Op.93 | Same |
| 89–95 | Beethoven Symphony 9, Op.125 | Same |
| 140–146 | Mozart Gran Partita, K.361 | Mark Simpson and ensemble |
| 147–150 | Shostakovich Symphony 1, Op.10 | Boston Symphony Orchestra / Andris Nelsons |
| 151–155 | Shostakovich Chamber Symphony, Op.110a | Same |
| 156–160 | Shostakovich Symphony 9, Op.70 | Same |
| 161–166 | Shostakovich Hamlet suite, Op.32a | Same |
| 167–171 | Shostakovich Symphony 8, Op.65 | Same |
| 172 | Shostakovich Lady Macbeth: Passacaglia, Op.29 | Same; excerpt, not complete opera |
| 173–176 | Shostakovich Symphony 10, Op.93 | Same |
| 177–178 | Shostakovich Symphony 2, Op.14 | Same |
| 179–182 | Shostakovich Symphony 3, Op.20 | Same |
| 183–187 | Shostakovich Symphony 13, Op.113 | Same; source also credits Matthias Goerne and choruses |
| 188–198 | Shostakovich King Lear incidental music, Op.58a | Same; selected incidental music |
| 199 | Shostakovich Festive Overture, Op.96 | Same |
| 200–203 | Shostakovich Symphony 7, Op.60 | Same |
| 204–207 | Shostakovich Violin Concerto 1, Op.77 | Ibragimova / Svetlanov orchestra / Vladimir Jurowski |
| 236 | Berlioz Francs-juges overture, Op.3 | Les Siècles / François-Xavier Roth |
| 237–243 | Prokofiev Alexander Nevsky, Op.78 | Borodina / Mariinsky orchestra and chorus / Gergiev |
| 244–247 | Prokofiev Symphony 1, Op.25 | Gürzenich-Orchester Köln / Dmitri Kitayenko |
| 248–251 | Prokofiev Symphony 7, Op.131 | Same |
| 252–259 | Prokofiev Symphony 2, Op.40 | Same |
| 260–263 | Prokofiev Symphony 3, Op.44 | Same |
| 264–267 | Prokofiev Symphony 4, original version, Op.47 | Same |
| 268–271 | Prokofiev Symphony 4, revised version, Op.112 | Same |
| 272–275 | Prokofiev Symphony 5, Op.100 | Same |
| 276–278 | Prokofiev Symphony 6, Op.111 | Same |
| 316–319 | Mahler Symphony 1 | Czech Philharmonic / Semyon Bychkov |
| 332 | Hindemith Trauermusik | Geraldine Walther / San Francisco Symphony / Blomstedt |

## Adversarial identity review

Shared anchors were challenged explicitly rather than assigned by the first
track of an album. For Beethoven 6–9, source album 213891369 identifies the
four-symphony release; matching Op.68/92/93/125 and the trusted Savall recommendations
resolve the groups despite a reused canonical Symphony-6 anchor. Similarly,
Shostakovich's Symphony 9 versus Hamlet (album 77611684), and King Lear versus
Festive Overture versus Symphony 7 (album 104156165), resolve by Work/catalogue
plus the same released Nelsons interpretation. Prokofiev's original Op.47 and
revised Op.112 Symphony 4 remain separate Works and both already have their
matching Kitayenko recommendations on album 285264999.

Catalogue and title discrepancies were checked against actual canonical Work
records, not only filename slugs. The Mozart K.491 canonical title currently
says **C major**, while the source explicitly says **C minor**. Its exact track
307469361, K.491 and Vogt/Paris evidence establish the existing interpretation;
the title defect is recorded separately, without changing canonical data in
this read-only step. Do not confuse this with K.271's harmless flattened slug:
that Work's actual canonical title correctly contains E-flat.

The King Lear and Lady Macbeth matches do not assert complete Work coverage.
Their current public excerpt metadata may deserve a later review, but a duplicate
recommendation is not the remedy. Canonical abbreviations, legacy spelling and
combined performer fields were checked against the trusted source and exact
release; no new Person was created for those textual differences.

Bruckner's ten version/edition units remain outside these 33 decisions. For
example, the canonical ORF/Poschner Symphony-4 general title has a date_text
of 1874–1876, while the selected source labels include 1888, second version and
Volksfest. No generic composer/title match was promoted across that conflict.
Likewise, the four Hindemith recommendations sharing track 284454595 do not
turn position 333 into four selected Works; Kammermusik 1 remains the boundary
case until its selected continuation is available.

## Availability correction and remaining work

The curator reports that all 39 tracks with empty API rights were playable from
the existing playlist. Their status is **API rights disagree with reported
playback**, not **unavailable in NL**. This is not an import blocker. Operational
availability remains outside canonical data.

The next authorised phase has not started. Step 2 would review the 32 absent
Work units and the three tracks of Shostakovich Violin Concerto 2 (120 tracks
in total). Step 3 handles the 37 Bruckner tracks; position 333 remains deferred.
There are no curator comparison choices established by this duplicate review.

## Verification

The evidence audit checks all 33 canonical Performance/Work references, exact
catalogue compatibility, matching release anchors, all 142 track ID/ISRC pairs,
disjoint ranges and a complete 300-position partition. Main stayed unchanged.
No file under `data/` changes in this follow-up. The prior full publication tests
are not repeated for report-only decisions, and no general matching engine is
claimed or shipped by this step.
