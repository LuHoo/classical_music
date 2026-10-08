# Best Classical — batch 001

Task: [#236](https://github.com/LuHoo/classical_music/issues/236), under the
[#186 intake epic](https://github.com/LuHoo/classical_music/issues/186).
Source: [the curator's playlist](https://tidal.com/playlist/c11f614b-c011-43b2-be10-639f5cf7e5e3).

The curator identified these playlists as their own accepted curation before
supplying this URL. The import therefore checks identity and overlap, without
inventing another listening queue.

## Batch decisions

Ten Works occupy playlist positions **1–33**. Seven are the same interpretations
already represented in canonical data; three become new Works and Performances.
No new competing recommendation requires an editorial choice in this batch.

| Positions | Work | Interpretation | Result |
| --- | --- | --- | --- |
| 1–3 | Mozart: Symphony No. 38, K. 504 | Scottish Chamber Orchestra / Charles Mackerras | Reuse |
| 4–7 | Mozart: Symphony No. 39, K. 543 | Scottish Chamber Orchestra / Charles Mackerras | Reuse |
| 8–11 | Mozart: Symphony No. 40, K. 550 | Scottish Chamber Orchestra / Charles Mackerras | Reuse |
| 12–15 | Mozart: Symphony No. 41, K. 551 | Scottish Chamber Orchestra / Charles Mackerras | Reuse |
| 16–20 | Bartók: Concerto for Orchestra, BB 123 / Sz. 116 | Orchestre National de Lille / Alexandre Bloch | Add; general Work, recorded revision unspecified |
| 21–23 | Bartók: Viola Concerto, BB 128 / Sz. 120, Serly completion | Amihai Grosz / Lille / Bloch | Add specific completion |
| 24–26 | Mozart: Piano Concerto No. 20, K. 466 | Charles Richard-Hamelin / Les Violons du Roy / Jonathan Cohen | Reuse |
| 27–29 | Mozart: Piano Concerto No. 23, K. 488 | Charles Richard-Hamelin / Les Violons du Roy / Jonathan Cohen | Reuse |
| 30 | Mozart: Adagio and Fugue, K. 546 | Les Violons du Roy / Jonathan Cohen | Reuse |
| 31–33 | Górecki: Symphony No. 3, Op. 36 | Dawn Upshaw / London Sinfonietta / David Zinman | Add |

Canonical additions: **1 Person (composer), 3 Work Groups, 3 Works, 3
Performances**. The existing Béla Bartók Person is reused by its actual ID
`388053797e01483593f1e62c6dd407ab`. The seven existing recommendations retain their
canonical IDs and metadata. The JSON manifest records each exact target ID and
all 33 source track/ISRC pairs.

## Source evidence

The [successful authenticated run](https://github.com/LuHoo/classical_music/actions/runs/37006035570)
read the first **100 of 5,518** playlist items, with album/artist/usage-rule
metadata. It checked the same playlist modification marker before and after
reading: `2026-10-02T12:06:31.897Z`. This is a bounded source prefix, not an import
of all 100 items or an assessment of the whole playlist.

All first 33 track IDs and ISRCs agree independently with
`side materials/Music collection/Best Classical.csv`, rows 1–33 (data rows,
excluding the header). The older export has 4,567 entries; it is corroborating
identity evidence, not the current playlist inventory. The companion manifest
retains the live-source hash and selected track identities after the transient
workflow artifact expires.

All 33 selected tracks returned `countryCode: NL`, a past `validFrom`, and
`STREAM` in subscription usage rules. This establishes reported catalogue
streaming rights at the snapshot time, not playback success. Availability and
check timestamps are not added to canonical data.

The API returned empty credit lists for this prefix. Composer and performer
roles are established from trusted repository/catalogue and independent
recording evidence; the import does not infer composer identity from the order
of Tidal's artist list.

## Identity and coverage review

- **Seven Mozart duplicates:** the first track is exactly the existing
  canonical Performance link, the Work catalogue number agrees, and the
  recording/performer evidence is compatible. No title-only match or extra
  Performance is created. The existing K. 543 Work title correctly uses E-flat;
  its stable ASCII ID loses the flat symbol and must not be interpreted as a
  different E-major composition. Existing album-level performer-text
  differences, including the extra pianist in K. 546's legacy metadata, are not
  treated as another interpretation or as an import decision.
- **Bartók catalogue:** `docs/bartok.md`, lines 80 and 84, already accepts the
  Lille/Bloch album and identifies BB 123 / BB 128. The live track titles supply
  Sz. 116 / Sz. 120. The album has eight tracks: five belong to the orchestral
  concerto and three to the viola concerto. Two Performances each reference
  exactly one Work. Amihai Grosz is credited on the viola group, not the other
  concerto; the live catalogue and independent recording source corroborate the
  spelling that differs from the legacy text.
- **Concerto for Orchestra revision:** retrieved source evidence does not
  establish the original or revised ending. The accepted interpretation is
  attached to a general Work with `version_assignment: unspecified`, as allowed
  by `docs/architecture/work.md`. No specific 1943/1945 version is guessed. This
  is explicit non-blocking version uncertainty, not curator-required work.
- **Viola completion:** [Leslie Wright's review of Alpha 1013](https://musicwebinternational.com/2023/11/review-of-concertos-by-bartok-on-alpha-classics/)
  explicitly identifies the original Serly edition as the one Grosz and Lille
  perform. The [publisher's Serly entry](https://www.boosey.com/cr/music/Bela-Bartok-Viola-Concerto-op-posth-ed-Serly/7423)
  independently establishes that completion and its 1949 premiere, distinct
  from the alternative Bartók/Dellamaggiore edition. The imported Work names
  Serly's completion; it is not assigned to the unfinished fragment or a generic
  Work that would hide completion identity. The recording source also establishes
  the 2022 session year. Legacy Gramophone notations `A/2023` and `01/2001` stay
  in `docs/bartok.md`; no unverified review issue is transferred to a 2022
  interpretation.
- **Górecki:** the [publisher's catalogue](https://www.boosey.com/cr/music/Henryk-Mikolaj-Gorecki-Symphony-No-3-Symphony-of-Sorrowful-Songs/5629)
  establishes composer, Op. 36, 1976 and soprano/orchestra scoring. [Nonesuch](https://www.nonesuch.com/albums/g-recki-symphony-no-3-lp)
  establishes Upshaw, London Sinfonietta, Zinman and the May 1991 recording.
  Its digital UPC `075597928266` equals the live album barcode; the three source
  movements and original export ISRCs agree. The 2016 vinyl reissue is the same
  interpretation, not another Performance or the recording date.
- **Performer authority:** existing global Person and artist names/aliases
  contain no canonical entries for Bloch, Grosz, Upshaw or Zinman. Consistent
  names with independently established roles use the minimal schema's supported
  named-performer representation. No per-composer authority duplicates or new
  ensemble entity type are introduced.
- **Coverage and boundary:** the new groups contain all five, three and three
  movements respectively. No Work is manufactured per movement and no extra
  album selection is promoted. Batch 001 ends with Górecki's third movement.

## Next batch

The next unprocessed entry is **position 34**, track **190541071**:
**Arvo Pärt, Tabula Rasa — I. Ludus**, followed by II. Silentium at position 35.
Future work must verify these IDs and the preceding manifest against the current
playlist before using position 34; a reorder invalidates a bare numeric cursor.
No later Works are imported by this PR.

## Completion evidence

Validation results and public rendering evidence are recorded in the draft PR.
The preflight uses the normative architecture, the explicit acceptance
instruction, one Work per Performance and a branch from current `main`.
Adversarial review checked shared-album grouping, wrong-composer/title collisions,
the Serly/fragment boundary, original/revised ambiguity, reissue identity,
stable legacy IDs and a final movement boundary against independent evidence.

Remaining identity cases requiring repository automation: **0**. Blocking
authority gates: **0**. Curator-required choices in this batch: **0**. Explicit
non-blocking revision uncertainty: **1**, described above. Existing background
suspicions are not converted into new curator issues. Runtime JSON and secrets
remain outside the committed tree; the batch manifest is intentionally retained
as source and decision provenance.
