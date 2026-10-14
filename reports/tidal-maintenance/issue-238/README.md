# Issue #238 — curator decisions and execution

The curator decided once per work/interpretation in issue #238 and its linked conversation. These records implement those decisions, not a new automatic recommendation policy.

## Scope and reconciliation

- `decisions.csv`: all 322 exact source occurrences (256 REVIEW + 66 NOT_FOUND), including the 29 previously repaired Spartacus occurrences. Decisions: 248 replace, 60 remove-recommendation, 14 remove. The 108 one-second repairs are excluded.
- `work-decisions.json`: W01–W104, 293 new occurrences, exact original/candidate metadata, curator decision, import provenance and canonical outcome per group. The earlier 29-track Spartacus batch is separately identified; it is not executed again.
- Source scan is pinned at commit `a1746134252c56ff0dc68afe9b45c8ef9168c498`, linked in the JSON. Original positions identify source cases, never substitute for occurrence IDs in writes.
- Every group has a curator decision. Execution holds are separate from decisions; they do not turn into automatic replacements or new curator questionnaires.

## Verified live result

On 2026-10-04 the authorized run finished successfully: 217 replacements and 14 removals; 5,539 → 5,525 items. Full occurrence/order comparison verified all 5,308 unaffected items, including the 21 appended items and the earlier 29 Spartacus repairs. `execution-summary.json` records timings, exact operations, inserted occurrence IDs and snapshot hashes without authentication material or a private full-playlist dump.

All 322 cases are accounted for: 217 newly repaired + 29 prior repairs verified + 14 playlist removals + 48 track cases covered by 21 canonical recommendation removals + 12 cases with no canonical recommendation + 2 identity holds.

## Canonical changes

48 existing Performance links are updated, preserving all other fields. 21 specifically rejected Performances are removed. All Persons, Works and Work Groups remain unchanged. A Performance is the recommendation in this repository; there is no separate recommendation flag.

Some selected tracks are internal movements rather than a Performance's entry link, or already point to a repaired entry track. These require no canonical URL edit. Other groups were never accepted into canonical Performances; their removal decision is a documented no-op, without promoting import candidates. Historical import reports remain historical evidence.

`remove` at W09–W12 authorizes the 14 exact Martinů playlist occurrences only. `remove-recommendation` never authorizes playlist deletion. W99 has no accepted RSNO/Lloyd-Jones Performance to delete; the Manze recommendation in `docs/holst.md` is preserved.

## Identity checks and holds

- **W22 — authority_evidence_required, one occurrence.** Old 12663453 names movement III, candidate 284435952 names IV; both last 7:28. The [label/distributor catalogue ODE921-2](https://www.naxos.com/CatalogueDetail/?id=ODE921-2) assigns approximately 7:25 to III and 5:06 to IV. This supports a candidate metadata problem, but does not independently prove its audio content. Do not replace this occurrence until the recording/movement is verified. Existing canonical link is preserved.
- **W64 — authority_evidence_required, one occurrence.** Old 24018641 is Dresden/Thielemann, 8:50; candidate 285159847 is credited to Sofia/Tabakov/Dikov, 9:36. Trusted import provenance and the [Dresden orchestra's discography, Edition vol. 34](https://www.staatskapelle-dresden.de/fileadmin/home/Archiv/pdf/Konzertplan/Konzertplan_Kapelle_2019-20_Web.pdf) support Dresden/Thielemann for the old recording. Equal ISRC is insufficient to prove the candidate is the same interpretation. Existing link and playlist occurrence are preserved pending authoritative candidate/audio verification.
- **W60 — resolved without curator work.** The [Chandos CHAN 10245 booklet, printed track list](https://www.chandos.net/chanimages/Booklets/CH10245.pdf) identifies tracks 8–10 as Piano Concerto No. 2 with Howard Shelley/BBC Philharmonic/Bamert. The old James Ehnes credit and import report's violin-concerto association are misleading album-level metadata. Candidate titles and timings match the piano concerto (booklet finale 7:45; both streaming versions 7:47). No violin Performance is repointed and no new canonical Performance is created.
- **W14/W15.** The [Ondine ODE740-2 catalogue](https://www.ondine.net/index.php?cid=2.2&lid=en&oid=2192) supports the Pommer/Leipzig symphonies and movement lengths; erroneous old durations do not justify changing Work identity. Curator-approved replacement keeps the existing interpretation.
- W31 and W89: wrong-work candidates are rejected by removal of the exact existing recommendation, never used as replacement URLs.

## Adversarial self-review

URL equality alone is not a work/interpretation match. W34's old concerto URL also occurs on an unrelated Hindemith Quartet recommendation; that Quartet is retained. W65's old Symphonic Dances URL also occurs on Pittsburgh Symphony and Ragtime legacy recommendations; those unrelated records are retained. Both canonical representations of the same approved Seattle/Schwarz complete Nobilissima visione recording receive the approved link repair, without identity restructuring.

Checks against independent inputs: all 322 CSV rows reconciled to pinned scan occurrence IDs and issue decisions; all 293 grouped rows equal the original source metadata; every replacement target equals the curator's selected candidate. Canonical before/after comparison confirms only Tidal URLs change in 48 files; each of the 21 removed Performances retains its Work. Other canonical files and the Manze source recommendation remain unchanged.

The local execution script is one-shot: fresh stable playlist snapshot, comparison to last successful repair (allowing appended tracks only), exact occurrence matching, fresh NL STREAM/ISRC/title/duration/artist checks against the approved candidate, backup before writes, insert-and-verify before deletion, modification-marker checks, refusal to repeat an existing journal, and full final order/occurrence comparison. No login token is persisted. Five fake-client tests cover the successful 217-replacement/14-removal run (including appended-track preservation), refusal on playlist drift, refusal on candidate drift, preservation of originals after an invalid insertion response, and stopping on concurrent modification. Full private snapshots and OAuth runtime files are not committed.

## Validation

Generated Work pages were independently checked: all 48 new URLs are present, all 21 removed recommendation links are absent, and all affected Work pages still exist.

Validation results and final live execution counts are recorded in the PR and the companion execution summary. Remaining identity investigations are two authority gates, not requests for the curator to repeat decisions. Issue #238 must remain open until these execution exceptions have been resolved or explicitly accepted.

## Architecture preflight

Read against `docs/architecture/architecture-principles.md`, `performance.md`, `recommendation-policy.md`, `repository-architecture.md`, `minimal-yaml-schemas.md` and `docs/workflows/candidate-review.md`. Scope is existing recommendation/link maintenance only, on a dedicated branch from current main. No Person/Work identities or new recommendation policy are introduced. Canonical edits are the curator's durable changes; source fingerprints, mappings and execution evidence remain reports. Authority lookup is limited to the consequential recording conflicts. Success means exact curator intent applied, no known wrong recording selected, no repeated per-track decisions, and every exception visible.
