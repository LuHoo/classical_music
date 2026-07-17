# Domain Model

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

---

## Release

Represents a published edition of one or more Recordings.

Examples include:

- CD releases;
- SACDs;
- digital albums;
- streaming releases.

A Release is distinct from the Recording(s) it contains.

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