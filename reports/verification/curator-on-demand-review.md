# Curator-on-demand validation review

Date: 2026-08-26

## Result

Canonical validation remains strict for errors and referential/domain invariants. Duplicate and similarity detection remains available, but findings in trusted existing data are classified as `background_suspicion` unless an identity-changing workflow explicitly activates an entity ID as an identity gate.

Current repository counts:

| Finding class | Count |
| --- | ---: |
| Action required | 0 |
| Background suspicions | 115 validator findings; 74 authority clusters |
| Automatically resolved/classified duplicate clusters | 30 |

The duplicate report contains 36 Work Group clusters (21 automatically resolved, 15 background) and 38 Work clusters (9 automatically resolved, 29 background). The previous report exposed the 15 and 29 background clusters as manual review. They are now deferred and do not fail CI or create Issues.

## Before and after

The previous duplicate-review artifact classified 15 Work Group and 29 Work clusters as manual review. The new default classification is 0 active curator decisions and 44 deferred background clusters. Explicit activation through `--identity-gate-id` promotes only the selected changed entity's cluster to `action_required`.

The validator's existing 115 duplicate warnings remain visible and non-blocking. Structural errors still return a failing exit code. Missing external authority identifiers on existing coherent Works are not made actionable by this change.

## Review of PR #138

- Duplicate classification: needs modification. The deterministic candidate discovery and authority-aware evidence are useful, but same composer plus title is only a suspicion for trusted legacy data. Escalation is now demand-driven.
- MusicBrainz authority lookup: still valid as evidence for new, changed, merged, split, or explicitly activated identity decisions. Complete MusicBrainz coverage is not a repository requirement.
- Stravinsky catalogue handling: still valid where the authority/catalogue evidence resolves a namespace conflict. Remaining unresolved clusters are background unless activated.
- Hindemith authority matching: still valid as evidence and deterministic classification. It does not turn absent authority IDs on existing Works into curator tasks.
- Arrangement handling / issue #142: needs modification. The current architecture says a practical transcription or performance variation does not automatically create a Work, but a recognised distinct arrangement, orchestration, transcription, completion, or revision may be a separate Work. PR #138's Beethoven removals cannot be justified solely by the rule "arrangements do not create Works".
- Work Group duplicate handling: needs modification. Similar Work Groups are lower-risk navigation suspicions when Work identities are clear and are background by default.
- Remaining `needs_authority_review` clusters: do not resolve them wholesale. They are automatically classified where deterministic evidence is sufficient, background when they affect trusted unchanged data, and actionable only when an activated identity decision remains unresolved.

## Beethoven arrangement assessment

PR #138 removed Beethoven Work Group and Work records for several symphonies and reassigned performances to the surviving records. That is valid only where the removed records were merely practical instrumentation/performance variants and the surviving Work is the intended artistic object. It is not a generally valid consequence of the word arrangement. Each affected record should be checked against the Work identity rules, source evidence, and performance context before any further canonical deletion. This branch makes no additional Beethoven data deletion or restoration.

## Operational policy

Use `scripts/validate_data.py --identity-gate-id ENTITY_ID` from an identity-changing workflow when a new or changed entity collides with an existing entity. Use the duplicate report for deferred investigation. Background suspicions must not create GitHub Issues automatically; an Issue represents an explicitly activated editorial decision.

## Verification

- `python3.11 -m pytest -q`: 9 passed.
- `python3.11 scripts/generate_duplicate_review.py`: completed.
- `python3.11 scripts/validate_data.py --json`: 0 errors, 115 warnings, 0 active identity decisions.
