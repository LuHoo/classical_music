# Recommendation Policy

## Purpose

This document defines the editorial rules that determine how recommended Performances are selected, compared and published.

It deliberately does **not** define the structure of a Work or a Performance. Those are specified elsewhere. This document describes the curator's decision process.

---

## Guiding principle

The repository is not a catalogue of available recordings.

It is a curated collection of recommendations.

The goal is therefore not to identify every existing Performance, but to identify the Performance that is currently recommended.

---

## One public recommendation

For every comparison category there is exactly one published recommendation.

Visitors come to the website for a recommendation, not for a list of options.

Other music services already provide exhaustive catalogues.

---

## Comparison categories

Recommendations are compared only within the same comparison category.

A comparison category consists of:

- one Work;
- one performance profile (when applicable).

For most Works there is only one comparison category.

Example:

    Ravel – Boléro

For some Works multiple performance traditions exist.

Example:

    Bach – Keyboard Concerto BWV 1052
        Piano
        Harpsichord

Each performance profile has its own recommendation.

The workflow must never compare Performances from different performance profiles.

---

## Performance profiles

A performance profile is introduced only when it represents a musically meaningful distinction that the curator wishes to preserve.

Examples include piano and harpsichord.

Performance profiles should remain exceptional rather than becoming a general classification system.

---

## Candidate Performances

A newly discovered Performance is never accepted automatically.

Workflow:

1. Identify the Work.
2. Determine the performance profile (if any).
3. Locate the current recommendation in that comparison category.
4. Create a comparison issue if necessary.
5. Listen.
6. Make an editorial decision.

---

## Temporary dual recommendations

During evaluation there may temporarily be:

- current recommendation;
- candidate recommendation.

After the decision there is again exactly one published recommendation within that comparison category.

---

## Editorial decisions

After comparison the curator may:

- retain the existing recommendation;
- replace it with the candidate;
- conclude both represent the same Performance;
- reject the candidate.

The repository never replaces recommendations automatically.

---

## Keep looking

Some recommendations are satisfactory but not definitive.

Example:

```yaml
keep_looking: true
```

This indicates only that the curator would welcome a better recommendation.

It does not trigger automatic searches or GitHub issues.

---

## Alternative searches

Searching for alternatives is always initiated manually.

The system may then:

1. search external sources;
2. propose candidate Performances;
3. create a single GitHub issue for review.

This pull-based workflow prevents large backlogs.

---

## Website policy

The public website normally displays only the current recommendation for each comparison category.

Candidates, workflow state and internal maintenance information are not shown.

---

## Design principles

1. The repository stores durable editorial knowledge.
2. Editorial judgement is never automated.
3. Comparisons occur only within the same comparison category.
4. Recommendations are replaced only after explicit review.
5. Workflow state belongs in GitHub Issues, not canonical data.
6. Simplicity takes precedence over exhaustive classification.

---

## Summary

The repository answers one question:

> Which Performance do I currently recommend?

Everything else belongs to the editorial workflow rather than the canonical collection.
