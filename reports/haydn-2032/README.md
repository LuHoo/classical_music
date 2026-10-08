# Haydn 2032 CD collection intake

Checked 2026-09-30. This follows the Vivaldi Edition intake: identify Works, assign stable opaque IDs, retain provenance and album-level Tidal links, select performances for newly requested repertoire, and open comparisons for already listed works.

## Scope and outcome

- 19 released numbered CD volumes (1–19), 77 distinct CD work occurrences, including 59 Joseph Haydn symphonies and 18 other works. The unnumbered 2-CD project release *Die Schöpfung* adds one further Work, for 20 released albums and 78 CD work occurrences in total.
- 77 new Works and WorkGroups; Mozart K. 239 reuses its existing entities. 11 new composer Persons, including an Anonymous attribution bucket, are added incrementally.
- 76 new selected Performances. The two already listed works (Mozart K. 239 and Bartók BB 76 / Sz. 68) remain comparison candidates in `occurrences.json` outside canonical performances.
- All 20 Tidal album identities were checked against public MusicAlbum metadata (album title and artists). These are album links, not invented track-level links. Tidal's `datePublished` describes the digital edition, not necessarily the CD release date.
- Volume 20, *For English Gentlemen* (ALPHA1102), is announced for 23 October 2026; it is recorded in `announced.json`, with no canonical entities or recommendation imported yet. A released promotional single does not make the complete album released.
- The first-ten-volume box is a reissue and creates no duplicate performances. The unnumbered *Die Schöpfung* companion is imported and documented in `companion-releases.json`; the [BR Chorus explicitly identifies it as part of the project](https://www.br-chor.de/cd-dvd/projekt-haydn-2032-giovanni-antonini-dirigiert-die-schoepfung/).

## Released volumes

| Vol. | Title | Label catalogue | Haydn symphonies (Hob. I) | Orchestra | Tidal |
|---:|---|---|---|---|---|
| 1 | [La Passione](https://www.haydn2032.com/en/projects/no1-la-passione) | ALPHA670 | 39, 49, 1 | Il Giardino Armonico | [Album](https://tidal.com/album/187335404) |
| 2 | [Il filosofo](https://www.haydn2032.com/en/projects/no2-il-filosofo) | ALPHA671 | 46, 22, 47 | Il Giardino Armonico | [Album](https://tidal.com/album/187335290) |
| 3 | [Solo e pensoso](https://www.haydn2032.com/en/projects/no3-solo-e-pensoso) | ALPHA672 | 42, 64, 4 | Il Giardino Armonico | [Album](https://tidal.com/album/187335264) |
| 4 | [Il distratto](https://www.haydn2032.com/en/projects/no4-il-distratto) | ALPHA674 | 60, 70, 12 | Il Giardino Armonico | [Album](https://tidal.com/album/187334728) |
| 5 | [L'homme de génie](https://www.haydn2032.com/en/projects/no5-lhomme-de-genie) | ALPHA676 | 80, 81, 19 | Kammerorchester Basel | [Album](https://tidal.com/album/187335064) |
| 6 | [Lamentatione](https://www.haydn2032.com/en/projects/no6-lamentatione) | ALPHA678 | 3, 26, 79, 30 | Kammerorchester Basel | [Album](https://tidal.com/album/187335083) |
| 7 | [Gli Impresari](https://www.haydn2032.com/en/projects/no7-gli-impresari) | ALPHA680 | 67, 65, 9 | Kammerorchester Basel | [Album](https://tidal.com/album/187335148) |
| 8 | [La Roxolana](https://www.haydn2032.com/en/projects/no8-la-roxolana) | ALPHA682 | 63, 43, 28 | Il Giardino Armonico | [Album](https://tidal.com/album/187335103) |
| 9 | [L'Addio](https://www.haydn2032.com/en/projects/no9-laddio) | ALPHA684 | 35, 45, 15 | Il Giardino Armonico | [Album](https://tidal.com/album/187296904) |
| 10 | [Les heures du jour](https://www.haydn2032.com/en/projects/no10-les-heures-du-jour) | ALPHA686 | 6, 7, 8 | Il Giardino Armonico | [Album](https://tidal.com/album/183220000) |
| 11 | [Au goût parisien](https://www.haydn2032.com/en/projects/no11-au-gout-parisien) | ALPHA688 | 82, 87, 24, 2 | Kammerorchester Basel | [Album](https://tidal.com/album/214310882) |
| 12 | [Les jeux et les plaisirs](https://www.haydn2032.com/en/projects/no12-les-jeux-et-les-plaisirs) | ALPHA690 | 61, 66, 69 | Kammerorchester Basel | [Album](https://tidal.com/album/230784321) |
| 13 | [Horn Signal](https://www.haydn2032.com/en/projects/no13-hornsignal) | ALPHA692 | 31, 59, 48 | Il Giardino Armonico | [Album](https://tidal.com/album/267861472) |
| 14 | [L'impériale](https://www.haydn2032.com/en/projects/no14-limperiale) | ALPHA694 | 53, 54, 33 | Kammerorchester Basel | [Album](https://tidal.com/album/304074965) |
| 15 | [La Reine](https://www.haydn2032.com/en/projects/no15-la-reine) | ALPHA696 | 85, 62, 50 | Kammerorchester Basel | [Album](https://tidal.com/album/347594506) |
| 16 | [The Surprise](https://www.haydn2032.com/en/projects/no16-the-surprise) | ALPHA698 | 98, 94, 90 | Il Giardino Armonico + Kammerorchester Basel | [Album](https://tidal.com/album/386182541) |
| 17 | [Per il Luigi](https://www.haydn2032.com/en/projects/no17-per-il-luigi) | ALPHA1146 | 36, 16, 13 | Kammerorchester Basel | [Album](https://tidal.com/album/432606500) |
| 18 | [Il maestro di scuola](https://www.haydn2032.com/en/projects/no18-maestro-e-scolare) | ALPHA1092 | 56, 29, 55 | Kammerorchester Basel | [Album](https://tidal.com/album/467075961) |
| 19 | [Trauer](https://www.haydn2032.com/en/projects/no19-trauer) | ALPHA1101 | 52, 44, 108 | Il Giardino Armonico | [Album](https://tidal.com/album/504485309) |

The complete German-language *Die Schöpfung* (Hob. XXI:2), ALPHA567, is performed by Il Giardino Armonico, Chor des Bayerischen Rundfunks and Antonini with Anna Lucia Richter, Maximilian Schmitt and Florian Boesch; the choir also credits Gabriele Weinfurter. [Tidal album](https://tidal.com/album/187429062). The choir web page has a Hoboken typo (XXXI instead of XXI), which is corrected in the catalogue.

## Identification and edition decisions

The official project pages establish programme context and versions; linked release tracklists establish what is actually recorded. The official shop contains transcription errors (for example volume 1's Symphony 49, and the key of Kraus VB 142), so those summaries are not copied blindly. Project/concert programmes are not assumed to equal CD tracklists.

- Volume 1: Gluck's *Don Juan*, Wq. 52, is the original 1761 version identified by the project, not an arbitrarily invented suite.
- Volume 3: *L'isola disabitata* overture, Hob. Ia:13, is separately catalogued; it is not a complete recording of the opera Hob. XXVIII:9. Francesca Aspromonte sings *Solo e pensoso*.
- Volume 7: Mozart's *Thamos*, K. 345, is a Work with a Performance explicitly marked as instrumental excerpts I–IV and VIIa.
- Volume 8: Bartók's orchestral BB 76 / Sz. 68 is distinct from his piano version; the seven tracks include the split final dance and represent the orchestral work. *Sonata Jucunda* has no invented catalogue number or composer.
- Volume 12: the *Toy Symphony* / *Berchtoldsgadner*, historically Hob. II:47, has uncertain authorship. The official project credits Johann Michael Haydn et al. (attributed), with Sonja Gerlach's Urtext. It is stored under Anonymous with that attribution note, not counted as an authenticated Joseph Haydn symphony.
- Volume 13: Telemann TWV 42:F14 is a **digital bonus absent from the CD**, explicitly identified as such by [Presto](https://www.prestomusic.com/classical/products/9408525--haydn-2032-vol-13-horn-signal). It stays in the inventory with `medium: digital_bonus`, without canonical import, and is excluded from the CD occurrence counts.
- Volume 14: Symphony 53 is version A; the separately catalogued one-movement Sinfonia Hob. Ia:7 is linked historically to the version B finale. There is no second full Symphony 53 import. Its association with *Genovefens vierter Theil* is tentative.
- Volume 16 uses a joint orchestra drawn from Il Giardino Armonico and Kammerorchester Basel, as the [official combined line-up](https://www.haydn2032.com/en/projects/no16-the-surprise) shows. Rossini's *La scala di seta* is represented as an opera Work with an overture-only Performance. The 13-track CD programme is also corroborated by the [release listing](https://www.aria-cd.com/arianew/shopping.php?pg=125/125new02).
- Volume 17: Dmitry Smirnov is the violin soloist in Hob. VIIa:1.
- Volume 18: Lessel's Symphony 5 has a finale-only Performance, not a claim of a complete symphony.
- Volume 19: Hob. I:108 (*Sinfonia B*) is separate from the numbered 1–104 sequence; Pärt's *Da pacem Domine* uses the string-orchestra version. Scheidt's Paduan à 4 is SSWV 43.

## Audit and continuation

`catalogue.json` and `companion-releases.json` retain programme metadata, source links, medium and verified Tidal album metadata. `occurrences.json` maps every occurrence to its entities or explicit exclusion; open candidates retain the full proposed Performance. `identity-map.json` assigns random UUIDs once and reuses them on subsequent updates. `summary.json` records the scope and entity totals. `created-issues.json` links the two comparison decisions: [Mozart #229](https://github.com/LuHoo/classical_music/issues/229) and [Bartók #230](https://github.com/LuHoo/classical_music/issues/230).

For a future volume, first verify the released physical programme and album identity, then reuse existing Work identities and open comparisons where a work already exists. Announced volumes and digital bonuses must not silently enter the CD counts. Existing repertoire documents and existing canonical recommendations remain unchanged.
