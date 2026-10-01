# Canonical artist data

This directory contains canonical identities for people, ensembles, orchestras, choirs,
and other credited musical entities. The purpose is to prevent spelling, language,
transliteration, abbreviation, and script differences from creating duplicate artists.

## Location

Artist records are stored in global authority YAML files under:

```text
data/artists/
```

Each record must have a globally unique, stable `id`. Artist identities are not
owned by a composer, source document, or migration batch. Composer-specific
provenance belongs on the Performance or source evidence that introduced the
artist, not in a composer-scoped artist namespace.

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
- `roles`: known artist capabilities or functions, such as `singer`, `conductor`, or `instrumentalist`.
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

`soloist` should be used only when a more specific type is not known. `type` is a
primary classification for the artist identity, not the complete list of possible
performance functions. Use `roles`, `instruments`, and `voice` to record known
capabilities when helpful.

Performance roles remain contextual. For example, Nathalie Stutzmann can be
credited as a singer in one Performance and as a conductor in another. Pinchas
Zukerman can be credited as violinist in one Performance and violist in another.
The global Artist record may describe those known capabilities, but it must not
force every Performance to use the same role.

## Performance references

Performance records may reference a global Artist with `artist_id`:

```yaml
performers:
  - artist_id: nathalie-stutzmann
    name: Nathalie Stutzmann
    role: contralto
```

When `artist_id` is present, validation requires it to resolve to an Artist record
under `data/artists/`. The `name` field may preserve the source display form, and
the `role` field describes the artist's function in that specific recording.

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
