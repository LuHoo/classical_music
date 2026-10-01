# Prokofiev curator-on-demand alignment review

This is a non-destructive policy classification of the 33 unresolved alignment records.
Existing canonical Works are trusted legacy input. No MBID or canonical YAML is written by this report.

## Summary

- Automatically resolved / safely classified: 7
- Unchanged because local identity is clear but authority coverage is absent or insufficient: 26
- Background suspicions: 0
- Genuine consequential curator decisions: 0

## Architecture pre-flight

- `docs/architecture/architecture-principles.md` governs this classification, together with the normative Work, Work Group, migration, and validation documents.
- The repository is a curated collection and canonical source of truth, not a MusicBrainz mirror.
- Existing canonical Prokofiev Works are trusted legacy input; missing external identifiers are not defects by themselves.
- Work identity follows the local Work and Work Group model, not MusicBrainz completeness.
- Revisions remain separate Works; a missing Op. 136 authority record does not inherit Op. 40.
- A recognised suite, film score, arrangement, or other distinct artistic object is not collapsed solely because titles match.
- Authority IDs are added only for reliable unambiguous matches; unresolved or missing coverage remains outside canonical data.
- Performances remain attached to exactly one Work; this report does not create Recording or Release entities.

## Decisions

| Local Work | Status | Decision | Reason |
| --- | --- | --- | --- |
| `sergei-prokofiev-alexander-nevsky-work` | `automatically_resolved` | `retain_as_distinct_local_work` | Source identifies the 1939 cantata separately from the 1938 film score. |
| `sergei-prokofiev-alexander-nevsky-2-work` | `automatically_resolved` | `retain_as_distinct_local_work` | Source identifies the 1938 film score separately from the 1939 cantata. |
| `sergei-prokofiev-lieutenant-kije-work` | `automatically_resolved` | `retain_as_distinct_local_work` | Source identifies the film score and separately names its orchestral suite. |
| `sergei-prokofiev-symphony-no-2-in-d-minor-revised-version-work` | `automatically_resolved` | `retain_as_distinct_local_work` | Architecture requires composer revisions to remain separate Works; missing Op. 136 authority coverage does not justify inheriting Op. 40. |
| `sergei-prokofiev-war-and-peace-suite-work` | `automatically_resolved` | `retain_as_suite_work` | The local title explicitly identifies a suite; authority absence does not justify assigning the opera Work. |
| `sergei-prokofiev-on-the-dnieper-work` | `automatically_resolved` | `safe_candidate_not_written` | The Op. 51 title and catalogue match; nearby sections and Op. 51bis are excluded from canonical writing. |
| `sergei-prokofiev-peter-and-the-wolf-work` | `automatically_resolved` | `safe_candidate_not_written` | The Op. 67 title and catalogue match; narrative sections are not the parent Work. |
| `sergei-prokofiev-ala-i-lolli-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-american-overture-2-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-american-overture-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-andante-from-piano-sonata-no-4-arranged-for-orchestra-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-andante-from-string-quartet-no-1-arranged-for-string-orchestra-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-cantata-for-the-20th-anniversary-of-the-october-revolution-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-kotovsky-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-le-pas-d-acier-the-steel-step-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-lermontov-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-piano-concerto-no-6-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-scythian-suite-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-2-from-romeo-and-juliet-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-3-from-romeo-and-juliet-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-from-chout-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-from-egyptian-nights-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-from-on-the-dnieper-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-from-semyon-kotko-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-from-the-gambler-four-portraits-and-denouement-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-suite-from-the-love-for-three-oranges-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-symphonic-march-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-the-partisans-in-the-ukrainian-steppes-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-thirty-years-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-tonya-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-two-poems-for-female-chorus-and-orchestra-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-urals-rhapsody-from-the-tale-of-the-stone-flower-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |
| `sergei-prokofiev-vocal-suite-from-the-fiery-angel-work` | `unchanged_authority_gap` | `leave_unchanged` | Existing canonical Work is trusted; missing MusicBrainz coverage is not identity evidence. |

## Curator decisions

None. The remaining 33 records contain no consequential unresolved identity decision after applying the architecture and local source evidence.
