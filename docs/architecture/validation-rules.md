# Validation Rules

## Purpose and scope

This document defines repository validation rules for the classical music
recommendation repository.

Validation determines whether repository data is:

- structurally valid;
- internally consistent;
- editorially coherent;
- sufficiently trustworthy to commit, publish or use as migration output.

These rules describe repository invariants. They do not prescribe parser
implementation, storage technology, programming language or CI tooling.

Validation covers:

- canonical entity records;
- candidate entities produced by migration;
- references between entities;
- recommendation semantics;
- provenance;
- slugs and aliases;
- external identifiers and platform references;
- repository-wide consistency.

Validation does not cover:

- how source Markdown is parsed;
- how IDs are generated;
- how data files are physically laid out;
- how the website renders valid data;
- whether a curator's musical recommendation is aesthetically correct.

Migration rules define how legacy source material is converted into candidate
domain entities. Validation rules define whether those candidates, and the
canonical repository data produced from them, satisfy the architecture.

Validation is independent of parser and storage implementation. The same
invariant applies whether data is stored in YAML files, generated from Markdown,
loaded into a database or checked during CI.

## Normative language

The following terms are normative.

`MUST` means the rule is mandatory.

`MUST NOT` means the prohibited condition is invalid.

`SHOULD` means the rule is expected by default, but documented exceptions may be
accepted.

`SHOULD NOT` means the condition is discouraged and normally produces a warning
or review item.

`MAY` means the condition is permitted but not required.

## Severity levels

Validation findings use three severity levels.

| Severity | Meaning | Blocks repository write | Blocks migration acceptance | Blocks commit | Blocks CI | Blocks publication |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `error` | Violated invariant that makes data inconsistent or unsafe | yes | yes | yes | yes | yes |
| `warning` | Valid but ambiguous, suspicious or editorially incomplete | no | profile-dependent | no by default | no by default | profile-dependent |
| `info` | Non-blocking enrichment or quality observation | no | no | no | no | no |

Errors MUST block canonical repository writes, accepted migrations, normal CI and
publication builds.

Warnings MUST remain visible in reports. They MAY block strict profiles, selected
migration runs or publication builds when a project policy explicitly promotes
them.

Info findings MUST NOT block writes, commits, CI or publication.

Missing optional enrichment is not invalid data. It becomes an error only when it
breaks identity, required provenance or referential integrity.

## Validation lifecycle

Validation applies at several stages.

| Stage | Purpose | Typical profile |
| --- | --- | --- |
| Parsing or candidate creation | Check intermediate source records and candidate entities without requiring full repository completeness | `candidate` |
| Migration staging | Check that generated candidates can be safely written | `migration` |
| Before repository write | Block invalid canonical data | `repository` |
| Pre-commit | Catch local deterministic errors before commit | `repository` |
| CI | Re-run local invariants in a clean environment | `repository`, `publication` |
| Publication build | Ensure public-site inputs are coherent and reachable where required | `publication` |
| Periodic external validation | Check URLs and external services without making every build depend on them | `external` |

Some checks are deterministic and local. These include syntax, required fields,
ID uniqueness, referential integrity, duplicate keys and target-type validation.
They SHOULD run before repository writes and in CI.

Some checks depend on external services. These include remote URL availability,
Tidal lookup, MusicBrainz lookup and Discogs lookup. They SHOULD normally run in
periodic or manually invoked external validation. External service failure MUST
NOT invalidate otherwise consistent local data.

## Validation result model

Validation findings MUST be machine-readable and stable enough for reports,
baselines and review queues.

Example:

```yaml
validation_finding:
  rule_id: REC-004
  severity: error
  entity_type: recommendation
  entity_id: 01JYB83A93D7G4MK5KXHYVY6KP
  field: target_id
  message: recommended_recording recommendations must target a Recording.
  source_file: data/recommendations/example.yaml
  source_location:
    line: 18
  related_entities:
    - entity_type: work
      entity_id: 01JYB82P5Q4TF0C8MGRY9KGH0M
  suggested_action: Change target_type to recording and target_id to the resolved Recording ID.
```

Required fields:

- `rule_id`;
- `severity`;
- `message`.

Recommended fields:

- `entity_type`;
- `entity_id`;
- `field`;
- `source_file`;
- `source_location`;
- `related_entities`;
- `suggested_action`;
- `profile`;
- `provenance`.

Rule identifiers MUST be stable. Renaming a rule MUST preserve the old identifier
as an alias in reports or migration baselines.

Rule ID prefixes:

| Prefix | Area |
| --- | --- |
| `SCH` | schema and syntax |
| `IDN` | identity and identifiers |
| `REF` | referential integrity |
| `DOM` | domain invariants |
| `REC` | recommendations |
| `EDT` | editorial consistency |
| `PRO` | provenance |
| `EXT` | external references |
| `DUP` | duplicate detection |
| `REP` | repository-wide invariants |

## Schema validation

Schema validation checks whether records are structurally readable and use
allowed fields and value types. It does not decide musical identity on its own.

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| SCH-001 | Canonical YAML or equivalent storage files MUST be syntactically valid. | error | repository | yes |
| SCH-002 | Duplicate keys in a mapping MUST NOT occur. | error | repository | yes |
| SCH-003 | Required fields for the entity type MUST be present and non-empty. | error | repository | yes |
| SCH-004 | Empty optional values MAY exist only where the schema explicitly permits unresolved enrichment. | warning | repository | yes |
| SCH-005 | Unknown fields SHOULD produce warnings unless the file declares a compatible schema version that permits them. | warning | repository | yes |
| SCH-006 | Dates MUST use documented formats, normally `YYYY`, `YYYY-MM-DD` or explicitly textual source values with provenance. | error | repository | yes |
| SCH-007 | URLs MUST be syntactically valid absolute URLs when stored as links. | error | repository | yes |
| SCH-008 | Enumerated fields MUST use allowed values. | error | repository | yes |
| SCH-009 | Versioned schemas MUST declare a schema version when multiple incompatible shapes are supported. | warning | repository | yes |

Important entity-specific requirements:

| Entity | Required identity fields | Required relationship fields | Notes |
| --- | --- | --- | --- |
| Composer | `id`, preferred name or display name | none | Names may have aliases. |
| Work Group | `id`, `slug` or preferred label | member Works where represented | Non-performable. |
| Work | `id`, composer reference, title or title candidate | Work Group reference only when grouped | Pilot files may use `composer_id`, `canonical_title` or `preferred_title`. |
| Work Part | `id`, parent Work, title or number | parent Work | Supported when stored by the current model. |
| Person | `id`, preferred name | none | May be used for performers or contributors. |
| Ensemble | `id`, preferred name | none | May be used for orchestras, choirs and groups. |
| Recording | `id`, concrete Work or contents, principal credits, provenance | Work or Work Part reference | Provisional recordings may lack date and venue. |
| Release | `id`, title or platform reference | contained Recording or tracks when known | Digital platform releases are allowed. |
| Recommendation | `id`, `target_type`, `target_id`, `recommendation_type` | target entity | Recording recommendations and gems are separate. |
| External reference | platform or authority, item type when applicable, identifier or URL | owning entity | Original URLs SHOULD be retained. |
| Provenance | source file or authority, extraction/enrichment method | owning entity or field | Required for migrated data. |
| Alias | alias value, alias type where needed | owning entity | Must not collide with another entity. |
| Merge or retirement record | retired ID, surviving ID or retirement reason | target entity when merged | Retired IDs must remain reserved. |

Allowed value examples:

- `identification_status`: `provisional`, `identified`,
  `externally_enriched`, `platform_confirmed`.
- `recommendation_type`: `recommended_recording`, `gem`.
- `target_type`: `recording`, `work`.
- link `status`: `active`, `unavailable`, `broken`, `unknown`.
- Tidal `item_type`: `track`, `album`, `unknown`.

These enumerations MAY be extended by an ADR or schema update. Validators SHOULD
report unrecognised values as warnings in candidate profiles and errors in
repository profiles when the field is normative.

## Identity validation

Slugs are locators and editorial labels, not identity.

Internal identity is established by permanent identifiers. Internal foreign keys
MUST use permanent IDs, not slugs.

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| IDN-001 | Every canonical entity MUST have one globally unique permanent ID. | error | repository | yes |
| IDN-002 | A permanent ID MUST NOT change because metadata, slug, title or relationships change. | error | repository | partial |
| IDN-003 | A permanent ID MUST NOT be reused after deletion, merge or split. | error | repository | yes |
| IDN-004 | Canonical slugs MUST be unique within the relevant entity namespace. | error | repository | yes |
| IDN-005 | Slug aliases MUST NOT collide with active canonical slugs or aliases for another entity in the same namespace. | error | repository | yes |
| IDN-006 | Previous slugs MUST remain aliases after slug changes. | error | repository | partial |
| IDN-007 | Deprecated and merged IDs MUST resolve to a survivor or retirement record. | error | repository | yes |
| IDN-008 | External identifiers SHOULD be unique within authority, entity type and item type where the authority defines unique objects. | warning | repository | yes |
| IDN-009 | Confirmed duplicate external identifiers for two active entities of the same type are errors unless the external authority permits reuse. | error | repository | yes |
| IDN-010 | Provisional status MUST NOT change permanent identity rules. | error | repository | yes |
| IDN-011 | Fallback Release slugs such as `...-tidal-<album-id>` MAY change after enrichment, but the old slug MUST remain an alias. | error | repository | partial |
| IDN-012 | Internal references MUST NOT use slugs where permanent IDs are required. | error | repository | yes |

## Referential integrity

Every reference MUST resolve to an existing entity of the correct type, unless the
record is explicitly in a candidate profile that permits unresolved references.

| Rule ID | Reference | Required target |
| --- | --- | --- |
| REF-001 | Work composer reference, such as `composer_id` | Composer |
| REF-002 | Work `work_group_id` or equivalent membership | Work Group |
| REF-003 | Work Group members | Works |
| REF-004 | Work Part parent | Work |
| REF-005 | Recording `work_id`, `works[].work_id` or `recording_contents[].work_id` | Work |
| REF-006 | Recording `work_part_id` or `recording_contents[].work_part_id` | Work Part |
| REF-007 | Release track or contents reference | Recording |
| REF-008 | Recommendation target | Entity matching `target_type` |
| REF-009 | Work Relationship source and target | Works |
| REF-010 | Contributor credits | Person or Ensemble |
| REF-011 | Provenance source reference | source record or authority reference |
| REF-012 | Merge survivor reference | active or redirected entity |

Specific recommendation and Work Group rules:

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REF-020 | A `recommended_recording` recommendation MUST have `target_type: recording` and target an existing Recording. | error | repository | yes |
| REF-021 | A `gem` recommendation MUST have `target_type: work` and target an existing concrete Work. | error | repository | yes |
| REF-022 | A Recording MUST NOT point directly to a Work Group. | error | repository | yes |
| REF-023 | A Recommendation MUST NOT point to a Release unless a later domain model defines a Release-targeted recommendation type. | error | repository | yes |
| REF-024 | Aliases and merged identifiers referenced by source data MUST resolve to the current canonical entity or explicit retired record. | error | repository | yes |

## Domain validation

Domain validation checks musically meaningful invariants.

### Work and Work Group

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-001 | A Work Group MUST be non-performable. | error | repository | yes |
| DOM-002 | Recordings MUST NOT target Work Groups. | error | repository | yes |
| DOM-003 | A Work Group SHOULD contain at least two Works. | warning | repository | yes |
| DOM-004 | An empty Work Group is an error. | error | repository | yes |
| DOM-005 | A single-member Work Group is a warning unless it is a temporary migration candidate. | warning | repository | yes |
| DOM-006 | A Work MUST belong to no more than one Work Group unless a later architecture decision explicitly permits multiple groups. | error | repository | yes |
| DOM-007 | Work Group membership MUST be compatible with version, revision, arrangement, orchestration, completion, realisation, suite or comparable derivative relationships. | warning | repository | partial |
| DOM-008 | A single ordinary Work MUST NOT automatically receive a Work Group. | warning | migration | partial |

### Work relationships

Allowed relationship types include:

```text
version_of
revision_of
arrangement_of
orchestration_of
transcription_of
completion_of
realisation_of
suite_from
excerpt_from
part_of
based_on
adaptation_of
incorporates
```

The vocabulary is open to later extension, but repository validators SHOULD warn
when a relationship type is not documented.

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-020 | Work Relationships MUST connect a source Work to a target Work. | error | repository | yes |
| DOM-021 | Work Relationships MUST NOT self-reference. | error | repository | yes |
| DOM-022 | Derivative relationships such as `revision_of`, `arrangement_of`, `orchestration_of`, `transcription_of`, `completion_of`, `realisation_of` and `suite_from` are directional. | error | repository | yes |
| DOM-023 | Reciprocal storage of inverse derivative relationships SHOULD NOT occur unless explicitly modelled as a distinct relationship type. | warning | repository | yes |
| DOM-024 | Derivative and historical relationships MUST be acyclic where the relationship semantics require origin-to-derivative direction. | error | repository | yes |
| DOM-025 | Structural `part_of` relationships MUST NOT create parent-child cycles. | error | repository | yes |
| DOM-026 | Multiple relationship types between the same source and target SHOULD be reviewed unless each type records a distinct fact. | warning | repository | yes |
| DOM-027 | Relationship records SHOULD include provenance when imported, inferred or manually corrected. | warning | repository | partial |

### Versions and revisions

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-040 | Separate version Works MUST contain enough metadata to distinguish the version. | error | repository | partial |
| DOM-041 | Version labels SHOULD NOT be attached merely because of minor editorial editions. | warning | migration | partial |
| DOM-042 | A Recording linked to a version-specific Work MUST NOT also be ambiguously linked to an undifferentiated parent Work for the same recorded content. | error | repository | partial |
| DOM-043 | Version years and composition dates MUST NOT be conflated without provenance. | warning | migration | partial |

### Arrangements and derivative Works

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-060 | An independently represented arrangement, orchestration, transcription, completion or realisation MUST have its own Work identity. | error | repository | partial |
| DOM-061 | A derived Work SHOULD point to its source Work when known. | warning | repository | partial |
| DOM-062 | Responsible contributor and role SHOULD be recorded when known. | warning | repository | partial |
| DOM-063 | Musical identity changes MUST NOT be stored only as Release or Recording annotations when a separate Work is required. | error | migration | partial |

### Recordings

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-080 | Each Recording MUST represent a specific recorded performance. | error | repository | partial |
| DOM-081 | Each Recording MUST point to at least one concrete Work or Work Part. | error | repository | yes |
| DOM-082 | Principal credits MUST be present for provisional Recordings according to the minimum rules. | error | migration | partial |
| DOM-083 | Release differences, remastering and platform appearances MUST NOT automatically create new Recordings. | warning | migration | partial |
| DOM-084 | Multiple Release appearances MAY point to the same Recording. | info | repository | yes |
| DOM-085 | Probable duplicate Recordings SHOULD be warnings unless identity is proven. | warning | repository | partial |

### Releases

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-100 | A Release MUST be distinct from the Recording or Recordings it contains. | error | repository | partial |
| DOM-101 | A Tidal album MAY be a valid digital Release. | info | repository | yes |
| DOM-102 | A Tidal Release MUST NOT automatically be equated with an LP, CD, SACD or another digital issue. | warning | migration | partial |
| DOM-103 | Release tracks SHOULD have valid order or medium positions when track data is stored. | warning | repository | yes |
| DOM-104 | Each Release track reference MUST resolve to a Recording. | error | repository | yes |
| DOM-105 | Platform IDs MUST be unique within platform and item type where appropriate. | error | repository | yes |

## Recommendation validation

The repository recognises at least two recommendation types:

```text
recommended_recording
gem
```

These are separate editorial assertions. A source entry may create both.

### `recommended_recording`

Every legacy Markdown entry containing a Tidal link represents a recommendation
of the specific cited recorded performance.

Canonical semantics:

```yaml
target_type: recording
recommendation_type: recommended_recording
```

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REC-001 | `recommended_recording` MUST target a Recording. | error | repository | yes |
| REC-002 | The target Recording MUST exist. | error | repository | yes |
| REC-003 | Provenance MUST include the legacy Tidal source or another explicit editorial source. | error | migration | partial |
| REC-004 | The linked Recording MUST be connected to the Work represented by the source entry. | error | migration | partial |
| REC-005 | A Tidal URL or Tidal platform reference MUST be retained when Tidal was the source. | error | migration | yes |
| REC-006 | Multiple Tidal links resolving to the same Recording MUST NOT create duplicate active recommendations. | error | repository | partial |
| REC-007 | Repeated source occurrences SHOULD add provenance rather than duplicate editorial assertions. | warning | migration | partial |

### `gem`

A diamond marker:

```text
💎
```

represents a personal recommendation of the musical Work itself.

Canonical semantics:

```yaml
target_type: work
recommendation_type: gem
```

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REC-020 | `gem` MUST target a concrete Work. | error | repository | yes |
| REC-021 | The target Work MUST exist. | error | repository | yes |
| REC-022 | Provenance MUST record the diamond marker or later explicit editorial decision. | error | migration | partial |
| REC-023 | A gem MUST NOT target a Work Group. | error | repository | yes |
| REC-024 | A gem attached to a version, revision, completion or arrangement applies only to that concrete Work. | error | repository | partial |
| REC-025 | A gem MUST NOT automatically propagate to related versions or the Work Group. | error | repository | partial |
| REC-026 | Duplicate active gem recommendations for the same target and editorial source MUST be prevented. | error | repository | yes |

### Recommendation uniqueness

Recommendation uniqueness is based on:

```text
target_id + recommendation_type + editorial source
```

Multiple provenance records may support the same Recommendation. They MUST NOT
be mistaken for duplicate Recommendations.

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REC-040 | The absence of `💎` MUST NOT be interpreted as a negative Work recommendation. | error | migration | partial |
| REC-041 | The absence of a Tidal link MUST NOT be interpreted as a non-recommendation. | error | migration | partial |
| REC-042 | A Work with both a gem and recommended recordings is valid. | info | repository | yes |
| REC-043 | A Recording recommendation MUST NOT automatically make its Work a gem. | error | migration | partial |
| REC-044 | A Recommendation MUST NOT target a Release unless a later model defines such a type. | error | repository | yes |

## Editorial validation

Editorial validation keeps the repository coherent without turning harmless style
differences into identity errors.

| Rule ID | Area | Expected validation |
| --- | --- | --- |
| EDT-001 | Preferred names | SHOULD follow established English or source-authority usage. |
| EDT-002 | Diacritics | Display metadata SHOULD preserve correct diacritics; slugs MUST use ASCII normalisation. |
| EDT-003 | Transliteration | Canonical transliterations SHOULD be consistent; variants MAY be aliases. |
| EDT-004 | Title capitalisation | SHOULD be consistent within language and title style. |
| EDT-005 | Generic work titles | SHOULD follow naming conventions for word order and numbering. |
| EDT-006 | Opus and catalogue formatting | SHOULD use consistent compact forms and source-provenance where ambiguous. |
| EDT-007 | Keys | SHOULD normally be omitted from slugs unless needed for disambiguation. |
| EDT-008 | Version labels | MUST distinguish material versions when separately modelled. |
| EDT-009 | Contributor roles | SHOULD use consistent role labels while preserving credited names. |
| EDT-010 | Slugs | MUST satisfy naming conventions in canonical data. |
| EDT-011 | Aliases | SHOULD include important spelling, language and historical variants. |
| EDT-012 | Label and catalogue numbers | SHOULD preserve display value and normalised comparison value where useful. |
| EDT-013 | Tidal URLs | SHOULD be normalised to platform references while retaining original URL. |

Blocking editorial errors are limited to cases that create ambiguity, break
references or violate identity rules. Inconsistent but harmless display wording is
a warning or automatic normalisation opportunity.

## Provenance validation

Every entity created through migration MUST have adequate provenance.

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| PRO-001 | Migrated entities MUST record source filename. | error | migration | yes |
| PRO-002 | Migrated entities SHOULD record source location or source record ID. | warning | migration | yes |
| PRO-003 | Migrated entities MUST preserve original raw Markdown or a resolvable source record containing it. | error | migration | partial |
| PRO-004 | Tidal URL and platform ID MUST be retained when parsed from source. | error | migration | yes |
| PRO-005 | Extraction method SHOULD be recorded for migrated assertions. | warning | migration | partial |
| PRO-006 | Enrichment source and retrieval date SHOULD be recorded for externally enriched fields. | warning | external | partial |
| PRO-007 | Manual confirmation MUST NOT be claimed unless explicitly recorded. | error | repository | partial |
| PRO-008 | Conflicting assertions MUST NOT be silently overwritten. | error | migration | partial |
| PRO-009 | Provisional status SHOULD be recorded when identity or enrichment remains unresolved. | warning | migration | partial |
| PRO-010 | Inferred or enriched values MUST be distinguishable from literal source values. | error | migration | partial |
| PRO-011 | Source residue MUST NOT be silently discarded during migration. | error | migration | partial |

## External validation

External validation covers MusicBrainz IDs, Discogs IDs, Tidal track and album
IDs, Wikidata IDs, URLs, ISRCs, barcodes and label catalogue numbers.

External validation has three modes.

### Local format validation

Local format validation is deterministic and suitable for CI.

| Rule ID | Invariant | Severity |
| --- | --- | ---: |
| EXT-001 | External IDs MUST match the documented format for their authority when known. | error |
| EXT-002 | URLs MUST be syntactically valid. | error |
| EXT-003 | Platform item types MUST match known values such as `track` or `album`. | error |
| EXT-004 | Duplicate external IDs for active same-type entities SHOULD be reviewed; confirmed duplicates are covered by identity rules. | warning |

### Remote existence validation

Remote validation depends on external APIs and SHOULD normally run periodically.

| Condition | Severity |
| --- | ---: |
| API outage or rate limit | info |
| Temporary URL timeout | info |
| Unreachable URL after repeated checks | warning |
| Deleted platform item | warning |
| Malformed ID rejected locally | error |

### Semantic external validation

Semantic validation checks whether returned metadata plausibly matches the local
entity.

| Condition | Severity |
| --- | ---: |
| Metadata mismatch affecting identity | warning, error after confirmation |
| Different label/country/date for Release candidate | warning |
| Different Work or artist for external Work/Recording ID | warning |
| Confirmed external ID assigned to wrong entity type | error |

A remote service outage MUST NOT invalidate internally consistent local data.

A removed or changed Tidal URL MUST NOT erase the historical provenance of the
recommendation.

## Duplicate detection

Duplicate detection is a quality process. It MUST NOT automatically merge records
based only on similarity.

| Entity | Strong evidence | Weak evidence |
| --- | --- | --- |
| Composer | same authority ID, manually confirmed same person | same family name |
| Work | same composer plus same catalogue number and title; same MusicBrainz Work ID | same title only |
| Work Group | same compositional source and same version family | adjacent works on a page |
| Person | same authority ID and name/date match | same credited surname |
| Ensemble | same authority ID and organisational continuity | similar ensemble name |
| Recording | same Work, performers, date, venue and authority ID | same performers only |
| Release | same barcode or catalogue number plus label and track list | same cover image |
| Recommendation | same target, type and editorial source | same source line with unresolved target |

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DUP-001 | Confirmed duplicates MUST be merged or represented by explicit merge records. | error | repository | partial |
| DUP-002 | Probable duplicates SHOULD produce warnings. | warning | repository | partial |
| DUP-003 | Weak similarity SHOULD be info or no finding. | info | repository | partial |
| DUP-004 | The validator MUST NOT merge automatically based only on identical titles, performer credits, durations, album covers or similar slugs. | error | migration | partial |

## Repository-wide validation

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REP-001 | Canonical data directories MUST NOT contain orphaned files. | error | repository | yes |
| REP-002 | Merge records MUST NOT be unreferenced or dangling. | error | repository | yes |
| REP-003 | Aliases MUST resolve to exactly one active, merged or retired entity. | error | repository | yes |
| REP-004 | Active duplicate recommendations MUST NOT exist. | error | repository | yes |
| REP-005 | Empty Work Groups MUST NOT exist in canonical data. | error | repository | yes |
| REP-006 | No two canonical files may define the same permanent ID. | error | repository | yes |
| REP-007 | Temporary migration IDs MUST NOT appear in canonical data. | error | repository | yes |
| REP-008 | Unresolved conflict markers MUST NOT appear in committed data or docs. | error | repository | yes |
| REP-009 | Source files MUST NOT be written into generated-data directories. | error | repository | yes |
| REP-010 | Generated output MUST be deterministic where ordering and serialisation are defined. | error | repository | partial |
| REP-011 | Validation and migration MUST NOT create unrelated formatting churn. | warning | migration | partial |
| REP-012 | Required publication entities MUST be reachable from publication roots. | error | publication | partial |

Persons, Ensembles, Releases and external authorities MAY legitimately exist
before they are publicly reachable, provided they are valid and have provenance
or a clear repository purpose.

## Provisional data

Provisional data can be valid.

Allowed provisional conditions include:

- Recording without date or venue;
- digital Release without label or catalogue number;
- unresolved equivalence between a digital Release and a physical Release;
- incomplete performer roles;
- unconfirmed external match;
- unresolved enrichment from a platform source.

Provisional status MUST NOT excuse:

- missing permanent ID;
- missing required relationship;
- invalid target type;
- broken referential integrity;
- duplicate canonical identity;
- missing provenance.

## Validation profiles

| Profile | Purpose | Typical blocking severity |
| --- | --- | --- |
| `candidate` | Validate intermediate migration objects before full resolution. | errors that corrupt source preservation |
| `migration` | Block unsafe repository writes from migration output. | errors |
| `repository` | Full local invariant validation over canonical data. | errors |
| `publication` | Check all data needed by the public website. | errors, selected warnings |
| `external` | Perform remote platform and authority checks. | format errors locally; remote findings normally warnings/info |
| `strict` | Promote selected warnings to errors for cleanup campaigns. | errors and configured warnings |

Profile guidance:

- `SCH`, `IDN`, `REF`, core `DOM`, `REC` and `REP` errors belong in
  `repository`.
- Source-preservation `PRO` rules belong in `candidate` and `migration`.
- URL reachability and remote metadata checks belong in `external`.
- Public reachability and display completeness belong in `publication`.
- Duplicate suspicion belongs in `repository` as warnings unless confirmed.

## Reporting and exit behaviour

Validation reports MUST include:

- summary counts by severity;
- summary counts by rule ID;
- entity identifiers and types;
- source file and source location where available;
- deterministic ordering;
- machine-readable output;
- human-readable output.

Recommended exit codes:

| Code | Meaning |
| ---: | --- |
| 0 | no errors; warnings or info may exist |
| 1 | one or more errors |
| 2 | validator misuse, unreadable input or configuration error |
| 3 | external validation could not complete because of service failure |

Warnings MUST NOT be hidden merely to obtain a green build.

Suppressions or waivers MUST be:

- explicit;
- narrow;
- documented;
- attributable;
- optionally time-limited;
- visible in reports.

Legacy warning baselines MAY be used during migration. A baseline MUST identify
the specific rule and entity. New warnings outside the baseline MUST remain
visible.

## Rule implementation guidance

Each normative rule SHOULD be suitable for one or more automated tests.

Validators SHOULD separate:

- syntax checks;
- local deterministic graph checks;
- duplicate-candidate heuristics;
- external API checks;
- editorial linting.

Validators SHOULD NOT modify canonical data while reporting findings. Automatic
normalisation MAY be offered as a separate command, but it MUST produce
reviewable changes.

## Examples

The examples use current architecture field names. IDs are illustrative.

### Valid Recording recommendation

```yaml
recommendation:
  id: 01REC000000000000000000001
  target_type: recording
  target_id: 01RCD000000000000000000001
  recommendation_type: recommended_recording
  source_type: legacy_markdown_tidal_link
  provenance:
    source_file: docs/mahler.md
    raw_markdown: >
      **Symphony No. 5** [*Berliner Philharmoniker, Gustavo Dudamel*](https://tidal.com/browse/track/229400428)
    platform_reference:
      platform: tidal
      item_type: track
      platform_id: "229400428"
      original_url: https://tidal.com/browse/track/229400428
```

### Invalid Recording recommendation targeting a Work

```yaml
recommendation:
  id: 01REC000000000000000000002
  target_type: work
  target_id: 01WRK000000000000000000001
  recommendation_type: recommended_recording
```

Finding: `REC-001`, error.

### Valid gem

```yaml
recommendation:
  id: 01REC000000000000000000003
  target_type: work
  target_id: 01WRK000000000000000000001
  recommendation_type: gem
  source_type: legacy_markdown_gem_marker
  provenance:
    source_file: docs/mahler.md
    raw_marker: "💎"
```

### Invalid gem targeting a Work Group

```yaml
recommendation:
  id: 01REC000000000000000000004
  target_type: work_group
  target_id: 01WGP000000000000000000001
  recommendation_type: gem
```

Finding: `REC-023`, error.

### Work Group with version Works

```yaml
work_group:
  id: 01WGP000000000000000000001
  slug: bruckner-symphony-8
  preferred_title: Symphony No. 8
  members:
    - 01WRK0000000000000000001887
    - 01WRK0000000000000000001890

works:
  - id: 01WRK0000000000000000001887
    slug: bruckner-symphony-8-1887
    preferred_title: Symphony No. 8, 1887 version
    work_group_id: 01WGP000000000000000000001
    relationships:
      - type: version_of
        target_id: 01WRK0000000000000000001890

  - id: 01WRK0000000000000000001890
    slug: bruckner-symphony-8-1890
    preferred_title: Symphony No. 8, 1890 version
    work_group_id: 01WGP000000000000000000001
```

### Recording incorrectly targeting a Work Group

```yaml
recording:
  id: 01RCD000000000000000000002
  work_id: 01WGP000000000000000000001
  principal_credits:
    - entity_id: 01ENS000000000000000000001
```

Finding: `REF-022`, error.

### Arrangement with source relationship

```yaml
work:
  id: 01WRK000000000000000000010
  slug: mussorgsky-pictures-at-an-exhibition-ravel-orchestration
  preferred_title: Pictures at an Exhibition, Ravel orchestration
  composer_id: 01CMP000000000000000000001
  relationships:
    - type: orchestration_of
      target_id: 01WRK000000000000000000009
      contributor_id: 01PER000000000000000000001
      contributor_role: orchestrator
```

### Provisional Tidal Release

```yaml
release:
  id: 01REL000000000000000000001
  slug: dudamel-berlin-philharmonic-2022-tidal-123456789
  title: Mahler: Symphony No. 5
  medium: digital
  identification_status: platform_confirmed
  platform_references:
    - platform: tidal
      item_type: album
      platform_id: "123456789"
      original_url: https://tidal.com/browse/album/123456789
```

### Duplicate recommendation with multiple provenance sources

```yaml
recommendation:
  id: 01REC000000000000000000005
  target_type: recording
  target_id: 01RCD000000000000000000001
  recommendation_type: recommended_recording
  provenance:
    - source_file: docs/mahler.md
      source_record_id: mahler-31
    - source_file: docs/mahler.md
      source_record_id: mahler-78
```

This is valid. It is one Recommendation with multiple provenance records.

### Broken referential link

```yaml
recording:
  id: 01RCD000000000000000000003
  work_id: 01WRK_DOES_NOT_EXIST
```

Finding: `REF-005`, error.

### Slug collision

```yaml
works:
  - id: 01WRK000000000000000000001
    slug: bruckner-symphony-8-1890
  - id: 01WRK000000000000000000002
    slug: bruckner-symphony-8-1890
```

Finding: `IDN-004`, error.

### Cyclic Work relationship

```yaml
works:
  - id: 01WRK000000000000000000001
    relationships:
      - type: revision_of
        target_id: 01WRK000000000000000000002
  - id: 01WRK000000000000000000002
    relationships:
      - type: revision_of
        target_id: 01WRK000000000000000000001
```

Finding: `DOM-024`, error.

## Normative summary

1. Every canonical entity MUST have one unique immutable permanent ID.
2. Every internal reference MUST resolve to an existing entity of the correct type.
3. A Recording MUST refer to a concrete Work or Work Part, never a Work Group.
4. A Tidal-link recommendation MUST target a Recording.
5. A gem recommendation MUST target a concrete Work.
6. Recording recommendations and gems MUST remain separate assertions.
7. A Work Group MUST be non-performable and group related Works.
8. Independently represented arrangements and material versions MUST be separate Works.
9. Recommendations MUST be deduplicated without losing provenance.
10. Provisional data MAY be incomplete but MUST NOT violate identity, referential integrity or provenance requirements.
11. External service failure MUST NOT invalidate internally consistent repository data.
12. Validation findings MUST use stable rule IDs and explicit severity levels.
