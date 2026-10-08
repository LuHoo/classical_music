# Vivaldi — Naïve Edition intake

Gecontroleerd en toegevoegd op 28 september 2026.

## Resultaat

- Alle 76 volumes: 401 album–RV-vermeldingen, 365 verschillende RV-aanduidingen.
- Alle 127 werken uit de oude Vivaldi-lijst behouden: 27 overlappen exact; samen 465 Works in 458 Work Groups.
- 42 bestaande aanbevelingen behouden; 338 Naïve-uitvoeringen toegevoegd op grond van het expliciete verzoek van de curator.
- 27 vergelijkingsissues aangemaakt, één voor elk exact overlappend bestaand werk. Ook de bestaande werken zonder aanbevolen uitvoering hebben een issue.
- 75 geverifieerde TIDAL-albumlinks. Volume 67 heeft geen gevonden volledige albumlink; de zes werken en de uitvoerenden zijn wel opgenomen.

## Selectie en modellering

De bron is de eerder gecontroleerde tabel van volumes 1–76, verrijkt met uitvoerenden uit de rechtstreeks bekeken TIDAL-pagina’s en de officiële volumepagina’s. Credits noemen de betrokken hoofdensemble/directie of instrumentalist; het betreft geen uitputtende castlijst. Er zijn geen externe werkidentifiers geraden.

De expliciete opdracht om de editie toe te voegen geldt als acceptatie van de nieuwe repertoirevermeldingen. Bij meerdere Naïve-opnamen van een nieuw werk is voor de eerste publicatie een complete uitvoering verkozen boven fragmenten, en vervolgens het laagste volumenummer. Dit is een praktische keuze zonder artistiek waardeoordeel. De overige voorkomens blijven in het onderstaande dossier beschikbaar. Bestaande aanbevelingen worden uitsluitend na de curatorbeslissing vervangen.

De 63 open album–werkvermeldingen staan in `occurrences.json` buiten canonical `data/`: ze betreffen de bestaande werken die vergeleken moeten worden of aanvullende opnamen binnen de editie. Iedere canonical Performance verwijst naar precies één Work; per Work is maximaal één aanbeveling opgenomen.

Aria’s en losse delen worden volgens het bestaande domeinmodel bij hun bronwerk bewaard, zonder voor ieder fragment een kunstmatig nieuw Work te maken. Het optionele openbare Performance-veld `excerpt` voorkomt dat een fragment wordt gepresenteerd als een complete opera of concerto. Apart gecatalogiseerde aria’s (RV 749.*), versies en reconstructies houden hun eigen Work-identiteit.

RV 711 en 711-D, 706 en 706-B, 181 en 181a, 431 en 431a, 438 en 438bis en de verwante legacy-versies 578/578a en 208/208a zijn niet samengevoegd tot één Work. Verwante versies delen waar van toepassing een Work Group. RV 438bis heeft RV 438b als alias. Argippo RV Anh. 137 blijft gescheiden van RV 697. De samengestelde reconstructies RV 468/399 en 482/406 blijven expliciet benoemd.

Een nadere controle corrigeerde de eerdere bronnotitie voor volume 11: RV 581 bevat alle drie delen, niet slechts een fragment. De RV-lijst en TIDAL-link zelf veranderden hierdoor niet.

Nieuwe permanente identifiers zijn eenmalig gegenereerde, betekenisloze UUID-waarden. Leesbare bestandsnamen blijven apart van die identifiers. `identity-map.json` bewaart de toewijzing voor herhaalbaarheid.

## Bestanden

- [Albumcatalogus met bronlinks en uitvoerenden](catalogue.json)
- [Alle 401 album–werkvermeldingen, inclusief open vergelijkingen](occurrences.json)
- [Vergelijkingsissues](issues.json)
- [Samenvatting](summary.json)
- [Bestaande curatorlijst](../../docs/vivaldi.md)

## Complete werkdekking van de editie

| RV | Werk | Volumes | Huidige aanbeveling / vergelijking |
|---|---|---|---|
| 61 | [Chamber Sonata, RV 61](../../data/works/vivaldi-rv-61.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/201) |
| 63 | [Chamber Sonata, RV 63](../../data/works/vivaldi-rv-63.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/202) |
| 64 | [Chamber Sonata, RV 64](../../data/works/vivaldi-rv-64.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/203) |
| 65 | [Chamber Sonata, RV 65](../../data/works/vivaldi-rv-65.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/204) |
| 66 | [Chamber Sonata, RV 66](../../data/works/vivaldi-rv-66.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/205) |
| 68 | [Chamber Sonata, RV 68](../../data/works/vivaldi-rv-68.yaml) | 12 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214962) |
| 70 | [Chamber Sonata, RV 70](../../data/works/vivaldi-rv-70.yaml) | 12 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214962) |
| 71 | [Chamber Sonata, RV 71](../../data/works/vivaldi-rv-71.yaml) | 12 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214962) |
| 73 | [Chamber Sonata, RV 73](../../data/works/vivaldi-rv-73.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/206) |
| 75 | [Chamber Sonata, RV 75](../../data/works/vivaldi-rv-75.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/207) |
| 77 | [Chamber Sonata, RV 77](../../data/works/vivaldi-rv-77.yaml) | 12 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214962) |
| 78 | [Chamber Sonata, RV 78](../../data/works/vivaldi-rv-78.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/208) |
| 79 | [Chamber Sonata, RV 79](../../data/works/vivaldi-rv-79.yaml) | 44 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/209) |
| 82 | [Chamber Sonata, RV 82](../../data/works/vivaldi-rv-82.yaml) | 26 | [Rolf Lislevand](https://tidal.com/album/92222513) |
| 83 | [Chamber Sonata, RV 83](../../data/works/vivaldi-rv-83.yaml) | 12 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214962) |
| 85 | [Chamber Sonata, RV 85](../../data/works/vivaldi-rv-85.yaml) | 26 | [Rolf Lislevand](https://tidal.com/album/92222513) |
| 86 | [Chamber Sonata, RV 86](../../data/works/vivaldi-rv-86.yaml) | 12 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214962) |
| 87 | [Chamber Concerto, RV 87](../../data/works/vivaldi-rv-87.yaml) | 19 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92795810) |
| 88 | [Chamber Concerto, RV 88](../../data/works/vivaldi-rv-88.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 90 | [Chamber Concerto, RV 90](../../data/works/vivaldi-rv-90.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 91 | [Chamber Concerto, RV 91](../../data/works/vivaldi-rv-91.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 92 | [Chamber Concerto, RV 92](../../data/works/vivaldi-rv-92.yaml) | 16 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214991) |
| 93 | [Chamber Concerto, RV 93](../../data/works/vivaldi-rv-93.yaml) | 26 | [Rolf Lislevand](https://tidal.com/album/92222513) |
| 94 | [Chamber Concerto, RV 94](../../data/works/vivaldi-rv-94.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 95 | [Chamber Concerto, RV 95](../../data/works/vivaldi-rv-95.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 97 | [Chamber Concerto, RV 97](../../data/works/vivaldi-rv-97.yaml) | 5 | [L’Astrée](https://tidal.com/album/92928923) |
| 98 | [Chamber Concerto, RV 98](../../data/works/vivaldi-rv-98.yaml) | 19 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92795810) |
| 99 | [Chamber Concerto, RV 99](../../data/works/vivaldi-rv-99.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 100 | [Chamber Concerto, RV 100](../../data/works/vivaldi-rv-100.yaml) | 16 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214991) |
| 101 | [Chamber Concerto, RV 101](../../data/works/vivaldi-rv-101.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 103 | [Chamber Concerto, RV 103](../../data/works/vivaldi-rv-103.yaml) | 19 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92795810) |
| 104 | [Chamber Concerto, RV 104](../../data/works/vivaldi-rv-104.yaml) | 5 | [L’Astrée](https://tidal.com/album/92928923) |
| 105 | [Chamber Concerto, RV 105](../../data/works/vivaldi-rv-105.yaml) | 5 | [L’Astrée](https://tidal.com/album/92928923) |
| 106 | [Chamber Concerto, RV 106](../../data/works/vivaldi-rv-106.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 107 | [Chamber Concerto, RV 107](../../data/works/vivaldi-rv-107.yaml) | 1 | [L’Astrée](https://tidal.com/album/66768093) |
| 108 | [Chamber Concerto, RV 108](../../data/works/vivaldi-rv-108.yaml) | 16 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214991) |
| 109 | [Concerto for strings, RV 109](../../data/works/vivaldi-rv-109.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 110 | [Concerto for strings, RV 110](../../data/works/vivaldi-rv-110.yaml) | 40, 52 | [I Barocchisti, Diego Fasolis](https://tidal.com/album/91194278) |
| 112 | [Concerto for strings, RV 112](../../data/works/vivaldi-rv-112.yaml) | 64 | [Europa Galante, Fabio Biondi](https://tidal.com/album/159927017) |
| 115 | [Concerto for strings, RV 115](../../data/works/vivaldi-rv-115.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 117 | [Concerto for strings, RV 117](../../data/works/vivaldi-rv-117.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 118 | [Concerto for strings, RV 118](../../data/works/vivaldi-rv-118.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 119 | [Concerto for strings, RV 119](../../data/works/vivaldi-rv-119.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 120 | [Concerto for strings, RV 120](../../data/works/vivaldi-rv-120.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 121 | [Concerto for strings, RV 121](../../data/works/vivaldi-rv-121.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 123 | [Concerto for strings, RV 123](../../data/works/vivaldi-rv-123.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 126 | [Concerto for strings, RV 126](../../data/works/vivaldi-rv-126.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 127 | [Concerto for strings, RV 127](../../data/works/vivaldi-rv-127.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 128 | [Concerto for strings, RV 128](../../data/works/vivaldi-rv-128.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 129 | [Concerto for strings, RV 129](../../data/works/vivaldi-rv-129.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 130 | [Sonata for strings “Al santo sepolcro”, RV 130](../../data/works/vivaldi-rv-130.yaml) | 6 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73947224) |
| 134 | [Concerto for strings, RV 134](../../data/works/vivaldi-rv-134.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 136 | [Concerto for strings, RV 136](../../data/works/vivaldi-rv-136.yaml) | 30 | [Accademia Bizantina](https://tidal.com/album/91195549) |
| Anh. 137 | [Argippo (pasticcio), RV Anh. 137](../../data/works/vivaldi-rv-anh-137.yaml) | 64 | [Europa Galante, Fabio Biondi](https://tidal.com/album/159927017) |
| 138 | [Concerto for strings, RV 138](../../data/works/vivaldi-rv-138.yaml) | 56, 73 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 141 | [Concerto for strings, RV 141](../../data/works/vivaldi-rv-141.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 142 | [Concerto for strings, RV 142](../../data/works/vivaldi-rv-142.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 143 | [Concerto for strings, RV 143](../../data/works/vivaldi-rv-143.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 145 | [Concerto for strings, RV 145](../../data/works/vivaldi-rv-145.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 146 | [Sinfonia, RV 146](../../data/works/vivaldi-rv-146.yaml) | 21 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/92206875) |
| 150 | [Concerto for strings, RV 150](../../data/works/vivaldi-rv-150.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 151 | [Concerto for strings, RV 151](../../data/works/vivaldi-rv-151.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 152 | [Concerto for strings, RV 152](../../data/works/vivaldi-rv-152.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 153 | [Concerto for strings, RV 153](../../data/works/vivaldi-rv-153.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 154 | [Concerto for strings, RV 154](../../data/works/vivaldi-rv-154.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 155 | [Concerto for strings, RV 155](../../data/works/vivaldi-rv-155.yaml) | 56 | [La Serenissima, Adrian Chandler](https://tidal.com/track/458197196); [Curatorissue](https://github.com/LuHoo/classical_music/issues/210) |
| 156 | [Concerto for strings, RV 156](../../data/works/vivaldi-rv-156.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 157 | [Concerto for strings, RV 157](../../data/works/vivaldi-rv-157.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 158 | [Concerto for strings, RV 158](../../data/works/vivaldi-rv-158.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 159 | [Concerto for strings, RV 159](../../data/works/vivaldi-rv-159.yaml) | 13 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91193915) |
| 160 | [Concerto for strings, RV 160](../../data/works/vivaldi-rv-160.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 161 | [Concerto for strings, RV 161](../../data/works/vivaldi-rv-161.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 162 | [Sinfonia, RV 162](../../data/works/vivaldi-rv-162.yaml) | 22 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/92797025) |
| 163 | [Concerto for strings, RV 163](../../data/works/vivaldi-rv-163.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 164 | [Concerto for strings, RV 164](../../data/works/vivaldi-rv-164.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 165 | [Concerto for strings, RV 165](../../data/works/vivaldi-rv-165.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 166 | [Concerto for strings, RV 166](../../data/works/vivaldi-rv-166.yaml) | 52 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91194501) |
| 167 | [Concerto for strings, RV 167](../../data/works/vivaldi-rv-167.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 169 | [Sinfonia “Al santo sepolcro”, RV 169](../../data/works/vivaldi-rv-169.yaml) | 24 | [Concerto Köln, Shunske Sato](http://www.tidal.com/track/64126591); [Curatorissue](https://github.com/LuHoo/classical_music/issues/211) |
| 171 | [Violin Concerto, RV 171](../../data/works/vivaldi-rv-171.yaml) | 45 | [Il Pomo d’Oro, Riccardo Minasi](https://tidal.com/album/92929122) |
| 177 | [Violin Concerto, RV 177](../../data/works/vivaldi-rv-177.yaml) | 49 | [Il Pomo d’Oro, Dmitry Sinkovsky](https://tidal.com/album/92205621) |
| 179a | [Violin Concerto, RV 179a](../../data/works/vivaldi-rv-179a.yaml) | 71 | [Fabio Biondi, Europa Galante](http://www.tidal.com/track/304319795); [Curatorissue](https://github.com/LuHoo/classical_music/issues/212) |
| 181 | [Violin Concerto, RV 181](../../data/works/vivaldi-rv-181.yaml) | 45 | [Il Pomo d’Oro, Riccardo Minasi](https://tidal.com/album/92929122) |
| 181a | [Violin Concerto, RV 181a](../../data/works/vivaldi-rv-181a.yaml) | 45 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/213) |
| 186 | [Violin Concerto, RV 186](../../data/works/vivaldi-rv-186.yaml) | 57 | [Europa Galante, Fabio Biondi](https://tidal.com/album/94258645) |
| 187 | [Violin Concerto, RV 187](../../data/works/vivaldi-rv-187.yaml) | 63 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/131385910) |
| 192 | [Sinfonia, RV 192](../../data/works/vivaldi-rv-192.yaml) | 7 | [Freiburger Barockorchester, Gottfried von der Goltz](https://tidal.com/album/65271994) |
| 194 | [Violin Concerto, RV 194](../../data/works/vivaldi-rv-194.yaml) | 67 | Concerto Italiano, Rinaldo Alessandrini, Boris Begelman — volledig TIDAL-album niet gevonden |
| 199 | [Violin Concerto, RV 199](../../data/works/vivaldi-rv-199.yaml) | 23 | [Academia Montis Regalis, Enrico Onofri](https://tidal.com/album/92207007) |
| 207 | [Violin Concerto, RV 207](../../data/works/vivaldi-rv-207.yaml) | 71 | [Fabio Biondi, Europa Galante](http://www.tidal.com/track/304319788); [Curatorissue](https://github.com/LuHoo/classical_music/issues/214) |
| 208 | [Violin Concerto, RV 208](../../data/works/vivaldi-rv-208.yaml) | 23 | [Academia Montis Regalis, Enrico Onofri](https://tidal.com/album/92207007) |
| 210 | [Violin Concerto, RV 210](../../data/works/vivaldi-rv-210.yaml) | 33 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/215) |
| 211 | [Violin Concerto, RV 211](../../data/works/vivaldi-rv-211.yaml) | 67 | Concerto Italiano, Rinaldo Alessandrini, Boris Begelman — volledig TIDAL-album niet gevonden |
| 212a | [Violin Concerto, RV 212a](../../data/works/vivaldi-rv-212a.yaml) | 49 | [Il Pomo d’Oro, Dmitry Sinkovsky](https://tidal.com/album/92205621) |
| 217 | [Violin Concerto, RV 217](../../data/works/vivaldi-rv-217.yaml) | 63 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/131385910) |
| 225 | [Violin Concerto, RV 225](../../data/works/vivaldi-rv-225.yaml) | 69 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/238630839) |
| 226 | [Violin Concerto, RV 226](../../data/works/vivaldi-rv-226.yaml) | 69 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/238630839) |
| 229 | [Violin Concerto, RV 229](../../data/works/vivaldi-rv-229.yaml) | 71 | [Fabio Biondi, Europa Galante](http://www.tidal.com/track/304319781); [Curatorissue](https://github.com/LuHoo/classical_music/issues/216) |
| 232 | [Violin Concerto, RV 232](../../data/works/vivaldi-rv-232.yaml) | 28 | [Modo Antiquo, Anton Steck](https://tidal.com/album/92207034) |
| 234 | [Violin Concerto, RV 234](../../data/works/vivaldi-rv-234.yaml) | 23 | [Academia Montis Regalis, Enrico Onofri](https://tidal.com/album/92207007) |
| 235 | [Violin Concerto, RV 235](../../data/works/vivaldi-rv-235.yaml) | 63 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/131385910) |
| 237 | [Violin Concerto, RV 237](../../data/works/vivaldi-rv-237.yaml) | 69 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/238630839) |
| 242 | [Violin Concerto, RV 242](../../data/works/vivaldi-rv-242.yaml) | 49 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/217) |
| 243 | [Violin Concerto, RV 243](../../data/works/vivaldi-rv-243.yaml) | 28 | [Modo Antiquo, Anton Steck](https://tidal.com/album/92207034) |
| 246 | [Violin Concerto, RV 246](../../data/works/vivaldi-rv-246.yaml) | 49 | [Il Pomo d’Oro, Dmitry Sinkovsky](https://tidal.com/album/92205621) |
| 257 | [Violin Concerto, RV 257](../../data/works/vivaldi-rv-257.yaml) | 62 | [Accademia Bizantina, Ottavio Dantone, Alessandro Tampieri](https://tidal.com/album/119018912) |
| 260 | [Violin Concerto, RV 260](../../data/works/vivaldi-rv-260.yaml) | 71 | [Fabio Biondi, Europa Galante](http://www.tidal.com/track/304319792); [Curatorissue](https://github.com/LuHoo/classical_music/issues/218) |
| 261 | [Violin Concerto, RV 261](../../data/works/vivaldi-rv-261.yaml) | 71 | [Fabio Biondi, Europa Galante](http://www.tidal.com/track/304319798); [Curatorissue](https://github.com/LuHoo/classical_music/issues/219) |
| 263a | [Violin Concerto, RV 263a](../../data/works/vivaldi-rv-263a.yaml) | 45 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/220) |
| 264 | [Violin Concerto, RV 264](../../data/works/vivaldi-rv-264.yaml) | 28 | [Modo Antiquo, Anton Steck](https://tidal.com/album/92207034) |
| 268 | [Violin Concerto, RV 268](../../data/works/vivaldi-rv-268.yaml) | 33 | [I Barocchisti, Diego Fasolis, Duilio Galfetti](https://tidal.com/album/92207252) |
| 270 | [Violin Concerto, RV 270](../../data/works/vivaldi-rv-270.yaml) | 23 | [Academia Montis Regalis, Enrico Onofri](https://tidal.com/album/92207007) |
| 271 | [Violin Concerto, RV 271](../../data/works/vivaldi-rv-271.yaml) | 45 | [Il Pomo d’Oro, Riccardo Minasi](https://tidal.com/album/92929122) |
| 273 | [Violin Concerto, RV 273](../../data/works/vivaldi-rv-273.yaml) | 62 | [Accademia Bizantina, Ottavio Dantone, Alessandro Tampieri](https://tidal.com/album/119018912) |
| 278 | [Violin Concerto, RV 278](../../data/works/vivaldi-rv-278.yaml) | 57 | [Europa Galante, Fabio Biondi](https://tidal.com/album/94258645) |
| 281 | [Violin Concerto, RV 281](../../data/works/vivaldi-rv-281.yaml) | 67 | Concerto Italiano, Rinaldo Alessandrini, Boris Begelman — volledig TIDAL-album niet gevonden |
| 282 | [Violin Concerto, RV 282](../../data/works/vivaldi-rv-282.yaml) | 57 | [Europa Galante, Fabio Biondi](https://tidal.com/album/94258645) |
| 283 | [Violin Concerto, RV 283](../../data/works/vivaldi-rv-283.yaml) | 67 | Concerto Italiano, Rinaldo Alessandrini, Boris Begelman — volledig TIDAL-album niet gevonden |
| 286 | [Violin Concerto, RV 286](../../data/works/vivaldi-rv-286.yaml) | 24 | [Accademia Bizantina](https://tidal.com/album/73947302) |
| 288 | [Violin Concerto, RV 288](../../data/works/vivaldi-rv-288.yaml) | 57 | [Europa Galante, Fabio Biondi](https://tidal.com/album/94258645) |
| 307 | [Violin Concerto, RV 307](../../data/works/vivaldi-rv-307.yaml) | 33 | [I Barocchisti, Diego Fasolis, Duilio Galfetti](https://tidal.com/album/92207252) |
| 312 | [Violin Concerto, RV 312](../../data/works/vivaldi-rv-312.yaml) | 33 | [I Barocchisti, Diego Fasolis, Duilio Galfetti](https://tidal.com/album/92207252) |
| 314 | [Violin Concerto, RV 314](../../data/works/vivaldi-rv-314.yaml) | 69 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/238630839) |
| 321 | [Violin Concerto, RV 321](../../data/works/vivaldi-rv-321.yaml) | 63 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/131385910) |
| 325 | [Violin Concerto, RV 325](../../data/works/vivaldi-rv-325.yaml) | 28 | [Modo Antiquo, Anton Steck](https://tidal.com/album/92207034) |
| 327 | [Violin Concerto, RV 327](../../data/works/vivaldi-rv-327.yaml) | 45 | [Il Pomo d’Oro, Riccardo Minasi](https://tidal.com/album/92929122) |
| 328 | [Violin Concerto, RV 328](../../data/works/vivaldi-rv-328.yaml) | 49 | [Il Pomo d’Oro, Dmitry Sinkovsky](https://tidal.com/album/92205621) |
| 330 | [Violin Concerto, RV 330](../../data/works/vivaldi-rv-330.yaml) | 57 | [Europa Galante, Fabio Biondi](https://tidal.com/album/94258645) |
| 331 | [Violin Concerto, RV 331](../../data/works/vivaldi-rv-331.yaml) | 45 | [Il Pomo d’Oro, Riccardo Minasi](https://tidal.com/album/92929122) |
| 332 | [Violin Concerto, RV 332](../../data/works/vivaldi-rv-332.yaml) | 23 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/221) |
| 333 | [Violin Concerto, RV 333](../../data/works/vivaldi-rv-333.yaml) | 33 | [I Barocchisti, Diego Fasolis, Duilio Galfetti](https://tidal.com/album/92207252) |
| 340 | [Violin Concerto, RV 340](../../data/works/vivaldi-rv-340.yaml) | 69 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/238630839) |
| 346 | [Violin Concerto, RV 346](../../data/works/vivaldi-rv-346.yaml) | 67 | Concerto Italiano, Rinaldo Alessandrini, Boris Begelman — volledig TIDAL-album niet gevonden |
| 350 | [Violin Concerto, RV 350](../../data/works/vivaldi-rv-350.yaml) | 33 | [I Barocchisti, Diego Fasolis, Duilio Galfetti](https://tidal.com/album/92207252) |
| 352 | [Violin Concerto, RV 352](../../data/works/vivaldi-rv-352.yaml) | 33 | [I Barocchisti, Diego Fasolis, Duilio Galfetti](https://tidal.com/album/92207252) |
| 353 | [Violin Concerto, RV 353](../../data/works/vivaldi-rv-353.yaml) | 28 | [Modo Antiquo, Anton Steck](https://tidal.com/album/92207034) |
| 362 | [Violin Concerto, RV 362](../../data/works/vivaldi-rv-362.yaml) | 23 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/222) |
| 363 | [Violin Concerto, RV 363](../../data/works/vivaldi-rv-363.yaml) | 71 | [Fabio Biondi, Europa Galante](http://www.tidal.com/track/304319784); [Curatorissue](https://github.com/LuHoo/classical_music/issues/223) |
| 365 | [Violin Concerto, RV 365](../../data/works/vivaldi-rv-365.yaml) | 67 | Concerto Italiano, Rinaldo Alessandrini, Boris Begelman — volledig TIDAL-album niet gevonden |
| 366 | [Violin Concerto, RV 366](../../data/works/vivaldi-rv-366.yaml) | 63 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/131385910) |
| 367 | [Violin Concerto, RV 367](../../data/works/vivaldi-rv-367.yaml) | 62 | [Accademia Bizantina, Ottavio Dantone, Alessandro Tampieri](https://tidal.com/album/119018912) |
| 368 | [Violin Concerto, RV 368](../../data/works/vivaldi-rv-368.yaml) | 28 | [Modo Antiquo, Anton Steck](https://tidal.com/album/92207034) |
| 369 | [Violin Concerto, RV 369](../../data/works/vivaldi-rv-369.yaml) | 30, 69 | [Accademia Bizantina](https://tidal.com/album/91195549) |
| 370 | [Violin Concerto, RV 370](../../data/works/vivaldi-rv-370.yaml) | 49 | [Il Pomo d’Oro, Dmitry Sinkovsky](https://tidal.com/album/92205621) |
| 371 | [Violin Concerto, RV 371](../../data/works/vivaldi-rv-371.yaml) | 62 | [Accademia Bizantina, Ottavio Dantone, Alessandro Tampieri](https://tidal.com/album/119018912) |
| 379 | [Violin Concerto, RV 379](../../data/works/vivaldi-rv-379.yaml) | 49 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/224) |
| 380 | [Violin Concerto, RV 380](../../data/works/vivaldi-rv-380.yaml) | 57 | [Europa Galante, Fabio Biondi](https://tidal.com/album/94258645) |
| 387 | [Violin Concerto, RV 387](../../data/works/vivaldi-rv-387.yaml) | 63 | [Le Concert de la Loge, Julien Chauvin](https://tidal.com/album/131385910) |
| 389 | [Violin Concerto, RV 389](../../data/works/vivaldi-rv-389.yaml) | 62 | [Accademia Bizantina, Ottavio Dantone, Alessandro Tampieri](https://tidal.com/album/119018912) |
| 390 | [Violin Concerto, RV 390](../../data/works/vivaldi-rv-390.yaml) | 62 | [Accademia Bizantina, Ottavio Dantone, Alessandro Tampieri](https://tidal.com/album/119018912) |
| 391 | [Violin Concerto, RV 391](../../data/works/vivaldi-rv-391.yaml) | 45 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/225) |
| 393 | [Viola d’amore Concerto, RV 393](../../data/works/vivaldi-rv-393.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 394 | [Viola d’amore Concerto, RV 394](../../data/works/vivaldi-rv-394.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 395 | [Viola d’amore Concerto, RV 395](../../data/works/vivaldi-rv-395.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 396 | [Viola d’amore Concerto, RV 396](../../data/works/vivaldi-rv-396.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 397 | [Viola d’amore Concerto, RV 397](../../data/works/vivaldi-rv-397.yaml) | 56 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/87860696) |
| 398 | [Cello Concerto, RV 398](../../data/works/vivaldi-rv-398.yaml) | 27 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/91802676) |
| 399 | [Cello Concerto, RV 399](../../data/works/vivaldi-rv-399.yaml) | 31 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/92207197) |
| 400 | [Cello Concerto, RV 400](../../data/works/vivaldi-rv-400.yaml) | 61 | [L’Onda Armonica, Christophe Coin](https://tidal.com/album/117652293) |
| 401 | [Cello Concerto, RV 401](../../data/works/vivaldi-rv-401.yaml) | 31 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/92207197) |
| 402 | [Concerto in C minor, RV 402](../../data/works/vivaldi-rv-402.yaml) | 76 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/518903747) |
| 403 | [Cello Concerto, RV 403](../../data/works/vivaldi-rv-403.yaml) | 31 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/92207197) |
| 404 | [Cello Concerto, RV 404](../../data/works/vivaldi-rv-404.yaml) | 61 | [L’Onda Armonica, Christophe Coin](https://tidal.com/album/117652293) |
| 406 | [Cello Concerto, RV 406](../../data/works/vivaldi-rv-406.yaml) | 27 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/91802676) |
| 407 | [Cello Concerto, RV 407](../../data/works/vivaldi-rv-407.yaml) | 61 | [L’Onda Armonica, Christophe Coin](https://tidal.com/album/117652293) |
| 408 | [Cello Concerto, RV 408](../../data/works/vivaldi-rv-408.yaml) | 31 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/92207197) |
| 409 | [Cello Concerto, RV 409](../../data/works/vivaldi-rv-409.yaml) | 27 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/91802676) |
| 410 | [Cello Concerto, RV 410](../../data/works/vivaldi-rv-410.yaml) | 27 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/91802676) |
| 411 | [Cello Concerto, RV 411](../../data/works/vivaldi-rv-411.yaml) | 31 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/92207197) |
| 414 | [Cello Concerto, RV 414](../../data/works/vivaldi-rv-414.yaml) | 27 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/91802676) |
| 415 | [Cello Concerto, RV 415](../../data/works/vivaldi-rv-415.yaml) | 61 | [L’Onda Armonica, Christophe Coin](https://tidal.com/album/117652293) |
| 417 | [Cello Concerto, RV 417](../../data/works/vivaldi-rv-417.yaml) | 31 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/92207197) |
| 419 | [Cello Concerto, RV 419](../../data/works/vivaldi-rv-419.yaml) | 27 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/91802676) |
| 420 | [Cello Concerto, RV 420](../../data/works/vivaldi-rv-420.yaml) | 61 | [L’Onda Armonica, Christophe Coin](https://tidal.com/album/117652293) |
| 421 | [Cello Concerto, RV 421](../../data/works/vivaldi-rv-421.yaml) | 27 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/91802676) |
| 422 | [Cello Concerto, RV 422](../../data/works/vivaldi-rv-422.yaml) | 31 | [Il Giardino Armonico, Giovanni Antonini, Christophe Coin](https://tidal.com/album/92207197) |
| 423 | [Cello Concerto, RV 423](../../data/works/vivaldi-rv-423.yaml) | 61 | [L’Onda Armonica, Christophe Coin](https://tidal.com/album/117652293) |
| 425 | [Mandolin Concerto, RV 425](../../data/works/vivaldi-rv-425.yaml) | 26 | [Rolf Lislevand](https://tidal.com/album/92222513) |
| 427 | [Flute Concerto, RV 427](../../data/works/vivaldi-rv-427.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) |
| 429 | [Flute Concerto, RV 429](../../data/works/vivaldi-rv-429.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) |
| 431 | [Flute Concerto, RV 431](../../data/works/vivaldi-rv-431.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) — Two Allegro movements only. |
| 431a | [Flute Concerto, RV 431a](../../data/works/vivaldi-rv-431a.yaml) | 46 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91801069) |
| 432 | [Flute Concerto, RV 432](../../data/works/vivaldi-rv-432.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) — First movement (Allegro) only. |
| 436 | [Flute Concerto, RV 436](../../data/works/vivaldi-rv-436.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) |
| 438 | [Flute Concerto, RV 438](../../data/works/vivaldi-rv-438.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) |
| 438bis | [Flute Concerto, RV 438bis](../../data/works/vivaldi-rv-438bis.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) — First movement (Allegro) only. |
| 440 | [Flute Concerto, RV 440](../../data/works/vivaldi-rv-440.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) |
| 447 | [Oboe Concerto, RV 447](../../data/works/vivaldi-rv-447.yaml) | 35 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/78146110) |
| 450 | [Oboe Concerto, RV 450](../../data/works/vivaldi-rv-450.yaml) | 35 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/78146110) |
| 451 | [Oboe Concerto, RV 451](../../data/works/vivaldi-rv-451.yaml) | 15, 35 | [Sonatori de la Gioiosa Marca](https://tidal.com/album/65272162) |
| 453 | [Oboe Concerto, RV 453](../../data/works/vivaldi-rv-453.yaml) | 35 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/78146110) |
| 454 | [Oboe Concerto, RV 454](../../data/works/vivaldi-rv-454.yaml) | 18 | [Curatorissue](https://github.com/LuHoo/classical_music/issues/226) |
| 455 | [Oboe Concerto, RV 455](../../data/works/vivaldi-rv-455.yaml) | 35 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/78146110) |
| 457 | [Oboe Concerto, RV 457](../../data/works/vivaldi-rv-457.yaml) | 35 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/78146110) |
| 461 | [Oboe Concerto, RV 461](../../data/works/vivaldi-rv-461.yaml) | 15 | [Sonatori de la Gioiosa Marca](https://tidal.com/album/65272162) |
| 463 | [Oboe Concerto, RV 463](../../data/works/vivaldi-rv-463.yaml) | 35 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/78146110) |
| 466 | [Bassoon Concerto, RV 466](../../data/works/vivaldi-rv-466.yaml) | 76 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/518903747) |
| 467 | [Bassoon Concerto, RV 467](../../data/works/vivaldi-rv-467.yaml) | 66 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/179330143) |
| 468/399 | [Bassoon Concerto (reconstruction), RV 468/399](../../data/works/vivaldi-rv-468-399.yaml) | 76 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/518903747) |
| 469 | [Bassoon Concerto, RV 469](../../data/works/vivaldi-rv-469.yaml) | 54 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/65305033) |
| 470 | [Bassoon Concerto, RV 470](../../data/works/vivaldi-rv-470.yaml) | 42 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305986) |
| 471 | [Bassoon Concerto, RV 471](../../data/works/vivaldi-rv-471.yaml) | 39 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305766) |
| 472 | [Bassoon Concerto, RV 472](../../data/works/vivaldi-rv-472.yaml) | 42 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305986) |
| 473 | [Bassoon Concerto, RV 473](../../data/works/vivaldi-rv-473.yaml) | 54 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/65305033) |
| 474 | [Bassoon Concerto, RV 474](../../data/works/vivaldi-rv-474.yaml) | 48 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65273521) |
| 475 | [Bassoon Concerto, RV 475](../../data/works/vivaldi-rv-475.yaml) | 48 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65273521) |
| 476 | [Bassoon Concerto, RV 476](../../data/works/vivaldi-rv-476.yaml) | 66 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/179330143) |
| 477 | [Bassoon Concerto, RV 477](../../data/works/vivaldi-rv-477.yaml) | 39 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305766) |
| 478 | [Bassoon Concerto, RV 478](../../data/works/vivaldi-rv-478.yaml) | 76 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/518903747) |
| 479 | [Bassoon Concerto, RV 479](../../data/works/vivaldi-rv-479.yaml) | 66 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/179330143) |
| 480 | [Bassoon Concerto, RV 480](../../data/works/vivaldi-rv-480.yaml) | 48 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65273521) |
| 481 | [Bassoon Concerto, RV 481](../../data/works/vivaldi-rv-481.yaml) | 15, 66 | [Sonatori de la Gioiosa Marca](https://tidal.com/album/65272162) |
| 482/406 | [Bassoon Concerto (reconstruction), RV 482/406](../../data/works/vivaldi-rv-482-406.yaml) | 76 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/518903747) |
| 483 | [Bassoon Concerto, RV 483](../../data/works/vivaldi-rv-483.yaml) | 42 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305986) |
| 484 | [Bassoon Concerto, RV 484](../../data/works/vivaldi-rv-484.yaml) | 39 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305766) |
| 485 | [Bassoon Concerto, RV 485](../../data/works/vivaldi-rv-485.yaml) | 48 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65273521) |
| 486 | [Bassoon Concerto, RV 486](../../data/works/vivaldi-rv-486.yaml) | 66 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/179330143) |
| 487 | [Bassoon Concerto, RV 487](../../data/works/vivaldi-rv-487.yaml) | 76 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/518903747) |
| 488 | [Bassoon Concerto, RV 488](../../data/works/vivaldi-rv-488.yaml) | 39 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305766) |
| 489 | [Bassoon Concerto, RV 489](../../data/works/vivaldi-rv-489.yaml) | 66 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/179330143) |
| 490 | [Bassoon Concerto, RV 490](../../data/works/vivaldi-rv-490.yaml) | 42 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305986) |
| 491 | [Bassoon Concerto, RV 491](../../data/works/vivaldi-rv-491.yaml) | 54 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/65305033) |
| 492 | [Bassoon Concerto, RV 492](../../data/works/vivaldi-rv-492.yaml) | 54 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/65305033) |
| 493 | [Bassoon Concerto, RV 493](../../data/works/vivaldi-rv-493.yaml) | 39 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305766) |
| 494 | [Bassoon Concerto, RV 494](../../data/works/vivaldi-rv-494.yaml) | 48 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65273521) |
| 495 | [Bassoon Concerto, RV 495](../../data/works/vivaldi-rv-495.yaml) | 39 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305766) |
| 496 | [Bassoon Concerto, RV 496](../../data/works/vivaldi-rv-496.yaml) | 42 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305986) |
| 497 | [Bassoon Concerto, RV 497](../../data/works/vivaldi-rv-497.yaml) | 18, 66 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/92206835) |
| 498 | [Bassoon Concerto, RV 498](../../data/works/vivaldi-rv-498.yaml) | 15, 54 | [Sonatori de la Gioiosa Marca](https://tidal.com/album/65272162) |
| 499 | [Bassoon Concerto, RV 499](../../data/works/vivaldi-rv-499.yaml) | 42 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305986) |
| 500 | [Bassoon Concerto, RV 500](../../data/works/vivaldi-rv-500.yaml) | 54 | [L’Onda Armonica, Sergio Azzolini](https://tidal.com/album/65305033) |
| 501 | [Bassoon Concerto, RV 501](../../data/works/vivaldi-rv-501.yaml) | 15, 76 | [Sonatori de la Gioiosa Marca](https://tidal.com/album/65272162) |
| 502 | [Bassoon Concerto, RV 502](../../data/works/vivaldi-rv-502.yaml) | 48 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65273521) |
| 503 | [Bassoon Concerto, RV 503](../../data/works/vivaldi-rv-503.yaml) | 39 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305766) |
| 504 | [Bassoon Concerto, RV 504](../../data/works/vivaldi-rv-504.yaml) | 42 | [L’Aura Soave Cremona, Sergio Azzolini](https://tidal.com/album/65305986) |
| 508 | [Concerto for two violins, RV 508](../../data/works/vivaldi-rv-508.yaml) | 51 | [Il Pomo d’Oro, Dmitry Sinkovsky, Riccardo Minasi](https://tidal.com/album/91801130) |
| 509 | [Concerto for two violins, RV 509](../../data/works/vivaldi-rv-509.yaml) | 51 | [Il Pomo d’Oro, Dmitry Sinkovsky, Riccardo Minasi](https://tidal.com/album/91801130) |
| 510 | [Concerto for two violins, RV 510](../../data/works/vivaldi-rv-510.yaml) | 51 | [Il Pomo d’Oro, Dmitry Sinkovsky, Riccardo Minasi](https://tidal.com/album/91801130) |
| 515 | [Concerto for two violins, RV 515](../../data/works/vivaldi-rv-515.yaml) | 51 | [La Serenissima, Adrian Chandler](https://tidal.com/track/401810407); [Curatorissue](https://github.com/LuHoo/classical_music/issues/227) |
| 517 | [Concerto for two violins, RV 517](../../data/works/vivaldi-rv-517.yaml) | 51 | [Il Pomo d’Oro, Dmitry Sinkovsky, Riccardo Minasi](https://tidal.com/album/91801130) |
| 523 | [Concerto for two violins, RV 523](../../data/works/vivaldi-rv-523.yaml) | 51 | [Il Pomo d’Oro, Dmitry Sinkovsky, Riccardo Minasi](https://tidal.com/album/91801130) |
| 532 | [Concerto for two mandolins, RV 532](../../data/works/vivaldi-rv-532.yaml) | 26 | [Rolf Lislevand](https://tidal.com/album/92222513) |
| 533 | [Concerto for two flutes, RV 533](../../data/works/vivaldi-rv-533.yaml) | 3 | [Academia Montis Regalis, Barthold Kuijken](https://tidal.com/album/92206603) |
| 534 | [Concerto for two oboes, RV 534](../../data/works/vivaldi-rv-534.yaml) | 18 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/92206835) |
| 535 | [Concerto for two oboes, RV 535](../../data/works/vivaldi-rv-535.yaml) | 75 | [Les Musiciens du Prince-Monaco, Gianluca Capuano](https://tidal.com/album/502817806) |
| 540 | [Concerto for viola d’amore and lute, RV 540](../../data/works/vivaldi-rv-540.yaml) | 26 | [Rolf Lislevand](https://tidal.com/album/92222513) |
| 541 | [Concerto for violin and organ, RV 541](../../data/works/vivaldi-rv-541.yaml) | 24 | [Accademia Bizantina](https://tidal.com/album/73947302) |
| 543 | [Concerto for violin and oboe, RV 543](../../data/works/vivaldi-rv-543.yaml) | 75 | [Les Musiciens du Prince-Monaco, Gianluca Capuano](https://tidal.com/album/502817806) |
| 545 | [Concerto for oboe and bassoon, RV 545](../../data/works/vivaldi-rv-545.yaml) | 15 | [Sonatori de la Gioiosa Marca](https://tidal.com/album/65272162) |
| 548 | [Concerto for oboe and violin, RV 548](../../data/works/vivaldi-rv-548.yaml) | 18 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/92206835) |
| 553 | [Concerto for four violins, RV 553](../../data/works/vivaldi-rv-553.yaml) | 75 | [Les Musiciens du Prince-Monaco, Gianluca Capuano](https://tidal.com/album/502817806) |
| 554a | [Concerto, RV 554a](../../data/works/vivaldi-rv-554a.yaml) | 6 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73947224) |
| 555 | [Concerto, RV 555](../../data/works/vivaldi-rv-555.yaml) | 75 | [Les Musiciens du Prince-Monaco, Gianluca Capuano](https://tidal.com/album/502817806) |
| 556 | [Concerto, RV 556](../../data/works/vivaldi-rv-556.yaml) | 6 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73947224) |
| 557 | [Concerto for two violins, two oboes, two recorders and bassoon, RV 557](../../data/works/vivaldi-rv-557.yaml) | 75 | [Les Musiciens du Prince-Monaco, Gianluca Capuano](https://tidal.com/album/502817806) |
| 559 | [Concerto, RV 559](../../data/works/vivaldi-rv-559.yaml) | 18 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/92206835) |
| 560 | [Concerto, RV 560](../../data/works/vivaldi-rv-560.yaml) | 18 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/92206835) |
| 566 | [Concerto, RV 566](../../data/works/vivaldi-rv-566.yaml) | 18 | [Zefiro, Alfredo Bernardini](https://tidal.com/album/92206835) |
| 569 | [Concerto, RV 569](../../data/works/vivaldi-rv-569.yaml) | 7 | [Freiburger Barockorchester, Gottfried von der Goltz](https://tidal.com/album/65271994) |
| 570 | [Concerto for flute, oboe, bassoon and strings “Tempesta di mare”, RV 570](../../data/works/vivaldi-rv-570.yaml) | 75 | [Les Musiciens du Prince-Monaco, Gianluca Capuano](https://tidal.com/album/502817806) |
| 574 | [Concerto, RV 574](../../data/works/vivaldi-rv-574.yaml) | 7 | [Freiburger Barockorchester, Gottfried von der Goltz](https://tidal.com/album/65271994) |
| 576 | [Concerto, RV 576](../../data/works/vivaldi-rv-576.yaml) | 7 | [Freiburger Barockorchester, Gottfried von der Goltz](https://tidal.com/album/65271994) |
| 577 | [Concerto, RV 577](../../data/works/vivaldi-rv-577.yaml) | 7 | [Freiburger Barockorchester, Gottfried von der Goltz](https://tidal.com/album/65271994) |
| 578a | [Concerto, RV 578a](../../data/works/vivaldi-rv-578a.yaml) | 34 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) |
| 579 | [Concerto funebre, RV 579](../../data/works/vivaldi-rv-579.yaml) | 6 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73947224) |
| 581 | [Concerto for violin and double string orchestra, RV 581](../../data/works/vivaldi-rv-581.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 582 | [Violin Concerto, RV 582](../../data/works/vivaldi-rv-582.yaml) | 59 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/107519620) |
| 584 | [Concerto for two violins and two organs, RV 584](../../data/works/vivaldi-rv-584.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) — Adapted for the reconstructed vesper programme. |
| 588 | [Gloria, RV 588](../../data/works/vivaldi-rv-588.yaml) | 36 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73947359) |
| 589 | [Gloria, RV 589](../../data/works/vivaldi-rv-589.yaml) | 36 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73947359) |
| 593 | [Domine ad adiuvandum me festina, RV 593](../../data/works/vivaldi-rv-593.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 594 | [Dixit Dominus, RV 594](../../data/works/vivaldi-rv-594.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 596 | [Confitebor tibi, Domine, RV 596](../../data/works/vivaldi-rv-596.yaml) | 72 | [Coro e Orchestra Ghislieri, Giulio Prandi](https://tidal.com/album/382776448) |
| 600 | [Laudate pueri, RV 600](../../data/works/vivaldi-rv-600.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 601 | [Laudate pueri, RV 601](../../data/works/vivaldi-rv-601.yaml) | 24 | [Accademia Bizantina](https://tidal.com/album/73947302) |
| 607 | [Laetatus sum, RV 607](../../data/works/vivaldi-rv-607.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 608 | [Nisi Dominus, RV 608](../../data/works/vivaldi-rv-608.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 609 | [Lauda Jerusalem, RV 609](../../data/works/vivaldi-rv-609.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 610a | [Magnificat, RV 610a](../../data/works/vivaldi-rv-610a.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 611 | [Magnificat, RV 611](../../data/works/vivaldi-rv-611.yaml) | 72 | [Coro e Orchestra Ghislieri, Giulio Prandi](https://tidal.com/album/382776448) |
| 612 | [Deus tuorum militum, RV 612](../../data/works/vivaldi-rv-612.yaml) | 59 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/107519620) |
| 615 | [Regina coeli, RV 615](../../data/works/vivaldi-rv-615.yaml) | 59 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/107519620) |
| 616 | [Salve Regina, RV 616](../../data/works/vivaldi-rv-616.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 618 | [Salve Regina, RV 618](../../data/works/vivaldi-rv-618.yaml) | 59 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/107519620) |
| 620 | [Sanctorum meritis, RV 620](../../data/works/vivaldi-rv-620.yaml) | 72 | [Coro e Orchestra Ghislieri, Giulio Prandi](https://tidal.com/album/382776448) |
| 621 | [Stabat Mater, RV 621](../../data/works/vivaldi-rv-621.yaml) | 6 | [Concerto Italiano, Rinaldo Alessandrini, Sara Mingardo](https://tidal.com/album/73947224) |
| 623 | [Canta in prato, ride in monte, RV 623](../../data/works/vivaldi-rv-623.yaml) | 10 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/73947162) |
| 625 | [Clarae stellae, scintillate, RV 625](../../data/works/vivaldi-rv-625.yaml) | 6 | [Concerto Italiano, Rinaldo Alessandrini, Sara Mingardo](https://tidal.com/album/73947224) |
| 626 | [In furore iustissimae irae, RV 626](../../data/works/vivaldi-rv-626.yaml) | 24 | [Accademia Bizantina](https://tidal.com/album/73947302) |
| 628 | [Invicti, bellate, RV 628](../../data/works/vivaldi-rv-628.yaml) | 10 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/73947162) |
| 629 | [Longe mala, umbrae, terrores, RV 629](../../data/works/vivaldi-rv-629.yaml) | 10 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/73947162) |
| 630 | [Nulla in mundo pax sincera, RV 630](../../data/works/vivaldi-rv-630.yaml) | 10 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/73947162) |
| 631 | [O qui coeli terraeque serenitas, RV 631](../../data/works/vivaldi-rv-631.yaml) | 10 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/73947162) |
| 633 | [Vestro principi divino, RV 633](../../data/works/vivaldi-rv-633.yaml) | 10 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/73947162) |
| 635 | [Ascende laeta, RV 635](../../data/works/vivaldi-rv-635.yaml) | 11 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73972217) |
| 638 | [Filiae maestae Jerusalem, RV 638](../../data/works/vivaldi-rv-638.yaml) | 59 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/107519620) |
| 641 | [Non in pratis aut in hortis, RV 641](../../data/works/vivaldi-rv-641.yaml) | 59 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/107519620) |
| 642 | [Ostro picta, armata spina, RV 642](../../data/works/vivaldi-rv-642.yaml) | 36 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/73947359) |
| 644 | [Juditha triumphans, RV 644](../../data/works/vivaldi-rv-644.yaml) | 2 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/91797497) |
| 650 | [Allor che lo sguardo, RV 650](../../data/works/vivaldi-rv-650.yaml) | 68 | [Abchordis Ensemble, Andrea Buccarella, Arianna Vendittelli](https://tidal.com/album/202223956) |
| 651 | [Amor hai vinto, RV 651](../../data/works/vivaldi-rv-651.yaml) | 16 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214991) |
| 652 | [Aure, voi più non siete, RV 652](../../data/works/vivaldi-rv-652.yaml) | 68 | [Abchordis Ensemble, Andrea Buccarella, Arianna Vendittelli](https://tidal.com/album/202223956) |
| 654 | [Elvira, anima mia, RV 654](../../data/works/vivaldi-rv-654.yaml) | 5 | [L’Astrée](https://tidal.com/album/92928923) |
| 656 | [Fonti di pianto piangete, RV 656](../../data/works/vivaldi-rv-656.yaml) | 16 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214991) |
| 657 | [Geme l’onda che parte, RV 657](../../data/works/vivaldi-rv-657.yaml) | 16 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92214991) |
| 660 | [La farfalletta s’aggira al lume, RV 660](../../data/works/vivaldi-rv-660.yaml) | 68 | [Abchordis Ensemble, Andrea Buccarella, Arianna Vendittelli](https://tidal.com/album/202223956) |
| 665 | [Si levi dal pensier, RV 665](../../data/works/vivaldi-rv-665.yaml) | 68 | [Abchordis Ensemble, Andrea Buccarella, Arianna Vendittelli](https://tidal.com/album/202223956) |
| 667 | [Sorge vermiglia in ciel la bella Aurora, RV 667](../../data/works/vivaldi-rv-667.yaml) | 68 | [Abchordis Ensemble, Andrea Buccarella, Arianna Vendittelli](https://tidal.com/album/202223956) |
| 669 | [Tra l’erbe i zeffiri, RV 669](../../data/works/vivaldi-rv-669.yaml) | 68 | [Abchordis Ensemble, Andrea Buccarella, Arianna Vendittelli](https://tidal.com/album/202223956) |
| 670 | [Alla caccia dell’alme e de’ cori, RV 670](../../data/works/vivaldi-rv-670.yaml) | 5 | [L’Astrée](https://tidal.com/album/92928923) |
| 671 | [Care selve, amici prati, RV 671](../../data/works/vivaldi-rv-671.yaml) | 5 | [L’Astrée](https://tidal.com/album/92928923) |
| 680 | [Lungi dal vago volto, RV 680](../../data/works/vivaldi-rv-680.yaml) | 19 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92795810) |
| 682 | [Vengo a voi, luci adorate, RV 682](../../data/works/vivaldi-rv-682.yaml) | 19 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92795810) |
| 683 | [Amor, hai vinto, RV 683](../../data/works/vivaldi-rv-683.yaml) | 19 | [L’Astrée, Giorgio Tabacco](https://tidal.com/album/92795810) |
| 684 | [Cessate, omai cessate, RV 684](../../data/works/vivaldi-rv-684.yaml) | 60 | [Accademia Bizantina, Ottavio Dantone, Delphine Galou](https://tidal.com/album/107519638) |
| 685 | [O mie porpora più belle, RV 685](../../data/works/vivaldi-rv-685.yaml) | 60 | [Accademia Bizantina, Ottavio Dantone, Delphine Galou](https://tidal.com/album/107519638) |
| 686 | [Qual in pioggia dorata, RV 686](../../data/works/vivaldi-rv-686.yaml) | 60 | [Accademia Bizantina, Ottavio Dantone, Delphine Galou](https://tidal.com/album/107519638) |
| 687 | [La Gloria e Imeneo, RV 687](../../data/works/vivaldi-rv-687.yaml) | 73 | [Abchordis Ensemble, Andrea Buccarella](https://tidal.com/album/444026485) |
| 690 | [Serenata a tre, RV 690](../../data/works/vivaldi-rv-690.yaml) | 70 | [Abchordis Ensemble, Andrea Buccarella](https://tidal.com/album/276512507) |
| 693 | [La Senna festeggiante, RV 693](../../data/works/vivaldi-rv-693.yaml) | 4 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91800664) |
| 695 | [Adelaide, RV 695](../../data/works/vivaldi-rv-695.yaml) | 22 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/92797025) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 697 | [Argippo, RV 697](../../data/works/vivaldi-rv-697.yaml) | 34 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 699 | [Armida al campo d’Egitto, RV 699](../../data/works/vivaldi-rv-699.yaml) | 22, 38 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/92797025) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 700 | [Arsilda, regina di Ponto, RV 700](../../data/works/vivaldi-rv-700.yaml) | 74, 40 | [La Cetra Barockorchester Basel, Andrea Marcon](https://tidal.com/album/401308324) |
| 702-B | [Atenaide, RV 702-B](../../data/works/vivaldi-rv-702-b.yaml) | 29 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91194048) |
| 703 | [Il Tamerlano (Il Bajazet), RV 703](../../data/works/vivaldi-rv-703.yaml) | 65, 40 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/153965807) |
| 704 | [La Candace, o siano li veri amici, RV 704](../../data/works/vivaldi-rv-704.yaml) | 20, 60 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/92930094) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 705 | [Catone in Utica, RV 705](../../data/works/vivaldi-rv-705.yaml) | 50 | [Il Complesso Barocco, Alan Curtis](https://tidal.com/album/91194446) |
| 706 | [La costanza trionfante degl’amori e degl’odii, RV 706](../../data/works/vivaldi-rv-706.yaml) | 30, 40 | [Accademia Bizantina](https://tidal.com/album/91195549) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 706-B | [Artabano, re de’ Parti, RV 706-B](../../data/works/vivaldi-rv-706-b.yaml) | 40 | [I Barocchisti, Diego Fasolis](https://tidal.com/album/91194278) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 709 | [Dorilla in Tempe, RV 709](../../data/works/vivaldi-rv-709.yaml) | 55, 40 | [I Barocchisti, Diego Fasolis](https://tidal.com/album/81199775) |
| 711 | [Farnace, RV 711](../../data/works/vivaldi-rv-711.yaml) | 22, 40 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/92797025) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 711-D | [Farnace, RV 711-D](../../data/works/vivaldi-rv-711-d.yaml) | 37 | [Le Concert des Nations, Jordi Savall](https://tidal.com/album/91797655) |
| 714 | [La fida ninfa, RV 714](../../data/works/vivaldi-rv-714.yaml) | 32, 30 | [Ensemble Matheus, Jean-Christophe Spinosi](https://tidal.com/album/78146023) |
| 717 | [Il Giustino, RV 717](../../data/works/vivaldi-rv-717.yaml) | 58, 60 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/97762130) |
| 718 | [Griselda, RV 718](../../data/works/vivaldi-rv-718.yaml) | 25 | [Ensemble Matheus, Jean-Christophe Spinosi](https://tidal.com/album/91800793) |
| 719 | [L’incoronazione di Dario, RV 719](../../data/works/vivaldi-rv-719.yaml) | 53, 40 | [Ottavio Dantone](https://tidal.com/album/91801343) |
| 721 | [L’inganno trionfante in amore, RV 721](../../data/works/vivaldi-rv-721.yaml) | 46 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91801069) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 722 | [Ipermestra, RV 722](../../data/works/vivaldi-rv-722.yaml) | 46 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91801069) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 725 | [L’Olimpiade, RV 725](../../data/works/vivaldi-rv-725.yaml) | 8, 22, 50 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/91800556) |
| 727 | [Orlando finto pazzo, RV 727](../../data/works/vivaldi-rv-727.yaml) | 14 | [Academia Montis Regalis, Alessandro de Marchi](https://tidal.com/album/92206658) |
| 728 | [Orlando furioso, RV 728](../../data/works/vivaldi-rv-728.yaml) | 17, 22 | [Ensemble Matheus, Jean-Christophe Spinosi](https://tidal.com/album/78145897) |
| 729 | [Ottone in villa, RV 729](../../data/works/vivaldi-rv-729.yaml) | 41 | [Il Giardino Armonico, Giovanni Antonini](https://tidal.com/album/91194330) |
| 732 | [Scanderbeg, RV 732](../../data/works/vivaldi-rv-732.yaml) | 30 | [Accademia Bizantina](https://tidal.com/album/91195549) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 733 | [Semiramide, RV 733](../../data/works/vivaldi-rv-733.yaml) | 22 | [Concerto Italiano, Rinaldo Alessandrini](https://tidal.com/album/92797025) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 734 | [La Silvia, RV 734](../../data/works/vivaldi-rv-734.yaml) | 20, 22, 30 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/92930094) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 736 | [Teuzzone, RV 736](../../data/works/vivaldi-rv-736.yaml) | 43, 30 | [Le Concert des Nations, Jordi Savall](https://tidal.com/album/92207656) |
| 737 | [Tieteberga, RV 737](../../data/works/vivaldi-rv-737.yaml) | 20, 60 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/92930094) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 738 | [Tito Manlio, RV 738](../../data/works/vivaldi-rv-738.yaml) | 21, 20, 22, 30, 40, 60 | [Accademia Bizantina, Ottavio Dantone](https://tidal.com/album/92206875) |
| 739 | [La verità in cimento, RV 739](../../data/works/vivaldi-rv-739.yaml) | 9, 20, 30, 40, 60 | [Ensemble Matheus, Jean-Christophe Spinosi](https://tidal.com/album/91800729) |
| 740 | [Il Tigrane, RV 740](../../data/works/vivaldi-rv-740.yaml) | 40 | [I Barocchisti, Diego Fasolis](https://tidal.com/album/91194278) — Excerpts: opera arias and/or sinfonia; this album does not contain the complete opera. |
| 749.13 | [Se fido rivedrò (Medea e Giasone), RV 749.13](../../data/works/vivaldi-rv-749-13.yaml) | 20 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/92930094) |
| 749.21 | [Zeffiretti che sussurrate, RV 749.21](../../data/works/vivaldi-rv-749-21.yaml) | 20 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/92930094) |
| 749.32 | [Se fide quanto belle, RV 749.32](../../data/works/vivaldi-rv-749-32.yaml) | 34 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) |
| 781 | [Concerto in D major, RV 781](../../data/works/vivaldi-rv-781.yaml) | 47 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/65306104) |
| 798 | [Violin Sonata, RV 798](../../data/works/vivaldi-rv-798.yaml) | 34 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) |
| 806 | [Recorder Sonata, RV 806](../../data/works/vivaldi-rv-806.yaml) | 34 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) |
| 807 | [Dixit Dominus, RV 807](../../data/works/vivaldi-rv-807.yaml) | 72 | [Coro e Orchestra Ghislieri, Giulio Prandi](https://tidal.com/album/382776448) |
| 810 | [Violin Sonata, RV 810](../../data/works/vivaldi-rv-810.yaml) | 34 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) |
| 811 | [Vos invito, barbare faces, RV 811](../../data/works/vivaldi-rv-811.yaml) | 34, 72 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) |
| 812 | [Concerto for oboe, cello, strings and continuo, RV 812](../../data/works/vivaldi-rv-812.yaml) | 34 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91800957) |
| 815 | [Violin Sonata, RV 815](../../data/works/vivaldi-rv-815.yaml) | 46 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91801069) |
| 816 | [Violin Sonata, RV 816](../../data/works/vivaldi-rv-816.yaml) | 46 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91801069) |
| 817 | [Violin Concerto, RV 817](../../data/works/vivaldi-rv-817.yaml) | 46 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/91801069) |
| 819 | [Orlando 1714, RV 819](../../data/works/vivaldi-rv-819.yaml) | 47, 30 | [Modo Antiquo, Federico Maria Sardelli](https://tidal.com/album/65306104) |

## Vergelijkingsissues

| RV | Issue |
|---|---|
| 61 | [#201](https://github.com/LuHoo/classical_music/issues/201) |
| 63 | [#202](https://github.com/LuHoo/classical_music/issues/202) |
| 64 | [#203](https://github.com/LuHoo/classical_music/issues/203) |
| 65 | [#204](https://github.com/LuHoo/classical_music/issues/204) |
| 66 | [#205](https://github.com/LuHoo/classical_music/issues/205) |
| 73 | [#206](https://github.com/LuHoo/classical_music/issues/206) |
| 75 | [#207](https://github.com/LuHoo/classical_music/issues/207) |
| 78 | [#208](https://github.com/LuHoo/classical_music/issues/208) |
| 79 | [#209](https://github.com/LuHoo/classical_music/issues/209) |
| 155 | [#210](https://github.com/LuHoo/classical_music/issues/210) |
| 169 | [#211](https://github.com/LuHoo/classical_music/issues/211) |
| 179a | [#212](https://github.com/LuHoo/classical_music/issues/212) |
| 181a | [#213](https://github.com/LuHoo/classical_music/issues/213) |
| 207 | [#214](https://github.com/LuHoo/classical_music/issues/214) |
| 210 | [#215](https://github.com/LuHoo/classical_music/issues/215) |
| 229 | [#216](https://github.com/LuHoo/classical_music/issues/216) |
| 242 | [#217](https://github.com/LuHoo/classical_music/issues/217) |
| 260 | [#218](https://github.com/LuHoo/classical_music/issues/218) |
| 261 | [#219](https://github.com/LuHoo/classical_music/issues/219) |
| 263a | [#220](https://github.com/LuHoo/classical_music/issues/220) |
| 332 | [#221](https://github.com/LuHoo/classical_music/issues/221) |
| 362 | [#222](https://github.com/LuHoo/classical_music/issues/222) |
| 363 | [#223](https://github.com/LuHoo/classical_music/issues/223) |
| 379 | [#224](https://github.com/LuHoo/classical_music/issues/224) |
| 391 | [#225](https://github.com/LuHoo/classical_music/issues/225) |
| 454 | [#226](https://github.com/LuHoo/classical_music/issues/226) |
| 515 | [#227](https://github.com/LuHoo/classical_music/issues/227) |

## Validatie

- Canonical validator: nul fouten; nul nieuwe Vivaldi-bevindingen. De 118 bestaande waarschuwingen betreffen andere data.
- Publicatievalidator en paginagenerator: geslaagd.
- Jekyll-build: geslaagd met de aanwezige Homebrew Ruby/Bundler-omgeving.
- Dekking: alle 76 volumes en 401 vermeldingen sluiten aan op canonical Works; geen dubbele aanbeveling per Work; de single van volume 67 is nergens als volledige albumlink gebruikt.
- Tests: 132 tests passed in the full run; its sole failure was the pre-Vivaldi fixed entity counts. After updating those counts, the affected test passed as well (133 tests verified).
