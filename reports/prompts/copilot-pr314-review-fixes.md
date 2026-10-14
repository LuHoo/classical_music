# Copilot-opdracht: herstel de vijf reviewbevindingen van PR #314

Je werkt als senior Python- en GitHub Actions-engineer in VS Code aan `LuHoo/classical_music`. Implementeer gerichte reparaties voor de vijf onderstaande reviewbevindingen in PR #314, behorend bij issue #308. Lever werkende code, betekenisvolle regressietests en correcte documentatie. Alleen een plan of advies is niet voldoende.

## Context en werkafspraken

- Issue: https://github.com/LuHoo/classical_music/issues/308
- PR: https://github.com/LuHoo/classical_music/pull/314
- Beoordeelde head: `c8441c53e447992a662142fd403938675a6af046`. Vergelijk eerst de actuele bestanden; behandel deze review als te verifiëren bevindingen, niet als vervanging van code-inspectie.
- Werk uitsluitend in Lucas' bestaande checkout, op `308-ci-optimalisatie-46-controlebeleid-en-betrouwbare-ci-selectie-per-wijzigingstype`, met de ingestelde upstream. Dit is een reparatie van de bestaande PR; maak geen nieuwe branch.
- Lees toepasselijke `AGENTS.md`-instructies. Controleer vóór iedere wijziging de checkout, actieve branch, upstream en bestaande wijzigingen met leesacties, waaronder `git status --short --branch` en `git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'`.
- Stop vóór wijzigingen als de branch of upstream niet klopt. Laat Lucas dat herstellen. Geen worktrees, clones, detached HEAD of wijzigingen op `main`.
- Git-beheer blijft bij Lucas: geen checkout, fetch, pull, reset, add, commit, push, merge of andere muterende Git-acties. Geen PR-comments, reviews, metadatawijzigingen of workflow-dispatches zonder aanvullende expliciete toestemming. Git is lokaal 2.10.1; adviseer geen `git switch` of `git restore`.
- Behoud bestaand werk, waaronder eventuele lokale `ci-baseline/`-metingen. De hele map `/reports/prompts/` is bedoeld om via Git te delen en mag niet worden genegeerd. Lucas verzorgt het toevoegen, committen en pushen.
- Beperk de implementatie tot deze reparaties en rechtstreeks benodigde tests/documentatie. Geen nieuwe optimalisaties, verzwakking van controles of uitbreiding van `curator finish`.

## Te behouden garanties

1. Alleen een aantoonbaar volledige, betrouwbare diff van de relevante revisies mag `data-only` selecteren. Iedere onzekerheid selecteert `full`.
2. `validate` blijft de stabiele job-/checknaam. Geen workflow-pathfilters, conditioneel overgeslagen vereiste job of constructie die een fout groen maakt.
3. Beide routes behouden actuele canonieke controles en relevante curator-, publicatie- en cross-intakecontroles. Geen validatiecache die controles op gewijzigde data vervangt.
4. Eén canonieke validatoruitvoering voedt console, JSON en samenvatting. Fouten behouden hun nonzero-exit en beschikbare rapporten/artifacts.
5. De handmatige volledige route blijft bestaan. Kortere testselectie mag niet als bewezen tijdwinst worden gepresenteerd.

## 1. Bewijs volledigheid van de GitHub-bestandenlijst

Inspecteer `scripts/classify_pr_changes.py`, vooral `_fetch_pr_files()` en de onvoorwaardelijke `classify(files, diff_complete=True)`.

Probleem: een pagina met minder dan 100 records beëindigt de lus, maar bewijst niet dat de volledige diff beschikbaar is. GitHubs endpoint voor PR-bestanden retourneert maximaal 3.000 bestanden; de huidige grens van 10.000 voorkomt daardoor geen stille afkapping. Een simulatie met 30 pagina's van 100 toegestane bestanden en daarna een lege pagina selecteerde `data-only` met `diff_complete=True`.

Herstel:

- Raadpleeg de actuele officiële API-documentatie en controleer het verwachte aantal gewijzigde bestanden uit PR-metadata tegen het aantal unieke, gevalideerde resultaten.
- Behandel ontbrekende/ongeldige metadata, aantalmismatch, duplicaten, onbetrouwbare paginering en overschrijding van de API-grens als onzeker: `full`, met een bruikbare reden.
- Behandel de limiet conservatief; accepteer een grensgeval alleen als volledigheid werkelijk bewezen is. Een veilige fallback is voldoende, een ingewikkelde alternatieve diffbron is niet vereist.
- Behoud de bestaande veilige fallback bij netwerkfouten, timeouts en ongeldige JSON.

Tests: normale kleine diff, meerdere pagina's, exact veelvoud van de paginagrootte, vroege lege pagina, duplicaten, ontbrekende metadata, aantalmismatch, grens van 3.000 en een grotere diff waarbij een codebestand buiten het opgehaalde deel valt. Mock de externe API; voer geen duizenden echte requests uit.

## 2. Koppel classificatie aan de revisies van de run

Probleem: het endpoint op PR-nummer retourneert de actuele PR, terwijl de workflow een specifieke revisie test. Een oudere opnieuw uitgevoerde run of een wijziging tijdens paginering kan daardoor classificeren op een andere diff. Concurrency-annulering bewijst geen revisieconsistentie.

Herstel:

- Leg expliciet vast welke verwachte head- en baserevisies bij deze run horen en hoe die zich verhouden tot de uitgecheckte mergecommit. Verwar `github.sha` bij een PR niet met de head-SHA.
- Geef de noodzakelijke verwachte revisies vanuit betrouwbare workflow-/eventcontext door aan de classifier.
- Controleer actuele PR-metadata vóór én na paginering tegen de verwachte revisies en volledigheidsgegevens. Bij ontbrekende, gewijzigde of afwijkende informatie: `full`.
- Voorkom dat een later gewijzigde base onterecht als bewezen equivalent wordt behandeld. Beschrijf eventuele grenzen van het bewijs en kies bij onzekerheid de volledige route.
- Neem de relevante revisies en fallbackreden op in het classificatierapport, zodat de beslissing controleerbaar is.

Tests: overeenkomende revisies, afwijkende head, afwijkende base, wijziging tussen pagina's, wijziging vóór/na ophalen, ontbrekende eventmetadata en rerun van een oude run nadat de PR is gewijzigd. Bewijs dat ieder onzeker geval `full` selecteert.

## 3. Verwerp onvolledige bestandsrecords

Inspecteer `FileChange.paths()` en `classify()` in `src/classical_music/ci_policy.py`, plus de API-parser.

Gereproduceerd:

```python
classify([FileChange(status="renamed", path="data/a.yaml")], diff_complete=True)
# Huidig: data-only, ondanks ontbrekend oud pad.

classify([FileChange(status="modified", path="")], diff_complete=True)
# Huidig: data-only, doordat het lege pad wordt weggefilterd.
```

Herstel:

- Vereis een geldige niet-lege repositoryrelatieve bestandsnaam; accepteer geen ongeldige typen of structureel onbetrouwbare paden.
- Vereis bij renames een geldig oud pad en controleer beide kanten van de rename.
- Stel voor `copied` vast welke metadata GitHub daadwerkelijk garandeert; ontbrekende informatie die nodig is om veilig te classificeren moet `full` geven.
- Laat ongeldige records niet verdwijnen uit de bewijslast en laat de pure classifier niet ten onrechte slagen door een lege verzameling paden.
- Behoud ondersteuning voor geldige Git-bestandsnamen; beperk normalisatie tot wat nodig is voor betrouwbare classificatie.

Tests: lege/null/ongeldige bestandsnaam, rename zonder oud pad, leeg/ongeldig oud pad, geldige rename binnen de allowlist, rename over de grens in beide richtingen en ongeldige records naast geldige records. Test zowel pure classifier als API-adapter.

## 4. Bescherm ook wachtende main- en handmatige runs

Inspecteer `.github/workflows/validate.yml`.

Probleem: niet-PR-runs delen momenteel een concurrencygroep op `github.ref`. `cancel-in-progress: false` beschermt de lopende run, maar standaard kan een nieuwe run een bestaande wachtende run in dezelfde groep vervangen. Dat schendt de afspraak om alleen achterhaalde runs van dezelfde PR te annuleren.

Herstel:

- Behoud een workflow-specifieke, stabiele groep per PR voor PR-events.
- Gebruik voor niet-PR-events een unieke groep per run, bijvoorbeeld op basis van `github.run_id`, met zo nodig `github.run_attempt`. Zorg dat de naamruimte niet met PR-groepen kan botsen.
- Behoud annulering uitsluitend voor PR-events. Verschillende PR's, main-pushes en handmatige runs mogen elkaar niet annuleren.
- Werk de uitleg bij; claim niet dat alleen `cancel-in-progress: false` alle annulering uitsluit.

Verificatie: controleer YAML en expressies met geschikte beschikbare tooling. Voeg een betekenisvolle beleidscontrole toe die de fout bij gedeelde niet-PR-groepen kan ontdekken, zonder alleen dezelfde expressie in een test te kopiëren. Beschrijf daarnaast een echte Actions-proef met twee runs van dezelfde PR, twee verschillende PR's en minstens drie overlappende niet-PR-runs op dezelfde ref. Voer die externe proef niet zelf uit zonder toestemming; vermeld eerlijk dat statische tests GitHub-scheduling niet bewijzen.

## 5. Rapporteer selectie en werkelijke uitvoering afzonderlijk

Inspecteer `scripts/summarize_classification.py` en de volgorde/voorwaarden van de workflowstappen.

Probleem: de samenvatting meldt nu dat de testsuite heeft gedraaid terwijl de stap vóór pytest staat en met `always()` ook na eerdere fouten wordt uitgevoerd. Na een validatorfout kan pytest overgeslagen zijn, terwijl de samenvatting uitvoering claimt.

Herstel:

- Maak duidelijk onderscheid tussen geselecteerde route/geplande controles en werkelijk uitgevoerde controles.
- Genereer de uitvoeringssamenvatting na de relevante stappen, ook bij fouten, met stapstatussen en beschikbare meet-/JUnitgegevens als bewijs.
- Maak onderscheid tussen geslaagd, gefaald, overgeslagen, geannuleerd en onbekend/onvolledig. Ontbrekende artifacts zijn geen bewijs van succes.
- Rapporteer uitgevoerde testselectie, aantallen en failures/skips waar beschikbaar; beweer geen uitvoering op grond van uitsluitend de classificatie.
- Behoud de foutstatus van de validator/tests en de bestaande artifactuploads. Vermijd `continue-on-error` of `|| true` om checks groen te krijgen.
- Corrigeer de bewering dat `DataValidator.run()` zelf `PublicationValidator` uitvoert: in de beoordeelde versie gebeurt dat niet. Beschrijf nauwkeurig welke controles via tests en de afzonderlijke Pages-workflow lopen. Een samenvatting van `validate` mag geen onbekend resultaat van die andere workflow als geslaagd presenteren.

Tests: succesvolle full- en data-only-route, validatorfout gevolgd door overgeslagen pytest, pytestfout, setup/classificatiefout, ontbrekend/onvolledig rapport en onbekende status. Controleer ook dat `validate_data.py --json-output` bij validatiefouten JSON bewaart en nonzero teruggeeft, en dat `--json` compatibel blijft.

## Uitvoering en validatie

1. Inspecteer de genoemde bestanden, bestaande tests, `pyproject.toml` en de CI-meetdocumentatie. Noteer kort de aanpak en eventuele afwijkingen van deze review door nieuwere code.
2. Implementeer de kleinste samenhangende oplossing. Houd classificatiebeleid, API-bewijs en rapportage duidelijk gescheiden, zonder onnodig framework.
3. Draai eerst de gerichte regressietests en relevante bestaande tests. Gebruik de bestaande Python-omgeving en projectversievereisten. Installeer of upgrade niet ongevraagd de globale omgeving.
4. Draai daarna de volledige suite en de data-only-selectie zoals de workflow die uitvoert. Gebruik bestaande testisolatie en tijdelijke uitvoermappen; muteer geen canonieke data, publicatie of curatorbeslissingen. Als een controle niet uitvoerbaar is, rapporteer de concrete beperking in plaats van succes te claimen.
5. Controleer dat de werkelijke controles behouden zijn, rapporten beschikbaar blijven bij fouten en de required check niet kan slagen door een overgeslagen afhankelijke job.
6. Werk `docs/workflows/ci-benchmark.md` en `docs/workflows/scripts-user-manual.md` bij waar nodig. Controleer testaantallen opnieuw: de beoordeelde versie bevat 34 policytests en 17 scripttests, samen 51; 39 + 18 in de PR-tekst klopt niet. Nieuw toegevoegde tests veranderen deze aantallen.
7. Herhaal geen claim van bewezen CI-tijdwinst. De eerdere full-run had 453 geslaagde tests; dat bewijst niet de veilige werking van de nieuwe foutscenario's of de data-only-route. Voor een prestatievergelijking blijven drie vergelijkbare runs per meetconditie, mediaan, spreiding, vaste dataset, revisies, omgeving en artifacts nodig. Laat ontbrekende metingen expliciet open.

## Oplevering

Geef een beknopt eindverslag met:

- Per bevinding: oorzaak, reparatie, gewijzigde bestanden en bewijs door tests.
- Exact uitgevoerde controles, aantallen/resultaten en relevante artifacts; scheid lokale tests van echte GitHub Actions-verificatie.
- Resterende risico's of nog benodigde externe verificatie, inclusief een uitvoerbaar testscenario voor Lucas.
- Een voorstel voor bijgewerkte PR-beschrijving, zonder die zelf te publiceren.
- Status tegenover de acceptatiecriteria van #308 en een onderbouwd advies over mergegereedheid.

Laat alle wijzigingen lokaal en ongecommit voor Lucas' review. Sluit issue #308 niet, merge niets en wijzig de PR-status niet zelf.

## PR #314 review fixes (issue #308)

Fixes five correctness gaps identified in review of c8441c53:

1. **Completeness proof**: file-list pagination now verified against the PR's
   reported `changed_files` count and GitHub's documented 3000-file cap, with
   duplicate detection — a short/empty page alone no longer proves completeness.
2. **Revision binding**: classification is now bound to this run's expected
   head/base SHA (from `github.event.pull_request.head/base.sha`, not
   `github.sha`), checked before and after pagination.
3. **Incomplete records rejected**: empty/null/whitespace paths and
   renames/copies missing a previous path now fail closed instead of
   vacuously passing.
4. **Concurrency**: non-PR runs now get a unique group per run attempt, so a
   queued run can no longer be silently replaced.
5. **Planned vs. executed**: the job summary now separates the selected route
   (before execution) from real step outcomes and JUnit counts (after), and
   no longer misattributes PublicationValidator to the validator step.

115 new/rewritten tests (54 policy + 36 script + 19 reporting + 6 validator).
Full suite: 517 passed. Data-only route: 250 passed (unchanged from before
these fixes). Coverage of validation+migration unchanged (82.87%/79.07%).

Not yet measured: real GitHub Actions concurrency behavior, CI wall-clock
comparison (requires 3 runs/route per issue #308).
