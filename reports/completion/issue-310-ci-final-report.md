# CI-eindrapport #310: bewijs, grenzen en onderhoud

Peildatum: 18 oktober 2026. Onderdeel van [#304](https://github.com/LuHoo/classical_music/issues/304).
**Status: gedeeltelijk uitgevoerd; acceptatie nog open.** Geen cumulatieve
snelheidsclaim en geen automatische sluiting van #310 of #304.

## Revisies en bronnen

- Werkbranch: `310-ci-optimalisatie-66-eindmeting-user-manual-en-onderhoudsafspraken`;
  onderzochte HEAD `f42ce3b53ee5d092dc3288f82864d1daa7ebeedf`, met correcte upstream.
- Lucas (`LuHoo`) mergede [#315](https://github.com/LuHoo/classical_music/pull/315)
  op 18 oktober als `caaa5ccc637c36748a481081604032ae648864fb`; die merge is voorouder
  van de werkbranch. Definitieve PR-head: `c8e3e2518d01e6c8a6a2c21f5674a33d07653ddf`.
- Data-tree voor alle hieronder gedownloade metingen:
  `615af8804456a950a478406d8e13564878ca6ee3`.
- Huidige source-tree `e6c07c13c7f331da155df75c790f6a2103edbade`, tests-tree
  `172bbfdb999ccaed0fd3c8a000ffa13bf26f5a3c`. #310 wijzigt geen productiecode of data.
- [Compacte artifactextractie](issue-310-ci-evidence.json) bevat individuele
  waarnemingen, omgeving/dependencies, exacte commando's, classificatie, effectieve
  exitstatus, JUnit, coverage-regel/hitdigest, installatiebewijs en SHA-256's.
  Bronbestanden staan lokaal onder `ci-baseline/issue310/RUN_ID/` (gitignored),
  inclusief ruwe `run-api.json`, `jobs-api.json` en genormaliseerde `run.json`.
  Alle gedownloade runs hebben attempt 1; de wachttijdreferentie is `run_started_at`.
  Runlinks hieronder verwijzen ook naar de originele artifacts.

## Vooraf vastgelegde meetgroepen

Vergelijk iedere conditie afzonderlijk met de ongewijzigde
`scripts/compare_ci_baseline.py`: minimaal drie succesvolle attempts met dezelfde
data/code/tests/repository-trees, commando, node-ID-uitkomsten, workers, runner-OS/
image/CPU, Python/dependencies en cacheconditie. Gewone dirty checkouts zijn verboden;
alleen de door #315 inhoudelijk geaudite installatie-uitzondering is toegestaan.
Veranderde code tussen baseline en eindgroep is juist onderwerp van onderzoek, maar
geen reden om verschillende condities binnen één comparatorgroep te mengen.

| Groep | Inhoud | Huidige bewijsstatus |
|---|---|---|
| B-full, vóór optimalisaties | #305-instrumentatie, volledige suite, 1 worker | Runs 203–205 beschikbaar, maar dirty zonder installatiebewijs en verschillende CPU's; afgewezen |
| B-curator, oud beleid | Dezelfde volledige suite bij curatorwijzigingen | Geen historische data-only-route; representatieve PR-evidence en geldige drie-runbaseline ontbreken |
| E-full | Definitieve #310-ref, volledige suite, standaard 2 workers | nog niet gemeten; finale #315-runs zijn correctheidsbewijs, geen #310-drie-runmeting |
| E-data-only | Legitieme data-only PR met volledige head/base-evidence en gerichte tests, 2 workers | nog niet gemeten; dispatch is altijd full |
| E-serial | Dezelfde eindref en full-selectie, expliciete seriële terugval | nog niet gemeten; afzonderlijke groep, niet met parallel poolen |

## Individuele CI-waarnemingen

Alle onderstaande runs zijn rechtstreeks uit artifacts en attemptmetadata gelezen.
Iedere run slaagt met nul JUnit-failures/errors/skips en coverage 985/1170 (84,19%).
Dit laatste is codedekking van validation/migration, geen percentage muziekdata.
Gelijke totalen zijn geen bewijs van gelijke tests of identieke bronregels tussen revisies.

| Run / artifactpagina | Commitgroep | CPU | Workers | Tests | Pytest (s) | validate-job (s) |
|---|---|---|---:|---:|---:|---:|
| [203](https://github.com/LuHoo/classical_music/actions/runs/38138286003) | `ea36428a` | 9V74 | 1 | 372 | 3302,32 | 3342 |
| [204](https://github.com/LuHoo/classical_music/actions/runs/38139221980) | `ea36428a` | 9V45 | 1 | 372 | 2372,87 | 2406 |
| [205](https://github.com/LuHoo/classical_music/actions/runs/38139224128) | `ea36428a` | 9V45 | 1 | 372 | 2510,97 | 2544 |
| [221](https://github.com/LuHoo/classical_music/actions/runs/38931354299) | `8a8574fa` | 7763 | 2 | 537 | 931,35 | 970 |
| [223](https://github.com/LuHoo/classical_music/actions/runs/38975140693) | `8a8574fa` | 7763 | 2 | 537 | 929,02 | 961 |
| [224](https://github.com/LuHoo/classical_music/actions/runs/39007085566) | `8a8574fa` | 7763 | 2 | 537 | 936,81 | 967 |
| [226](https://github.com/LuHoo/classical_music/actions/runs/39045057201) | `8a8574fa` | 7763 | 1 | 537 | 1243,93 | 1280 |
| [229](https://github.com/LuHoo/classical_music/actions/runs/39059827039) | `8a8574fa` | 7763 | 1 | 537 | 1261,00 | 1294 |
| [232](https://github.com/LuHoo/classical_music/actions/runs/39064939302) | `8a8574fa` | 7763 | 1 | 537 | 1243,61 | 1278 |
| [236](https://github.com/LuHoo/classical_music/actions/runs/39140756238) | finale PR | 9V74 | 2 | 554 | 707,81 | 734 |
| [237](https://github.com/LuHoo/classical_music/actions/runs/39144596359) | `caaa5ccc` | 7763 | 2 | 554 | 911,82 | 947 |

Oude volledige baselinecommit: `ea36428a46d61e6993cb8f043484e78200944220`,
source `91213e46b01483b002a52e368578790c7c19c673`, tests
`6ebc499acd76096813af56a6b02c31de0219b279`; Ubuntu-image `20261004.327.1`.
Historische #309-commit: `8a8574fab7cbe4b22953a3469a4c8eaea79cb595`.
Recente runs gebruiken image `20261012.334.1`. Python is 3.13.16; exacte packages
en platformstrings staan per run in de extractie. De validate-workflow gebruikt geen
dependencycache; vergelijk dat niet met de Bundler-cache van de aparte CI-workflow.

Run 236 heeft API-head `c8e3e251...`, maar artifact/GITHUB_SHA
`8c6a2bbbb2d01b5c49552cbd1f6e4c9f147f8645`: de synthetische PR-mergecheckout.
`classification.json` bindt de volledige diff aantoonbaar aan definitieve head
`c8e3e251...` en base `0055b686...`. Verwar head en geteste merge niet.
Run 237 test de echte main-merge. Beide hebben een geverifieerde installatie-audit,
554 tests en `complete: true`, maar verschillende CPU's en zijn geen homogene groep.

De oorspronkelijke 41/78-minutenruns en de overige #309-runs staan met hun
uitsluitingsredenen in [het benchmarkdocument](../../docs/workflows/ci-benchmark.md).
Run 234 faalde, 235 werd geannuleerd; die zijn geen succesvolle eindmetingen.
Historische 216 was geannuleerd en 217 gebruikte oudere code/527 tests. Geen trage
geldige waarneming is verwijderd op grond van zijn duur.

## Eindvergelijking per route

### Code/full

| Maatstaf | Voor | Na | Verschil |
|---|---|---|---|
| Totale CI-jobduur, exclusief wachtrij | nog niet gemeten als geldige drie-runbaseline | nog niet gemeten op de eindref | nog niet gemeten |
| Pytest-duur | nog niet gemeten als geldige drie-runbaseline | nog niet gemeten als eindgroep | nog niet gemeten |
| Canonieke/publicatievalidatie (onderscheiden) | nog niet gemeten als vergelijkbare groep | nog niet gemeten als vergelijkbare groep; publicatie zit deels in pytest | nog niet gemeten |
| Uitgevoerde tests, failures en skips | 372 / 0 / 0 per oude waarneming, geen aanvaarde groep | 554 / 0 / 0 in twee finale #315-runs, nog geen #310-groep | +182 tests; geen performanceconclusie |
| Dekking van dezelfde modules | 985/1170; bronrevisie verschilt | 985/1170; dezelfde modules, bronregelvergelijking vereist | geen gelijkheid afgeleid uit percentage |
| Runner-minuten / aantal workers | nog niet gemeten als geldige groep / 1 | nog niet gemeten als geldige groep / 2 | nog niet gemeten |

### Curator/data-only

| Maatstaf | Voor | Na | Verschil |
|---|---|---|---|
| Totale CI-jobduur, exclusief wachtrij | nog niet gemeten voor representatieve curatorgroep; oud beleid was full | nog niet gemeten | nog niet gemeten |
| Pytest-duur | nog niet gemeten als geldige groep | nog niet gemeten | nog niet gemeten |
| Canonieke/publicatievalidatie (onderscheiden) | nog niet gemeten als geldige groep | nog niet gemeten; canonieke pass plus publicatie/cross-intake in pytest vereist | nog niet gemeten |
| Uitgevoerde tests, failures en skips | Volledige suite onder oud beleid; geen bewezen historische data-only-route | nog niet gemeten met actuele classificatie en JUnit | nog niet gemeten |
| Dekking van dezelfde modules | nog niet gemeten als vergelijkbare groep | nog niet gemeten | nog niet gemeten |
| Runner-minuten / aantal workers | nog niet gemeten als groep / 1 | nog niet gemeten als groep / 2 | nog niet gemeten |

## Bijdrage per stap

| Stap | Bijdrage en behouden controle | Bewijs en beperking |
|---|---|---|
| [#305 / #311](https://github.com/LuHoo/classical_music/pull/311) | Timings, fasen, YAML/buildtellers, JUnit, coverage en artifacts | Inzicht, geen optimalisatiewinst. Baseline 203–205 beschikbaar maar strikt afgewezen; geen bewezen vooraf vastgesteld numeriek doel |
| [#306 / #312](https://github.com/LuHoo/classical_music/pull/312) | Eén onveranderlijke raw snapshot per operatie; nieuwe operatie leest actuele data | Lokaal n=3: validatie 49,16 naar 10,55 s, validate+build 62,73 naar 11,66 s; minder herhaald parserwerk, geen CI-eindvergelijking |
| [#307 / #313](https://github.com/LuHoo/classical_music/pull/313) | Read-only sessiefixtures en tijdelijke publicatie-uitvoer; muterende curatorcataloguskopieën blijven | Lokale voor/na-waarneming 3084,95 naar 2609,31 s, loads 779266 naar 294267, tests 398 naar 402; geen homogene CI-drie-runvergelijking |
| [#308 / #314](https://github.com/LuHoo/classical_music/pull/314) | Eén canonieke pass, fail-safe revisiegebonden routing, eerlijk gepland/uitgevoerd, unieke non-PR-concurrency | Minder geselecteerde softwaretests; lokaal 517 full / 250 data-only zonder bewezen pytesttijdwinst. Actuele data-only-CI-groep en live concurrencyproef ontbreken |
| [#309 / #315](https://github.com/LuHoo/classical_music/pull/315) | Twee workers op één runner, gescheiden artifacts, fail-closed fasen/coverage en installatie-audit | Historische 7763-groep: jobmediaan 1280 naar 965 s, -24,6%; pytest 1243,93 naar 932,93 s. Beperkte installatieprovenance; standaard twee workers blijft behouden |
| Cumulatief #304 | Alle controles behouden, minder herhaling/selectie plus parallel uitvoeren | nog niet gemeten met geldige baseline- en eindgroepen voor beide routes; percentages uit lokale/CI-stappen worden niet opgeteld |

De volledige historische #309-groep heeft n=3 serieel en n=5 parallel, jobspreiding
1278–1294 versus 961–970 s; runner-minuten 21,33 versus 16,08 op één runner.
Gesamplede RSS +23,1% is geen runnerbreed piekgeheugen en kan gedeelde pagina's
dubbeltellen. De zes hier opnieuw gedownloade 7763-runs zijn een controleerbare
deelverzameling, niet een vervanging of selectieve herberekening van die vijf-runrapportage.
De ongewijzigde comparator weigert ook deze historische dirty #309-artifacts zonder
installatie-audit; zij zijn geen strikte #310-baseline. De lokale 30,7%-pilot is apart.

## Bottlenecks en doelbeoordeling

De artifactextractie bevat de traagste modules op basis van gesommeerde fasetijd.
Curatorintegratie, cataloguskopieën en volledige keuze-/publicatiecontroles blijven
de dominante paden. Bij paralleliteit is gesommeerde fasetijd geen job-walltime.
Duplicatie van sessiefixtures verhoogt YAML-loads; workerstart/IPC hebben geen aparte
timing. Publicatievalidatie binnen pytest overlapt met pytestduur en wordt niet
nogmaals bij de jobduur opgeteld. Runner-minuten zijn jobseconden/60, geen factuur.

Het epic en #305 verlangen een na de nulmeting vastgelegd doel; in de onderzochte
issuebeschrijvingen, #305-comments en benchmarkdocument is geen concreet numeriek
streefdoel aangetroffen. **Doel gehaald: niet beoordeelbaar.** Lucas moet vóór nieuwe
eindmetingen een doel met meetgrenzen en referentiegroep vastleggen; geen achteraf
gekozen grens presenteren als oorspronkelijk afgesproken doel.

## Verificatie en open acties

De finale #315-code heeft groene [validate 236](https://github.com/LuHoo/classical_music/actions/runs/39140756238)
en [main 237](https://github.com/LuHoo/classical_music/actions/runs/39144596359).
De afzonderlijke [sitebouw op finale PR-head](https://github.com/LuHoo/classical_music/actions/runs/39140756229)
en [sitebouw op main-merge](https://github.com/LuHoo/classical_music/actions/runs/39144596365)
zijn groen. Dit is geen eindverificatie van nog niet gepushte #310-documentatie.

Lokale correctheidsverificatie op de #310-werkboom is voltooid met Python 3.14.3
op macOS, basiscommit `f42ce3b53ee5d092dc3288f82864d1daa7ebeedf` plus de
ongecommitte documentatiewijzigingen. Uitvoer: `ci-baseline/issue310/local-Ni22s1/`.

| Controle | Werkelijk resultaat |
|---|---|
| Canonieke validator, `validate_data.py --json-output` via `measure_ci.py` | Exit 0, 0 fouten, 115 waarschuwingen, 55,23 s |
| Volledige pytest-suite met meetplugin, `-n 2 --dist load --durations=30`, JUnit en coverage-XML | 554 passed; JUnit 554 tests, 0 failures/errors/skips; exit 0 |
| Pytestcommandoduur / pytest-eigen rapport | 2113,39 s / 2110,88 s; lokale correctheidsrun, geen CI-benchmark |
| Worker-evidence | `gw0`, `gw1`, `complete: true`, geen aggregatiefouten |
| Coverage validation/migration | 985/1170 (84,19%) |
| Publicatiebuilds / YAML-loads | 32 / 330224 |
| Lokale documentatiecontrole | Bestandslinks, JSON, Liquid-markeringen en `git diff --check` gecontroleerd |
| Lokale Jekyll-bouw | Niet uitgevoerd: `bundle check` faalt omdat Bundler 2.5.9 ontbreekt; geen globale installatie/upgrade uitgevoerd |

De canonieke waarschuwingen zijn niet als fouten of als genegeerde failures
voorgesteld. De volledige suite oefent de actuele publicatie- en isolatiecontroles
uit, maar vervangt geen echte Jekyll-build van deze documentatie. Nieuwe
GitHub-eindmetingen en de sitecheck op de uiteindelijke #310-ref blijven nodig.

Branch-API op 18 oktober: `protected: true`. Het protection-endpoint retourneert
met de huidige toegang 404 en repository-rulesets `[]`. Welke statuschecks technisch
worden afgedwongen is daarmee niet vastgesteld; de oude claim 'geen bescherming'
wordt niet overgenomen. Lucas controleert dit zelf in Settings, zonder automatische wijzigingen.

Nog vereist voor voltooiing, door Lucas te organiseren:

1. Leg eerst het streefdoel en de baseline-reproductie vast. De huidige comparator
   mag geen oude dirty runs goedkeuren zonder oorspronkelijk installatiebewijs.
   Een nieuwe baseline-meetref moet oude productiesemantiek/testselectie behouden,
   met uitsluitend noodzakelijke geaudite meetinstrumentatie. Dit vereist Lucas'
   expliciete Git-/meetbesluit, niet een terugdraaiing van #315 op de #310-branch.
2. Commit/push zelf #310 en publiceer de draft PR tegen main. Bewaar de exacte SHA.
   Draai op die vaste ref minimaal drie full-runs met `force_full=true`,
   `pytest_mode=parallel`; groepeer achteraf op vooraf bepaalde omgevingscriteria,
   nooit op snelheid. Verzamel aanvullende runs als CPU/image/dependencies verschillen.
3. Organiseer een echte, inhoudelijk legitieme data-only PR en minimaal drie passende
   succesvolle attempts; geen muziekdata aanpassen alleen om een route te triggeren.
   Bewaar `classification.json`, verwachte/waargenomen head/base én werkelijke JUnit/
   pytestselectie. De normale documentatie-PR en elke dispatch blijven full.
4. Verzamel de oude full-beleidsgroep voor representatief curatorwerk en code/full,
   plus afzonderlijk een eindgroep voor `pytest_mode=serial` indien de terugval
   kwantitatief wordt vergeleken. Download per attempt de artifacts en API-metadata.
5. Laat de huidige volledige suite, canonieke/publicatiecontroles en de afzonderlijke
   Pages-`build` op dezelfde eindversie slagen. Start zelf **Build and Deploy Jekyll
   site to GitHub Pages** op dezelfde ref; `CI / build` alleen is onvoldoende.
6. Vergelijk iedere homogene groep afzonderlijk, vul beide eindtabellen met
   mediaan [min–max], n en links, en beoordeel het vooraf vastgelegde doel. Lucas
   reviewt/merget en handelt open afwijkingen af vóór hij #304 eventueel sluit.

Het [bestaande User Manual](../../docs/workflows/scripts-user-manual.md) beschrijft
deze bediening, garantiegrenzen, foutdiagnose en onderhoudsverantwoordelijkheid.