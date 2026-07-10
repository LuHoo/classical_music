# Canonical artist data

This directory contains canonical identities for people, ensembles, orchestras, choirs,
and other credited musical entities. The purpose is to prevent spelling, language,
transliteration, abbreviation, and script differences from creating duplicate artists.

## Location

Artist records may be stored in composer- or migration-sized YAML files under:

```text
data/artists/
```

Each record must have a globally unique, stable `id`.

## Proposed format

```yaml
id: royal-concertgebouw-orchestra
type: orchestra
canonical_name: Royal Concertgebouw Orchestra
display_names:
  en: Royal Concertgebouw Orchestra
  nl: Koninklijk Concertgebouworkest
aliases:
  - Concertgebouw Orchestra
  - RCO
country: Netherlands
city: Amsterdam
authorities:
  musicbrainz_artist_id:
  wikidata:
```

For a person:

```yaml
id: dmitri-shostakovich
type: composer
canonical_name: Dmitri Shostakovich
display_names:
  en: Dmitri Shostakovich
  nl: Dmitri Sjostakovitsj
  de: Dmitri Schostakowitsch
  ru: Дмитрий Шостакович
aliases:
  - Dmitry Shostakovich
  - Shostakovich
  - Sjostakovitsj
authorities:
  musicbrainz_artist_id:
  wikidata:
```

## Required fields

- `id`: stable internal identity, independent of display language.
- `type`: the primary artist type.
- `canonical_name`: default display name when no localized name is selected.

## Recommended fields

- `display_names`: language- or script-specific preferred names.
- `aliases`: abbreviations, shortened forms, transliterations, historical forms, and metadata variants.
- `country`: country associated with an organization or person when useful.
- `city`: home city for an ensemble or institution when useful.
- `instruments`: instruments for soloists or instrumentalists.
- `voice`: voice type for singers.
- `authorities`: verified external identifiers.
- `notes`: local modelling notes.

## Artist types

The initial controlled vocabulary is:

```text
composer
conductor
singer
instrumentalist
soloist
orchestra
ensemble
choir
institution
label
```

`soloist` should be used only when a more specific role is not known. A person may later
need multiple roles; a future schema can add `roles` while retaining `type` as the primary
classification.

## Identifier conventions

Use a stable, lowercase, ASCII identifier. The ID should normally resemble the best-known
international name, but it is an internal key and must not change merely because the public
display name changes.

Examples:

```text
royal-concertgebouw-orchestra
bernard-haitink
dmitri-shostakovich
akademie-fuer-alte-musik-berlin
```

## Matching rule for future validation

A future validation script should normalize and compare:

1. `id`
2. `canonical_name`
3. all values in `display_names`
4. all values in `aliases`

Normalization should include:

- case folding;
- Unicode normalization;
- punctuation removal;
- repeated-whitespace normalization;
- optional accent/diacritic folding;
- common abbreviation normalization;
- transliteration-aware comparison where practical.

The validator should warn rather than automatically merge when a new name closely resembles
an existing identity. Short aliases such as surnames and initials can be ambiguous.

## External authority evaluation

MusicBrainz artist identifiers are suitable as optional authority identifiers because they
cover both people and groups and maintain aliases and relationships. They should not replace
local IDs: external records can be merged, split, renamed, or temporarily unavailable.

The repository should store only verified authority IDs plus local additions. Empty authority
fields are preferable to guessed IDs. MusicBrainz aliases may assist reconciliation, but local
aliases remain necessary for Dutch spellings, collection-specific abbreviations, and metadata
variants encountered in streaming services.
