# Tidal link maintenance — issue #64, local implementation

This workflow maintains locators on accepted canonical Performances. It never
creates a Performance, promotes a candidate, modifies `keep_looking`, creates
GitHub issues, or deploys the website.

## Architecture pre-flight

1. Governing documents read: `architecture-principles.md`,
   `repository-architecture.md`, `performance.md`, `recommendation-policy.md`,
   `minimal-yaml-schemas.md`, and `workflow-design-notes.md` under
   `docs/architecture/`. ADR 0004 is superseded and is not normative.
2. Purpose: keep listening links useful without changing musical recommendations.
3. Smallest scope: a local command, one JSON/Markdown report, optional verified
   URL updates, plus a bounded authenticated GitHub Actions pilot. No monthly
   scheduler or new canonical entity.
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

No monthly schedule is activated. A later periodic rollout must persist the
previous JSON report/fingerprints between runs; these disposable pilot runners
do not automatically restore historical fingerprints. The downloadable JSON
can be reused locally with `--previous`. Any future URL repairs should be
prepared in a maintenance PR using `--apply`, never published automatically.

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
read-only permissions and bounded branch triggers. Tests contain only
synthetic credentials.
