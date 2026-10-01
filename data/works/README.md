# Canonical work data

This directory contains lightweight work identity records. The purpose is to separate the identity of a musical work from the way that work is displayed, translated, catalogued, or described by a streaming service.

The records are intentionally incremental. A composer page may exist before any work records are present, and a composer may have only the works that are currently needed by the collection.

## Location

Work records are grouped by composer:

```text
data/works/<composer_id>/<work_id>.yaml
```

For example:

```text
data/works/hector-berlioz/berlioz-op14.yaml
```

## Required fields

```yaml
id: berlioz-op14
composer_id: hector-berlioz
canonical_title: Symphonie fantastique
```

- `id` is the repository's stable internal work identifier.
- `composer_id` identifies the composer independently of the page title.
- `canonical_title` is the default display title when no localized title is available.

## Recommended fields

```yaml
localized_titles:
  fr: Symphonie fantastique
  en: Fantastic Symphony
  nl: Symphonie fantastique

catalogue:
  opus: Op. 14
  holoman: H. 48

aliases:
  - Fantastic Symphony
  - Épisode de la vie d'un artiste
  - Episode in the Life of an Artist
  - Op. 14

authorities:
  musicbrainz_work_id:
  wikidata:

notes: >-
  Optional local notes about identity, title variants, or modelling choices.
```

- `localized_titles` supports language-specific display without changing the internal ID.
- `catalogue` stores catalogue references such as opus numbers, Holoman numbers, or other work catalogue identifiers.
- `aliases` stores names and metadata strings that may appear in recordings, streaming metadata, imports, or notes.
- `authorities` stores external identifiers when they have been verified.
- `notes` is optional and should only contain local modelling notes.

## Identifier conventions

Use stable, language-independent IDs. Prefer catalogue-based IDs when available:

```text
berlioz-op14
berlioz-h138
```

When no reliable catalogue number is available, use a short normalized title:

```text
berlioz-rob-roy
```

The ID should not be changed merely because the displayed title changes.

## Matching rule for future validation

A future validation script should be able to match incoming metadata against:

1. `id`
2. `canonical_title`
3. values in `localized_titles`
4. values in `catalogue`
5. values in `aliases`

Matching should be case-insensitive and should normalize punctuation, accents, and repeated whitespace.

## External authority evaluation

MusicBrainz work IDs are suitable as optional external authority identifiers, because they identify works separately from recordings and releases. They should not replace local IDs, since local IDs need to remain stable even if an external database changes its preferred title or merge history.

For the pilot, `musicbrainz_work_id` is included as a nullable field. The field should be populated only after the exact work entity has been verified. This avoids importing uncertain identifiers while keeping the format ready for authority-backed reconciliation.
