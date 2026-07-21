# Minimal YAML Schemas

## Purpose

This document defines the minimal YAML shapes needed before migration can begin.

It is intentionally small. The goal is to make the canonical model writable and
validatable without turning the repository into a general music database.

The canonical entities are:

- Person;
- Work Group;
- Work;
- Performance.

No separate canonical Recording, Release, Recommendation, Track, Album or
Availability entities are introduced.

## General rules

All canonical files use YAML.

Every canonical record has:

- `id`;
- stable local identity;
- only the metadata needed for identification, presentation, matching or
  maintenance.

Identifiers are lowercase ASCII slugs. They should be stable enough for links and
cross-references, but the exact identifier policy may be refined separately.

Empty optional fields should be omitted rather than stored as blank values.

External identifiers are references, not identity authorities.

## Directory layout

```text
data/
├── persons/
├── work-groups/
├── works/
└── performances/
```

The preferred initial layout is one file per canonical record:

```text
data/persons/<person-id>.yaml
data/work-groups/<work-group-id>.yaml
data/works/<work-id>.yaml
data/performances/<performance-id>.yaml
```

Migration batches may temporarily use grouped review files outside canonical
data, but accepted canonical data should settle into the layout above.

## Person

### Purpose

A Person represents an individual human being.

Composer is a role of a Person, not a separate entity type. Performers,
arrangers, orchestrators, librettists, editors and completers may also be
Persons.

### Required fields

```yaml
id: anton-bruckner
name: Anton Bruckner
```

Required:

- `id`;
- `name`.

### Optional fields

```yaml
sort_name: Bruckner, Anton
roles:
  - composer
display_names:
  nl: Anton Bruckner
aliases:
  - A. Bruckner
external_ids:
  musicbrainz: ...
  wikidata: ...
notes: >
  Local identity note, only when needed.
```

`aliases` are for names that help matching or disambiguation. They should not
become complete authority-source alias lists.

`roles` may record known repository roles such as composer, conductor, soloist,
arranger or librettist. A Person may have more than one role.

## Work Group

### Purpose

A Work Group represents the artistic family of one musical composition.

It groups Works that originate from the same underlying musical idea while
remaining distinct artistic Works in their own right.

### Required fields

```yaml
id: bruckner-symphony-3
composer_id: anton-bruckner
title: Symphony No. 3
```

Required:

- `id`;
- `composer_id`;
- `title`.

### Optional fields

```yaml
catalogue:
  wab: WAB 103
aliases:
  - Symphony No. 3 in D minor
description: >
  Shared context for the family of versions.
external_ids:
  musicbrainz: ...
  wikidata: ...
```

Only metadata that applies to the whole family belongs on the Work Group.
Version-specific metadata belongs on the Work.

## Work

### Purpose

A Work represents one distinct artistic composition or version.

Every Work belongs to exactly one Work Group.

### Required fields

```yaml
id: bruckner-symphony-3-1889
work_group_id: bruckner-symphony-3
composer_id: anton-bruckner
title: Symphony No. 3 in D minor
```

Required:

- `id`;
- `work_group_id`;
- `composer_id`;
- `title`.

### Optional fields

```yaml
version: 1889 version
catalogue:
  wab: WAB 103
year: 1889
key: D minor
instrumentation: orchestra
gem: true
aliases:
  - Symphony No. 3, 1889 version
relationships:
  - type: revision_of
    work_id: bruckner-symphony-3-1877
external_ids:
  musicbrainz: ...
  wikidata: ...
notes: >
  Local modelling note, only when needed.
```

`gem` is only a public presentation attribute. It must not affect migration,
validation, search priority or recommendation workflow.

Relationship vocabulary should remain sparse. It should describe real
work-to-work relationships, not performance-practice differences.

## Performance

### Purpose

A Performance represents one curatorially accepted interpretation of exactly one
Work.

Presence in canonical Performance data implies recommendation.

### Required fields

```yaml
id: haitink-rco-bruckner-symphony-3-1889
work_id: bruckner-symphony-3-1889
performers:
  - person_id: bernard-haitink
    role: conductor
  - name: Royal Concertgebouw Orchestra
    role: orchestra
```

Required:

- `id`;
- `work_id`;
- `performers`.

At least one performer must be present.

### Performer references

Prefer `person_id` when the performer has a canonical Person record.

Use `name` only when the performer is not yet canonical or is an ensemble whose
canonical modelling has not been finalised.

```yaml
performers:
  - person_id: martha-argerich
    role: piano
  - name: Chamber Orchestra of Europe
    role: orchestra
```

The initial schema permits free role strings. A controlled role vocabulary can
be introduced later if validation pressure justifies it.

### Optional fields

```yaml
profile: piano
version_assignment: unspecified
year: 1981
dates:
  recorded: 1981
location: Amsterdam
release:
  label: Philips
  catalogue_number: ...
  album_title: ...
links:
  tidal:
    url: https://tidal.com/...
reviews:
  gramophone:
    issue: 2021-10
    url: https://...
external_ids:
  musicbrainz_recording: ...
  musicbrainz_release: ...
  discogs_release: ...
keep_looking: true
notes: >
  Local identity note, only when needed.
```

`profile` is used only when a musically meaningful comparison category needs to
be preserved, such as piano versus harpsichord for a Bach keyboard concerto.
Instrumentation differences should normally be handled here or in Performance
metadata, not by creating additional Works.

`version_assignment: unspecified` may be used when a Performance is attached to
a general Work because the recording metadata does not identify a specific
version, completion or edition. It records uncertainty; it does not make the
Work Group performable and it must not be used when the recording might belong
to a different Work.

`release` is limited Performance metadata. It does not create a canonical
Release entity and does not define Performance identity.

`keep_looking: true` means only that the curator remains open to finding a
better recommendation. It must not automatically create searches or GitHub
Issues.

## Recommendation representation

There is no separate Recommendation entity in the minimal schema.

The initial rule is:

> A canonical Performance is a recommendation.

For each comparison category there is one public recommendation. A comparison
category consists of one Work and, when relevant, one performance profile.

During migration and listening, candidate Performances remain outside canonical
data until accepted.

## Candidate and migration data

Temporary candidates, listening queues, search results, duplicate evidence and
comparison state do not belong in `data/`.

They may be stored in:

- GitHub Issues;
- generated reports;
- migration review files;
- temporary artefacts under `generated/`, `cache/` or `reports/`.

Those artefacts may use looser structures, but they must not be treated as
canonical schema.

## Minimal validation rules

Before migration writes canonical data, validation should check:

1. YAML syntax is valid.
2. Required fields are present and non-empty.
3. IDs are unique within each entity type.
4. `composer_id` values reference existing Persons.
5. Every Work references exactly one existing Work Group.
6. Every Performance references exactly one existing Work.
7. No Performance references a Work Group.
8. Every Performance has at least one performer.
9. `keep_looking`, when present, is boolean.
10. Gramophone issues, when present, use `YYYY-MM`.
11. Duplicate-looking Persons, Work Groups, Works and Performances are reported
    for manual review.

Validation should detect uncertainty, not resolve it silently.

## Deferred decisions

The following are deliberately deferred:

- JSON Schema or another formal validation language;
- controlled vocabularies for performer roles;
- canonical modelling of ensembles;
- full identifier policy;
- complete external identifier coverage;
- link-check operational metadata;
- recommendation history;
- migration report schema.

These decisions can be made after the minimal canonical shape has been tested in
a pilot migration.

## Summary

The minimal schema is enough to migrate durable curator knowledge:

- Persons identify people;
- Work Groups organise artistic families;
- Works identify specific artistic versions;
- Performances store accepted recommendations.

Everything else remains temporary workflow state or deferred schema design.
