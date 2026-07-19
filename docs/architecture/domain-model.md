# Domain Model

> Status: Superseded by `repository-architecture.md`, `work.md`, `performance.md`,
> and `recommendation-policy.md`.
>
> This document records an earlier conceptual model. The current authoritative
> model has four core canonical entities: Person, Work Group, Work and
> Performance. Recording and Release are not separate canonical entities.

## Purpose

This document defines the conceptual domain model of the music collection.

The domain model identifies the long-lived entities that make up the collection and
describes their responsibilities. It deliberately does **not** prescribe how these
entities are stored, identified, or exposed through the website. Those concerns are
covered elsewhere in the architecture documentation.

The guiding principle is that every entity listed here has its own identity that
remains stable, regardless of changes in names, metadata, or relationships.

---

# Core Principles

The model distinguishes between three categories of objects.

## Primary entities

Primary entities have their own persistent identity and lifecycle.

Examples include:

- a composer;
- a musical work;
- a work group;
- a recording;
- a release.

These objects can exist independently and may be referenced throughout the system.

## Relationship entities

Some relationships carry information of their own.

For example, a musician participating in a recording is not merely a reference to a
Person, but also includes:

- role;
- instrument or voice;
- billing order;
- credited name.

Likewise, relationships between musical works (arrangement, revision, orchestration,
etc.) are modelled explicitly rather than encoded as simple pointers.

## Derived objects

Some objects exist only as a consequence of another entity.

Examples include:

- website pages;
- search indexes;
- streaming links;
- redirects;
- generated navigation structures.

These objects do not receive permanent identities.

---

# Primary Entities

## Composer

Represents the creator of one or more musical works.

A Composer is conceptually a specialised Person, but is treated as a separate entity
within the collection because composers form the primary navigation structure of the
website.

Responsibilities include:

- biographical information;
- catalogue of works;
- external authority links.

---

## Person

Represents an individual participating in musical performances.

Examples include:

- conductors;
- soloists;
- singers;
- arrangers;
- librettists.

A Person may participate in many recordings.

---

## Ensemble

Represents an orchestra, choir or chamber ensemble.

Examples:

- orchestras;
- chamber orchestras;
- choirs;
- string quartets;
- vocal ensembles.

---

## Work

Represents an abstract musical composition.

Examples:

- Symphonie fantastique
- Brandenburg Concerto No. 3
- La mer

A Work exists independently of any performance or recording.

A distinct version, revision or derivative form may receive its own Work identity.
This includes arrangements, orchestrations, completions, reconstructions, suites,
excerpts and other forms that function as independently identifiable performance
objects.

A version receives its own Work identity when it functions as a meaningful
independent performance object and the distinction is relevant to identification,
recommendation or presentation within the collection.

When multiple Works represent versions or derivative forms of the same
compositional source, they may be grouped by a Work Group and related to each other
through explicit Work Relationships.

---

## Work Group

A Work Group is a non-performable entity that groups two or more Works
representing versions, revisions, arrangements, orchestrations, completions or
other derivative forms of the same compositional source.

A Work Group exists to identify and organise a family of related Works. It is not
itself a musical performance object.

The following rules apply:

- a Work Group is not performable;
- a Recording can never refer directly to a Work Group;
- a Recommendation can never refer directly to a Work Group;
- a Work Group is created only when there are actually multiple Works to group;
- a single ordinary Work does not automatically receive a Work Group;
- every Recording and Recommendation must resolve to a concrete Work.

Members of a Work Group may have explicit relationships to each other, such as:

- `revision_of`;
- `version_of`;
- `arrangement_of`;
- `orchestration_of`;
- `completion_of`;
- `suite_from`.

---

## Work Part

Represents an identifiable subdivision of a Work.

Examples include:

- movements;
- acts;
- scenes;
- individual numbers.

A Work Part belongs to exactly one Work.

---

## Recording

Represents a specific recorded performance.

A Recording may contain one or more Works.

The same Recording may appear on multiple Releases.

A Recording always refers to one or more concrete Works. It must never refer only
to a Work Group.

Recordings may be created provisionally when the collection has enough information
to identify the performed Work and principal artists, but not yet enough
information to identify every release or catalogue detail.

Recording records may therefore include an `identification_status`, such as:

- `provisional`;
- `identified`;
- `externally_enriched`.

For initial entry, the minimum acceptable information is:

- the concrete Work or Works performed;
- the principal artist or artists needed to recognise the performance;
- at least one source link documenting the recording or platform appearance.

---

## Release

Represents a published edition of one or more Recordings.

Examples include:

- CD releases;
- SACDs;
- digital albums;
- streaming releases.

A Release is distinct from the Recording(s) it contains.

A Release may be a physical edition or a digital platform release.

A platform-confirmed digital album is a Release in its own right. For initial
creation, a Tidal album ID may be accepted as provisional external identification
when label, catalogue number or fuller release metadata are not yet known.

Release identification may progress through stages:

- platform-confirmed digital Release;
- externally enriched Release;
- definitively identified Release.

Label and catalogue number are desirable metadata, but they are not required for
initial creation of a Release.

---

## Label

Represents the publisher of Releases.

Examples include:

- Deutsche Grammophon;
- Philips;
- BIS;
- Chandos.

---

## Recommendation

Represents an editorial recommendation maintained by the project.

A Recommendation is intentionally modelled as a separate entity because it may
contain information beyond a simple boolean flag, including:

- editorial notes;
- replacement history;
- recommendation period;
- rationale.

A Recommendation refers to a Recording.

Because a Recording always resolves to a concrete Work, a recommended arrangement,
orchestration, completion or other derivative form must first exist as its own
Work before it can be recommended.

---

# Relationship Entities

## Recording Participation

Represents the participation of a Person or Ensemble in a Recording.

Typical attributes include:

- role;
- instrument;
- voice type;
- billing order;
- credited name.

---

## Recording Work

Represents the inclusion of a Work within a Recording.

Typical attributes may include:

- track range;
- order;
- editorial status;
- notes.

---

## Work Relationship

Represents semantic relationships between Works.

Examples include:

- arrangement of;
- revision of;
- orchestration of;
- based on;
- excerpt from;
- part of.

---

# Authority Entities

These entities describe external authority systems rather than musical objects.

## Catalogue System

Represents a catalogue numbering system.

Examples include:

- Opus;
- BWV;
- Köchel;
- Hoboken;
- Deutsch;
- Wq;
- Sz.

---

## External Authority

Represents an external authority database.

Examples include:

- MusicBrainz;
- Wikidata;
- VIAF;
- ISNI.

These entities provide authoritative identifiers but do not define the internal
identity of collection objects.

---

# Derived Objects

The following objects are generated from the primary entities and therefore do not
receive permanent identities.

- Website pages
- Search indexes
- Navigation structures
- Redirects
- Streaming availability
- Cover image derivatives

---

# Open Design Questions

The following topics remain intentionally undecided.

## Composer versus Person

The current model treats Composer as a specialised entity because composers form the
primary organisational structure of the collection.

An alternative is to model Composer purely as a subtype of Person.

This decision can be revisited during implementation.

---

## Performance

The current model assumes that Recordings are the primary representation of musical
performances.

If future requirements include performances that were never recorded, a separate
Performance entity may be introduced.

---

## Identifier Strategy

This document intentionally avoids prescribing identifier formats.

Identifier generation, slugs, aliases, redirects and rename strategies are described
in a separate architectural document.
