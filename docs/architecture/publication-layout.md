# Publication layout

Composer overviews follow the editorial style of the legacy `docs/vivaldi.md`:
compact paragraphs, bold Work titles, readable catalogue numbers and dates,
italic performer names linked directly to Tidal, and a diamond for a Gem.
Work titles still link to detail pages containing roles, reviews and other
recommendation metadata. Profiles and excerpt coverage are also visible inline.
Works without a recommendation remain visible without a workflow/status label.

Categories form sections. Work Group headings appear only when a section has
multiple Works in the same artistic family; singleton titles are not repeated.

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
