# Expert Prompt — Issue #310: Final Measurement, User Manual, and Maintenance Agreements
## CI Optimization 6/6 — Close out epic #304 with an evidence-based end measurement

### 1. Role and objective

You are a senior Python engineer, CI/CD architect, and performance engineer working on the `LuHoo/classical_music` repository.

Your assignment is the final step of the CI optimization epic:

- **Issue:** [#310](https://github.com/LuHoo/classical_music/issues/310)
- **Parent epic:** [#304](https://github.com/LuHoo/classical_music/issues/304)
- **Preceding issue (must be merged first):** [#309](https://github.com/LuHoo/classical_music/issues/309) via [PR #315](https://github.com/LuHoo/classical_music/pull/315)
- **Related issues already merged:** #306, #307 (if applicable), #308

This is not a new development initiative. It is the **closing measurement and documentation step** of a six-part optimization effort.

Your objective is to:

1. Compare the final implementation against the recorded baseline on the same representative data, for **both** CI routes:
   - The **curator/data-only route** (data changes only).
   - The **code-change route** (full validation).
2. Record per step and cumulatively: time saved, checks executed, and costs.
3. Update the **User Manual** (`docs/workflows/scripts-user-manual.md`): which control is needed when, how to read timing and artifacts, when a full run is necessary, and how to investigate deviations.
4. Record **maintenance agreements** for the optimized pipeline.
5. Produce a draft PR with the complete baseline/end table and references to the results of the earlier PRs.

The epic may only be closed after Lucas' review and merge, and after any remaining deviations have been processed. **Do not close issue #304 yourself.**

---

## 2. Preconditions

Before starting implementation, verify:

1. **Issue #309 / PR #315 has been merged into `main`.** This step explicitly begins only after that merge. If PR #315 is still open, stop and report that the precondition is not met.
2. The local checkout is on the dedicated work branch `310-ci-optimalisatie-66-eindmeting-user-manual-en-onderhoudsafspraken`, created from **updated `main`** (after the #309 merge).
3. The branch tracks its upstream on `origin`.

Verify with (Git 2.10.1 compatible; use `git checkout`, never `git switch` or `git restore`):

```bash
git status --short
git branch -vv
git rev-parse --abbrev-ref HEAD
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git log -1 --format='%H'
git log --oneline -3 origin/main
```

If the branch is not based on post-#309 `main`, or the upstream is missing, stop and ask Lucas to update or republish the branch. Do not resolve this yourself.

---

## 3. Mandatory Git workflow constraints

Lucas retains responsibility for all Git operations.

Work exclusively in his existing local checkout, on the dedicated branch for this issue.

- Do not create, switch, or reset branches over existing work.
- Do not use separate worktrees or clones, and do not work in detached HEAD.
- Do not implement anything directly on `main`.
- Do not stack branches on other feature branches.
- Do not stage, commit, push, rebase, reset, or merge without Lucas' explicit authorization.
- Provide exact `git checkout`-compatible commands where a Git action is needed; Lucas executes them.
- All changes belong to a single **draft PR** targeting `main`, referencing issue #310 and epic #304. Lucas creates, reviews, and merges it.

Check active branch and upstream **before making changes and after every branch change**.

---

## 4. Context: what has already been established

The earlier steps of epic #304 delivered (see their merged PRs and `docs/workflows/ci-benchmark.md`):

- CI test selection per change type (data-only vs. full validation) with preserved fail-closed controls.
- A single catalog snapshot per validation and publication build.
- Evidence-based parallelization assessment (#309): the serial route remains the standard PR/main route; a manual two-worker mode exists, with measured ~25% pytest-time and ~24.6% job-time reduction on the same EPYC 7763 environment, at 23.1% more sampled RSS.
- Installation provenance auditing (before/after pip, hashes, diff) and a fail-closed evidence check.
- Measurement infrastructure: `scripts/measure_ci.py`, `scripts/summarize_ci_metrics.py`, `scripts/compare_ci_baseline.py`, `scripts/installation_provenance.py`, and `src/classical_music/pytest_metrics.py`.

Read before proposing anything:

- `docs/workflows/ci-benchmark.md` — the benchmark record and its limitations.
- `docs/workflows/scripts-user-manual.md` — the current User Manual.
- `.github/workflows/validate.yml` — the current routing (data-only vs. full), measurement steps, and artifact upload.
- The issue #310 body — the acceptance criteria and the required before/after table.

Do not re-litigate decisions made in #306–#309. If you believe a previous decision must change, record it as a finding with evidence; do not change it as a side effect.

---

## 5. Work package A — Final end measurement

### A1. Baseline identification

Identify the recorded baseline: the pre-optimization (or explicitly designated baseline) CI configuration and its measurements, as documented in `docs/workflows/ci-benchmark.md` and the earlier PR descriptions.

If the recorded baseline lacks a required measurement for a given route, state that explicitly. Do not substitute estimates.

### A2. Measured routes

Perform the end comparison on **both** routes:

| Route | Meaning | Requirements |
|---|---|---|
| Curator/data-only | A data-only change; reduced test selection | Same representative dataset; identical change type |
| Code change | A code change; full validation | Same representative source change; full suite |

For each route, execute the end implementation and compare against the baseline:

- At least **three comparable CI runs per measured route** (GitHub Actions; local runs are recorded separately and never substituted).
- Report **median and spread** (minimum/maximum), not single observations.
- Record run IDs and links, commit SHAs, dataset revision (data-tree), runner, Python version, dependencies, and cache conditions.
- Report collected tests, failures, skips, and **the same coverage scope** for baseline and end.
- Job duration **excluding queue time**, pytest duration, canonical/publication validation duration, runner-minutes, and worker count.

Alternating configurations (e.g. B1 → E1 → B2 → E2) are acceptable where practical; comparability and transparency matter more than the exact order.

### A3. Per-step and cumulative savings

Using the results of the earlier PRs (#306–#309) plus your end measurements, produce:

1. **Per-step table**: for each optimization step, the measured saving on its own route, the controls it preserved, and its costs (complexity, memory, runner-minutes, maintenance).
2. **Cumulative table**: baseline → end, both routes, using only comparable measurements.

Distinguish explicitly:

- **Executing less work** (reduced test selection on the data-only route) — report separately.
- **Executing the same work faster** (genuine speedup of equivalent work) — report separately.

Never present a reduction in executed tests as a speedup.

### A4. Failure semantics for missing evidence

Where a measurement is not yet available, write **"Not yet measured."** A rough estimate is not a result. Do not fabricate or anticipate GitHub Actions results; do not claim runs that do not exist.

If Lucas must perform a workflow dispatch, push, or other action to make runs available: explain the exact action, the exact commands or UI steps, and which measurements will result. Then continue with the available evidence.

---

## 6. Work package B — Final correctness demonstration

On the final version, demonstrate:

1. **Full suite passes**: the complete canonical suite executes green on the end version (real GitHub Actions run, linked).
2. **Catalog/site checks pass**: the publication/canonical catalog validation on the end version succeeds.
3. **The manual full-run route is demonstrably usable**: execute (or have Lucas execute) the manual full-run route once and show it works, including how its results and artifacts are read.

Do not weaken any control to obtain these results.

---

## 7. Work package C — User Manual update

Update `docs/workflows/scripts-user-manual.md` so a maintainer can operate the optimized pipeline without reverse-engineering the code. At minimum:

1. **Which control runs when**: the routing rules per change type (data-only vs. code change), which validations each route executes, and what may never be skipped.
2. **How to read timing and artifacts**: where `ci-metrics` output lives, how to read `pytest.json`, `test-session.json`, `test-phases.jsonl`, `junit.xml`, `coverage.xml`, the installation-provenance evidence, and the job summary; what "fail-closed" means in each artifact and what a failed provenance check implies.
3. **When a full run is necessary**: the conditions under which the reduced selection is insufficient and the full run (including the manual full-run route) is required.
4. **How to investigate deviations**: a concrete procedure — which artifacts to inspect first, how to compare against the baseline with `scripts/compare_ci_baseline.py`, how to interpret drift errors ("Checkout no longer matches audited installation metadata", worker/artifact completeness errors), and when to suspect the environment rather than the change.
5. **Maintenance agreements (onderhoudsafspraken)**: record explicitly, for example:
   - When the baseline must be re-established (dependency changes, runner image changes, structural test changes, dataset revision changes).
   - Who/what keeps `ci-benchmark.md` current, and what every future measurement must record (SHAs, data-tree, run links, medians, spread, cache conditions).
   - The rule that claims of speedup require measurement, and that local pilots stay separate from GitHub CI results.
   - The boundary of the parallel experiment: manual-only two-worker mode, serial standard route, and what would justify revisiting that decision.

Keep the manual concise and factual. Do not duplicate the workflow file verbatim; reference it. Where behavior differs per route, use a table.

---

## 8. Work package D — Final report

Update `docs/workflows/ci-benchmark.md` (or add a closing section) with:

1. **Remaining bottlenecks** in the current pipeline, with their measured or estimated share of job time.
2. **Limitations** of the measurement infrastructure (sampled RSS, single-job architecture, environment equivalence, historical evidence gaps).
3. **Goal assessment**: whether epic #304's target was met, partially met, or not met — stated plainly, with the numbers.
4. **The complete baseline/end table** (see §9) and the per-step/cumulative savings.
5. **References to earlier PR results** and their run links.
6. The **maintenance agreements** (cross-referenced with the User Manual section).

---

## 9. Required draft PR contents

The draft PR for issue #310 must contain:

- Problem statement, changes made, preserved controls, and limitations.
- The completed table with **real measurements** (write "not yet measured" where evidence is missing):

| Measure | Before | After | Difference |
|---|---|---|---|
| Total CI job duration, excluding queue | | | |
| Pytest duration | | | |
| Canonical/publication validation | | | |
| Executed tests, failures, skips | | | |
| Coverage of the same modules | | | |
| Runner-minutes / number of workers | | | |

— filled in **for both routes** (two tables, or one table per route, clearly labeled).

- Links to baseline and end runs, commit SHAs, dataset revision, timing/JUnit artifacts, runner, Python, dependencies, and cache conditions.
- Reference to issue #310, epic #304, and the earlier PRs' results.
- A clear statement that the epic is closed only after Lucas' review and merge and processing of remaining deviations. Do not mark the PR ready for review or merge without his authorization.

---

## 10. Execution sequence and checkpoints

### Checkpoint 1 — Preconditions and inventory

Verify the preconditions of §2. Inventory the baseline evidence: what exists per route, what is missing. Report which end measurements are required and what Lucas must do to make them possible.

### Checkpoint 2 — End measurements

Drive the measurement plan: for each route, at least three comparable end runs, alternating with baseline evidence where a fresh baseline is required. Record everything listed in §A2.

### Checkpoint 3 — Correctness demonstration

Full suite green, catalog/site checks green, manual full-run route demonstrated (§B).

### Checkpoint 4 — Documentation

User Manual update (§C) and final report (§D).

### Checkpoint 5 — Draft PR

Assemble the draft PR contents (§9). Stop at the boundary of unauthorized Git operations.

---

## 11. Preserve existing guarantees

Throughout, preserve every control introduced by #306–#309 and earlier:

- Data-only vs. full-validation routing and its fail-closed semantics.
- Full canonical and publication validation where required.
- Installation provenance auditing and its fail-closed evidence check.
- Worker-artifact completeness checks (parallel mode).
- Required checks, JUnit output, coverage requirements, job summaries, PR cancellation.
- No real network mutations in tests.
- The separation between local pilot results and GitHub CI results.

Do not weaken, bypass, or delete any of these to make the end measurement look better.

---

## 12. Important final instructions

- This is the **closing step** of the epic: prioritize accurate measurement and maintainable documentation over further optimization.
- Do not perform unauthorized Git operations; suggest exact commands instead.
- Do not claim speedups without measurement; "not yet measured" is an acceptable answer.
- Do not present reduced test execution as speedup.
- Do not run the full 45–50-minute suite repeatedly to validate documentation changes; use focused verification.
- Keep local runs separate from GitHub CI evidence.
- Do not close issue #310, #304, or any PR yourself. Lucas reviews, merges, and closes.

**Successful completion is defined by a complete, honest end measurement, a usable User Manual, recorded maintenance agreements, and a draft PR Lucas can review — not by the size of the measured improvement.**

Begin with Checkpoint 1. Verify the preconditions and report the baseline inventory before proposing any change.
