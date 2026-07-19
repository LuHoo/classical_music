# Work

## Purpose

A `Work` represents one distinct musical composition as it is recognised in the
repository.

A Work is the artistic object to which Performances are attached. It is not a
recording, release, publication or editorial recommendation.

Every Performance refers to exactly one Work.

---

## Core principle

A Work is an artistic identity.

Two manifestations belong to the same Work only when they represent the same
musical work from the curator's perspective.

Identity is determined by musicological judgement rather than by streaming
metadata.

---

## Relationship to Work Group

Every Work belongs to exactly one Work Group.

The Work Group collects all closely related artistic versions of the same
underlying composition.

Examples include:

- composer revisions;
- authorised versions;
- completions;
- orchestrations published by the composer.

The Work Group is therefore the umbrella concept.

The Work is the specific artistic version.

---

## Revisions

A revision is always a separate Work.

Examples:

- Bruckner Symphony No. 3 (1873)
- Bruckner Symphony No. 3 (1889)

These belong to the same Work Group but are different Works.

The same applies to substantially different composer-authorised revisions.

---

## Arrangements and orchestrations

An arrangement or orchestration becomes a separate Work when it represents a
distinct artistic work recognised by the composer or musical tradition.

Not every practical transcription deserves a separate Work.

The repository models repertoire, not every playable variant.

---

## Individual movements

Normally, individual movements are not separate Works.

The canonical Work is the complete artistic whole.

Exceptions may exist where a movement has become an established independent
concert work.

Suites published as independent artistic works are separate Works.

The boundary is determined by musical practice rather than by technical
possibility.

---

## Identity

The following do **not** create a new Work:

- different performers;
- different instruments used in performance;
- different labels;
- different recordings;
- different releases;
- remasters.

These belong to Performance.

The following normally **do** create a new Work:

- composer revisions;
- distinct composer versions;
- recognised completions;
- independent suites;
- independently recognised orchestrations.

---

## Performance relationship

A Work may temporarily have multiple candidate Performances during editorial
comparison.

After publication, each comparison category has exactly one public
recommendation, as defined in `recommendation-policy.md`.

A Work may therefore have multiple published recommendations only when they
belong to different comparison categories (for example piano versus
harpsichord).

---

## Performance profiles

Performance profiles are **not** properties of a Work.

They are curatorially assigned to Performances.

The workflow may infer a likely profile from external metadata, but the stored
classification is part of the canonical Performance.

Examples include:

- piano
- harpsichord

Most Works require no explicit performance profile.

---

## Works without recommendations

A Work may exist without any recommended Performance.

This allows the repository to represent:

- incomplete composer catalogues;
- future listening plans;
- repertoire awaiting evaluation.

The website should still display such Works.

---

## Public metadata

A Work contains the information needed to identify and present the composition.

Typical fields include:

- title;
- composer;
- catalogue number;
- year (when useful);
- key;
- instrumentation;
- duration (optional);
- aliases.

The public flag:

```yaml
gem: true
```

is solely a presentation feature.

It has no workflow or validation implications.

---

## External identifiers

External identifiers may be stored for matching and maintenance.

Examples:

```yaml
external_ids:
  musicbrainz_work: ...
  wikidata: ...
```

The repository remains authoritative for Work identity.

---

## Required fields

Initial required fields:

- id
- work_group_id
- composer_id
- title

---

## Optional fields

Examples:

- catalogue number
- opus number
- nickname
- key
- year
- instrumentation
- aliases
- external identifiers
- gem

The repository should remain intentionally sparse.

---

## Validation

Validation should ensure:

1. every Work belongs to one Work Group;
2. referenced composer exists;
3. ids are unique;
4. aliases do not create duplicate Works;
5. revisions are modelled as separate Works;
6. Performances reference existing Works.

Validation should report possible duplicate Works but never merge them
automatically.

---

## File location

Each Work is stored as:

```
data/works/<work-id>.yaml
```

---

## Summary

A Work is the canonical representation of one artistic composition.

It belongs to exactly one Work Group.

It may have zero or more Performances.

Different recordings, releases and instrumental interpretations do not create
new Works.

Composer revisions and other artistically distinct versions do.
