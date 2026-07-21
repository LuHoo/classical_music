# Workflow Design Notes

## Purpose

This document captures high-level curator workflows for migration and day-to-day maintenance.

It is not a schema, automation or implementation specification. Canonical entity boundaries are defined in `repository-architecture.md`, `work.md`, `performance.md` and `recommendation-policy.md`.

## Guiding principle

Workflows are centred around the curator's decisions.

Automation may help identify, validate, report and prepare candidates, but it must not replace editorial judgement or write recommendations automatically.

## Migration workflow

Migration from the existing Markdown collection should preserve durable editorial meaning:

- Persons in composer roles;
- Works;
- Work-level `gem` markers;
- accepted Performance recommendations;
- Tidal links;
- Gramophone references such as `(10/2021)`.

The migration process should produce reviewable candidates before canonical data is written.

For every migrated entry, determine:

1. the Person in the composer role;
2. the Work;
3. the Work Group;
4. whether the Work already exists;
5. whether the Performance already exists;
6. whether the relevant comparison category already has a recommendation.

Multiple candidate Performances of the same Work should be retained in migration review artefacts, not silently promoted into canonical Performance data.

## Playlist import workflow

Existing exported Tidal playlists may be used as source material.

For every playlist entry, determine:

1. composer identity;
2. Work identity;
3. candidate Performance identity;
4. whether the candidate duplicates an existing Performance;
5. whether it belongs to an existing comparison category;
6. whether a comparison issue is needed.

Playlist imports must not create canonical Performances until the curator has listened and accepted them as recommendations.

## Add a Performance

Adding a Performance is expected to be the primary day-to-day workflow.

If no recommended Performance exists for the comparison category:

1. Identify the Person in the composer role.
2. Identify or create the Work.
3. Determine whether a performance profile is relevant.
4. Verify the Performance.
5. Listen and accept it.
6. Add it as the canonical Performance.

If a recommendation already exists in the same comparison category:

1. Register the new item as a candidate outside canonical data.
2. Create one GitHub issue requesting editorial comparison, when the curator is actively considering it.
3. Listen.
4. Record the editorial decision.

Possible outcomes:

- keep the existing recommendation;
- replace it;
- conclude both entries are identical;
- reject the candidate;
- keep both only if they belong to different comparison categories.

## Extend the catalogue

Three scenarios are recognised.

### Performance found for an unknown Work

Create the missing Work and Work Group as needed, then attach the accepted Performance after listening.

### Add a Work without a Performance

Works may be added without an immediate recommendation so they appear on the website and can be completed later.

### Add the important catalogue of a composer

Populate important Works of a favourite composer, leaving recommended Performances for later where necessary.

## Add a Person in the composer role

Typical triggers include:

- Gramophone;
- radio;
- newly discovered repertoire;
- curator interest.

Steps:

1. Check whether the Person already exists.
2. Establish canonical identity.
3. Create the Person if needed.
4. Add the first Work.
5. Optionally add an accepted Performance.

## Search for alternatives

Searching for alternatives is always manually initiated by the curator, per Work.

A manual request may lead to:

1. external searching;
2. a small set of candidate Performances;
3. one GitHub issue for comparison;
4. listening;
5. an editorial decision.

`keep_looking: true` may appear on a canonical Performance, but it does not automatically create searches or GitHub Issues. A generated report may list these Performances.

## Maintain Tidal links

Replacing an obsolete or broken Tidal link with an updated link to the same interpretation does not create a new Performance.

Periodic link validation may generate reports, but link status should not determine whether the Performance remains recommended.

## Add Gramophone references

Gramophone references are low-priority enrichment.

Store:

- issue, such as `2021-10`;
- optional review URL.

Review text is not copied into the repository.

## Website publication

Website publication is not a curator workflow.

Accepted repository changes should trigger:

```text
repository update
    ↓
validation
    ↓
website generation
    ↓
GitHub Pages publication
```

The website should publish the current recommendation for each comparison category and omit internal workflow state unless a later explicit design decision changes that rule.

## Summary

Primary editorial workflows are:

1. migrate the existing collection;
2. add or compare Performances;
3. extend the catalogue with Works and Persons;
4. maintain links and references.

Supporting processes may generate reports and candidates, but canonical recommendations remain the result of manual editorial judgement.
