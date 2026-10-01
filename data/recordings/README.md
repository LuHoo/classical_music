# Internal recording data model

This directory holds the internal YAML representation of recordings used for curation and maintenance. It is intentionally separate from the public recommendation pages, which remain a curated view of the current recommendations.

## Directory and filename convention

- Store one YAML file per recording under `data/recordings/`.
- Use a lowercase slug with hyphens for the recording ID.
- The filename should be the same as the `id` field, with a `.yml` suffix.

Examples:

- `data/recordings/berlioz-symphonie-fantastique.yml`
- `data/recordings/berlioz-orchestral-collection.yml`

## Proposed YAML format

```yaml
id: example-recording-id
title: Example release title
label: Example Label
catalog_number: ABC-123
year: 1998
edition: Remastered
artists:
  conductor:
    - canonical-artist-id
  orchestra:
    - canonical-artist-id
  soloists:
    - canonical-artist-id
works:
  - work_id: canonical-work-id
    status: recommended
    track:
      number: 1
      title: Example track title
    notes: Optional note for this work on this recording.
    links:
      tidal:
        url: https://tidal.com/browse/album/12345
        status: active
        last_checked: "2026-07-09"
links:
  tidal:
    url: https://tidal.com/browse/album/12345
    status: active
    last_checked: 2026-07-09
notes: Optional note about the release as a whole.
```

## Field definitions

### Recording-level fields

- `id` (required): stable internal identifier for the recording, using a lowercase slug.
- `title` (required): the release or album title.
- `label` (optional): label name.
- `catalog_number` (optional): catalogue number.
- `year` (optional): original release year.
- `edition` (optional): edition, reissue, or remaster note.
- `artists` (optional): mapping of performer role names to arrays of canonical artist IDs. Roles are free-form and may include `conductor`, `orchestra`, `soloists`, `piano`, `choir`, or any other useful role.
- `works` (required): list of works contained on the recording.
- `links` (optional): album-level external links such as streaming or purchase links.
- `notes` (optional): free-form notes about the recording as a whole.

### Work-entry fields

Each item in `works` represents one work on the recording.

- `work_id` (required): canonical work ID.
- `status` (optional): recommendation status for the relationship between this recording and this work.
- `track` (optional): minimal track-level information when needed to distinguish a specific track or movement on the album.
  - `number` (optional): track number or position.
  - `title` (optional): track title.
- `notes` (optional): free-form notes for this work on this recording.
- `links` (optional): work-specific external links; this is used when a specific track or work needs a different URL from the album-level link.

### Link fields

Each link entry supports:

- `url` (required): the external URL.
- `status` (required): one of the values below.
- `last_checked` (optional): date the link was last checked in `YYYY-MM-DD` form.

Allowed link statuses:

- `active`: the link is known to be usable.
- `unavailable`: the link is known to be unavailable, removed, or inaccessible.
- `broken`: the link appears malformed or clearly broken.
- `unknown`: the link has not yet been checked.

## Recommendation statuses

The recommendation status belongs to the relationship between a recording and a work, not to the recording as a whole.

- `recommended`: this recording is the current public recommendation for that work.
- `candidate`: this recording is under active consideration for that work.
- `previous_candidate`: this recording was considered previously and is retained only as internal history.
- `superseded`: this recording was once the recommendation but has since been replaced.
- `unavailable`: this recording is no longer reasonably accessible or relevant for recommendation purposes.

### Treatment of unevaluated works

If a work is present on an album but has not yet been evaluated, it should be listed in `works` without a `status` field. This keeps the album contents visible in the internal data without implying a recommendation state.

## Design decisions

1. Recommendation status is stored within each work entry in the recording file, rather than in a separate mapping. This keeps the status attached to the specific recording/work relationship.
2. The invariant “at most one current recommendation per work” should be enforced later by a validation script or CI check. It should reject any case where more than one recording file has a work entry with status `recommended` for the same canonical work ID.
3. Works that have never been evaluated are represented as work entries without a `status` field.
4. Links may apply to the album as a whole via the top-level `links` field, or to an individual work via `works[].links` when a specific URL is needed.
5. Reissues or remastered editions are stored as separate recording files with their own `id`; the edition information belongs in the recording file via `edition`, `year`, and `catalog_number`.
6. Required fields are `id`, `title`, and `works`. The rest are optional unless a future schema requires them.
7. A formal schema or validation mechanism is not added in this issue; that is a sensible follow-up task once the format is exercised with real data.

## Example: single-work recording

See `data/recordings/berlioz-symphonie-fantastique.yml`.

## Example: multi-work recording with mixed statuses

See `data/recordings/berlioz-orchestral-collection.yml`.

## Separation from public recommendation pages

These files are internal source data. They do not directly generate the public composer or work pages. The public site remains a curated presentation of the current recommended recordings, while this directory stores the underlying internal record for albums, works, performers, and recommendation states.

## Assumptions and follow-up work

- Canonical artist IDs and canonical work IDs are assumed to exist elsewhere in the repository or will be introduced in a later step.
- This proposal does not implement import tools, link monitoring, or automatic publication of public pages.
- A follow-up issue could add a schema, a validation script, and tooling for maintaining these files.
