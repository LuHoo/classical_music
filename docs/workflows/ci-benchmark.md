# CI-nulmeting — issue #305

Deze stap voegt metingen toe; hij claimt geen versnelling. De volledige pytest-suite,
standaard coverage-instellingen en beide canonieke validatorpasses blijven behouden.
De JSON-validator verbergt een fout niet meer achter `|| true`; artifacts blijven
beschikbaar via `if: always()`. Stap #308 behandelt pas het samenvoegen van validatorpasses.

## Wat wordt gemeten?

De workflow gebruikt `scripts/measure_ci.py` rond beide validatorpasses en pytest.
Elk commando krijgt een log en JSON met wall-clockduur, exitstatus, UTC-start/einde,
commandoregel, commit/tree-IDs, dirty-status, Python, OS/CPU, dependencyversies en
CI-runidentiteit. Alleen geselecteerde niet-geheime omgevingsvelden worden opgeslagen.
Environment-verzameling valt buiten de gemeten commandoduur; GitHub-jobduur bevat
wel deze overhead, installatie en artifactverwerking. Er is geen dependencycache.

Pytest gebruikt in CI expliciet twee workers met `--dist load`. De optionele plugin
`classical_music.pytest_metrics` levert:

- `test-phases.jsonl`: na iedere afgeronde setup/call/teardown een regel met node-ID,
  duur, uitkomst, xfail en YAML-load/publicatiebuildtellers;
- `test-session.json`: collected count, exitstatus en totaaltellers; bij xdist een
  fail-closed samenvoeging van alle workerprocessen;
- `junit.xml`, `coverage.xml` en de gebruikelijke terminalcoverage;
- `--durations=30` plus jobsummary met aparte top-30 voor setup, call en teardown.

Tellers zijn aanroepen (ook mislukte), geen unieke bestanden of bewezen geldige
publicaties. Ze tellen alleen het huidige proces; child-processen en gemockte/
vervangen methoden zijn niet volledig zichtbaar. Sessietotalen omvatten ook
collectie; fasetotalen beginnen bij de test. De plugin verandert geen testselectie,
parserinstellingen of validatieregels. Elke worker schrijft naar een eigen map; de
controller controleert volledigheid, dubbele fasen en verzamelde node-ID's voordat
hij de root-artifacts schrijft.

`ci-metrics-RUN_ID-ATTEMPT` bevat alle bestanden. Na een gewone testfout blijven
JUnit en fasegegevens bruikbaar. Na een harde kill kunnen alleen reeds geschreven
fasen/logs beschikbaar zijn; ontbrekende sessies worden als onvolledig gemeld.
Artifacts zijn niet gegarandeerd bij runnerverlies of vóór checkout/setup-falen.

## Historische aanwijzingen, geen gepoolde baseline

| Maatstaf | Run 37835735444 | Run #200 / 37849333733 |
|---|---:|---:|
| Commit | 95fa0743ac0bd98eb15e746fdd42bb6faf831889 | a827bfb4f42958ebcdba310c2ab9e7f5c3b860e3 |
| Totale validate-job | 2467 s | 4770 s |
| Pytest-stap | 2441 s | 4725 s |
| Pytest eigen rapport | 2436,27 s | 4721,85 s |
| Canonieke validator, iedere pass | 6 s | 12 s |
| Dependency-installatie | 8 s | 12 s |
| Tests | 364 passed | 364 passed |
| Coverage, validation + migration | 84% | 84% |
| Runner-minuten (jobduur / 60, geen tarieffactor) | 41,12 | 79,50 |

Bronnen: [run 37835735444](https://github.com/LuHoo/classical_music/actions/runs/37835735444)
en [run #200](https://github.com/LuHoo/classical_music/actions/runs/37849333733).

De commits hebben volgens `git diff` identieke repository-inhoud. Beide logs noemen
runner-image ubuntu-24.04 versie 20261004.327.1, provisioner 20261002.596 en dezelfde
geïnstalleerde dependencyversies, waaronder pytest 8.4.2, coverage 7.16.2 en
ruamel.yaml 0.19.1. Beide runs gebruikten Python 3.13.16. De beschikbare gegevens
verklaren het tijdverschil niet. Hostbelasting/hardware blijft een hypothese; ook
de losse validator werd ongeveer tweemaal zo traag. De oude logs hebben geen
per-testtimings of CPU-model en er zijn geen drie voldoende onderbouwde metingen
voor de nieuwe meetketen. Hieruit wordt daarom geen mediaan of einddoelbereik verzonnen.

De lokale audit van 8 oktober (Python 3.9, macOS) telde voor één publicatievalidatie
39.612 loads over 10.044 catalogusbestanden. Experimentele, tijdelijke memoization
bracht 55,73 s terug naar 27,31 s met gelijk rapport. Dat is bewijs voor een kans in
#306, geen GitHub-snelheidsmeting en geen geïmplementeerde optimalisatie.

## Reproduceerbare baseline op GitHub

1. Commit/push deze stap handmatig op de issuebranch en maak één draft PR tegen main.
   De bestaande pull_request-trigger draait de volledige suite met meetinstrumentatie.
2. Gebruik vervolgens dezelfde PR-run/revisie voor twee extra volledige reruns. Geen
   nieuwe commits, gewijzigde dataset, workerinstellingen of package-upgrades tussen
   metingen. Bestaande runs mogen alleen meetellen als dezelfde bewijsvelden bestaan.
3. Bewaar elke run-attempt afzonderlijk. Download na voltooiing de artifact en de
   bijbehorende jobmetadata, bijvoorbeeld (vervang ID, ATTEMPT en DIRECTORY):

```bash
gh run download ID --repo LuHoo/classical_music --name ci-metrics-ID-ATTEMPT --dir DIRECTORY
gh api repos/LuHoo/classical_music/actions/runs/ID/attempts/ATTEMPT > DIRECTORY/run-api.json
gh api repos/LuHoo/classical_music/actions/runs/ID/attempts/ATTEMPT/jobs > DIRECTORY/jobs-api.json
```

Maak `DIRECTORY/run.json` met `createdAt` uit `run-api.json.created_at` en `jobs`
uit `jobs-api.json.jobs`, met per job `name`, `conclusion`, `startedAt` uit
`started_at` en `completedAt` uit `completed_at`. Bewaar de originele API-bestanden
als bron. Bij reruns is created_at die van de oorspronkelijke run; gebruik daarom
`run_started_at` uit de betreffende attempt als startreferentie en noteer dat de
resulterende wachttijd alleen de vertraging vanaf attempt-start tot job-start meet.
Voor de eerste attempt kan `created_at` als referentie voor volledige scheduling-
vertraging worden gebruikt. Gebruik één consistente definitie in de vergelijking.

4. Vergelijk drie complete artifactmappen:

```bash
python scripts/compare_ci_baseline.py DIRECTORY1 DIRECTORY2 DIRECTORY3 > baseline.json
```

De vergelijking weigert minder dan drie runs, dubbele run-attempts, dirty-checkouts,
falende runs en verschillen in data/code/tests/tree, omgeving, dependencies,
commandoregel, testselectie of uitkomsten. Bij afwijkende runner-images/CPU’s of
versies: apart rapporteren en nieuwe vergelijkbare metingen verzamelen, niet poolen.
Het resultaat toont mediaan/minimum/maximum voor pytest, jobduur, scheduling-
vertraging en runner-minuten. Runner-minuten zijn de som van jobduren, geen factuur.

## Beperkte lokale diagnose

Voer vanuit de bestaande checkout uit, met de projectomgeving:

```bash
CI_METRICS_DIR=ci-metrics .venv/bin/python scripts/measure_ci.py --label pytest -- \
  .venv/bin/python -m pytest tests/test_publication_validator.py tests/test_publication_site.py \
  -p classical_music.pytest_metrics --durations=30 --junitxml=ci-metrics/junit.xml
.venv/bin/python scripts/summarize_ci_metrics.py ci-metrics
```

Deze subset is een profiel van representatieve paden, geen full-suitebaseline.
Controleer de duurste fase vóór zwaarder profileren. Gebruik timing en tellers om
#306 en #307 af te bakenen; verander in #305 geen testgaranties of productiealgoritmen.
De nieuwe failure/skip/collection-tests verifiëren de meetketen met kleine fixtures.

## Catalog snapshot benchmark — issue #306

`scripts/benchmark_catalog_snapshot.py` measures the catalog-loading paths that
issue #306 changed. It is a measurement harness: it temporarily wraps
`ruamel.yaml.YAML.load`, `PublicationDataAdapter.load_canonical_data` and
`CatalogSnapshot.load` to count invocations and accumulate parse time, and it
restores them afterwards. It does not alter production behaviour and it writes
the generated site to a temporary directory.

Run it from the existing checkout, with the project environment:

```bash
.venv/bin/python scripts/benchmark_catalog_snapshot.py --runs 3 \
  --output ci-metrics/snapshot-benchmark.json
```

Three scenarios are measured, each repeated `--runs` times:

- `validate` — `PublicationValidator(repo).validate()`;
- `build` — `PublicationSiteGenerator(repo, tmp).generate(validate=False)`;
- `validate+build` — `PublicationSiteGenerator(repo, tmp).generate(validate=True)`.

The report records, per scenario, the number of `YAML.load` calls, the number of
distinct files parsed, the number of catalog loads and snapshot loads, and the
median, minimum and maximum of parse time, wall-clock time and CPU time. The
environment block captures the Python version, platform, commit, branch, the
`data` tree ID and whether the working tree was dirty. Compare only reports whose
environment and `data` tree ID match; wall-clock and CPU time are reported
separately and must not be presented interchangeably.

To compare a baseline with a change, run the command on the unmodified revision
first, keep the JSON report, then run it again after the change.

Publication equivalence is verified separately by hashing every generated file
and comparing the resulting tree digest between the two revisions, and by
comparing the full `ValidationResult` error and warning lists.

### Local observations, 2026-10-11

Python 3.14.3, macOS arm64, `data` tree of commit `ea36428a`, three runs per
scenario, medians:

| Scenario | YAML loads | Distinct files | Parse (s) | Wall (s) | CPU (s) |
|---|---:|---:|---:|---:|---:|
| `validate` before | 39,612 | 10,044 | 27.56 | 49.16 | 31.86 |
| `validate` after | 10,044 | 10,044 | 5.54 | 10.55 | 6.53 |
| `validate+build` before | 49,657 | 10,045 | 34.63 | 62.73 | 40.39 |
| `validate+build` after | 10,045 | 10,045 | 5.83 | 11.66 | 7.43 |
| `build` before | 10,045 | 10,045 | 5.26 | 10.81 | 6.77 |
| `build` after | 10,045 | 10,045 | 5.60 | 11.97 | 7.20 |

The gain comes from removing repeated parser invocations, not from faster
parsing: the publication validator parsed the work-group, work and performance
directories three times each on top of the adapter's own load. A build without
validation parses the same number of files as before and is slightly slower,
because the snapshot additionally freezes the parsed documents.

These are local measurements. They say nothing about GitHub Actions duration;
CI figures must be collected from an actual workflow run as described above.

## Resultaat en streefdoel

Het resultaat van #305 is inzicht, niet een geclaimde kortere CI-run. De definitieve
nulmeting, ranglijst en het onderbouwde epic-streefdoel worden na drie matching CI-runs
in de draft PR en dit document ingevuld. Voorlopig richt #306 zich op eliminatie van
herhaalde loads; hoeveel dat van de volledige jobtijd bespaart is nog niet gemeten.
#305 blijft open zolang de drie runs en hun analyse ontbreken. De draft PR benoemt
expliciet wat al is geïmplementeerd/getest en wat nog niet is gemeten.

## Twee-worker pilot en besluit — issue #309

Dezelfde revision `f4c769169a9465b164dd45f18a06403ca2a63163` is lokaal zes keer
volledig gemeten: drie seriële runs en drie runs met `-n 2 --dist load`. De omgeving
was Python 3.14.3 op macOS arm64; xdist was alleen voor deze metingen aan de lokale
developmentomgeving toegevoegd. De workflow bleef ongewijzigd totdat deze vergelijking
was afgerond.

| Conditie | Runs (s) | Mediaan | Min–max |
|---|---:|---:|---:|
| Serieel | 2998.74, 2861.37, 2844.43 | 2861.37 s (47:41) | 2844.43–2998.74 s |
| Twee workers | 1826.93, 2195.66, 1984.14 | 1984.14 s (33:04) | 1826.93–2195.66 s |

De mediane winst is 877.23 seconden, oftewel 30.7%. Alle zes runs verzamelden 527
tests, slaagden volledig en bouwden 32 publicaties. Elke coverage-XML rapporteerde
985 van 1170 regels (84.19%). De worker-variant rapporteerde meer YAML-loads
(320180 tegenover 294267), omdat sessiefixtures per proces worden opgebouwd; dat
extra werk verhinderde de gemeten winst niet. Peak memory is niet gemeten.

Besluit: CI gebruikt voortaan twee expliciete xdist-workers. `-n auto` en opgesplitste
jobs zijn niet ingevoerd: de twee-worker run behoudt één check, één JUnit/coverage-
rapport en fail-closed worker-metrics, terwijl de metingen een reproduceerbare
medianewinst boven de lokale spreiding laten zien. GitHub-hosted CI-tijden moeten
nog met dezelfde drie-runmethode op de workflow worden verzameld; de lokale cijfers
zijn geen gesimuleerde CI-metingen.

## Deterministic fixtures and shared real-catalog reads — issue #307

Issue #307 reduces redundant full-catalog work *inside the test suite*, reusing the
shared snapshot from #306 rather than introducing a second measurement mechanism.

### What was duplicated

Before #307, several test modules independently parsed the complete real catalog,
each with its own `PublicationDataAdapter`, `PublicationValidator`, `EntityMatcher`
or manual YAML glob:

- `tests/test_publication_adapter.py` built a fresh adapter per test method (18 full
  loads for one module);
- `tests/test_publication_validator.py::TestPublicationWithRealData` (3 loads);
- `tests/test_chamber_import.py` and `tests/test_piano_import.py` each loaded the
  catalog in a module-scoped fixture with a hand-written YAML loader (2 loads);
- `tests/migration/test_entity_matcher.py` and `test_migrate_failclosed.py`
  constructed a new `EntityMatcher` per test (46 loads);
- `tests/test_original_arrangement_decisions.py` loaded the catalog and additionally
  called `PublicationSiteGenerator(ROOT).generate()` with the **default output
  directory**, writing ~3,678 generated pages directly into the checkout at
  `<repo>/publication/` and deleting whatever was there before (masked only because
  `/publication/` is gitignored).

### What changed

`tests/conftest.py` adds three session-scoped fixtures built on top of #306:

- `catalog_snapshot` — one `CatalogSnapshot.load(repository_root)` per test session;
- `canonical_matcher` — one `EntityMatcher` over the real `data/` directory;
- `canonical_records` — the snapshot's records thawed into ordinary, per-test-safe
  mutable dicts (`thaw()`), because frozen snapshot records reject both mutation
  and `deepcopy`.

Every test above now receives the adapter/validator/matcher/record set through
these fixtures instead of constructing its own. The assertions, inputs and
guarantees are unchanged; only the repeated parsing was removed. This is *doing
less work*, not *doing the same work faster*: the snapshot's parser, loader
configuration and record contents are identical to what each test built itself.

`test_original_arrangement_decisions.py` now passes an explicit `tmp_path`
output directory to `PublicationSiteGenerator`, so a run never writes into the
checkout. `tests/test_suite_isolation.py` adds an explicit regression test for
this: it records a hash of the real `data/`, `reports/`, `docs/`,
`side materials/` and `_data_generated/` trees before and after a full
publication build, and fails if anything in the checkout changed.

### What was deliberately not changed

`tests/test_curator.py` and `tests/test_curator_collections.py` still construct a
function-scoped `shutil.copytree` of the real `data/`, `reports/playlist-import/`,
`reports/curator-decisions/`, `docs/` and `side materials/` trees per test, because
each test calls `curator.execute()`/`curator.plan_decision()`, which mutates its
copy and revalidates it end to end (including a full publication build through
`chamber_import.audit`/`check_inventory`). These assertions are collection-wide
(no leaked pending choice, no competing recommendation, decision-vs-recommendation
equality across the *entire* performance set) and a reduced synthetic manifest
would weaken exactly the guarantees #307 must preserve. These tests remain the
Chamber, Piano and Best Classical full-catalog end-to-end controls. Converting
the copy to hardlinks was considered and rejected: any test that wrote through a
hardlink in place (rather than via `os.replace`) could silently corrupt the real
checkout, which is an unacceptable risk for a timing optimization.

### Measurement: before/after, same commit, same dataset

Both runs used commit `5e2591a8` (`data` tree `615af880`, clean working tree),
Python 3.14.3, macOS arm64, 10 CPUs, the full command used in `validate.yml`:

```bash
CI_METRICS_DIR=ci-metrics .venv/bin/python scripts/measure_ci.py --label pytest -- \
  .venv/bin/python -m pytest -p classical_music.pytest_metrics --durations=30 \
  --junitxml=ci-metrics/junit.xml --cov-report=xml:ci-metrics/coverage.xml
```

| Metric | Before | After | Difference |
|---|---:|---:|---:|
| YAML parser calls (session total) | 779,266 | 294,267 | −62% |
| Full-catalog loads in read-only modules (adapter/validator/chamber/piano/matcher) | ~24 | 2 shared + 2 per-build | −83% |
| Tests collected/passed | 398 / 398 | 402 / 402 | +4 (new isolation tests) |
| Failures / skips | 0 / 0 | 0 / 0 | none |
| Pytest duration | 3084.95 s | 2609.31 s | −15% |
| Coverage, `validation` + `migration` | 895/1080 = 82.87% | 895/1080 = 82.87% | 0 (identical lines) |

The remaining ~2,497 s is dominated by `tests/test_curator.py` (893 s) and
`tests/test_curator_collections.py` (1,403 s), which is filesystem copy and
decision-validation cost, not redundant YAML parsing — the deliberately retained
full-catalog controls described above. The 2 remaining per-build full parses are
`PublicationSiteGenerator.generate()`'s own internal `CatalogSnapshot.load()`,
scoped to one build by #306's design; sharing that internal snapshot across tests
would require widening `PublicationSiteGenerator`'s public API beyond this issue's
scope, for a saving of one parse (~6 s).

Order independence was checked by running the affected modules standalone, in
reversed module order, and inside the full suite; all three produce the same
pass count. `pytest-randomly` was not added: the repository has no existing
dependency for randomized ordering, and the manual checks above establish the
same guarantee for the changed modules without a new dependency.

### GitHub CI measurements

Not yet measured. CI figures must come from an actual GitHub Actions run after
Lucas pushes this branch; see "Reproduceerbare baseline op GitHub" above for the
three-run comparison protocol. Local before/after figures in this section are not
substitutes for CI wall-clock numbers.

## Validation routing policy — issue #308

Issue #308 reduces unnecessary full-suite runs by classifying a pull request's
changed files and selecting a narrower pytest scope for curator/data-only
changes. It reuses the #305–#307 infrastructure unchanged; it does not
introduce a second measurement system. A PR #314 review identified five
correctness gaps in the first implementation; this section documents the
fixed design. The gaps and fixes are listed explicitly in "Review fixes"
below.

### Why

Before #308, `validate.yml` ran `scripts/validate_data.py` **twice** per job —
once for console output, once with `--json` — each a fresh, independent full
catalog parse, and always ran the complete pytest suite regardless of what
changed. A pure curator-decision change (a new performance, a resolved
recommendation choice) paid the same cost as a code change.

### Classification

`src/classical_music/ci_policy.py` classifies every changed file using a
fixed allowlist of prefixes and extensions:

| Prefix | Allowed extensions |
|---|---|
| `data/` | `.yaml` |
| `reports/playlist-import/` | `.json`, `.md` |
| `reports/curator-decisions/` | `.json` |

A change set is **data-only** only when every changed path (both sides of a
rename or copy) is a structurally valid, non-empty, repository-relative path
on the allowlist, the change-status list is complete and every status is
recognized, and at least one file changed. A record with a missing, empty, or
whitespace-only path, or a `renamed`/`copied` record missing its previous
path, is treated as incomplete evidence — not silently ignored. Anything else
— unknown paths, mixed changes, unrecognized git statuses, an empty or
incomplete diff, or an explicit `force_full` request — selects **full**.
`docs/`, `side materials/` and `generated/legacy/` are deliberately **not**
allowlisted even though they are not Python: they are prose/reference
material, but excluding them costs nothing and keeps the allowlist minimal
and auditable.

### Fetching the changed-file list, with proof of completeness

Changed files for a pull request are fetched via
`GET /repos/{owner}/{repo}/pulls/{number}/files` (`scripts/classify_pr_changes.py`,
using the `gh` CLI already available on GitHub-hosted runners), not a local
`git diff`. This avoids every shallow-checkout and multi-commit edge case
entirely: GitHub itself computes the add/remove/modify/rename/copy status and
the correct base/head diff for the PR, independent of how many commits or
force-pushes it contains.

GitHub's documentation for this endpoint states: "Responses include a maximum
of 3000 files." A page shorter than the requested `per_page` is the usual
pagination-termination signal, but it does **not** by itself prove the
fetched list is the complete diff — a flaky response, a silently truncated
page, or exceeding the 3000-file cap could all look identical to a normal
last page. `_fetch_pr_evidence()` therefore proves completeness independently:

1. Fetch the PR resource (`GET /pulls/{number}`) and read its `changed_files`
   count. A missing or non-integer count is treated as unreliable.
2. If `changed_files` exceeds 3000, the files-list endpoint can never return
   the complete diff; classification selects `full` without even attempting
   to paginate.
3. Paginate the files endpoint, accumulating entries until a short page.
4. Reject duplicate filenames across pages (a sign of unreliable pagination).
5. Require the number of **fetched** entries to exactly equal the
   **reported** `changed_files` count. Any mismatch — including the
   previously-accepted "30 full pages then an empty page" case where the
   metadata under- or over-reports the true count — selects `full`.

Any failure to retrieve or verify this list (network error, rate limit,
malformed response, missing PR number, an unprovable count) degrades to
**full** and never raises — classification failure is not a workflow failure,
because full validation is always sufficient on its own.

### Binding classification to this run's revisions

The files-list endpoint is keyed on the **PR number**, which always reflects
the PR's *current* state — not necessarily the revision this particular
workflow run is validating. A re-run of an older run reuses its original,
now-stale, triggering event; a push arriving mid-pagination could change the
diff out from under the fetch. Neither case is detectable from the PR number
alone.

`classify_pr_changes.py` is given this run's expected revisions explicitly,
from the triggering event context —
`github.event.pull_request.head.sha` and `github.event.pull_request.base.sha`
— **not** `github.sha`, which for `pull_request` events is the synthetic
merge commit `actions/checkout` checks out, not the PR's actual head commit.

Before paginating, the fetched PR metadata's `head.sha`/`base.sha` must match
the expected values exactly; after paginating, the PR is re-fetched and its
`head.sha`/`base.sha`/`changed_files` must still match both the expected
values and the pre-pagination reading. Any mismatch at either point — wrong
revision, a revision that changed between pages, or a missing expected
revision entirely — selects `full` without reporting a false `data-only`.
Both the expected and observed revisions are recorded in the classification
JSON's `evidence` block for auditability.

### Routes

Both routes always run, in one job, unconditionally:

1. One canonical `DataValidator` execution (`scripts/validate_data.py --json-output ...`),
   producing console, JSON and job-summary output from a single `ValidationReport`.
2. The curator/data regression test subset described below, which is where
   publication validation (`PublicationValidator`) and cross-intake checks
   are actually exercised — **not** the validator step: `DataValidator.run()`
   does not invoke `PublicationValidator`.

Only the **pytest scope** differs:

- **data-only** — `classical_music.ci_policy.CURATOR_REGRESSION_TESTS`: a
  fixed list of test files covering the #307 guarantee matrix (chamber/piano/
  best-classical ingestion, curator decision/rollback/lock semantics, source
  preservation, the shared catalog snapshot and its consumers, parser and
  entity-matcher identity resolution, fail-closed migration gates, and
  canonical validation rules). `tests/test_ci_policy.py::TestPytestTargets::test_curator_regression_tests_are_real_files`
  fails the suite if this list ever drifts from the actual files on disk.
- **full** — pytest's configured default discovery (`testpaths = tests/` in
  `pyproject.toml`), i.e. the complete suite.

Because the curator regression subset is a strict subset of the full suite,
the data-only route never skips a canonical or publication control; it only
narrows which additional software tests run. Cross-intake references remain
checked on every PR regardless of route, because the chamber/piano/best-
classical regression tests load and assert against the complete real catalog.

### Not part of this job

`.github/workflows/pages.yml` already builds the actual Jekyll site and runs
`scripts/check_publication_links.py` unconditionally on every PR, with no
path filter, as a separate required check (`build`, workflow "Build and
Deploy Jekyll site to GitHub Pages"). This is the "actual publication
workflow" the epic requires; it is an independent check, and its result is
never folded into `validate`'s own summary.

### Required status check

Empirically confirmed via `gh pr view <number> --json statusCheckRollup`: the
check name is `validate` (job id in `validate.yml`), workflow "Validate
Canonical Data". No GitHub branch-protection rule or ruleset is currently
configured on this repository (`gh api repos/.../branches/main/protection`
returns 404; `gh api repos/.../rulesets` returns `[]`) — "required" is
currently Lucas's own manual practice, not a technical GitHub enforcement. The
job id and workflow name are unchanged by #308.

`validate.yml` remains a **single job**. Classification only changes which
pytest paths one unconditional `pytest` step receives; it is never split into
a job that a dependent job could skip or misinterpret as success. This
avoids the entire class of risk in multi-job `needs:`/`if: always()`
aggregation, by construction: there is no dependency to skip.

### Concurrency

{% raw %}
```yaml
concurrency:
  group: >-
    ${{ github.event.pull_request.number
        && format('validate-pr-{0}', github.event.pull_request.number)
        || format('validate-run-{0}-{1}', github.run_id, github.run_attempt) }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```
{% endraw %}

For `pull_request` events the group key is the PR number, stable across every
commit pushed to that PR, so a new push cancels that PR's own superseded run.
Different PRs have different numbers and never share a group.

For `push`/`workflow_dispatch`, the group key is `run_id`/`run_attempt`, which
GitHub guarantees is unique to that run attempt — no two runs (of any event
type) ever share that group. This matters independently of
`cancel-in-progress: false`: GitHub's queueing behaviour can replace a
*pending* run sharing a group even when the *running* one is protected from
cancellation, so `cancel-in-progress` alone does not establish the "never
cancels an unrelated run" guarantee for non-PR events — giving every non-PR
run its own, never-shared group does. `classical_music.ci_policy.concurrency_group`
mirrors this expression for a static, testable proxy
(`tests/test_ci_policy.py::TestConcurrencyGroup`); it is not proof of GitHub's
actual scheduling behaviour. That requires a real Actions run with at least
two pushes to the same PR, two different PRs running concurrently, and three
overlapping non-PR runs on the same ref — not yet performed; see "Remaining
CI verification."

### Manual full validation

`workflow_dispatch` accepts a `force_full` boolean input. When true, the
classifier returns `full` unconditionally without even attempting to read the
change set. Push and manual runs already default to `full` regardless of this
flag; the input exists to let Lucas force the full route when re-running a
dispatch is otherwise unnecessary (e.g. re-validating after an unrelated
infrastructure change).

### Curator `finish` — a documented, not expanded, scope

`classical_music.curator_batch.finish()` already provides a coherent,
offline check of source data, decision records, canonical consistency and
publication consistency for a batch of local curator decisions: it stages a
full temporary copy, checks canonical IDs for collisions, builds the
publication site once (which runs `PublicationValidator`), and runs every
registered intake's audit (chamber/piano/best-classical) against that build.
It intentionally runs only `tests/test_curator_batch.py` as its regression
check — a deliberate, pre-existing design choice to keep `finish` fast and
offline, documented at `curator_batch.TESTS`. Issue #308 is a CI-workflow
change; it does not expand `finish`'s test selection, since that is local
tooling behaviour Lucas already chose deliberately, not part of the GitHub
Actions pipeline. This is recorded here as an explicit, deliberate scope
boundary, not an oversight.

### Reporting: selected route vs. actual execution

The job summary has two, deliberately separate, sections:

- **Validation policy** (`scripts/summarize_classification.py`), rendered
  right after classification, before the validator or pytest steps run. It
  describes only what is *planned* — the selected route, reason, changed
  files, and which controls will be selected — using "will run"/"selected"
  language, never "ran" or "passed".
- **Execution summary** (`scripts/summarize_execution.py`), rendered with
  `if: always()` at the very end, after the validator and pytest steps. It
  reports each step's real outcome (`success`/`failure`/`cancelled`/`skipped`/
  unknown) from `steps.<id>.outcome`, plus real counts parsed from
  `validation-report.json` and `junit.xml` when those steps actually
  succeeded or failed. A validator failure followed by a skipped pytest step
  is reported as exactly that — skipped, not executed — never as if the full
  suite had run. A missing artifact is reported as "not treated as success",
  never inferred as success.

This directly fixes a defect in the first implementation: the policy summary
used to run with `if: always()` *before* the pytest step and claimed "the
full relevant software regression suite ran" / "only the selected pytest
targets were narrowed" regardless of whether pytest had actually executed —
including after a validator failure that caused pytest to be skipped
entirely.

### Testing

`tests/test_ci_policy.py` (54 tests) covers the full scenario table from
issue #308 (allowlisted add/modify/delete/rename, cross-boundary renames,
code/schema/dependency/workflow changes, mixed changes, unknown paths, new
directories, empty/incomplete/missing diffs, unknown git status, and forced
full validation), incomplete/invalid file records (empty/null/whitespace
paths, renames/copies missing a previous path, absolute paths, `..`
segments), and the concurrency-group invariant — purely against pure
functions, with no GitHub Actions dependency.

`tests/test_classify_pr_changes.py` (36 tests) covers the script layer:
event-type branching, completeness proof (exact page-size boundaries, the
3000-file cap, duplicate filenames across pages, count mismatches, missing/
invalid `changed_files` metadata), revision binding (matching/mismatched
head/base, revision drift during pagination, missing expected revisions, a
stale re-run after the PR moved), `gh api` failure modes (non-zero exit,
malformed JSON, unexpected shape, timeout), pagination, rename reporting, and
that `main()` never raises and always exits 0.

`tests/test_summarize_classification_and_execution.py` (19 tests) and
`tests/test_validate_data.py` (6 tests) cover the reporting split: the policy
summary never claims execution; the execution summary correctly distinguishes
success/failure/skipped/cancelled/unknown and never infers success from a
missing artifact; `validate_data.py --json-output` preserves the JSON report
and nonzero exit code on a validation failure, and the pre-existing `--json`
flag stays compatible.

These are local unit tests; GitHub's actual required-check behaviour (branch
protection interaction, concurrency cancellation in practice) still requires
verification in a real Actions run — see "Remaining CI verification" in the
PR description.

