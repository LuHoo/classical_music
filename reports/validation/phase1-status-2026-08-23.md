# Phase 1 Check Status (2026-08-23)

Issue: #127

## What improved in this pass

- Validation checks were expanded to cover more key rules.
- Machine output was made safer for tooling by printing plain JSON.
- Grouped legacy data files are now reported clearly as non-canonical instead of creating noisy cascades.
- New automated tests were added for the new checks.

## Current validation snapshot

- Errors: 275
- Warnings: 350

Top open rule groups by count:

- SCH-005 (unknown fields): 233
- SCH-003 (required fields missing): 133
- DOM-044 (missing performer details): 116
- DUP-003 (possible duplicate works): 59
- DUP-002 (possible duplicate work groups): 56
- REF-002 (work composer links): 17
- CAN-002 (legacy grouped canonical files): 7

## What this means

- The checking system is stronger and clearer.
- The remaining work is mostly data cleanup and normalization.
- Legacy grouped files need conversion into one-file-per-record canonical shape.

## Next actions

1. Fix missing required fields in canonical files.
2. Fix missing or invalid performer details.
3. Resolve unknown fields by either renaming or documenting allowed fields.
4. Convert grouped legacy files flagged by CAN-002.
5. Review duplicate warnings and decide case-by-case.
