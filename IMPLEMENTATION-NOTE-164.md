# Implementation Note: Issue #164 — Reproducible Migration Pipeline

**Status**: Starting Phase 1 — Implementation planning  
**Date**: 2026-08-27  
**Branch**: `feature/164-reproducible-migration`

## Pre-flight Checklist Answers

### 1. Which existing migration/parser/writer scripts are being reused?

**Existing infrastructure (already in repository):**

- **`scripts/migrate.py`** (main orchestrator)
  - Parses selected composer markdown files
  - Creates WorkCandidate and PerformanceCandidate objects
  - Classifies items for review
  - Supports `--dry-run` mode
  - Generates `migration-summary.json` with review items
  - Writes preview canonical YAML files to `generated/migration/canonical-preview/`

- **`src/classical_music/migration/parser.py`**
  - Extracts work titles, gems, dates, performers, Tidal links, Gramophone issues
  - Parses heading context (categories)
  - Returns `SourceRecord` objects with structured metadata

- **`src/classical_music/migration/writer.py`**
  - Generates stable IDs for works and performances
  - Writes canonical YAML preview files
  - Supports idempotent output (same input → same files)

- **`src/classical_music/migration/classifier.py`**
  - Classifies records for review reasons
  - Identifies: incompleteness, ambiguity, data quality issues

- **`scripts/validate_data.py`**
  - Validates canonical data structure and constraints
  - Can validate migration output

### 2. Which gaps remain for source reading, matching, writing and summaries?

**Gaps to close:**

1. **Entity Matching** (critical)
   - Parser extracts source records
   - Writer generates candidates
   - **Missing**: Matching against existing canonical entities (Person → Work Group → Work → Performance)
   - Need to check: Does a candidate already exist in data/?
   - Decision logic: When to preserve existing ID vs. create new

2. **Identity Gate Workflow** (critical)
   - Parser extracts source records
   - Classifier identifies review items
   - **Missing**: Curator review interface for consequential identity questions
   - Current state: review_items list in JSON
   - Need: Structured escalation to curator with actionable identity questions only

3. **Batch Orchestration** (important)
   - Can migrate one composer at a time
   - **Missing**: Ability to orchestrate batches, track state, resume incomplete batches
   - Need: Run stats, batch markers

4. **Better Review Summaries** (important)
   - Current: Raw review_items with classifications
   - **Missing**: Categorized summaries (safe canonical / unchanged / background / consequential)
   - Need: Clearer escalation path

5. **Dry-run Validation** (supporting)
   - Dry-run mode exists
   - **Missing**: Comparison tool to validate idempotence (run twice, compare previews)
   - Need: Diff report showing expected idempotence

### 3. Which composer or small batch for the first vertical slice?

**First vertical slice: Composers already partially migrated**

Candidates (from data/works/):
- Bruckner (already has version/concept handling via identity gates)
- Prokofiev (recent curator-on-demand work)
- Hindemith (documented authority gaps, known pattern)

**Why these:**
- Already in canonical form (can test matching against existing)
- Exercises version/revision patterns (Work Group + multiple Works)
- Known authority resolution patterns (MusicBrainz IDs, catalogues)
- Demonstrate identity gates and background suspicions correctly

**Slice scope:**
- Parse existing markdown section
- Match against canonical entities
- Classify review items
- Prove dry-run idempotence
- Document how to expand to remaining collection

### 4. How the run will prove idempotence and safe writes?

**Idempotence validation:**

1. **Run 1**: `python3 scripts/migrate.py --composer bruckner --dry-run`
   - Generates `generated/migration/migration-summary-bruckner-1.json`
   - Previews canonical YAML files

2. **Run 2**: Same command
   - Generates `generated/migration/migration-summary-bruckner-2.json`
   - Previews canonical YAML files

3. **Comparison**:
   - Hash/diff migration-summary files (should be identical)
   - Hash/diff preview files (should be identical)
   - Report: "✓ Idempotent" or show diffs if not

**Safe writes proof:**

1. **Dry-run comparison** shows expected output without touching canonical data
2. **Schema validation** ensures output passes `validate_data.py`
3. **Identity checks** confirm no duplicate Work IDs, broken references
4. **No canonical write** until curator explicitly approves (separate workflow)

### 5. Which outcomes are canonical writes and which remain reports/background suspicions?

**Canonical writes (only when explicitly approved):**
- Works with clear identity (matched to existing or strong source evidence)
- Performances with clear Work mapping
- Gems, Tidal links, Gramophone references

**Reports (non-actionable background):**
- Authority gaps (missing MusicBrainz IDs) — no action needed
- Source format improvements — documented for future
- Metadata completeness observations

**Escalation (consequential identity questions):**
- Ambiguous Person assignments
- Revision vs. separate work decisions
- Arrangement classification (when not clear from source)
- These → GitHub Issues for curator review, one issue per decision, not one per gap

---

## First Vertical Slice Plan

**Phase 1** (this branch): Implementation planning and first command  
**Phase 2** (next phase): End-to-end pipeline for Bruckner  
**Phase 3** (future): Batch orchestration and remaining composers  

### Phase 1 Deliverables (this PR)

1. ✓ This implementation note
2. Enhanced `scripts/migrate.py`:
   - Add entity matching logic (check for existing canonical entities)
   - Add better review summaries (categorize by safe/unchanged/background/consequential)
   - Add idempotence comparison tool
3. Test: Run on Bruckner source data, validate idempotence
4. Draft PR against main

### Expected Outcomes

- `migrate.py --composer bruckner --dry-run` produces reviewable, idempotent migration-summary.json
- Bruckner works match against existing canonical entities
- Review items only include consequential identity decisions (small list, not large)
- No canonical files written (dry-run only at this phase)

---

## Architecture Alignment

**Principles involved:**
- Principle 1: Curated collection (preserve curator intent in migration)
- Principle 2: Repository is canonical (existing data is trusted input)
- Principle 3: Legacy data is trusted (migration preserves it unless proven wrong)
- Principle 4: Person/Work identity must be correct (automation determines, curator reviews consequential only)
- Principle 15: Automation reduces curator workload
- Principle 16: Distinguish errors/gates/background suspicions (escalate only consequential)
- Principle 18: Git workflow (feature branch, tests, draft PR)

**Related to issues:**
- #131: Source-reading quality → parser enhanced by this work
- #132: Safe write mode → dry-run proof by this work
- #133: Better review summaries → migration reporting enhanced by this work
- Recommendation: Close #131, #132, #133 as subsumed by #164 after this phase completes

---

## Success Criterion

The migration pipeline can:
- Run on one composer with a one-line command
- Produce idempotent, reviewable migration summaries
- Match source records to existing canonical entities (preserving their IDs)
- Escalate only consequential identity questions (small, grouped, actionable)
- Prove dry-run safety with reproducible previews
- Be expanded to remaining collection in manageable batches without architectural changes

After Phase 1, the next curator can confidently run Phase 2 without re-understanding the pilot internals.
