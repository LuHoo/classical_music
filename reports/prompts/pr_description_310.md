# Draft-PR-titel

CI-eindinventaris, User Manual en onderhoudsafspraken (#310)

# Draft-PR-beschrijving tegen main

Closes #310

Part of #304

## Probleem en verandering

De eerdere optimalisaties hebben verschillende meetgrenzen en bewijsbeperkingen.
Deze PR scheidt historische lokale/CI-resultaten van een geldige cumulatieve
eindmeting, bewaart compacte artifactevidence en werkt het bestaande User Manual
in het Nederlands bij. Er is geen nieuwe optimalisatie, route- of datawijziging.

**Draft houden: de acceptatiecriteria voor eindmetingen zijn nog niet volledig bewezen.**
`Closes #310` geldt pas bij uiteindelijke merge na afhandeling van de open punten.
De epic wordt niet automatisch gesloten.

## Behouden controles

Eén actuele canonieke pass, publicatie-/cross-intakecontroles in pytest, stabiele
`validate`, twee workers standaard en handmatige seriële terugval. Full bij
code/schema/dependencies/workflows/onzekerheid; data-only alleen met volledige,
revisiegebonden allowlist-evidence. `finish` blijft een gerichte lokale batchgrens.
De echte Pages-build en linkcontrole blijven een afzonderlijke controle.

## Revisies en bewijs

- #315-merge: `caaa5ccc637c36748a481081604032ae648864fb`.
- #310-onderzoeksbasis: `f42ce3b53ee5d092dc3288f82864d1daa7ebeedf`;
  uiteindelijke PR-head na commit/push: **nog in te vullen**.
- Data-tree: `615af8804456a950a478406d8e13564878ca6ee3`.
- Baselinekandidaat: `ea36428a46d61e6993cb8f043484e78200944220`;
  [203](https://github.com/LuHoo/classical_music/actions/runs/38138286003),
  [204](https://github.com/LuHoo/classical_music/actions/runs/38139221980),
  [205](https://github.com/LuHoo/classical_music/actions/runs/38139224128):
  afgewezen wegens ongeaudite dirty status; bovendien verschillende CPU's.
- Finale #315-[validate](https://github.com/LuHoo/classical_music/actions/runs/39140756238)
  en [main](https://github.com/LuHoo/classical_music/actions/runs/39144596359):
  554 tests, nul failures/errors/skips, coverage 985/1170, audit/workerbewijs compleet.
- Afzonderlijke sitechecks:
  [finale PR](https://github.com/LuHoo/classical_music/actions/runs/39140756229),
  [main-merge](https://github.com/LuHoo/classical_music/actions/runs/39144596365).
- Alle run-/artifactlinks, SHA's, individuele cijfers, hashes en kosten staan in
  [het eindrapport](../completion/issue-310-ci-final-report.md) en
  [de artifactextractie](../completion/issue-310-ci-evidence.json).

## Code/full: cumulatieve eindvergelijking

| Maatstaf | Voor | Na | Verschil |
|---|---|---|---|
| Totale CI-jobduur zonder wachtrij | nog niet gemeten als geldige baselinegroep | nog niet gemeten op eindref | nog niet gemeten |
| Pytestduur | nog niet gemeten als geldige baselinegroep | nog niet gemeten als eindgroep | nog niet gemeten |
| Canonieke/publicatievalidatie | nog niet gemeten als vergelijkbare groep | nog niet gemeten; publicatie deels binnen pytest | nog niet gemeten |
| Tests, failures, skips | 372/0/0 per oude waarneming | 554/0/0 in finale #315-runs; geen #310-eindgroep | +182 tests, geen snelheidsconclusie |
| Dekking van dezelfde modules | 985/1170, oude bronrevisie | 985/1170, nieuwe bronrevisie | geen gelijkheid afgeleid uit totaal |
| Runner-minuten / workers | nog niet gemeten als geldige groep / 1 | nog niet gemeten als geldige groep / 2 | nog niet gemeten |

## Curator/data-only: cumulatieve eindvergelijking

| Maatstaf | Voor | Na | Verschil |
|---|---|---|---|
| Totale CI-jobduur zonder wachtrij | nog niet gemeten als curatorbaselinegroep; oud beleid full | nog niet gemeten | nog niet gemeten |
| Pytestduur | nog niet gemeten als groep | nog niet gemeten | nog niet gemeten |
| Canonieke/publicatievalidatie | nog niet gemeten als groep | nog niet gemeten als groep | nog niet gemeten |
| Tests, failures, skips | full, geen historische data-only-route | nog niet gemeten met actuele route-evidence | nog niet gemeten |
| Dekking van dezelfde modules | nog niet gemeten als groep | nog niet gemeten als groep | nog niet gemeten |
| Runner-minuten / workers | nog niet gemeten als groep / 1 | nog niet gemeten als groep / 2 | nog niet gemeten |

## Methode, besluit en beperkingen

Minimaal drie succesvolle vergelijkbare CI-runs per conditie; ongewijzigde strikte
comparator binnen iedere groep, daarna expliciete vergelijking tussen groepen.
CPU/image/dependencies, data, testselectie, audit en uitkomsten moeten aantoonbaar
passen. Queue, jobtijd en commandoduur blijven onderscheiden. Twee pytest-workers
delen één runner; minuten niet maal twee. RSS is gesampled, geen runnerbrede piek.

De historische #309-groep ondersteunt het behouden tweeworkerbesluit (-24,6%
jobtijd op 7763), maar is geen geaudite #310-baseline. Lokale percentages worden
niet opgeteld bij CI-winst. Het oorspronkelijke numerieke streefdoel is niet
aangetroffen: doelbeoordeling niet beoordeelbaar, geen achteraf gekozen doel.

## Nog nodig vóór afronding

Lokale verificatie is geslaagd: volledige suite **554 passed**, JUnit nul
failures/errors/skips, coverage **985/1170 (84,19%)**, twee complete workers en
32 publicatiebuilds. Canonieke validator: exit 0, nul fouten, 115 waarschuwingen.
Python 3.14.3/macOS; gemeten pytestcommandoduur 2113,39 s. Dit is geen CI-meting.
Documentlinks/JSON/Liquid en diff-whitespace zijn gecontroleerd. Lokale Jekyll-bouw
is niet uitgevoerd: Bundler 2.5.9 ontbreekt. De huidige PR-sitebuild moet nog groen zijn.

- Lucas legt doel en een geldige baseline-reproductie vast vóór verdere eindmetingen.
- Drie passende actuele full-runs en drie legitieme data-only-PR-runs; geen dispatch
  als data-only voorstellen en geen muziekdata wijzigen alleen voor de benchmark.
- Groene volledige suite, actuele catalogus/publicatie en echte sitebouw op de
  uiteindelijke #310-versie; handmatige full-route op die ref aantonen.
- Tabellen aanvullen met individuele runs, mediaan, spreiding, n en artifacts;
  branchbescherming met Lucas verifiëren. Geen merge of sluiting van #304 door Copilot.

Referenties: #311, #312, #313, #314, #315; issue #310 en epic #304.