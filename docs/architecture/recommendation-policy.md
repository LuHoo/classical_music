# Recommendation Policy

## Purpose

This document defines the editorial rules that determine how recommended Performances are selected, compared and published.

It does not define Work or Performance structure. Those entity boundaries are defined in `work.md` and `performance.md`.

## Guiding principle

The repository is not a catalogue of available recordings.

It is a curated collection of recommendations. The goal is to identify the Performance that is currently recommended for each comparison category.

Recommendations must never be replaced automatically.

## Comparison categories

For every comparison category there is one public recommendation.

A comparison category consists conceptually of:

- one Work;
- one performance profile, when a performance profile is relevant.

For most Works no explicit performance profile is needed.

Example:

```text
Ravel - Bolero
```

Some Works may legitimately have more than one public recommendation because different performance traditions should not be treated as alternatives.

Example:

```text
Bach - Keyboard Concerto BWV 1052
    piano
    harpsichord
```

The harpsichord Performance must not automatically be treated as a replacement candidate for the piano Performance.

## Performance profiles

A performance profile belongs to a Performance, not to a Work.

A profile may be proposed from available metadata, such as instrument credits, but not all curatorially relevant distinctions can reliably be inferred from metadata. The final profile is therefore an explicit canonical classification.

Performance profiles should remain sparse and should be introduced only when a musically meaningful distinction needs to be preserved.

The repository should not create a large predefined taxonomy of performance profiles.

## Candidate Performances

A newly discovered Performance is never accepted automatically.

The normal comparison workflow is:

1. Identify the Work.
2. Determine the performance profile, if any.
3. Locate the current recommendation in that comparison category.
4. Create one comparison issue if necessary.
5. Listen.
6. Make an editorial decision.

Candidate Performances remain outside canonical data until accepted.

## Editorial decisions

After comparison the curator may:

- retain the existing recommendation;
- replace it with the candidate;
- conclude both represent the same Performance;
- reject the candidate;
- keep both only when they belong to different comparison categories.

During comparison there may temporarily be a current recommendation and a candidate. After editorial judgement, only one recommendation remains public within that comparison category.

## Keep looking

Some recommendations are satisfactory but not definitive.

```yaml
keep_looking: true
```

This indicates only that the curator remains open to finding a better recommendation.

It does not require an explanation, score, stars, reason code or artistic/technical assessment.

It does not trigger automatic searches or GitHub Issues.

A generated report may list Performances marked `keep_looking: true`.

## Searching for alternatives

Searching for alternative Performances is always manually initiated by the curator, per Work.

A manual request may lead to:

1. an external search;
2. a small set of candidate Performances;
3. one GitHub issue for comparison;
4. listening;
5. an editorial decision.

Do not design automatic searches or automatic GitHub issue creation for every Work or Performance marked as improvable.

## Website policy

The public website normally displays only the current recommendation for each comparison category.

Visitors should receive a clear recommendation rather than a catalogue of all available Performances.

Candidates, workflow state, matching evidence, migration state, link-check data and `keep_looking` are not normally shown.

When a recommended Performance is attached to a general Work because the exact
version, completion or edition is unknown, the website may omit that internal
uncertainty unless it is useful to users. The recommendation remains valid as a
recommendation for the general Work.

## Summary

The repository answers one editorial question:

> Which Performance do I currently recommend for this Work and, where relevant, this performance profile?

Everything else belongs to the editorial workflow rather than the public recommendation.
