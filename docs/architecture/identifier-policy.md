# Identifier Policy

This document defines the identifier strategy used throughout the music collection
for the current canonical model.

The canonical entities with permanent internal identifiers are Person, Work Group,
Work and Performance. The repository does not create separate canonical
Recording or Release identifiers.

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

External identifiers include MusicBrainz identifiers, Wikidata identifiers,
catalogue identifiers and platform identifiers. They are stored as evidence and
links after matching, not as replacements for repository identity.

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

Work Group is a permanently identified object type.

Each Work Group receives:

- its own permanent identifier;
- its own preferred slug;
- its own aliases;
- the same merge, split and retirement treatment as other primary entities.

The Work Group identifier is distinct from the identifiers of its member Works.
Changing membership, enriching metadata or adding explicit Work Relationships does
not change the Work Group's permanent identifier.

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

# Object-Specific Slug Rules

## Person slugs

Person slugs should use the most recognisable personal name form in conventional
English usage.

Examples:

```text
beethoven
saint-saens
vaughan-williams
```

For ensembles or groups, the most recognisable collective name should be used.

## Work Group slugs

Work Group slugs should reflect the shared artistic title of the family of Works.
They should be concise and should not include version-specific or performance-specific
metadata.

Examples:

```text
mahler-symphony-10
berlioz-symphonie-fantastique
```

## Work slugs

Work slugs should be more specific than the parent Work Group slug when the Work
represents a distinct artistic version or editorial interpretation.

Examples:

```text
mahler-symphony-10-cooke-completion
berlioz-symphonie-fantastique-1873-version
```

## Performance slugs

Performance slugs should be derived from the underlying Work and a short
profile or performer label when that is needed for disambiguation.

Examples:

```text
mahler-symphony-10-cooke-completion-berlin-philharmonic
bach-keyboard-concerto-bwv1052-piano
```

Performance slugs must never include platform, label, catalogue or release
metadata as their primary basis.

---

# Provisional Objects

Provisional status never affects permanent identity.

Once assigned, an identifier remains stable even when the object is later
enriched, reclassified or merged.

If an object is later found to duplicate another object, the normal merge policy
applies: one permanent identifier survives, and the deprecated identifier remains
available as an alias or redirect.

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
