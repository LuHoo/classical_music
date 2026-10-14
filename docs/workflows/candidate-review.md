# Candidate Review Workflow

## Scope

Candidates are review artifacts, not canonical entities.

Canonical data contains only accepted Persons, Work Groups, Works, and Performances.

Candidates remain outside `data/` until accepted.

## Candidate Lifecycle

- `open`: Newly identified candidate waiting for review.
- `accepted`: Accepted and migrated into canonical data.
- `rejected`: Explicitly declined.
- `superseded`: Replaced by a better or corrected candidate.

## Candidate Record Shape

```yaml
source_file: docs/mozart.md
source_line: 42
candidate_work: mozart-piano-concerto-no-20-work
performer_text: Charles Richard-Hamelin, Les Violons du Roi, Jonathan Cohen
tidal_url: https://tidal.com/track/313466200
musicbrainz_recording_id: <optional>
musicbrainz_release_id: <optional>
review_reason: uncertain_match
status: open
```

## Review Steps

1. Confirm source provenance.
2. Validate work identity and Work Group placement.
3. Verify performer text and platform link quality.
4. Check authority sources (Grove, composer side materials, MusicBrainz, fallback Wikipedia).
5. Decide one of: accept, reject, supersede.
6. Record rationale and link evidence.

## Decision Paths

### Accept Candidate

- Ensure target Work is correct.
- Ensure comparison-category policy is respected.
- Create or update canonical Performance.
- Mark candidate `accepted` with rationale.

### Reject Candidate

- Keep source traceability.
- Mark `rejected` with reason (e.g., wrong Work, duplicate, weak evidence).

### Replace Performance

- Keep existing recommendation and candidate separate during review.
- Only after curator decision, update canonical Performance.
- Mark previous candidate(s) `superseded` as needed.

### Update Performance

- For same underlying interpretation, update metadata or links without creating a new identity.
- Record rationale for auditability.

## Governance

Curator decision is authoritative.
No automation may accept candidates or replace recommendations automatically.
