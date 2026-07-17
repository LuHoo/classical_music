---

title: Information Architecture
nav_order: 7
------------

# Information Architecture

## Purpose

This document describes the information architecture of the classical music catalogue.

It translates the architectural decisions into a coherent information model without yet prescribing the exact YAML structure, file layout, validation technology or website implementation.

The architecture is designed to support:

* a work-centred catalogue of classical music;
* curated recording recommendations;
* multiple performances and releases of the same work;
* availability across streaming services;
* explicit relationships between related works;
* gradual enrichment from external authority sources;
* generation of public composer, work and recommendation pages;
* continued manual curation without requiring a complete musicological ontology.

The model deliberately separates:

1. musical and curatorial facts;
2. publication and availability facts;
3. presentation and navigation structures;
4. external authority identifiers.

## Architectural principles

### Work-centred design

`Work` is the central musical entity.

Recommendations, performances, releases and availability ultimately describe how a particular work can be heard. Composer pages, contributor pages and navigation structures provide access to works but do not replace the work as the central catalogue object.

### Separation of musical identity and publication

A musical work is not the same as:

* a particular performance;
* a recorded release;
* an album;
* a remaster;
* a streaming-service listing;
* a platform-specific URL.

These concepts must remain separate so that a recommendation can survive changes in release packaging or streaming availability.

### Relationships are first-class facts

Relationships between works are explicit domain facts.

They are not inferred merely because works appear in the same group, catalogue series or website section. A relationship records that one work is related to another work in a particular, directional way.

Examples include:

* a revision of another work;
* an arrangement or orchestration;
* a completion or reconstruction;
* a suite or excerpt from a larger work;
* a work based on another work;
* a work incorporating material from one or more earlier works.

The examples do not form a complete taxonomy.

### Open relationship terminology

The relationship vocabulary is open-ended.

Relationship names:

* do not need to form a complete set;
* do not need to be mutually exclusive;
* may overlap semantically;
* may follow the terminology used by the relevant contributor or authoritative source;
* must not be restricted to a closed enumeration.

For example, one contributor may describe a work as `based_on` another work, while another uses `adaptation_of` in a comparable situation. The catalogue may preserve both terms.

Future normalized categories may be added for search, analysis or presentation, but they must not replace the original relationship terminology.

### Local curation with external authority support

The repository owns its curatorial decisions.

External sources such as MusicBrainz, Discogs, Wikidata, library catalogues, publisher catalogues and specialist reference works may provide:

* identifiers;
* names;
* dates;
* catalogue numbers;
* work relationships;
* performer metadata;
* release metadata.

External records support local curation but do not automatically determine:

* which works are included;
* which recordings are recommended;
* how works are presented;
* which source is preferred when authorities disagree;
* whether two records should be treated as the same local entity.

### Presentation is derived from domain information

Website structures such as:

* related-work sections;
* groups of revisions;
* suites from a stage work;
* composer work lists;
* recommended recordings;
* streaming links;

are derived views over the domain model.

A navigation group may be generated automatically or curated explicitly for display. It is not a primary musical entity and does not own recommendations, performances, releases or relationships.

## Primary entities

The primary information entities are:

1. `Contributor`
2. `Work`
3. `Recommendation`
4. `Performance`
5. `Release`
6. `Availability`

Work-to-work relationships are first-class domain facts associated with works. They may later be represented as embedded relationship records or as separate technical records, but conceptually they connect one `Work` to another `Work`.

## Conceptual overview

```text
Contributor
    contributes to
Work
    has typed relationship to
Work

Work
    has
Recommendation

Recommendation
    identifies
Performance

Performance
    is published on
Release

Release
    has
Availability
```

A more complete conceptual view is:

```text
Contributor ───── contributes to ───── Work
     ▲                                      │
     │                                      │
     └──── attributed relationship ─────────┘

Work ───── typed relationship ─────► Work

Work ───── has ─────► Recommendation
Recommendation ───── identifies ─────► Performance
Performance ───── appears on ─────► Release
Release ───── is available through ─────► Availability
```

## Contributor

### Definition

A `Contributor` is a person or collective body that contributes creatively or interpretatively to a work or performance.

Examples include:

* composer;
* arranger;
* orchestrator;
* transcriber;
* editor, where the editorial contribution is musically significant;
* completer;
* reconstructor;
* librettist;
* author of a source text;
* conductor;
* orchestra;
* ensemble;
* choir;
* soloist;
* singer.

The precise contributor roles may differ between works and performances.

### Identity

A contributor has one stable local identifier.

A contributor may also have identifiers from external authority systems, such as:

* MusicBrainz;
* Wikidata;
* VIAF;
* ISNI;
* Discogs.

External identifiers do not replace the local identifier.

### Core information

A contributor may contain:

* preferred display name;
* sort name;
* alternative names;
* birth and death dates, where applicable;
* formation and dissolution dates for organizations;
* contributor type;
* nationality or geographical association;
* short descriptive note;
* external authority identifiers;
* source references.

### Relationships

A contributor may:

* create or contribute to zero, one or many works;
* participate in zero, one or many performances;
* fulfil different roles in different contexts.

A contributor role belongs to the relevant contribution record. It is not necessarily a permanent property of the contributor.

For example, a person may be represented as:

* composer of one work;
* arranger of another;
* pianist in a performance;
* conductor in a different performance.

## Work

### Definition

A `Work` is a distinct musical or music-related intellectual creation that the catalogue treats as independently identifiable.

A work is normally modelled separately when it can meaningfully have its own:

* identity;
* title;
* contributor attribution;
* catalogue number;
* scoring;
* date;
* recommendation;
* relationship to another work;
* performance tradition.

The catalogue does not need to solve every musicological distinction between work, version, expression and realization before including a work. The practical threshold is whether the form is stable and independently useful within the catalogue.

### Identity

Every work has one stable local identifier.

A work may also have:

* MusicBrainz work identifiers;
* Wikidata identifiers;
* publisher identifiers;
* thematic catalogue references;
* catalogue numbers such as BWV, K., Op., D., Hob. or RV;
* identifiers from specialist work catalogues.

Catalogue numbers are attributes or authority references. They are not assumed to be globally unique identifiers.

### Core information

A work may contain:

* preferred title;
* subtitle;
* alternative titles;
* original-language title;
* sort title;
* contributors and their roles;
* composition date or period;
* revision date or period;
* premiere date;
* catalogue number;
* opus number;
* key;
* scoring or instrumentation;
* genre or work type;
* number of movements or sections;
* duration indication;
* descriptive notes;
* source citations;
* external identifiers.

Not every work requires every field.

### Contributor attribution

A work may have multiple contributors.

Each attribution should record the relevant role, such as:

* composer;
* arranger;
* orchestrator;
* transcriber;
* completer;
* reconstructor;
* librettist;
* text author.

The terminology used should remain faithful to the relevant source where possible.

### Work relationships

A work may have zero, one or many outgoing relationships to other works.

A work may also have zero, one or many incoming relationships from other works.

Each relationship contains conceptually:

* one source work;
* one target work;
* one relationship name;
* optional contributor attribution;
* optional note;
* optional source citation;
* optional external authority reference.

The relationship is directional.

For example:

```text
Piano Concerto, Op. 61a
    arrangement_of
Violin Concerto, Op. 61
```

Only the asserted direction is stored as the fact. The website may display the inverse relationship:

```text
Violin Concerto, Op. 61
    arranged as
Piano Concerto, Op. 61a
```

The inverse display label may be generated and does not need to be stored as a second relationship.

### Open relationship names

Relationship names are not restricted to a closed vocabulary.

Terms currently found or expected in the collection include:

```text
revision_of
arrangement_of
orchestration_of
transcription_of
completion_of
reconstruction_of
suite_from
excerpt_from
part_of
based_on
adaptation_of
incorporates
```

This list is illustrative.

A relationship name may be added when required by the source material without first changing a central enumeration.

Validation should confirm the structure of the relationship record and the validity of its references. It should not reject a relationship solely because its name is new.

### Multiple relationships

A work may have several simultaneous relationships.

For example, a work may:

* be a suite from a stage work;
* also be arranged from music in that work;
* contain material from another work;
* be completed by another contributor.

The model must therefore permit multiple relationship records between the same or different works.

### Cross-contributor relationships

Relationships may connect works by different contributors.

Examples include:

* variations on a theme by another composer;
* an orchestration of another composer’s work;
* an adaptation of a stage or literary work;
* a reconstruction involving a later contributor;
* a transcription by one contributor of another contributor’s work.

The contributor pages and website navigation must not assume that related works always belong to the same composer.

### Structural relationships

A relationship such as `part_of` represents containment rather than derivation.

It may be used for independently modelled:

* movements;
* songs;
* arias;
* numbers;
* sections;
* cycles;
* sets.

The catalogue should not require every movement or section to become a separate work. Separate modelling is appropriate only when the component needs independent identity within the catalogue.

### Threshold for a separate work

A form is likely to be modelled as a separate `Work` when it is:

* independently published;
* independently performed;
* independently recorded;
* independently recommendable;
* attributed to a distinct creative contributor;
* assigned a distinct catalogue identity;
* recognised by relevant authority sources as a separate work.

A form is less likely to be a separate work when it is:

* a routine performing edition;
* a recording-specific cut;
* a one-off performance choice;
* a remastering difference;
* an alternative release sequence;
* a minor variant without stable independent identity.

These are curatorial guidelines, not automated rules.

## Recommendation

### Definition

A `Recommendation` is a local curatorial judgment that identifies a preferred performance of a particular work.

A recommendation is not identical to:

* a release;
* an album;
* a review;
* a streaming link;
* a general endorsement of every work on a release.

### Identity

Every recommendation has one stable local identifier or is uniquely identifiable within the work to which it belongs.

The physical implementation may determine whether recommendations receive globally unique IDs or work-scoped IDs.

### Core information

A recommendation may contain:

* the work being recommended;
* the selected performance;
* recommendation status;
* curatorial note;
* rationale;
* recommendation date;
* date last reviewed;
* source or provenance of the recommendation;
* priority or ordering;
* alternative recommended performances.

### Cardinality

A recommendation belongs to exactly one work.

A work may have:

* no recommendation;
* one primary recommendation;
* several recommendations;
* recommendations for different performance traditions or versions.

A recommendation does not belong to a navigation group or work cluster.

### Scope

When a release contains several works, a recommendation applies only to the explicitly identified work-performance combination.

The presence of a recommended recording on an album does not imply that all works on that album are recommended.

## Performance

### Definition

A `Performance` represents the interpretation of a work by a particular set of performers.

It captures the musical event or recorded interpretation independently of the release on which it appears.

This separation allows the same performance to appear on:

* an original release;
* a reissue;
* a compilation;
* a remastered edition;
* multiple streaming-service manifestations.

### Identity

Every performance has one stable local identifier.

A performance may also have external identifiers where available, although external databases do not always distinguish performances consistently.

### Core information

A performance may contain:

* work;
* conductor;
* orchestra;
* ensemble;
* choir;
* soloists;
* singers;
* other performers;
* performance or recording date;
* recording venue;
* live or studio status;
* edition or version performed;
* performance-specific note;
* source citations;
* external identifiers.

### Performer roles

Each performer attribution should identify the role relevant to the performance.

Examples include:

* conductor;
* orchestra;
* violin;
* piano;
* soprano;
* choir;
* narrator;
* continuo;
* ensemble.

The role terminology may be open-ended where needed.

### Work association

A performance represents exactly one work at the level at which recommendations are made.

A release containing a symphony, overture and concerto therefore normally contains at least three performance records.

A multi-movement work need not be split into separate performance records unless its movements are themselves independently modelled and recommended as works.

### Performance-specific variants

A performance may record which edition, completion, reconstruction or version was used.

Where that form has an independent and stable work identity in the catalogue, the performance should point to that specific work.

Where it is merely a performance-specific choice, it may remain performance metadata rather than creating another work.

## Release

### Definition

A `Release` represents a published audio product or edition on which one or more performances appear.

Examples include:

* original LP;
* CD;
* SACD;
* digital album;
* boxed set;
* compilation;
* remastered reissue;
* platform-distributed digital release.

### Identity

Every release has one stable local identifier.

A release may also have identifiers from:

* MusicBrainz;
* Discogs;
* record labels;
* barcode systems;
* streaming platforms.

Platform URLs are not stable release identifiers.

### Core information

A release may contain:

* title;
* label;
* catalogue number;
* release date or year;
* country or market;
* format;
* edition;
* barcode;
* disc and track structure;
* cover-image reference;
* liner-note information;
* source citations;
* external identifiers.

### Relationship to performances

A release contains one or many performances.

The same performance may appear on multiple releases.

A release may contain performances of works that are not represented by recommendations.

### Release versus recording

The model must avoid treating a release title as the identity of the performance.

A remastered reissue may be a new release containing the same underlying performance.

A newly edited or materially different recording may require a separate performance record.

## Availability

### Definition

`Availability` records that a release or relevant release manifestation is accessible through a particular service or channel.

Examples include:

* Tidal;
* Apple Music;
* Spotify;
* Qobuz;
* Idagio;
* physical media;
* label store;
* retailer;
* library catalogue.

### Identity

Availability is normally identified by the combination of:

* release;
* service;
* service-specific reference or URL.

The physical implementation may use a separate local identifier where useful.

### Core information

An availability record may contain:

* release;
* service;
* URL;
* platform-specific identifier;
* territorial scope;
* availability status;
* date first observed;
* date last checked;
* date availability ended;
* matching confidence;
* note.

### Volatility

Availability is inherently less stable than the musical and release entities.

A streaming URL may:

* change;
* redirect;
* disappear;
* point to a replacement release;
* differ by country;
* represent an incorrectly matched album.

Availability data must therefore include status and checking information.

### Status

Possible statuses may include:

```text
active
unavailable
redirected
uncertain
not_checked
```

The exact status vocabulary belongs to the later physical schema design.

### Platform independence

A recommendation must remain valid when a particular streaming link becomes unavailable.

The recommendation points to a performance. The availability record describes where a release containing that performance can currently be accessed.

## Navigation and presentation structures

### Derived navigation groups

The website may group related works for human navigation.

Examples include:

* versions of Bruckner’s Symphony No. 4;
* suites derived from a ballet;
* the relationship between Berio’s `Sequenza` and `Chemins` works;
* excerpts from a stage work;
* arrangements of a source work.

Such groups are derived from the work relationship graph where possible.

### Curated navigation groups

Mechanical graph traversal may not always produce an intelligible website section.

The implementation may therefore permit curated navigation metadata, such as:

* group label;
* preferred root work;
* display order;
* works to include or exclude;
* introductory text.

A curated navigation group is not a primary domain entity.

It:

* does not own work relationships;
* does not own recommendations;
* does not constrain a work to one group;
* does not define musical identity;
* may overlap with other navigation groups;
* may be regenerated or changed without altering domain facts.

### Composer pages

A composer or contributor page is a view over:

* contributor information;
* works attributed to that contributor;
* relevant work relationships;
* recommendations;
* selected explanatory text.

A composer page should not become the sole storage location for work data.

### Work pages

A work page may present:

* title and contributor information;
* catalogue and composition details;
* work relationships;
* related-work navigation;
* recommended performances;
* releases containing those performances;
* current availability.

### Recommendation pages or sections

A recommendation view may present:

* the recommended performance;
* performers;
* recording information;
* preferred release;
* alternative releases;
* availability links;
* curatorial rationale.

The website may combine this information into a work page rather than generating a separate page for every recommendation.

## Authority identifiers and provenance

### Local identifiers

Every primary entity must have a stable local identifier.

Local identifiers:

* are controlled by the repository;
* must not change merely because an external source changes;
* should remain stable when display names change;
* should not encode volatile facts unnecessarily.

The exact identifier syntax will be defined separately.

### External identifiers

Entities may contain zero, one or many external identifiers.

Each external identifier should include:

* authority or system;
* identifier;
* optional URL;
* optional status;
* optional date last checked;
* optional note.

### Source attribution

Important facts may include provenance.

Source attribution is especially useful for:

* disputed dates;
* relationship terminology;
* work-version distinctions;
* contributor roles;
* completion or reconstruction attributions;
* release matching;
* availability matching.

The later schema should permit source references without requiring every ordinary fact to carry a full citation.

### Conflicting sources

The repository may retain a preferred local value when external sources disagree.

Where the disagreement is relevant, the catalogue may record:

* alternative values;
* source-specific wording;
* explanatory notes;
* uncertainty.

The information model must not assume that external authority data is internally consistent.

## Cardinalities

The principal cardinalities are:

### Contributor and Work

* A contributor may contribute to zero, one or many works.
* A work has one or many contributor attributions.
* A contributor may have different roles for different works.

### Work and Work

* A work may have zero, one or many outgoing relationships.
* A work may have zero, one or many incoming relationships.
* A work relationship has exactly one source and one target.
* Multiple relationships may exist between the same pair of works when they express distinct source claims.

### Work and Recommendation

* A work may have zero, one or many recommendations.
* A recommendation belongs to exactly one work.

### Recommendation and Performance

* A recommendation identifies exactly one performance.
* A performance may be used by zero, one or many recommendations, although in normal use recommendations concern the work performed.

### Work and Performance

* A performance represents exactly one locally modelled work.
* A work may have zero, one or many performances.

### Performance and Release

* A performance may appear on one or many releases.
* A release contains one or many performances.

### Release and Availability

* A release may have zero, one or many availability records.
* An availability record belongs to exactly one release and one service context.

## Ownership of information

| Information                              | Owning entity                                  |
| ---------------------------------------- | ---------------------------------------------- |
| Contributor identity and names           | `Contributor`                                  |
| Work title and musical identity          | `Work`                                         |
| Work contributor attribution             | `Work` contribution record                     |
| Relationship between two works           | Work-to-work relationship record               |
| Curatorial recommendation                | `Recommendation`                               |
| Performers and recorded interpretation   | `Performance`                                  |
| Label, catalogue number and release date | `Release`                                      |
| Streaming URL and availability status    | `Availability`                                 |
| Website grouping and display order       | Presentation or navigation metadata            |
| External authority identifier            | The entity being identified                    |
| Source citation                          | The fact or entity to which the source applies |

Information should be stored at the lowest stable entity that owns the fact.

For example:

* a conductor belongs to the performance, not the release;
* a label belongs to the release, not the performance;
* a Tidal URL belongs to availability, not the recommendation;
* `arrangement_of` belongs to the relationship between two works, not to a navigation group.

## Data integrity principles

### Referential integrity

All local references must resolve to existing entities.

The implementation should validate at least:

* contributor references;
* work references;
* recommendation-to-work references;
* recommendation-to-performance references;
* performance-to-work references;
* release-to-performance references;
* availability-to-release references;
* work relationship targets.

### Structural validation

Structural validation may enforce:

* required identifiers;
* expected field shapes;
* uniqueness of local identifiers;
* valid dates or date ranges;
* required source and target in a relationship;
* required service in an availability record.

### Semantic restraint

Validation must not overstate musicological certainty.

It should not require:

* a complete work genealogy;
* a closed relationship taxonomy;
* one canonical label for every relationship;
* every related work to be locally present;
* every movement to be separately modelled;
* every external authority to agree;
* every work to have a recommendation.

### Duplicate detection

The import and curation workflow should detect possible duplicates using combinations of:

* contributor;
* title;
* catalogue number;
* external identifier;
* date;
* scoring;
* related work;
* performers;
* label and catalogue number.

Possible duplicates should be reviewed rather than automatically merged solely on fuzzy matching.

## Local and external relationships

A work relationship normally targets another local work.

The later physical schema may permit a relationship to an external authority record when the target work has not yet been imported locally.

Such a relationship should preserve enough information to:

* identify the external target;
* display a meaningful temporary label;
* migrate the relationship to a local work later;
* avoid creating an artificial local work solely to satisfy referential integrity.

The exact mechanism is deferred to schema design.

## Temporal information

Dates in classical-music metadata are often uncertain.

The model should be capable of representing:

* exact dates;
* years;
* year ranges;
* approximate dates;
* dates before or after a known boundary;
* composition and revision periods;
* recording and release dates.

The physical schema should not force uncertain historical dates into false precision.

## Multilingual information

Works and contributors may have names and titles in several languages.

The model should distinguish:

* preferred display title;
* original title;
* alternative title;
* translated title;
* sort title;
* language, where relevant.

The website may choose a display language without discarding source-language titles.

## Implementation boundaries

This document defines the conceptual and logical information architecture.

It does not yet define:

* the exact YAML syntax;
* directory and file organization;
* JSON Schema;
* ID format;
* whether relationships are embedded or stored separately;
* API design;
* database tables;
* website templates;
* search index structure;
* import scripts;
* synchronization policy;
* precise validation messages.

Those decisions should be derived from this information architecture and documented separately.

## Expected physical model

Although the exact implementation remains open, the repository is expected to contain structured data for at least:

```text
contributors
works
recommendations
performances
releases
availability
```

Work relationships may be stored:

* within each source work;
* in separate relationship records;
* in a normalized relationship file.

Whichever representation is chosen must preserve:

* direction;
* source;
* target;
* original relationship terminology;
* optional provenance;
* multiple simultaneous relationships.

Navigation groups, if stored, must be clearly separated from authoritative work relationship facts.

## Evolution of the model

The model is intended to grow incrementally.

Future schema pressure may justify additional concepts, such as:

* edition;
* expression;
* version;
* realization;
* movement;
* text;
* venue;
* session;
* recording event;
* review;
* source;
* navigation group.

Such entities should be introduced only when the collection contains repeated cases that cannot be modelled clearly with the current entities and relationships.

In particular, the architecture does not currently introduce a separate `Version`, `Expression` or `Realization` entity. Independently identifiable and recommendable forms are represented as works and connected by explicit relationships.

## Summary

The information architecture is centred on `Work`.

Musical derivations and connections are represented by explicit, directional work-to-work relationships using an open, source-faithful vocabulary.

Recommendations identify performances of individual works. Performances are separated from releases, and releases are separated from volatile availability on streaming or other services.

Website groupings are derived or curated presentation structures. They do not own musical facts and do not constrain the work relationship graph.

This structure supports a curated classical-music catalogue that is precise enough for reliable data management while remaining flexible enough to accommodate differing contributor terminology, incomplete authority data and gradual expansion of the collection.
