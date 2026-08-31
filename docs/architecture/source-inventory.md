# Source Inventory

## Purpose

This document identifies which existing repository and side-material sources are
inputs for migration, and which sources are only background or review material.

It is a migration-planning document. It does not migrate data, define schemas or
change canonical records.

## Source priority

Migration should use the following priority order.

1. Current composer Markdown pages under `docs/`.
2. Existing Tidal exports and playlist spreadsheets.
3. Local Grove side materials for identity support, Work-boundary review and
   version evidence.
4. Composer-specific side materials for focused catalogue or boundary review.
5. MusicBrainz as a required authority check for Work identities,
   Work-to-Work relationships, external identifiers and recording/release
   matching evidence.
6. Wikipedia composition lists as fallback or supplementary authority evidence
   when local Grove, side materials or MusicBrainz are absent, incomplete or too
   narrow.
7. Existing pilot YAML and architecture documents as design context only.

When sources disagree, the canonical repository decision is made by curator
review. External or side-material sources do not override the curated Markdown
collection automatically.

## Primary migration inputs

### Current composer Markdown pages

Location:

```text
docs/*.md
```

Scope:

- 65 composer pages in the repository root `docs/` directory.
- Excludes `docs/architecture/`.

Migration role:

- primary source for the existing curated collection;
- primary source for Work selections;
- primary source for `gem` markers;
- primary source for legacy Tidal-linked Performance recommendation candidates;
- primary source for visible Gramophone issue references already present in the
  curated pages.

Allowed extraction:

- Person in composer role;
- Work Group candidates;
- Work candidates;
- Work-level `gem: true`;
- Tidal-linked Performance recommendation candidates;
- performer display text from linked recommendation lines;
- Gramophone issue references attached to recommendation lines;
- local notes needed to preserve identity decisions.

Not allowed:

- treating a Tidal link as a canonical Recording or Release;
- writing candidate Performances directly to canonical data;
- creating canonical data from ambiguous source text without review;
- treating Markdown formatting or filenames as permanent identity.

### Tidal exports and playlist spreadsheets

Locations:

```text
side materials/Music collection/Best Classical.csv
side materials/Music collection/Best Classical.xlsx
side materials/Music collection/Chamber Tidal.xlsx
side materials/Music collection/Piano Tidal.xlsx
side materials/Music collection/results_Best Classical (Tidal).xlsx
```

Migration role:

- source for Performance recommendation candidates;
- cross-check for existing Tidal links;
- source for candidate performer and platform metadata;
- source for identifying missing candidate Performances that are not yet present
  in the composer Markdown pages.

Allowed extraction:

- Tidal URLs or platform identifiers;
- track or album display text;
- performer and ensemble display text;
- Work and composer text as candidate matching evidence;
- playlist grouping context, such as piano or chamber, as possible review
  context.

Not allowed:

- automatically accepting playlist entries as canonical Performances;
- replacing existing recommendations automatically;
- inferring canonical Work identity solely from Tidal metadata;
- inferring a final performance profile solely from playlist membership;
- creating canonical Recording, Release, Album or Track entities.

### Grove side materials

Locations:

```text
side materials/Music collection/Grove/*.doc
side materials/Music collection/Grove/dIndy.xlsx
```

Migration role:

- secondary identity and work-boundary support;
- source for composer and Work disambiguation;
- source for version, revision, completion, arrangement and catalogue context.

Allowed extraction:

- composer identity evidence;
- Work title and catalogue evidence;
- version and revision distinctions;
- arrangement, orchestration, suite and completion context;
- aliases that help matching.

Not allowed:

- copying Grove text into canonical data;
- importing full biographies or complete work catalogues by default;
- treating Grove coverage as a requirement to include every listed Work;
- overriding curator decisions automatically.

Review workflow:

Grove should be checked first when migration reports uncertainty about:

- Work Group boundaries;
- version or revision identity;
- arrangement, orchestration, suite or completion status;
- whether a source distinction belongs to Work identity or Performance profile.

If Grove confirms a structural relationship, migration may update canonical YAML
after validation. If Grove does not cover the item, the item remains unresolved
until another authority source or curator decision resolves it.

### MusicBrainz

Location:

```text
https://musicbrainz.org/
```

Reference documentation:

- <https://musicbrainz.org/doc/Style/Classical/Works>
- <https://musicbrainz.org/doc/MusicBrainz_Entity>

Migration role:

- external authority source for stable MusicBrainz identifiers;
- relationship evidence for Persons, Works, Recordings, Releases and Artists;
- cross-check for Tidal-linked recommendation candidates;
- evidence for whether arrangements, revisions and derived Works are commonly
  represented as distinct Works;
- source for release and recording metadata attached to a Performance
  candidate.

Allowed extraction:

- MusicBrainz identifiers for matched Persons and Works;
- MusicBrainz Recording or Release identifiers as external evidence on
  Performance candidates;
- work-to-work relationship evidence;
- recording-to-work relationship evidence;
- credited performer, conductor, ensemble and release display metadata as
  matching evidence.

Not allowed:

- importing MusicBrainz as the canonical data model;
- creating canonical Recording, Release, Track, Album or Release Group entities;
- accepting MusicBrainz Work boundaries automatically when they conflict with
  curator decisions or better musicological evidence;
- promoting Performance candidates solely because MusicBrainz has a matching
  Recording or Release;
- copying annotations, biographies or extensive prose into canonical data.

Review workflow:

MusicBrainz should be checked after local Grove and composer-specific side
materials, or earlier when the open question is specifically about an external
identifier, Work relationship, recording, release or performer relationship.

MusicBrainz review is part of migration, not merely optional enrichment, when a
report flags uncertainty about:

- whether parsed rows are the same Work or separate Works;
- whether early, revised, arranged, completed or reconstructed forms should be
  grouped in one Work Group;
- whether a Tidal-linked row can be matched to concrete recording or release
  evidence.

If MusicBrainz confirms a stable external identifier or relationship, migration
may record that evidence. If it only shows that a recording exists, the item
remains a Performance recommendation candidate until the relevant Work and
curatorial recommendation decisions are resolved.

### Wikipedia composition lists

Location:

```text
https://en.wikipedia.org/wiki/List_of_compositions_by_<composer>
```

Migration role:

- fallback or supplementary authority evidence;
- useful when the local Grove export is missing, incomplete or too narrow;
- useful for confirming common version, revision, arrangement and genre facts.

Allowed extraction:

- work title and genre evidence;
- catalogue or opus evidence when present;
- version and revision notes;
- arrangement, suite, orchestration or completion context;
- high-level dating evidence.

Not allowed:

- bulk-importing all listed works;
- treating Wikipedia as more authoritative than the curated collection;
- copying article prose into canonical data;
- resolving controversial or ambiguous cases without curator review;
- promoting Performance candidates when recording-version assignment remains
  unclear.

Review workflow:

Wikipedia may support canonical YAML updates when it resolves a structural
uncertainty already raised by migration. The change should be documented in a
report or GitHub Issue comment, with unresolved cases left as review candidates.

## Secondary review inputs

### Legacy TeX collection files

Location:

```text
side materials/Music collection/*.tex
```

Scope:

- 49 TeX files at the top level of `side materials/Music collection/`.

Migration role:

- archival source for cross-checking earlier collection state;
- useful when current Markdown is ambiguous or appears incomplete;
- possible source for older titles, notes or recommendation context.

Allowed extraction:

- identity clues;
- older title variants;
- evidence that a current Markdown entry was derived from older notes;
- curator notes that still affect Work or Performance identity.

Not allowed:

- treating TeX files as more authoritative than current Markdown by default;
- bulk-importing entries absent from current Markdown without curator review;
- importing formatting or LaTeX structure as canonical data.

### Compiled music document

Locations:

```text
side materials/Music collection/music.tex
side materials/Music collection/music.pdf
```

Migration role:

- archival and review material;
- useful for checking how older TeX sources were assembled.

Not allowed:

- using the PDF as a primary parse source when the underlying Markdown or TeX is
  available;
- treating page layout as canonical structure.

### Building a Library and Gramophone-like spreadsheets

Locations:

```text
side materials/Music collection/Building a Library.xlsx
```

Migration role:

- background recommendation research;
- possible source for comparison candidates or Gramophone-related context.

Not allowed:

- automatically creating canonical Performances;
- automatically replacing recommendations;
- importing review text, ratings or full critical metadata.

### Composer-specific side files

Examples:

```text
side materials/strauss.xlsx
side materials/Music collection/stravinsky by k-number.xlsx
side materials/Music collection/bruckner
side materials/Music collection/stravinsky
side materials/Music collection/weill
side materials/Music collection/zemlinsky
```

Migration role:

- composer-specific research or catalogue support;
- useful for difficult Work Group and Work-boundary decisions.

Allowed extraction:

- catalogue identifiers;
- version labels;
- local disambiguation notes;
- aliases and title variants.

Not allowed:

- bulk-importing complete composer catalogues without curator approval;
- treating side files as canonical data in their present format.

## Existing repository data

### Pilot Work YAML

Location:

```text
data/works/
```

Migration role:

- existing pilot data and schema evidence;
- possible seed material after review and conversion to the current minimal
  schema.

Required review before reuse:

- rename or map `canonical_title` to the current `title` field;
- add `work_group_id`;
- confirm `composer_id` references canonical Person records;
- distinguish pilot examples from accepted canonical migration output.

Not allowed:

- assuming existing pilot YAML already satisfies the new canonical schema;
- migrating around the required Work Group relationship.

### Pilot artist data

Location:

```text
data/artists/
```

Migration role:

- identity pilot and matching aid.

Required review before reuse:

- map `artists` terminology to the current `Person` model where applicable;
- decide how ensembles will be handled before treating ensemble records as
  canonical;
- avoid carrying obsolete artist type assumptions into Person records.

### Pilot recording data

Location:

```text
data/recordings/
```

Migration role:

- superseded pilot material;
- may help understand earlier modelling experiments.

Not allowed:

- treating recordings as canonical migration targets;
- creating new canonical Recording or Release entities from these files;
- using pilot recording shape as the current Performance schema.

## Out-of-scope or background-only material

### Architecture documents

Location:

```text
docs/architecture/
```

Role:

- design and policy context;
- not a source of musical catalogue data.

### Top 2000 files

Location:

```text
side materials/Music collection/Top2000/
```

Role:

- out of scope for the classical music migration unless a later decision says
  otherwise.

### Wikipedia raw data

Location:

```text
side materials/Raw data wikipedia.xlsx
```

Role:

- background reference only.

Not allowed:

- determining canonical Work or Person identity automatically;
- bulk-importing external catalogue facts.

### Pilot Domain Model MindNode

Location:

```text
side materials/Pilot Domain Model.mindnode/
```

Role:

- architecture background only;
- not migration source data.

### System and generated files

Examples:

```text
docs/.DS_Store
side materials/.DS_Store
side materials/Music collection/.DS_Store
```

Role:

- ignored for migration.

## Migration-source classification

| Source family | Migration classification | Canonical write allowed directly |
| --- | --- | --- |
| `docs/*.md` composer pages | primary source | no, only after parsing, validation and review where needed |
| Tidal exports and playlist spreadsheets | primary candidate source | no |
| Grove files | secondary identity source | no |
| MusicBrainz | required external identifier and relationship review source | no |
| Legacy TeX files | secondary review source | no |
| Compiled `music.pdf` | background/review source | no |
| Building a Library spreadsheet | background candidate source | no |
| Composer-specific side files | secondary research source | no |
| Existing pilot Work YAML | pilot seed after review | no |
| Existing pilot artist YAML | pilot seed after review | no |
| Existing recording YAML | superseded pilot material | no |
| Architecture docs | design context | no |
| Top 2000 files | out of scope | no |
| MindNode model | architecture background | no |
| `.DS_Store` and system files | ignored | no |

## Open review questions

Before automated migration begins, the curator should confirm:

1. whether current `docs/*.md` pages are the authoritative starting collection;
2. whether TeX entries absent from current Markdown should be ignored by default
   or reported as possible missing historical entries;
3. whether `Best Classical.xlsx` or `Best Classical.csv` is the preferred source
   when both exist;
4. whether `results_Best Classical (Tidal).xlsx` is a curated export or an
   automated matching result;
5. whether Grove material should be converted into searchable text before
   migration review;
6. how MusicBrainz lookups should be cached or recorded for reproducible review;
7. how to treat ensembles before a canonical ensemble model is defined.

## Summary

The migration should start from the current composer Markdown pages and Tidal
exports.

Grove, MusicBrainz, TeX and composer-specific side materials support identity
review and boundary decisions.

Existing pilot YAML and architecture materials are design context, not canonical
migration input.

No source may write canonical data directly without parsing, validation and any
required curator review.
