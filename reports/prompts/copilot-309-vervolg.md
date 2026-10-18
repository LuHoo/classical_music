# Expert Follow-up Prompt — Issue #309 / Draft PR #315
## Complete CI Benchmarking, Parallel Safety Verification, and Evidence-Based Decision

### 1. Role and objective

You are a senior Python engineer, CI/CD architect, and performance engineer working on the `LuHoo/classical_music` repository.

Your assignment is to address the outstanding review findings for:

- **Issue:** [#309](https://github.com/LuHoo/classical_music/issues/309)
- **Draft PR:** [#315](https://github.com/LuHoo/classical_music/pull/315)
- **Parent epic:** [#304](https://github.com/LuHoo/classical_music/issues/304)
- **Preceding issue:** [#308](https://github.com/LuHoo/classical_music/issues/308)

PR #315 introduces two-worker pytest execution using `pytest-xdist`, worker-specific measurement artifacts, and aggregation of worker metrics.

The implementation includes promising local performance measurements, but the review identified outstanding requirements that must be addressed before the PR can be merged.

**Your objective is to complete the existing implementation, verify its correctness, and establish whether parallel execution produces a meaningful improvement in GitHub Actions.**

Do not treat parallel execution as a predetermined outcome.

A decision to restore serial execution is acceptable if the CI measurements do not justify parallelization.

Do not create a new implementation from scratch. Work incrementally from the existing changes in PR #315.

---

## 2. Mandatory Git workflow constraints

Lucas retains responsibility for all Git operations.

Work exclusively in his existing local checkout, using the existing working branch associated with PR #315.

Before making any changes, inspect:

```bash
git status --short
git branch -vv
git rev-parse --abbrev-ref HEAD
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git log -1 --format='%H'
```

Verify that:

1. The active branch corresponds to PR #315.
2. The active branch is not `main`.
3. The branch has an appropriate upstream.
4. The checkout does not contain unrelated changes that would be overwritten.
5. PR #315 targets `main`.

If these conditions are not satisfied, stop and report the problem.

Do not automatically resolve Git-related problems.

**Git operations are Lucas's responsibility unless he explicitly authorizes a particular action.**

Specifically:

- Do not create or switch branches.
- Do not create worktrees or clones.
- Do not stage, commit, push, rebase, reset, or merge.
- Do not create another PR.
- Do not modify PR #315 through the GitHub API without authorization.
- Do not overwrite existing work.

Git commands suggested to Lucas must be compatible with Git 2.10.1.

Use `git checkout`, never `git switch` or `git restore`.

All changes must remain part of the existing PR #315.

---

## 3. Review findings to address

The review of PR #315 identified five concerns.

### Finding 1 — GitHub Actions performance is not yet established

The existing benchmark documentation reports three serial and three parallel runs on the same local revision:

`f4c769169a9465b164dd45f18a06403ca2a63163`

Results:

| Metric | Serial | Two workers |
|---|---:|---:|
| Number of runs | 3 | 3 |
| Median pytest duration | 2861.37 s | 1984.14 s |
| Minimum | 2844.43 s | 1826.93 s |
| Maximum | 2998.74 s | 2195.66 s |
| Tests collected | 527 | 527 |
| Coverage | 84.19% | 84.19% |

The observed median improvement is 877.23 seconds, approximately 30.7%.

These measurements were performed locally on macOS arm64 with Python 3.14.3.

The GitHub Actions workflow uses Ubuntu and Python 3.13.

Consequently, these results cannot establish the performance improvement of the GitHub-hosted workflow.

**Required action:** Perform a controlled GitHub Actions comparison before making the final decision.

### Finding 2 — Runner consumption and memory are insufficiently documented

The existing documentation does not establish:

- Complete GitHub CI job duration.
- Aggregate runner-minutes.
- Parallel execution overhead in GitHub Actions.
- Peak memory consumption.
- The effect of installation and workflow overhead on the actual improvement.

**Required action:** Extend the measurement report and instrumentation where necessary.

### Finding 3 — Worker artifact aggregation requires stronger completeness checks

The current `ParallelControllerMetrics` implementation verifies:

- The expected number of worker directories.
- The presence of worker artifacts.
- Readability of JSON records.
- Worker identity in session metadata.
- Duplicate `(nodeid, phase)` combinations.
- Agreement between the number of unique node IDs and collected tests.

However, these checks do not establish that every required test phase has been recorded.

For example, a test may have a recorded setup phase but lack a corresponding call or teardown phase.

The current implementation also does not comprehensively validate the contents and consistency of individual worker records.

**Required action:** Strengthen aggregation so incomplete, malformed, or inconsistent worker results cannot silently produce successful validation.

### Finding 4 — Coverage aggregation and failure propagation need end-to-end verification

The current regression tests cover selected aggregation scenarios using synthetic worker artifacts.

However, the review did not establish adequate end-to-end verification of:

- Actual two-worker pytest execution.
- Worker crashes.
- Missing or incomplete worker reports.
- Missing or incomplete coverage results.
- Correct propagation of failures to the final CI job.
- Preservation of required-check semantics.

**Required action:** Add targeted integration tests and controlled failure scenarios.

### Finding 5 — The decision between serial, two-worker, and separate-job execution needs stronger justification

PR #315 adopts two workers without a complete GitHub Actions comparison.

It also excludes separate test jobs without a sufficiently documented evaluation.

**Required action:** Complete the architectural assessment and make the final decision based on evidence.

---

# 4. Work package A — Strengthen worker-result aggregation

Inspect:

- `src/classical_music/pytest_metrics.py`
- `tests/test_ci_metrics.py`
- Existing CI reporting and summarization scripts.
- Relevant pytest and pytest-xdist hooks.

First establish the actual pytest lifecycle and distinguish:

1. Successful test execution.
2. Setup failures.
3. Call failures.
4. Teardown failures.
5. Skipped tests.
6. Expected failures.
7. Unexpected passes.
8. Worker crashes.
9. Interrupted or incomplete sessions.

Do not assume every test must have an identical sequence of setup, call, and teardown reports.

For example, a setup failure may prevent a call phase from occurring legitimately.

### Required validation

Improve aggregation to detect, where applicable:

- Missing worker artifacts.
- Missing expected workers.
- Unexpected worker identities.
- Missing session metadata.
- Malformed JSON.
- Malformed or inconsistent phase records.
- Duplicate phase records.
- Phase records attributed to the wrong worker.
- Missing required phase records.
- Inconsistent test collection counts.
- Invalid or inconsistent exit-status information.
- Worker processes that did not complete normally.
- Disagreement between worker metrics and the controller's observed execution.

Use pytest's actual reporting semantics to distinguish valid lifecycle exceptions from incomplete data.

Avoid rejecting legitimate skips, setup failures, or xfails merely because they do not follow the usual successful-test lifecycle.

### Fail-closed requirement

If required evidence is missing or inconsistent, the aggregate result must indicate failure.

The final pytest process must exit unsuccessfully.

The GitHub Actions required check must not report success.

Do not merely place an error message in a JSON file while returning a successful exit status.

Preserve useful diagnostic artifacts even when aggregation fails.

### Important limitation

Do not unnecessarily duplicate pytest-xdist's own process management or failure detection.

Identify which guarantees are already provided by pytest and pytest-xdist, and implement additional checks only where they are genuinely needed.

Prefer straightforward, maintainable validation logic.

---

# 5. Work package B — Verify actual parallel execution

Expand regression coverage beyond direct unit tests of the metrics controller.

Implement targeted integration tests that invoke pytest with two real workers.

Use small, isolated synthetic test suites.

These tests must:

- Execute quickly.
- Avoid production dataset processing.
- Avoid external network access.
- Use temporary directories.
- Avoid real publication or playlist mutations.
- Produce deterministic outcomes.
- Work reliably in CI.

### Required scenarios

Verify at least:

| Scenario | Expected outcome |
|---|---|
| Two workers complete successfully | Success; complete aggregated metrics |
| A test fails in worker 1 | Failed pytest process |
| A test fails in worker 2 | Failed pytest process |
| Failures occur in both workers | Failed pytest process; failures remain observable |
| A test fails during setup | Failed process; valid lifecycle reporting |
| A test fails during teardown | Failed process; valid lifecycle reporting |
| A test is skipped | Valid skipped result |
| A worker terminates unexpectedly | Failed process; incomplete execution recognized |
| Worker metrics are missing | Failed aggregation |
| Worker metrics contain duplicate records | Failed aggregation |
| Worker metrics are malformed | Failed aggregation |
| Worker phase data are incomplete | Failed aggregation |

Use controlled failure injection where practical.

For worker-crash tests, avoid unnecessarily terminating the overall test runner or creating nondeterministic failures.

Do not conceal intermittent failures through retries.

### Test isolation

Ensure the integration tests use isolated directories for:

- Generated test files.
- Worker metrics.
- JUnit files.
- Coverage data.
- Temporary output.
- Any simulated publication artifacts.

Where possible, verify that worker-specific output paths cannot overwrite each other.

Do not introduce unnecessary fixtures or configuration changes into the existing production test suite.

---

# 6. Work package C — Validate coverage aggregation

Inspect the existing configuration of:

- `pytest-cov`
- `coverage.py`
- `pytest-xdist`
- GitHub Actions artifact generation
- Coverage reporting

Determine which coverage aggregation guarantees are already supplied by the existing tools.

Avoid writing a separate coverage implementation if the standard tools already provide the required behavior.

### Required checks

Establish that:

1. All successfully executing workers contribute their coverage.
2. The final XML report contains combined coverage.
3. Coverage is not overwritten by another worker.
4. Equivalent tests produce equivalent module coverage.
5. A worker failure cannot silently produce an apparently complete passing check.
6. Missing or corrupt required coverage evidence cannot be mistaken for successful complete validation.
7. Existing coverage requirements are preserved.

Use a small synthetic test suite to verify aggregation across two workers.

Construct a case where different tests cover different code paths.

Demonstrate that the combined report contains coverage contributions from both workers.

Also test a controlled failure or missing-artifact scenario.

### Avoid redundant mechanisms

If pytest-cov already manages worker coverage correctly, retain that mechanism.

Additional code should focus on detecting missing or invalid evidence rather than reimplementing coverage combination.

Document any limitations of the standard tools.

---

# 7. Work package D — Establish reliable GitHub Actions benchmarks

This is a critical acceptance requirement.

The final recommendation must be supported by GitHub Actions measurements rather than extrapolation from local results.

## D1. Benchmark configurations

Compare:

**S — Serial execution**

The optimized serial configuration established before issue #309.

**P — Two-worker execution**

The current proposed configuration:

```bash
python -m pytest -p classical_music.pytest_metrics -n 2 --dist load
```

Both configurations must execute equivalent workloads.

### Comparability requirements

Use:

- Identical production source and test data.
- Identical test collection and selection.
- Identical canonical validation.
- Identical publication checks.
- Equivalent dependencies.
- The same runner type.
- The same Python version.
- Comparable cache conditions.
- The same measurement boundaries.

The only material experimental difference should be the execution configuration.

Do not compare historical data-only workflow results with current full-suite results.

Do not compare runs from different dataset revisions without establishing equivalence.

Do not infer performance improvement from reduced test selection.

### Workflow design

Determine the least intrusive way to support controlled serial and parallel benchmarks.

Prefer an explicitly selectable benchmark mode over repeated manual editing of the workflow.

However:

- Do not introduce unnecessary permanent CI complexity.
- Do not alter normal production validation semantics.
- Do not weaken required checks.
- Do not enable automatic parallel execution of external side effects.
- Do not create additional jobs unless justified.
- Do not modify branch protection settings.

If a temporary benchmark configuration is appropriate, document how it is enabled and how experimental changes will be removed afterward.

Do not require Lucas to create another working branch or PR.

## D2. Measurement repetition

Perform at least three comparable GitHub Actions runs for each configuration.

Prefer alternating configurations where practical to limit systematic effects from changing runner conditions.

For example:

S1 → P1 → S2 → P2 → S3 → P3

The exact order is less important than comparability and transparency.

Do not substitute repeated local runs for GitHub Actions evidence.

### Git responsibility

Lucas is responsible for committing and pushing changes.

If further measurements require a commit, push, workflow dispatch, or another GitHub action that you are not authorized to perform:

1. Explain the required action.
2. Provide the exact applicable commands or GitHub UI instructions.
3. Identify which measurements will become available.
4. Continue analyzing the available evidence.
5. Do not fabricate or anticipate results.

Do not claim to have executed GitHub Actions runs unless they actually exist.

## D3. Required measurements

For every benchmark run, record:

- Run ID and URL.
- Commit SHA.
- Dataset revision.
- Test-selection route.
- Runner operating system.
- Runner image details where available.
- Python version.
- Dependency versions.
- Cache conditions.
- Number of pytest workers.
- Collected tests.
- Passed, failed, and skipped tests.
- Coverage.
- Pytest duration.
- Canonical validation duration.
- Complete CI execution duration, excluding queue time.
- Runner-minutes.
- Peak memory where measurable.
- Relevant timing, JUnit, and coverage artifacts.

Clearly distinguish elapsed wall-clock time from aggregate runner consumption.

A single GitHub Actions runner executing two pytest workers does not automatically consume twice the runner-minutes.

For the current single-job architecture, runner-minutes are primarily determined by runner execution duration, subject to GitHub's billing rules.

Do not confuse pytest worker count with the number of GitHub-hosted runners.

### Memory measurement

Investigate whether peak memory can be measured reliably without substantial overhead.

Consider:

- Process-tree resource usage.
- Runner-level memory.
- Peak resident memory.
- Sampling limitations.
- Instrumentation overhead.

A process-level measurement that excludes worker subprocesses must not be presented as total pytest memory consumption.

If a reliable measurement is impractical, document that limitation explicitly.

Do not invent memory figures.

---

# 8. Work package E — Benchmark analysis

Once sufficient GitHub Actions evidence is available, calculate:

- Median serial duration.
- Median parallel duration.
- Absolute median difference.
- Relative median difference.
- Minimum and maximum.
- Observed spread.
- Runner-minute difference.
- Memory difference where available.

Use the same workload and equivalent controls.

Provide the following table:

| Metric | Serial | Two workers | Difference |
|---|---|---|---|
| Total CI execution, excluding queue | | | |
| Pytest duration | | | |
| Canonical/publication validation | | | |
| Collected/executed tests | | | |
| Failures and skips | | | |
| Coverage of equivalent modules | | | |
| Runner-minutes | | | |
| Number of runners | | | |
| Pytest workers | | | |
| Peak memory, where measurable | | | |

Report individual observations as well as medians and spread.

If evidence is unavailable, write:

**Not yet measured.**

Do not substitute estimates for observations.

### Performance interpretation

Consider the complete workflow, not merely the pytest step.

For example, reducing pytest execution by 30% does not necessarily reduce the entire CI job by 30%.

Account for:

- Dependency installation.
- Test collection.
- Canonical validation.
- Artifact uploads.
- Measurement overhead.
- Parallel process startup.
- Duplicated session fixtures.

Explicitly distinguish:

**Executing less work** from **executing equivalent work faster**.

Evaluate whether the observed improvement is meaningful relative to run-to-run variation and resource consumption.

Do not make artificial speedup claims.

---

# 9. Work package F — Evaluate separate test jobs

Issue #309 also requires consideration of distributing tests across separate GitHub Actions jobs.

This does not necessarily require implementing an additional multi-job workflow.

First perform an architectural assessment.

Evaluate:

1. Whether the current test suite contains naturally independent partitions.
2. Whether those partitions have significantly different execution costs.
3. Whether separate jobs could run concurrently without shared state.
4. Whether repeated runner initialization would eliminate the expected savings.
5. Whether dependency installation and environment setup would be duplicated.
6. Whether JUnit and coverage aggregation would become more complicated.
7. Whether required-check semantics would require modification.
8. Whether runner-minute consumption would increase.
9. Whether additional workflow complexity is justified.

Document the conclusions.

If there is no credible indication that separate jobs could outperform two-worker execution, explain why a full benchmark is not justified.

If a credible benefit remains, describe a minimal safe experiment.

Do not introduce separate permanent CI jobs without measured justification.

---

# 10. Work package G — Make the final decision

After the technical checks and benchmarks, select one outcome.

### Outcome A — Keep two pytest workers

Accept this outcome only if:

- GitHub Actions measurements establish a meaningful improvement.
- The result is not merely an artifact of reduced test selection.
- Runner consumption is acceptable.
- Worker isolation is verified.
- Aggregated coverage is correct.
- Failure handling is fail-closed.
- Required-check semantics are preserved.
- Operational complexity remains justified.

### Outcome B — Restore serial execution

Choose this if:

- GitHub CI improvement is negligible.
- Results remain inconclusive.
- Memory or runner consumption is disproportionate.
- Parallel execution creates unacceptable reliability risks.
- Coverage or result aggregation cannot be made trustworthy.

Keep useful measurement infrastructure.

Remove unnecessary permanent parallelization code and dependencies.

### Outcome C — Evidence remains incomplete

If required CI measurements cannot be obtained:

- Do not claim parallel execution is justified.
- Keep PR #315 in draft.
- Document exactly which evidence is missing.
- Prefer retaining the serial production configuration until the decision can be supported.

Do not equate promising local results with completed acceptance criteria.

---

# 11. Preserve existing CI guarantees

Throughout this work, preserve the functionality introduced in earlier CI optimization issues.

In particular:

- Existing data-only and full-validation routing.
- Full canonical validation.
- Publication-integrity checks.
- Manual full-suite execution.
- Existing coverage requirements.
- Reliable JUnit output.
- Fail-closed validation behavior.
- Accurate job summaries.
- PR-specific cancellation.
- Preservation of unrelated PR and `main` runs.
- No real network mutations in tests.

Do not weaken these guarantees to obtain faster execution.

Avoid changes to unrelated production functionality or datasets.

---

# 12. Required documentation changes

Update:

`docs/workflows/ci-benchmark.md`

The documentation must distinguish:

1. Existing local benchmark results.
2. New GitHub Actions benchmark results.
3. Instrumentation changes.
4. Worker-isolation measures.
5. Coverage verification.
6. Failure-propagation verification.
7. Separate-job assessment.
8. Final architectural decision.
9. Remaining limitations.

Retain the existing local measurements as historical evidence.

Do not replace them with CI results without identifying the different execution environments.

Include links to all relevant GitHub Actions runs and artifacts.

Document the exact revisions used.

If the final solution retains serial execution, explain why the local improvement was insufficient to justify parallel CI.

If two-worker execution is retained, explain why the measured GitHub CI benefit outweighs the additional complexity.

---

# 13. Execution sequence and checkpoints

Execute the work in the following sequence.

### Checkpoint 1 — Reassess the existing implementation

Inspect the current PR and relevant files.

Report briefly:

- Which review findings remain valid.
- Which concerns are already addressed by existing tools.
- Which additional tests or code changes are genuinely necessary.
- How CI benchmarks can be performed without violating the Git workflow.

Do not rewrite working components unnecessarily.

### Checkpoint 2 — Correctness and integration tests

Implement the necessary improvements to:

- Worker-result validation.
- Failure handling.
- Integration tests.
- Coverage verification.

Run the relevant local tests.

Report the commands used, actual results, and any unresolved failures.

### Checkpoint 3 — Benchmark preparation

Implement the smallest suitable mechanism for comparing serial and two-worker GitHub Actions execution.

Verify that the comparison is reproducible.

Explain what Lucas must do to make the benchmark available in GitHub Actions.

Stop at the boundary of unauthorized Git operations.

### Checkpoint 4 — CI measurements

Collect and analyze the real GitHub Actions runs when available.

Do not fabricate missing results.

If the required runs do not yet exist, produce the precise remaining benchmark procedure and clearly mark the comparison as incomplete.

### Checkpoint 5 — Final decision and implementation

Select serial or parallel execution based on the evidence.

Implement the justified configuration.

Remove unnecessary experimental infrastructure.

### Checkpoint 6 — Draft PR documentation

Prepare an updated, concise PR description containing:

- Problem.
- Changes.
- Preserved controls.
- Measurement methodology.
- Before/after results.
- Decision.
- Limitations.
- References to issue #309 and epic #304.

Do not mark PR #315 ready for review or merge it without Lucas's authorization.

---

# 14. Final deliverables

Your work must result in:

1. Stronger verification of worker-result completeness.
2. Targeted end-to-end tests for actual parallel execution.
3. Verified coverage combination and failure propagation.
4. A reproducible GitHub Actions benchmark procedure.
5. At least three comparable CI measurements per configuration, when access permits.
6. Reporting of CI wall-clock duration and runner consumption.
7. A documented assessment of memory consumption.
8. An evaluation of separate test jobs.
9. An evidence-based decision between serial and parallel execution.
10. Updated benchmark documentation.
11. A concise, accurate description for draft PR #315.

If external actions by Lucas remain necessary, distinguish completed implementation work from pending measurements.

Do not report the issue as fully completed until its acceptance criteria have been satisfied.

---

## 15. Important final instructions

This is a **follow-up review correction**, not a new development initiative.

Keep the scope tightly focused on the outstanding findings in PR #315.

Use the existing implementation wherever possible.

Do not add complexity merely to demonstrate technical sophistication.

In particular:

- Do not implement custom scheduling if pytest-xdist already handles it correctly.
- Do not reimplement coverage aggregation if pytest-cov already provides it.
- Do not duplicate GitHub Actions failure handling unnecessarily.
- Do not introduce persistent benchmarking infrastructure that is more expensive to maintain than the performance improvement it evaluates.
- Do not run the complete 45–50-minute test suite repeatedly merely to validate small changes to measurement code. Use focused tests first; reserve full-suite runs for the required performance comparisons.
- Do not perform unauthorized Git operations.
- Do not claim performance improvements without actual measurements.

**Successful completion is defined by verified correctness and an evidence-based decision, not by retaining parallelization.**

Begin with Checkpoint 1. Inspect the actual state of PR #315 and identify the smallest set of changes required to resolve the review findings.