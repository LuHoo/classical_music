# Validation Rules

## Purpose and scope

This document defines the validation rules required before automated migration
can write canonical data.

Validation applies to the canonical model:

- Person;
- Work Group;
- Work;
- Performance.

It does not validate separate canonical Recording, Release, Recommendation,
Track, Album or Availability entities because the current architecture does not
define them.

The minimal YAML shapes are defined in `minimal-yaml-schemas.md`. Migration
rules are defined in `migration-rules.md`.

## Normative language

`MUST` means the rule is mandatory.

`MUST NOT` means the prohibited condition is invalid.

`SHOULD` means the rule is expected by default, but documented exceptions may be
accepted after review.

`MAY` means the condition is permitted but not required.

## Severity levels

| Severity | Meaning | Blocks canonical write | Blocks CI | Blocks publication |
| --- | --- | ---: | ---: | ---: |
| `error` | Violated invariant that makes data inconsistent or unsafe | yes | yes | yes |
| `warning` | Ambiguous, suspicious or incomplete data that needs visibility | no | no by default | no by default |
| `info` | Non-blocking enrichment or report detail | no | no | no |

Errors must block migration acceptance and canonical repository writes.

Warnings must remain visible in reports and may be promoted to errors by a
stricter migration profile.

## Validation profiles

| Profile | Purpose |
| --- | --- |
| `candidate` | Validate parsed source records and migration candidates before manual review. |
| `migration` | Validate accepted candidates before writing canonical files. |
| `repository` | Validate canonical data in `data/`. |
| `publication` | Validate data needed to generate the public website. |
| `external` | Validate external services such as streaming links without blocking ordinary local correctness. |

Local deterministic checks should run before canonical writes and in CI.

External-service checks should run only in manual or periodic profiles. A Tidal
or MusicBrainz outage must not invalidate otherwise coherent canonical data.

## Validation result model

Validation findings should be machine-readable.

Example:

```yaml
validation_finding:
  rule_id: REF-030
  severity: error
  entity_type: performance
  entity_id: haitink-rco-bruckner-symphony-3-1889
  field: work_id
  message: Performance must reference an existing Work, not a Work Group.
  source_file: data/performances/haitink-rco-bruckner-symphony-3-1889.yaml
```

Recommended fields:

- `rule_id`;
- `severity`;
- `message`;
- `entity_type`;
- `entity_id`;
- `field`;
- `source_file`;
- `source_location`;
- `related_entities`;
- `suggested_action`;
- `profile`.

Rule identifiers should remain stable once reports depend on them.

## Rule prefixes

| Prefix | Area |
| --- | --- |
| `SCH` | schema and syntax |
| `IDN` | identifiers |
| `REF` | referential integrity |
| `DOM` | domain invariants |
| `REC` | recommendation semantics |
| `CAN` | candidate containment |
| `DUP` | duplicate detection |
| `EXT` | external references |

## Schema and syntax

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
| IDN-011 | Fallback Performance slugs such as `<work-slug>-<profile-or-performer-label>` MAY change after enrichment, but the old slug MUST remain an alias. | error | repository | partial |
| IDN-012 | Internal references MUST NOT use slugs where permanent IDs are required. | error | repository | yes |

At least one performer entry is required for every canonical Performance.

## Identifier rules

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| IDN-001 | IDs MUST be unique within each canonical entity type. | error | repository | yes |
| IDN-002 | IDs MUST use lowercase ASCII slug form until a separate identifier policy defines otherwise. | error | repository | yes |
| IDN-003 | IDs MUST NOT be reused for a different entity after deletion, merge or split. | error | repository | partial |
| IDN-004 | A changed title, alias, role, performer list or link MUST NOT require a changed ID. | error | repository | partial |
| IDN-005 | Temporary candidate IDs MUST NOT be written as canonical IDs unless explicitly accepted. | error | migration | partial |

## Referential integrity

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REF-001 | `Work Group.composer_id` MUST reference an existing Person. | error | repository | yes |
| REF-002 | `Work.composer_id` MUST reference an existing Person. | error | repository | yes |
| REF-003 | `Work.work_group_id` MUST reference an existing Work Group. | error | repository | yes |
| REF-004 | `Performance.work_id` MUST reference an existing Work. | error | repository | yes |
| REF-005 | A Performance MUST NOT reference a Work Group. | error | repository | yes |
| REF-006 | Work relationships MUST reference existing Works. | error | repository | yes |
| REF-007 | Performer `person_id` values MUST reference existing Persons. | error | repository | yes |

The key migration-blocking rules are:

- every Work has exactly one Work Group;
- every Performance refers to exactly one Work;
- no Performance refers to a Work Group.

## Work Group rules

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-001 | A Work Group MUST be non-performable. | error | repository | yes |
| DOM-002 | A Work Group MUST NOT have Performances attached directly. | error | repository | yes |
| DOM-003 | A Work Group MUST NOT have recommendation status. | error | repository | yes |
| DOM-004 | A Work Group MAY contain one or more Works. | info | repository | yes |
| DOM-005 | Duplicate-looking Work Groups SHOULD be reported for manual review, not merged automatically. | warning | repository | partial |

## Work rules

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-020 | Every Work MUST belong to exactly one Work Group. | error | repository | yes |
| DOM-021 | A Work MUST NOT belong to more than one Work Group. | error | repository | yes |
| DOM-022 | A Work MAY exist without any recommended Performance. | info | repository | yes |
| DOM-023 | Composer revisions MUST be modelled as separate Works within the same Work Group. | error | migration | partial |
| DOM-024 | Different performers, recordings, releases, remasters, labels or streaming links MUST NOT create new Works. | error | migration | partial |
| DOM-025 | Practical transcriptions SHOULD NOT automatically create separate Works. | warning | migration | partial |
| DOM-026 | Individual movements or arias SHOULD NOT automatically create separate Works merely because they can be performed separately. | warning | migration | partial |
| DOM-027 | Duplicate-looking Works SHOULD be reported for manual review, not merged automatically. | warning | repository | partial |

## Performance rules

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DOM-040 | Every canonical Performance MUST represent exactly one accepted interpretation of exactly one Work. | error | repository | partial |
| DOM-041 | A Performance MUST contain exactly one `work_id`. | error | repository | yes |
| DOM-042 | A Performance MUST NOT contain multiple Work references. | error | repository | yes |
| DOM-043 | A changed Tidal URL, reissue, remaster, label, catalogue number or album appearance MUST NOT by itself create a new Performance. | error | migration | partial |
| DOM-044 | At least one performer MUST be present. | error | repository | yes |
| DOM-045 | Duplicate-looking Performances SHOULD be reported for manual review, not merged automatically. | warning | repository | partial |
| DOM-046 | Release-related fields on Performance MUST remain limited metadata and MUST NOT imply a canonical Release entity. | error | repository | partial |

## Recommendation semantics

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REC-001 | Presence in canonical Performance data implies recommendation. | error | repository | partial |
| REC-002 | Canonical Performance files SHOULD NOT contain `recommended: true`. | warning | repository | yes |
| REC-003 | A separate canonical Recommendation entity MUST NOT be required by migration. | error | migration | yes |
| REC-004 | For each comparison category there MUST be no more than one public recommendation. | error | publication | partial |
| REC-005 | A comparison category is one Work plus one performance profile when a profile is relevant. | error | publication | partial |
| REC-006 | Performance profiles MUST belong to Performances, not Works. | error | repository | yes |
| REC-007 | Recommendations MUST NOT be replaced automatically. | error | migration | partial |
| REC-008 | `keep_looking: true` MUST NOT automatically create searches or GitHub Issues. | error | migration | partial |

## Gem rules

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| REC-020 | `gem` belongs only to Work. | error | repository | yes |
| REC-021 | `gem` MUST NOT appear on Work Group or Performance records. | error | repository | yes |
| REC-022 | A gem marker MUST NOT create a Performance. | error | migration | yes |
| REC-023 | A gem marker MUST NOT imply a Performance recommendation. | error | migration | yes |
| REC-024 | A Performance recommendation MUST NOT make its Work a gem. | error | migration | yes |

These rules keep Work-level public presentation separate from Performance-level
recommendation.

## Candidate containment

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| CAN-001 | Candidate Performances MUST NOT be written to `data/performances/`. | error | repository | yes |
| CAN-002 | Candidate searches, listening queues, comparison state and duplicate evidence MUST NOT be stored as canonical data. | error | repository | partial |
| CAN-003 | Tidal-linked legacy entries MUST become Performance recommendation candidates before acceptance. | error | migration | partial |
| CAN-004 | A Performance candidate MUST NOT become canonical before listening and editorial acceptance. | error | migration | partial |
| CAN-005 | If an accepted Work already has a recommendation in the same comparison category, a new candidate MUST remain non-canonical until editorial comparison is resolved. | error | migration | partial |

Allowed non-canonical locations include:

- GitHub Issues;
- generated reports;
- migration review files;
- temporary artefacts under `generated/`, `cache/` or `reports/`.

## External references

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| EXT-001 | External identifiers are references, not identity authorities. | warning | repository | partial |
| EXT-002 | Tidal URLs belong to Performance links or Performance candidates. | error | repository | yes |
| EXT-003 | A changed Tidal URL MUST NOT invalidate an otherwise accepted Performance. | error | repository | partial |
| EXT-004 | Link-check status MUST NOT decide whether a Performance remains recommended. | error | publication | partial |

## Duplicate detection

Duplicate detection produces review items unless the duplicate is structurally
certain.

| Rule ID | Invariant | Severity | Profile | Automatable |
| --- | --- | ---: | --- | --- |
| DUP-001 | Possible duplicate Persons SHOULD be reported for review. | warning | migration | partial |
| DUP-002 | Possible duplicate Work Groups SHOULD be reported for review. | warning | migration | partial |
| DUP-003 | Possible duplicate Works SHOULD be reported for review. | warning | migration | partial |
| DUP-004 | Possible duplicate Performances SHOULD be reported for review. | warning | migration | partial |
| DUP-005 | Validators MUST NOT merge duplicates automatically. | error | migration | partial |

## Publication checks

Publication validation should ensure that the public website receives:

- Works, including Works without Performances;
- the current recommended Performance for each comparison category;
- relevant performer display text;
- streaming links when present;
- optional Gramophone references when present.

Publication should not expose:

- candidate Performances;
- migration state;
- matching evidence;
- duplicate reports;
- link-check internals;
- `keep_looking`.

## Summary

Validation protects the new model before migration writes canonical data.

The essential invariants are:

- every Work has exactly one Work Group;
- every Performance references exactly one Work;
- no Performance references a Work Group;
- `gem` and Performance recommendation remain separate;
- candidates stay outside canonical data until accepted.
