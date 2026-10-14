# Expertprompt voor Copilot: issue #309 — veilige parallelisatie beoordelen en meten

Je werkt als senior Python-, testinfrastructuur- en GitHub Actions-engineer aan `LuHoo/classical_music`. Voer issue #309 uit: onderzoek na de eerdere CI-optimalisaties of twee workers of afzonderlijke testjobs aantoonbaar zinvolle winst geven, zonder controles, isolatie of betrouwbare rapportage te verliezen. Implementeer alleen parallelisatie waarvoor het bewijs de keuze ondersteunt. Een onderbouwde conclusie om serieel te blijven is een volwaardig resultaat.

## Bronnen, scope en werkbasis

- Issue: https://github.com/LuHoo/classical_music/issues/309
- Epic: https://github.com/LuHoo/classical_music/issues/304
- Voorgaande stap: issue #308, gemergede PR https://github.com/LuHoo/classical_music/pull/314
- Werkbranch: `309-ci-optimalisatie-56-veilige-parallelisatie-beoordelen-en-meten`.
- Bij het opstellen van deze prompt stonden deze branch en `origin/main` op `0055b686f23b11c48db94dc2c15102fd54d9520d`, de merge van PR #314. Verifieer de actuele toestand zelf; gebruik dit niet als blijvende garantie.
- Lees eerst de actuele issuebeschrijving, toepasselijke `AGENTS.md`, `pyproject.toml`, `.github/workflows/validate.yml`, `docs/workflows/ci-benchmark.md` en de relevante code en tests.
- Voer implementatie uitsluitend uit in Lucas' bestaande checkout op de genoemde branch met ingestelde upstream. Controleer vóór wijzigingen checkout, actieve branch, upstream en bestaand werk, bijvoorbeeld met `git status --short --branch` en `git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'`. Ontbreekt de juiste werkbasis, stop vóór wijzigingen en laat Lucas die herstellen.
- Geen worktrees, clones, detached HEAD, nieuwe branches of wijzigingen op `main`. Respecteer bestaand lokaal werk en bestaande meetbestanden.
- Git-beheer blijft bij Lucas: geen fetch/pull, checkout, reset, staging, commit, push of merge zonder afzonderlijke expliciete toestemming. Lokaal is Git 2.10.1 vastgesteld; adviseer geen `git switch` of `git restore`.
- Laat externe wijzigingen, workflow-dispatches en het publiceren van een PR aan Lucas, tenzij hij daar afzonderlijk toestemming voor geeft. Bereid wel een volledige draft-PR-beschrijving voor, gericht op `main`, met verwijzingen naar #309 en #304. Lucas reviewt en merget zelf.
- De hele map `reports/prompts/` wordt via Git gedeeld. Ruwe meetuitvoer hoort in de bestaande genegeerde meetmappen of CI-artifacts; een duurzaam verslag hoort in de projectdocumentatie.
- Geen bronplaylist-/TIDAL-acties, muzikale curatorbeslissingen, wijzigingen in echte gebruikersdata of uitbreiding naar issue #310.

## Onveranderlijke garanties

1. Geen tests verwijderen, overslaan, retries toevoegen of validatie verzwakken om parallelisatie sneller of groen te maken.
2. De door #308 geselecteerde tests blijven per route inhoudelijk gelijk: vergelijk full-serieel met full-parallel, en data-only-serieel met data-only-parallel. Vergelijk geen verschillende routes alsof het parallelisatiewinst is.
3. Actuele canonieke, publicatie-, bronbehoud- en cross-intakecontroles blijven bestaan. Geen eerder geslaagde validatie als cachebewijs voor gewijzigde data.
4. Required check `validate` blijft betrouwbaar rood bij iedere relevante fout of ontbrekend verplicht resultaat. Geen pathfilters of afhankelijkheidsconstructies die stilzwijgend groen opleveren.
5. Eén canonieke validatorrun blijft console, JSON en samenvatting voeden. De aparte echte sitebouw en linkcontrole blijven behouden.
6. Annulering blijft beperkt tot achterhaalde runs van dezelfde PR; andere PR's, main- en handmatige runs blijven beschermd. Behoud de revisie- en volledigheidscontroles van de classifier.

## 1. Onderzoek de huidige kosten en veiligheidsgrenzen

Maak eerst een korte analyse op basis van actuele timings en code:

- Welke tests bepalen de kritieke doorlooptijd? Welke kosten zitten in setup, collectie, YAML-loads, catalogussnapshots, publicatiebouw en teardown?
- Welke tests zijn CPU-, geheugen- of I/O-gebonden? Hoeveel helpt taakverdeling als enkele lange tests de totale duur domineren?
- Welke sessiefixtures worden per proces opnieuw opgebouwd? `catalog_snapshot`, `canonical_matcher` en curatorfixtures zijn belangrijke kandidaten. Neem extra catalogusloads en geheugen per worker mee; een sessiefixture is niet vanzelf gedeeld tussen workers.
- Inventariseer alle schrijfdoelen, tijdelijke mappen, locks, vaste bestandsnamen, globale toestand, environment-mutaties en subprocessen. Controleer vooral publicatie-uitvoer, curatorbeslisrecords, coverage, JUnit en meetbestanden.
- Controleer dat tests geen echte netwerkmutaties of dubbele externe acties kunnen uitvoeren. Locks en rollback blijven juist, ook als tests gelijktijdig lopen. Verwijder geen lock om een benchmark te laten slagen.
- Hergebruik fixtures uitsluitend wanneer ze onveranderlijk zijn. Muterende tests krijgen eigen tijdelijke mappen; de echte checkout, `publication/` en gebruikersbeslissingen blijven onaangeroerd.

Gebruik de huidige testisolatie en relevante tests, waaronder `tests/conftest.py`, `tests/test_suite_isolation.py`, curator-/collectietests en publicatietests. Voeg alleen betekenisvolle regressietests toe voor werkelijk gevonden risico's.

## 2. Maak de bestaande meetinfrastructuur geschikt voor het experiment

Inspecteer expliciet:

- `src/classical_music/pytest_metrics.py`: weigert momenteel parallelisme; `Metrics` schrijft vaste namen en truncatet bij initialisatie `test-phases.jsonl`.
- `scripts/measure_ci.py`: rapporteert momenteel `workers=1`; controleer ook scope van procesmetingen.
- `scripts/compare_ci_baseline.py`: vereist identieke workers, commandoregel, dependencies en tree-IDs binnen een baseline. Deze waarborgen mogen niet simpelweg verdwijnen om een vergelijking mogelijk te maken.
- `scripts/summarize_ci_metrics.py`, `scripts/summarize_execution.py`, coverage- en JUnit-output en bestaande infrastructuurtests.

Pas waar nodig deze infrastructuur gericht aan:

- Geef iedere worker/job/runpoging eigen uitvoerpaden en herleidbare metadata. Geen gelijktijdige writes of truncatie van dezelfde bestanden.
- Onderscheid controller- en worker-events. Tel een testfase niet dubbel als een event zowel lokaal als via de controller zichtbaar is. Rapporteer setup/call/teardown, fouten en counters met hun echte scope.
- Voeg resultaten deterministisch samen. Controleer volledigheid, runidentiteit, worker/shard-identiteit, verwachte test-nodeids en outcomes. Ontbrekende, dubbele, afgebroken of onleesbare verplichte resultaten mogen niet stilzwijgend als succes tellen.
- Houd individuele artifacts beschikbaar bij een fout of crash. Maak duidelijk welke resultaten onvolledig zijn; een som van geslaagde deelresultaten bewijst geen geslaagde run.
- Behoud strenge vergelijking binnen een meetconditie. Maak de vergelijking tussen serieel en parallel expliciet, met alleen de bedoelde verschillen toegestaan, zoals workers en schedulerargumenten. Installeer waar mogelijk dezelfde dependencyset in beide condities en gebruik dezelfde benchmarkcapabele code/testrevisie.
- Wijzig of 'normaliseer' geen ruwe provenance om twee onvergelijkbare runs gelijk te laten lijken. Leg legitieme verschillen vast; verzamel nieuwe runs als bewijs tekortschiet.
- Controleer actuele officiële documentatie en versiecompatibiliteit voordat je bijvoorbeeld pytest-xdist en pytest-cov configureert. Maak geen aannames over coveragecombinatie of fixtures over procesgrenzen.

## 3. Vergelijk kleine, verklaarbare alternatieven

Begin met de bestaande seriële uitvoering en één beperkte parallelle kandidaat met **twee workers**. Gebruik geen onbeperkt `-n auto`. Onderzoek afzonderlijke testjobs alleen als timing en isolatie daar een concrete reden voor geven; bouw niet onnodig meerdere parallelisatiesystemen.

Leg vooraf het besliscriterium vast: herhaalbare vermindering van de kritieke doorlooptijd die groter is dan de gemeten spreiding, met een expliciete afweging van extra runner-minuten, geheugen, complexiteit en risico. Beloof geen percentage zonder baseline.

- Bij twee workers op één runner: meet proces-/fixtureoverhead, schedulerverdeling en de invloed op lange tests. Twee workers op één runner betekenen niet automatisch tweemaal zoveel runner-minuten.
- Bij meerdere jobs: neem installatie, checkout, redundante fixtures, artifactoverdracht en aggregatie mee. Runner-minuten zijn de som van bezette jobtijd; wall-clock is de kritieke keten, niet die som.
- Behoud een eenvoudige seriële fallback. Maak experimentele paralleliteit zo nodig opt-in totdat het bewijs compleet is.
- Test beide bestaande routes onafhankelijk; behoud precies de geselecteerde testverzameling en controles.

## 4. Bewijs fail-closed resultaten en samengestelde coverage

Maak kleine, geïsoleerde infrastructuurtests die de volgende gevallen werkelijk uitlokken:

- Eén test faalt op één worker/shard terwijl de andere slaagt.
- Setup- of collectiefout, workercrash, afgebroken uitvoer en ontbrekend resultaatbestand.
- Een ontbrekende of dubbele shard en ontbrekende test-nodeids; geen stille gaten of dubbele telling.
- Fout in coveragecombinatie of ontbrekende coverage van een verplichte worker/shard.
- Gelijktijdige publicatie-uitvoer en muterende fixtures blijven gescheiden; echte repositorybestanden worden niet gewijzigd.
- Rapportage blijft beschikbaar en de eindstatus blijft nonzero bij fouten, ook met latere `always()`-stappen.

Controleer samengestelde coverage van **dezelfde modules en uitvoerbare regels**, met consistente bronpaden. Gemiddelde percentages van workers zijn geen gecombineerde coverage. Verklaar verschillen in geraakte regels en bewijs dat subprocessen waar nodig worden meegenomen. Laat geen oud coveragebestand nieuwe resultaten beïnvloeden.

Bij meerdere jobs moet `validate` alle verwachte resultaten expliciet controleren. `skipped`, `cancelled`, een mislukte dependency of ontbrekend artifact mogen niet als succesvol worden geaggregeerd. Controleer de echte workflowconfiguratie; een losse Pythonkopie van de YAML-logica is geen regressiebewijs voor de workflow zelf.

## 5. Meetprotocol en bewijs

Gebruik minimaal drie vergelijkbare volledige runs **per meetconditie** voor de eindvergelijking. Lokale proeven en GitHub Actions-resultaten blijven afzonderlijk. Gebruik actuele post-#308-baselines; oude 453/517-tests-runs zijn historische context, geen automatische baseline voor nieuwe code.

Leg per run vast:

- Commit-SHA, data-/source-/testrevisies en eventuele lokale dirty-status. Claim geen exact committed bewijs bij een gewijzigde checkout.
- Route, volledige commandoregel, verzamelde nodeids, daadwerkelijk uitgevoerde tests, failures, errors, skips en retries.
- Runner/image, Python, dependencies, cachecondities, aantal workers/jobs, scheduler en run-id/attempt.
- Pytest-wall-clock, totale jobduur exclusief wachtrij, canonieke/publicatievalidatieduur, setup/teardown, YAML-loads en builds waar betrouwbaar gemeten.
- Runner-minuten en geheugen waar meetbaar. Meet voor parallelle processen bij voorkeur het gelijktijdige totale geheugen; tel losse procespieken niet op alsof ze gelijktijdig optraden. Label meetmethode en beperkingen. Schrijf 'niet gemeten' als betrouwbare meting ontbreekt.
- Timing-, JUnit-, coverage-, worker- en samenvattingsartifacts, plus links naar de CI-runs.

Rapporteer mediaan en spreiding (min/max, eventueel aanvullend een andere verklaarde maat), geen geselecteerde beste run. Bewaar mislukte experimenten als diagnostiek en rapporteer ze; gebruik ze niet als succesvolle baseline en verberg instabiliteit niet met retries. Controleer eerst de bruikbaarheid van `ci-baseline/`; de eerder aangetroffen lege `baseline.json` is geen valide meetrapport.

Vul deze verplichte tabel met echte resultaten of 'nog niet gemeten'. Maak aparte vergelijkingen per route en benoem de configuraties:

| Maatstaf | Serieel | Parallel (configuratie) | Verschil |
|---|---|---|---|
| Totale CI-jobduur, exclusief wachtrij | | | |
| Pytest-duur | | | |
| Canonieke/publicatievalidatie | | | |
| Uitgevoerde tests, failures en skips | | | |
| Dekking van dezelfde modules | | | |
| Runner-minuten / aantal workers | | | |
| Geheugen en meetmethode | | | |

## 6. Beslissing, documentatie en oplevering

Neem één expliciete, onderbouwde beslissing:

- **Parallelisatie invoeren** als winst herhaalbaar is, alle garanties bewezen behouden zijn en de kostenafweging aanvaardbaar is; of
- **Serieel behouden** als winst onvoldoende is, overhead/geheugen te hoog is, isolatie onvoldoende bewezen is of CI-bewijs ontbreekt. Lever dan alleen nuttige meet-/isolatieverbeteringen en een reproduceerbaar besluit op. Geen ongebruikte experimentele productiecode laten staan.

Voer de gerichte infrastructuurtests en vervolgens de relevante volledige routes uit met de juiste Pythonversie (project vereist minimaal 3.13). Controleer de interpreter vóór het testen; de bestaande `.venv` is eerder als Python 3.9 aangetroffen. Upgrade geen globale omgeving ongevraagd. Meld concrete beperkingen als de juiste omgeving of CI-uitvoering nog ontbreekt.

Werk `docs/workflows/ci-benchmark.md` en waar nodig de scripts-user-manual bij met reproduceerbare opdrachten, isolatieafspraken, artifactstructuur, volledige resultaten en besluit. Beschrijf alleen wat daadwerkelijk is aangetoond. Houd de bredere eindmeting en onderhoudsafronding van #310 buiten deze stap.

Lever ten slotte:

1. Een overzicht van gewijzigde bestanden met doel en behouden controles.
2. Exacte test-/meetopdrachten, resultaten en beperkingen, uitgesplitst in lokaal en CI.
3. De vergelijkingstabellen, provenance en artifact-/runlinks.
4. De beslissing serieel/parallel met risico's, fallback en onderbouwing.
5. Een complete conceptbeschrijving voor één **draft PR** naar `main`, met `Closes #309` alleen wanneer de acceptatie daadwerkelijk rond is, en `Part of #304`. Benoem openstaande acties expliciet als bewijs nog ontbreekt.
6. Concrete vervolgstappen die Lucas handmatig moet uitvoeren voor commit/push, externe meetruns en review. Publiceer of merge niets zelfstandig.

Werk door tot de lokaal toegestane implementatie, verificatie en documentatie compleet zijn. Stop niet bij een plan; presenteer ontbrekende externe toestemming of ontbrekend CI-bewijs wel eerlijk en schakel de standaardroute niet speculatief om naar parallel.
