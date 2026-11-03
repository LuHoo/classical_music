# Nieuwe-uitvoering-workflow (issue-template + registratie zonder `--work`)

Design issue #435. De curator-opener van een nieuw uitvoeringsissue hoeft alléén de
TIDAL-album-URL te kennen: work-id's zijn implementatiedetail en worden door het
script uit het album zelf opgelost.

## Workflow

1. Open een issue via het template **"Nieuwe uitvoering"** (`.github/ISSUE_TEMPLATE/new-performance.yml`); het enige verplichte veld is de TIDAL-album-URL.
2. Draai lokaal (copy-paste-blok staat in de issue-body):

   ```bash
   source ~/.tidal/env
   .venv/bin/python scripts/register_earmarked_recording.py "https://tidal.com/browse/album/<id>" --issue <nr> --comment
   ```

3. `--comment` plaatst het registratierapport als comment op het issue via de lokale `gh` CLI (bookkeeping, nooit een besluit). Zonder `gh` (of bij falen) is de Terminal-uitvoer de fallback; er gaat dan niets verloren.
4. Tracks zonder canoniek werk: voeg `--create-parking-issue` toe; het script opent dan — na een duplicaatcheck op de album-URL — een aparte parkeerissue met adviserend MusicBrainz-bewijs.

## Beslisboom (`--issue` zonder `--work`)

| Casus | Gedrag |
|---|---|
| ≥1 kandidaat-werk mét bestaande aanbeveling (track-anker) | Vergelijkingsroute: uniek → automatisch geselecteerd; meerdere → interactieve prompt "voor welk werk is dit issue?"; daarna binding + vergelijkingsplaylist `Curator <datum> Issue #<nr>` |
| Canoniek werk zónder bestaande aanbeveling | Geen playlist; het rapport meldt "direct adoption possible" — het album kán de aanbeveling worden (besluit via curatorrecord + PR, PR #339-patroon; het script schrijft nooit zelf een aanbeveling) |
| Track zónder canoniek werk | Parkeerissue met adviserende MusicBrainz-suggesties (#327-route: ISRC-keten; mint-voorstelmodus #331 als vervolg). Het kandidaat-album is nooit het bestaansrecht van het werk |
| Ambigue match | Fail-closed: stoppen en de ambiguïteit tonen (geen kandidaat, geen playlist) |

## Randvoorwaarden

- Fail-closed blijft leidend: geen automatische canonisatie, geen automatische aanbeveling; scripts registreren en stellen voor, de curator beslist (candidate-review-governance).
- GitHub-schrijfacties (`--comment`, `--create-parking-issue`) staan uitsluitend achter expliciete vlaggen en lopen via de lokale `gh`; comments triggeren de curator-listening-playlist-workflow niet (die vuurt op opened/reopened/labeled/edited, zie #366).
- Een mislukte parkeerissue-duplicaatcheck leidt nooit tot een tweede issue (fail-closed).
- `--dry-run` schrijft niets en plaatst geen comment of parkeerissue.
- Elke run met `--issue` maakt een nieuwe playlist aan; her-run dus alleen als de playlist (nog) niet bestaat (bekend volgpunt).

## Besluit na de registratie

- Vergelijkingsroute: `./curator <nr> <keuze> --apply`, daarna `./curator finish`; git blijft handmatig.
- Directe adoptie: curatorrecord + PR (PR #339-patroon).
- Parkeerissue: canonisatie via gewone review-wijziging, daarna de albumregistratie her-runnen; de track matcht dan automatisch.
