# Best Classical: final Bruckner comparison (37 tracks)

The curator authorised completing this comparison on 2026-10-02. All 37 tracks
at positions 279–315 represent ten interpretations already present in canonical
data. No Person, Work Group, Work or Performance is added. Track 333 remains
deferred. This report supersedes the earlier Bruckner-deferred disposition;
the earlier scale and preparation reports remain historical evidence.

## Exact recording evidence

The read-only reference audit queried ten exact canonical Tidal track IDs:
https://github.com/LuHoo/classical_music/actions/runs/37053043146.
Each canonical first-track ISRC matches the selected first track of its musical
unit exactly. All ten canonical tracks belong to Tidal album 384348581,
*Bruckner: The Symphonies*. The Naxos 8.501804 box catalogue independently
identifies the component Capriccio recordings. Each selected unit stays within
its original component release. The matching is not based on conductor/name
similarity alone. `bruckner-37.json` retains all 37 selected positions, track IDs
and ISRCs, component barcodes, canonical anchors and final Work assignments.

## Versions and editions

| Positions | Selection | Version | Edition | Original CD |
|---|---|---|---|---|
| 279–282 | Symphony 5 | 1878 | Nowak | C8090 |
| 283–286 | Symphony 4 | 1888 | Korstvedt | C8085 |
| 287–290 | Nullified Symphony | 1869 | Nowak | C8082 |
| 291–294 | Symphony 8 | 1890 | Nowak | C8081 |
| 295–298 | Symphony 6 | 1881 | Haas, prepared by Williamson | C8080 |
| 299–302 | Symphony 3 | 1873 | Nowak | C8086 |
| 303–306 | Symphony 4 | Second version, 1878–1880 / 1881 performance text | Korstvedt | C8083 |
| 307 | Symphony 4: Volksfest finale only | 1878 | Korstvedt | C8083 |
| 308–311 | Symphony 8 | 1887 | Hawkshaw | C8087 |
| 312–315 | Symphony 2 | 1877 | Hawkshaw | C8089 |

Primary sources:

- Naxos box catalogue, component recordings and editions:
  https://www.naxos.com/CatalogueDetail/?id=8.501804
- Capriccio C8083: second version and separately recorded Volksfest finale:
  https://capriccio.at/bruckner24-4-the-complete-versions-edition
- C8089 booklet, printed pp. 9 and 15–17: comparison with Carragan's edition
  and the explicit cycle edition table:
  https://cdn.naxosmusiclibrary.com/sharedfiles/booklets/CAR/booklet-C8089.pdf
- Naxos 2023 Capriccio catalogue, printed p. 86, C8080 entry:
  https://cdn.naxos.com/sharedfiles/PDF/Capriccio.pdf
  (indexed catalogue text identifies Haas, prepared by John Williamson).

The last source reconciles the cycle booklet's Williamson attribution with
the shorter Haas attribution in the product catalogue. These editorial
attributions do not create new artistic Works. For C8089, the booklet and box
catalogue identify Hawkshaw; the Carragan string present on both Tidal releases
is conflicting provider metadata and is not used to assign the edition.

## Canonical corrections

The two existing Symphony 4 Performances were attached to the wrong versions:
the Linz track 384348624 starts the complete second-version symphony, while the
ORF track 384348628 is only the alternative 1878 Volksfest finale. Their Work
assignments are exchanged, preserving the existing Performance IDs, performers,
Tidal links and accepted recommendations. Historical ID wording is not used as
musical identity. The ORF Performance now explicitly displays
`excerpt: Volksfest finale only`. The complete Linz interpretation belongs to
the existing third local Work entry, whose date label is clarified as
1878–1880 / 1881 performance text. No full 1878 interpretation is invented.

Symphony 2's existing 1877 Work no longer conflates that version with the 1892
printed revision. Its Performance records Hawkshaw and the primary evidence.
The corrected Works receive explicit version fields and version-qualified titles
so their distinct artistic identities are visible rather than relying on dates.
Symphony 6 records the Haas/Williamson preparation. The corresponding three
lines in the legacy composer document are corrected to keep its links and
version descriptions consistent with canonical data. Other Bruckner entries
remain unchanged.

The corrections preserve the previously accepted interpretations and retain
their identities; no competing recording is selected. An exact first-track
ISRC plus the box's component-release and version evidence supports reissue
reuse. The audit does not claim live playback or complete per-movement ISRC
matching against the box. API rights metadata remains outside canonical data.

## Final disposition of positions 34–333

| Disposition | Tracks | Performances |
|---|---:|---:|
| Existing recommendations, including Bruckner | 179 | 43 |
| Newly imported recommendations | 120 | 33 |
| Deferred boundary track 333 | 1 | — |
| Total | 300 | |

Actual canonical and publication verification is recorded in `bruckner-37.json`.
The Symphony 4 pages must show the Linz full recording and ORF finale on their
respective Works, with the excerpt label visible. Collection totals stay at
1,516 Works and 974 Performances. The work remains on draft PR #237; no merge
or deployment is performed.
