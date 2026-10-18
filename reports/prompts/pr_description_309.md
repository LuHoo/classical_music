Closes #309

## Probleem en resultaat
Beoordeelt veilige pytest-parallelisatie na de eerdere CI-optimalisaties (#304).
PR/main en handmatige runs gebruiken standaard twee workers; handmatig blijft serieel beschikbaar.
Op dezelfde EPYC 7763-omgeving tonen drie seriële en vijf parallelle runs 25.0%
minder pytesttijd en 24.6% minder jobtijd/runner-minuten, tegen 23.1% meer gesamplede RSS.
Deze metingen onderbouwen de nieuwe standaard; de bijgewerkte workflow moet nog groen worden in CI.

| Maatstaf (mediaan) | Serieel | Parallel |
|---|---:|---:|
| Job zonder wachtrij | 21:20 | 16:05 |
| Pytestopdracht | 1243.93 s | 932.93 s |
| Canonieke validator | 11.91 s | 11.93 s |
| Tests / failures / skips | 537 / 0 / 0 | 537 / 0 / 0 |
| Coverage validation + migration | 985/1170 | 985/1170 |
| Runner-minuten / workers | 21.33 / 1 | 16.08 / 2 |
| Gesamplede procesboom-RSS | 466852 KiB | 574880 KiB |

Serieel: runs 226/229/232. Parallel: 221/223/224/225/227. Commit:
8a8574fab7cbe4b22953a3469a4c8eaea79cb595. Data-tree:
615af8804456a950a478406d8e13564878ca6ee3. Python 3.13.16, Ubuntu 24 image
20261012.334.1, vier zichtbare CPU's, gelijke dependencies, geen dependencycache.
Spreiding, alle run/artifactlinks en beperkingen staan in docs/workflows/ci-benchmark.md.

## Behouden controles en reviewfixes
- Eén validate-job; dezelfde testselectie en volledige canonieke validatie.
- Worker-eigen metrics en tijdelijke uitvoer; volledige levenscycluscontrole.
- Effectieve foutstatus in rootrapport; malformed counters behouden diagnostiek.
- Echte xdist-tests voor coveragecombinatie, ontbrekende workeroverdracht, foutfasen en crash.
- Installatie-audit vóór/na pip, met hashes en diff; geen algemene dirty-checkuitzondering.
- Comparator weigert incomplete parallelle resultaten.

## Besluit en beperkingen
Gebruik twee workers als standaard, met serieel als handmatige terugvaloptie. Dezelfde CPU geeft consistente winst, maar andere
CPU-modellen zijn niet equivalent. Historische egg-info-wijzigingen missen voor/na-inhoud;
de comparator blijft oude dirty artifacts weigeren. Nieuwe runs leveren controleerbare
installatie-evidence. RSS is gesampled, niet runnerbreed; publicatievalidatie zit in pytest.
Lokale 30.7%-pilotcijfers blijven gescheiden van GitHub-resultaten.

De historische PR-validatie 219/poging 2 is geslaagd. Na commit/push van deze reviewfixes
is een nieuwe groene PR-validatie nodig. Lokale regressievalidatie van de reviewfixes: 153 tests geslaagd (Python 3.13, macOS), inclusief echte xdist-subprocessen, coverageverlies, ongeldige metrics, installatieprovenance en CI-classificatie. De volledige catalogussuite is niet opnieuw lokaal uitgevoerd.
