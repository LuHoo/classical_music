# Best Classical — full scan results, 2026-10-03

The complete authenticated catalogue scan passed. Best Classical was not modified.

| Outcome | Track occurrences |
|---|---:|
| Total scanned | 5,518 |
| Streaming available in NL | 4,479 |
| Original ID returns HTTP 404 for NL | 1,039 |
| Confirmed replacement | 609 |
| One ISRC candidate requiring metadata review | 364 |
| No streaming candidate found by original ISRC | 66 |
| Unresolved API errors | 0 |

All 1,039 unavailable originals retained enough identity metadata in playlist includes to recover their original ISRC; no cases lacked a fingerprint. The archived CSV was available as fallback. The source modification marker remained unchanged during the scan.

All 23 original test occurrences (139–146 and 345–359) are included among the 609 confirmed replacements. The full report records the exact old occurrence itemId, ISRC, title, duration, artists, candidate ID, and each matching check. Confirmed candidates are distinct from their original IDs.

The 364 review cases each have exactly one streaming candidate with the original ISRC; these are metadata mismatches rather than multiple-candidate ambiguities:

| Failed checks | Cases |
|---|---:|
| Duration only | 133 |
| Title only | 103 |
| Artist overlap only | 38 |
| Title and duration | 46 |
| Duration and artist overlap | 17 |
| Title and artist overlap | 20 |
| Title, duration and artist overlap | 7 |

Of the 133 duration-only cases, 108 differ by exactly one second and 5 by two seconds. They remain REVIEW under the agreed exact-duration criterion; the scan did not silently relax that rule. A subsequent grouped review could distinguish rounding or remastering metadata from genuinely different recordings.

The 66 NOT_FOUND results mean no streaming-available NL candidate with the original ISRC was found; they do not establish that the recording is absent under every other identifier.

Reports:
- [Full review table](full-playlist-scan-2026-10-03.md)
- [Complete machine-readable evidence](full-playlist-scan-2026-10-03.json)

Successful read-only Actions run: https://github.com/LuHoo/classical_music/actions/runs/37109526198

Nine targeted automated tests passed. Result QA verified totals, 1,039 distinct old occurrence itemIds, direct HTTP 404 evidence, all four identity checks for each confirmed match, replacement IDs different from originals, the unchanged source, and all 23 known cases.

The first scan classified metadata-poor included resources as uncertain. The corrected scanner also performs explicit individual lookups for those placeholders, with two bounded read-only workers, and validates the bulk ID and ISRC endpoints against known examples. The complete corrected run above is authoritative.

Next stage: repair the 609 confirmed occurrences after fresh source and candidate checks. Review the remaining 364 by metadata discrepancy groups; retain the 66 without an exact-ISRC replacement.
