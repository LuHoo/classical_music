# Implementation Note: Issue #164 Reproducible Migration

## Architecture Pre-flight

This update was checked against `docs/architecture/architecture-principles.md`,
including Principle 19, and the normative Work, Work Group, identity, migration,
validation and Performance documents.

The implementation preserves the repository as a curated recommendation
collection. External authority evidence remains demand-driven. Existing legacy
data is trusted, but Person and Work identity still fail closed when repository
or authority evidence has not established identity.

## Identity Gate

Migration now treats candidate discovery and identity resolution as separate
steps:

```python
candidates = matcher.find_work_candidates(...)
resolution = matcher.resolve_work_identity(...)
```

Candidate discovery may use normalized titles, source provenance, catalogue
numbers and Work-family candidates. Identity resolution then requires specific
evidence for one canonical Work before returning `MATCHED`.

Evidence consumed by the resolver now includes:

- trusted legacy provenance: canonical `source.file` plus `source.line`;
- parsed catalogue identifiers such as WAB and Opus, including `bis`;
- canonical title and normalized title candidates;
- Work Group/family candidates as navigation only;
- version/date/revision text as identity evidence.

`NO_MATCH != NEW_WORK` remains enforced. A missing repository match does not
create a Work candidate. If the source has concrete Work evidence but no
repository candidate, the result is `AUTHORITY_EVIDENCE_REQUIRED`, not curator
escalation and not canonical creation.

Composer identity also fails closed. A document slug is never used as a
canonical Person ID fallback.

## Parser Fixes

The parser now preserves catalogue evidence on `SourceRecord.catalogue` and
keeps revision/version descriptors in `work_text`.

The Prokofiev collective juvenile line is parsed as two source Work records:

- `prokofiev:12:1` -> `Symphony (1902)`;
- `prokofiev:12:2` -> `Symphony (1908)`.

Those two records route to the authority gate because they are not established
canonical repository identities.

## Vertical Slice Evidence

Command:

```bash
.venv/bin/python scripts/migrate.py --composer bruckner --composer prokofiev --dry-run
```

Observed result:

- source records: 140;
- existing Works matched automatically: 138;
- existing Performances matched automatically: 53;
- new Work candidates: 0;
- new Performance candidates: 34;
- authority-gated Work identities: 2 Prokofiev juvenile symphonies;
- curator-required Work identity decisions: 0;
- false-positive Work matches found in adversarial review: 0;
- false-positive Performance matches found in adversarial review: 0.

The 21 repository-resolvable cases named in the blocking review are now consumed
by generic repository evidence: provenance, catalogue, title, version/date and
relationship context. The only remaining non-matched Work identities in these
slices are the two parsed Prokofiev juvenile symphonies, both routed to
authority evidence before any curator question.

## Performance Matching

Performance matching runs only after Work identity is resolved. It reads
canonical Tidal links from both supported repository shapes:

- `links.tidal.url`;
- list entries with `platform: tidal`.

URLs are normalized for `http`/`https`, `www.tidal.com` and transient query
suffixes. A matched canonical Performance is reported as existing and is not
recreated. Different performance profiles remain separate comparison contexts.

## Regression Tests

Added and retained tests cover exact Work identity, revision disambiguation,
catalogue/version conflicts, alias-style matching, no-match fail-closed
semantics, unresolved Composer identity, missing MBID behavior, resolved
version/revision classification, unknown identity-affecting failures, existing
Performance matching, performance-profile distinction, dry-run idempotence, WAB
32/42/43 distinctions, Bruckner source-line provenance, Prokofiev Opus/version
distinctions and the juvenile-symphony parser split.

Verification:

```bash
.venv/bin/python -m pytest tests/migration -q
```

Result: 38 passed.

## Hygiene

Runtime and development debris were removed from the PR:

- `.coverage`;
- `__pycache__` and `*.pyc`;
- `src/classical_music/migration/entity_matcher_old.py`;
- stale generated run summaries and source-record dumps.

`.gitignore` already covers these Python runtime artifacts.

## Adversarial Self-review

I explicitly tried to falsify the clean counts by inspecting all non-`MATCHED`
slice rows in `generated/migration/migration-summary.json`. Only
`prokofiev:12:1` and `prokofiev:12:2` remain non-matched, and both are
authority-gated rather than curator-required.

The Bruckner version rows that previously looked unresolved were checked against
trusted source provenance and catalogue evidence. The Tantum ergo collisions
resolve to separate Works by WAB number. Prokofiev suite/source collisions now
preserve `bis` opus suffixes, avoiding false Work matches.

The remaining limitation is deliberate: this PR does not perform live authority
lookup for the two juvenile Prokofiev symphonies and does not migrate the rest
of the collection. It keeps PR #167 as a draft vertical slice for #164.
