# Full TIDAL playlist availability scan

The scanner reads the entire current Best Classical playlist and reports unavailable occurrences and candidate replacements. It cannot perform write requests. The user's local disposable write test passed on 2026-10-03; that verified OAuth and occurrence-aware playlist mutations, but this full-scan stage remains report-only.

Run `python3 scripts/scan_tidal_playlist.py` from the repository root, with a catalogue access token or the existing app credentials supplied securely through the environment. Python 3.9 or newer is supported by these standalone scripts. The read-only GitHub Actions workflow uses the existing `TIDAL_CLIENT_ID` and `TIDAL_CLIENT_SECRET` secrets; it requires no user token.

Two known-ID and ISRC preflight checks validate bulk query behavior before scanning. The scanner uses a full cursor-paginated snapshot with included track, artist and album metadata, checks its item count, and verifies `lastModifiedAt` both after pagination and after matching. Ordered occurrences and item IDs are retained. Missing included resources are queried in batches of at most 20 IDs; a resource still missing availability metadata (including an included placeholder) receives an individual lookup through two bounded read-only workers. An explicit HTTP 404 for countryCode=NL or an explicit availability list without STREAM establishes catalogue unavailability for NL. A network failure, 429, 5xx, missing availability metadata, or failed catalogue search remains uncertainty, never proof that a recording disappeared.

For unavailable tracks, original ISRC, title, duration and performers are taken from live metadata and, where unavailable, the existing CSV export by old track ID. Catalogue recovery uses batches of at most 20 ISRCs and follows bounded pagination. No title-based replacement is guessed when an original ISRC cannot be recovered.

Classifications:

| Status | Meaning |
|---|---|
| CONFIRMED | Exactly one streaming-available NL candidate with identical ISRC, normalized title, exact duration, and at least one overlapping credited artist; old occurrence itemId is present. |
| REVIEW | Multiple playable manifestations, incomplete identity evidence, a metadata mismatch, or a missing occurrence itemId. No automatic selection. |
| NOT_FOUND | Completed exact-ISRC search found no streaming candidate in NL. |
| MISSING_FINGERPRINT | No valid original ISRC could be recovered from live data or the archived export. |
| UNCERTAIN | Original resource check failed or lacked availability metadata. |
| UNCERTAIN_SEARCH | An unavailable original was established, but the recovery search failed or exceeded its bounded pagination. |
| UNSUPPORTED_MEDIA | A non-track occurrence; preserved without attempting replacement. |

Normalization only changes case, diacritics and punctuation; it does not reinterpret titles or select another performance. Catalogue STREAM availability does not independently verify user-account playback. Matching is conservative: translated titles or differently formatted credits can require review even for the same recording.

Outputs are `reports/tidal-maintenance/full-playlist-scan.json` and `.md`. The JSON contains exact occurrence itemIds, old metadata evidence, candidate IDs and individual checks. The Markdown provides aggregate counts and a review table. Actions stores the full operational reports as a 14-day artifact. A dated summary can be committed separately after result review.

Nine automated tests cover exact matching, metadata mismatches, multiple manifestations, unplayable candidates, recovery from the archived CSV, transient HTTP errors, repeated occurrences, missing fingerprints and refusal of write methods.

```bash
python3 -m unittest discover -s tests -p test_scan_tidal_playlist.py
```

The next repair stage must re-read the source and revalidate the original occurrence and replacement before writing; the historical report is not itself an instruction to delete anything. Unavailable originals without a confirmed replacement remain in the playlist.

Official contract checked: https://tidal-music.github.io/tidal-api-reference/tidal-api-oas.json, version 1.10.148; `GET /tracks` documents `filter[id]` and `filter[isrc]` with at most 20 identifiers per query.
