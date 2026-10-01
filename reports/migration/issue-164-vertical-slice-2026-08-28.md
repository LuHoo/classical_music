# Issue #164 Vertical Slice Evidence

## Scope

Dry-run composers:

- Bruckner;
- Prokofiev.

Command:

```bash
.venv/bin/python scripts/migrate.py --composer bruckner --composer prokofiev --dry-run
```

## Results

| Measure | Count |
| --- | ---: |
| Source records | 140 |
| Existing Works matched automatically | 138 |
| Existing Performances matched automatically | 53 |
| New Work candidates | 0 |
| New Performance candidates | 34 |
| Authority-gated Work identities | 2 |
| Curator-required Work identity decisions | 0 |
| False-positive Work matches found | 0 |
| False-positive Performance matches found | 0 |

## Authority Gate

The only non-matched Work identities are the parsed Prokofiev juvenile
symphonies:

| Source ID | Parsed Work | Status | Next Step |
| --- | --- | --- | --- |
| `prokofiev:12:1` | `Symphony (1902)` | `authority_evidence_required` | Demand-driven authority evidence |
| `prokofiev:12:2` | `Symphony (1908)` | `authority_evidence_required` | Demand-driven authority evidence |

These are not curator-required decisions in this PR because repository evidence
is insufficient and authority evidence has not yet been exhausted.

## Blocking-review Cases

The 21 repository-resolvable cases named in the latest blocking review now
resolve automatically using generic repository evidence:

- trusted source provenance (`source.file` plus `source.line`);
- catalogue identifiers, including WAB and Opus/`bis`;
- canonical title and normalized title candidates;
- Work-family candidates used only for navigation;
- version/date/revision evidence for final Work selection.

The Bruckner `Tantum ergo` collisions resolve by WAB number. The Bruckner
Symphony No. 5 line 48/50 versions resolve by trusted source provenance. The
Prokofiev Sinfonietta and Symphony No. 4 original/revised versions resolve by
provenance, catalogue and version evidence.

## Adversarial Review

I inspected every non-`matched` row from the dry-run summary. Only the two
Prokofiev juvenile symphonies remain non-matched, and both route to the
authority gate. No repository-resolvable Bruckner or Prokofiev case remains
classified as curator-required.

Performance matching was checked separately from Work identity. It only runs
after Work identity is resolved, reads both canonical Tidal link shapes, and
does not use performer metadata to decide Work version identity.
