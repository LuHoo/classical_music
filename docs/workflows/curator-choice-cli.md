# Curator choices from the command line

`./curator ISSUE CHOICE` saves a local decision immediately, with curator **LAH**.
Enter several decisions, then run `./curator finish` once:

```bash
./curator 246 C093
./curator 263 P078
./curator finish
```

Use your existing checkout and a workbranch created from updated main, with an
upstream. Git remains entirely manual. Review `git status`, `git diff` and new files
before adding, committing, pushing and reviewing your PR yourself.

## Parameters

- `--dry-run`: preview the proposed files without saving or running final validation.
- `--apply`: optional compatibility flag; applying is already the default.
- `--curator NAME`: override LAH for this decision or playlist confirmation.
- `--replace-existing`: explicitly allow replacing a registered recommendation;
  the original Performance is preserved in the decision record.
- `--decision-url URL`: cite an existing comment on this issue; its content is not fetched.
- `--playlist-remove-unselected`: record exact IDs for a manual TIDAL action.
- `ISSUE playlist-done --note TEXT`: record your confirmation of that action.
- `finish`: validate the accumulated decisions and publication, then run batch tests.

Example preview: `./curator 242 C035 --replace-existing --dry-run`.
Without `--dry-run`, this example saves the replacement immediately.

Registered C/P/unit codes, explicit A/B aliases and `existing` are supported.
An identical retry does nothing; a conflicting resolved choice is refused.
Historical source tracks and reviewed metadata remain preserved. The script makes
no Git, GitHub or TIDAL writes and does not deploy the generated site.

## Validation and recovery

Each entry checks choice validity, replacement safety and file consistency before
saving. Expensive intake audits, publication generation and regression tests run
only at `finish`. All registered intakes share one publication build. The targeted
suite is `tests/test_curator_batch.py`; pytest must be installed in the interpreter
used by the wrapper (`CURATOR_PYTHON`, local `.venv/bin/python`, or `python3`).

`reports/curator-decisions/batch-status.json` records pending, validated or failed
status. A new choice removes the old success stamp. After manual data/code changes,
run `finish` again. Existing decisions without a status report are also checked.
A failed finish preserves decisions and the previous publication. Fix the reported
error and rerun; only **Finish geslaagd** confirms completion.

Writes are serialized with `.curator.lock`, reject intervening changes and roll
back ordinary write errors. This is not a crash-proof database transaction. Review
files after a crash and only remove a stale lock once no curator writer is running.

Chamber and Piano support registered single-recommendation choices. Best Classical
requires reviewed registrations in its legacy windows; cross-window choices remain
unsupported. Contemporary, Opera and Lieder require additional registered adapters.
The historical full Best Classical import audit is distinct from current choice
validation; see the manual for its known legacy reference limitation.

See the [detailed User Manual](scripts-user-manual.md) for installation, all scripts,
parameters, manual playlist actions, recovery and collection registration.
The separate [listening-playlist workflow](curator-listening-playlists.md) retains
its own preview default and explicit external-write `--apply` flag.
