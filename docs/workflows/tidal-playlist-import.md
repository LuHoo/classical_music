# Import a curator's Tidal playlist in Work batches

The curator may explicitly designate a playlist as already accepted curation.
That instruction supplies musical acceptance for its selections. Playlist
membership by itself does not supply acceptance for an arbitrary public list.
Identity, coverage and an existing recommendation must still be checked.

Canonical boundaries and recommendation policy remain those in
`../architecture/repository-architecture.md`, `../architecture/work.md`,
`../architecture/performance.md` and `../architecture/recommendation-policy.md`.

## Retrieve the source

The **Tidal playlist source snapshot** GitHub Actions workflow reads a public
playlist with the repository's `TIDAL_CLIENT_ID` and `TIDAL_CLIENT_SECRET` secrets.
It obtains a masked, ephemeral catalogue token and writes only a source artifact.
It has no canonical write or deployment step. Dispatch becomes available after
the workflow exists on the default branch; the draft's narrow push trigger
allows its read-only live pilot before merge.

For a local catalogue token or app credentials already provided in the
environment:

```bash
python scripts/fetch_tidal_playlist.py \
  https://tidal.com/playlist/c11f614b-c011-43b2-be10-639f5cf7e5e3 \
  --limit 100 --country NL
```

The default limit is 100 source items; the allowed range is 1–200. This is a
metadata fetch budget, not the canonical batch size. The reader preserves item
order and duplicate occurrences, follows Tidal's cursor pagination, delays
requests, and bounds retries after HTTP 429. It refuses external-host redirects,
cross-resource pagination and repeated cursors. It checks the playlist's
modification marker before and after reading.

The ignored JSON source includes track, album, artist and usage-rule resources.
Missing metadata, inaccessible items, or empty credits must remain explicit
evidence gaps rather than guessed identities. A 401/403/404 response does not
prove that a playlist does not exist. Private-list access needs a suitably
authorized user token; this app-credentials workflow does not establish it.

`source_complete: false` means the snapshot is only a prefix. When the limit cuts
through a page, its next cursor would skip unread entries; the reader does not
offer that cursor as a resume point. Subsequent imports use verified positions
and track identities, not a guessed offset into a changed playlist.

## Prepare one bounded import

1. Start from current `main` on a dedicated branch. Use approximately ten musical
   Works as the default batch. Include the complete movement group of the final
   Work, and record the first entry of the next batch.
2. Establish composer and Work/catalogue identity from repository evidence and
   demand-driven authority evidence. Group movements by Work and underlying
   interpretation, not merely by album, punctuation or an adjacent artist name.
   One album can contribute more than one canonical Performance.
3. Verify coverage. A single movement or aria normally belongs to its parent
   Work, with a public `excerpt` description when the selection is incomplete.
   Do not infer acceptance of unselected album tracks to turn an excerpt into a
   complete recommendation.
4. Match the existing interpretation before proposing a new Performance. An
   exact trusted canonical Tidal track plus compatible Work/catalogue evidence
   can resolve a duplicate. For a different release, exact recording evidence
   such as ISRCs supports matching; shared titles or performers alone do not
   establish recording identity. Check global Person and performer authority
   before adding identities. Existing Persons must use their actual `id`, which
   may differ from the YAML filename. Named performers without a canonical
   Person are permitted by the minimal schema.
5. Reuse a matching Performance. Add a verified, accepted interpretation when
   the comparison category is vacant. A different recommendation for the same
   Work/profile remains outside canonical data until the curator explicitly
   chooses. Report those choices together in the batch; do not create an issue
   for every source track.
6. A known completion or independent arrangement needs its specific Work. A
   general composition with an unidentified original/revised version may use the
   documented general-Work fallback and `version_assignment: unspecified` on
   its Performance. Do not use this fallback to hide ambiguity between a
   fragment, completion or another artistic object.
7. Check `usageRules.attributes.countryCode`, `subscription` and `validFrom`
   for the requested country. API subscription streaming rights are catalogue
   evidence, not a successful playback test. Missing or unavailable links do
   not invalidate the curator's musical acceptance. Keep operational checks
   outside canonical YAML.
8. Retain a small batch manifest with Work/Performance decisions, source
   track IDs/ISRCs, independent evidence and the next boundary. Raw responses
   stay ignored or in the workflow artifact. Validate canonical data and public
   rendering, perform adversarial identity review, and end with a draft PR.

The first concrete batch is documented in
`../../reports/playlist-import/best-classical/batch-001.md` and its companion
JSON manifest. It imports three missing recommendations and reuses seven
existing interpretations. This pilot does not implement automatic musicological
matching or the separate Excel-column intake contract in issue #186.
