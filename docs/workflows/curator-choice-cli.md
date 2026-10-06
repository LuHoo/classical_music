# Curator choices from the command line

`./curator <issue-number> <choice>` previews a single recommendation decision.
It uses the existing reviewed Chamber snapshot, canonical YAML and
`reports/curator-decisions/`; it does not maintain a second catalogue.
Python 3.13+ and the project dependencies are required:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
./curator 246 C093                       # preview, no repository writes
./curator 246 C093 --dry-run             # same explicit preview
./curator 246 C093 --apply --curator Lucas
```

Run from a working branch. Review the resulting diff and commit/open a PR as
usual. The CLI neither commits nor pushes, posts comments, closes issues, nor
changes TIDAL. Publication pages are generated and checked; live deployment
still happens through the normal merged PR workflow.

## Choices and evidence

The issue must occur exactly once in the manifest's pending/resolved choices.
C-unit codes are accepted directly. A/B aliases are explicit `choice_aliases`
on that same choice object, never inferred from array order. This first version
registers the labels already published in #240 (A=C003, B=C287) and #241
(A=C210, B=C298). Other current issues use their published C-codes, including
three-candidate #247. A future issue can add its reviewed labels to its choice
object. Unknown labels fail with the available choices.

`--apply` records the explicit local command as the curator decision, with the
local username (or `--curator`), UTC timestamp and selected/not-selected units.
An optional `--decision-url <issue-comment-url>` links an existing comment on
that issue; the CLI does not fetch or authenticate the comment. Otherwise the
manifest and Performance cite the local decision record. A reviewer can add
the resulting PR URL to `implementation_pr` in that record. Post the decision
and PR link to the issue through the usual curator workflow; the CLI does not
claim that an issue comment has been posted.

All movements and source occurrences remain in the historical snapshot.
Selected new recordings become canonical Performances; rejected units become
`not_selected`. Manifest counts, the import README and resolved choices are
updated together. Existing recommendations can be selected with their C-code
or `existing` when exactly one existing recommendation is registered:

```bash
./curator 242 C400                     # keep the existing recommendation
./curator 242 C035 --replace-existing  # preview replacing it with C035
./curator 242 C035 --replace-existing --apply
```

Replacement requires that extra flag, preserves the old canonical record in
the decision's `replaced_performances`, and refuses records used by another
import unit. Existing links are unchanged when retaining a recommendation.
Excerpts and reviewed profiles are copied, never inferred.

## Manual playlist actions

A recommendation choice alone does not request playlist removal. To explicitly
plan removal of the unselected source recordings, use:

```bash
./curator 246 C093 --playlist-remove-unselected
./curator 246 C093 --playlist-remove-unselected --apply
```

The output gives the playlist name/URL, work, performers, **each exact track
ID**, and selected IDs to keep. The decision record stores a pending manual
action. Check current membership and IDs in TIDAL; snapshot positions are
historical and must not be used as current positions. Shared IDs with other
source occurrences block automatic planning and need manual review.

After doing the action yourself, preview and record the confirmation:

```bash
./curator 246 playlist-done --note "Removed the three listed IDs; selected recording retained"
./curator 246 playlist-done --apply --curator Lucas \
  --note "Removed the three listed IDs; selected recording retained"
```

This records **curator-reported** completion, not an API/live verification.
It preserves the original action and decision. Confirmation without a pending
action or a verification note fails. Retrying the same decision or completion
is a no-op; a conflicting decision fails. A retry cannot silently add a playlist
action to a decision made without one.

## Validation and limits

Preview and apply build a scratch copy and reuse the Chamber inventory audit,
canonical publication validator and publication generator. The affected Work's
selected link is checked as well. No broad identity/duplicate scan or network
link check is needed for this path. Apply installs changes only after validation,
checks for intervening input changes, serializes CLI writes with `.curator.lock`,
and rolls back ordinary write failures. Playlist confirmation validates only
the decision records because it does not change canonical or publication data. Multi-file installation is not a
crash-proof database transaction: use Git to review/recover after a machine
crash; remove a stale lock only after verifying no CLI process is running.

V1 supports the current **Chamber single-recommendation** issues. It deliberately
rejects `geen`, `unresolved`, multi-profile decisions and changes to an already
resolved choice, whose semantics require further review. Other playlist
manifest schemas are not implicitly imported. No existing curator issue is
resolved merely by installing this CLI.

#240 / PR #300 is the regression reference. On today's repository
`./curator 240 A` reports the existing decision without rewriting it or asking
for the completed removal again. The integration test reconstructs the pending
case, verifies the same canonical Wigmore Soloists Performance, and checks
that C287's manual action contains 12423579, 12423580, 12423581 and 12423582.

```bash
.venv/bin/python -m pytest tests/test_curator.py tests/test_chamber_import.py \
  tests/test_original_arrangement_decisions.py --no-cov
.venv/bin/python scripts/check_chamber_import.py
```
