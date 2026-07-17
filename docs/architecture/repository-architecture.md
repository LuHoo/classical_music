# Repository Architecture

## Purpose

This document defines the physical and logical organisation of the repository.

The repository supports a curated collection of classical Works and recommended Performances. It is not intended to reproduce the entity models or metadata coverage of MusicBrainz, Discogs, Tidal, Gramophone, Wikipedia, or other external sources.

The architecture should remain proportionate to the public website:

- the user browses Composers and Works;
- a Work may be marked as a Gem;
- a Work may have one or more recommended Performances;
- a Performance may contain a Tidal link;
- a Performance may contain a link to a Gramophone review.

Everything else exists only to support accurate identification, maintenance, migration, validation, and publication.

---

## Design principles

### 1. The repository represents the collection

The repository is the canonical representation of the curated collection.

The existing Markdown files are the starting point and are assumed to be substantially correct. Migration should preserve their editorial meaning unless a genuine identity problem is found.

External sources may help identify, validate, or enrich entities. They do not replace the repository's own canonical identities or recommendations.

### 2. Accuracy before completeness

The repository must be certain about the identity of:

- a Person;
- a Composer;
- a Work;
- a version, arrangement, orchestration, revision, or completion represented as a separate Work;
- a recommended Performance.

Metadata completeness is secondary.

The repository should not collect information merely because an external source makes it available.

### 3. Minimal persistent data

Only information that serves at least one of the following purposes should be stored persistently:

- identifying an entity;
- distinguishing it from another entity;
- representing an editorial recommendation;
- supporting the public website;
- maintaining an external link;
- documenting a consequential identity decision.

Temporary metadata used during matching or migration belongs outside the canonical data model.

### 4. Repository-first identification

When a new Tidal link is introduced, the repository is consulted first.

The preferred sequence is:

```text
Tidal link
    ↓
Existing Person and Work data
    ↓
Existing Performance data
    ↓
External sources, only where needed
    ↓
Human review, only when identity remains uncertain
```

Existing canonical entities should be reused whenever possible.

### 5. External ontologies are not copied

MusicBrainz distinguishes Works, Recordings, Releases, Tracks, and other entities for its own purposes. Discogs organises Releases and Masters. Tidal exposes Tracks and Albums.

This repository uses only the distinctions required by the collection.

In particular, it does not maintain separate internal entities for Performance, Recording, and Release.

---

## Core domain objects

The persistent collection is organised around the following core objects:

```text
Person
Work Group
Work
Performance
```

Recommendations are represented as editorial properties or records attached to Works and Performances.

### Person

A Person represents an individual.

Composer is a role of a Person, not a separate entity type. A Person may also act as conductor, soloist, arranger, orchestrator, editor, librettist, or completer.

The repository must avoid duplicate Person identities caused by:

- alternative spellings;
- diacritics;
- transliterations;
- initials;
- pseudonyms;
- historical name forms;
- identical names belonging to different people.

### Work Group

A Work Group is a non-performable grouping of closely related Works.

It is created only when the collection represents multiple musically meaningful versions or derivations that users should understand as belonging together.

Examples may include:

- materially different versions of the same symphony;
- an original Work and a later independently performed revision.

A Performance is never linked directly to a Work Group.

### Work

A Work is a performable musical entity.

Separate Works are created for musically meaningful and independently performable:

- versions;
- arrangements;
- orchestrations;
- revisions;
- completions.

Editorial corrections, remastering, or minor source differences do not create a new Work.

A Work may be marked as a Gem.

The identity of every Work on the website must be unambiguous.

### Performance

A Performance represents the recommended interpretation as recognised by the curator and the website user.

It combines the concepts that external databases may separately describe as a performance, recording, release, track, or album manifestation.

A Performance normally includes:

- the Work performed;
- relevant performers;
- optional disambiguating information such as a year;
- zero or more platform links;
- an optional Gramophone review reference;
- recommendation status.

The term `Performance` is used in the repository as a practical collection concept. It does not imply that every recorded item is a single documented live event.

---

## Public model

The public website is built around the following hierarchy:

```text
Person in the role of Composer
    ↓
Work
    ↓
recommended Performance
    ↓
Tidal link, when available
    ↓
Gramophone review link, when available
```

The user does not need to navigate separate Recording and Release entities.

The public presentation should not expose internal migration, matching, cache, or validation structures.

---

## Proposed top-level layout

```text
.
├── data/
├── sources/
├── docs/
├── site/
├── generated/
├── cache/
├── reports/
├── scripts/
└── tests/
```

The exact static-site directory may later be adapted to the technology used by GitHub Pages. The architectural distinction between canonical data, source material, generated output, and temporary data should remain.

---

## `data/`: canonical collection data

The `data/` directory contains the persistent, canonical representation of the collection.

```text
data/
├── persons/
├── work-groups/
├── works/
└── performances/
```

Only reviewed and accepted collection data belongs here.

### `data/persons/`

Contains one file per Person.

Example:

```text
data/persons/
└── anton-bruckner.yaml
```

Illustrative structure:

```yaml
id: anton-bruckner
name: Anton Bruckner

external_ids:
  musicbrainz: ...
  wikidata: ...
```

Additional information is stored only when needed for identification or presentation.

A complete biography, discography, nationality profile, or list of aliases is not required.

### `data/work-groups/`

Contains one file per Work Group.

Example:

```text
data/work-groups/
└── bruckner-symphony-8.yaml
```

Illustrative structure:

```yaml
id: bruckner-symphony-8
composer_id: anton-bruckner
title: Symphony No. 8 in C minor

members:
  - bruckner-symphony-8-1887
  - bruckner-symphony-8-1890
```

Work Groups remain exceptional and should not be created for every Work.

### `data/works/`

Contains one file per Work.

Example:

```text
data/works/
└── bruckner-symphony-8-1890.yaml
```

Illustrative structure:

```yaml
id: bruckner-symphony-8-1890
composer_id: anton-bruckner
title: Symphony No. 8 in C minor
version: 1890
catalogue_number: WAB 108
work_group_id: bruckner-symphony-8
gem: true

relationships:
  - type: revision_of
    target_work_id: bruckner-symphony-8-1887
```

The exact schema belongs in the domain and metadata documentation. The repository architecture only requires that each Work has a stable, independent canonical record.

### `data/performances/`

Contains one file per Performance.

Example:

```text
data/performances/
└── haitink-rco-bruckner-8.yaml
```

Illustrative structure:

```yaml
id: haitink-rco-bruckner-8
work_id: bruckner-symphony-8-1890

performers:
  conductor: bernard-haitink
  orchestra: royal-concertgebouw-orchestra

year: 1981
recommended: true

links:
  tidal:
    url: ...
    status: active

reviews:
  gramophone:
    issue: 1981-10
    url: ...
```

The `year` and other disambiguating metadata are optional. They should be included only when useful for recognition, matching, or display.

A Performance may exist without a current Tidal link. The recommendation is not identical to platform availability.

---

## Recommendation representation

The current collection contains two distinct editorial judgements.

### Work recommendation

The diamond symbol in the legacy Markdown represents a Work-level recommendation:

```yaml
gem: true
```

### Performance recommendation

A legacy entry containing a Tidal link represents recommendation of that Performance:

```yaml
recommended: true
```

These meanings must remain distinct during migration.

External sources may not create, remove, or modify either recommendation automatically.

If later requirements justify a separate Recommendation entity, the data may be refactored without changing this editorial distinction. A separate entity is not required for the initial repository design.

---

## Platform links

Platform links belong to a Performance.

Example:

```yaml
links:
  tidal:
    url: ...
    status: active
    last_checked: 2026-07-17
```

Additional platforms may later be added under the same structure.

A platform link is a route to a Performance, not the identity of the Performance itself.

Consequently:

- a broken Tidal link does not invalidate the Performance;
- replacement of a Tidal URL does not create a new Performance;
- equivalent links on multiple platforms may refer to the same Performance.

Platform-specific metadata should remain minimal.

---

## Gramophone references

Gramophone information is represented only as a reference to a review of a Performance.

Legacy notations such as:

```text
(10/2021)
```

mean that the Performance was reviewed in the October 2021 issue of *Gramophone*.

During migration this may become:

```yaml
reviews:
  gramophone:
    issue: 2021-10
```

When the review URL is known:

```yaml
reviews:
  gramophone:
    issue: 2021-10
    url: ...
```

The repository does not need to store:

- review text;
- quotations;
- star ratings inferred from the review;
- an extensive critical reception model;
- complete issue contents.

The review link is contextual information attached to the Performance.

---

## `sources/`: retained source material

The `sources/` directory contains material used to construct, verify, or enrich the collection but not itself part of the canonical domain data.

Suggested layout:

```text
sources/
├── legacy-markdown/
├── lucas-grove/
└── references/
```

### `sources/legacy-markdown/`

Contains the original or preserved Markdown collection during migration.

These files remain the authoritative migration source for:

- existing Work selections;
- Gem markers;
- recommended Performance entries;
- existing Tidal links;
- existing Gramophone issue references.

After migration they may remain as archival source material, but the canonical website should be generated from `data/`.

### `sources/lucas-grove/`

Contains the curator's historical Word documents about selected Composers.

These documents are an internal authority source. They may help with:

- Composer identity;
- Work identity;
- preferred titles;
- version distinctions;
- historical editorial context.

They should not be treated as canonical entity files in their present Word format.

A later conversion process may transform them into a more usable format, for example:

```text
sources/lucas-grove/converted/
```

or:

```text
generated/lucas-grove/
```

The converted output should remain source or research material unless specific values are deliberately promoted into canonical `data/` records.

Conversion by Codex or another tool should preserve:

- document identity;
- headings and structure;
- source filename;
- traceability to the original Word file.

It should not automatically rewrite canonical Works or Persons.

### `sources/references/`

May contain manually maintained references, notes, or source pointers that do not belong to a single canonical entity.

This directory should remain limited and purposeful.

---

## `docs/`: architecture and editorial policy

The `docs/` directory contains human-readable documentation.

Suggested layout:

```text
docs/
├── architecture/
└── editorial/
```

### `docs/architecture/`

Includes documents such as:

- `domain-model.md`
- `identity-rules.md`
- `naming-conventions.md`
- `identifier-policy.md`
- `migration-rules.md`
- `validation-rules.md`
- `metadata-architecture.md`
- `repository-architecture.md`

Workflow documents may be added later, after the repository structure is stable.

### `docs/editorial/`

May contain policies for:

- Gems;
- recommended Performances;
- preferred naming;
- review references;
- handling uncertain cases.

Architecture documents define the system. Editorial documents define curatorial practice.

---

## `site/`: website source

The `site/` directory contains the source files used to produce the GitHub Pages website.

It may include:

- templates;
- page layouts;
- styles;
- JavaScript;
- static assets;
- site configuration.

The website must read from canonical or generated data rather than from temporary caches or external APIs during publication.

The precise framework is a later implementation decision.

---

## `generated/`: reproducible derived output

The `generated/` directory contains files produced from canonical data or retained sources.

Examples:

```text
generated/
├── indexes/
├── website-data/
├── search/
└── lucas-grove/
```

Possible outputs include:

- Composer indexes;
- Work indexes;
- Performance indexes;
- JSON used by the website;
- search indexes;
- converted internal Grove documents;
- migration previews.

Generated files should be reproducible and should not be edited manually.

Whether they are committed to Git depends on deployment requirements, but their generated status must remain explicit.

---

## `cache/`: temporary external data

The `cache/` directory contains temporary or reproducible external metadata used during matching and enrichment.

Suggested layout:

```text
cache/
├── tidal/
├── musicbrainz/
├── discogs/
└── wikidata/
```

Cached data is not canonical.

It may be deleted and rebuilt without changing the collection.

The cache may contain:

- API responses;
- search candidates;
- normalised matching records;
- temporary URL resolution results.

Large or sensitive caches should normally be excluded from Git.

---

## `reports/`: review and validation output

The `reports/` directory contains generated information requiring inspection.

Examples:

```text
reports/
├── migration/
├── validation/
├── unresolved-identities/
├── duplicate-candidates/
└── broken-links/
```

Reports may identify:

- unresolved Composer or Work matches;
- possible duplicate Performances;
- invalid references;
- missing required fields;
- inactive Tidal links;
- Gramophone issue references without URLs.

Reports are not canonical data.

A report finding becomes canonical only after a reviewed change to `data/`.

---

## `scripts/`: repository operations

The `scripts/` directory contains code for:

- migration;
- validation;
- site generation;
- link checking;
- source conversion;
- external matching;
- report generation.

Scripts should respect the separation between:

- canonical data;
- retained source material;
- generated output;
- temporary cache;
- reports.

No script may silently overwrite identity-critical canonical data.

---

## `tests/`: automated checks

The `tests/` directory contains automated tests for:

- schemas;
- identifiers;
- referential integrity;
- migration semantics;
- website generation;
- duplicate detection;
- source conversion;
- link parsing.

Tests should particularly protect:

- unique Person identities;
- unique Work identities;
- valid Work relationships;
- valid Performance-to-Work references;
- preservation of Gem and Performance recommendation semantics.

---

## Canonical and non-canonical areas

The repository distinguishes clearly between canonical and non-canonical content.

| Location | Status | Manually edited |
|---|---|---:|
| `data/` | canonical collection | yes |
| `sources/` | retained source material | sometimes |
| `docs/` | canonical policy and documentation | yes |
| `site/` | website source | yes |
| `generated/` | derived output | no |
| `cache/` | temporary external data | no |
| `reports/` | derived review output | no |
| `scripts/` | operational code | yes |
| `tests/` | automated checks | yes |

Only `data/` defines the entities and recommendations shown on the final website.

---

## File granularity

The preferred default is one canonical file per stable entity.

Advantages include:

- stable diffs;
- simple review;
- limited merge conflicts;
- direct validation;
- easy entity lookup;
- clear ownership of changes.

The main exception is very small supporting vocabularies, which may be stored in a shared file if they do not represent independent curated entities.

The repository should not create one file per external assertion, track, API response, or review observation.

---

## Identifier and filename alignment

Canonical filenames should normally derive from stable repository identifiers.

Example:

```text
data/works/bruckner-symphony-8-1890.yaml
```

with:

```yaml
id: bruckner-symphony-8-1890
```

Renaming a display title should not automatically require changing the stable identifier.

Detailed slug and identifier rules remain governed by:

- `naming-conventions.md`;
- `identifier-policy.md`.

---

## Identity review boundaries

Routine metadata updates may be automated or reviewed lightly.

The following operations require explicit review:

- creating a new Person where a possible match already exists;
- merging or splitting Persons;
- creating a new Work where a possible match already exists;
- merging or splitting Works;
- assigning a Performance to a version-specific Work;
- converting an arrangement, orchestration, revision, or completion into a separate Work;
- merging Performances;
- changing the Work referenced by a recommended Performance.

Minor differences in dates, durations, labels, or source spelling do not require a decision record unless they create genuine identity uncertainty.

---

## Migration from the current Markdown files

Migration should preserve the present collection rather than reinterpret it unnecessarily.

The migration process should:

1. parse existing Composer and Work structure;
2. create or match canonical Persons;
3. create or match canonical Works;
4. preserve Gem markers as Work recommendations;
5. create recommended Performances from entries containing Tidal links;
6. preserve existing Gramophone issue references;
7. report only genuine ambiguities;
8. avoid enrichment that is unrelated to identity or website presentation.

Because the current Markdown data is believed to be more than 99% correct, migration should use it as trusted editorial input.

External validation should focus on detecting exceptional identity errors rather than challenging every entry.

---

## Adding a new Tidal link

A new Tidal link should eventually support the following repository operation:

```text
Tidal link
    ↓
extract available title and performer metadata
    ↓
match existing Person or Composer
    ↓
match existing Work
    ↓
match or create Performance
    ↓
store Tidal link
    ↓
review only when Composer or Work identity is uncertain
```

The detailed matching and workflow design belongs in later workflow documentation.

The repository architecture requires only that the resulting canonical data fits into:

- `data/persons/`;
- `data/works/`;
- `data/performances/`.

---

## Deferred complexity

The initial repository should not introduce separate persistent entities for:

- Recordings;
- Releases;
- Tracks;
- Albums;
- Reviews;
- source assertions;
- recording sessions;
- remasterings;
- platform manifestations.

Such concepts may appear in temporary matching data or external source adapters.

They should become canonical entities only if a demonstrated user or maintenance requirement cannot be met with the current model.

---

## Summary

The repository is organised around a small set of stable, curated entities:

```text
Person
Work Group
Work
Performance
```

The public website presents Composers, Works, Gems, recommended Performances, Tidal links, and optional Gramophone review links.

The repository deliberately separates:

- canonical collection data;
- retained source material;
- generated website output;
- temporary external metadata;
- validation and migration reports.

Identity accuracy is mandatory for Persons and Works.

Metadata accumulation is not a project objective.

The architecture should remain simple enough that the collection continues to be recognisable as a curated recommendation list rather than becoming a general-purpose music database.
