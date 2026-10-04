# Piano review and verification

Base: `6139470` on main, including merged Chamber PR #262. This intake is on
`import/piano-playlist` and is submitted as a draft PR.

## Identity review

Reviewed movement boundaries against the archived Piano sheet and the complete
current source, then compared all groups against canonical Works, Performances,
Person names/aliases and other groups in the same intake. Catalogue numbers are
search hints, not automatic identity decisions. Same-title orchestral versions
of Ravel and Grieg were checked separately from the selected keyboard Works.
The existing Beethoven/Scharwenka arrangement Works are reused.

The independent checks found and corrected these material cases:

- Casella, not Ravel, wrote the Ravel pastiche: [BnF catalogue](https://catalogue.bnf.fr/ark:/12148/cb444895347).
- Nicoara, not Busoni, wrote Quasi sonatina: [composer's biography](https://www.victornicoara.com/bio-en).
- Dohnányi's Valses nobles is an independent concert transcription of Schubert:
  [Hyperion notes](https://www.hyperion-records.co.uk/dc.asp?dc=D_CDA67932).
- The Beethoven album also contains Schumann's canonic studies in Debussy's
  two-piano arrangement: [SOMM](https://somm-recordings.com/recording/beethoven-symphonies-volume-1/).
- Busoni's six Elegien and added Berceuse form the seven-piece selection:
  [Chandos](https://www.chandos.net/products/catalogue/CHAN%2020237).
- Egri's two-piano selection also credits Attila Pertis; its last waltz is not
  selected: [duo's discography](https://egri-pertis.com/en/recordings/).
- Hough's ornamented Nocturne Op. 9 No. 2 remains a third candidate in the same
  Work comparison, not an automatically accepted new Work:
  [Hyperion's explanation](https://www.hyperion-records.co.uk/dc.asp?dc=D_CDA68351/2).
- The legacy Brahms Op. 117, 118 and 119 headings incorrectly named individual
  pieces. The existing opus fields and Paul Lewis recording identify complete
  sets, corroborated by the [label track list](https://store.harmoniamundi.com/format/923164-brahms-late-piano-works-opp-116-119?lang=nl).
  Only these three Work titles/sources and their family titles change. No
  existing Performance or recommendation link changes.

The new tail is Shostakovich's Second Piano Sonata, already recommended with
Saskia Giorgini, and 40 Grieg selections with Peter Donohoe. Independent sources:
[Pentatone](https://www.pentatonemusic.com/product/mozart-shostakovich-concertos-for-piano-and-strings-piano-sonata/)
and [Chandos](https://www.chandos.net/products/catalogue/CHAN%2020464%282%29).

Remaining source questions are explicit in [identity-research.md](identity-research.md).
They include the K. 397 endings, Satie's sixth Nocturne and the D. 459/459A
boundary. Uncertainty is not silently converted into a new recommendation.

## Verification

- All 2,119 source positions, item IDs, track IDs, ISRCs, titles, durations,
  artists and album references were compared directly with the raw API artifact.
  No occurrence was lost. The raw artifact and ordered identities have SHA-256
  fingerprints in the manifest.
- Canonical validation with every new and changed identity activated:
  **0 errors, 0 action-required findings**, 115 existing background warnings.
- Piano inventory/publication audit passed: all references, selected listening
  anchors, public links and excerpt descriptions; pending candidates remain
  outside canonical Performance data.
- All **15 focused Piano and Chamber regression tests passed**. They include
  missing/changed occurrences, raw metadata changes, wrong-Work reuse, curator
  leakage, the embellished Nocturne and non-adjacent movement anchors.
- NL subscription STREAM rules were present for 1,562 source occurrences and
  absent for 557. This is catalogue metadata, not a playback test or a reason to
  reject the curator's musical selection.

The full GitHub validation/test and website workflows run on the draft PR.
Their live results are authoritative for completion; the focused local tests
above are not a claim that the entire test suite was run locally.
