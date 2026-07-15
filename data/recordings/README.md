# Canonical recording data

This directory contains internal recording records. A recording represents a specific release or recorded performance and is separate from the public composer and work pages.

The model supports:

- multiple works on one recording;
- references to canonical work IDs;
- references to canonical artist IDs;
- recommendation status per work;
- unstable streaming links with status and last-checked metadata;
- previous candidates that remain available internally without becoming public recommendations.

## Location

```text
data/recordings/<recording_id>.yaml
```

For example:

```text
data/recordings/haitink-rco-berlioz-fantastique.yaml
```

## Required fields

```yaml
id: haitink-rco-berlioz-fantastique
artists:
  conductor:
    - bernard-haitink
  orchestra:
    - royal-concertgebouw-orchestra
works:
  - work_id: berlioz-op14
    status: recommended
```

- `id` is the repository's stable internal recording identifier.
- `artists` maps performance roles to canonical artist IDs from `data/artists/`.
- `works` lists canonical work IDs from `data/works/` and gives each work a recommendation status.

## Recommended fields

```yaml
title: Berlioz: Symphonie fantastique
label: Philips
catalog_number: 0000 000
year: 1979
release_year: 1980

artists:
  conductor:
    - bernard-haitink
  orchestra:
    - royal-concertgebouw-orchestra
  soloist: []

works:
  - work_id: berlioz-op14
    status: recommended
    notes:

links:
  tidal:
    status: active
    url: https://tidal.com/browse/album/...
    last_checked: 2026-07-10

identifiers:
  musicbrainz_release_id:
  discogs_release_id:

notes: >-
  Optional local notes about edition, source, remastering, or selection decisions.
```

## Work statuses

Each work on a recording has one of these statuses:

- `recommended`: the current public recommendation for that work;
- `candidate`: under consideration but not yet the public recommendation;
- `previous_candidate`: previously considered and retained for history;
- `superseded`: once recommended, but replaced by another recording;
- `unavailable`: no longer usable as a recommendation, for example because the recording or link is unavailable.

A recording can therefore contain one recommended work and another work that is only a candidate.

The renderer must publish only work-recording combinations whose status is `recommended`. The presence of a recording in this directory does not itself make it public.

## Streaming links

Streaming links are external and unstable. Each service link should include:

```yaml
links:
  tidal:
    status: active
    url: https://tidal.com/...
    last_checked: 2026-07-10
```

Supported link statuses should initially be:

- `active`
- `unverified`
- `unavailable`
- `redirected`

`last_checked` uses ISO date format (`YYYY-MM-DD`). A future validator can warn when an active link has not been checked within a configured period.

A recording may include links for multiple services later without changing the work or artist references:

```yaml
links:
  tidal: ...
  spotify: ...
  apple_music: ...
```

## Artist roles

Artist roles are represented as lists, even where only one artist is expected:

```yaml
artists:
  conductor:
    - bernard-haitink
  orchestra:
    - royal-concertgebouw-orchestra
  choir:
    - bach-collegium-japan-chorus
  soloist:
    - mitsuko-uchida
```

This supports recordings with multiple conductors, ensembles, soloists, singers, or choirs. More specific roles such as `piano`, `violin`, `soprano`, or `narrator` may be added when useful, but should still contain canonical artist IDs.

## Recording identity

A recording ID should be stable and descriptive, but must not be treated as display text. A practical pattern is:

```text
<lead-artist>-<ensemble>-<composer-or-work>
```

Examples:

```text
haitink-rco-berlioz-fantastique
suzuki-bach-collegium-japan-mozart-great-mass
kremer-kremerata-baltica-mozart-violin-concertos
```

When two releases contain the same underlying performance, they may initially be represented by one recording record with release metadata. If release-level differences become important, a later model can separate `performance` from `release`.

## Validation rules

A future validator should check that:

1. every `work_id` resolves to exactly one canonical work;
2. every artist ID resolves to exactly one canonical artist;
3. every work status is allowed;
4. every link status is allowed;
5. every `last_checked` value is a valid ISO date;
6. only one recording is `recommended` for a work unless multiple recommendations are explicitly allowed;
7. a `previous_candidate`, `candidate`, `superseded`, or `unavailable` work is not published automatically;
8. duplicate service URLs are reported;
9. a recording with no works or no artists is rejected.

## External recording authorities

MusicBrainz release IDs can be stored as optional external identifiers. They should not replace local recording IDs because:

- one performance may appear on multiple releases;
- releases can be merged or split in external databases;
- the repository may model a recommendation at a different level from MusicBrainz.

The pilot therefore keeps nullable authority fields and does not populate them unless the exact release has been verified.
