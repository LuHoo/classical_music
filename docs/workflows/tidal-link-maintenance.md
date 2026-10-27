# Tidal link maintenance — issue #64, local implementation

This workflow maintains locators on accepted canonical Performances. It never
creates a Performance, promotes a candidate, modifies `keep_looking`, or deploys
the website. The only automated GitHub issues are curator-review requests for
confirmed-dead links (approved in issue #64, 2026-10-25); they change nothing.

## Architecture pre-flight

1. Governing documents read: `architecture-principles.md`,
   `repository-architecture.md`, `performance.md`, `recommendation-policy.md`,
   `minimal-yaml-schemas.md`, and `workflow-design-notes.md` under
   `docs/architecture/`. ADR 0004 is superseded and is not normative.
2. Purpose: keep listening links useful without changing musical recommendations.
3. Smallest scope: a local command, one JSON/Markdown report, optional verified
   URL updates, plus a bounded authenticated GitHub Actions pilot. The
   curator-approved extension of 2026-10-25 (issue #64) adds an hourly
   report-only rotation round of 20 URLs and curator-review issue escalation;
   still no new canonical entity.
4. Identity: no Person or Work identity changes; preserve trusted legacy input.
5. Curator load: group shared URLs, separate technical uncertainty from confirmed
   missing pages, and make no automatic curator queue.
6. Boundary: only replacement URLs are durable canonical metadata. Status,
   timestamps and identity fingerprints remain operational artifacts.
7. External authority: the official Tidal API is optional and demand-driven for
   matching the same resource, not for comprehensive catalogue enrichment.
8. Simplicity: ordinary resource-specific public HTML is enough for the initial
   availability check; an API is not required to run the checker.
9. Git: feature branch from main, tests/validation, draft PR; no merge.
10. Success: repair proven locators, retain accepted recommendations, and avoid
    treating a network block or a similar title as a musical decision.

## Run locally

Install the project dependencies as usual (Python 3.13):

```bash
python -m pip install -e '.[dev]'
python scripts/check_tidal_links.py --limit 10
python scripts/check_tidal_links.py
```

The inventory reads only `data/performances/*.yaml`, supporting both existing
mapping and list forms of `links`. Each unique URL is checked once. Legacy HTTP,
`www`, and `browse` forms are requested through the equivalent HTTPS resource.
The default delay is 0.5 seconds and the timeout is 15 seconds per request.
A run is sequential and bounded; there are no automatic retries on throttling.
Use `--limit` for a small pilot before checking the collection.

Default outputs are `reports/tidal-maintenance/latest.json` and `latest.md`.
They are ignored by git. The JSON stores `status` and UTC `last_checked` for each
URL and each referencing Performance, along with reasons and identity evidence.
The existing output is loaded before a subsequent run to preserve verified
fingerprints. `--previous <report.json>` can select another baseline explicitly.
A limited run retains earlier fingerprints for unchecked URLs; only the checked
URLs receive fresh statuses/timestamps. This is a report of observations, not a
permanent declaration of availability.

| Status | Meaning |
| --- | --- |
| `ok` | Resource-specific Tidal content is present. |
| `redirect` | Same-ID URL normalization/redirect, or a proven replacement ID. |
| `unavailable` | HTTP 404/410 or the observed Tidal HTTP-200 content-not-found page. |
| `uncertain` | Access blocked, timeout, throttling, generic app shell, unsupported URL, or unresolved replacement evidence. |

A public page proves catalogue-page availability, **not regional playback
rights**. HTTP-200 by itself is insufficient. Live observations on 2026-10-02:
`https://tidal.com/album/187335103` returned MusicAlbum JSON-LD; a deliberately
nonexistent album ID returned HTTP-200 with `Not Found - TIDAL` and
`The requested content could not be found on TIDAL.` Metadata format changes
fall back to `uncertain` rather than deleting a link.

## Recover the same Performance

A redirect retaining the album/track ID is safe. A changed ID requires identity
evidence from the original URL, captured on an earlier successful run or still
retrievable through the official API. Evidence is bound to that URL and cannot
be reused merely because the Performance ID is unchanged.

For tracks, Tidal's public MusicRecording JSON-LD provides `isrcCode`. For albums,
the optional API supplies `barcodeId`. With API access, the checker looks up exact
ISRC/barcode matches after a missing or uncertain page; it does not conduct a
search for a different interpretation or use `keep_looking` as a trigger.

```bash
# Set TIDAL_ACCESS_TOKEN securely in your environment; do not commit it.
python scripts/check_tidal_links.py --use-api --country NL
python scripts/check_tidal_links.py --use-api --country NL --apply
```

Provide an access token, or set `TIDAL_CLIENT_ID` and `TIDAL_CLIENT_SECRET`
from your Tidal developer app. With app credentials, `--use-api` obtains a
temporary token through the official client-credentials flow. Token requests
refuse redirects and never print provider error bodies or credentials. On
GitHub Actions the generated token is masked; it is not stored in a file or
report. Official API contract consulted:
[Tidal Web API reference](https://tidal-music.github.io/tidal-api-reference/),
`https://openapi.tidal.com/v2`, `GET /tracks/{id}`, `GET /albums/{id}`,
`GET /tracks?filter[isrc]=…`, `GET /albums?filter[barcodeId]=…` with `countryCode`.
No private/undocumented endpoints or embedded application tokens are used.

Existing technical discovery tools can also supply candidate **URLs for the
same Performance**, not recommendation candidates:

```json
{
  "https://tidal.com/track/123": ["https://tidal.com/track/456"]
}
```

Pass this as `--recovery-urls urls.json`. Each destination is fetched anew.
A track replacement requires the exact original ISRC. An album replacement
requires the exact original barcode verified by the API. Titles and artists
alone are insufficient. Cross-kind targets, generic pages, different identifiers,
multiple verified matches and partial/paginated search results cannot cause an
update. Multiple equivalent manifestations remain technical uncertainty and
are not automatically labelled curator work.

Without an API token, public-page checking, same-ID normalization/redirect repair,
and ISRC verification of supplied replacement track URLs work. Automatic global
replacement discovery and album-barcode verification require API access. If a
link has already disappeared before any fingerprint was captured and the API
cannot retrieve its identity, this implementation cannot safely recover it from
names alone. It reports the evidence gap; it does not ask the curator to select
a different recommendation. API behavior is covered with independent protocol
fixtures. The bounded live pilot below tests the same API contract against
the configured app credentials.

`--apply` updates only verified `links.tidal.url` (or the equivalent list entry).
The default is report-only. YAML comments and quoting are round-tripped. Each
canonical file is re-read and checked against the inventory before edits are
written, so a concurrent editorial change aborts the update. Recommendations,
profiles, notes, reviews, performers and `keep_looking` remain unchanged.

## Previous candidates are context only

Recommendation history is not canonical data. Optionally pass a small existing
history export with `--previous-candidates history.json`:

```json
[
  {
    "work_id": "canonical-work-id",
    "profile": null,
    "url": "https://tidal.com/album/123",
    "source": "https://github.com/LuHoo/classical_music/issues/456"
  }
]
```

Confirmed unavailable links show matching entries for the same Work and profile
in both reports, or explicitly state that none were supplied. The checker does
not invent a recommendation history, fetch or promote these candidates, open
issues, or search for other Performances. An unavailable URL remains attached to
its accepted recommendation and is labelled `no longer available at this Tidal
URL`; this does not claim the Performance has vanished from all of Tidal.

## Hourly rotation ledger

`--state reports/tidal-maintenance/state.json` (with `--limit N`) changes the
selection from "first N URLs" to a rotation: the N least recently checked URLs,
never-checked URLs first, ties broken deterministically by URL. The ledger is
an operational artifact outside `data/`, never canonical metadata. It records
`last_checked`, `status`, and a consecutive-problem counter (`strikes`) per
URL. The counter resets on any healthy check and restarts on a different
problem status.

```bash
python scripts/check_tidal_links.py --use-api --country NL \
  --state reports/tidal-maintenance/state.json --limit 20
```

With a few thousand unique URLs, an hourly round of 20 URLs covers the whole
collection in roughly one week.

## Escalation to curator-review issues

`scripts/escalate_tidal_failures.py` turns problem findings into exactly one
open issue per URL (label `tidal-link-broken`, deduplicated by a stable HTML
marker containing the URL):

- a confirmed `unavailable` URL escalates immediately;
- an `uncertain` URL escalates only after `--uncertain-after` (default 3)
  consecutive problem rounds, to avoid issue floods on transient throttling
  or network blocks;
- `ok`/`redirect` URLs never escalate;
- an existing open issue receives one comment per new check result instead of
  a duplicate issue.

An issue body lists the Performance, Work, file, URL, reason, and supplied
previous candidates as context, and states explicitly that nothing is promoted
and the recommendation stays unchanged. The script requires `GITHUB_TOKEN`
(or `--dry-run` to inspect planned actions without any API call). The
recovery search itself runs inside the check (exact ISRC/barcode identity
only); if it finds no safe replacement, the issue is the call for curator
review. Safe URL repairs remain a local `--apply` decision; the workflow never
writes to repository contents.

## Authenticated GitHub Actions pilot

Set repository Actions secrets `TIDAL_CLIENT_ID` and `TIDAL_CLIENT_SECRET`.
`.github/workflows/tidal-link-check.yml` provides a report-only pilot using
`scripts/run_tidal_api_check.py`. It obtains a temporary token in memory,
checks one independently observed track ISRC and an album barcode, exercises
both exact-identifier search endpoints, then checks 5 collection URLs by
default. An authentication/metadata pre-flight failure fails the job before a
misleading successful maintenance report can be produced.

The job has read-only repository permissions, a 15-minute timeout and a maximum
of 50 URLs. Credentials are scoped to the pilot step; checkout does not retain
a Git token. Output is one JSON/Markdown artifact retained for 14 days and a
Markdown job summary. It cannot apply URL changes, publish recommendations,
open issues, or deploy the site.

Once the workflow is on the default branch, use **Actions → Tidal link check →
Run workflow** and select the branch and limit. GitHub requires the workflow
file to exist on the default branch before offering manual dispatch. To test
this draft without merging, a narrow bootstrap trigger also runs on pushes to
`issue-64-tidal-link-maintenance` that change the workflow or its runtime code.
It is not a recurring schedule and does not run on other feature branches or
pull requests from forks.

## Scheduled hourly maintenance round

The `round` job in the same workflow runs hourly (`cron: "17 * * * *"`, an off-peak minute because GitHub drops delayed runs during peak load at :00) once the
workflow reaches the default branch; GitHub only schedules from there. Use
**Actions -> Tidal link check -> Run workflow** with the `run_round` input to
test a round manually before merging. Each round:

1. checks the 20 least recently checked URLs (`--state` rotation, `--use-api`
   with the repository secrets `TIDAL_CLIENT_ID`/`TIDAL_CLIENT_SECRET`);
2. persists the rotation ledger and the latest report through `actions/cache`
   (`tidal-maintenance-state-v1`), so a cache miss only resets rotation order,
   never correctness;
3. escalates problem URLs with `scripts/escalate_tidal_failures.py` and the
   ephemeral `GITHUB_TOKEN`, under `permissions: issues: write` - it can open
   or comment on issues and nothing else;
4. uploads the round report as a 14-day artifact and writes a job summary.

The round never writes repository contents, never applies URL repairs, and
never changes recommendations. Safe repairs found during a round appear in the
report; apply them locally with `--apply` and a maintenance PR.

## Validation and adversarial evidence

`tests/test_tidal_maintenance.py` verifies actual behavior for soft 404s, access
blocks, generic shells, wrong-resource metadata, changed-ID redirects without
evidence, exact/mismatched ISRCs, ambiguous replacements, wrong resource kinds,
stale URL fingerprints, shared links, both YAML shapes, unchanged editorial
metadata, previous-candidate profile filtering, concurrent edits, official API
barcode recovery, token exclusion and pagination refusal. Tests use independent
input responses, not the checker's own labels as expected ground truth.

Authentication and workflow tests in `tests/test_tidal_auth.py` verify the
client-credentials request, explicit-token precedence, redaction of provider
errors, runner masking, refusal of authentication/Bearer redirects, an
independent ISRC mismatch, exact-search pre-flight, environment cleanup,
read-only permissions, bounded branch triggers, and the bounded hourly round
contract (twenty URLs, issue-write only, no `--apply`). The rotation ledger and
escalation behaviour - never-checked-first ordering, strike counting,
threshold-gated uncertainty, marker deduplication, and the explicit
no-promotion wording - are covered in `tests/test_tidal_maintenance.py`,
including a token-free `--dry-run` subprocess test. Tests contain only
synthetic credentials.

## Fingerprint backfill (issue #396)

Recovery of a removed URL is only possible when the original URL's identity
fingerprint (ISRC for tracks, barcode for albums) was captured while the URL
was still alive. If an anchor dies before the hourly rotation ever checked
it, the round can only report "original identity fingerprint unavailable;
no replacement search" (the #392/#393 pattern).

`scripts/backfill_tidal_fingerprints.py` closes that gap systematically:

- it selects canonical Tidal URLs that do not have a fingerprint yet —
  never-attempted first, then least recently attempted, deterministically;
- for up to 60 URLs per run (default) it queries the authenticated Tidal
  API for the identifier, with an unauthenticated JSON-LD page fallback;
- a failed attempt (dead or blocked URL) is recorded and retried only after
  all unknown URLs have been attempted once;
- it persists the ledger in
  `reports/tidal-maintenance/fingerprints.json` (shared Actions cache entry
  with `state.json` and `latest.json`) and adopts fingerprints recorded by
  check rounds from `latest.json`, so both sides converge;
- it adopts ISRC fingerprints from the raw playlist-import snapshots under
  `reports/playlist-import/` (see below).

The workflow `.github/workflows/tidal-fingerprint-backfill.yml` runs this
twice per hour (minutes 13 and 43 — quiet minutes offset from the hourly
round at minute 17) under `permissions: contents: read` only. The cadence
is deliberately few-but-large: GitHub's scheduler is best-effort, throttles
high-frequency schedules and silently drops queued runs under load, so a
declared 6x20 schedule delivered no runs at all in practice (issue #401).
Two 60-URL runs keep the same declared throughput with fewer ticks to
lose; the job timeout (20 minutes) covers the worst case of 60 sequential
15-second timeouts.

The hourly round passes `--previous reports/tidal-maintenance/fingerprints.json`
so `recover()` sees the full backfill ledger as its fingerprint source; the
ledger shape (`{"version": 1, "fingerprints": {...}}`) is intentionally the
same `fingerprints` mapping that `check_tidal_links.py --previous` reads.

Run locally:

```bash
source ~/.tidal/env  # or export TIDAL_CLIENT_ID / TIDAL_CLIENT_SECRET
python scripts/backfill_tidal_fingerprints.py --use-api --country NL \
  --state reports/tidal-maintenance/fingerprints.json --limit 60
```

### Import adoption (issue #410)

The playlist-import snapshots (`snapshot-*.json`, `window-*.json` under
`reports/playlist-import/`) are raw Tidal API artifacts captured while every
URL was still alive: their `units[].tracks[]` entries carry the original track
IDs and ISRCs. They are therefore earlier Tidal evidence than the ledger
itself. The backfill adopts these ISRCs into the ledger on every run:

- only `snapshot-*.json` and `window-*.json` files are read; other intake
  files are ignored;
- tracks are matched to canonical URLs by Tidal resource identity, so
  `http://www.tidal.com/track/1` in a performance file and
  `https://tidal.com/track/1` in a snapshot are the same anchor, and the
  fingerprint is stored under the exact canonical URL string;
- an existing identifier is never overwritten; a `source` field records the
  snapshot the ISRC came from;
- a malformed recognized snapshot fails closed.

Measured on 2026-10-27: this closes the evidence gap for 2,196 of the 2,461
canonical URLs. Of the 358 dead anchors found in a full page scan, 346
recovered their ISRC from the imports and are repairable by the existing
`recover()` without any curator action; only 12 remained without evidence.

### Report transparency (issue #402)

The run report (`fingerprints.md`, shown in the job summary and uploaded as a
workflow artifact) does not only show aggregate counts. It renders, from the
ledger after the run:

- **Pending URLs by status** — the full pending pool split over the
  `status` values the capture path records (`unavailable`, `uncertain`, …)
  plus `never-attempted`, so a run's `attempted 60, captured 20` can be read
  back as "40 attempts landed, this is how the remainder is distributed";
- **Confirmed unavailable** — every pending canonical URL with
  `status: unavailable`, together with the referencing performance ids,
  work ids and YAML files, so a dead anchor can be repaired immediately
  instead of waiting for the hourly rotation to reach it;
- **Next up** — the next ten pending URLs in the exact `select_due`
  order, so the otherwise implicit queue (never-attempted first, then
  least recently attempted, ties by URL) is inspectable.

The backfill deliberately does not open issues for the URLs it finds dead.
The job runs under `permissions: contents: read` only; issue escalation with
strike thresholds is the role of the hourly round
(`escalate_tidal_failures.py`), which is rate-limited by design. Adding
`issues: write` to a twice-per-hour backfill job would bypass that bound —
if backfill-driven escalation is wanted later, it is an explicit curator
decision, not a default.

The backfill is operational only: it reads canonical data and never writes
it, never selects or creates a recommendation, and never promotes a
replacement URL. Behaviour is covered in
`tests/test_fingerprint_backfill.py`.
