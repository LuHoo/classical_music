# Work Group

## Purpose

A `Work Group` represents the artistic family of one musical composition.

It groups together all Works that originate from the same underlying musical idea
while remaining distinct artistic Works in their own right.

A Work Group exists primarily to organise closely related Works and to present
them coherently on the website.

It is **not** an editorial or workflow object.

---

## Core principle

A Work Group answers the question:

> *Which Works belong to the same artistic family?*

A Work answers:

> *Which specific artistic version is this?*

A Performance answers:

> *Which interpretation of that Work is recommended?*

---

## Relationship to Work

Every Work belongs to exactly one Work Group.

A Work Group contains one or more Works.

Examples include:

```text
Bruckner – Symphony No. 3
    ├── 1873 version
    ├── 1877 version
    └── 1889 version
```

or

```text
Mahler – Symphony No. 10
    ├── Cooke completion
    ├── Carpenter completion
    └── Wheeler completion
```

The Work Group provides the common artistic context.

The Works represent the individual artistic realisations.

---

## What does *not* belong to a Work Group

Differences in performance practice do **not** create additional Works or Work
Groups.

Examples include:

- piano versus harpsichord;
- historical versus modern instruments;
- different ensemble sizes when the artistic Work is otherwise the same;
- different conductors;
- different soloists;
- different choirs;
- different recording venues;
- different labels;
- remasters;
- digital releases.

These distinctions belong to Performances.

For example:

```text
Bach – Keyboard Concerto BWV 1052

Work Group
    │
    └── Work
            ├── Performance (piano)
            └── Performance (harpsichord)
```

The Work remains the same.

Only the recommended Performances differ.

---

## Navigation

The primary purpose of a Work Group is navigation.

It allows the website to present related Works together.

For example:

```text
Symphony No. 3

Available versions

• Original version (1873)
• Revised version (1877)
• Final version (1889)
```

Without the Work Group, these Works would appear unrelated.

---

## Metadata

A Work Group contains only metadata that applies equally to every Work within
the group.

Typical examples include:

- composer;
- canonical title;
- catalogue position within the composer's oeuvre;
- optional description.

Metadata that differs between versions belongs to the individual Work.

---

## Recommendation policy

Recommendations are never attached to a Work Group.

Recommendations belong exclusively to Performances.

A Work Group therefore has no recommendation status.

It may contain:

- Works with recommendations;
- Works without recommendations;
- a mixture of both.

---

## Workflow

The normal workflow never operates directly on Work Groups.

When adding a new recommendation:

```text
Performance
        ↓
Work
        ↓
Work Group (resolved through the Work)
```

Editorial comparison always occurs within:

- one Work;
- one performance profile (when applicable).

The Work Group plays no role in selecting or comparing Performances.

---

## Public presentation

The website may use the Work Group to:

- organise navigation;
- display alternative versions of a composition;
- provide context for related Works.

Visitors should perceive a Work Group as a convenient organisational concept,
not as an additional musical object.

---

## Required fields

Initially only a small number of fields are required:

- id
- composer_id
- title

---

## Optional fields

Examples include:

- catalogue number (when shared)
- aliases
- short description
- external identifiers

The Work Group should remain intentionally lightweight.

---

## Validation

Validation should ensure:

1. every referenced Work Group exists;
2. every Work belongs to exactly one Work Group;
3. Work Group identifiers are unique;
4. duplicate Work Groups are reported for manual review.

Validation should never merge Work Groups automatically.

---

## File location

Each Work Group is stored as:

```text
data/work-groups/<work-group-id>.yaml
```

---

## Summary

A Work Group is a lightweight organisational object.

It groups together artistically related Works while remaining independent of
editorial recommendations and performance practice.

Its primary responsibilities are:

- grouping related Works;
- supporting navigation;
- providing shared context.

The musical content resides in the Works.

The editorial content resides in the Performances.
