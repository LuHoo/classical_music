# Identity Rules

## Purpose

This document defines the identity rules for every primary entity in the music collection.

An identity rule answers a single question:

> **When do two records represent the same real-world object?**

These rules are independent of identifiers, filenames, titles or external authority databases. They provide the foundation for deduplication, merging and long-term identifier stability.

---

# Primary Entities

## Composer

Two records represent the same Composer if they describe the same historical individual in their role as a composer, regardless of name variants, spelling, language or external identifiers.

---

## Person

Two records represent the same Person if they describe the same historical individual, regardless of names, pseudonyms, credited names or external identifiers.

---

## Ensemble

Two records represent the same Ensemble if they describe the same performing group throughout its continuous existence, regardless of language, spelling or name variations.

A formally renamed ensemble is considered the same Ensemble if its organisational identity remains unchanged.

---

## Work

Two Work records represent the same Work when they denote the same performable musical object.

Title variants, language, catalogue numbers, metadata corrections and publication history do not create new Works.

A materially distinct version, revision, arrangement, orchestration or completion is a different Work when it can be meaningfully selected and performed as such.

Different editions or metadata descriptions of the same performable musical object do not create a new Work.

An arrangement receives its own Work identity once it is independently included in the collection, and always when a Recording or Recommendation refers to it.

This is an operational identity rule for this collection, not a universal musicological claim.

---

## Work Group

Two Work Group records represent the same Work Group when they group the same compositional source and the same family of versions or derivative Works.

A Work Group must not be created for every incidental or accidental collection of arrangements. It exists only when the grouped Works represent a coherent family of versions, revisions, arrangements, orchestrations, completions or other derivative forms of the same compositional source.

---

## Work Part

Two records represent the same Work Part if they describe the same identifiable structural subdivision of the same parent Work.

Movement numbers, translated titles and numbering conventions do not affect identity.

---

## Recording

Two records represent the same Recording if they originate from the same recorded performance captured in the same recording session.

Different mastering, remastering, audio formats or releases do not create new Recordings.

Different releases, remasters and platform appearances do not create a new Recording when the underlying recorded performance is the same.

Different edits or mixes may constitute different Recordings when they materially alter the recorded performance object.

---

## Release

Two records represent the same Release if they describe the same published commercial or digital product.

Differences in label, catalogue number, barcode, medium, release date, country, packaging or streaming platform constitute distinct Releases.

A Tidal digital album is a Release in its own right and must not automatically be identified with an earlier LP, CD or other platform edition.

---

## Label

Two records represent the same Label if they describe the same publishing or recording label as a legal or commercial entity, regardless of branding changes or logo revisions.

Corporate ownership changes alone do not necessarily create a new Label.

---

## Recommendation

Two records represent the same Recommendation if they describe the same editorial recommendation maintained by the project for the same Recording.

Changes to recommendation status, rationale or editorial notes do not create a new Recommendation.

---

# Relationship Entities

## Recording Participation

Two records represent the same Recording Participation if they describe the participation of the same Person or Ensemble in the same Recording in the same musical role.

Different credited names or billing order do not create new participations.

---

## Recording Work

Two records represent the same Recording Work relationship if they describe the inclusion of the same Work within the same Recording.

Track numbering or sequencing metadata does not affect identity.

---

## Work Relationship

Two records represent the same Work Relationship if they describe the same semantic relationship between the same source Work and target Work.

Editorial notes do not affect identity.

---

# Authority Entities

## Catalogue System

Two records represent the same Catalogue System if they describe the same recognised catalogue numbering scheme.

Revisions or extensions of a catalogue remain part of the same Catalogue System.

---

## External Authority

Two records represent the same External Authority if they describe the same external authority database or identifier system.

Changes to APIs or ownership do not affect identity.

---

# General Principles

## Identity is immutable

Once an entity has been created, its identity never changes.

---

## Metadata is mutable

Titles, descriptions, dates, external identifiers and other metadata may be corrected without changing identity.

---

## Relationships are mutable

Relationships between entities may be added, removed or corrected without affecting the identity of the participating entities.

---

## Merge policy

If two records are discovered to represent the same real-world object, they are merged into a single entity.

The surviving entity retains its permanent identifier.

Deprecated identifiers remain available as aliases or redirects and are never reused.

---

## Split policy

If one record is discovered to represent multiple real-world objects, new entities are created.

Each new entity receives its own permanent identifier.

The original identifier is retired and retained only for migration and historical reference.
