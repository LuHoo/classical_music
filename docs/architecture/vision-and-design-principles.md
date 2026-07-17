---
title: Vision & Design Principles
nav_order: 1
---

# Vision & Design Principles

## Purpose

This repository is a curated knowledge base for classical music.

Its primary purpose is not to catalogue every recording ever made, nor to duplicate existing musicological databases. Instead, it captures informed editorial judgement about musical works and their performances while relying on authoritative external sources for factual metadata.

The repository serves both as the source for a public website and as a reusable knowledge layer for future applications.

---

# Core Principles

## 1. Works are the central concept

The musical work is the fundamental entity of the repository.

Everything else exists in relation to a work:

- performances
- releases
- recommendations
- streaming availability
- editorial notes

The repository is therefore work-centric rather than recording-centric.

---

## 2. Curation over completeness

The objective is not to become another MusicBrainz or Discogs.

Completeness of factual metadata is delegated to external authorities.

The repository adds value through:

- editorial judgement
- recommended performances
- preferred releases
- listening notes
- relationships that matter to the curator

Only information that contributes to these goals should be maintained locally.

---

## 3. Separate facts from opinions

The repository deliberately separates objective metadata from editorial decisions.

Examples of factual information:

- titles
- catalogue numbers
- dates
- instrumentation
- contributors
- relationships between works

Examples of editorial information:

- recommended performances
- preferred releases
- review status
- listening priorities
- personal notes

This distinction allows factual information to evolve independently of curation.

---

## 4. External authorities own factual metadata

Whenever possible, factual information is imported rather than maintained manually.

Typical authorities include:

- MusicBrainz
- Discogs
- Wikipedia
- Grove Music Online

The repository stores stable references to these authorities rather than duplicating large amounts of metadata.

---

## 5. Recommendations are independent of streaming platforms

A recommendation identifies an artistic interpretation.

Streaming services merely provide temporary access to that interpretation.

If a recording disappears from TIDAL or another platform, the recommendation remains valid.

Availability information is therefore maintained separately from recommendations.

---

## 6. Relationships are first-class citizens

Music is not simply a collection of isolated works.

Works are connected through:

- revisions
- orchestrations
- arrangements
- completions
- excerpts
- suites
- adaptations

These relationships are part of the domain model rather than textual annotations.

---

## 7. Contributors are more than composers

Many musical works involve multiple creative contributors.

Examples include:

- composer
- arranger
- orchestrator
- completer
- editor
- librettist

The repository therefore models contributors together with their roles instead of assuming a single composer field.

---

## 8. Stable identities are more important than names

Titles may change.

Spellings differ.

Languages vary.

External catalogues evolve.

Every domain object therefore receives a stable local identifier that remains valid independently of naming conventions.

---

## 9. The architecture precedes the implementation

The logical model is intentionally independent of:

- YAML structure
- directory layout
- GitHub Pages
- programming language
- import tooling

Implementation choices may evolve without affecting the conceptual model.

---

## 10. Incremental completeness

The repository is expected to grow continuously.

Not every composer will initially have:

- a complete catalogue
- recommendations
- preferred releases
- streaming links

Partial knowledge is acceptable.

Completeness improves over time without requiring structural redesign.

---

# Design Principles

## Prefer relationships over text

Whenever information describes a relationship between domain objects, model it explicitly rather than embedding it in free text.

---

## Prefer identities over names

Store references to entities instead of repeating strings.

---

## Prefer import over duplication

If reliable information already exists elsewhere, reference or import it.

Do not maintain parallel copies without good reason.

---

## Prefer extensibility over optimisation

The model should accommodate future knowledge without structural changes.

Examples include:

- ritual associations
- philosophical themes
- historical context
- educational annotations

These should be added through new relationships rather than modifications of the core model.

---

## Separate domain knowledge from presentation

The repository represents knowledge.

The website is only one possible presentation of that knowledge.

Future applications may expose different views over the same underlying model.

---

# Long-term Vision

Although currently focused on recommended recordings, the repository is designed as a reusable knowledge layer for classical music.

Future applications may connect musical works with broader intellectual domains such as literature, philosophy, symbolism, education, or ritual.

By separating factual knowledge from editorial interpretation, and by modelling relationships explicitly, the repository aims to remain useful far beyond its original purpose while preserving a single coherent representation of the musical domain.