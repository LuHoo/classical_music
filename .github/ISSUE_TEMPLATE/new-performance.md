---
name: New performance
about: Register a candidate performance (TIDAL album) for the curator workflow (design issue #435)
title: "New performance: <performance / album>"
---

Fill in only the TIDAL album URL — work IDs or track IDs are not needed.
The registration script resolves composers and works from the album itself and
resolves the comparison work: a unique candidate is selected automatically;
multiple candidates trigger an interactive prompt. Works without an existing
recommendation are reported as candidates for direct adoption; tracks without
a canonical work get a parking issue. See `docs/workflows/new-performance-issue.md`.

### TIDAL album URL (required)

https://tidal.com/album/<id>

### Notes (optional)

Why this candidate? Context for the curator decision.

---

## Processing (script)

The curator runs this workflow locally — the script does the work.

1. Note this issue's number (`<nr>`), then register the album:

   ```bash
   source ~/.tidal/env
   .venv/bin/python scripts/register_earmarked_recording.py "https://tidal.com/album/<id>" --issue <nr> --comment
   ```

2. `--comment` posts the registration report as a comment on this issue (via
   `gh`; without `gh` the terminal output is the fallback).
3. Tracks without a canonical work: add `--create-parking-issue` to have the
   script open a separate parking issue (duplicate check on the album URL;
   advisory MusicBrainz evidence; canonization remains a curator decision).
4. Decide via the comparison route `./curator <nr> <choice> --apply` (or direct
   adoption via curator record + PR), then close with `./curator finish`; git
   stays manual.
