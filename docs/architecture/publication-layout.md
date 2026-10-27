# Publication layout

Composer overviews follow the editorial style of the legacy `docs/vivaldi.md`:
compact paragraphs, bold Work titles, readable catalogue numbers and dates,
italic performer names linked directly to Tidal, and a diamond for a Gem.
Recommended Work titles link to detail pages containing roles, reviews and other
recommendation metadata. Profiles and excerpt coverage are also visible inline.
Works without a recommendation remain visible as plain bold text without a link
or workflow/status label, including within editorial collections. The landing
page contains collection counts and composer navigation; it does not list Works
without recommendations.

Categories form sections. Work Group headings appear only when a section has
multiple Works in the same artistic family; singleton titles are not repeated.

Composers are ordered by family name: the last token of the canonical Person
name, with the full name as tiebreaker — the same family-name convention the
attribution pipeline uses for its page pool. The composers index is the single
navigation for composers (issue #404): composer pages are excluded from the
theme's sidebar navigation (`nav_exclude: true`), and the Collection and
Composers pages disable the theme's automatic child "Table of Contents"
(`has_toc: false`), so a composer appears exactly once per page. The theme's
search keeps indexing every page.

## Editorial collections

Optional `data/publication/<composer-id>.yaml` files preserve curated collection
names and member order. They are presentation metadata, not Work Groups or new
canonical musical entities. Each file contains its `composer_id` and an ordered
`collections` list. Each entry has a `title`, ordered `work_ids`, and optional
`opus` and `date_text` display text. A Work may appear in at most one collection
and must belong to that composer. Invalid membership blocks generation.
Unlisted Works are always rendered in the remaining category sections.

Vivaldi's initial file promotes the twelve opus descriptions, dates and order
from the trusted legacy page. Alternative catalogue entries remain separate
Works, with their own recommendations. Generation reads only `data/`; it does
not parse legacy Markdown or copy its recommendations. Collection headings
never imply a recommendation for every member.

## Deployment layout

The public site is exactly the generated collection (issue #358). The site
generator writes the complete Jekyll source to `publication/` (not committed):
the collection landing page, `composers/` and `works/` pages with root-level
permalinks (`/`, `/composers/`, `/works/`), plus the repository's theme
overrides (`_includes/head_custom.html` and `assets/`) copied along so the
collection keeps its styling.

Jekyll builds with `--source publication`, never from the repository root.
The build output therefore contains only the collection, and the site root
(`https://luhoo.github.io/classical_music/`) is the collection landing page.
Internal repository material — candidate review queues, curator comparison and
migration reports, prompts, fixtures, canonical data files — is never part of
the build and cannot deploy. A fail-closed guard in `pages.yml` fails the build
if any internal directory (`docs`, `report`, `reports`, `data`, `sources`,
`tests`, `scripts`, `src`) appears in the output. The legacy docs-based landing
page is not part of the build source and is therefore no longer published.

Pull-request runs upload the built site as a `site-preview` artifact for
review before merging; deployment to `gh-pages` only runs after a push to
`main`. Composer URLs follow Person ids; human-friendly slugs instead of
hash ids remain a separate design decision outside this issue.
