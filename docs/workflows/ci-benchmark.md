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

## Resultaat en streefdoel

Het resultaat van #305 is inzicht, niet een geclaimde kortere CI-run. De definitieve
nulmeting, ranglijst en het onderbouwde epic-streefdoel worden na drie matching CI-runs
in de draft PR en dit document ingevuld. Voorlopig richt #306 zich op eliminatie van
herhaalde loads; hoeveel dat van de volledige jobtijd bespaart is nog niet gemeten.
#305 blijft open zolang de drie runs en hun analyse ontbreken. De draft PR benoemt
expliciet wat al is geïmplementeerd/getest en wat nog niet is gemeten.
