# Workflow Design Notes

## Status

This document captures the current design decisions regarding the curator workflows for the classical music repository. It is intentionally high-level and serves as input for a later, more detailed `workflow-architecture.md`.

## Guiding principle

The workflows are centred around the activities of the curator rather than the implementation details of the software.

## Primary workflows

### 1. Migrate the existing collection

**Phase A – Existing Markdown collection**

Preserve:
- Persons (Composers)
- Works
- Gem markers
- recommended Performances
- Tidal links
- Gramophone references such as `(10/2021)`

**Phase B – Existing Tidal playlists**

Import the exported Excel playlists (orchestral, chamber and piano music).

For every playlist entry determine:

1. Composer
2. Work
3. Whether the Work already exists
4. Whether the Performance already exists
5. Whether another recommended Performance already exists

Multiple Performances of the same Work should initially be retained as candidates.

### 2. Add a Performance

This is expected to become the primary day-to-day workflow.

If no recommended Performance exists:

1. Identify Composer
2. Identify Work
3. Verify Performance
4. Add Performance

If a recommended Performance already exists:

- Register the candidate Performance
- Create a GitHub issue requesting editorial comparison

Possible outcomes:

- Keep the existing recommendation
- Replace it
- Keep both temporarily
- Conclude both entries are identical
- Reject the candidate

### 3. Extend the catalogue

Three scenarios are recognised.

**A. Performance found for an unknown Work**

Create the missing Work and attach the Performance.

**B. Add a Work without a Performance**

Works may be added without an immediate recommendation so they appear on the website and can be completed later.

**C. Add the complete catalogue of a Composer**

Populate all important Works of a favourite Composer, leaving recommended Performances for later if necessary.

### 4. Add a new Composer

Typical triggers:

- Gramophone
- Radio
- Newly discovered repertoire

Steps:

1. Check whether the Person already exists
2. Establish canonical identity
3. Create the Composer
4. Add the first Work
5. Optionally add a recommended Performance

### 5. Maintain Tidal links

Manual:

- Replace obsolete or broken links with updated links to the same Performance.

Periodic:

- Investigate automated monthly validation of stored Tidal links.

### 6. Add Gramophone references

Low-priority enrichment.

Store:

- issue (e.g. 2021-10)
- optional review URL

Review text is not copied into the repository.

## Website publication

Website publication is not a curator workflow.

Accepted repository changes should automatically trigger:

Repository update
→ validation
→ website generation
→ GitHub Pages publication

## Summary

Primary editorial workflows:

1. Migrate the existing collection.
2. Add or compare Performances.
3. Extend the catalogue with Works and Composers.
4. Maintain the collection.

Supporting processes:

- Tidal link validation
- Gramophone references
- Automatic website publication

A future `workflow-architecture.md` will describe the detailed identification and matching pipeline.
