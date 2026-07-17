# Identifier Policy

## Purpose

This document defines the identifier strategy used throughout the music collection.

The primary design goal is long-term stability.

Identifiers exist to establish identity, not to convey meaning.

Human-readable names are represented separately through slugs.

---

# Design Principles

The identifier system follows five principles.

1. Identity is permanent.
2. Identifiers are meaningless.
3. Slugs are human-readable.
4. Slugs may change.
5. External identifiers never determine internal identity.

---

# Permanent Identifiers

Every primary entity receives exactly one permanent identifier.

The identifier:

- is assigned once;
- never changes;
- is never reused;
- is independent of titles and metadata;
- is independent of external databases.

Examples:

```
01JYB82P5Q4TF0C8MGRY9KGH0M
01JYB83A93D7G4MK5KXHYVY6KP
01JYB84S2YH89J3P2A71KDWX9F
```

The identifier has no semantic meaning.

Applications must never attempt to interpret any part of the identifier.

---

# Identifier Generation

Identifiers are generated automatically when a new entity is created.

Generation must satisfy:

- global uniqueness;
- immutability;
- independence from storage location;
- independence from import order.

Identifiers are never edited manually.

---

# Slugs

Every public entity has one preferred slug.

The slug exists solely for human readability.

Example:

```
berlioz-symphonie-fantastique
```

The slug:

- should be concise;
- should be descriptive;
- should remain reasonably stable;
- may change if editorial improvements are made.

Internal references must never use slugs.

---

# Slug Construction

Unless documented otherwise, slugs follow the structure

```
<primary-name>-<descriptive-name>
```

Typical examples include:

```
berlioz-symphonie-fantastique
mahler-symphony-5
bach-mass-in-b-minor
```

Slugs should avoid unnecessary metadata.

For example:

Good

```
mahler-symphony-5
```

Avoid

```
gustav-mahler-symphony-no-5-in-c-sharp-minor-1904
```

---

# Normalisation

Slug generation applies the following normalisation rules.

## Case

All characters are lowercase.

---

## Accents

Accented characters are converted to their ASCII equivalents.

Examples:

```
é → e
ö → o
ø → o
á → a
```

---

## Whitespace

Whitespace becomes a single hyphen.

Multiple consecutive hyphens are collapsed.

---

## Punctuation

Punctuation is removed unless it contributes to readability.

Examples:

```
No. 5
```

becomes

```
5
```

Ampersands become

```
and
```

Quotation marks are removed.

Parentheses are removed.

---

## Unicode

Canonical Unicode normalisation is applied before slug generation.

---

# Numbering

Common musical numbering is preserved in simplified form.

Examples:

```
Symphony No. 5
```

becomes

```
symphony-5
```

```
Piano Concerto No. 21
```

becomes

```
piano-concerto-21
```

Catalogue numbers are included only when required for disambiguation.

Example:

```
mozart-symphony-40-k550
```

not

```
mozart-k550
```

---

# Slug Changes

Changing a slug never changes the identity of an entity.

Whenever the preferred slug changes:

1. the previous slug is preserved;
2. the new slug becomes canonical;
3. existing references remain valid through redirects.

---

# Slug Aliases

Entities may contain any number of historical slugs.

Example

```
preferred slug

berlioz-symphonie-fantastique

aliases

berlioz-op14
fantastic-symphony
```

Aliases are never reused for another entity.

---

# Legacy Identifiers

Imported collections may contain legacy identifiers.

Legacy identifiers are stored only for migration purposes.

They never replace the permanent internal identifier.

---

# External Identifiers

External authority identifiers are stored separately.

Examples include:

- MusicBrainz
- Wikidata
- VIAF
- ISNI

External identifiers may be corrected or expanded.

They never determine internal identity.

---

# Deleted Entities

Identifiers are never deleted.

If an entity is removed because it was created in error, its identifier is retired.

The identifier remains reserved permanently.

It must never be reassigned.

---

# Merged Entities

When two entities are merged:

- one identifier becomes canonical;
- the other identifier is deprecated;
- deprecated identifiers remain resolvable;
- deprecated identifiers are never reused.

Historical references therefore remain valid indefinitely.

---

# Split Entities

When one entity is split into multiple entities:

- each new entity receives a new permanent identifier;
- the original identifier is retired;
- historical mappings are retained where possible.

---

# Internal References

Relationships between entities always reference permanent identifiers.

Slugs must never be used as foreign keys.

---

# Public URLs

Public URLs are based on the preferred slug.

The website should automatically redirect historical slugs to the canonical slug.

Users should never encounter broken links because of editorial improvements.
