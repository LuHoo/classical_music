# Migration Rules

## Purpose

This document defines how the existing composer Markdown files and related
source material are migrated into the new canonical model.

The migration converts editorial source material into:

- Person;
- Work Group;
- Work;
- Performance.

It does not create canonical Recording, Release, Recommendation, Track, Album or
Availability entities.

The minimal canonical YAML shapes are defined in `minimal-yaml-schemas.md`.
Migration source classification is defined in `source-inventory.md`.

## Core principles

### Source material is editorial input

The existing Markdown files combine several kinds of information in one line or
paragraph:

- composer and Work metadata;
- catalogue references;
- dates;
- version, revision, completion or arrangement labels;
- gem markers;
- performers;
- Tidal links;
- Gramophone references;
- occasional local notes.

A source entry must therefore never be copied directly into a single canonical
entity.

Migration decomposes each source entry into candidate facts, then resolves those
facts against the canonical model.

### Migration is staged

The migration pipeline is:

```text
source material
    ↓
parse source records
    ↓
create candidates
    ↓
resolve identities
    ↓
validate candidates
    ↓
manual review where needed
    ↓
write canonical data
```

No canonical file may be written before the relevant candidates pass validation
and any required manual review.

### Canonical data stores durable curator knowledge

Canonical data may store:

- accepted Person identities;
- accepted Work Group identities;
- accepted Work identities;
- accepted Performance recommendations;
- verified external identifiers and links when useful.

Canonical data must not store:

- listening queues;
- unreviewed candidate Performances;
- search results;
- comparison state;
- duplicate evidence;
- temporary migration identifiers.

Those belong in GitHub Issues, generated reports or temporary migration
artefacts.

### Migration must not invent certainty

When the source does not support a reliable decision, migration creates a
candidate, warning or review item.

It must not silently decide:

- whether two Persons are identical;
- whether two Works are the same artistic version;
- whether a Work belongs in an existing Work Group;
- whether two Tidal links represent the same Performance;
- whether a candidate Performance should replace an existing recommendation;
- whether a year is a composition, revision, recording or release year.

## Source units

### Composer file

Each legacy composer Markdown file provides a composer context.

The filename, page title and front matter may help identify a Person in the
composer role, but they are not themselves canonical identity.

The composer must be resolved to a canonical Person before Works from that file
are accepted.

### Source entry

A source entry is normally one Markdown paragraph describing a Work and,
optionally, a recommended Performance.

Example:

```markdown
[gem] **Symphony No. 5** (1901-02)
[*Berliner Philharmoniker, Gustavo Dudamel*](http://www.tidal.com/track/229400428)
```

This entry may produce:

- a Person reference for the composer;
- a Work Group candidate;
- a Work candidate;
- a Work-level `gem` value;
- a Performance recommendation candidate from the Tidal-linked performance;
- provenance for each parsed fact.

A source entry may produce more than one Work only when it explicitly describes
distinct artistic versions, revisions, completions, arrangements, suites or
other Works.

## Intermediate source records

Parsing first creates source-oriented records that preserve the original text and
do not yet assign canonical identity.

Example:

```yaml
source_record:
  source_file: docs/mahler.md
  source_location:
    heading_path:
      - Symphonies
    line_start: 31
    line_end: 32
  raw_markdown: >
    [gem] **Symphony No. 5** (1901-02)
    [*Berliner Philharmoniker, Gustavo Dudamel*]
    (http://www.tidal.com/track/229400428)
  parsed:
    gem_marker: true
    work_text: Symphony No. 5
    date_text: 1901-02
    credits_text:
      - Berliner Philharmoniker
      - Gustavo Dudamel
    tidal_links:
      - http://www.tidal.com/track/229400428
```

Intermediate source records must preserve:

- source file;
- source position where available;
- heading context;
- complete original Markdown;
- parsed fragments;
- all links;
- unparsed residue.

Unparsed residue must not be discarded.

## Person migration

Composer names are resolved to Person records.

When a Person does not yet exist, migration may create a Person candidate with:

- `id`;
- `name`;
- optional aliases;
- optional external identifiers;
- provenance.

The migration may propose `roles`, such as `composer`, `conductor` or `soloist`,
but roles do not create separate Person identities.

Possible duplicate Persons must be reported for review rather than merged
automatically.

## Work Group migration

Every accepted Work must belong to exactly one Work Group.

Migration should resolve an existing Work Group when the source entry belongs to
an already represented artistic family.

Migration should create a Work Group candidate when:

- a new Work is introduced;
- the Work does not belong to an existing Work Group;
- the Work belongs to a newly identified family of versions or derivations.

A Work Group may contain one Work. It does not need to wait for multiple Works
before it can exist.

Work Group metadata should include only values shared by all Works in the
family, such as composer and family title.

## Work migration

A Work candidate represents one distinct artistic composition or version.

Migration should resolve or create a Work candidate using:

- composer identity;
- title;
- catalogue number;
- version or revision label;
- arrangement, orchestration, completion or suite information;
- aliases;
- external identifiers where verified;
- local editorial context.

Composer revisions are separate Works within the same Work Group.

Different performers, instruments used in performance, labels, releases,
remasters, albums or Tidal links do not create new Works.

### Gem markers

The legacy diamond marker:

```text
gem
```

or its legacy symbol marks the Work:

```yaml
gem: true
```

`gem` is a Work-level public presentation attribute.

It must not:

- create a Performance;
- mark a Performance as better;
- affect search priority;
- trigger workflow;
- imply that all Performances of the Work are recommended.

## Tidal links and Performance recommendation candidates

Every legacy Tidal link represents a recommendation candidate for the cited
interpretation.

It must be interpreted as a Performance recommendation candidate, not as a
canonical Recording, Release or Recommendation entity.

The parsed source link should be retained in the candidate:

```yaml
performance_candidate:
  source_record_id: ...
  work_id: resolved-work-id
  performers:
    - name: Berliner Philharmoniker
      role: orchestra
    - name: Gustavo Dudamel
      role: conductor
  links:
    tidal:
      url: http://www.tidal.com/track/229400428
```

The candidate becomes a canonical Performance only after:

1. the Work is resolved;
2. the performers are sufficiently identified for presentation;
3. duplicate Performance checks pass or are reviewed;
4. the curator has listened and accepted it as a recommendation;
5. recommendation policy permits it in the relevant comparison category.

If a Work already has a public recommendation in the same comparison category,
the new item remains a candidate until editorial comparison is complete.

Migration must never replace an existing recommendation automatically.

## Performance profiles

A performance profile is assigned to a Performance candidate only when it
preserves a musically meaningful comparison category.

Examples include:

- piano;
- harpsichord.

Profiles may be proposed from metadata, but final profile assignment is a
curatorial classification.

Migration must not create a large predefined taxonomy of profiles.

## Gramophone references

A legacy Gramophone issue reference attached to a Tidal-linked entry belongs to
the Performance candidate.

Example:

```yaml
reviews:
  gramophone:
    issue: 2021-10
```

The repository stores only the reference. It must not copy review text,
quotations, ratings or extended critical metadata into canonical data.

## Candidate storage

Candidates and review artefacts must remain outside canonical data until
accepted.

Allowed locations include:

- GitHub Issues;
- generated migration reports;
- temporary review files under `generated/`, `cache/` or `reports/`.

Candidate files may use temporary IDs. Temporary IDs must not become canonical
IDs unless deliberately accepted.

## Canonical write rules

Migration may write canonical data only after validation confirms that:

- every Person record has required fields;
- every Work Group has required fields;
- every Work references exactly one Work Group;
- every Performance references exactly one Work;
- no Performance references a Work Group;
- candidate Performances are not written to `data/performances/`;
- `gem` remains on Work records;
- accepted Performance presence implies recommendation.

## Manual review triggers

Migration should create review items for:

- possible duplicate Persons;
- possible duplicate Work Groups;
- possible duplicate Works;
- possible duplicate Performances;
- uncertain Work Group assignment;
- uncertain Work/version boundary;
- uncertain performer identity;
- uncertain performance profile;
- multiple candidate Performances in the same comparison category;
- candidate replacement of an existing recommendation.

Manual review must resolve the editorial question before canonical data is
written.

## Summary

Migration converts legacy source material into candidates for the new canonical
model.

Old Tidal links become Performance recommendation candidates. They do not create
canonical Recording, Release or Recommendation entities.

Only accepted Persons, Work Groups, Works and Performances belong in canonical
data.
