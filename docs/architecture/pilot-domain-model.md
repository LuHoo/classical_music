# Pilot Domain Model

## Purpose

This document models a pilot set of twenty deliberately difficult cases drawn from the existing composer files.

The purpose is not to migrate the complete collection. The set is intended to test:

- permanent identifiers;
- canonical slugs;
- title and slug aliases;
- versions and revisions;
- arrangements and orchestrations;
- incomplete and completed works;
- ambiguous numbering;
- work-to-work relationships;
- the boundary between Work, Recording and Release.

The permanent identifiers below are generated test identifiers. If this pilot is adopted as production data, they may be retained; otherwise they must be treated as disposable and must not be referenced outside the pilot.

## Modelling conventions

Each case is represented as one or more entities. Internal relationships use permanent identifiers, never slugs.

The following provisional distinction is used:

- a **Work** is an abstract composition;
- a materially distinct authorised or editorial version may be a separate Work related to the base Work;
- an arrangement or orchestration is a separate Work when it has an independent performance identity;
- a completion or realisation of an unfinished work is a separate Work;
- a **Recording** represents a particular recorded performance;
- a **Release** is not created unless the source contains enough release-level metadata to identify a specific commercial or digital issue.

Streaming links in the source files generally identify tracks or albums, but do not by themselves provide enough metadata to model a reliable Release. They are therefore recorded as provisional source links rather than as definitive Release entities.

---

# Composer entities

```yaml
composers:
  - id: 01KXR8H939GK5XDBC3DFAAZ329
    slug: bach
    preferred_name: Johann Sebastian Bach

  - id: 01KXR8H939FCWJK1GRMM74WJMF
    slug: brahms
    preferred_name: Johannes Brahms

  - id: 01KXR8H939NACPDTZSD7R1BAT5
    slug: hindemith
    preferred_name: Paul Hindemith

  - id: 01KXR8H939TC9D0H4P81TCPG84
    slug: dvorak
    preferred_name: Antonín Dvořák

  - id: 01KXR8H93941KXYAE4ANP70NP0
    slug: bruckner
    preferred_name: Anton Bruckner

  - id: 01KXR8H9396B7C6ZEZT7ND5RGR
    slug: honegger
    preferred_name: Arthur Honegger

  - id: 01KXR8H939JX3SHGHKB22D7NH8
    slug: mahler
    preferred_name: Gustav Mahler

  - id: 01KXR8H939WCSVNRYVJDT58JAS
    slug: mendelssohn
    preferred_name: Felix Mendelssohn Bartholdy

  - id: 01KXR8H9393SKYNKQCQ1GBY2E3
    slug: prokofiev
    preferred_name: Sergei Prokofiev

  - id: 01KXR8H939P7154M9RBSYJA9A0
    slug: mozart
    preferred_name: Wolfgang Amadeus Mozart

  - id: 01KXR8H939W3D80Q1G4JQT9SE0
    slug: stravinsky
    preferred_name: Igor Stravinsky

  - id: 01KXR8H939N4MCMFFC6NA2AQ74
    slug: shostakovich
    preferred_name: Dmitri Shostakovich

  - id: 01KXR8H939VGQ28TX177PV6DY2
    slug: schubert
    preferred_name: Franz Schubert

  - id: 01KXR8H9390PTQ36F96QHJYHRH
    slug: saint-saens
    preferred_name: Camille Saint-Saëns

  - id: 01KXR8H939X2ABQDPYT060V4MH
    slug: zemlinsky
    preferred_name: Alexander von Zemlinsky

  - id: 01KXR8H939H0AHS3DK368BMCS0
    slug: vaughan-williams
    preferred_name: Ralph Vaughan Williams

  - id: 01KXR8H939M6ANC5SADG7H09S8
    slug: szymanowski
    preferred_name: Karol Szymanowski

  - id: 01KXR8H939TA58VTW22FRQBXZT
    slug: rautavaara
    preferred_name: Einojuhani Rautavaara

  - id: 01KXR8H939GA0EPPZGM7Q52B0M
    slug: bartok
    preferred_name: Béla Bartók
```

---

# Case 1 — Bach: two versions with separate catalogue suffixes

The early and revised versions of Brandenburg Concerto No. 5 are modelled as distinct Works under a common conceptual parent. The BWV suffixes already distinguish the versions.

```yaml
works:
  - id: 01KXR8H939M1JAH3D1D0CANVCA
    type: work
    composer_id: 01KXR8H939GK5XDBC3DFAAZ329
    slug: bach-brandenburg-concerto-5
    preferred_title: Brandenburg Concerto No. 5
    status: conceptual_parent

  - id: 01KXR8H939KACX57ZBXK34W035
    type: work
    composer_id: 01KXR8H939GK5XDBC3DFAAZ329
    slug: bach-brandenburg-concerto-5-bwv1050-2
    preferred_title: Brandenburg Concerto No. 5, early version
    catalogue:
      system: BWV
      number: "1050.2"
    relationships:
      - type: version_of
        target_id: 01KXR8H939M1JAH3D1D0CANVCA

  - id: 01KXR8H939KYMMW8E3GY93VHRM
    type: work
    composer_id: 01KXR8H939GK5XDBC3DFAAZ329
    slug: bach-brandenburg-concerto-5-bwv1050-1
    preferred_title: Brandenburg Concerto No. 5, revised version
    catalogue:
      system: BWV
      number: "1050.1"
    relationships:
      - type: revision_of
        target_id: 01KXR8H939KACX57ZBXK34W035
      - type: version_of
        target_id: 01KXR8H939M1JAH3D1D0CANVCA
```

**Decision tested:** catalogue numbers are included because the versions would otherwise collide.

---

# Case 2 — Brahms: original chamber version of Serenade No. 1

The familiar orchestral form and the original chamber-orchestra form are materially different versions.

```yaml
works:
  - id: 01KXR8H9394CSRJPTFV3GP18VX
    type: work
    composer_id: 01KXR8H939FCWJK1GRMM74WJMF
    slug: brahms-serenade-1
    preferred_title: Serenade No. 1
    catalogue:
      system: opus
      number: "11"

  - id: 01KXR8H939W3SP6A8BBFW27AWG
    type: work
    composer_id: 01KXR8H939FCWJK1GRMM74WJMF
    slug: brahms-serenade-1-original-chamber-version
    preferred_title: Serenade No. 1, original chamber-orchestra version
    relationships:
      - type: version_of
        target_id: 01KXR8H9394CSRJPTFV3GP18VX
```

**Decision tested:** the distinguishing phrase appears only for the non-default version.

---

# Case 3 — Hindemith: Hérodiade with and without recitation

The two forms are separate versions because the presence of recitation changes the performance work.

```yaml
works:
  - id: 01KXR8H939ZQD0NJ1XEY04FSJB
    type: work
    composer_id: 01KXR8H939NACPDTZSD7R1BAT5
    slug: hindemith-herodiade
    preferred_title: Hérodiade
    year: 1944
    status: conceptual_parent

  - id: 01KXR8H939FE1APDV5TZY08JN0
    type: work
    composer_id: 01KXR8H939NACPDTZSD7R1BAT5
    slug: hindemith-herodiade-without-recitation
    preferred_title: Hérodiade, version without recitation
    relationships:
      - type: version_of
        target_id: 01KXR8H939ZQD0NJ1XEY04FSJB

  - id: 01KXR8H939JW1A86W228ZDC483
    type: work
    composer_id: 01KXR8H939NACPDTZSD7R1BAT5
    slug: hindemith-herodiade-with-recitation
    preferred_title: Hérodiade, version with recitation
    relationships:
      - type: version_of
        target_id: 01KXR8H939ZQD0NJ1XEY04FSJB
```

**Decision tested:** words that distinguish the versions may be retained despite the general preference for conciseness.

---

# Case 4 — Dvořák: formal title before nickname

```yaml
works:
  - id: 01KXR8H939P73655X86QJN18K1
    type: work
    composer_id: 01KXR8H939TC9D0H4P81TCPG84
    slug: dvorak-symphony-9
    preferred_title: Symphony No. 9
    title_aliases:
      - From the New World
      - New World Symphony
    catalogue:
      system: Burghauser
      number: "178"
```

**Decision tested:** the nickname is an alias, not part of the canonical slug.

---

# Case 5 — Bruckner: Symphony No. 8, 1887 and 1890 versions

```yaml
works:
  - id: 01KXR8H939K8973FCATACG4H3V
    type: work
    composer_id: 01KXR8H93941KXYAE4ANP70NP0
    slug: bruckner-symphony-8
    preferred_title: Symphony No. 8
    catalogue:
      system: WAB
      number: "108"
    status: conceptual_parent

  - id: 01KXR8H9391MCHFFZFZP1VZTGY
    type: work
    composer_id: 01KXR8H93941KXYAE4ANP70NP0
    slug: bruckner-symphony-8-1887
    preferred_title: Symphony No. 8, 1887 version
    relationships:
      - type: version_of
        target_id: 01KXR8H939K8973FCATACG4H3V

  - id: 01KXR8H939Z3HA7CP41T12JH58
    type: work
    composer_id: 01KXR8H93941KXYAE4ANP70NP0
    slug: bruckner-symphony-8-1890
    preferred_title: Symphony No. 8, 1890 version
    relationships:
      - type: revision_of
        target_id: 01KXR8H9391MCHFFZFZP1VZTGY
      - type: version_of
        target_id: 01KXR8H939K8973FCATACG4H3V
```

**Decision tested:** years are the minimum stable distinction between versions.

---

# Case 6 — Honegger: title takes precedence over series designation

```yaml
works:
  - id: 01KXR8H939ZJVKGF0CPWCGQ52J
    type: work
    composer_id: 01KXR8H9396B7C6ZEZT7ND5RGR
    slug: honegger-pacific-231
    preferred_title: Pacific 231
    title_aliases:
      - Symphonic Movement No. 1
    catalogue:
      system: H
      number: "53"
```

**Decision tested:** the distinctive title is canonical; the generic series designation is an alias.

---

# Case 7 — Mahler: unfinished Symphony No. 10 and Gamzou realisation

```yaml
works:
  - id: 01KXR8H939YX24GN8G0M6P1R5J
    type: work
    composer_id: 01KXR8H939JX3SHGHKB22D7NH8
    slug: mahler-symphony-10
    preferred_title: Symphony No. 10
    completion_status: unfinished
    year: 1910

  - id: 01KXR8H939V7JME74JG5B2YPGN
    type: work
    composer_id: 01KXR8H939JX3SHGHKB22D7NH8
    slug: mahler-symphony-10-gamzou-realisation
    preferred_title: Symphony No. 10, realisation by Yoel Gamzou
    contributor:
      name: Yoel Gamzou
      role: completion
    relationships:
      - type: completion_of
        target_id: 01KXR8H939YX24GN8G0M6P1R5J
```

**Decision tested:** a later realisation is not the same Work as Mahler's unfinished score.

---

# Case 8 — Mendelssohn: conventional numbering versus historical “No. 1/2”

The two violin concertos are separate Works. Parenthetical historical numbering is normalised to canonical Arabic numbering.

```yaml
works:
  - id: 01KXR8H93995QYP1FYQSTYS40A
    type: work
    composer_id: 01KXR8H939WCSVNRYVJDT58JAS
    slug: mendelssohn-violin-concerto-1
    preferred_title: Violin Concerto No. 1
    key: D minor
    year: 1822

  - id: 01KXR8H939MR9WCZ9P8HGQA32E
    type: work
    composer_id: 01KXR8H939WCSVNRYVJDT58JAS
    slug: mendelssohn-violin-concerto-2
    preferred_title: Violin Concerto No. 2
    key: E minor
    catalogue:
      system: opus
      number: "64"
    year: 1844
```

**Decision tested:** numbering is canonical even when the source presents it parenthetically.

---

# Case 9 — Prokofiev: Symphony No. 4, two substantially revised versions

```yaml
works:
  - id: 01KXR8H939FNMNNGKKABEP6GAD
    type: work
    composer_id: 01KXR8H9393SKYNKQCQ1GBY2E3
    slug: prokofiev-symphony-4
    preferred_title: Symphony No. 4
    status: conceptual_parent

  - id: 01KXR8H9395EKK6ZK7188RAANJ
    type: work
    composer_id: 01KXR8H9393SKYNKQCQ1GBY2E3
    slug: prokofiev-symphony-4-1930
    preferred_title: Symphony No. 4, original version
    catalogue:
      system: opus
      number: "47"
    relationships:
      - type: version_of
        target_id: 01KXR8H939FNMNNGKKABEP6GAD

  - id: 01KXR8H939DGZBHX8SQ1HHW79K
    type: work
    composer_id: 01KXR8H9393SKYNKQCQ1GBY2E3
    slug: prokofiev-symphony-4-1947
    preferred_title: Symphony No. 4, revised version
    catalogue:
      system: opus
      number: "112"
    relationships:
      - type: revision_of
        target_id: 01KXR8H9395EKK6ZK7188RAANJ
      - type: version_of
        target_id: 01KXR8H939FNMNNGKKABEP6GAD
```

**Decision tested:** a new opus number does not create an unrelated Work; the two Works remain explicitly related.

---

# Case 10 — Mozart: unfinished Requiem and Süssmayr completion

```yaml
works:
  - id: 01KXR8H9397WNJCMCCAP38GPTM
    type: work
    composer_id: 01KXR8H939P7154M9RBSYJA9A0
    slug: mozart-requiem-k626
    preferred_title: Requiem
    catalogue:
      system: K
      number: "626"
    completion_status: unfinished

  - id: 01KXR8H939S04JJ1Q6BAN3DNGX
    type: work
    composer_id: 01KXR8H939P7154M9RBSYJA9A0
    slug: mozart-requiem-k626-sussmayr-completion
    preferred_title: Requiem, Süssmayr completion
    contributor:
      name: Franz Xaver Süssmayr
      role: completion
    relationships:
      - type: completion_of
        target_id: 01KXR8H9397WNJCMCCAP38GPTM
```

**Decision tested:** the catalogue number is included because it is the conventional identifier and improves disambiguation.

---

# Case 11 — Stravinsky: Petrushka 1911 and 1947 versions

```yaml
works:
  - id: 01KXR8H939TYGV3B77RRB5A9M1
    type: work
    composer_id: 01KXR8H939W3D80Q1G4JQT9SE0
    slug: stravinsky-petrushka
    preferred_title: Petrushka
    catalogue:
      system: K
      number: "012"
    status: conceptual_parent

  - id: 01KXR8H939V0B3EJ9W2632WPZ3
    type: work
    composer_id: 01KXR8H939W3D80Q1G4JQT9SE0
    slug: stravinsky-petrushka-1911
    preferred_title: Petrushka, 1911 version
    relationships:
      - type: version_of
        target_id: 01KXR8H939TYGV3B77RRB5A9M1

  - id: 01KXR8H9390DB486ZCQ7ZPJM1V
    type: work
    composer_id: 01KXR8H939W3D80Q1G4JQT9SE0
    slug: stravinsky-petrushka-1947
    preferred_title: Petrushka, 1947 version
    relationships:
      - type: revision_of
        target_id: 01KXR8H939V0B3EJ9W2632WPZ3
      - type: version_of
        target_id: 01KXR8H939TYGV3B77RRB5A9M1
```

**Decision tested:** established title spelling is retained; year distinguishes versions.

---

# Case 12 — Shostakovich: String Quartet No. 8 and Chamber Symphony

The Chamber Symphony is an arrangement of the quartet and therefore a separate Work.

```yaml
works:
  - id: 01KXR8H93954K2CVX0AM3GWKP7
    type: work
    composer_id: 01KXR8H939N4MCMFFC6NA2AQ74
    slug: shostakovich-string-quartet-8
    preferred_title: String Quartet No. 8
    catalogue:
      system: opus
      number: "110"

  - id: 01KXR8H9395FV6JEJ78MTBJBS9
    type: work
    composer_id: 01KXR8H939N4MCMFFC6NA2AQ74
    slug: shostakovich-chamber-symphony-op110a
    preferred_title: Chamber Symphony
    catalogue:
      system: opus
      number: "110a"
    relationships:
      - type: arrangement_of
        target_id: 01KXR8H93954K2CVX0AM3GWKP7
```

**Decision tested:** an arrangement is not folded into the source Work.

---

# Case 13 — Schubert: D 567 and D 568 as two versions

```yaml
works:
  - id: 01KXR8H939RJQZ434NHEN6Y2AK
    type: work
    composer_id: 01KXR8H939VGQ28TX177PV6DY2
    slug: schubert-piano-sonata-d568
    preferred_title: Piano Sonata
    catalogue:
      system: Deutsch
      number: "568"
    key: E-flat major

  - id: 01KXR8H939H03G8J9GAVYF0NE0
    type: work
    composer_id: 01KXR8H939VGQ28TX177PV6DY2
    slug: schubert-piano-sonata-d567
    preferred_title: Piano Sonata, first version
    catalogue:
      system: Deutsch
      number: "567"
    key: D-flat major
    relationships:
      - type: earlier_version_of
        target_id: 01KXR8H939RJQZ434NHEN6Y2AK
```

**Decision tested:** the historical catalogue identity is retained even though scholarship treats D 567 as the first version of D 568.

---

# Case 14 — Saint-Saëns: title before nickname

```yaml
works:
  - id: 01KXR8H9398V0N12DJQQKGSGD8
    type: work
    composer_id: 01KXR8H9390PTQ36F96QHJYHRH
    slug: saint-saens-symphony-3
    preferred_title: Symphony No. 3
    title_aliases:
      - Organ Symphony
    catalogue:
      - system: opus
        number: "78"
      - system: Ratner
        number: "176"
```

**Decision tested:** `saint-saens` uses ASCII; the nickname is not canonical.

---

# Case 15 — Zemlinsky: original song and Beaumont orchestration

```yaml
works:
  - id: 01KXR8H9399BM178HN563KBXJJ
    type: work
    composer_id: 01KXR8H939X2ABQDPYT060V4MH
    slug: zemlinsky-erdeinsamkeit
    preferred_title: Erdeinsamkeit
    original_scoring: voice and piano
    year: 1900-1901

  - id: 01KXR8H9398EHWM59Z1P5FBP3Z
    type: work
    composer_id: 01KXR8H939X2ABQDPYT060V4MH
    slug: zemlinsky-erdeinsamkeit-beaumont-orchestration
    preferred_title: Erdeinsamkeit, orchestration by Antony Beaumont
    year: 1999
    contributor:
      name: Antony Beaumont
      role: orchestrator
    relationships:
      - type: orchestration_of
        target_id: 01KXR8H9399BM178HN563KBXJJ
```

**Decision tested:** a posthumous orchestration is a separate Work with its own contributor.

---

# Case 16 — Vaughan Williams: A London Symphony and its revisions

The source lists revisions in 1918, 1920 and 1933 but does not establish that every version must immediately be a separate entity. The pilot models the general Work and records version candidates for later authority work.

```yaml
works:
  - id: 01KXR8H939VGN3NHRB92K2QV4B
    type: work
    composer_id: 01KXR8H939H0AHS3DK368BMCS0
    slug: vaughan-williams-symphony-2
    preferred_title: Symphony No. 2
    title_aliases:
      - A London Symphony
    version_candidates:
      - 1913
      - 1918
      - 1920
      - 1933
    modelling_status: requires_version_research
```

**Decision tested:** the model does not invent separate version entities until the boundaries are verified.

---

# Case 17 — Szymanowski: two different Hafiz song cycles

These are distinct Works, not versions, because the opus numbers, number of songs and scoring differ.

```yaml
works:
  - id: 01KXR8H939A2JK5Q13ADV88NRC
    type: work
    composer_id: 01KXR8H939M6ANC5SADG7H09S8
    slug: szymanowski-love-songs-of-hafiz-op24
    preferred_title: Love Songs of Hafiz
    catalogue:
      system: opus
      number: "24"
    scoring: voice and piano
    parts_count: 6

  - id: 01KXR8H939P411RJ6RR7FN55W4
    type: work
    composer_id: 01KXR8H939M6ANC5SADG7H09S8
    slug: szymanowski-love-songs-of-hafiz-op26
    preferred_title: Love Songs of Hafiz
    catalogue:
      system: opus
      number: "26"
    scoring: voice and orchestra
    parts_count: 8
```

**Decision tested:** same title does not imply same identity; opus numbers are required for disambiguation.

---

# Case 18 — Rautavaara: The Fiddlers in piano and string-orchestra forms

```yaml
works:
  - id: 01KXR8H9393563RJ0Y7HX6T4QY
    type: work
    composer_id: 01KXR8H939TA58VTW22FRQBXZT
    slug: rautavaara-the-fiddlers
    preferred_title: The Fiddlers
    original_title: Pelimannit
    status: conceptual_parent

  - id: 01KXR8H939X1EJ19J112JYBXTK
    type: work
    composer_id: 01KXR8H939TA58VTW22FRQBXZT
    slug: rautavaara-the-fiddlers-piano
    preferred_title: The Fiddlers, piano version
    year: 1952
    relationships:
      - type: version_of
        target_id: 01KXR8H9393563RJ0Y7HX6T4QY

  - id: 01KXR8H939CHMCYVPG7NFWAWCB
    type: work
    composer_id: 01KXR8H939TA58VTW22FRQBXZT
    slug: rautavaara-the-fiddlers-string-orchestra
    preferred_title: The Fiddlers, string-orchestra version
    year: 1972
    relationships:
      - type: arrangement_of
        target_id: 01KXR8H939X1EJ19J112JYBXTK
      - type: version_of
        target_id: 01KXR8H9393563RJ0Y7HX6T4QY
```

**Decision tested:** scoring can be the minimum distinguishing element.

---

# Case 19 — Bartók: ballet and two orchestral suites

The ballet and the short and long suites are three separate Works.

```yaml
works:
  - id: 01KXR8H939WX044Z6C36DCC246
    type: work
    composer_id: 01KXR8H939GA0EPPZGM7Q52B0M
    slug: bartok-the-wooden-prince
    preferred_title: The Wooden Prince
    catalogue:
      system: BB
      number: "74"
    form: ballet

  - id: 01KXR8H939RRABX13HX6PM0N3E
    type: work
    composer_id: 01KXR8H939GA0EPPZGM7Q52B0M
    slug: bartok-the-wooden-prince-short-suite
    preferred_title: The Wooden Prince, short orchestral suite
    catalogue:
      system: BB
      number: "74"
    relationships:
      - type: suite_from
        target_id: 01KXR8H939WX044Z6C36DCC246

  - id: 01KXR8H9395QSKDKP92W8MYDBN
    type: work
    composer_id: 01KXR8H939GA0EPPZGM7Q52B0M
    slug: bartok-the-wooden-prince-long-suite
    preferred_title: The Wooden Prince, long orchestral suite
    catalogue:
      system: BB
      number: "74"
    year: 1932
    relationships:
      - type: suite_from
        target_id: 01KXR8H939WX044Z6C36DCC246
```

**Decision tested:** a shared catalogue number does not collapse distinct derivative Works.

---

# Case 20 — Recording and release boundary

A source entry such as the recommended recording of Mahler's Symphony No. 5 identifies performers and a Tidal track, but usually omits the release label, catalogue number and release year needed by the current release-slug convention.

The source can therefore support a provisional Recording entity:

```yaml
recording:
  id: 01KXR8H939AVDTH89J2FEZ1432
  type: recording
  provisional_slug: dudamel-berlin-philharmonic-mahler-symphony-5
  work_id: null
  participants:
    - name: Gustavo Dudamel
      role: conductor
    - name: Berliner Philharmoniker
      role: orchestra
  source_links:
    tidal:
      url: http://www.tidal.com/track/229400428
      status: unverified
  modelling_status: incomplete
  missing:
    - recording_date
    - recording_venue
    - release_id
```

A definitive Release must not yet be created:

```yaml
release:
  status: not_modelled
  reason: >
    The source does not provide a verified label, catalogue number,
    release year and release-level identity.
```

**Decision tested:** a streaming URL is not treated as a stable Release identifier.

---

# Findings from the pilot

## 1. Conceptual parent Works are useful but require a policy decision

Cases such as Bach, Bruckner, Prokofiev and Stravinsky benefit from a common conceptual parent. Such parents improve navigation and relationship modelling, but they may not correspond to separately performable Works.

The domain model should therefore decide whether `conceptual_parent` is:

- a normal Work subtype;
- a Work Group entity;
- or a generated grouping without permanent identity.

A dedicated **Work Group** entity may ultimately be cleaner.

## 2. Version boundaries require authority research

The source files are sufficient to identify candidate versions, but not always to determine whether each candidate deserves its own Work. Vaughan Williams is the clearest example.

No automated import should create version entities solely from words such as `revised`, `version` or a list of years.

## 3. Catalogue numbers identify, but do not define, identity

The pilot contains:

- one Work with multiple catalogue references;
- several versions with one shared catalogue number;
- separate Works with different catalogue suffixes;
- derivative Works sharing the source Work's catalogue number.

Catalogue data must remain metadata rather than the internal key.

## 4. Arrangements and completions need contributors

A Work relationship alone is insufficient. The derived Work should record the arranger, orchestrator, editor or completer and that person's role.

## 5. Recording and Release cannot yet be reliably separated from most source lines

The existing Markdown files combine:

- Work metadata;
- performer credits;
- recommendation markers;
- Tidal links;
- occasional acquisition or review dates.

They do not consistently contain release-level metadata. Enrichment from MusicBrainz, Discogs or another authority will be necessary before reliable Recording and Release entities can be generated.

## 6. Recommendation should attach to a Recording, not to the source line

The diamond marker identifies an editorial recommendation, but the recommended object appears to be the cited performance or recording. During migration, the marker should become a Recommendation entity linked to the resolved Recording.

---

# Proposed next step

Before converting all composer files, use this pilot to decide four unresolved matters:

1. whether conceptual parent Works should become a separate `Work Group` entity;
2. when a version is materially distinct enough to receive its own Work identity;
3. whether arrangements always become separate Works or only when independently catalogued or performed;
4. which minimum metadata is required before a Recording or Release may be created.

Only after those decisions should an automated parser be written.
