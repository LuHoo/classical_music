# Live playlist recovery pilot — 2026-10-03

Status: live read and replacement planning passed; live write test awaits user OAuth authorization. No source-playlist mutations.

- Live playlist: Best Classical, `c11f614b-c011-43b2-be10-639f5cf7e5e3`.
- Full stable snapshot: 5,518 track occurrences; count agrees with API metadata.
- Modification marker unchanged during pagination: `2026-10-02T12:06:31.897Z`.
- Every occurrence has an API `itemId`. No repeated track IDs in this snapshot.
- All 23 reported old IDs remain at the originally reported positions.
- Each has exactly one streaming-available NL candidate with the original ISRC and duration.
- The dry-run sequence retains 5,518 entries and changes only positions 139–146 and 345–359.
- `TIDAL_USER_ACCESS_TOKEN` was absent. App credentials successfully read the public playlist, but no user-authorized writes were attempted.
- Five targeted automated tests passed; disposable write logic is tested with fake responses, not yet against the live API.

Successful Actions run: https://github.com/LuHoo/classical_music/actions/runs/37107238970

The earlier attempt stopped at a conservative 200-page cap. The bounded limit was raised to 1,000 pages / 10,000 items; the complete retry passed. The older CSV contains 4,567 rows and is not a current inventory.

| Live position | Old ID | Verified new ID | Exact old occurrence itemId |
|---:|---|---|---|
| 139 | 160324010 | 283191456 | 36aa41d2-c8b5-44dc-955d-46b383dc80fa |
| 140 | 160324011 | 283191455 | 9b79dc83-8f44-4f6a-b049-78dd14d72d61 |
| 141 | 160324012 | 283191457 | 908b8228-700f-4682-8e7e-f55b1143a29e |
| 142 | 160324013 | 283191458 | 9e3cd378-7395-437f-98ac-ac02b1a5e994 |
| 143 | 160324014 | 283191459 | 5abe1096-67d9-46bc-974a-0cab37ec4eae |
| 144 | 160324015 | 283191460 | 0d9e1551-17ed-43c8-b495-87464bd61b18 |
| 145 | 160324016 | 283191461 | d8da4d69-dfd2-4f58-8611-cb7ca0db3398 |
| 146 | 160324017 | 283191462 | 7f57f7dd-e8b3-43aa-ad26-0162563a9323 |
| 345 | 151740135 | 282819593 | cb9ea6b4-2850-4c0c-8ea9-8a714bab9b59 |
| 346 | 151740136 | 282819594 | 745b3c21-1b68-42ac-aeac-c8e7d8d5620c |
| 347 | 151740137 | 282819595 | b6cfde2a-f2f4-4850-a428-92fff223c868 |
| 348 | 151740138 | 282819596 | 6ae92c5a-4fa2-4828-a799-74be33c81e0e |
| 349 | 151740139 | 282819597 | 21ce2733-6a92-419f-971a-59ac7c65426f |
| 350 | 151740140 | 282819598 | b490425d-f638-4c49-943b-a7503b243176 |
| 351 | 151740141 | 282819599 | effcff3d-5cd3-4b02-9052-dcb7cc663956 |
| 352 | 151740142 | 282819600 | 97caf044-9fa7-446a-bb8f-6d48e799b4bf |
| 353 | 151740143 | 282819601 | 581352f2-104f-46f2-8c1f-fb7060352712 |
| 354 | 151740144 | 282819602 | 844186c8-6114-4f1d-8494-193f1bf0fac6 |
| 355 | 151740145 | 282819603 | 01a08629-c602-4308-9821-db12283f8bfa |
| 356 | 151740146 | 282819604 | 29a1784c-29c5-49a3-8aee-8c534af06510 |
| 357 | 151740147 | 282819605 | 413421bb-3e0d-4df4-a798-98df3a117ed6 |
| 358 | 151740148 | 282819606 | 649558c9-208e-456d-acbb-b7675e9abb05 |
| 359 | 151740149 | 282819607 | d8eac248-243b-42af-b23f-01414f1fb2c8 |

For the one-time local login and disposable write test, see [the pilot instructions](../../../docs/workflows/tidal-playlist-recovery-pilot.md). The temporary test playlist is deleted after the test; Best Classical is never modified by that command. A subsequent source repair must fetch a fresh snapshot and compare occurrence identities rather than using this historical plan blindly.

