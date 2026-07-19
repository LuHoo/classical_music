# Performance

## Purpose

A `Performance` represents one curatorially accepted interpretation of one musical `Work`.

It is the repository object that connects:

- a single Work;
- the performers responsible for the interpretation;
- the curator's recommendation;
- one or more links through which the Performance may be accessed;
- optional references such as a Gramophone review.

The term `Performance` is used as a practical collection concept. It may correspond externally to what another source calls a recording, track, album item, release, or performance event.

The repository does not maintain separate canonical entities for Recording and Release unless a future, demonstrated requirement makes that necessary.

## Core principle

A Performance always refers to exactly one Work.

```text
Performance
    ↓
exactly one Work
```

A Tidal album may contain several Works, but each Work represented in that album is modelled as a separate Performance.

A single canonical Performance must never contain multiple `work_id` values.

## Curatorial boundary

A Performance enters canonical repository data only after it has been listened to and judged good enough to recommend.

Candidate Performances that have not yet been heard or accepted do not belong in `data/performances/`.

They may temporarily exist in:

- a GitHub issue;
- a generated report;
- a migration review file;
- an external matching result.

The canonical repository contains accepted Performances, not listening queues.

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

When identity remains uncertain, the repository should not silently create a duplicate. The case should be reported for review.

## Relationship to Work

Each Performance must contain one valid `work_id`.

```yaml
work_id: martin-symphonie-concertante
```

The referenced Work must already exist in `data/works/`.

If a new Performance is discovered for a Work that does not yet exist, the Work must be created first.

A Performance may refer to a version-specific Work. It must never point only to a Work Group.

## Relationship to performers

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

The exact role structure should remain flexible enough to represent orchestral music, chamber music, piano music, vocal music, and unusual ensembles.

Performers that have stable canonical identities should refer to `Person` or ensemble identifiers rather than relying only on free text.

Illustrative examples:

```yaml
performers:
  conductor: bernard-haitink
  orchestra: royal-concertgebouw-orchestra
```

```yaml
performers:
  ensemble: alban-berg-quartett
```

```yaml
performers:
  piano: alfred-brendel
```

The final schema may choose either role keys or an ordered list of role assignments. The architectural requirement is that performer identity remains clear and machine-readable.

## Recommendation semantics

Every canonical Performance is recommended.

The repository therefore does not need a field such as:

```yaml
recommended: true
```

if presence in `data/performances/` already implies recommendation.

A separate recommendation flag should only be retained if required for migration compatibility or future support of non-recommended historical Performances.

The preferred initial rule is:

> A Performance file in canonical data represents an accepted recommendation.

## Keep looking

Some recommended Performances are acceptable but may later be improved.

This is represented by a simple boolean:

```yaml
keep_looking: true
```

Its meaning is:

> This Performance is currently recommended, but the curator wishes to remain alert for a better alternative.

No explanation is required.

The repository does not need to store:

- a quality score;
- stars;
- separate artistic and technical assessments;
- a justification;
- a reason code.

When `keep_looking` is absent or false, no active search is implied.

A list of Performances marked `keep_looking: true` may be generated automatically.

No GitHub issue should be created automatically from this flag.

## Alternative search workflow

Searching for alternatives is manually triggered per Work.

Only then may the system:

1. search external sources;
2. suggest plausible alternatives;
3. create a GitHub issue for comparison;
4. wait for listening and editorial judgement.

This pull-based model prevents the repository from generating a large backlog of inactive issues.

Alternative candidates remain non-canonical until they have been heard and accepted.

## Replacement and comparison

When a new accepted Performance is added for a Work that already has a recommended Performance, the existing recommendation must not be overwritten automatically.

A comparison issue should be created only when the curator is actively considering both.

Possible outcomes include:

- retain the existing Performance;
- replace it with the new Performance;
- temporarily retain both;
- determine that both entries represent the same Performance;
- reject the new candidate.

The repository should not assume that each Work can permanently have only one Performance unless that editorial rule is established elsewhere.

The public site may nevertheless choose to present one preferred Performance prominently.

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

Optional operational metadata may include:

```yaml
links:
  tidal:
    url: https://tidal.com/...
    status: active
    last_checked: 2026-07-19
```

Such operational fields are secondary and may be maintained by automated checks.

## Gramophone references

A Gramophone reference is optional metadata attached to a Performance.

Legacy notation such as:

```text
(10/2021)
```

means that the Performance was reviewed in the October 2021 issue of *Gramophone*.

Preferred representation:

```yaml
reviews:
  gramophone:
    issue: 2021-10
```

When available:

```yaml
reviews:
  gramophone:
    issue: 2021-10
    url: https://...
```

The repository stores only the reference.

It does not store:

- the review text;
- extracted ratings;
- extended quotations;
- a complete review ontology.

## Optional disambiguating metadata

A Performance may contain limited additional metadata when it helps identify or present the interpretation.

Examples include:

- year;
- recording date;
- recording location;
- label;
- catalogue number;
- source album title.

These fields are optional.

They should not be added merely because an external source provides them.

> Retain disambiguating metadata only when it materially helps recognition, matching, maintenance, or presentation.

## External identifiers

Stable external identifiers may be stored when useful.

```yaml
external_ids:
  musicbrainz_recording: ...
  musicbrainz_release: ...
  discogs_release: ...
```

External identifiers are references, not identity authorities.

A single Performance may legitimately point to identifiers from different external entity types because external databases model the same material differently.

The repository remains authoritative for the Performance identity.

## Suggested minimal structure

```yaml
id: example-performance
work_id: example-work

performers:
  conductor: example-conductor
  orchestra: example-orchestra

keep_looking: false

links:
  tidal:
    url: https://tidal.com/...

reviews:
  gramophone:
    issue: 2021-10
    url: https://...
```

For a Performance where a better alternative would be welcome:

```yaml
id: martin-symphonie-concertante-example
work_id: martin-symphonie-concertante

performers:
  conductor: example-conductor
  orchestra: example-orchestra

keep_looking: true

links:
  tidal:
    url: https://tidal.com/...
```

## Required fields

The initial required fields are:

- `id`;
- `work_id`;
- `performers`.

At least one performer relationship must be present.

A platform link is not required.

`keep_looking` defaults to `false` when omitted.

## Optional fields

Possible optional fields include:

- `year`;
- `links`;
- `reviews`;
- `external_ids`;
- limited disambiguating release information;
- `keep_looking`.

Optional fields should remain sparse.

## File location

Each Performance is stored in a separate canonical file:

```text
data/performances/<performance-id>.yaml
```

Example:

```text
data/performances/haitink-rco-bruckner-8.yaml
```

The filename should match the stable repository identifier.

Display names may change without requiring a new identifier.

## Validation rules

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

## Migration implications

During migration from the existing Markdown files:

- each accepted Tidal-linked entry becomes a Performance candidate;
- the associated Work must be identified;
- performer names must be normalised;
- existing Gramophone references must be preserved;
- duplicate representations of the same interpretation must be detected;
- migration must not infer quality scores or reasons;
- `keep_looking` should only be set where explicitly decided by the curator.

Playlist imports may contain multiple Performances of the same Work.

These should be retained for review rather than automatically collapsed.

## Website presentation

The website user should normally see only:

- the Work;
- the relevant performers;
- the Tidal link, when available;
- the Gramophone review link, when available.

Internal fields such as external identifiers, link-check timestamps, migration notes, duplicate-detection data, and `keep_looking` do not need to be publicly visible.

The public website may present a single preferred Performance or multiple Performances depending on later editorial policy.

## Deferred questions

The following choices may be finalised during schema design without changing this entity definition:

- exact YAML syntax for performer roles;
- whether ensembles are modelled as Persons or as a separate entity;
- whether more than one current recommended Performance may be publicly shown for one Work;
- whether historical superseded Performances remain canonical;
- which operational link-status fields are committed to Git;
- which external identifier types are supported initially.

These are implementation and policy decisions, not reasons to split Performance into Recording and Release.

## Summary

A Performance is:

- one accepted interpretation;
- of exactly one Work;
- identified by its performers and limited disambiguating metadata;
- optionally linked to Tidal and Gramophone;
- optionally marked `keep_looking: true`;
- canonical only after it has been heard and accepted.

The repository stores durable curator knowledge.

Unheard candidates, active searches, comparisons, and temporary alternatives remain outside canonical Performance data until an editorial decision has been made.
