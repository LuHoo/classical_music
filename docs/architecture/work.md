# Work

## Purpose

A `Work` represents one distinct artistic composition or version as recognised by the repository.

A Work is the artistic object to which Performances are attached. It is not a recording, release, publication, streaming item or editorial recommendation.

## Core rule

Every Work belongs to exactly one Work Group.

```text
Work
    ↓
exactly one Work Group
```

A Work Group is the umbrella for closely related Works. The Work is the specific artistic version that can receive Performances.

## Identity

Work identity is determined by musicological and curatorial judgement, not by streaming metadata or release packaging.

The following do not create a new Work:

- different performers;
- different recordings;
- different releases;
- remasters;
- labels or catalogue numbers attached to recordings;
- changed streaming links.

The following normally create a separate Work:

- composer revisions;
- distinct composer-authorised versions;
- independently recognised artistic versions;
- recognised completions;
- independent suites;
- independently recognised orchestrations or arrangements.

Composer revisions are always separate Works within the same Work Group.

## Arrangements, transcriptions and versions

An arrangement, orchestration or transcription becomes a separate Work only when it represents a distinct artistic object recognised by the composer, by musical tradition or by the curator's presentation needs.

A practical transcription does not automatically deserve a separate Work.

The repository models repertoire, not every playable variant.

## Movements, arias and excerpts

An individual movement, aria or excerpt is normally not a separate Work merely because it can be performed separately.

An exception may exist when the excerpt has become an established independent concert work or was published as an independent suite.

This is a boundary case. It should be resolved cautiously for the specific repertoire rather than by introducing a large universal classification system.

## Relationship to Performance

Every Performance refers to exactly one Work.

A Work may exist without any recommended Performance. Such Works remain part of the catalogue and must still be eligible for display on the website.

Different performance traditions do not create new Works. When the distinction matters editorially, it is represented by a performance profile on the Performance and by the comparison rules in `recommendation-policy.md`.

## Performance profiles

Performance profiles are not properties of a Work.

They are sparse, explicit classifications on Performances. A profile may be proposed from available metadata, such as instrument credits, but the final profile is a canonical curatorial classification.

Most Works require no explicit performance profile.

## Public metadata

A Work contains enough information to identify and present the composition.

Typical metadata may include:

- title;
- composer;
- catalogue number;
- opus number;
- nickname;
- key;
- year, when useful;
- instrumentation, when useful;
- aliases;
- external identifiers.

The public presentation attribute:

```yaml
gem: true
```

belongs to the Work. It must not affect workflow, validation or prioritisation.

## Required fields

The initial required fields are:

- `id`;
- `work_group_id`;
- `composer_id`;
- `title`.

Exact YAML syntax is deferred to later schema design.

## Validation

Validation should ensure that:

1. every Work belongs to exactly one Work Group;
2. every referenced composer exists;
3. Work identifiers are unique;
4. aliases do not conceal duplicate Works;
5. revisions are modelled as separate Works;
6. Performances reference concrete Works, not Work Groups.

Validation should report possible duplicate Works for review, not merge them automatically.

## Summary

A Work is one distinct artistic composition or version.

It belongs to exactly one Work Group, may have zero or more recommended Performances, and remains independent of recordings, releases, remasters, performers and streaming links.
