# Repository Architecture

## Purpose

This document defines the repository-level architecture for the classical music recommendation collection.

The repository is a curated recommendation collection, not an exhaustive catalogue of recordings, releases, tracks, albums or external authority records. It stores durable curator knowledge that is needed to identify Works, preserve recommendations, maintain links and generate the public website.

Detailed entity boundaries are defined in:

- `work.md`;
- `performance.md`;
- `recommendation-policy.md`.

Operational workflows are described in `workflow-design-notes.md`.

## Architectural principles

### Repository authority

The canonical repository is authoritative for local identity and editorial recommendations.

External sources such as MusicBrainz, Discogs, Wikidata, Wikipedia, Tidal and Gramophone may help with identification, matching and validation. They do not determine canonical identity and must not create, remove or replace recommendations automatically.

### Curated scope

The repository should represent:

- selected Persons;
- selected Work Groups;
- selected Works;
- curatorially accepted Performances;
- minimal external references and links needed for matching, maintenance or presentation.

It should not accumulate metadata merely because an external source provides it.

### Durable canonical data

Only durable curator knowledge belongs in canonical data.

Temporary candidates, listening queues, searches, comparisons, migration review artefacts, duplicate evidence and other workflow state remain outside canonical data. They may live in GitHub Issues, generated reports or temporary migration artefacts.

### No canonical Recording or Release entities

The initial canonical model has four core entities:

```text
Person
Work Group
Work
Performance
```

The repository does not introduce separate canonical Recording or Release entities. Limited release-related details may be stored on a Performance when useful for recognition, matching, maintenance or presentation, but they do not define Performance identity.

## Core entities

### Person

A Person represents an individual.

Composer is a role of a Person, not a separate canonical entity type. A Person may also act as conductor, soloist, arranger, orchestrator, editor, librettist or completer.

Person records exist to avoid duplicate identities caused by spelling variants, diacritics, transliterations, initials, pseudonyms, historical name forms or identical names belonging to different people.

### Work Group

A Work Group is a non-performable grouping of closely related Works.

Every Work belongs to exactly one Work Group. A Work Group may contain one Work, but it becomes musically important when the collection represents multiple versions or derivations that should be understood together.

A Performance never links directly to a Work Group.

### Work

A Work represents one distinct artistic composition or version.

Every Work belongs to exactly one Work Group. Composer revisions are separate Works within the same Work Group. Different performers, recordings, releases, labels, remasters or streaming links do not create new Works.

A Work may exist without any recommended Performance and must still be eligible for display on the website.

The Work-level public presentation attribute is:

```yaml
gem: true
```

`gem` must not affect workflow, validation or prioritisation.

### Performance

A Performance represents one curatorially accepted interpretation of exactly one Work.

A Performance enters canonical data only after the curator has listened to it and judged it good enough to recommend. A changed Tidal URL, reissue, remaster, alternative digital release or different album containing the same interpretation does not create a new Performance.

Presence in canonical Performance data implies recommendation. A separate field such as `recommended: true` should be avoided unless a temporary migration requirement makes it necessary.

## Public model

The public website should ordinarily show:

- the Work;
- the recommended performers;
- the relevant streaming link;
- an optional Gramophone reference or link.

Visitors should receive a clear recommendation rather than a catalogue of all available Performances.

The website should not normally expose:

- internal identifiers;
- candidate Performances;
- migration state;
- matching evidence;
- link-check data;
- `keep_looking`.

## Repository layers

The proposed top-level layout is:

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

The exact static-site directory may later be adapted to the technology used for GitHub Pages. The distinction between canonical data, source material, generated output and temporary data should remain.

## `data/`: canonical collection data

The `data/` directory contains reviewed, accepted collection data.

```text
data/
├── persons/
├── work-groups/
├── works/
└── performances/
```

The exact YAML schema is deferred. The architectural requirement is that each canonical entity has one stable local identity and belongs to the correct directory.

## `sources/`: retained source material

The `sources/` directory contains material used to construct, verify or enrich the collection but not itself part of canonical data.

Examples include:

- preserved legacy Markdown;
- exported Tidal playlists;
- historical Word documents;
- manually retained reference material.

Source material may guide migration and review, but values become canonical only when deliberately promoted into `data/`.

## `generated/`, `cache/` and `reports/`

Generated output, caches and reports are not canonical data.

They may contain:

- candidate Performances;
- search results;
- matching evidence;
- duplicate reports;
- `keep_looking` reports;
- link-check reports;
- migration review files.

These artefacts support workflow decisions. They do not define repository identity or public recommendations.

## `site/`

The website is generated from canonical data.

Website generation should respect the publication rules in `recommendation-policy.md`: publish the current recommendation for each comparison category, and keep internal workflow state out of the public view unless a later explicit design decision says otherwise.
