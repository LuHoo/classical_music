# ADR 0002: Domain entities and ownership

- Status: Accepted
- Date: 2026-07-16

## Context

ADR 0001 established that the repository is a curated catalogue of classical musical works and their recommended performances.

This ADR defines the core domain entities of the system and assigns ownership of information to exactly one entity.

The goal is to avoid duplicated metadata and to establish a stable semantic model before deciding on file formats, YAML schemas or import workflows.

## Decision

The domain consists of six primary entities:

- Composer
- Work Family
- Work
- Performance
- Release
- Availability

Recommendations are relationships between works and performances rather than independent musical entities.

The repository follows the principle:

> Every piece of information has exactly one owner.

## Domain model

```text
Composer
      │
      │ contributes to
      ▼
Work
      │
      │ belongs to
      ▼
Work Family (optional)

Work
      │
      │ recommended performance
      ▼
Performance
      │
      │ published as
      ▼
Release
      │
      │ available through
      ▼
Availability
```

The model is relational rather than hierarchical.

## Composer

A composer is a person contributing creatively to one or more works.

Typical contribution roles include:

- composer
- co-composer
- arranger
- orchestrator
- transcriber
- completer
- reconstructor

The exact vocabulary will be defined later.

A work may therefore reference multiple composers with different roles.

## Work Family

A work family groups closely related musical works.

Typical examples include:

- composer revisions;
- orchestrations;
- transcriptions;
- reductions;
- completions;
- reconstructions.

A work family is purely an organisational concept.

It:

- has no performances;
- has no releases;
- has no recommendations.

Its purpose is navigation and grouping.

## Work

A work is the smallest independently performable musical entity recognised by the catalogue.

Examples include:

- the original version of a composition;
- an orchestration;
- a transcription;
- a revised version;
- a completion.

Each work:

- may belong to one work family;
- may have one or more contributing composers;
- may exist without a recommendation.

A recommendation always belongs to an individual work.

The public website displays all works contained in the catalogue, regardless of whether a recommendation already exists.

## Recommendation

A recommendation expresses the curator's current preferred performance of a work.

Each work has at most one current recommendation.

A recommendation may additionally specify a preferred release if multiple releases of the same performance differ materially in:

- sound quality;
- mastering;
- format;
- completeness.

The recommendation never points directly to a streaming platform.

## Performance

A performance represents a recorded interpretation of one work.

A performance contains artistic information such as:

- conductor;
- orchestra;
- soloists;
- choir;
- recording date;
- recording location.

A performance is independent of commercial publication.

The same performance may appear on multiple releases.

## Release

A release represents a commercial publication of a performance.

Examples include:

- original LP;
- CD;
- SACD;
- digital release;
- remastered edition;
- box set.

A release contains publication-specific information, including:

- label;
- catalogue number;
- release year;
- edition;
- remastering.

A release never changes the identity of a performance.

## Availability

Availability describes how a release can currently be accessed.

Examples include:

- TIDAL
- Apple Music
- Spotify
- Qobuz

Availability contains operational information such as:

- platform;
- platform identifier;
- URL;
- status;
- last checked.

Availability is intentionally separated from recommendations because streaming platforms are external and unstable.

## Ownership of information

The following ownership rules apply.

| Information | Owner |
|-------------|-------|
| Composer names | Composer |
| Relationships between related works | Work Family |
| Titles, catalogue numbers, instrumentation | Work |
| Composer contributions | Work |
| Artistic interpretation | Performance |
| Recording participants | Performance |
| Label, catalogue number, remaster | Release |
| Curatorial choice | Recommendation |
| Streaming identifiers and URLs | Availability |

Information should not be duplicated between entities unless justified by performance or interoperability requirements.

## Consequences

### Advantages

- Clear separation of responsibilities.
- Stable identifiers.
- Independent evolution of catalogue, curation and distribution.
- Support for multiple composers per work.
- Support for arrangements, orchestrations and revisions.
- Streaming services remain implementation details.

### Trade-offs

- More entities than a recording-centric model.
- Additional relationships must be maintained.
- Requires validation of cross references.

## Future work

Future ADRs will define:

- canonical identifier strategy;
- contribution roles;
- recording metadata;
- release metadata;
- import workflows from MusicBrainz and Discogs;
- recommendation workflow;
- website generation.
