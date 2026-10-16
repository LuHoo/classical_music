Closes #309

## Changes
- Keeps normal PR validation serial pending GitHub evidence.
- Adds manual serial/two-worker benchmark selection.
- Makes worker metrics aggregation fail closed for malformed or incomplete evidence.
- Adds real-xdist coverage, failure-lifecycle, and worker-crash tests.
- Records sampled Linux process-tree RSS as lower-bound provenance.

## Validation
- 28 focused tests passed locally.
- Existing six-run local result remains historical only: median pytest reduction 30.7%.
- No GitHub Actions performance conclusion yet.

## Remaining Evidence
Run three comparable GitHub serial and two-worker dispatches on one commit, then compare job duration, pytest duration, runner-minutes, coverage, artifacts, and sampled RSS.

References: #309, #304.