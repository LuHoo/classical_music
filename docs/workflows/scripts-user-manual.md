# User Manual — playlist-ingestion en curator scripts

Dit handboek beschrijft de scripts in PR #301 en de uitbreiding naar Chamber,
Piano en Best Classical. Voer voorbeelden uit vanuit de repositoryroot.
Voorbeelden zijn opdrachten die **jij** uitvoert; ze leggen geen curatorbeslissing vast
zolang je ze niet met `--apply` uitvoert. Nummers en keuzecodes moeten passen bij
het manifest in jouw checkout.

## 1. Wat is klaar en wat vraagt nog voorbereiding?

| Collectie | Beslissingen toepassen | Grens |
|---|---|---|
| Chamber | Geregistreerde keuzes met C-codes, bestaande expliciete A/B-aliases en `existing` | Eén aanbevolen uitvoering per werk |
| Piano | Geregistreerde keuzes met P-codes; momenteel #263 en #264 | Versieonderzoek #293 is geen uitvoeringskeuze |
| Best Classical | Adapter voor `window-*.json`, inclusief preview, apply, tellingen, bronbehoud en handmatige playlistacties | De bestaande drie vensters bevatten nog geen `recommendation_choices` met issuekoppelingen en stabiele unitcodes. Die moeten eerst worden beoordeeld en geregistreerd |
| Contemporary, Opera, Lieder | Uitbreidingsroute via hetzelfde keuzecontract | Nog geen ingestion, geregistreerd manifest of geteste auditadapter meegeleverd |

Best Classical is dus technisch ondersteund voor **geregistreerde keuzes**, maar
niet direct bedienbaar met de oude, alleen tekstueel beschreven alternatieven.
Het script verzint geen issuenummers, performers, keuzelabels of muzikale identiteiten.
Kandidaten voor hetzelfde werk over meerdere Best Classical-vensters blokkeren
toepassing; die vereisen eerst een afzonderlijk beoordeelde consolidatie en adapter.

## 2. Installatie

Benodigd: Python 3.13 of hoger en een lokale checkout van de code. Git is nodig
voor jouw eigen versiebeheer. Het beslisscript zelf werkt offline zonder GitHub-
of TIDAL-login.

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
./curator --help
```

`curator` is de shellwrapper voor `scripts/apply_curator_decision.py`. De wrapper
gebruikt eerst `CURATOR_PYTHON`, anders `.venv/bin/python`, anders `python3`.
Bijvoorbeeld: `CURATOR_PYTHON=/pad/naar/python3.13 ./curator 263 P078`.
De wrapper vindt de repository vanaf zijn eigen locatie. Andere scripts kunnen
relatieve invoer- en uitvoerpaden gebruiken: draai ze vanuit de repositoryroot.
Gebruik geen Python `-O`: die schakelt auditasserties uit en wordt door curator geweigerd.

## 3. Veilige workflow: Git blijft volledig handmatig

De voorbeelden gebruiken `git checkout`, passend bij Lucas' lokale Git 2.10.1.

1. Bekijk je huidige branch en eventuele lokale wijzigingen. Maak **zelf** je
   werkbranch vanaf de gewenste, actuele basis.
2. Luister naar de alternatieven en lees het issue en de bronregistratie.
3. Draai een preview. Controleer gekozen uitvoering, afwijzingen en eventuele
   vervanging van een bestaande aanbeveling.
4. Herhaal met `--apply` als de preview klopt. Dit past lokale bestanden aan.
5. Herhaal stappen 2–4 voor andere issues op dezelfde branch. Een schone Git-status
   is tussen beslissingen niet vereist; de volgende beslissing ziet de eerdere wijzigingen.
6. Controleer de gezamenlijke diff en nieuwe bestanden. Doe eventuele bronplaylistacties
   zelf in TIDAL en registreer de voltooiing afzonderlijk.
7. Doe zelf `add`, `commit`, `push`, PR-review en merge. Controleer daarna de normale
   publicatieworkflow. De CLI deployt geen website en sluit geen issues.

```bash
# Zelf uitvoeren in jouw checkout; kies zelf basis en branchnaam.
git status
git checkout -b curator-beslissingen

./curator 246 C093
./curator 246 C093 --apply --curator Lucas
./curator 263 P078
./curator 263 P078 --apply --curator Lucas

git status --short
git diff --check
git diff
# Kies expliciet de bestanden uit git status, inclusief nieuwe Performance/decision-bestanden.
git add <gecontroleerde-bestanden>
git diff --cached
git commit -m "Record reviewed curator decisions"
git push -u origin curator-beslissingen
# Open, review en merge vervolgens zelf de PR.
```

Een fout bij de tweede beslissing draait de eerste geslaagde beslissing niet
terug. Er is geen batchtransactie over meerdere commando's. Bestanden onder
`publication/` kunnen gegenereerd en Git-ignored zijn; volg de bestaande
publicatieworkflow en forceer ze niet automatisch in Git. Gebruik `git status`
om ook nieuwe, nog niet getrackte bestanden te bekijken: `git diff` toont die niet.

## 4. Volledige referentie van `./curator`

```text
./curator ISSUE CHOICE [--dry-run | --apply] [--curator NAME]
  [--decision-url URL] [--replace-existing] [--playlist-remove-unselected]
./curator ISSUE playlist-done [--dry-run | --apply] [--curator NAME] [--note TEXT]
```

| Parameter | Betekenis / standaard |
|---|---|
| `ISSUE` | Verplicht positief bedoeld issuenummer, zonder `#`; moet precies één geregistreerde keuze aanwijzen |
| `CHOICE` | Verplichte unitcode (`C093`, `P078`, geregistreerde Best Classical-code), expliciete alias of `existing` |
| `--dry-run` | Expliciete preview; ook de standaard zonder modusflag. Geen blijvende repositorywijzigingen |
| `--apply` | Schrijft na geslaagde validatie; kan niet samen met `--dry-run` |
| `--curator NAME` | Auteur van beslissing/bevestiging; standaard lokale gebruikersnaam |
| `--decision-url URL` | Optionele bestaande `https://github.com/LuHoo/classical_music/issues/ISSUE#issuecomment-N` als bron; alleen de vorm en issuekoppeling worden gecontroleerd, niet de inhoud/auteur |
| `--replace-existing` | Expliciete toestemming om een bestaande aanbeveling te vervangen; de oude volledige Performance wordt in het beslisrecord bewaard |
| `--playlist-remove-unselected` | Registreert exacte track-ID's voor **handmatige** verwijdering uit de bronplaylist; doet geen TIDAL-aanroep |
| `playlist-done` | Aparte actie voor het bevestigen van een eerder vastgelegde handmatige playlistactie |
| `--note TEXT` | Verplicht bij eerste `playlist-done`; beschrijf wat je werkelijk hebt gecontroleerd. Alleen geldig bij deze actie |
| `-h`, `--help` | Toon gebruiksinformatie |

A/B worden uitsluitend uit `choice_aliases` gelezen; nooit uit arrayvolgorde.
`existing` vereist precies één geregistreerde bestaande aanbeveling. `geen`,
`unresolved`, meerdere profielen tegelijk en herziening van afgesloten keuzes
zijn geen ondersteunde CLI-beslissingen. Gebruik daarvoor een beoordeelde wijziging.

```bash
./curator 240 A                         # bestaande Chamber-beslissing: geen wijziging
./curator 263 P078                      # Piano-preview
./curator 264 P182 --dry-run             # expliciete preview
./curator 242 existing                  # bestaande aanbeveling behouden
./curator 242 C035 --replace-existing    # vervanging alleen bekijken
./curator 242 C035 --replace-existing --apply --curator Lucas
```

Bij nieuwe besluiten worden Performance YAML, het oorspronkelijke manifest,
`reports/curator-decisions/issue-ISSUE.json`, rapporttellingen en gegenereerde
publicatie bijgewerkt. Historische brontracks, posities en ruwe metadata blijven
behouden. Piano's expliciet beoordeelde `listening_track_id` blijft de luisterlink;
anders is dat de eerste opgenomen track. Excerpt, profiel en versieaanduiding
worden overgenomen, niet bedacht. Best Classical krijgt actuele tellingen boven
het oorspronkelijke historische vensterrapport.

Dezelfde vastgelegde CLI-keuze opnieuw uitvoeren is een no-op. Een andere keuze
voor hetzelfde afgesloten issue stopt. Oude, handmatig vastgelegde groepsbesluiten
zijn niet automatisch omzetbaar naar individuele CLI-records. Een latere retry kan
geen playlistactie toevoegen aan een besluit dat zonder die actie is vastgelegd.

## 5. Bronplaylist handmatig bijwerken

```bash
./curator 263 P078 --playlist-remove-unselected
./curator 263 P078 --playlist-remove-unselected --apply --curator Lucas
# Verwijder nu zelf de genoemde IDs in TIDAL en behoud de gekozen uitvoering.
./curator 263 playlist-done --note "Afgewezen ID verwijderd; gekozen ID behouden"
./curator 263 playlist-done --apply --curator Lucas \
  --note "Afgewezen ID verwijderd; gekozen ID behouden"
```

Controleer de huidige playlist: snapshotposities zijn historisch. Gedeelde of
herhaalde verwijder-ID's blokkeren het plan omdat afzonderlijke voorkomens dan
moeten worden beoordeeld. `playlist-done` is jouw bevestiging, geen live verificatie.
Zonder eerdere actie of zonder eerste verificatienotitie stopt het script.
`--decision-url`, `--replace-existing` en `--playlist-remove-unselected` mogen niet
met `playlist-done` worden gecombineerd.

## 6. Luistervergelijkingen en inloggen

Deze route is gescheiden van beslissingen toepassen en kan **extern schrijven**.
Zie ook [luisterplaylistbeheer](curator-listening-playlists.md) voor de volledige
activatie, rechten, issue-events en herstelprocedure.

| Script | Parameters | Effect |
|---|---|---|
| `create_curator_listening_playlist.py` | `ISSUE`; `--apply`; `--recover-playlist-id UUID`; `--discover` | Standaard leest het GitHub en previewt een plan. `--apply` maakt/vult een aparte TIDAL-vergelijkingsplaylist en schrijft een GitHub-issuecomment als journaal |
| `tidal_playlist_login.py` | `--client-id ID` (anders `TIDAL_CLIENT_ID`); één van `--setup-curator-playlists`, `--repair-spartacus`, `--repair-one-second`, `--repair-confirmed` | Interactieve browserlogin. Setup bewaart een refreshgrant als repositorysecret; reparatiemodi wijzigen de bronplaylist. Zonder modus start een schrijfproef met een tijdelijke playlist |

`--recover-playlist-id` is uitsluitend voor de geïdentificeerde vergelijkingsplaylist
na een onzeker antwoord, nooit een bronplaylist-ID. `--discover` is een workflowhulp
met `GITHUB_EVENT_NAME`, `GITHUB_EVENT_PATH`, `GITHUB_OUTPUT` en bij handmatige
workflowdispatch `INPUT_ISSUE`; het schrijft de gevonden issues naar het workflowoutputbestand.
`GITHUB_TOKEN` moet passende leesrechten hebben, en bij apply ook issue-schrijfbevoegdheid.
De workflow gebruikt TIDAL-appgeheimen en een gebruikersgrant. Zet tokens niet in
Git, screenshots of rapporten. Setup vereist `gh`-login met rechten om het secret te zetten.

```bash
GITHUB_TOKEN="$(gh auth token)" .venv/bin/python scripts/create_curator_listening_playlist.py 263
.venv/bin/python scripts/tidal_playlist_login.py --setup-curator-playlists --client-id "$TIDAL_CLIENT_ID"
```

Activatie vereist de workflow op de default branch, de geregistreerde callback
`http://127.0.0.1:8765/callback` en de TIDAL-grant voor dezelfde app. Deze ontwikkeling
heeft geen live playlist aangemaakt of autorisatie uitgevoerd. Een bestaande
opname buiten de snapshot vereist voor de vergelijking een gecontroleerde complete
tracklijst in `existing_performance_tracks`; één canonieke luisterlink is onvoldoende.

### Omgevingsvariabelen voor TIDAL

| Variabele | Gebruikt voor |
|---|---|
| `TIDAL_ACCESS_TOKEN` | Bestaand catalogusaccesstoken; anders gebruiken catalogusscripts de appgegevens hieronder |
| `TIDAL_CLIENT_ID`, `TIDAL_CLIENT_SECRET` | Appautorisatie voor cataloguslezingen; dezelfde app bij luisterplaylistsetup |
| `TIDAL_USER_ACCESS_TOKEN` | Gebruikersrechten voor playlistlezingen/schrijfacties in live pilot, reparaties en luisterplaylistbeheer |
| `TIDAL_USER_REFRESH_TOKEN` | Refreshgrant voor luisterplaylistbeheer, normaal als GitHub Actions-secret opgeslagen door setup |
| `GITHUB_TOKEN` | GitHub lezen en, uitsluitend in de externe apply-route, het issuejournaal schrijven |

Een catalogustoken geeft geen toestemming om gebruikersplaylists te wijzigen.
Het offline beslisscript `./curator` gebruikt geen van deze tokens.

## 7. Ingestion en controles

Alle Python-commando's hieronder hebben prefix `.venv/bin/python scripts/`.
Controles wijzigen geen canonieke muziekdata, maar kunnen rapporten of de lokale
gegenereerde `publication/` vernieuwen. Zij voeren geen Git-opdrachten uit.

| Script | Parameters en standaardwaarden | Gebruik / uitvoer |
|---|---|---|
| `fetch_tidal_playlist.py` | `PLAYLIST`; `--limit 100`; `--country NL`; `--output reports/tidal-playlist/source.json` | Leest TIDAL-catalogus; bewaart JSON buiten `data/`. Geen automatische canonical ingestion. Controleer `source_complete` |
| `analyse_tidal_scale.py` | `SOURCE`; vereist `--output PATH`; optioneel `--inventory PATH`; `--start 34`; `--end 333`; `--source-run 37024628787` | Analyse van een afgebakende bronselectie. Standaarden stammen uit de oorspronkelijke proef, dus geef voor nieuwe bronnen je eigen grenzen op |
| `check_chamber_import.py` | Geen parameters | Volledige Chamber-broncontrole, curatorrecords en publicatiegeneratie |
| `check_piano_import.py` | Geen parameters | Piano-controle inclusief ruwe metadatafingerprint, luisterankers, versieonderzoek en curatorrecords |
| `check_tidal_window_import.py` | `--manifest PATH`, standaard `reports/playlist-import/best-classical/window-333-1998.json` | Controle van één Best Classical-venster, canonieke verwijzingen, geregistreerde keuzes en publicatie |
| `validate_data.py` | `--json`; herhaalbaar `--identity-gate-id ID` | Brede canonieke validatie; JSON naar stdout of leesbare tabel. Exit 1 bij fouten |
| `generate_publication_site.py` | Geen parameters | Valideert en bouwt `publication/` opnieuw; vervangt de bestaande gegenereerde inhoud |
| `check_publication_links.py` | `--site-dir _site`; `--config _config.yml` | Controleert lokale links in een eerder gebouwde Jekyll-site |
| `summarize_validation_report.py` | `REPORT`; `--limit 10` | Vat opgeslagen validatie-JSON samen |

```bash
.venv/bin/python scripts/fetch_tidal_playlist.py <playlist-id> --limit 100 --country NL --output reports/tidal-playlist/source.json
.venv/bin/python scripts/check_piano_import.py
.venv/bin/python scripts/check_tidal_window_import.py --manifest reports/playlist-import/best-classical/window-1999-4000.json
.venv/bin/python scripts/validate_data.py --json > reports/validation/local.json
```

Maak de uitvoermap voor shellredirecties zelf eerst aan. `./curator` doet staged
validatie voor iedere beslissing: daarvoor hoef je niet iedere keer de volledige
testsuite of brede identiteitsanalyse te draaien. Gerichte regressies voor deze route:

```bash
.venv/bin/python -m pytest tests/test_curator.py tests/test_curator_collections.py \
  tests/test_chamber_import.py tests/test_piano_import.py \
  tests/test_original_arrangement_decisions.py tests/test_curator_listening.py \
  --no-cov -o addopts='' -q
```

## 8. Overige onderhouds- en migratiescripts

Deze inventaris omvat ook scripts die normaal niet nodig zijn om curatorbeslissingen
vast te leggen. Gebruik historische herstelproeven niet als algemene ingestiontool.

| Script | Parameters / standaardwaarden | Effect en grens |
|---|---|---|
| `check_tidal_links.py` | `--repo-root` huidige map; `--output reports/tidal-maintenance/latest.json`; `--previous PATH`; `--recovery-urls PATH`; `--previous-candidates PATH`; `--country NL`; `--use-api`; `--timeout 15`; `--delay 0.5`; `--limit N`; `--apply` | Leest links en maakt rapporten; met `--apply` schrijft het geverifieerde canonieke URL-vervangingen. Geen muzikale curatorbeslissing |
| `run_tidal_api_check.py` | `--limit 5` (1–50); `--output reports/tidal-maintenance/latest.json` | Beperkte geauthenticeerde catalogusproef en linkrapport; geen bronplaylistmutaties |
| `scan_tidal_playlist.py` | `--output reports/tidal-maintenance/full-playlist-scan.json` | Leest de vaste Best Classical-bron en schrijft JSON plus Markdown; geen generieke playlistparameter |
| `playlist_live_pilot.py` | `--test-write`; `--output reports/tidal-maintenance/playlist-live-pilot.json` | Zonder flag leesproef; met flag schrijfproef op een wegwerpplaylist met gebruikersautorisatie |
| `playlist_recovery_pilot.py` | Geen parameters | Historische cataloguszoekproef voor vaste ontbrekende tracks; schrijft rapport, geen bronplaylistmutaties |
| `repair_tidal_playlist.py` | `--journal PATH`; één van `--spartacus`, `--duration-one-second`; zonder modus de eerder bevestigde reparatiebatch | **Live bronplaylistreparatie**, geen dry-runmodus. Vaste historische goedkeuringsrapporten, ID's en journaalcontroles; niet onderdeel van curatorkeuzes |
| `parse_docs.py` | herhaalbaar `--composer SLUG` of `--all` | Leest componist-Markdown; schrijft `generated/migration/source-records.json` |
| `migrate.py` | herhaalbaar `--composer SLUG` of `--all`; `--dry-run` | Classificeert migratiekandidaten; zonder dry-run schrijft het gegenereerde migratievoorstellen, geen curatoracceptatie |
| `generate_review_report.py` | `--input generated/migration/migration-summary.json` | Schrijft lokale reviewrapporten en issueconcepten onder `reports/review/`; plaatst geen GitHub-issues |
| `compare_migration_runs.py` | `SUMMARY1 SUMMARY2` | Vergelijkt aantallen, categorieën en Work-ID-verzamelingen; geen volledige bytevergelijking. Exit 0 gelijk volgens deze criteria, 1 verschil, 2 ongeldige invoer |
| `generate_duplicate_review.py` | herhaalbaar `--identity-gate-id ID` | Schrijft het vaste rapport `reports/validation/duplicate-review-2026-08-23.md` |
| `classify_authority_duplicates.py` | `--json-output reports/verification/authority-duplicate-classification.json`; `--markdown-output reports/verification/authority-duplicate-classification.md`; herhaalbaar `--identity-gate-id ID` | Lokale classificatie/rapportage van identiteitsvragen |
| `classify_prokofiev_alignment.py` | `INPUT`; vereist `--json-output PATH` en `--markdown-output PATH` | Gerichte Prokofjev-analyse; geen algemene curatorbeslissing |

Voorbeelden zonder bronplaylistmutaties:

```bash
.venv/bin/python scripts/check_tidal_links.py --limit 5
.venv/bin/python scripts/parse_docs.py --composer debussy
.venv/bin/python scripts/migrate.py --composer debussy --dry-run
.venv/bin/python scripts/generate_review_report.py
.venv/bin/python scripts/compare_migration_runs.py first.json second.json
.venv/bin/python scripts/summarize_validation_report.py reports/validation/local.json --limit 5
```

Argparse/Typer-scripts bieden `--help`. Scripts zonder argumentparser
(`check_chamber_import.py`, `check_piano_import.py`, `generate_publication_site.py`,
`playlist_recovery_pilot.py`) voeren hun vaste taak uit, ook wanneer je `--help`
meegeeft. Lees daarvoor dit handboek en de bron; gebruik `--help` daar niet als proef.

## 9. Best Classical registreren en volgende playlists aansluiten

Het contract staat in dezelfde beoordeelde bronmanifesten, zonder tweede catalogus.
Voeg pas na inhoudelijke controle het volgende toe:

- Een stabiele, unieke `unit_id` per kandidaat, `work_id`, `curator_issue`,
  `positions`, volledige geordende `tracks`, beoordeelde `performers` of
  `candidate_performers` als objecten met `name` en zo nodig `role`.
- Een `recommendation_choices`-entry met `issue_url`, `work_id`, `composer`,
  `title`, `units`, `existing_performances` en `decision: null`.
- Alleen expliciet gepubliceerde labels in `choice_aliases`. Gebruik bestaande
  canonieke IDs bij `existing_performances`, ook wanneer die buiten de snapshot vallen.
- Onafhankelijke Work-identiteit, excerpt/profiel/versie indien van toepassing;
  complete bronverantwoording en correcte oorspronkelijke tellingen.

Voorbeeld **schema**, geen uit te voeren echte issuekeuze:

```json
{
  "work_id": "reviewed-work-id",
  "composer": "Reviewed composer",
  "title": "Reviewed work title",
  "units": ["BC001", "BC002"],
  "existing_performances": [],
  "choice_aliases": {"A": "BC001", "B": "BC002"},
  "issue_url": "https://github.com/LuHoo/classical_music/issues/REPLACE_WITH_REAL_NUMBER",
  "decision": null
}
```

De registratie moet alle kandidaten voor dat werk omvatten en mag niet conflicteren
met een ander manifest. Het huidige Best Classical-pad controleert één venster;
voor verspreide kandidaten is verdere consolidatie nodig. Beoordeel oude
`credited_artists` expliciet tot performers; vrije providertekst wordt niet
stilzwijgend als curatorbewijs gepromoveerd.

Architectuur: `playlist_choices.py` bevat `Intake` en de expliciete `INTAKES`-registratie,
issue-resolutie, windowtellingen en keuzevalidatie. `curator.py` bevat de gedeelde
beslis- en schrijflogica. `chamber_import.py`, `piano_import.py` en
`best_classical_import.py` bewaken hun eigen bronregels. Voor Contemporary, Opera
of Lieder: voeg een beoordeeld manifest, registratiepatroon, rapportadapter en
specifieke audit toe; test bronbehoud, alle gebruikte beslismodi, preview/apply,
herhaling, ambiguïteit en luisterplanning. Alleen een naam aan `INTAKES` toevoegen
is onvoldoende. `curator_listening.py` kan hetzelfde keuzecontract lezen, maar
luisterondersteuning bewijst op zichzelf geen ondersteuning voor toepassen.

### Gerichte validatie versus historisch vensterrapport

Best Classical valideert bij een beslissing de venstertellingen, geregistreerde
keuzes en de huidige canonieke publicatie. De zelfstandige
`check_tidal_window_import.py` blijft de volledige historische import controleren.
Die kan al vóór een nieuwe beslissing falen door latere cataloguswijzigingen:
op de PR-basis verwijst venster 333–1998 bijvoorbeeld naar het inmiddels ontbrekende
`gustav-holst-hammersmith-playlist-1508.yaml`. De CLI herstelt of verbergt die
historische verwijzing niet. Een geslaagde curator-preview is daarom geen bewijs
dat elk oud importrecord nog naar een bestaande aanbeveling verwijst.

## 10. Fouten, herstel en beperkingen

| Melding / situatie | Betekenis en actie |
|---|---|
| Geen unieke geregistreerde keuze | Controleer branch, issuekoppeling en intakeadapter; Best Classical eerst registreren |
| Onbekende keuze | Gebruik de weergegeven unitcodes/aliases; A/B bestaan alleen na expliciete registratie |
| Bestaande aanbevelingen verschillen | Canonieke data zijn gewijzigd sinds de beoordeling; herbeoordeel de registratie |
| `--replace-existing` vereist | Bekijk het te vervangen record en geef de flag pas na die controle |
| Verwijzing vanuit andere intake | Vervanging zou bronverwijzingen breken; gezamenlijke handmatige beoordeling nodig |
| Kandidaten in ander venster | Geen gedeeltelijke Work-keuze toepassen; consolideer en beoordeel eerst |
| `.curator.lock` bestaat | Controleer of een andere apply loopt. Verwijder alleen een achtergebleven lock nadat vaststaat dat er geen schrijver actief is |
| Inputs gewijzigd tijdens validatie | Preview opnieuw; geen oude berekening forceren |
| Audit of publicatie faalt | De voorgestelde lokale wijziging wordt niet geïnstalleerd; herstel de concrete bron-/canonieke fout |
| Computer crasht tijdens apply | Controleer Git-diff, nieuwe bestanden en beslisrecord voordat je herhaalt. Meerdere bestanden vormen geen crashbestendige database-transactie |

De CLI gebruikt tijdelijke bestanden voor validatie, een schrijverslot, controle
op gelijktijdige wijzigingen en rollback bij gewone schrijffouten. Dit beschermt
niet tegen iedere stroomstoring of tegen handmatige wijzigingen vanuit andere
programma's. Bewaar je eerdere werk en herstel alleen de betrokken bestanden;
een algemene reset kan ook andere, nog niet gecommitte beslissingen verwijderen.

Succes retourneert 0; verwachte curator- of invoerfouten retourneren 2 met een
melding. De brede standalone audits gebruiken asserties en kunnen bij falen een
traceback/exit 1 geven. Geen van deze curatorcommando's maakt een branch, commit,
push, PR of merge. Handmatige TIDAL-acties en de externe luisterplaylistworkflow
hebben hun eigen, hierboven beschreven effecten.
