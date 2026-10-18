# Expert Implementation Prompt — Issue #309: Safe CI Parallelization Assessment (merged version)

## 1. Role and objective

You are acting as a senior Python engineer, CI/CD architect, test-infrastructure engineer, and performance engineer working on the `LuHoo/classical_music` repository.

Your assignment is to implement **GitHub issue #309** within the existing CI optimization epic (#304).

**Objective:** Determine, by reproducible measurement, whether running the existing tests with two parallel workers or splitting tests into separate GitHub Actions jobs produces a worthwhile improvement over the optimized serial execution established by preceding issues — **without** losing checks, isolation, coverage, or reliable reporting.

This is an evidence-driven performance investigation, not a mandate to introduce parallel execution. A well-argued decision to stay serial is a fully valid outcome.

Do not introduce permanent parallelization unless comparable measurements demonstrate a meaningful benefit without compromising correctness, reproducibility, coverage, or failure detection.

## 2. Repository context and prerequisites

- Issue: https://github.com/LuHoo/classical_music/issues/309
- Epic: https://github.com/LuHoo/classical_music/issues/304
- Preceding step: issue #308, merged PR https://github.com/LuHoo/classical_music/pull/314
- Working branch: `309-ci-optimalisatie-56-veilige-parallelisatie-beoordelen-en-meten`
- At the time this prompt was written, this branch and `origin/main` were at `0055b686f23b11c48db94dc2c15102fd54d9520d`, the merge of PR #314. Verify the actual state yourself; do not treat this as a standing guarantee.
- Read first: the current issue description, applicable `AGENTS.md`, `pyproject.toml`, `.github/workflows/validate.yml`, `docs/workflows/ci-benchmark.md`, and the relevant code and tests.

Before implementing anything:

1. Inspect the current repository, workflows, tests, and available documentation.
2. Read issues #309 and #308 and their relevant implementation history if accessible.
3. Identify the existing CI execution model, the canonical validation commands, and the test-selection logic.
4. Identify existing performance measurement facilities and artifacts.
5. Check whether relevant optimizations from preceding issues have been merged into `main`.
6. Determine which existing tests and validation steps are eligible for parallel execution.

Treat the actual repository implementation as authoritative. Do not assume that any particular tool, plugin, or configuration already exists.

### Explicit prerequisites

Implementation must take place exclusively in Lucas's existing local checkout on the named branch with upstream configured. Before making changes, inspect:

```bash
git status --short --branch
git rev-parse --abbrev-ref HEAD
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
git log -1 --format='%H'
```

Verify that:

- The current branch is the dedicated working branch for issue #309.
- The branch is not `main` and has a valid upstream.
- The preceding issue has been merged into the updated `main` baseline.
- The checkout is suitable for implementation: no unexpected pre-existing local work that changes the semantics of measurements.

If the correct working basis is missing, **stop before making any changes** and explain exactly what Lucas needs to restore.

**Do not perform Git operations on Lucas's behalf:** no fetch/pull, checkout, reset, staging, commit, push, or merge without separate explicit authorization. Local Git is known to be 2.10.1; do not advise `git switch` or `git restore`. Do not create worktrees, clones, detached HEADs, new branches, or stacked branches. Do not implement on `main`. Respect existing local work and existing measurement files.

Leave external changes, workflow dispatches, and PR publication to Lucas unless he separately authorizes them. Do prepare a complete draft-PR description targeting `main`, referencing #309 and #304. Lucas reviews and merges himself.

### Out of scope

- No source-playlist or TIDAL actions, no musical-curator decisions, no changes to real user data, no expansion into issue #310 (broader end-measurement and maintenance wrap-up stay outside this step).
- The directory `reports/prompts/` is shared via Git. Raw measurement output belongs in the existing ignored measurement directories or CI artifacts; a durable account belongs in the project documentation.

## 3. Immutable guarantees

These guarantees are architectural constraints, not functionality to replace:

1. **No test weakening.** Do not delete, skip, weaken, or add retries to tests or validation to make parallel execution faster or greener.
2. **Same-workload comparison.** The tests selected by #308 remain substantively identical per route: compare full-serial vs. full-parallel, and data-only-serial vs. data-only-parallel. Never compare different routes as if the difference were parallelization gain.
3. **Checks stay.** Current canonical, publication, source-preservation, and cross-intake checks remain in place. No previously successful validation may serve as cache evidence for changed data.
4. **Fail-closed required check.** The required check `validate` remains reliably red on any relevant error or missing mandatory result. No path filters or dependency constructs that silently turn green.
5. **One canonical validator run.** One canonical validator run keeps feeding console, JSON, and summary. The separate real site build and link check remain preserved.
6. **Cancellation scope.** Cancellation remains restricted to superseded runs of the same PR; other PRs, `main`, and manual runs stay protected. Preserve the classifier's revision and completeness checks.
7. **Route selection unchanged.** Preserve the data-only versus full-validation routing established in #308. Preserve the manually selectable full-validation route.

## 4. Phase A — Establish the current execution baseline and cost profile

Reconstruct the existing CI execution model and produce a short analysis based on actual timings and code:

- Which tests determine the critical path duration? Which costs sit in setup, collection, YAML loads, catalog snapshots, publication build, and teardown?
- Which tests are CPU-, memory-, or I/O-bound? How much does task distribution help if a few long tests dominate total duration?
- Which session fixtures are rebuilt per process? `catalog_snapshot`, `canonical_matcher`, and curator fixtures are important candidates. Account for extra catalog loads and memory per worker; a session fixture is not automatically shared between workers.
- Inventory all write targets, temporary directories, locks, fixed filenames, global state, environment mutations, and subprocesses. Check publication output, curator decision records, coverage, JUnit, and measurement files in particular.
- Verify tests cannot perform real network mutations or duplicate external actions. Locks and rollback remain correct even when tests run concurrently. Do not remove a lock to make a benchmark pass.
- Reuse fixtures only when they are immutable. Mutating tests get their own temporary directories; the real checkout, `publication/`, and user decisions remain untouched.

Use the current test isolation and relevant tests, including `tests/conftest.py`, `tests/test_suite_isolation.py`, curator/collection tests, and publication tests. Add only meaningful regression tests for risks actually found.

Distinguish at least: workflow initialization and dependency installation, test collection, actual test execution, canonical validation and publication checks, coverage aggregation and reporting, artifact generation and upload, and GitHub Actions job startup/orchestration. Measure separately where existing instrumentation permits.

### Baseline requirements

Use current post-#308 baselines; old 453/517-test runs are historical context, not an automatic baseline for new code. Record per run: workflow/run identifiers, commit SHA, dataset/data revision and content identity (and any local dirty status — do not claim exact committed evidence from a modified checkout), route, full command line, collected nodeids, executed tests, failures, errors, skips, retries, Python version, runner OS/image, dependency versions and lockfile revision, cache state, wall-clock durations, runner-minutes, memory where measurable, and coverage including modules covered.

Check the usability of `ci-baseline/` first; the previously encountered empty `baseline.json` is not a valid measurement report.

Do not alter test selection merely to improve measured performance.

## 5. Phase B — Investigate parallelization risks

Conduct a systematic parallel-safety assessment before enabling parallel execution.

### 5.1 Temporary files and directories

Inspect tests and validation commands for shared temporary paths, fixed filenames, generated publication files, persistent output directories, cache directories, files written relative to the repository root, and cleanup procedures that could remove another worker's output. Identify any operations where independent workers could overwrite, delete, or read one another's intermediate results. Use isolated temporary directories where necessary. Do not introduce different test semantics merely to support parallel execution.

### 5.2 Shared mutable fixtures

Inspect session-, module-, and other shared-scoped fixtures. Determine whether tests depend on global mutable state, shared files, shared database state, environment variable modifications, process-wide caches, a particular execution order, or initialization performed by another test. Distinguish thread safety, process isolation, and cross-job isolation: an arrangement safe for separate processes is not necessarily safe for concurrent processes modifying shared filesystem resources.

### 5.3 Locks and serialization

Identify existing locking mechanisms and serialization requirements. Check for lock contention, non-atomic file operations, shared write targets, race conditions, deadlock risks, and implicit synchronization through test ordering. Do not remove safety mechanisms to obtain faster measurements. Avoid adding locks that merely recreate serial execution with additional process overhead.

### 5.4 External side effects

Tests must not cause real external mutations. Inspect operations involving network calls, remote APIs, playlist modifications, publication or deployment actions, external data updates, and remote storage. Ensure tests use appropriately isolated mocks or fixtures. Parallel execution must not duplicate external actions.

### 5.5 Retries and nondeterminism

Inspect any retry behavior and failure recovery. Do not introduce retries that conceal race conditions or intermittent test failures. A test that succeeds only after retrying must not silently count as equivalent to a deterministically passing test. Document any pre-existing nondeterminism encountered.

## 6. Phase C — Instrument the existing measurement infrastructure for the experiment

Inspect explicitly:

- `src/classical_music/pytest_metrics.py`: currently rejects parallelism; `Metrics` writes fixed names and truncates `test-phases.jsonl` at initialization.
- `scripts/measure_ci.py`: currently reports `workers=1`; also check the scope of process measurements.
- `scripts/compare_ci_baseline.py`: requires identical workers, command line, dependencies, and tree IDs within a baseline. These safeguards must not simply disappear to make a comparison possible.
- `scripts/summarize_ci_metrics.py`, `scripts/summarize_execution.py`, coverage and JUnit output, and existing infrastructure tests.

Adapt this infrastructure in a targeted way where needed:

- Give each worker/job/run attempt its own output paths and traceable metadata. No concurrent writes or truncation of the same files.
- Distinguish controller and worker events. Do not count a test phase twice if an event is visible both locally and via the controller. Report setup/call/teardown, errors, and counters with their real scope.
- Merge results deterministically. Check completeness, run identity, worker/shard identity, expected test nodeids, and outcomes. Missing, duplicate, truncated, or unreadable mandatory results must not silently count as success.
- Keep individual artifacts available on failure or crash. Make clear which results are incomplete; a sum of successful partial results does not prove a successful run.
- Preserve strict comparison within a measurement condition. Make the serial-vs-parallel comparison explicit, with only the intended differences allowed (e.g., workers and scheduler arguments). Install the same dependency set in both conditions where possible and use the same benchmark-capable code/test revision.
- Do not modify or "normalize" raw provenance to make two incomparable runs look equal. Record legitimate differences; collect new runs if evidence is insufficient.
- Check current official documentation and version compatibility before configuring e.g. pytest-xdist and pytest-cov. Make no assumptions about coverage combination or fixtures across process boundaries.
- If additional timing instrumentation is needed, implement the smallest reliable change before proceeding.

## 7. Phase D — Evaluate execution alternatives

Start from the existing serial execution and one limited parallel candidate: **two workers**. Do not use unlimited `-n auto`. Investigate separate test jobs only if timing and isolation give a concrete reason; do not build multiple parallelization systems unnecessarily.

- **Configuration S — Serial baseline.** The existing optimized execution model. This is the control configuration and must remain available throughout.
- **Configuration P1 — Two pytest workers.** Possibly using `pytest-xdist` if compatible. First determine whether the dependency is already present; if not, evaluate the additional dependency and installation overhead before adopting it. Assess test distribution, collection overhead, process startup costs, fixture duplication, scheduling imbalance, peak memory, worker-specific temporary directories, coverage collection/combination, and handling of failures and worker termination. Note: two workers on one runner do not automatically mean twice the runner-minutes.
- **Configuration P2 — Separate GitHub Actions test jobs.** Only if justified. Take into account installation, checkout, redundant fixtures, artifact transfer, aggregation, and coordination. Runner-minutes are the sum of occupied job time; wall-clock is the critical chain, not that sum. Do not assume splitting tests across jobs reduces total CI resource consumption.

Define the decision criterion **before** evaluating final measurements: a repeatable reduction of the critical-path duration that is larger than the measured spread, with an explicit trade-off of extra runner-minutes, memory, complexity, and risk. Do not promise a percentage without a baseline. Do not introduce an arbitrary speedup threshold after seeing the results. A configuration that reduces wall-clock but substantially increases runner consumption or operational complexity requires an explicit trade-off assessment.

Preserve a simple serial fallback. Make experimental parallelism opt-in until the evidence is complete. Test both existing routes independently; keep exactly the selected test collection and checks.

Avoid premature optimization of individual tests. The first question is whether distributing the existing workload provides a measurable advantage.

## 8. Phase E — Prove fail-closed results and combined coverage

Create small, isolated infrastructure tests that actually provoke:

- A test failing on one worker/shard while the other succeeds; multiple simultaneous failures.
- Collection or setup error, worker crash, truncated output, and missing result file.
- A missing or duplicate shard and missing test nodeids; no silent gaps or double counting.
- A coverage-combination failure or missing coverage from a mandatory worker/shard.
- Concurrent publication output and mutating fixtures staying separated; real repository files unchanged.
- A canonical validation failure and a publication-integrity failure reaching the required check.
- Reporting remaining available and the final status remaining nonzero on errors, also with later `always()` steps. Verify that collecting results cannot conceal the original failure status.

Verify combined coverage of **the same modules and executable lines**, with consistent source paths. Averages of worker percentages are not combined coverage. Explain differences in covered lines and prove subprocesses are included where needed. Do not let an old coverage file influence new results. All expected coverage artifacts are generated, cannot overwrite one another, missing worker coverage is detected, and existing thresholds remain enforced.

If GitHub Actions uses an aggregation job, investigate how its status interacts with branch protection and required checks. Do not silently rename or remove required checks. If repository settings must change, document the required configuration and request Lucas's authorization first. Check the real workflow configuration; a standalone Python copy of the YAML logic is not regression proof for the workflow itself. With multiple jobs, `validate` must explicitly check all expected results; `skipped`, `cancelled`, a failed dependency, or a missing artifact must not aggregate as success.

Where useful, use controlled failure injection rather than naturally occurring errors. Do not introduce brittle tests depending on precise execution timing. Benchmarks demonstrate performance under specified conditions; correctness tests verify preserved behavior — do not conflate them.

## 9. Phase F — Measurement protocol and evidence

Use at least three comparable full runs **per measurement condition** for the final comparison. Local trials and GitHub Actions results remain separate; do not use local benchmark results as a substitute for CI measurements, and do not simulate CI measurements.

Record per run:

- Commit SHA, data/source/test revisions, and any local dirty status. Do not claim exact committed evidence from a modified checkout.
- Route, full command line, collected nodeids, executed tests, failures, errors, skips, and retries.
- Runner/image, Python, dependencies, cache conditions, workers/jobs, scheduler, and run id/attempt.
- Pytest wall-clock, total job duration excluding queue time, canonical/publication validation duration, setup/teardown, YAML loads, and builds where reliably measured.
- Runner-minutes and memory where measurable. For parallel processes, preferably measure concurrent total memory; do not sum separate process peaks as if they occurred simultaneously. Label the measurement method and its limitations. Write "not measured" where reliable measurement is missing.
- Timing, JUnit, coverage, worker, and summary artifacts, plus links to the CI runs.

Report median and spread (min/max, optionally another declared measure), not a selected best run. Keep failed experiments as diagnostics and report them; do not use them as a successful baseline and do not hide instability with retries.

Where test configuration changes require different commits, demonstrate and document that the relevant source, test data, and validation semantics remain equivalent. Record all deviations and qualify conclusions where exact equivalence is not established.

Distinguish two fundamentally different improvements: **reduced workload** (fewer checks/tests executed because the workflow selects a route — the #308 work) versus **faster execution** (the same workload in less elapsed time). Issue #309 concerns the second category. Do not attribute savings from previous test-selection optimizations to the parallelization experiment. Measurement instrumentation alone is not a performance improvement; if instrumentation is the primary deliverable, state explicitly that its benefit is improved visibility, not reduced runtime.

Fill the mandatory table with actual results or "Not yet measured". Provide separate comparisons per route and name the configurations explicitly:

| Metric | Serial | Parallel (configuration) | Difference |
|---|---|---|---|
| Total CI job duration, excluding queue time | | | |
| Pytest duration | | | |
| Canonical/publication validation | | | |
| Executed tests, failures, and skips | | | |
| Coverage of the same modules | | | |
| Runner-minutes / number of workers | | | |
| Memory and measurement method | | | |

If no parallel configuration is adopted, distinguish the experimental results from the final serial implementation. Do not present rejected experimental timings as the performance of the final solution.

## 10. Phase G — Decision, documentation, and delivery

Make one explicit, well-founded decision:

- **Outcome A — Retain serial execution** if the benefit is insufficient or not repeatable, overhead/memory is too high, isolation is insufficiently proven, or CI evidence is missing. Deliver only useful measurement/isolation improvements and a reproducible decision. Do not leave unused experimental production code in place.
- **Outcome B — Adopt two-worker pytest execution** only if comparable runs show meaningful wall-clock improvement, worker isolation is verified, coverage aggregation is correct, failure handling is fail-closed, resource consumption is acceptable, and the added dependency and maintenance burden are justified. Preserve a serial execution option.
- **Outcome C — Adopt separate CI test jobs** only if independent jobs demonstrably improve the overall workflow, runner costs are acceptable, test partitions are maintainable, required-check aggregation is reliable, and publication/validation semantics remain unchanged.
- **Outcome D — Insufficient evidence** if comparable measurements cannot be completed (runner availability, permissions, CI restrictions). Retain serial execution, deliver the completed investigation and instrumentation, state precisely which measurements are missing, and document the experiments needed. Do not claim a performance improvement.

**The preferred solution is the least complex configuration that provides a demonstrable, repeatable net benefit without weakening existing controls.** Do not leave temporary benchmark artifacts in the repository unless intentionally documented and useful. Do not leave experimental parallelization infrastructure in place merely because it was developed during the investigation.

Run the targeted infrastructure tests and then the relevant full routes with the correct Python version (the project requires at least 3.13). Verify the interpreter before testing; the existing `.venv` has previously been found to be Python 3.9. Do not upgrade a global environment unrequested. Report concrete limitations if the correct environment or CI execution is still missing.

Update `docs/workflows/ci-benchmark.md` and, where necessary, the scripts user manual with reproducible commands, isolation agreements, artifact structure, full results, and the decision. Describe only what has actually been demonstrated. Keep the broader end-measurement and maintenance wrap-up of #310 outside this step.

Finally deliver:

1. An overview of changed files with purpose and preserved checks.
2. Exact test/measurement commands, results, and limitations, split into local and CI.
3. The comparison tables, provenance, and artifact/run links.
4. The serial/parallel decision with risks, fallback, and justification.
5. A complete draft description for one **draft PR** to `main`, with `Closes #309` only when acceptance is actually met, and `Part of #304`. Name open actions explicitly where evidence is still missing.
6. Concrete follow-up steps Lucas must perform manually for commit/push, external measurement runs, and review. Publish or merge nothing on your own.

## 11. Draft PR description structure

Prepare the following Markdown structure:

- **Summary** — problem addressed and selected solution.
- **Baseline** — the optimized serial CI architecture and reference measurements.
- **Parallelization assessment** — temporary outputs and locks, shared fixtures, process overhead, memory, coverage aggregation, failure propagation, external side effects.
- **Experimental configurations** — serial, two-worker, and any evaluated multi-job configuration; explain any configurations excluded from benchmarking.
- **Measurement methodology** — workload equivalence, environment, cache conditions, measurement boundaries, repetition.
- **Before/after results** — the mandatory measurement table with evidence links; medians and spread across at least three comparable runs per configuration used in the final comparison.
- **Decision** — the selected outcome, supporting evidence, and why alternatives were rejected; say so explicitly if evidence is insufficient.
- **Preserved controls** — test selection, canonical validation, publication integrity, full relevant coverage, fail-closed aggregation, required-check failure reporting, manual full-suite execution, PR cancellation behavior.
- **Validation** — actual tests and checks executed, outcomes, remaining limitations.
- **Limitations and follow-up** — unresolved concerns, missing measurements, recommended future work.
- **References** — `Closes #309` only if fully resolved, epic `Part of #304`, preceding PRs/issues (#308, PR #314), baseline and final CI runs, measurement artifacts.

Do not claim completion when acceptance criteria have not been met.

## 12. Work sequence and checkpoints

Execute in this order, reporting at each checkpoint before continuing:

1. **Checkpoint 1 — Baseline and risk assessment.** Verified repository/branch state, existing CI architecture, existing measurement capabilities, potential parallelization hazards, proposed experiment configurations, and any prerequisites blocking safe execution. Do not change the CI execution strategy yet.
2. **Checkpoint 2 — Instrumentation and isolation.** Implement only the measurement infrastructure and isolation improvements necessary for reliable experiments. Run relevant correctness checks and explain the changes and their effect on reproducibility.
3. **Checkpoint 3 — Controlled experiments.** Evaluate the serial baseline and relevant parallel configurations. Local exploratory measurements where useful; GitHub Actions for CI performance conclusions. If an experiment requires Lucas to commit, push, or dispatch a workflow, provide the precise required action and continue once the resulting evidence is available. Do not simulate CI measurements.
4. **Checkpoint 4 — Decision.** Present the measurement results and a justified recommendation, the trade-offs, and an explicit statement whether the evidence supports adopting parallel execution.
5. **Checkpoint 5 — Final implementation.** Apply the selected configuration, remove experimental changes not part of the chosen solution, and run relevant regression and validation checks.
6. **Checkpoint 6 — Draft PR preparation.** Final implementation summary, measurement report, and draft PR description. Do not create the PR, commit, or push without Lucas's explicit authorization. The PR remains a draft until Lucas has reviewed the evidence.

If an unexpected architectural issue requires changes beyond the stated scope, document it and seek authorization before substantially expanding the implementation.

## 13. Final instruction

**Optimize for verified performance, correctness, and maintainability — not for introducing parallel execution.**

Successful completion of issue #309 may result in no change to the current serial CI strategy. An evidence-based decision to retain serial execution is a valid outcome. A parallel implementation without reliable comparative measurements is not.

Work through to locally permitted implementation, verification, and documentation being complete. Do not stop at a plan; present missing external authorization or missing CI evidence honestly, and do not speculatively switch the default route to parallel.
