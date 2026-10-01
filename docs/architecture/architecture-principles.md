# Architecture Principles

## Purpose

This document is the governing architectural policy for the repository.

All implementation work, Codex tasks, migration work, validation rules, workflow design and future architecture changes must be checked against these principles before work begins.

More detailed architecture documents define individual entities and processes. If an implementation conflicts with these principles or with the normative architecture documents, the implementation must change rather than silently reinterpret the architecture.

## 1. Curated collection, not music database

The repository exists to publish and maintain a curated collection of classical Works and recommended Performances.

It is not intended to reproduce MusicBrainz, Discogs, Tidal, Wikipedia or another comprehensive music catalogue.

When a simpler model fully supports the curator and the website, prefer the simpler model.

## 2. The repository is canonical

Canonical identity, relationships and editorial recommendations belong to this repository.

External sources support identification, validation and maintenance. They do not define the collection.

Missing external metadata or identifiers are not defects by themselves.

## 3. Existing legacy data is trusted input

The existing curated collection is assumed to be substantially correct.

Migration and validation must preserve its editorial meaning unless there is positive evidence of an identity problem.

Do not require existing records to prove their identity again merely because an external authority is incomplete or ambiguous.

## 4. Person and Work identity must be correct

The highest accuracy requirement applies to the identity of Persons and Works.

Before creating or materially changing an identity-critical entity, automation should use repository evidence and appropriate external authorities to establish identity as confidently as possible.

Human curator review is required only when a consequential identity question remains unresolved after automation has done the available investigation.

## 5. Minimal persistent metadata

Store only durable information needed to:

- identify or distinguish entities;
- represent the curator's recommendation;
- support the public website;
- maintain useful external links;
- document consequential identity decisions.

Do not accumulate metadata merely because an external source provides it.

## 6. External authorities are supporting tools

MusicBrainz and other appropriate authorities may provide ground truth for identity questions.

Authority lookup is demand-driven. Complete external-ID coverage is not a project objective.

Absence of a MusicBrainz Work ID does not make an otherwise clear existing Work uncertain or incomplete.

## 7. Core domain model

The canonical model is:

```text
Person
  ↓
Work Group
  ↓
Work
  ↓
Performance
```

The arrows express the principal conceptual relationships, not ownership or mandatory one-to-one cardinality.

Do not introduce canonical Recording or Release entities unless a demonstrated user or maintenance requirement cannot be met by the current model.

## 8. Work Group is lightweight

A Work Group groups closely related Works that belong to the same artistic family.

It primarily supports organisation, shared context and navigation.

It does not carry recommendations and does not participate in Performance comparison.

Work Group uncertainty should not be escalated to the curator unless it materially affects Work identity or website navigation.

## 9. Work represents artistic identity

A Work represents one distinct artistic composition or version.

Composer revisions are separate Works within the same Work Group.

Practical instrumentation or performance differences do not automatically create separate Works.

An arrangement, orchestration, transcription, completion or other derived form may be a separate Work when it represents a distinct artistic object recognised by the composer, musical tradition or the curator's presentation needs.

## 10. Performance represents the recommendation

A Performance represents one curatorially accepted interpretation of exactly one Work.

A Performance enters canonical data only after the curator has listened to it and judged it good enough to recommend.

Changed streaming URLs, reissues, remasters and alternative digital manifestations do not by themselves create new Performances.

Candidate Performances and listening queues are not canonical data.

## 11. Performance profiles are sparse and explicit

Different performance traditions may require separate recommendations without creating separate Works.

Examples include piano and harpsichord Performances of the same Bach keyboard concerto.

When such a distinction matters, store a sparse `performance_profile` on the Performance.

Metadata may suggest a profile, but the canonical profile is a curatorially meaningful classification. Do not build a large universal profile taxonomy.

## 12. One public recommendation per comparison category

A comparison category is conceptually:

```text
Work + performance_profile (when applicable)
```

For each comparison category the website normally publishes one recommendation.

Temporary competing candidates may exist during editorial comparison, but workflow state must not be confused with the public recommendation.

The curator controls recommendation changes. They are never replaced automatically.

## 13. `gem` is presentation only

`gem` is a public Work attribute expressing the curator's special recommendation of that Work.

It does not affect identity, validation, workflow priority or authority lookup.

## 14. `keep_looking` is passive

A recommended Performance may contain:

```yaml
keep_looking: true
```

This means only that the curator remains open to a better Performance.

It must not automatically trigger searches, GitHub Issues or recurring curator work.

Searching for alternatives is manually initiated per Work.

## 15. Automation must reduce curator workload

Automation exists to do research, matching, classification, validation and routine maintenance before asking the curator a question.

Curator review is the last resort, not the default fallback.

A technical warning, missing identifier or possible similarity must not automatically become a curator task.

If automation produces a large human review queue, first re-examine the automation and classification rules.

## 16. Distinguish errors, identity gates and background suspicions

### Invariant violations

Structural errors such as broken references, duplicate permanent IDs or invalid canonical relationships should be strict and may block merging.

### Identity gates

New or materially changed Person/Work identities require strong verification. Automation should resolve as much as possible before escalation.

### Background suspicions

Possible anomalies in trusted existing data may remain in generated reports when they do not currently affect canonical identity or use of the collection.

Background suspicions must not:

- fail unrelated CI;
- automatically create GitHub Issues;
- be presented as immediate curator work.

They become active only when explicitly selected for review or when a consequential identity-changing operation makes them relevant.

## 17. Durable knowledge versus temporary work

Canonical data stores durable curator knowledge.

Temporary evidence, candidates, searches, migration intermediates and unresolved background suspicions belong in reports, caches or GitHub Issues as appropriate.

GitHub Issues represent active work, not a storage location for every theoretical improvement.

## 18. Git workflow is mandatory

Substantive repository changes follow this default workflow:

```text
latest appropriate base
    ↓
dedicated feature branch
    ↓
focused commits
    ↓
tests and validation
    ↓
draft pull request
    ↓
curator review
```

Do not commit substantive changes directly to `main`.

Do not merge or mark the PR ready for review unless the curator explicitly asks for that action.

This workflow is a project default and does not need to be repeated by the curator in every task.

## 19. Mandatory completion and adversarial review protocol

Substantive Codex/agent work must not be declared complete on the basis of passing tests or self-generated metrics alone.

### Completion has three distinct stages

```text
implementation
    ↓
adversarial self-review
    ↓
completion evidence
```

Passing tests after implementation is necessary but is not by itself evidence that the task is complete.

### Adversarial self-review is mandatory

Before claiming completion, the implementing agent must actively try to falsify its own solution against the task's architecture and acceptance criteria.

Examples of adversarial review:

- **for automatic identity matches**, look for evidence that the selected Person/Work/Performance could be wrong;
- **for unresolved/escalated cases**, try to prove that repository evidence or appropriate authority evidence can resolve the case without the curator;
- **for migrations**, verify that trusted source information was not lost by parsing or normalization;
- **for workflow automation**, inspect whether the implementation manufactures avoidable curator work;
- **for validators**, test both false positives and false negatives rather than optimizing warning counts.

A current function's inability to resolve a case is a software diagnosis, not evidence that human judgment is required.

### Curator escalation requires exhaustion of automation

An identity case may be labelled `curator_required` only after the agent has established:

```text
repository evidence insufficient
AND
appropriate demand-driven authority evidence insufficient or genuinely ambiguous
AND
the unresolved question materially affects canonical identity or an active curator decision
```

If repository evidence can resolve it, classify it as automation work. If only external authority evidence is still required, classify it as an authority gate, not curator work.

### Independent ground truth

Never validate a resolver/classifier by treating its own output as ground truth.

Ground truth must come from an independent source appropriate to the task, such as:

- trusted legacy provenance;
- canonical repository evidence independent of the decision under test;
- catalogue identifiers or established relationships;
- an appropriate authoritative external source;
- a previously recorded curator decision.

A result is not proven correct merely because the selected canonical ID exists or its title looks plausible.

### Completion claims require evidence pointers

Codex/agents must not claim `done`, `complete`, `all requirements satisfied`, or equivalent unless every acceptance criterion has a concrete evidence pointer.

Require a PR section conceptually like:

```markdown
## Completion evidence

### Acceptance criteria
- [x] Criterion 1
  Evidence: `path/file.py` + named test/report section
- [x] Criterion 2
  Evidence: `reports/...` §...

### Adversarial self-review
Cases deliberately tested to falsify the implementation:
- ...

### Remaining unresolved cases
- repository_resolvable: 0
- authority_evidence_required: N
- curator_required: N

For every curator_required case:
- repository evidence checked: ...
- authority evidence checked: ...
- why human judgment remains necessary: ...

### Repository hygiene
- [x] no runtime artifacts
- [x] no backup implementation files
- [x] generated files intentionally retained only
- [x] PR body/docs reflect current implementation
```

The exact formatting may vary, but the evidence content is mandatory. A checked box without an evidence pointer does not count as completion evidence.

### Re-read the original task before declaring completion

Immediately before the completion claim, the agent must re-read:

- the issue/task description;
- all blocking review comments still applicable;
- the acceptance criteria;
- the governing architecture documents.

It must explicitly reconcile its implementation against them. Requirements may not silently be moved to `future work` when they were part of the current acceptance criteria.

### Technical metrics are diagnostic, not completion criteria

Metrics such as match rate, warning count, line coverage, external-ID coverage or number of passing tests do not prove architectural correctness by themselves.

Prefer domain-level success measures such as:

- zero known false-positive identity matches;
- no unnecessary curator escalations;
- all identity-critical decision paths behaviorally tested;
- canonical data remains within the documented domain model;
- curator/user workflow is actually simplified.

### Repository hygiene is part of completion

Runtime artifacts, caches, backup source files, stale generated output and obsolete PR/documentation claims must be removed before completion unless explicitly retained as stable repository artifacts.

### Relationship to existing principles

This protocol explicitly reinforces:

- Principle 2: repository is canonical;
- Principle 3: trusted legacy data;
- Principle 4: Person/Work identity accuracy;
- Principle 6: demand-driven authorities;
- Principle 15: automation reduces curator workload;
- Principle 16: distinguish identity gates from background suspicions;
- Principle 18: mandatory Git workflow.

## Mandatory pre-flight checklist

Before starting any implementation, Codex task or substantive repository change, answer these questions:

1. **Architecture** — Which normative architecture documents constrain this task, and has the current version of each been read?
2. **Purpose** — Does the proposed work directly support the curated recommendation collection or website?
3. **Scope** — What is the smallest change that fully achieves that purpose?
4. **Identity** — Does the task create or change Person or Work identity? If so, what evidence can automation establish before curator review?
5. **Curator load** — Does the proposed solution reduce human work, or does it manufacture a new review backlog?
6. **Canonical boundary** — Which results are durable canonical knowledge, and which belong only in reports, caches, candidates or Issues?
7. **External authority** — Is authority lookup necessary for a real identity question, rather than being pursued for metadata completeness?
8. **Simplicity** — Is there a simpler model or workflow that fully supports the curator and website?
9. **Git workflow** — Is the work being performed in a dedicated feature branch with tests/validation and a draft PR as the endpoint?
10. **Success criterion** — Is success defined in curator/user terms rather than technical completeness metrics such as external-ID coverage?

If these questions expose a conflict with the proposed task, stop and correct the task before implementation.

## Governing rule

When in doubt, preserve the curator's intent, protect Person and Work identity, minimise persistent metadata and human workload, and choose the simplest architecture that fully supports the collection and website.
