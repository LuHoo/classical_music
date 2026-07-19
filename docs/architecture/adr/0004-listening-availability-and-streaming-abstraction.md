---
title: "ADR 0004: Listening availability and streaming abstraction"
nav_order: 5
---

# ADR 0004: Listening availability and streaming abstraction

- Status: Superseded
- Date: 2026-07-16
- Superseded by: `../repository-architecture.md`, `../performance.md`,
  `../recommendation-policy.md`

> ADR 0004 records an earlier Release and Availability abstraction. The current
> authoritative design stores streaming links on Performance as limited metadata
> and does not introduce separate canonical Release or Availability entities.

## Context

ADR 0001 establishes that the repository is a curated catalogue of musical works and their recommended performances.

ADR 0002 defines the core domain entities.

ADR 0003 establishes that external services provide authoritative metadata where appropriate.

The final step is to define how recommended performances are made available for listening.

Streaming services change over time.

Albums disappear.

URLs change.

The same performance may exist on multiple platforms simultaneously.

The recommendation itself should therefore remain independent of any particular streaming service.

## Decision

Listening availability is treated as an operational layer.

Recommendations identify artistic choices.

Streaming services merely provide access to those choices.

The recommendation remains valid even if every streaming link temporarily disappears.

## Principles

### Recommendations are platform-independent

A recommendation identifies:

- a work;
- a preferred performance;
- optionally a preferred release.

It never identifies a streaming platform.

### Availability is operational

Availability records how a release can currently be accessed.

Typical platforms include:

- TIDAL
- Apple Music
- Spotify
- Qobuz

Additional platforms may be added without changing the recommendation model.

### Multiple platforms

The same release may be available on multiple platforms simultaneously.

Likewise, different releases of the same performance may exist on different platforms.

The availability model must therefore support multiple listening destinations.

### Preferred release

Where different releases of the same performance differ materially—for example because of:

- remastering;
- format;
- completeness;

the recommendation may identify a preferred release.

If equivalent releases exist on different platforms, they are considered interchangeable listening destinations.

### Universal listening links

Some streaming providers offer platform-independent listening links that redirect users to their preferred streaming service.

Such links are considered convenience features rather than canonical identifiers.

The repository may support them where appropriate, but recommendations shall never depend on them.

### Platform identifiers

Platform-specific identifiers and URLs are operational metadata.

They may change over time.

They are therefore intentionally separated from works, performances, releases and recommendations.

## Availability information

Availability may contain information such as:

- platform;
- platform identifier;
- URL;
- status;
- last checked;
- notes.

The exact data model will be defined later.

## User experience

Visitors should be able to:

1. navigate to a work;
2. view the recommended performance;
3. choose one of the currently available listening options.

If no listening option is currently available, the recommendation itself remains visible.

The absence of a streaming link does not invalidate the recommendation.

## Responsibilities

| Entity | Responsibility |
|----------|----------------|
| Work | Musical composition |
| Recommendation | Curatorial choice |
| Performance | Artistic interpretation |
| Release | Commercial publication |
| Availability | Current listening options |

## Consequences

### Advantages

- Recommendations remain stable.
- Multiple streaming platforms are supported naturally.
- Platforms can be added or removed independently.
- Streaming URLs become replaceable operational data.
- Public recommendations remain available even when no streaming service currently offers the recording.

### Trade-offs

- Additional availability data must be maintained.
- Platform identifiers require periodic verification.
- Different platforms may expose different releases of the same performance.

## Future work

Future ADRs will define:

- platform identifier strategy;
- universal listening links;
- automatic availability checking;
- import and synchronisation workflows;
- hybrid caching of platform metadata.
