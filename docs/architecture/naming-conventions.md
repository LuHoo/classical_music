# Naming Conventions

> Status: Superseded for Recording and Release naming by
> `repository-architecture.md` and `performance.md`.
>
> This document records earlier naming guidance. The current authoritative
> canonical model uses Performance, not separate Recording or Release entities.

## Purpose

This document defines the naming conventions used for human-readable slugs in the music collection.

These conventions apply to composers, persons, ensembles, works, work parts, recordings and releases. They are intended to make slugs:

* recognisable;
* concise;
* consistent;
* predictable;
* suitable for filenames and public URLs.

Slugs are not permanent identifiers. Permanent identity is governed by `identifier-policy.md`.

---

# General Principles

Slugs use English naming conventions, contain only ASCII characters and include no more information than is necessary for recognition and disambiguation.

The preferred form is the shortest form that remains clear and unique within the relevant entity type.

Examples:

```text
mahler-symphony-5
saint-saens
rimsky-korsakov
berlioz-symphonie-fantastique
```

---

# 1. Language

English is the default language for slugs.

Generic musical forms, genres, instruments and descriptive terms use standard English names.

Examples:

```text
symphony
piano-concerto
violin-sonata
mass
string-quartet
```

Fixed work titles may remain in their established original-language form when that form is commonly used in English-language musical discourse.

Examples:

```text
debussy-la-mer
wagner-die-walkure
stravinsky-le-sacre-du-printemps
berlioz-symphonie-fantastique
```

English conventional spellings are used for personal names and transliterated titles.

---

# 2. Character Set

Slugs contain ASCII characters only.

Accents and other diacritical marks are removed.

Examples:

```text
Saint-Saëns → saint-saens
Dvořák → dvorak
Bartók → bartok
Janáček → janacek
```

The correctly accented form remains available in display metadata.

---

# 3. Personal Names

Personal-name components use the most recognisable full family name in its conventional English spelling.

Initials and shortened family names are not used.

Examples:

```text
rimsky-korsakov
vaughan-williams
saint-saens
rachmaninoff
```

Avoid:

```text
r-korsakov
rimsky
rvw
rakhmaninov
```

Compound family names retain all meaningful components.

Alternative spellings and transliterations may be stored as aliases or search terms.

---

# 4. Conciseness

Slugs omit information that is implied, redundant or unnecessary for identification.

Examples:

```text
mahler-symphony-5
mozart-piano-concerto-21
beethoven-piano-sonata-14
```

Avoid:

```text
mahler-symphony-no-5-in-c-sharp-minor
mozart-concerto-for-piano-and-orchestra-no-21
beethoven-piano-sonata-number-14-in-c-sharp-minor
```

Words such as `no`, `number`, `opus`, `major`, `minor`, `for` and `in` are omitted unless they are needed for recognition or disambiguation.

---

# 5. Normalised Word Order

Instrument or performing force normally precedes the work genre.

Examples:

```text
piano-concerto
violin-concerto
cello-sonata
piano-sonata
flute-quartet
```

Avoid:

```text
concerto-for-piano
concerto-for-violin
sonata-for-cello
```

The following established ensemble and chamber-music terms are exceptions:

```text
string-quartet
string-quintet
piano-quartet
piano-quintet
piano-trio
```

These conventional forms are preferred over mechanically reordered alternatives.

---

# 6. Numbering

Arabic numerals are used wherever possible.

Examples:

```text
symphony-5
piano-concerto-21
string-quartet-14
act-2
book-1
```

Avoid:

```text
symphony-v
fifth-symphony
piano-concerto-xxi
```

Roman numerals are retained only in exceptional cases where they form an indispensable and established part of the title or identity.

---

# 7. Catalogue Numbers

Catalogue numbers are included only when necessary.

They may be used when:

* a work has no sufficiently recognisable title or conventional number;
* two otherwise valid slugs would be identical;
* the catalogue number is the usual means of identifying the work.

Catalogue identifiers are normalised and written as concisely as possible.

Examples:

```text
bach-cantata-bwv140
mozart-adagio-k546
schubert-piano-sonata-d960
vivaldi-violin-concerto-rv269
```

Preferred compact forms include:

```text
bwv140
k550
d960
rv269
```

Avoid unnecessary separators such as:

```text
bwv-140
k-550
d-960
```

unless a particular catalogue system requires separators for clarity.

---

# 8. Keys

Keys are normally omitted from slugs.

Examples:

```text
beethoven-symphony-5
mozart-piano-concerto-21
schubert-piano-sonata-d960
```

Keys may be added only when required to distinguish otherwise identical works.

When included, keys follow this convention:

```text
c-major
c-minor
e-flat-major
f-sharp-minor
b-flat-minor
```

---

# 9. Titles and Nicknames

A formal title or conventional work designation takes precedence over a nickname.

Examples:

```text
haydn-symphony-94
beethoven-symphony-6
dvorak-symphony-9
```

Avoid using the nickname as the canonical slug:

```text
haydn-surprise-symphony
beethoven-pastoral-symphony
dvorak-new-world-symphony
```

Nicknames may be retained as title aliases or search terms.

For works with a unique established title, that title is used.

Examples:

```text
rimsky-korsakov-sheherazade
debussy-la-mer
holst-the-planets
```

---

# 10. Initial Articles

Initial articles are retained when they form part of an established work title.

Examples:

```text
debussy-la-mer
holst-the-planets
wagner-die-walkure
stravinsky-le-sacre-du-printemps
```

Articles may be ignored separately for sorting purposes, but are not removed from the slug.

---

# 11. Apostrophes

Apostrophes are removed without inserting an additional separator.

Examples:

```text
L'enfant et les sortilèges
```

becomes:

```text
lenfant-et-les-sortileges
```

Similarly:

```text
L'heure espagnole
```

becomes:

```text
lheure-espagnole
```

---

# 12. Hyphens

An existing hyphen in a personal name or fixed title remains semantically visible.

Examples:

```text
rimsky-korsakov
saint-saens
vaughan-williams
```

Because spaces and most separators also become hyphens during normalisation, the source metadata remains authoritative for determining whether a hyphen belongs to the name itself.

---

# 13. Transliteration

Names and titles originally written in non-Latin scripts use one consistent conventional English transliteration.

Examples:

```text
tchaikovsky
rachmaninoff
shostakovich
mussorgsky
prokofiev
```

Alternative transliterations are not used interchangeably in canonical slugs.

They may be stored as aliases or search terms.

Examples of non-canonical alternatives include:

```text
chaikovsky
rakhmaninov
musorgsky
prokofyev
```

---

# 14. Disambiguation

When the normal slug is not unique, the minimum stable distinguishing element is added.

Suitable disambiguators include:

* conventional numbering;
* catalogue number;
* year of version or revision;
* arranger or orchestrator;
* place or institutional qualifier;
* generation suffix in an established personal name.

Examples:

```text
johann-strauss-i
johann-strauss-ii
bach-violin-concerto-1
bach-violin-concerto-2
bruckner-symphony-8-1890
```

Disambiguation must not depend on database order, internal identifiers or temporary metadata.

Avoid:

```text
bach-violin-concerto-2a
bach-violin-concerto-copy
bach-violin-concerto-new
```

---

# 15. Versions, Revisions and Arrangements

When versions, revisions, arrangements or orchestrations are modelled as separate Works, the distinction must be visible in the slug.

Examples:

```text
bruckner-symphony-8-1890
stravinsky-firebird-suite-1919
mussorgsky-pictures-at-an-exhibition-ravel-orchestration
```

Preferred distinguishing terms include:

```text
version
revision
arrangement
orchestration
suite
excerpt
```

A year alone may be used where it is the conventional and sufficient distinction.

Examples:

```text
bruckner-symphony-8-1887
bruckner-symphony-8-1890
```

The shortest clear and stable form is preferred.

Use the minimum distinguishing suffix needed to identify the concrete Work.

Preferred order:

1. fixed version year;
2. stable editorial version name;
3. functional distinguishing term.

Examples:

```text
-1887
-1890
-original-version
-revised-version
-with-recitation
-without-recitation
```

Arrangement, orchestration, completion and realisation slugs should name the
distinguishing agent or form when that is the clearest identity cue.

Examples:

```text
-ravel-orchestration
-schoenberg-orchestration
-sussmayr-completion
-gamzou-realisation
-string-orchestra
-piano-version
```

---

# 16. Work Groups

A Work Group uses the unsuffixed conceptual slug when multiple concrete Works
exist for versions, revisions, arrangements, orchestrations, completions or other
derivative forms of the same compositional source.

Examples:

```text
bruckner-symphony-8
stravinsky-petrushka
mahler-symphony-10
```

Concrete Works within the Work Group add the minimum distinguishing suffix.

Examples:

```text
bruckner-symphony-8-1887
bruckner-symphony-8-1890
stravinsky-petrushka-1911
stravinsky-petrushka-1947
mahler-symphony-10-gamzou-realisation
```

The main slug without a version suffix belongs to the Work Group when multiple
concrete Works exist.

A single ordinary Work does not automatically receive a Work Group. In that case,
the unsuffixed slug remains available for the Work itself.

This replaces the pilot convention where a `conceptual_parent` could be modelled
as a Work. The parent slug belongs to the Work Group once the collection needs a
formal grouping entity.

---

# 17. Work Parts

A Work Part uses the slug of its parent Work followed by `mvmt` and its Arabic movement number.

Examples:

```text
mahler-symphony-5-mvmt-1
mahler-symphony-5-mvmt-2
beethoven-string-quartet-14-mvmt-6
```

The movement title is normally not included in the canonical slug.

Avoid:

```text
mahler-symphony-5-first-movement
mahler-symphony-5-movement-no-1
mahler-symphony-5-mvmt-4-adagietto
```

A movement title may be retained as display metadata or a search alias.

For structural divisions other than movements, an equivalent concise term may be used where needed, such as:

```text
act-1
scene-2
book-3
part-1
```

---

# 18. Recordings

Recording slugs identify the performed recording, not a commercial release.

The preferred form uses the principal artist or artists and the performed Work:

```text
<principal-artist>-<ensemble-or-secondary-artist>-<work>
```

Example:

```text
dudamel-berlin-philharmonic-mahler-symphony-5
```

When required for disambiguation, add the recording year:

```text
dudamel-berlin-philharmonic-mahler-symphony-5-2021
```

For recordings without a conductor, the principal soloist, ensemble or other
leading credited artist takes the first position.

Where more than one soloist has equal prominence, the smallest recognisable
combination of principal names is used.

Recording slugs should not attempt to identify a label, catalogue number or
platform edition. Those belong to Release slugs.

---

# 19. Releases

Release slugs identify published editions or digital platform releases.

For orchestral recordings, the preferred order is:

```text
<conductor>-<orchestra>-<release-year>-<label>-<catalogue-number>
```

Example:

```text
haitink-concertgebouw-1985-philips-4162832
```

Fallback when label or catalogue number is not yet known:

```text
<conductor>-<orchestra>-<release-year>-tidal-<album-id>
```

Example:

```text
dudamel-berlin-philharmonic-2022-tidal-123456789
```

The conductor is treated as the principal artist, followed by the orchestra.

The following rules apply:

* use the recognisable family name of the conductor;
* use a concise, established name for the orchestra;
* use the release year, not the recording year;
* use the normalised label name;
* include the catalogue number in compact normalised form;
* use a platform fallback only while fuller release metadata is unavailable;
* omit punctuation and spaces from the catalogue number unless needed for clarity.

Examples:

```text
karajan-berlin-philharmonic-1963-deutsche-grammophon-138923
haitink-concertgebouw-1985-philips-4162832
rattle-london-symphony-2017-lso-live-lso0790
```

For releases without a conductor, the principal soloist, ensemble or other leading credited artist takes the first position.

Examples:

```text
pollini-1977-deutsche-grammophon-2530644
amadeus-quartet-1962-deutsche-grammophon-138894
```

Where more than one soloist has equal prominence, the smallest recognisable combination of principal names is used.

Release slugs should not attempt to list all included works.

Work relationships are maintained separately through permanent identifiers.

---

# Normalisation Procedure

Slug generation applies the following steps in order:

1. select the preferred English or established original-language name;
2. apply the entity-specific word-order convention;
3. transliterate non-Latin scripts using the approved English form;
4. convert accented characters to ASCII;
5. convert all letters to lowercase;
6. remove apostrophes without replacement;
7. remove other punctuation unless needed as a meaningful separator;
8. replace whitespace and remaining separators with hyphens;
9. collapse consecutive hyphens;
10. remove leading and trailing hyphens;
11. add the minimum stable disambiguator when necessary.

---

# Aliases

Alternative names, spellings, transliterations, nicknames and previous canonical slugs may be stored as aliases.

Examples:

```yaml
slug: rachmaninoff-piano-concerto-2
slug_aliases:
  - rakhmaninov-piano-concerto-2

title_aliases:
  - Piano Concerto No. 2 in C minor
```

Aliases do not change the canonical slug and must not be reused for another entity.

---

# Examples

## Persons

```text
saint-saens
rimsky-korsakov
vaughan-williams
rachmaninoff
tchaikovsky
```

## Works

```text
mahler-symphony-5
haydn-symphony-94
mozart-piano-concerto-21
bach-cantata-bwv140
rimsky-korsakov-sheherazade
debussy-la-mer
holst-the-planets
```

## Work Parts

```text
mahler-symphony-5-mvmt-1
mahler-symphony-5-mvmt-4
beethoven-symphony-9-mvmt-4
```

## Versions and Arrangements

```text
bruckner-symphony-8-1890
stravinsky-firebird-suite-1919
mussorgsky-pictures-at-an-exhibition-ravel-orchestration
```

## Recordings and Releases

```text
haitink-concertgebouw-1985-philips-4162832
karajan-berlin-philharmonic-1963-deutsche-grammophon-138923
rattle-london-symphony-2017-lso-live-lso0790
```

---

# Scope

These conventions define the current canonical naming policy.

Exceptional cases may require a documented editorial decision. Such exceptions must preserve the underlying principles of:

* recognisability;
* conciseness;
* consistency;
* stable disambiguation;
* separation between human-readable naming and permanent identity.
