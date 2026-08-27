"""
Entity matcher: Find existing canonical entities matching migration candidates.

This module implements two-stage matching:
1. Candidate discovery: Find plausible existing entities (fuzzy, catalogue, aliases)
2. Identity resolution: Determine if specific canonical entity represents same
   artistic identity

Principle 3: Existing legacy data is trusted input. Migration must preserve
curator intent and avoid recreating entities that already exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from classical_music.migration.models import (
    WorkIdentityResolution,
    WorkIdentityResult,
)

yaml = YAML(typ="safe")


@dataclass(frozen=True)
class ExistingEntity:
    """Existing canonical entity from data/."""

    entity_type: str  # "work" | "work_group" | "performance" | "person"
    entity_id: str
    file_path: Path
    data: dict[str, Any]
    normalized_title: str | None = None
    composer_id: str | None = None

    @classmethod
    def from_file(cls, entity_type: str, file_path: Path) -> ExistingEntity | None:
        """Load a canonical entity from YAML file."""
        try:
            data = yaml.load(file_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return None

            entity_id = data.get("id")
            if not entity_id:
                return None

            title = data.get("title", "")
            normalized_title = normalize_title(title) if title else None
            composer_id = data.get("composer_id")

            return cls(
                entity_type=entity_type,
                entity_id=entity_id,
                file_path=file_path,
                data=data,
                normalized_title=normalized_title,
                composer_id=composer_id,
            )
        except Exception:
            return None


def normalize_title(title: str) -> str:
    """Normalize title for matching (lowercase, minimal punctuation)."""
    if not title:
        return ""
    normalized = re.sub(r"\s+", " ", title.casefold().strip())
    # Normalize various quote styles to double quote
    normalized = re.sub(r'[""\']', '"', normalized)
    return normalized


def extract_version_info(text: str) -> dict[str, str] | None:
    """
    Extract version/revision information from title.
    
    Returns dict with keys:
    - year: extracted year (e.g., "1865")
    - type: "version", "revision", etc. or "year" if just year
    - full_text: original extracted text
    
    Or None if no version info found.
    
    Handles patterns:
    - "(1865 version)" or "(1865 revision)" or "(1863 version, ...)"
    - "(1865, first concept...)" (comma-separated)
    - "(1866 "Linz version"...)" (quoted)
    - "(1865)" (just year)
    """
    # Match patterns like "(1865 version...)" "(1865 revision...)" etc.
    # Allow text after the keyword up to closing paren
    match = re.search(
        r'\((\d{4})\s+(version|revision|edition|variant)[^)]*\)',
        text,
        re.IGNORECASE
    )
    if match:
        return {
            "year": match.group(1),
            "type": match.group(2).lower(),
            "full_text": match.group(0),
        }
    
    # Match year followed by quote (e.g., "(1866 "Linz version")")
    match = re.search(r'\((\d{4})\s*"', text)
    if match:
        return {
            "year": match.group(1),
            "type": "version",
            "full_text": match.group(0),
        }
    
    # Match year followed by comma (e.g., "(1865, first concept)")
    # This is common in Bruckner symphonies
    match = re.search(r'\((\d{4}),', text)
    if match:
        return {
            "year": match.group(1),
            "type": "year_descriptive",
            "full_text": match.group(0),
        }
    
    # Match just year in parentheses like "(1865)"
    match = re.search(r'\((\d{4})\)$', text)
    if match:
        return {
            "year": match.group(1),
            "type": "year",
            "full_text": match.group(0),
        }
    
    return None


def extract_catalogue_number(text: str) -> str | None:
    """
    Extract catalogue number from text.
    
    Looks for patterns like:
    - WAB. 101 (Bruckner)
    - Op. 23 (opus)
    - K. 545 (Köchel, Mozart)
    - BWV 846 (Bach)
    """
    # Match WAB. DIGITS
    match = re.search(r'WAB\.?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return f"WAB.{match.group(1)}"
    
    # Match Op. or Opus DIGITS
    match = re.search(r'Op\.?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return f"Op.{match.group(1)}"
    
    # Match K. DIGITS (Köchel)
    match = re.search(r'K\.?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return f"K.{match.group(1)}"
    
    # Match BWV DIGITS
    match = re.search(r'BWV\.?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return f"BWV.{match.group(1)}"
    
    return None


class EntityMatcher:
    """Match migration candidates against existing canonical entities."""

    def __init__(self, data_root: Path):
        """Load existing entities from data/."""
        self.data_root = data_root
        self.works: dict[str, ExistingEntity] = {}
        self.work_groups: dict[str, ExistingEntity] = {}
        self.performances: dict[str, ExistingEntity] = {}
        self.persons: dict[str, ExistingEntity] = {}
        self._composer_slug_to_id: dict[str, str] = {}  # "bruckner" → "anton-bruckner"

        self._load_works()
        self._load_work_groups()
        self._load_performances()
        self._load_persons()
        self._build_composer_mapping()

    def _load_works(self) -> None:
        """Load existing works from data/works/."""
        works_dir = self.data_root / "works"
        if not works_dir.exists():
            return

        for file_path in works_dir.rglob("*.yaml"):
            entity = ExistingEntity.from_file("work", file_path)
            if entity and entity.entity_id:
                self.works[entity.entity_id] = entity

    def _load_work_groups(self) -> None:
        """Load existing work groups from data/work-groups/."""
        groups_dir = self.data_root / "work-groups"
        if not groups_dir.exists():
            return

        for file_path in groups_dir.glob("*.yaml"):
            entity = ExistingEntity.from_file("work_group", file_path)
            if entity and entity.entity_id:
                self.work_groups[entity.entity_id] = entity

    def _load_performances(self) -> None:
        """Load existing performances from data/performances/."""
        perfs_dir = self.data_root / "performances"
        if not perfs_dir.exists():
            return

        for file_path in perfs_dir.glob("*.yaml"):
            entity = ExistingEntity.from_file("performance", file_path)
            if entity and entity.entity_id:
                self.performances[entity.entity_id] = entity

    def _load_persons(self) -> None:
        """Load existing persons from data/persons/."""
        persons_dir = self.data_root / "persons"
        if not persons_dir.exists():
            return

        for file_path in persons_dir.glob("*.yaml"):
            entity = ExistingEntity.from_file("person", file_path)
            if entity and entity.entity_id:
                self.persons[entity.entity_id] = entity

    def _build_composer_mapping(self) -> None:
        """
        Build mapping from doc slug to canonical composer_id.
        E.g., "bruckner" → "anton-bruckner"
        """
        slug_to_id = {}
        for work in self.works.values():
            if work.composer_id:
                # Extract last word as doc slug (e.g., "anton-bruckner" → "bruckner")
                parts = work.composer_id.split("-")
                slug = parts[-1]
                if slug and slug not in slug_to_id:
                    slug_to_id[slug] = work.composer_id
        self._composer_slug_to_id = slug_to_id

    def resolve_composer_id(self, doc_slug: str) -> str | None:
        """
        Resolve doc slug to canonical composer_id.
        Returns canonical composer_id or None if not found.
        
        FAIL CLOSED: No fallback to slug if not found.
        """
        return self._composer_slug_to_id.get(doc_slug)

    def find_work_candidates(
        self, composer_id: str, work_title: str
    ) -> list[ExistingEntity]:
        """
        Candidate discovery: Find plausible existing Works matching composer and title.

        Uses three strategies in order:
        1. Exact normalized title match (including version text in canonical)
        2. Catalogue number match (WAB, Op, etc.)
        3. Base title match (without version/revision text in source)

        Returns list of candidate Works (may be multiple, empty, or one).
        This is candidate discovery only - does NOT determine identity.
        """
        candidates: list[ExistingEntity] = []
        normalized_query = normalize_title(work_title)
        
        # Strategy 1: Exact normalized title match (fast path)
        for work in self.works.values():
            if (
                work.composer_id == composer_id
                and work.normalized_title == normalized_query
            ):
                candidates.append(work)
        
        if candidates:
            return candidates
        
        # Strategy 2: Try catalogue number matching
        query_catalogue = extract_catalogue_number(work_title)
        if query_catalogue:
            for work in self.works.values():
                if work.composer_id != composer_id:
                    continue
                
                # Check catalogue field in canonical work data
                canonical_catalogue = work.data.get("catalogue")
                if canonical_catalogue == query_catalogue:
                    candidates.append(work)
        
        if candidates:
            return candidates
        
        # Strategy 3: Try base title matching (for version variations)
        # E.g., "Symphony No. 1 in C minor (1865 version)" → "Symphony No. 1 in C minor"
        # This discovers the Work Group or base Work, but version must be checked
        # in identity resolution
        base_title = re.sub(r'\(.*?\)', '', work_title).strip()
        if base_title != work_title:
            normalized_base = normalize_title(base_title)
            for work in self.works.values():
                if (
                    work.composer_id == composer_id
                    and work.normalized_title == normalized_base
                ):
                    candidates.append(work)
        
        return candidates


    def _extract_year_from_date_text(self, date_text: str | None) -> str | None:
        """Extract first 4-digit year from date_text."""
        if not date_text:
            return None
        import re
        match = re.search(r'(\d{4})', date_text)
        return match.group(1) if match else None

    def resolve_work_identity(
        self,
        work_title: str,
        composer_id: str,
        candidates: list[ExistingEntity],
    ) -> WorkIdentityResult:
        """
        Identity resolution: Determine if and which canonical Work matches source.

        Takes source Work title and candidate Works, returns resolution result.
        
        Preserves version/revision text as identity evidence and applies it to
        distinguish between multiple candidates (e.g., different versions of
        same symphony).
        
        Returns WorkIdentityResult with:
        - status: MATCHED | NEW_IDENTITY | UNRESOLVED | BACKGROUND_ONLY
        - matched_work_id: if MATCHED
        - evidence_used: what evidence informed decision
        - requires_curator_action: whether human review needed
        """
        evidence_used: list[str] = []
        
        # Extract version information from source
        version_info = extract_version_info(work_title)
        if version_info:
            evidence_used.append(f"version: {version_info['full_text']}")
        
        catalogue = extract_catalogue_number(work_title)
        if catalogue:
            evidence_used.append(f"catalogue: {catalogue}")
        
        # Case 1: No candidates found
        if not candidates:
            return WorkIdentityResult(
                status=WorkIdentityResolution.UNRESOLVED,
                candidates_count=0,
                evidence_used=evidence_used,
                rationale="No candidate Works found; cannot resolve identity without positive evidence for new Work",
                requires_curator_action=True,
            )
        
        # Case 2: Exactly one candidate
        if len(candidates) == 1:
            candidate = candidates[0]
            
            # If source has version info, verify it doesn't contradict canonical
            # (Only conflict if canonical explicitly has different version_year)
            if version_info:
                canonical_version_year = candidate.data.get("version_year")
                # Only raise conflict if canonical has version info that differs
                if canonical_version_year and canonical_version_year != version_info["year"]:
                    # Version mismatch: this candidate is not the right version
                    return WorkIdentityResult(
                        status=WorkIdentityResolution.UNRESOLVED,
                        candidates_count=1,
                        evidence_used=evidence_used,
                        rationale=f"Found Work but version mismatch: source {version_info['year']} vs canonical {canonical_version_year}",
                        requires_curator_action=True,
                    )
                # If canonical has no version_year, source version info doesn't conflict
            
            # Single candidate matches
            evidence_used.append("exact_single_candidate")
            return WorkIdentityResult(
                status=WorkIdentityResolution.MATCHED,
                matched_work_id=candidate.entity_id,
                candidates_count=1,
                evidence_used=evidence_used,
                rationale=f"Single canonical Work matches: {candidate.entity_id}",
                requires_curator_action=False,
            )
        
        # Case 3: Multiple candidates (ambiguity)
        # Try to use version info to disambiguate
        if version_info:
            # Check both version_year field and date_text for year
            version_matches = [
                c for c in candidates
                if c.data.get("version_year") == version_info["year"]
                or self._extract_year_from_date_text(c.data.get("date_text")) == version_info["year"]
            ]
            
            if len(version_matches) == 1:
                # Version info resolved the ambiguity
                candidate = version_matches[0]
                evidence_used.append("version_disambiguation")
                return WorkIdentityResult(
                    status=WorkIdentityResolution.MATCHED,
                    matched_work_id=candidate.entity_id,
                    candidates_count=len(candidates),
                    evidence_used=evidence_used,
                    rationale=f"Used version evidence to select from {len(candidates)} candidates",
                    requires_curator_action=False,
                )
            elif len(version_matches) > 1:
                # Version info didn't uniquely resolve
                return WorkIdentityResult(
                    status=WorkIdentityResolution.UNRESOLVED,
                    candidates_count=len(candidates),
                    evidence_used=evidence_used,
                    rationale=f"Version {version_info['year']} matches multiple Works; cannot resolve identity",
                    requires_curator_action=True,
                )
            else:
                # Source has version that doesn't match any candidate
                return WorkIdentityResult(
                    status=WorkIdentityResolution.UNRESOLVED,
                    candidates_count=len(candidates),
                    evidence_used=evidence_used,
                    rationale=f"Source version {version_info['year']} doesn't match any of {len(candidates)} candidates",
                    requires_curator_action=True,
                )
        
        # Multiple candidates and no version info to disambiguate
        return WorkIdentityResult(
            status=WorkIdentityResolution.UNRESOLVED,
            candidates_count=len(candidates),
            evidence_used=evidence_used + ["multiple_candidates_no_version_evidence"],
            rationale=f"Found {len(candidates)} plausible Works but no version evidence to resolve",
            requires_curator_action=True,
        )

    def find_work_group(self, composer_id: str, work_group_name: str) -> ExistingEntity | None:
        """Find an existing work group matching composer and name."""
        normalized_query = normalize_title(work_group_name)
        for wg in self.work_groups.values():
            if (
                wg.composer_id == composer_id
                and wg.normalized_title == normalized_query
            ):
                return wg
        return None

    def find_performance(self, work_id: str, performer_text: str) -> ExistingEntity | None:
        """Find an existing performance matching work and performer."""
        performer_normalized = normalize_title(performer_text) if performer_text else ""
        for perf in self.performances.values():
            if perf.data.get("work_id") == work_id:
                # Match performer name
                existing_performers = perf.data.get("performers", "")
                if isinstance(existing_performers, str):
                    existing_normalized = normalize_title(existing_performers)
                    if existing_normalized == performer_normalized:
                        return perf
        return None

    def find_person(self, person_id: str) -> ExistingEntity | None:
        """Find an existing person by ID."""
        return self.persons.get(person_id)

    def matches_summary(self) -> dict[str, int]:
        """Return summary of loaded entities."""
        return {
            "persons": len(self.persons),
            "work_groups": len(self.work_groups),
            "works": len(self.works),
            "performances": len(self.performances),
        }


# Backward compatibility: keep old find_work() function that returns single entity or None
def find_work(
    matcher: EntityMatcher, composer_id: str, work_title: str
) -> ExistingEntity | None:
    """
    DEPRECATED: Use find_work_candidates() + resolve_work_identity() instead.
    
    This function is kept for backward compatibility but does NOT properly
    handle identity resolution. It only returns first exact match.
    """
    candidates = matcher.find_work_candidates(composer_id, work_title)
    return candidates[0] if candidates else None
