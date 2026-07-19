# Migration Rules

> Status: Superseded for entity design by `repository-architecture.md`, `work.md`,
> `performance.md`, `recommendation-policy.md` and `workflow-design-notes.md`.
>
> This document records an earlier migration design that created Recording,
> Release and Recommendation entities. The current authoritative architecture
> treats migrated Tidal-linked entries as Performance recommendation candidates
> and promotes only curatorially accepted Performances into canonical data.

## Purpose

This document defines how the existing composer Markdown files are migrated into the structured music-collection repository.

The migration converts editorial source material into domain entities while preserving provenance, avoiding unsupported assumptions, and separating parsing from identity resolution and validation.

These rules govern:

- parsing source Markdown;
- creating candidate entities;
- resolving existing entities;
- creating Works, Work Groups, Recordings, Releases and Recommendations;
- interpreting Tidal links;
- interpreting gem markers;
- handling versions, arrangements and incomplete metadata;
- recording uncertainty and provenance;
- writing validated repository data.

The migration process must follow the domain model, identity rules, identifier policy and naming conventions defined elsewhere in `docs/architecture/`.

---

# 1. Core Principles

## 1.1 Source Markdown is editorial input, not the domain model

The existing Markdown files combine several kinds of information in a single line:

- composer and work metadata;
- catalogue references;
- dates;
- version or arrangement information;
- performers;
- Tidal links;
- editorial recommendations;
- gem markers;
- occasional notes or review dates.

A source line must therefore never be copied directly into a single repository object.

Migration decomposes each source entry into the appropriate domain entities and relationships.

## 1.2 Migration is staged

The migration pipeline is:

```text
Markdown source
      ↓
Parsing
      ↓
Intermediate source records
      ↓
Interpretation
      ↓
Candidate entities
      ↓
Entity resolution
      ↓
Relationship construction
      ↓
Validation
      ↓
Repository write
```

No repository file may be written before the candidate entities have passed validation.

## 1.3 Migration must be reproducible

Given the same source files, migration rules, authority data and resolution decisions, the migration must produce the same candidate model.

Automatic migration must not depend on:

- filesystem order;
- import order;
- database row numbers;
- temporary slugs;
- random inference;
- undocumented manual intervention.

Permanent identifiers may be generated during migration, but once accepted into the repository they must remain stable.

## 1.4 Migration must preserve provenance

Every migrated entity or field must retain enough provenance to determine:

- which source file contained the information;
- which source entry produced it;
- whether the value was parsed, inferred, enriched or manually confirmed;
- which external authority supplied enriched metadata;
- whether the value remains provisional.

Source Markdown remains an evidential source even after migration.

## 1.5 Migration must not invent certainty

When the source does not support a reliable decision, migration creates:

- a provisional entity;
- a candidate relationship;
- an unresolved reference;
- or a review item.

The migration must not silently guess:

- whether two recordings are identical;
- whether two versions are materially distinct;
- which historical release a Tidal album represents;
- which person performed an ambiguous role;
- whether a listed year is a composition, recording or release year.

---

# 2. Source Unit

## 2.1 Composer file

Each source Markdown file represents one composer context.

The front matter and heading may provide:

- preferred display name;
- source slug or filename;
- navigation order;
- external reference links.

The filename is not a permanent identifier.

The composer must be resolved by identity rules before source entries are migrated.

## 2.2 Source entry

A source entry is normally one Markdown paragraph describing a musical work and possibly one or more recommended recordings.

Example:

```markdown
💎 **Symphony No. 5** (1901–02)
[*Berliner Philharmoniker, Gustavo Dudamel*](http://www.tidal.com/track/229400428)
```

This entry contains at least:

- a Work candidate;
- a Work-level gem recommendation;
- a Recording candidate;
- a digital Release candidate or reference;
- a Recording-level recommendation;
- provenance.

A single source entry may produce multiple Works when it explicitly describes versions, arrangements, completions or derivative forms.

---

# 3. Intermediate Source Record

Parsing must first create a source-oriented intermediate record.

The intermediate record preserves source wording and does not yet assign domain identity.

Example:

```yaml
source_record:
  source_file: data/legacy/mahler.md
  source_location:
    heading_path:
      - Middle period
    line_start: 31
    line_end: 32

  raw_markdown: >
    💎 **Symphony No. 5** (1901–02)
    [*Berliner Philharmoniker, Gustavo Dudamel*]
    (http://www.tidal.com/track/229400428)

  parsed:
    gem_marker: true
    work_text: Symphony No. 5
    date_text: 1901–02
    credits_text:
      - Berliner Philharmoniker
      - Gustavo Dudamel
    tidal_links:
      - http://www.tidal.com/track/229400428
```

The intermediate record must preserve:

- the complete original Markdown;
- source filename;
- heading hierarchy;
- source position where available;
- all parsed text fragments;
- all links;
- unparsed residue.

Unparsed residue must not be discarded.

---

# 4. Parsing Rules

## 4.1 Work text

The parser should recognise, where present:

- preferred title;
- generic work type;
- conventional number;
- catalogue system and number;
- key;
- nickname;
- composition date;
- version or revision label;
- scoring;
- arranger, orchestrator, editor or completer;
- completion status;
- source comments.

Parsing only extracts candidate facts. It does not establish identity.

## 4.2 Tidal links

Every source entry containing a Tidal link represents the user's recommendation of the specific cited performance or recording.

This is a Recording-level recommendation.

The source link must be parsed into:

```yaml
platform_reference:
  platform: tidal
  item_type: track | album | unknown
  platform_id: ...
  original_url: ...
```

The original URL must always be retained, even after normalising the platform ID.

Where a source entry contains multiple Tidal links, each link is a separate recommendation candidate unless the source clearly indicates that the links are alternatives representing the same recording.

## 4.3 Gem marker

The diamond marker:

```text
💎
```

represents a personal Work-level recommendation.

It means that the user considers the Work itself a gem that others should hear.

It does **not** recommend only the cited performance.

The gem marker must therefore create or update a Work-level recommendation:

```yaml
recommendation:
  target_type: work
  recommendation_type: gem
  source: editorial
```

A source entry may contain both:

- a Work-level gem recommendation;
- a Recording-level recommendation created from its Tidal link.

These are distinct recommendations and must never be collapsed.

## 4.4 Recommendation semantics

The migration recognises at least two recommendation types.

### Recording recommendation

Triggered by a Tidal link.

```yaml
recommendation:
  target_type: recording
  recommendation_type: recommended_recording
```

Meaning:

> This particular recording or performance is recommended.

### Work gem recommendation

Triggered by `💎`.

```yaml
recommendation:
  target_type: work
  recommendation_type: gem
```

Meaning:

> This Work is a personal gem and is especially recommended for listening.

The absence of a gem marker does not imply a negative judgement about the Work.

The absence of a Tidal link means only that no specific recording recommendation is encoded in that source entry.

## 4.5 Editorial dates and annotations

Parenthetical dates following a Tidal recommendation may represent:

- the user's date of addition;
- a review month;
- a release date;
- or another editorial annotation.

They must not automatically be interpreted as recording or release dates.

Unless the meaning is explicitly established, they remain:

```yaml
source_annotation:
  raw_value: "12/2025"
  interpretation_status: unresolved
```

---

# 5. Composer Resolution

Before Work candidates are resolved, the composer must be matched to an existing Composer entity.

Resolution may use:

- exact preferred name;
- recognised aliases;
- normalised family name;
- filename;
- MusicBrainz composer ID;
- Wikidata ID;
- manually confirmed mapping.

A new Composer may be created only when no existing identity matches.

Spelling differences, diacritics and transliteration variants must not create duplicate Composer entities.

---

# 6. Work Candidate Construction

A parsed source record creates a Work candidate containing:

```yaml
work_candidate:
  composer_id: ...
  preferred_title_candidate: ...
  work_type_candidate: ...
  number_candidate: ...
  catalogue_candidates: [...]
  key_candidate: ...
  date_candidates: [...]
  scoring_candidate: ...
  version_candidate: ...
  derivative_candidate: ...
  source_record_id: ...
```

The candidate remains source-oriented until entity resolution is complete.

---

# 7. Work Resolution

## 7.1 Resolution order

A Work candidate should be matched using the following evidence, in descending importance:

1. confirmed external Work identifier;
2. existing manually confirmed source mapping;
3. composer plus catalogue system and catalogue number;
4. composer plus normalised title and conventional number;
5. composer plus title, scoring, date and version information;
6. aliases and historical titles.

No single field other than a confirmed permanent external identifier is universally decisive.

## 7.2 Existing Work

When the candidate matches an existing Work:

- the existing permanent ID is reused;
- new aliases may be added;
- missing metadata may be proposed as enrichment;
- contradictory metadata creates a review item;
- no duplicate Work is created.

## 7.3 New Work

A new Work may be created when:

- no existing Work identity matches;
- the candidate represents a performable musical object;
- enough metadata exists to distinguish it from other Works by the same composer;
- required identity and naming validations pass.

The minimum initial Work metadata is:

```yaml
work:
  id: ...
  composer_id: ...
  slug: ...
  preferred_title: ...
  provenance: ...
```

At least one of the following should normally also be known:

- conventional number;
- catalogue number;
- distinctive title;
- scoring;
- version designation;
- composition date.

---

# 8. Work Groups

## 8.1 Creation rule

A Work Group is created when two or more separately modelled Works belong to the same compositional family.

Examples include:

- original and revised versions;
- original and completed forms;
- composition and orchestration;
- ballet and suite;
- original scoring and arrangement.

A Work Group must not be created solely in anticipation of possible future variants.

## 8.2 Migration into an existing Work Group

When a newly resolved Work belongs to an existing Work Group:

- the Work is added as a member;
- the appropriate Work-to-Work relationship is recorded;
- the Work Group identity remains unchanged.

## 8.3 Creation from an existing single Work

When a second related Work is introduced and no Work Group exists:

1. retain the existing Work ID;
2. create a new Work Group;
3. add the existing Work and the new Work as members;
4. retain all existing Recording and Recommendation links to the concrete Work;
5. do not redirect Work references to the Work Group.

The Work Group is a grouping entity, not a replacement for the Work.

---

# 9. Versions and Revisions

## 9.1 Separate Work identity

A version or revision receives a separate Work identity when it:

- functions as a meaningful independent performance object; and
- is relevant to identification, recommendation or presentation in the collection.

Evidence may include:

- a fixed version year;
- separate score or edition;
- materially different structure;
- materially different scoring;
- different text or recitation;
- independent performance practice;
- separate catalogue or opus designation;
- explicit choice of version on recordings or programmes.

## 9.2 Cases not automatically split

The following do not normally create separate Works:

- minor editorial corrections;
- alternative scholarly editions without a materially different composition;
- remastering;
- interpretation choices;
- ordinary cuts made in a particular performance;
- performance duration differences;
- different cadenzas used only as performance choices.

## 9.3 Uncertain version boundaries

When the source indicates versions but the material distinction is not established:

```yaml
modelling_status: requires_version_research
version_candidates:
  - ...
```

The migration must not automatically split the Work.

A split becomes necessary when a Recording or Recommendation cannot otherwise be assigned to the correct musical object.

---

# 10. Arrangements and Other Derivative Works

## 10.1 General rule

An arrangement, orchestration, transcription, suite, completion or realisation receives a separate Work identity once it is independently included in the collection.

It must receive a separate Work identity whenever:

- a Recording is linked to it;
- a Tidal recommendation refers to it;
- a Work-level recommendation refers specifically to it;
- it is presented independently in the public collection.

## 10.2 Derivative relationship

The derived Work must link to its source Work using the most specific available relationship:

```text
arrangement_of
orchestration_of
transcription_of
completion_of
realisation_of
suite_from
revision_of
version_of
```

The responsible contributor and role should be recorded when known.

## 10.3 Unrecommended arrangements

Arrangements merely mentioned in source notes do not need to be fully modelled unless they are independently included as collection objects.

They may remain as:

```yaml
derivative_candidate:
  status: not_modelled
```

---

# 11. Recording Migration

## 11.1 Trigger

Every valid Tidal link creates a Recording candidate and a Recording-level recommendation candidate.

The migration must not attach the recommendation directly to the Work.

## 11.2 Minimum metadata for a provisional Recording

A provisional Recording may be created when the following are known:

```yaml
recording:
  id: ...
  work_id: ...
  principal_credits: [...]
  source_platform:
    platform: tidal
    item_type: track
    platform_id: ...
    original_url: ...
  identification_status: provisional
```

Required:

- a concrete Work;
- at least one principal performer or ensemble;
- a resolvable Tidal reference;
- provenance.

For classical recordings, the migration should attempt to identify:

- conductor;
- orchestra or ensemble;
- soloist or soloists;
- choir;
- other principal credited performers.

Missing recording date or venue does not block provisional creation.

## 11.3 Recording resolution

A Recording candidate should be matched against existing Recordings using:

- MusicBrainz Recording ID;
- ISRC, with caution;
- same Work;
- same principal performers;
- recording date and venue;
- duration;
- release appearances;
- platform identifiers;
- manually confirmed equivalence.

A Tidal track ID identifies a platform track, not necessarily the underlying Recording across all releases.

Therefore:

- the same Tidal track ID is strong evidence for the same platform item;
- different Tidal track IDs may still refer to the same Recording;
- identical credits alone are insufficient to merge Recordings.

When identity remains uncertain, create or retain separate provisional Recording candidates and flag them for review.

## 11.4 Multi-work tracks

A Tidal track may contain:

- one Work;
- one movement or Work Part;
- several short Works;
- an excerpt;
- a medley.

The migration must not force a one-to-one Work relationship when the source or metadata indicates otherwise.

Possible structures include:

```yaml
recording_contents:
  - work_id: ...
  - work_part_id: ...
```

A Recommendation still targets the Recording as a whole unless the source explicitly limits it to one Work or part.

---

# 12. Release Migration

## 12.1 Tidal album as digital Release

A Tidal album may create a provisional digital Release when enough album-level metadata can be retrieved.

Minimum metadata:

```yaml
release:
  id: ...
  title: ...
  primary_artists: [...]
  release_date: ...
  medium: digital
  platform_references:
    - platform: tidal
      item_type: album
      platform_id: ...
      original_url: ...
  identification_status: platform_confirmed
```

The relevant track-to-Recording relationships must also be stored.

## 12.2 Missing label or catalogue number

Label and catalogue number are desirable but do not block creation of a provisional digital Tidal Release.

When they are unavailable, the fallback slug may use the Tidal album ID according to `naming-conventions.md`.

## 12.3 No automatic historical identification

A Tidal album must not automatically be identified as:

- the original LP;
- a particular CD issue;
- a SACD;
- another platform's digital edition;
- a physical release sharing the same cover.

Such equivalence requires external authority evidence or manual confirmation.

## 12.4 Release resolution

Release matching may use:

- MusicBrainz Release ID;
- Discogs release ID;
- barcode or UPC;
- label and catalogue number;
- exact track listing;
- release date and country;
- platform album ID;
- copyright and phonogram data.

Conflicting evidence produces a review item rather than an automatic merge.

---

# 13. Recommendation Migration

## 13.1 Recording recommendations from Tidal links

For every valid Tidal link:

```yaml
recommendation:
  id: ...
  target_type: recording
  target_id: ...
  recommendation_type: recommended_recording
  source_type: legacy_markdown_tidal_link
  provenance: ...
```

If several links refer to the same resolved Recording, only one active recommendation is required, but all source references must remain in provenance.

## 13.2 Work gems from diamond markers

For every gem marker:

```yaml
recommendation:
  id: ...
  target_type: work
  target_id: ...
  recommendation_type: gem
  source_type: legacy_markdown_gem_marker
  provenance: ...
```

The gem applies to the specific Work represented by the source entry.

When the entry describes a particular version or arrangement, the gem applies to that concrete Work, not automatically to the entire Work Group.

## 13.3 Entries containing both

An entry with both `💎` and a Tidal link creates two recommendations:

```text
Work ── gem recommendation

Recording ── recommended-recording recommendation
```

The Recording links to the Work, but the recommendations remain separate editorial assertions.

## 13.4 Recommendation uniqueness

A Recommendation should be unique by:

```text
target_id + recommendation_type + editorial source
```

Repeated source occurrences should add provenance rather than create duplicate active Recommendation entities.

---

# 14. External Enrichment

## 14.1 Enrichment order

Where available, external enrichment should normally proceed from:

1. Tidal platform metadata;
2. MusicBrainz;
3. Discogs;
4. Wikidata or Wikipedia;
5. specialist catalogues or editorial sources;
6. manual confirmation.

No external source is universally authoritative for every field.

## 14.2 Field-level provenance

External enrichment must be recorded at field level where practical.

Example:

```yaml
release_date:
  value: 1985
  provenance:
    source: tidal
    retrieved_at: ...
    status: unconfirmed
```

A later confirmed value may replace it without changing the entity ID.

## 14.3 Conflicts

When sources disagree:

- do not silently overwrite;
- retain competing assertions where useful;
- apply source-priority rules if defined;
- create a review item when the difference affects identity;
- record the final editorial decision.

---

# 15. Identifier Assignment

## 15.1 Candidate stage

Intermediate source records and unresolved candidates may use temporary migration identifiers.

These temporary identifiers must never appear in committed repository relationships.

## 15.2 Accepted entities

Permanent IDs are assigned when:

- the entity is accepted for repository creation; or
- an existing entity is matched.

Once committed, the permanent ID is never regenerated because metadata or slugs change.

## 15.3 Merges

When migration discovers duplicates:

- choose the surviving entity according to identity rules;
- redirect all references;
- preserve the retired ID as a merged identifier;
- preserve all provenance;
- never reuse the retired ID.

---

# 16. Slug Generation

Slugs are generated only after entity type and identity are sufficiently established.

Slug generation follows `naming-conventions.md`.

Migration must not use slugs as internal foreign keys.

A provisional fallback slug may later change, especially for Releases, but:

- the permanent ID remains unchanged;
- the old slug becomes an alias;
- URLs must remain resolvable where required.

---

# 17. Review Queue

Migration must produce an explicit review queue for unresolved cases.

Review reasons include:

```text
ambiguous_composer
ambiguous_work
possible_duplicate_work
possible_duplicate_recording
possible_duplicate_release
uncertain_version_boundary
unresolved_arrangement
missing_principal_credit
tidal_lookup_failed
conflicting_catalogue_number
conflicting_release_metadata
unparsed_source_residue
```

Each review item must contain:

- source record;
- candidate entities;
- conflicting evidence;
- proposed options;
- reason automatic resolution was refused.

---

# 18. Failure Handling

## 18.1 Local failure

Failure to migrate one source entry must not corrupt other successfully parsed entries.

The failed entry remains in the migration report with its raw source preserved.

## 18.2 External lookup failure

When Tidal or another authority cannot be reached:

- retain the parsed platform ID and original URL;
- create no unsupported enriched values;
- mark the lookup status;
- allow later retry.

A Tidal-link recommendation must not be lost merely because enrichment temporarily fails.

## 18.3 Broken links

A broken or unavailable Tidal link remains provenance for the original recommendation.

It may create a review item and a provisional Recording candidate when the source credits and Work are sufficient.

The original URL must not be deleted.

---

# 19. Repository Write Rules

Repository writes must be:

- atomic;
- deterministic;
- validated;
- reviewable in version control.

The migration should generate changes in a staging directory or branch before they are accepted into the canonical data directories.

A repository write may include:

- new entities;
- enriched fields;
- aliases;
- relationships;
- Recommendations;
- provenance records;
- review items.

The migration must not rewrite unrelated entities merely to change formatting or field order.

---

# 20. Idempotency

Running the migration repeatedly over the same unchanged source must not create:

- duplicate Works;
- duplicate Work Groups;
- duplicate Recordings;
- duplicate Releases;
- duplicate Recommendations;
- new permanent IDs for existing entities.

Repeated runs may enrich or resolve provisional entities when new authority data or decisions become available.

---

# 21. Migration Reporting

Every migration run should produce a report containing:

```yaml
migration_report:
  source_files_processed: ...
  source_records_parsed: ...
  composers_matched: ...
  composers_created: ...
  work_groups_created: ...
  works_matched: ...
  works_created: ...
  recordings_matched: ...
  recordings_created: ...
  releases_matched: ...
  releases_created: ...
  recording_recommendations_created: ...
  work_gems_created: ...
  review_items_created: ...
  failed_records: ...
```

The report should also list all automatic merges and all cases where existing metadata would change.

---

# 22. Recommended Initial Migration Strategy

The first production migration should be conservative.

## Pass 1 — Source extraction

Create intermediate source records for all Markdown entries without writing domain entities.

Validate parsing completeness and unparsed residue.

## Pass 2 — Composer and Work migration

Resolve or create:

- Composers;
- Works;
- Work Groups;
- Work relationships;
- Work-level gem Recommendations.

Do not yet create Releases unless necessary.

## Pass 3 — Tidal enrichment

For every Tidal link:

- resolve track and album IDs;
- retrieve metadata;
- create or match Recordings;
- create Recording-level Recommendations;
- create provisional digital Releases where minimum metadata exists.

## Pass 4 — External authority enrichment

Attempt matching with:

- MusicBrainz;
- Discogs;
- other approved authority sources.

## Pass 5 — Human review

Resolve:

- uncertain versions;
- duplicate recordings;
- ambiguous releases;
- unresolved credits;
- failed Tidal lookups.

## Pass 6 — Repository commit

Write only accepted and validated entities.

---

# 23. Normative Summary

The following rules are mandatory:

1. Source Markdown must first be parsed into intermediate source records.
2. Repository entities must not be written before resolution and validation.
3. Every Tidal link represents a recommendation of a specific Recording.
4. Every diamond marker represents a Work-level `gem` recommendation.
5. A source entry may create both recommendation types.
6. Recommendations must never be inferred from the mere presence of a Work without a Tidal link or gem marker.
7. A Recording recommendation must target a Recording, not a Work or Release.
8. A gem recommendation must target the specific Work, not automatically its Work Group.
9. Versions receive separate Work identities only when they are meaningful independent performance objects and relevant to the collection.
10. Independently included arrangements and derivative forms receive separate Work identities.
11. A Work Group is created only when two or more related Works require grouping.
12. A Tidal track or album ID is a platform identifier, not a permanent internal identity.
13. Provisional entities are permitted where minimum metadata exists and uncertainty is explicit.
14. Migration must preserve provenance and unresolved source text.
15. Repeated migration must be idempotent.
