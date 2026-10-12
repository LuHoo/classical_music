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

Pytest blijft serieel. De optionele plugin `classical_music.pytest_metrics` levert:

- `test-phases.jsonl`: na iedere afgeronde setup/call/teardown een regel met node-ID,
  duur, uitkomst, xfail en YAML-load/publicatiebuildtellers;
- `test-session.json`: collected count, exitstatus en totaaltellers;
- `junit.xml`, `coverage.xml` en de gebruikelijke terminalcoverage;
- `--durations=30` plus jobsummary met aparte top-30 voor setup, call en teardown.

Tellers zijn aanroepen (ook mislukte), geen unieke bestanden of bewezen geldige
publicaties. Ze tellen alleen het huidige proces; child-processen en gemockte/
vervangen methoden zijn niet volledig zichtbaar. Sessietotalen omvatten ook
collectie; fasetotalen beginnen bij de test. De plugin verandert geen testselectie,
parserinstellingen of validatieregels. Hij weigert parallelle uitvoering totdat
issue #309 een correcte aggregatie heeft uitgewerkt.

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
