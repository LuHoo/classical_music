# Samenvatting Analyse Issues #137, #143, #151 — background_suspicion Architectuur

**Datum**: 2026-08-27  
**Status**: ✅ Principes geïmplementeerd op main (PRs #160, #161, #162)  
**Doel**: Semantische analyse documenteren; implementatie erkennen  

---

## STATUS UPDATE: Implementatie op Main

**Deze analyse is geschreven voordat ontdekt werd dat PRs #160–#162 de kernarchitectuurprincipes al hebben geïmplementeerd.**

De volgende zijn officieel aangenomen op `main`:

### 1. **Architectuurprincipes (#161)**
Zie: [docs/architecture/architecture-principles.md](docs/architecture/architecture-principles.md)

**Principe 16: Background suspicions**
- Mogelijke afwijkingen in vertrouwde data blijven in rapporten, maar:
  - Mogen CI NIET doen falen
  - Mogen automatisch GEEN GitHub Issues maken
  - Worden ALLEEN actief bij expliciete selectie OF identity-changing operatie

**Principe 4: Identity gates**
- Nieuwe/materieel gewijzigde identiteiten vereisen verificatie
- Automation lost eerst op; curator beoordeelt alleen consequentiële onopgeloste vragen

### 2. **Duplicaatclassificatie met Autoriteit-bewijs (#160)**
Zie: [src/classical_music/authority/classifier.py](src/classical_music/authority/classifier.py)

- Classificeert clusters als: `confirmed_duplicate`, `distinct_works`, `catalogue_conflict`, `needs_authority_review`
- Bepaalt per cluster: `curator_review_required: bool`
- **Kritiek**: Behandelt NIET alle duplicaatwarschuwingen als werk; onderscheidt achtergrond van actionable

### 3. **Curator-on-Demand Validatie-workflow (#160)**
Zie: [reports/verification/curator-on-demand-review.md](reports/verification/curator-on-demand-review.md)

- Huidige stand: **0 action required**, 115 background suspicions, 74 autoriteit-clusters
- Duplicaatrapport: 36 Work Group-clusters (21 auto-opgelost, 15 achtergrond) + 38 Work-clusters (9 auto-opgelost, 29 achtergrond)
- **Operationeel**: Gebruik `python3 scripts/validate_data.py --identity-gate-id ENTITY_ID` voor expliciete activatie

---

## Validatie Initiële Hypothese

**Originele hypothese**: "Tooling behandelt `background_suspicion` als curatorwerk, wat ruis creëert."

**Bevinding**: ✅ **Hypothese was juist, maar oplossing was al in voorbereiding.**

De analysedocumenten hieronder identificeren correct:
- Bruckner-versies moeten GEEN curator-werk genereren
- Validatorwaarschuwingen zijn standaard background_suspicion
- Escalatie moet demand-driven zijn (expliciete activatie)
- Duplicaatdetectie moet classificeren, niet wholesale merges aanraden

**Wat op main werd toegevoegd**:
- Formele architectuurprincipes die dit onderscheid coderen
- Autoriteit-classifier die onderscheid in code implementeert
- Curator-on-demand workflow die onderscheid operationeel maakt
- `--identity-gate-id` mechanisme voor expliciete activatie

---

## Resterende Issues Status

### Issue #137: Bruckner Versie-grenzen

**Voor**: Validator waarschuwt herhaald; duplicaatrapport adviseert auto-merge  
**Nu**:
- Bruckner-versies: validatorwaarschuwingen blijven, maar geclassificeerd als **background_suspicion** (niet-blokkerend, niet-actionable)
- Principe 16 van toepassing: waarschuwingen doen CI NIET falen of GitHub Issues maken
- Geen curatorwerk gecreëerd tenzij expliciet geactiveerd via `--identity-gate-id`

**Status**: ✅ **Effectief opgelost door implementatie Principes 4 & 16**

**Aanbeveling**: 
- Sluit #137 met opmerking: "Curatorbesluit behouden; implementatie via architectuurprincipes op main (#160–#162)"

### Issue #143: Validator-waarschuwingen als Background Suspicion

**Voor**: Drie waarschuwingen behandeld als drie curator-taken  
**Nu**:
- Alexander Nevsky: apart gevolgd in #144; niet gedupliceerd
- Bach 0.91 gelijkenis: **background_suspicion** standaard; wordt actionable alleen als identity-changing operatie het expliciet activeert
- Principe 16 geldt: waarschuwingen zijn niet-blokkerend, maken geen Issues, doen CI niet falen

**Status**: ✅ **Geïmplementeerd in Principe 16**

**Aanbeveling**:
- Sluit #143 met opmerking: "Principe geïmplementeerd: zie Architectuurprincipes Principe 16; Curator-on-Demand workflow operationeel"

### Issue #151: Phase 2 Catalogus-verificatie

**Voor**: Scope suggereerde groot duplicaat-reconciliation werk  
**Nu**:
- Duplicaatclassificatie onderscheidt achtergrond van actionable
- Stravinsky K 066 fout: blijft datafout; lokale fix voldoende
- Hindemith ontbrekende catalogussen: **background_suspicion**; kan onderzocht worden maar niet actionable als merge-kandidaten
- Bruckner/Beethoven: behandeld als **background_suspicion** (niet-blokkerend); geen migratie-werk geïmpliceerd

**Scope-reductie**:
- Concreet werk: 1 datafout (Stravinsky K 066) + 5 onderzoeksitems + 1 documentatie-fix = 7 items
- Duplicaat-clusters: nu **background_suspicion** (niet-blokkerend); genereren geen geïmpliceerd werk

**Status**: ⚠️ **Gedeeltelijk — scope is juist maar vereist één verduidelijking**

**Aanbeveling**:
- Verduidelijken: Heeft PR #138 (Phase 2: AI-powered catalogue verification) updates nodig gezien classifier-werk op main?
- Zo ja: Update PR om duplicaatclassificatie uit te lijnen met on-demand activatie
- Zo nee: Voer alleen concrete data-items uit (datafout + onderzoek)
- Sluit #151 met opmerking: "Scope verfijnd per autoriteit-classifier; Phase 2 richt zich op data-compleetheid, niet duplicaat-reconciliation"

---

## Conceptueel Model (Geïmplementeerd op Main)

### Het Semantische Onderscheid

```
Validator waarschuwt (zelfde componist + titel)
  ↓
Autoriteit-classifier onderzoekt:
  - Catalogussen (verschillende WAB/opus? → distinct_works)
  - MusicBrainz IDs (zelfde MBID? → confirmed_duplicate)
  - Relaties (version_of? → catalogue_conflict)
  - Bewijssterkte → curator_review_required: bool
  ↓
Als curator_review_required == false:
  → Geclassificeerd als background_suspicion
  → Zichtbaar in rapport; NIET in Issues/CI-falen/werkrij
  ↓
Als curator_review_required == true:
  → Wordt actionable ALLEEN bij expliciete activatie
  → Gebruik `--identity-gate-id ENTITY_ID` om tot action_required te promoveren
```

**Wat NIET nodig was** (per LuHoo terugkoppeling):
- Aparte `curator_decisions.yaml` register
- Grote validator-refactor
- Data-model wijzigingen

**Wat NODIG was** (nu op main):
- Autoriteit-classifier logica ✅
- Principe-definities ✅
- Demand-driven activatie workflow ✅

---

## Resterende Architectuurwerk (Indien Gaten Overblijven)

### Vraag 1: Generieke Titel-classificatie
**Vraag**: Behandelt classifier Hindemith "Concerto" #1, #2, etc. correct?
- ✅ Zo geclassificeerd als `distinct_works` (andere work_group_ids): voldoende
- ⚠️ Zo geclassificeerd als `needs_authority_review`: overweeg of metagegevens-onderzoek kan voorafgaan

### Vraag 2: Work Group-gelijkenis
**Vraag**: Worden Work Group gelijkeniswarschuwingen nu correct onderdrukt voor vertrouwde data?
- ✅ Zo Principe 16 filtert ze naar achtergrond: voldoende
- ⚠️ Zo generen ze nog steeds Issues: verbetering nodig

### Vraag 3: Autoriteit-bewijssterkte
**Vraag**: Is classifier-bewijs voldoende voor on-demand activatie?
- ✅ Zo MusicBrainz IDs + catalogussen lossen meeste gevallen op: ga door met Phase 2
- ⚠️ Zo veel clusters nog onopgelost: gericht onderzoek nodig voordat activatie

---

## Conclusie

**De hypothese was juist**: Tooling behandelde background_suspicion als curatorwerk.

**De oplossing is nu geïmplementeerd**: PRs #160–#162 op main stellen vast:
- Formele principes (Principe 4, 16)
- Autoriteit-classifier (distinct_works, background_suspicion, action_required)
- Operationele workflow (--identity-gate-id voor expliciete activatie)

**Impact op issues**:
- #137 → Gesloten (besluit behouden via classifier)
- #143 → Gesloten (Principe 16 is nu geldende regel)
- #151 → Verfijnd (scope is data-compleetheid, niet duplicaat-reconciliation)

**Restend werk**: Verifieer classifier-voldoendheid; ga door met Phase 2 data-compleetheid zo checks passen.

---

## Originele Analyse (Hieronder) — Voor Referentie

De volgende secties vormen de originele conceptuele analyse, die geldig blijft en het denken achter de nu-geïmplementeerde principes uitlegt.

---

# ORIGINELE ANALYSE

## 1. Huidige Situatie (Pre-Implementatie)

### Issue #137: Bruckner Versie-/Concept-grenzen
- ✅ Curatorbesluit bestaat: Bruckner-versies zijn aparte Works
- ❌ Validator herhaalt waarschuwingen; geen mechanisme om dit op te slaan
- 📊 Endloze ruis; dezelfde beslissing wordt steeds gegenereerd

### Issue #143: Validator-waarschuwingen
- ✅ Principe gedefinieerd: "background suspicions by default"
- ❌ NIET geïmplementeerd in code
- 🎯 Alle DUP-* als "curator-werk" behandeld

### Issue #151: Phase 2-scope
- ❌ Grote migratiespanning gesuggereerd
- ✅ Eigenlijke werktaken: 1 datafout + 5 onderzoeksitems = 7 items
- 📉 Scope reduceert ~90% met principetoepassing

---

## 2. Het Ruis-Probleem

Tooling verwarrt vijf verschillende dingen:

| Type | Voorbeeld | Was | Zou Moeten |
|------|-----------|---|---|
| **Curatorbesluit** | Bruckner WAB 101/102 = apart | DUP-002 waarschuwing | Geen waarschuwing; opslaan als "decided" |
| **Achtergrond observatie** | Bach 0.91 titel-gelijkenis | DUP-003 waarschuwing | Onderzoek EERST; eskaleer alleen onopgelost |
| **Onderzoekswerk** | Hindemith: voeg opusnummer toe | DUP-002 waarschuwing | Markeert als "research-required", niet "curator-merge" |
| **Datafout** | Stravinsky K 066 → K 064 | DUP-002 waarschuwing | Repareer; voorkom herhaling |
| **Echte onzekerheidheid** | Prokofiev film vs. suite | DUP-002/003 waarschuwing | Curator-taak (maar alleen als echt onopgelost) |

**Huidige systeem**: Alle vijf rijen genereren dezelfde DUP-* waarschuwing. Geen onderscheid.

**Na implementatie**: Classifier onderscheidt; background suspicions worden niet als werk behandeld.

---

## Volgende Stappen

Controleer:
```bash
python3 scripts/validate_data.py --json
python3 scripts/generate_duplicate_review.py
```

1. Zijn Bruckner/Beethoven-clusters nu `distinct_works` of vergelijkbaar?
2. Zijn Hindemith/Stravinsky/Bach-clusters correct als background_suspicion?
3. Zijn clusters nog gemarkeerd `needs_authority_review` die background zouden moeten zijn?

Zo checks passen: **Geen verdere architectuurwerk nodig.** Ga door met Phase 2 data-compleetheid.
