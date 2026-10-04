# Playlist recovery API pilot — 2026-10-03

The authenticated official TIDAL catalogue pilot found one exact ISRC match for each of the 23 reported unavailable tracks. All old IDs returned HTTP 404; all new candidates advertised STREAM availability for countryCode=NL and had the same duration as the CSV export. No playlist was modified.

Source: `side materials/Music collection/Best Classical.csv`. Positions refer to this existing export, not a newly fetched live playlist. The old recording identifiers remain recoverable because this export retained the ISRCs. Account-level playback and user-authorized playlist read/write access were not tested.

Run: https://github.com/LuHoo/classical_music/actions/runs/37106634757

Script: `scripts/playlist_recovery_pilot.py` on branch `issue-64-tidal-link-maintenance`. Credentials were supplied exclusively by GitHub Actions secrets; the token was not persisted.

| Export position | Old ID | Verified new URL | ISRC | Duration (s) |
|---:|---:|---|---|---:|
| 139 | 160324010 | https://tidal.com/track/283191456 | GBYDS2000298 | 475 |
| 140 | 160324011 | https://tidal.com/track/283191455 | GBYDS2000299 | 564 |
| 141 | 160324012 | https://tidal.com/track/283191457 | GBYDS2000300 | 506 |
| 142 | 160324013 | https://tidal.com/track/283191458 | GBYDS2000301 | 307 |
| 143 | 160324014 | https://tidal.com/track/283191459 | GBYDS2000302 | 289 |
| 144 | 160324015 | https://tidal.com/track/283191460 | GBYDS2000303 | 502 |
| 145 | 160324016 | https://tidal.com/track/283191461 | GBYDS2000304 | 606 |
| 146 | 160324017 | https://tidal.com/track/283191462 | GBYDS2000305 | 204 |
| 345 | 151740135 | https://tidal.com/track/282819593 | FINDE2000078 | 85 |
| 346 | 151740136 | https://tidal.com/track/282819594 | FINDE2000079 | 348 |
| 347 | 151740137 | https://tidal.com/track/282819595 | FINDE2000080 | 428 |
| 348 | 151740138 | https://tidal.com/track/282819596 | FINDE2000081 | 186 |
| 349 | 151740139 | https://tidal.com/track/282819597 | FINDE2000082 | 134 |
| 350 | 151740140 | https://tidal.com/track/282819598 | FINDE2000083 | 262 |
| 351 | 151740141 | https://tidal.com/track/282819599 | FINDE2000084 | 480 |
| 352 | 151740142 | https://tidal.com/track/282819600 | FINDE2000085 | 202 |
| 353 | 151740143 | https://tidal.com/track/282819601 | FINDE2000086 | 185 |
| 354 | 151740144 | https://tidal.com/track/282819602 | FINDE2000087 | 235 |
| 355 | 151740145 | https://tidal.com/track/282819603 | FINDE2000088 | 451 |
| 356 | 151740146 | https://tidal.com/track/282819604 | FINDE2000089 | 373 |
| 357 | 151740147 | https://tidal.com/track/282819605 | FINDE2000090 | 206 |
| 358 | 151740148 | https://tidal.com/track/282819606 | FINDE2000091 | 392 |
| 359 | 151740149 | https://tidal.com/track/282819607 | FINDE2000092 | 394 |

Next stage: verify the official user OAuth playlist-read and playlist-write capabilities, read the live playlist and preserve occurrence order and duplicates. Do not interpret this catalogue pilot as a successful playlist repair.

