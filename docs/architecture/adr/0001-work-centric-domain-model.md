---
title: "ADR 0001: Work-centric domain model"
nav_order: 2
---

# ADR 0001: Work-centric domain model

- Status: Superseded
- Date: 2026-07-16
- Superseded by: `../repository-architecture.md`, `../work.md`,
  `../performance.md`, `../recommendation-policy.md`

> ADR 0001 established the work-centred direction, but some details below refer
> to preferred releases and listening links as separate recommendation concerns.
> The current authoritative design keeps canonical data centred on Person, Work
> Group, Work and Performance, with release-related details stored only as limited
> Performance metadata when useful.

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

> A curated catalogue of classical musical works and their recommended performances, supported by explicit work-to-work relationships and optional derived navigation groups.

The public website shall display all works that are included in the local catalogue, regardless of whether a recommendation already exists.

A recommendation is optional.

If present, it identifies:

1. the preferred performance;
2. optionally the preferred release of that performance;
3. one or more listening locations.

## Domain model

The conceptual model is relational rather than strictly hierarchical:

```text
Composer
    ↕ contributes to
Work
    ↕ has typed relationship to
Work

Work
    ↓
Recommendation (optional)
    ↓
Performance
    ↓
Preferred Release (optional)
    ↓
Available Listening Links
```

A composer contributes to one or more works, and a work may have contributions from one or more composers or arrangers.

A work may have zero, one or many typed, directional relationships to other works. These relationships may form networks rather than a single tree. Related works may also be grouped for navigation or presentation, but such groups are derived or curated presentation helpers rather than primary domain entities.

Recommendations belong to individual works, not to derived navigation groups.

### Composer

Represents the musical author.

### Derived navigation groups (optional)

A derived navigation group may be used for presentation or website navigation.

Such a group is not a primary domain entity. It does not own musical facts, relationships, recommendations, performances or releases. It may simply reflect a curated or computed view over explicit work-to-work relationships.

### Work

A work is the smallest independently performable musical entity recognised by the catalogue.

A work may have zero, one or many typed, directional relationships to other works. These relationships are first-class domain facts and are not owned by a derived navigation group.

Different revisions, orchestrations or transcriptions are modelled as separate works when they are independently catalogued and may be linked explicitly.

The relationship vocabulary is intentionally open-ended. The repository may retain the terminology used by the relevant contributor or authority source without forcing all relationships into a closed taxonomy.

A work may exist without a recommendation.

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

## Multiple related works

Closely related musical works are connected by explicit, directional work-to-work relationships.

Examples include:

- different composer revisions;
- orchestrations by other composers;
- piano reductions;
- chamber arrangements;
- suites or excerpts derived from another work.

Each related work is treated as an independent catalogue entry and may have its own recommendation.

Website displays may derive groups such as “works derived from Pulcinella” or “versions of Bruckner Symphony No. 4”, but these are presentation views rather than primary domain entities.

## Architectural consequences

This decision separates the project into independent layers.

### Catalogue

Defines:

- composers;
- works;
- canonical identifiers;
- work-to-work relationship facts.

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
- Supports independent recommendations for revisions, orchestrations and arrangements of the same music material.

### Trade-offs

- Introduces additional entities (Performance and Release).
- Requires generation of the public website from structured data.
- Requires future import and synchronisation tooling.

## Future work

This ADR deliberately leaves the following decisions for future ADRs:

- canonical identifier strategy;
- relationship vocabulary and validation rules for work-to-work relationships;
- recording/performance/release data model;
- recommendation workflow;
- import pipeline from MusicBrainz and Discogs;
- streaming platform abstraction;
- website generation pipeline;
- validation rules and schemas.
