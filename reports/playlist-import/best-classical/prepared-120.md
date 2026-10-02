# Best Classical: identification and import preparation for 120 tracks

## Result and scope

The curator authorised the next identification/import-preparation step on
2026-10-02 at 19:33 Europe/Amsterdam. All **120 tracks / 33 selected musical
units** are represented by explicit proposed entities, outside canonical data.
The proposal contains **9 new composer Persons, 32 Work Groups, 32 Works and
33 Performances**. Shostakovich's Violin Concerto No. 2 reuses its existing Work.
No additional recommendation is published, replaced, merged or deployed.

- `prepared-120.yaml`: the exact proposed canonical records, grouped by entity
  type; these are not files installed under `data/`.
- `prepared-120.json`: source hash, positions, all 120 track IDs/ISRCs, source
  album/barcode/release-date evidence, primary sources and validation results.
- The retained source is the stable live snapshot from
  https://github.com/LuHoo/classical_music/actions/runs/37024628787.

This step did not re-fetch the playlist or repeat a complete test/CI cycle.
Musical acceptance comes from the curator's explicit playlist instruction.
Identity/coverage decisions and the proposed classification are recorded here.

## Prepared selections

| Playlist positions | Work(s) | Proposed interpretation | Tracks |
|---|---|---|---:|
| 34–35 | Pärt: Tabula Rasa | Capuçon, Sochard, Bellom / Lausanne chamber orchestra | 2 |
| 36–42 | Zemlinsky: Lyric Symphony, Op.18 | Marc, Hagegård / Concertgebouw / Chailly | 7 |
| 43–49 | Zemlinsky: Symphonic Songs, Op.20 | White / Concertgebouw / Chailly | 7 |
| 50 | Zemlinsky: Psalm 83 | Slovak Philharmonic Chorus / Vienna Philharmonic / Chailly | 1 |
| 51–69 | Bartók: The Wooden Prince, Sz.60; Dance Suite, Sz.77 | WDR / Măcelaru | 19 |
| 96–116 | Sibelius: Symphonies 1, 2, 3, 5, 6, 7; Tapiola | Oslo / Mäkelä; Symphony 3 is movement I only | 21 |
| 117–119 | Sibelius: Three Late Fragments, Virtanen realisation | Oslo / Mäkelä | 3 |
| 120–125 | Schubert: Unfinished, D.759; Great, D.944 | Le Concert des Nations / Savall | 6 |
| 126–131 | Martinů: Violin Concertos 2, H.293, and 1, H.226 | Zimmermann / Bamberg / Hrůša | 6 |
| 132–138 | Rachmaninoff: Symphony 1, Op.13; Symphonic Dances, Op.45 | Philadelphia / Nézet-Séguin | 7 |
| 139 | Mark Simpson: Geysir | Simpson and the credited wind/bass ensemble | 1 |
| 208–210 | Shostakovich: Violin Concerto 2, Op.129 | Ibragimova / Svetlanov orchestra / Jurowski | 3 |
| 211–226 | Schmidt: Symphonies 1–4; Notre Dame (Intermezzo only) | Frankfurt Radio Symphony / Paavo Järvi | 16 |
| 227–235 | Vaughan Williams: Sinfonia antartica; Symphony 9 | BBC / Brabbins; Watts and chorus in Antartica | 9 |
| 320–331 | Poulenc: Piano Concerto, FP146; Trio, FP43; Concert champêtre, FP49; Oboe Sonata, FP185 | Bebbington, Roberts, Davies / RPO / Latham-Koenig as appropriate | 12 |
| **Total** | **33 units** | | **120** |

Each multi-Work album produces one Performance per selected Work, not one
Performance per album or movement. Only the listed playlist positions contribute
accepted curation. Sibelius Symphony 4 and the remaining movements of Symphony 3,
Bartók's solo violin sonata on BIS-2457, and Pärt's other album works are excluded
from this proposal because they were not selected in the analysed window.

## Identity, coverage and modelling decisions

**Global authority.** Reuse actual canonical Person IDs for Pärt
(`3933294105514c1885644d1099a7006b`), Bartók
(`388053797e01483593f1e62c6dd407ab`) and Shostakovich. Nine absent composer
Persons are proposed after the global Person/artist inventory check. Existing
artist authority, including Paavo Järvi, is reused where matched. Other performers
use permitted named credits; there is no new performer-identity catalogue.
Mark Simpson is the composer/clarinettist of Geysir, not Robert Simpson; his
proposed Person is reused as the clarinet credit rather than creating two people.

**Explicit partial selections.** Sibelius Symphony 3 receives
`excerpt: First movement only`. Notre Dame is modelled as the parent opera,
with `excerpt: Intermezzo only` on its Performance. Schubert's two-movement
Unfinished is the recognised unfinished composition as recorded, with no invented
completion. Sibelius Symphony 7's four source tracks are sections of the same
one-movement composition, not four Works.

**Virtanen fragments.** The proposed Work is the named, realised set
*Three Late Fragments (Timo Virtanen realisation)*, with HUL1325, HUL1326/9 and
HUL1327/2 evidence and explicit version attribution. It has its own Work Group.
The primary Hyperion work page and independently released Chandos programme
recognise this set; the latter describes Virtanen's preparation of late sketches.
No complete Symphony 8 is created, and the sketches' association with that lost
symphony remains uncertain. This is an explicit repertoire modelling proposal,
not a claim that the original manuscripts constituted a completed three-part Work.

**Poulenc keyboard tradition.** Resonus identifies Bebbington's Concert champêtre
as the piano version. The proposed Performance has `profile: piano`. The general
composition Work is retained; replacing harpsichord with piano does not, by itself,
justify a separate artistic Work under the repository's rules. Chamber entries
use only the credited chamber performers, not the album's orchestra/conductor.

**General versions.** The Wooden Prince, Sibelius Symphonies 1 and 5, and
Rachmaninoff Symphony 1 use general composition Works with
`version_assignment: unspecified` on the proposed Performances. The evidence
identifies the compositions and interpretations but does not justify a particular
revision/edition assignment. The Wooden Prince selection is the full ballet,
not its separately extracted suite. No unspecified-version fallback conceals
the explicitly identified Virtanen realisation or turns an excerpt into a full Work.

**Recording dates.** Source release dates are retained in provenance, not copied
blindly into Performance years. The proposal uses recording years only where
primary sources establish them: Savall/Schubert 2021; Martinů Concerto 1 in 2018
and Concerto 2 in 2019; Brabbins/Vaughan Williams 2022. Unknown session years are
omitted. Digital and physical barcodes can differ; related label editions support
composer/recording identity without a false claim of exact barcode equality.

**Availability.** The curator reports playback from the existing playlist. Empty
API rights lists are operational uncertainty, not rejection or an import blocker.
No runtime availability fields are proposed in canonical YAML.

## Primary evidence by recording

| Source | Evidence used |
|---|---|
| [Warner/Erato: Pärt](https://www.warnerclassics.com/release/tabula-rasa) | Composer, Lausanne ensemble, featured soloists, digital barcode |
| [Decca: Zemlinsky](https://www.deccaclassics.com/en/catalogue/products/zemlinsky-lyrische-symphonie-7275), [Chailly box](https://www.deccaclassics.com/en/catalogue/products/zemlinsky-lyrische-symphonie-chailly-433), [composer catalogue](https://www.zemlinsky.at/EN/Catalogue-of-Compositions/catalog.pdf) | Work/catalogue identities, singers, recording family; track-specific orchestras/chorus from retained source |
| [Linn/Outhere: Bartók](https://outhere-music.com/en/albums/bartok-wooden-prince-dance-suite) | Full ballet/Dance Suite programme, WDR/Măcelaru; CKD714 label catalogue |
| [Decca: Sibelius](https://www.deccaclassics.com/en/catalogue/products/sibelius-klaus-maekelae-12615), [release announcement](https://www.deccaclassics.com/en/artists/klaus-makela/news/klaus-maekelae-releases-debut-album-265377) | Composer/opuses, cycle/recording identity; only selected sections prepared |
| [Hyperion fragment work entry](https://www.hyperion-records.co.uk/dw.asp?dc=W24919_4852256), [Chandos](https://www.chandos.net/products/catalogue/CHAN%2010809) | Named set and Virtanen's realisation; uncertain Symphony-8 provenance remains explicit |
| [Alia Vox: Schubert](https://www.alia-vox.com/en/producte/franz-schubert-transfiguracio/) | D.759/D.944, all selected movements, missing orchestra credit, 2021 sessions |
| [BIS-2457 booklet](https://eclassical.textalk.se/shop/17115/art19/5059519-b620d1-BIS-2457_booklet.pdf) | H.226/H.293, all movement identities, soloist/orchestra/conductor, separate 2018/2019 sessions |
| [DG: Rachmaninoff](https://www.deutschegrammophon.com/en/catalogue/products/rachmaninoff-symphony-no-1-symphonic-dances-nezet-seguin-12192) | Op.13/45, Philadelphia/Nézet-Séguin recording |
| [Orchid: Geysir](https://www.orchidclassics.com/releases/orc100150-mark-simpson/) | Composer, independent wind work, complete ensemble/instrument credits, ORC100150 |
| [Hyperion: Shostakovich](https://www.hyperion-records.co.uk/dc.asp?dc=D_CDA68313) | Op.129 interpretation, Ibragimova/Svetlanov/Jurowski, CDA68313 |
| [DG: Schmidt](https://www.deutschegrammophon.com/en/catalogue/products/franz-schmidt-complete-symphonies-paavo-jaervi-12080), [DG booklet indexed excerpt](https://cdn.naxosmusiclibrary.com/sharedfiles/booklets/DGG/booklet-00028948383405.pdf) | Four symphonies, Frankfurt/Järvi recording; indexed booklet text calls Intermezzo an opera excerpt. Full PDF retrieval was unavailable; it was not read in full. |
| [Hyperion: Vaughan Williams](https://www.hyperion-records.co.uk/dc.asp?dc=D_CDA68405) | Complete selected symphonies, vocal contributors, 2022 sessions, CDA68405 |
| [Resonus: Poulenc](https://www.resonusclassics.com/products/poulenc-piano-concerto-concert-champetre-mark-bebbington-royal-philharmonic-orchestra-res10256) | Four FP identities, tracklist, instrument/ensemble credits, piano tradition, RES10256 |

## Verification and handoff

The exact 106 proposed records were materialised only in an isolated copy of the
repository data and checked with the canonical validator, including changed-ID
identity gates. Result: **0 errors, 0 action-required findings, no new-entity
findings**, with **118 unchanged background suspicions**. The temporary copy is
not a deployed collection. Publication validation passed; the generated temporary
output contains all 32 proposed Works and 33 Performances, and both excerpt
descriptions plus the Virtanen realisation title were checked. There were 1,551
generated Markdown pages. No Jekyll build or deployment was performed. Publication
results are retained in the manifest.

The source hash remains identical to the earlier review. The 120 positions are
disjoint and belong exactly to its 32 absent-Work units plus the existing Work
without a Performance. Their ID/ISRC evidence is retained without changing source
order or adding unselected album tracks. The 142 confirmed-existing tracks remain
unchanged; the 37 Bruckner tracks and position-333 boundary remain outside this step.

This completes import preparation. Applying this exact proposal to canonical
data, validating the actual import once, and checking the final public output is
the next step; it has not been performed by this preparation. The existing PR
remains a draft. No new curator comparison decision was identified in these
vacant recommendation categories.
