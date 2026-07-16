# ADR 0001: Work-centric domain model

- Status: Accepted
- Date: 2026-07-16

## Context

The purpose of this project is to maintain a curated collection of recommended classical recordings.

The primary user journey is:

> Composer → Work → Recommended performance → Listen

Initially the project focused mainly on recordings. During the architectural design it became clear that recordings are not the central concept. Classical music listeners think in terms of works, not albums or releases, and the long-term goals of the project require a complete catalogue of selected works, including works that do not yet have a recommendation.

Examples of future workflows include:

- expanding the catalogue with new composers;
- expanding existing composers with additional works;
- gradually filling gaps in the recommendation catalogue;
- replacing recommendations with better performances;
- supporting multiple streaming platforms.

These workflows all revolve around works rather than recordings.

## Decision

The **work** becomes the central entity of the system.

The repository is defined as:

> A curated catalogue of classical works and their recommended performances.

The public website shall display all works that are included in the local catalogue, regardless of whether a recommendation already exists.

A recommendation is optional.

If present, it identifies:

1. the preferred performance;
2. optionally the preferred release of that performance;
3. one or more listening locations.

## Domain model

The conceptual model is:

```text
Composer
    ↓
Work
    ↓
Recommended Performance (optional)
    ↓
Preferred Release (optional)
    ↓
Available Listening Links
```

### Composer

Represents the musical author.

### Work

Represents the musical composition.

A work exists independently of any recommendation.

A work may therefore be:

- present in the catalogue without a recommendation;
- under investigation;
- associated with a current recommendation.

### Performance

Represents the artistic interpretation of a work.

The recommendation applies primarily to the performance rather than a commercial release.

### Release

Represents a specific commercial publication of a performance.

Different releases of the same performance may differ because of:

- remastering;
- format (CD, SACD, digital, etc.);
- completeness;
- editorial differences.

Where these differences are artistically relevant, a preferred release may be identified.

### Listening links

Listening links are operational access points.

They do not define the identity of a recommendation.

## Source of truth

The repository is the source of truth.

The public GitHub Pages website is generated from the repository data.

External music services are treated only as listening destinations.

## External metadata

The project is not intended to become a comprehensive music database.

Whenever possible, metadata should be obtained from external authority sources.

Typical roles include:

| Source | Primary role |
|---------|--------------|
| MusicBrainz | Canonical identities and relationships |
| Discogs | Releases and label information |
| Wikipedia | General background |
| Grove | Musicological reference |
| Gramophone | Critical evaluation |
| Streaming platforms | Listening availability |

The repository stores only the metadata necessary to support the recommendation workflow and local curation.

## Public website

For every selected composer the website displays the local work catalogue.

Each work is shown as either:

- recommended;
- no recommendation yet.

Works without recommendations remain visible because one of the goals of the project is to progressively complete the catalogue.

## Architectural consequences

This decision separates the project into independent layers.

### Catalogue

Defines:

- composers;
- works;
- canonical identifiers.

### Curation

Defines:

- recommended performances;
- preferred releases;
- candidates;
- historical recommendations;
- editorial notes.

### Distribution

Defines:

- streaming availability;
- platform-specific links;
- universal listening links.

Each layer may evolve independently.

## Consequences

### Advantages

- Matches the way classical music is organised and experienced.
- Supports incremental completion of composer catalogues.
- Separates artistic recommendations from commercial releases.
- Supports multiple streaming platforms.
- Prevents streaming services from becoming the source of truth.
- Simplifies future import workflows from MusicBrainz and Discogs.

### Trade-offs

- Introduces additional entities (Performance and Release).
- Requires generation of the public website from structured data.
- Requires future import and synchronisation tooling.

## Future work

This ADR deliberately leaves the following decisions for future ADRs:

- canonical identifier strategy;
- recording/performance/release data model;
- recommendation workflow;
- import pipeline from MusicBrainz and Discogs;
- streaming platform abstraction;
- website generation pipeline;
- validation rules and schemas.
