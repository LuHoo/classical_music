# Expertprompt voor Copilot — issue #310: eindmeting, User Manual en onderhoudsafspraken

Je bent senior Python-, test- en GitHub Actions-engineer in VS Code. Voer issue #310 van `LuHoo/classical_music` uit: maak een controleerbare eindvergelijking van de CI-optimalisaties, werk het bestaande gebruikershandboek bij en leg onderhoudsafspraken vast. Lever concrete rapporten, documentatie en alleen rechtstreeks noodzakelijke meettooling/tests. Deze prompt bevat de noodzakelijke projectgeschiedenis; veronderstel geen eerdere chatcontext.

## 1. Opdracht en harde startvoorwaarden

- Issue: https://github.com/LuHoo/classical_music/issues/310
- Epic: https://github.com/LuHoo/classical_music/issues/304
- Voorgaande stap: https://github.com/LuHoo/classical_music/issues/309 — PR https://github.com/LuHoo/classical_music/pull/315
- Bestaande lokale checkout van Lucas: `/Users/Lucas_new/Documents/6. Mental/6.3 classical_music (git)`.
- Voorbereide branch: `310-ci-optimalisatie-66-eindmeting-user-manual-en-onderhoudsafspraken`, met gelijknamige upstream bij `origin`.

**Momentopname 18 oktober 2026:** #305–#308 en PR's #311–#314 zijn afgerond/gemerged. #309 en PR #315 zijn nog open. Lucas wacht op een groene CI-pipeline en merget #315 zelf. De voorbereide #310-branch stond bij inspectie op `0055b686f23b11c48db94dc2c15102fd54d9520d` (merge #314), dus bevatte #315 nog niet. Dit is een voorbereidingsprompt, geen toestemming om de afhankelijkheid over te slaan.

Voordat je implementatiebestanden wijzigt:

1. Lees toepasselijke `AGENTS.md` en eventuele Copilot-instructies. Inspecteer checkout, branch, upstream en bestaande wijzigingen met uitsluitend leesacties, bijvoorbeeld:

   ```bash
   git --version
   git rev-parse --show-toplevel
   git status --short --branch
   git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
   git log -5 --oneline
   ```

2. Verifieer dat #315 door Lucas is gemerged, dat de groene checks betrekking hebben op de definitieve PR-revisie en dat de #310-werkbranch de gemergede wijzigingen vanaf bijgewerkte `main` bevat. Alleen een gesloten issue, een groene oudere run of een synthetische PR-merge-SHA bewijst dat niet. Als GitHub niet bereikbaar is: vraag Lucas om het concrete mergebewijs en de relevante rungegevens; verzin geen status.
3. Ontbreekt de juiste basis, branch of upstream, stop vóór wijzigingen en laat Lucas dat zelf herstellen. De hierboven genoemde branch kan inmiddels zijn bijgewerkt; controleer de actuele toestand. Geen gestapelde branch boven op de open #315.
4. Behoud al het bestaande werk en lokale benchmarkbestanden. Controleer branch/upstream opnieuw na iedere door Lucas uitgevoerde branchwissel.

**Al het Git-beheer blijft bij Lucas.** Voer geen fetch, pull, checkout, reset, add, commit, push, merge, rebase, stash, clean of andere muterende Git-opdracht uit. Geen worktrees, clones, losse implementatiekopieën, detached HEAD of werk rechtstreeks op `main`. Geef indien nodig alleen instructies voor Lucas. Zijn Git is 2.10.1: gebruik `git checkout`/`git checkout -b` en bij een nieuwe branch `git push -u origin <branch>` vóór implementatie; adviseer geen `git switch` of `git restore`. Laat hem nooit onveilig over onafgerond werk heen wisselen.

Lucas maakt/publiceert ook de draft PR en start de benodigde externe runs zelf. Maak geen PR, comments, reviews, workflow-dispatches, reruns, issuewijzigingen of merges zonder afzonderlijke expliciete opdracht. Bereid wel alle teksten en exact benodigde handelingen voor. Geen automatische sluiting van #304.

## 2. Project en bestaande controles

Dit is een Python-project voor canonieke klassieke-muziekdata, curatorbeslissingen en publicatie via Jekyll. Python vereist minimaal 3.13; CI gebruikt 3.13. Gebruik de bestaande projectomgeving en dependencyversies; geen globale upgrades. Muzikale beslissingen, gebruikersdata, bronplaylists en TIDAL-acties vallen buiten deze opdracht.

Lees vóór het plan minimaal:

- `docs/workflows/ci-benchmark.md`: meetprotocol, beperkingen, resultaten per eerdere stap en het besluit over parallelisatie.
- `docs/workflows/scripts-user-manual.md`: **het bestaande User Manual**, met volledig handmatige Git-workflow. Maak geen tweede handboek.
- `.github/workflows/validate.yml`, `.github/workflows/pages.yml`, `.github/workflows/ci.yml`, `pyproject.toml`.
- `scripts/measure_ci.py`, `scripts/compare_ci_baseline.py`, `scripts/summarize_ci_metrics.py`, `src/classical_music/pytest_metrics.py` en na #315 `scripts/installation_provenance.py`.
- `src/classical_music/ci_policy.py`, `scripts/classify_pr_changes.py`, `scripts/summarize_classification.py`, `scripts/summarize_execution.py`, `scripts/validate_data.py`.
- `src/classical_music/curator_batch.py`, de relevante publicatie-/catalogussnapshotcode, `tests/conftest.py`, de bijbehorende garantie- en regressietests.
- `reports/prompts/copilot-pr314-review-fixes.md` als historische uitleg van vijf opgeloste correctheidsproblemen; implementeer deze reparaties niet opnieuw.

Behoud deze taakverdeling:

| Moment/route | Wat werkelijk wordt gecontroleerd |
|---|---|
| Individuele curatorbeslissing | Geldige keuze, vervangingsbevoegdheid, bronconflicten, veilig schrijven; geen zware eindcontrole per keuze |
| `./curator finish` | Gezamenlijke actuele bron-/beslisrecord-/canonieke/publicatiecontrole voor geregistreerde intakes, één gedeelde publicatiebouw en gerichte `tests/test_curator_batch.py`; geen volledige softwaretestsuite of gedeployde Jekyll-sitecontrole |
| Data-only PR | Eén actuele canonieke `DataValidator`-run plus `CURATOR_REGRESSION_TESTS`; publicatievalidatie en cross-intakegaranties zitten in pytest |
| Code/schema/dependencies/workflow of onbekend/gemengd | Volledige pytest-suite, plus dezelfde canonieke en publicatiegaranties |
| Publicatieketen | Afzonderlijke `build`-job in `pages.yml`: echte publicatiegeneratie, Jekyll-bouw, aanwezigheid van publicatie-index en `check_publication_links.py` |

`DataValidator.run()` roept **niet** `PublicationValidator` aan. Schrijf dus niet dat één canonieke validatorpass alle publicatiecontroles uitvoert. Een groene `validate` bewijst niet dat de afzonderlijke sitebouw groen is. Een gekozen route is een plan; alleen stapuitkomsten en artifacts bewijzen uitvoering. Een overgeslagen, geannuleerde of onbekende stap is geen succes.

Data-only is uitsluitend toegestaan bij een volledige, revisiegebonden diff met erkende statussen en uitsluitend toegestane paden: `data/*.yaml` ook in submappen, `reports/playlist-import/` met `.json`/`.md`, `reports/curator-decisions/` met `.json`. Controleer beide zijden van renames/copies. Onzekerheid, lege/onvolledige diff, onbekende paden of gemengde wijzigingen geven `full`. Push en handmatige dispatch gebruiken altijd `full`, ook zonder `force_full=true`. Documentatie-only is dus niet automatisch data-only.

Behoud `validate` als stabiele checknaam, nonzero-foutstatus, altijd beschikbare diagnostiek waar uitvoerbaar, en annulering uitsluitend van achterhaalde runs van dezelfde PR. Geen workflow-pathfilters, zwakkere tests, validatiecache voor gewijzigde data of soepelere comparator om betere cijfers te krijgen. De eerdere documentatie meldde geen technisch ingestelde branch protection; verifieer de actuele situatie en verwar een projectafspraak niet met GitHub-handhaving.

## 3. Voorgeschiedenis en betrouwbaarheid van bewijs

| Stap | Issue/PR | Vastgestelde bijdrage en beperking |
|---|---|---|
| Nulmeting | #305 / #311 | Timings, JUnit, coverage, fasegegevens, YAML-/buildtellers en artifacts. Meetinfrastructuur geeft inzicht, niet vanzelf snelheidswinst. De documentatie bevat nog open punten voor een strikte drie-runbaseline en een onderbouwd streefdoel, ondanks sluiting van #305. |
| Catalogussnapshot | #306 / #312 | Eén onveranderlijke raw snapshot binnen een validatie/bouw, behoud van paden/diagnostiek; nieuwe runs lezen actuele data. Lokale medianen: validatie 49,16 → 10,55 s, YAML-loads 39.612 → 10.044; validatie+bouwen 62,73 → 11,66 s. Geen GitHub-eindmeting. |
| Fixtures en isolatie | #307 / #313 | Gedeelde read-only catalogusfixtures en publicatie-uitvoer naar tijdelijke mappen. Lokale pytest 3084,95 → 2609,31 s, loads 779.266 → 294.267, tests 398 → 402. Curatorintegratietests behouden volledige tijdelijke cataloguskopieën: garanties mochten niet verdwijnen. |
| Routering | #308 / #314 | Eén canonieke pass, veilige testselectie en gescheiden geplande/werkelijke samenvatting. Vijf reviewfixes: volledigheid, head/base-binding, onvolledige records, unieke non-PR-concurrency en eerlijke uitvoeringrapportage. Na fixes lokaal 517 full / 250 data-only; eerdere PR-tekst noemt nog 453. Lokale routevergelijking gaf ongeveer géén pytesttijdwinst ondanks minder tests. CI-vergelijking en echt concurrencygedrag waren nog niet bewezen. |
| Parallelisatie | #309 / #315 | Twee workers met worker-eigen artifacts, fail-closed levenscyclus-/coveragecontrole, installatie-audit en gesamplede RSS. Lees de uiteindelijke gemergede versie en nieuwe groene run; historisch bewijs geldt niet automatisch voor latere reviewfixes. |

Referenties: [#311](https://github.com/LuHoo/classical_music/pull/311), [#312](https://github.com/LuHoo/classical_music/pull/312), [#313](https://github.com/LuHoo/classical_music/pull/313), [#314](https://github.com/LuHoo/classical_music/pull/314), [reviewcorrectie #314](https://github.com/LuHoo/classical_music/pull/314#issuecomment-6166151015), [#315](https://github.com/LuHoo/classical_music/pull/315).

Merge-SHA's voor herleidbaarheid: #311 `ea36428a46d61e6993cb8f043484e78200944220`; #312 `5e2591a8a5d2e81a29bdc097c20059f55881ad99`; #313 `43a2d64c74f5791d5f1256004de5b907a03bc952`; #314 `0055b686f23b11c48db94dc2c15102fd54d9520d`. Het oorspronkelijke instrumentatie-head van #311 is `64af1154b9599cd455205335a7a3cd4f5bb2c839`. Controleer welke daadwerkelijk gemeten revisie bij een artifact hoort; merge en head zijn niet uitwisselbaar.

### Belangrijke correctie bij #315

Op onderzochte head `adf15a3f1041e005a6734882611739cd9e223544` zegt de PR-beschrijving nog dat de standaard serieel blijft. Het benchmarkdocument bevat echter het **bijgestelde besluit van 18 oktober: twee workers standaard voor PR, main en handmatige runs**, met `pytest_mode=serial` als handmatige terugval. De workflowcode bevestigt die nieuwe standaard. Neem de verouderde PR-beschrijving niet over en draai het nieuwe besluit niet stilzwijgend terug. Controleer bij start het definitieve mergebesluit en signaleer resterende inconsistenties.

Historische #309-CI-groep: commit `8a8574fab7cbe4b22953a3469a4c8eaea79cb595`, data-tree `615af8804456a950a478406d8e13564878ca6ee3`, AMD EPYC 7763, vier zichtbare CPU's, Python 3.13.16, Ubuntu-image `20261012.334.1`, gelijke dependencies, geen dependencycache.

- Serieel runs 226/229/232: pytestmediaan 1243,93 s [1243,61–1261,00], job 1280 s [1278–1294].
- Parallel runs 221/223/224/225/227: pytestmediaan 932,93 s [929,02–936,81], job 965 s [961–970].
- Beide 537 tests, 0 failures/skips, coverage 985/1170; job/runner-minuten circa −24,6%, gesamplede procesboom-RSS circa +23,1%. Twee workers delen één runner: minuten niet maal twee rekenen.
- De historische artifacts bevatten dirty egg-info zonder inhoudelijk installatiebewijs. De strikte comparator weigert die terecht. Het is handmatig beoordeeld bewijs met beperking, geen strikte baseline voor #310. Nieuwe runs moeten de installatie-audit bevatten. Alleen de exact gecontroleerde installatie-uitzondering mag worden geaccepteerd.
- Andere CPU-modellen niet poolen; de lokale 30,7%-pilot niet als CI-resultaat gebruiken. RSS is gesampled en kan gedeelde pagina's dubbeltellen; geen runnerbreed piekgeheugen.

De oorspronkelijke 41- en 78-minutenruns zijn historische aanwijzingen, geen drie-runbaseline: [37835735444](https://github.com/LuHoo/classical_music/actions/runs/37835735444) en [37849333733](https://github.com/LuHoo/classical_music/actions/runs/37849333733). Verklaar het verschil niet zonder bewijs als hardware- of code-effect. 84% coverage betekent codedekking, geen percentage gecontroleerde muziekdata.

## 4. Uitvoering: inventariseren, meten en rapporteren

### A. Bewijsinventaris en meetplan

Inventariseer bestaande runlinks, attempts, artifacts, revisies, lokale rapporten, resultaten en gaten per stap. Noteer wat rechtstreeks uit artifacts/API komt en wat alleen in een eerder verslag staat. Ontbrekende of verlopen artifacts blijven ontbrekend; reconstrueer geen ruwe meetwaarden uit afgeronde percentages. Lees broncode/argumentparsers vóór scriptgebruik: sommige projectscripts voeren hun taak ook met `--help` uit.

Leg vooraf meetgroepen en vergelijkingscriteria vast. Verzamel voor **baseline én eindversie per relevante route minimaal drie vergelijkbare succesvolle CI-runs**: curator/data-only en code/full. De oude baseline draaide voor beide wijzigingstypen de volledige suite; verzin geen historische data-only-route. Rapporteer die beleidsverandering expliciet. Stratificeer daarnaast standaardmodus en seriële terugval waar relevant.

Gebruik vaste representatieve data met identieke data-tree/hash en equivalente garanties. Binnen één meetgroep: gelijke code/tests, runner-OS/image/CPU, Python/dependencies/cacheconditie, commando, selectie, workers en uitkomsten. Tussen baseline en eindversie mogen juist de onderzochte codewijzigingen verschillen, maar verklaar veranderde tests en dekking. Geen metingen over verschillende CPU's middelen en geen langzame geldige runs selectief verwijderen. Rapporteer mislukte/onvolledige/geannuleerde runs apart met uitsluitingsreden.

Gebruik `compare_ci_baseline.py` voor drie of meer **binnen dezelfde conditie** passende artifactmappen. De comparator vereist onder meer gelijke source/tests/repository-trees en workerinstellingen: geef hem dus niet baseline en eindcode of serieel en parallel als één homogene groep. Vergelijk daarna de afzonderlijke groepssamenvattingen met expliciete verschillen. Verzwak zijn checks niet; alleen een aantoonbaar noodzakelijke aanvullende rapportage mag worden toegevoegd met betekenisvolle tests.

Een handmatige dispatch is altijd full. Gebruik bestaande passende data-only-PR-runs of laat Lucas een legitieme geschikte PR en herhalingen organiseren. Wijzig geen muziekdata of curatorbeslissingen uitsluitend om de route te triggeren; doe een full-dispatch niet voor als data-only-bewijs. Opnieuw draaien van een oude PR na head/base-wijziging kan terecht naar full terugvallen. Controleer `classification.json` én de werkelijk uitgevoerde testselectie.

### B. Metingen ophalen en bewaren

Gebruik de bestaande meetketen; geen tweede parallel meetsysteem. Bewaar per run/attempt:

- Run- en joblinks, event, branch/ref, geteste SHA, PR-head/base en eventuele synthetische merge-SHA; data/source/tests-tree.
- Exacte commandoregel, werkelijke route en workers, OS/image/CPU, Python, dependencyversies, cache en installatieprovenance.
- Jobduur zonder wachtrij, gemeten pytestcommandoduur, canonieke validatieduur, afzonderlijk beschikbare publicatietiming, setup/call/teardown, YAML-loads/builds, tests/failures/errors/skips/xfails en coverage van dezelfde modules en bronregels.
- Ruwe job- en attemptmetadata, timing-JSON/logs, `junit.xml`, `coverage.xml`, `test-session.json`, `test-phases.jsonl`, classificatie, validatierapport en waar aanwezig `installation.json` en worker-artifacts.

Gebruik attempt-specifieke API-metadata, niet ongemerkt de laatste poging. Het bestaande protocol beschrijft bijvoorbeeld:

```bash
gh run download ID --repo LuHoo/classical_music --name ci-metrics-ID-ATTEMPT --dir DIRECTORY
gh api repos/LuHoo/classical_music/actions/runs/ID/attempts/ATTEMPT > DIRECTORY/run-api.json
gh api repos/LuHoo/classical_music/actions/runs/ID/attempts/ATTEMPT/jobs > DIRECTORY/jobs-api.json
```

Vervang placeholders met geverifieerde waarden en maak de uitvoermap vooraf. Normaliseer `run.json` zoals de comparator vereist, met behoud van de originele metadata. Bij reruns is de oorspronkelijke `created_at` geen zuivere wachttijd van die attempt; gebruik/verklaar de attempt-startreferentie. Publicatievalidatie zit deels binnen pytest: tel geen overlappende tijden bij elkaar en verzin geen aparte totale publicatieduur.

Rapporteer per groep mediaan, minimum, maximum en n; vermeld individuele waarden en uitval. Runner-minuten zijn de som van relevante jobduren/60, geen automatisch berekende factuur. Scheid `validate`-kosten van de bredere workflow-/sitekosten. Bewaar lokale diagnose apart van CI.

Als nieuwe runs nodig zijn: werk alle onafhankelijke documentatie en analyses af, lever Lucas de exacte run-/ref-/inputinstructies en ontbrekende bewijsvelden en wacht voor conclusies op resultaten. Start zelf geen externe runs. Historische revisies lokaal uitchecken of tijdelijke clones maken is geen alternatief voor Lucas' Git-beheer.

### C. Eindrapport

Werk `docs/workflows/ci-benchmark.md` bij en maak één samenhangend eindrapport, bij voorkeur `reports/completion/issue-310-ci-final-report.md` conform de bestaande repositorystructuur. Deze prompt staat op verzoek onder `report/prompts`; hernoem of verplaats bestaande `reports/` niet.

Vul per route onderstaande tabel met echte cijfers (mediaan [min–max], n) en gekoppelde evidence. Bij ontbrekend bewijs schrijf letterlijk **nog niet gemeten**, met oorzaak en benodigde vervolgactie. Nul is geen vervanging voor onbekend.

| Maatstaf | Voor | Na | Verschil |
|---|---|---|---|
| Totale CI-jobduur, exclusief wachtrij | | | |
| Pytest-duur | | | |
| Canonieke/publicatievalidatie (onderscheiden) | | | |
| Uitgevoerde tests, failures en skips | | | |
| Dekking van dezelfde modules | | | |
| Runner-minuten / aantal workers | | | |

Voeg een stapmatrix #305 t/m #309 plus cumulatief eindresultaat toe: bewijslinks, dataset/revisies, controles, lokale/CI-status, kosten, tijdwinst en beperkingen. Maak onderscheid tussen meetinfrastructuur, minder herhaalde parsing/bouw met dezelfde garanties, minder geselecteerde tests, en sneller uitvoeren door paralleliteit. Tel percentages uit verschillende omgevingen niet op. Cumulatieve winst komt uit een passende baseline/eindvergelijking; ontbreekt die, claim haar niet.

Beoordeel het oorspronkelijke streefdoel alleen als dit aantoonbaar is vastgelegd. Ontbreekt het nog, noteer dat als acceptatiegat en laat Lucas een onderbouwd doel vaststellen vóór nieuwe eindmetingen; presenteer geen achteraf gekozen doel als vooraf afgesproken. Rapporteer gehaald/niet gehaald of niet beoordeelbaar, resterende bottlenecks, bewijsbeperkingen en concrete open afwijkingen. Sluiting van eerdere issues bewijst niet dat elk oorspronkelijk meetcriterium is ingevuld.

## 5. User Manual en onderhoud

Werk het bestaande handboek in helder Nederlands bij, met uitvoerbare voorbeelden die passen bij de uiteindelijke mergeversie:

- Wanneer individuele controles, `finish`, data-only CI, full CI en de echte sitebouw nodig zijn; welke controles elkaar niet vervangen.
- Hoe Lucas in Actions de route, echte uitkomsten, timings, JUnit, coverage, worker- en installatie-artifacts vindt; verschil tussen gepland, uitgevoerd, geslaagd, overgeslagen en ontbrekend bewijs.
- Handmatige volledige run via `Validate Canonical Data` / `validate.yml`, juiste branch/ref en `force_full=true`; na #315 expliciet de werkelijke `pytest_mode`-opties, standaard en seriële terugval. `force_full` bepaalt testscope, niet worker-aantal. Toon ook de afzonderlijke sitecontrole.
- Wanneer een full-run nodig is: code/schema/dependencies/workflow, onbekende/gemengde wijzigingen, onbetrouwbare classificatie, herstel/onderzoek en eindverificatie. Een oud groen rapport valideert geen nieuwe data.
- Onderzoekspad voor tijdregressie, afwijkende testaantallen/coverage, ontbrekende workers/artifacts, installatie-auditfout of full-fallback: eerst revisie, omgeving en selectie vergelijken; daarna faseprofiel/bottleneck onderzoeken.
- Onderhoud: Lucas is reviewer en mergebeslisser; bij relevante workflow/dependency/parser/testselectie/coveragewijzigingen garantie- en routematrix nalopen, meetprotocol opnieuw toepassen en besluiten met evidence vastleggen. Bewaar runlinks en compacte duurzame bewijsbestanden voordat artifacts verlopen. Bij pytest-cov-upgrades blijft de echte worker-coverageverliesregressie verplicht; de #315-overdrachtscontrole steunt op pytest-cov 5.

Geen uitbreiding van curator `finish`, andere parser, nieuwe testselectie, extra workers of nieuwe optimalisatie als nevenwerk. Geen bronplaylist-/TIDAL-acties of wijzigingen aan canonieke muziekgegevens. Tijdelijke testdata en uitvoer zijn toegestaan voor isolatie; gebruik geen hardlinks naar mutabele echte data. Genereer niet ongevraagd over Lucas' bestaande `publication/` of `_site/` heen. Een script zonder veilige uitvoeroptie vereist een passend testharnas/tijdelijke uitvoer of een door Lucas uitgevoerde CI-controle, geen extra implementatiecheckout.

## 6. Verificatie en oplevering

1. Controleer eerst eventuele meettoolwijzigingen met gerichte positieve en negatieve tests, inclusief onvolledige evidence, foutstatus en vergelijkbaarheid. Voeg geen triviale tests toe voor alleen tekstwijzigingen.
2. Laat de volledige suite en actuele catalogus/publicatiecontroles op de eindversie slagen. Gebruik de bestaande pytestconfig met coverage voor `src/classical_music/validation` en `src/classical_music/migration`, de meetplugin, durations, JUnit en coverage-XML. Ontleen route/workerargumenten aan de actuele workflow; verander addopts niet om coverage of controles te laten verdwijnen.
3. Bewijs de data-only-route met echte route-/uitvoerevidence, en de handmatige full-route met een geslaagde dispatch op de betreffende eindversie. Bewijs echte Jekyll-bouw en linkcontrole via de afzonderlijke `build`-job. Een oudere groene run of alleen unit-tests volstaan niet.
4. Verifieer documentatielinks, Markdown en Jekyll/Liquid-veiligheid; Actions-expressies in documentatie moeten niet onbedoeld door Liquid worden verwerkt. Controleer bestaande en nieuwe bestanden afzonderlijk; `git diff` toont geen untracked inhoud. Gebruik alleen leesacties, waaronder `git diff --check` en `git status --short --branch`.
5. Lever een Nederlandstalige samenvatting: gewijzigde bestanden, werkelijk uitgevoerde verificaties met resultaten, complete baseline/eindtabellen, resterende beperkingen en precieze handelingen voor Lucas.
6. Bereid één kopieerbare **draft-PR-titel en -beschrijving tegen main** voor, met `Refs #310` en `Part of #304` zolang de acceptatie van #310 open is (geen automatische sluiting voor acceptatie; pas bij de uiteindelijke merge kan Lucas dit wijzigen in een sluitende verwijzing), verwijzingen naar #311–#315, probleem/verandering/behouden controles, complete tabellen, SHA's/datarevisies/run-/artifactlinks en open bewijsvelden. Lucas publiceert de draft zelf. Zet niet `Closes #304` in de PR.

**Klaar betekent:** voldoende vergelijkbare CI-runs en herleidbare analyses voor beide routes; per-stap- en cumulatieve beoordeling met eerlijke beperkingen; actuele User Manual en onderhoudsafspraken; groene volledige suite, catalogus/sitecontroles en aantoonbare handmatige full-run; reviewbare draft-PR-inhoud. Als bewijs ontbreekt, lever het afgeronde deel en benoem exact welk acceptatiecriterium openstaat. Claim geen voltooiing. De epic wordt pas na Lucas' review/merge en afhandeling van resterende afwijkingen gesloten, door Lucas zelf.
