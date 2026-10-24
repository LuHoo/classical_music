# Pending curator scenarios

`pending-choices.json` preserves reviewed pending inputs from the commit identified
by `source_commit`. It includes only the choices, candidate units, existing
Performances and report text used by the curator regression tests.

The session fixture in `tests/conftest.py` copies the current catalogue into a
pytest temporary directory and restores these scenarios there. Tests must not
assume that real curator issues remain unresolved in the production manifests.
The fixture never changes production data and requires no Git executable, old
commit availability or network access at test runtime.

The three curator test modules opt in through their module-scoped fixture.
Other tests continue to validate the actual current catalogue. The historical
resolved cases (#240 and #244) remain resolved to exercise refusal and retry rules.

Update these scenarios deliberately when changing the reviewed input contract,
not when recording ordinary curator decisions. Do not skip tests or weaken the
production check that rejects an already resolved choice.
