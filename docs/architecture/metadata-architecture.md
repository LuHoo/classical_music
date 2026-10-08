# Metadata Architecture

> Status: Superseded by `repository-architecture.md`, `work.md`, `performance.md`,
> and `recommendation-policy.md`.
>
> This document records an earlier metadata design that treated Recording and
> Release as canonical entities. The current authoritative design uses Person,
> Work Group, Work and Performance as the core canonical entities. Release-related
> details may exist only as limited Performance metadata when useful.

## Purpose

This document defines how metadata is represented, maintained, and enriched within the repository.

Unlike MusicBrainz, Discogs, or Wikipedia, this repository is **not** intended to become a comprehensive music database.

Its purpose is to maintain a carefully curated collection of recommended classical works and recordings.

Metadata exists to support that goal.

---

# Design philosophy

The repository is the canonical representation of the collection.

External sources are consulted to identify, validate, and enrich entities, but they do not define the collection.

The repository owns:

- canonical entity identities;
- canonical relationships;
- editorial recommendations;
- presentation on the website.

External metadata is only incorporated when it improves the quality and maintainability of the collection.

Whenever possible, metadata should remain minimal.

---

# Architectural principles

The metadata architecture follows the following principles.

## 1. Repository-first

The repository is always consulted before external sources.

When processing a new recording, the preferred workflow is:

```
Tidal
    ↓
Existing repository
    ↓
MusicBrainz
    ↓
Discogs
    ↓
Other sources
```

The system first attempts to determine whether the Composer, Work, Recording, or Release already exists.

External sources are only consulted when the repository cannot confidently identify the entity.

---

## 2. Canonical metadata

Each entity stores only the metadata required to represent the collection.

Typical examples include:

Composer

- name
- identifiers

Work

- title
- composer
- version
- catalogue number
- relationships

Recording

- performers
- referenced Work
- recommendation status

Release

- label
- catalogue number
- platform links

Additional metadata is added only when it serves a clear purpose.

---

## 3. Metadata is not accumulated

The repository intentionally avoids storing large amounts of external metadata.

For example, it does not aim to preserve:

- complete biographies
- full discographies
- complete release histories
- all aliases
- every external attribute

Instead, external identifiers provide access to those resources whenever required.

---

## 4. Identity is paramount

The most important objective of the metadata architecture is reliable identity.

The repository should never be uncertain about:

- which Composer is represented;
- which Work is represented;
- how different versions of a Work relate;
- which Recording is referenced.

Identity always takes precedence over metadata completeness.

---

## 5. Metadata supports decisions

Metadata exists to support three activities:

- identifying entities;
- validating entities;
- presenting entities.

Metadata should never become a goal in itself.

---

# Metadata categories

Metadata is divided into three categories.

## Core metadata

Core metadata defines the canonical representation of an entity.

Examples include:

Composer

- preferred name

Work

- preferred title
- composer
- version
- catalogue number

Recording

- Work
- performers

Release

- label
- catalogue number

Platform links

- Tidal URL

Core metadata is stored directly in the repository.

---

## Disambiguation metadata

Some metadata exists primarily to distinguish entities.

Examples include:

- recording year
- recording location
- release year
- playing time
- performer spelling
- catalogue number
- label

These values help identify entities.

They are retained only when useful.

Minor disagreements between sources normally do not require permanent provenance.

---

## Enrichment metadata

Enrichment metadata provides additional context.

Examples include:

- biographies
- historical notes
- instrumentation
- premiere information
- extended descriptions

Such information is optional.

Whenever possible it should be obtained through external references rather than duplicated locally.

---

# External sources

Different sources have different purposes.

## Tidal

Purpose:

- entry point for new recordings;
- platform availability.

Tidal is normally the first source encountered by the user.

It is not considered authoritative for entity identity.

---

## MusicBrainz

Primary role:

- identity
- relationships
- performers
- recordings
- releases

MusicBrainz is the preferred structured metadata source.

Its identifiers are stored whenever available.

---

## Discogs

Primary role:

- commercial releases
- labels
- catalogue numbers
- release editions

Discogs complements MusicBrainz but does not determine repository identity.

---

## Wikipedia

Used primarily for orientation.

It is not treated as an authoritative metadata source.

---

## Internal Grove documents

The repository contains historical Grove-style notes prepared by the curator.

These documents represent valuable editorial knowledge accumulated before the repository existed.

They serve as an internal authority source during difficult identification decisions but are not automatically imported into entity metadata.

---

# Repository-first identification

Whenever a new recording is introduced, identification follows this strategy.

## Step 1

Determine whether the Composer already exists.

## Step 2

Determine whether the Work already exists.

## Step 3

Determine whether the Recording already exists.

## Step 4

Determine whether the Release already exists.

Only when these questions cannot be answered confidently are external sources consulted.

---

# Identity decisions

Only a limited number of situations require explicit editorial decisions.

Typical examples include:

- distinguishing different versions of a Work;
- identifying arrangements;
- identifying completions;
- merging duplicate Recordings;
- separating different Releases.

These decisions should be documented.

Routine metadata differences do not require separate decision records.

---

# External identifiers

Whenever available, stable external identifiers should be stored.

Typical examples include:

- MusicBrainz identifiers
- Discogs identifiers
- Wikidata identifiers

External identifiers allow future enrichment without duplicating external metadata.

---

# Provenance

The repository records provenance only where it provides long-term value.

Normal metadata generally requires only source-level provenance.

Explicit decision provenance is reserved for:

- Work identity
- Composer identity
- Recording identity
- Release identity
- editorial merges
- editorial splits

This keeps the repository maintainable while preserving the reasoning behind important editorial decisions.

---

# Synchronisation

Synchronisation with external sources is non-destructive.

External sources may:

- suggest metadata;
- provide identifiers;
- validate existing entities;
- detect potential duplicates.

They may never automatically:

- redefine entity identity;
- replace editorial recommendations;
- overwrite canonical relationships.

Human review remains responsible for significant identity decisions.

---

# Recommendations

Recommendations are editorial objects.

Neither MusicBrainz, Discogs, nor any other external source determines:

- Gems
- Recommended Recordings
- Editorial notes

These originate exclusively from the repository.

---

# Summary

The repository is a curated collection rather than a comprehensive music database.

Metadata supports the collection.

Identity has priority over completeness.

External sources assist the repository, but the repository remains authoritative.
