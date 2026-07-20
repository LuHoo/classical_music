# Performance

## Purpose

A `Performance` represents one curatorially accepted interpretation of exactly one `Work`.

It is the repository object that connects:

- one Work;
- the performers responsible for the interpretation;
- optional links through which the Performance may be accessed;
- optional references such as a Gramophone review;
- sparse metadata needed for recognition, matching, maintenance or presentation.

The term `Performance` is a practical collection concept. It may correspond externally to what another source calls a recording, track, album item, release or performance event.

The repository does not maintain separate canonical Recording or Release entities.

## Core rule

A Performance always refers to exactly one Work.

```text
Performance
    ↓
exactly one Work
```

A Tidal album may contain several Works. Each accepted interpretation of a Work is modelled as a separate Performance.

A canonical Performance must never contain multiple `work_id` values and must never point only to a Work Group.

### Unknown version assignment

A Performance may be canonical even when the exact version, completion or
edition of the recording is unknown, provided that the general Work identity is
clear.

In that case the Performance should refer to the general Work within the Work
Group and record the uncertainty explicitly, for example:

```yaml
work_id: mozart-mass-in-c-minor-k427
version_assignment: unspecified
notes: >
  Recording metadata does not identify a specific completion/version.
```

This fallback must not be used when the ambiguity could point to a different
Work, such as an arrangement instead of the original, a reconstruction instead
of a fragment, or a completion whose identity materially changes the
recommendation category.

## Curatorial boundary

A Performance enters canonical data only after the curator has listened to it and judged it good enough to recommend.

Candidate Performances that have not yet been heard or accepted do not belong in `data/performances/`.

They may temporarily exist in:

- a GitHub issue;
- a generated report;
- a migration review file;
- an external matching result.

Canonical data contains accepted Performances, not listening queues.

## Identity

Two entries represent the same Performance when they refer to the same underlying interpretation of the same Work.

The following do not by themselves create a new Performance:

- a changed Tidal URL;
- a reissue;
- a remaster;
- a different digital storefront;
- a different album containing the same interpretation;
- a changed catalogue number;
- a changed cover image;
- a spelling variation in performer metadata.

A new Performance is created when the underlying interpretation is different.

Typical indicators include:

- different performers;
- a different orchestra or ensemble;
- a different conductor;
- a different soloist;
- a different performance event or studio interpretation;
- a materially different recorded interpretation of the same Work.

When identity remains uncertain, the repository should report the case for review rather than silently creating a duplicate.

## Performers

A Performance records the performers needed to identify and present the interpretation.

Possible roles include:

- conductor;
- orchestra;
- ensemble;
- soloist;
- singer;
- choir;
- instrumentalist;
- accompanist.

The exact role structure should remain flexible enough to represent orchestral music, chamber music, piano music, vocal music and unusual ensembles.

Performers with stable canonical identities should refer to Person or ensemble identifiers rather than relying only on free text.

## Recommendation semantics

Every canonical Performance is recommended.

Presence in `data/performances/` should therefore imply recommendation. A field such as:

```yaml
recommended: true
```

is redundant and should be avoided unless a temporary migration requirement makes it necessary.

Publication rules, comparison categories and replacement policy are defined in `recommendation-policy.md`.

## Performance profiles

A performance profile belongs to a Performance, not to a Work.

It is used only when a musically meaningful distinction should preserve more than one public recommendation for the same Work.

Example:

- Bach keyboard concerto, piano;
- Bach keyboard concerto, harpsichord.

Profiles should remain sparse. The repository should not introduce a large predefined taxonomy.

## Keep looking

Some recommended Performances are acceptable but may later be improved.

This is represented by a simple boolean:

```yaml
keep_looking: true
```

Its meaning is only:

> This Performance is currently recommended, but the curator remains open to finding a better recommendation.

No explanation, score, stars, reason code or artistic/technical assessment is required.

`keep_looking: true` must not automatically create searches or GitHub Issues. A generated report may list these Performances.

## Platform links

Platform links belong to a Performance.

```yaml
links:
  tidal:
    url: https://tidal.com/...
```

A platform link is not the identity of the Performance.

Therefore:

- replacing a dead Tidal URL does not create a new Performance;
- multiple platform links may refer to the same Performance;
- a Performance may remain canonical even when no active platform link exists.

Operational fields such as link status or last-checked dates may be maintained outside canonical data or stored only when later schema design finds them necessary.

## Gramophone references

A Gramophone reference is optional metadata attached to a Performance.

Legacy notation such as:

```text
(10/2021)
```

means that the Performance was reviewed in the October 2021 issue of `Gramophone`.

Preferred representation may later be:

```yaml
reviews:
  gramophone:
    issue: 2021-10
    url: https://...
```

The repository stores only the reference. It does not store review text, extracted ratings, extended quotations or a complete review ontology.

## Optional disambiguating metadata

A Performance may contain limited additional metadata when it helps identify or present the interpretation.

Examples include:

- year;
- recording date;
- recording location;
- label;
- catalogue number;
- source album title;
- stable external identifiers.

These fields are optional and do not define canonical identity.

They should not be added merely because an external source provides them.

## Required fields

The initial required fields are:

- `id`;
- `work_id`;
- `performers`.

At least one performer relationship must be present. A platform link is not required.

Exact YAML syntax is deferred to later schema design.

## Migration implications

During migration:

- each legacy accepted Tidal-linked entry is interpreted as a Performance recommendation candidate;
- the associated Work must be identified first;
- performer names must be normalised;
- existing Gramophone references must be preserved;
- duplicate representations of the same interpretation must be detected;
- migration must not infer quality scores or reasons;
- `keep_looking` should be set only where explicitly decided by the curator.

Playlist imports may contain multiple Performances of the same Work. They should be retained in migration review artefacts or GitHub Issues until the curator decides which Performance becomes canonical for the relevant comparison category.

## Validation

At minimum, validation should ensure that:

1. `id` is unique;
2. `work_id` refers to an existing Work;
3. the Work is not a Work Group;
4. at least one performer is present;
5. referenced Person or ensemble identifiers exist;
6. platform URLs use supported platforms;
7. Gramophone issue values use `YYYY-MM`;
8. `keep_looking` is boolean;
9. no canonical Performance refers to more than one Work;
10. possible duplicate Performances are reported for review.

Validation should detect uncertainty, not resolve it silently.

## Website presentation

The website user should normally see only:

- the Work;
- the relevant performers;
- the streaming link, when available;
- the Gramophone review link, when available.

Internal fields such as external identifiers, link-check timestamps, migration notes, duplicate-detection data and `keep_looking` do not need to be publicly visible.

## Summary

A Performance is one accepted interpretation of exactly one Work.

It is canonical only after listening and editorial acceptance. Unheard candidates, active searches, comparisons and temporary alternatives remain outside canonical Performance data until an editorial decision has been made.
