## Migration Dry-Run Output Schema

The `scripts/migrate.py --dry-run` command generates a `migration-summary.json` file documenting the migration analysis. This document describes the output structure.

### Summary Location

```
generated/migration/migration-summary.json
```

### Top-Level Fields

```json
{
  "dry_run": boolean,
  "works": WorkCandidate[],
  "performances": PerformanceCandidate[],
  "matched_entities": { source_id: canonical_entity_id },
  "review_summary": ReviewSummary,
  "written_files": string[]
}
```

### WorkCandidate Structure

Each work extracted from legacy Markdown:

```json
{
  "id": "composer-slug-work-title-work",
  "work_group_id": "composer-slug-work-base-title-group",
  "composer_id": "canonical-composer-id",
  "title": "Full work title with versions",
  "gem": boolean,
  "source_file": "docs/composer.md",
  "source_line": 42
}
```

**Fields**:
- `id`: Stable ID generated from composer, title (or reused if matched to existing)
- `work_group_id`: Groups versions of same work (e.g., all Symphony No. 1 variants)
- `composer_id`: Canonical composer identifier (e.g., "anton-bruckner")
- `title`: Raw title from legacy Markdown (includes version/revision notes)
- `gem`: Marked with 💎 in source (indicates curator-curated recording)
- `source_file`: Markdown file containing this entry
- `source_line`: Line number in Markdown

### PerformanceCandidate Structure

Each performance with Tidal link:

```json
{
  "id": "composer-work-performer-perf",
  "work_id": "composer-work-work",
  "performer_text": "Orchestra, Conductor",
  "tidal_url": "https://tidal.com/browse/track/...",
  "gramophone_issue": "issue text or null",
  "source_file": "docs/composer.md",
  "source_line": 42
}
```

**Fields**:
- `id`: Stable ID combining work and performer names
- `work_id`: Reference to parent work candidate
- `performer_text`: "Orchestra Name, Conductor Name" format from legacy
- `tidal_url`: First Tidal link from legacy Markdown
- `gramophone_issue`: Optional Gramophone reference from inline `[issue]`
- `source_file`, `source_line`: Location in Markdown

### Matched Entities Map

```json
{
  "matched_entities": {
    "composer:line-number": "canonical-work-id-from-data"
  }
}
```

Maps source record IDs to existing canonical entity IDs. If present, the work is `UNCHANGED` (no action needed).

### Review Summary

```json
{
  "review_summary": {
    "total_items": 42,
    "by_category": {
      "safe": 10,
      "unchanged": 30,
      "background": 2,
      "consequential": 0
    },
    "consequential_count": 0,
    "action_required_count": 0,
    "consequential_items": [
      {
        "source_id": "composer:123",
        "source_file": "docs/composer.md",
        "source_line": 123,
        "work_text": "Work with identity ambiguity",
        "rationale": "Identity gate(s) found: version_revision..."
      }
    ]
  }
}
```

**Categories**:
- `safe`: No issues; can migrate confidently
- `unchanged`: Matched to existing canonical entity (no action)
- `background`: Non-actionable metadata (authority lookup demand-driven)
- `consequential`: Identity gate requiring curator review

Identity-result statuses may also include `authority_evidence_required`. This
means repository evidence did not establish an existing Work and the next step
is demand-driven authority evidence. It is not a curator-required decision
unless authority evidence is insufficient or genuinely ambiguous.

**ClassificationReasons** (from real classifier):
- `version_revision`: "rev.", "revised" text (identity gate)
- `arrangement_orchestration`: "arr.", "arrangement" text (identity gate)
- `completion_reconstruction`: "completed by" text (identity gate)
- `suite_excerpt_derived`: "excerpt from", "suite" text (identity gate)
- `multiple_tidal_links`: Multiple Tidal URLs (non-actionable - pick first)
- `uncertain_match`: Low confidence match (non-actionable)

### Written Files

```json
{
  "written_files": [
    "generated/migration/canonical-preview/works/composer/work-id.yaml",
    "generated/migration/canonical-preview/performances/composer/perf-id.yaml"
  ]
}
```

Paths to canonical YAML files created by dry-run (if not actually dry-run mode).

## Example: Bruckner Migration

```json
{
  "dry_run": true,
  "works": [
    {
      "id": "anton-bruckner-symphony-no-1-in-c-minor-das-kecke-beserl-3-work",
      "work_group_id": "anton-bruckner-symphony-no-1-in-c-minor-group",
      "composer_id": "anton-bruckner",
      "title": "Symphony No. 1 in C minor \"Das kecke Beserl\" (1865, first concept)",
      "gem": false,
      "source_file": "docs/bruckner.md",
      "source_line": 18
    }
  ],
  "performances": [
    {
      "id": "anton-bruckner-symphony-no-1-in-c-minor-das-kecke-beserl-3-work-bruckner-orchester-linz-markus-poschner-perf",
      "work_id": "anton-bruckner-symphony-no-1-in-c-minor-das-kecke-beserl-3-work",
      "performer_text": "Bruckner Orchester Linz, Markus Poschner",
      "tidal_url": "https://tidal.com/browse/track/384348598?u",
      "gramophone_issue": null,
      "source_file": "docs/bruckner.md",
      "source_line": 18
    }
  ],
  "matched_entities": {
    "bruckner:18": "anton-bruckner-symphony-no-1-in-c-minor-das-kecke-beserl-3-work"
  },
  "review_summary": {
    "total_items": 42,
    "by_category": {
      "safe": 0,
      "unchanged": 42,
      "background": 0,
      "consequential": 0
    },
    "consequential_count": 0,
    "action_required_count": 0,
    "consequential_items": []
  },
  "written_files": []
}
```

## Understanding the Output

### For Curator Review

1. **Check `consequential_items`**: These need curator decision
2. **Check `by_category` counts**: Understand distribution of work
   - High `unchanged`: Good entity matching
   - High `background`: Non-actionable metadata gaps
   - High `consequential`: Identity questions need curator attention

### For Validation

1. **Idempotence**: Run twice with `--dry-run`, expect identical `review_summary`
2. **Coverage**: Total work candidates should roughly match composer's work count
3. **Matching**: Higher `unchanged` count means better entity matching quality

### For Migration

1. **Remove `--dry-run` flag** when ready to write canonical YAML files
2. **Follow `consequential_items` decisions** before final migration
3. **Verify `written_files`** were created correctly
