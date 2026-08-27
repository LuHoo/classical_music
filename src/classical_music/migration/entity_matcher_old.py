"""
Entity matcher: Find existing canonical entities matching migration candidates.

This module loads existing canonical entities from data/ and provides matching
logic to preserve curator intent when migrating source records.

Principle 3: Existing legacy data is trusted input. Migration must preserve
curator intent and avoid recreating entities that already exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

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
        """
        return self._composer_slug_to_id.get(doc_slug)

    def find_work(self, composer_id: str, work_title: str) -> ExistingEntity | None:
        """
        Find an existing work matching composer and title.

        Tries three strategies in order:
        1. Exact normalized title match (fast path)
        2. Catalogue number match (WAB, Op, etc.)
        3. Base title match (if title contains version/revision text)

        Returns the existing entity if found, None otherwise.
        """
        normalized_query = normalize_title(work_title)
        
        # Strategy 1: Exact normalized title match
        for work in self.works.values():
            if (
                work.composer_id == composer_id
                and work.normalized_title == normalized_query
            ):
                return work
        
        # Strategy 2: Try catalogue number matching
        query_catalogue = extract_catalogue_number(work_title)
        if query_catalogue:
            for work in self.works.values():
                if work.composer_id != composer_id:
                    continue
                
                # Check catalogue field in canonical work data
                canonical_catalogue = work.data.get("catalogue")
                if canonical_catalogue == query_catalogue:
                    return work
        
        # Strategy 3: Try base title matching (for version variations)
        # E.g., "Symphony No. 1 in C minor" (from various versions)
        base_title = re.sub(
            r'\(.*?\)', '', work_title
        ).strip()  # Remove parentheses and contents
        if base_title != work_title:
            normalized_base = normalize_title(base_title)
            for work in self.works.values():
                if (
                    work.composer_id == composer_id
                    and work.normalized_title == normalized_base
                ):
                    return work
        
        return None

    def find_work_group(self, composer_id: str, work_group_name: str) -> ExistingEntity | None:
        """
        Find an existing work group matching composer and name.

        Returns the existing entity if found, None otherwise.
        """
        normalized_query = normalize_title(work_group_name)
        for wg in self.work_groups.values():
            if (
                wg.composer_id == composer_id
                and wg.normalized_title == normalized_query
            ):
                return wg
        return None

    def find_performance(self, work_id: str, performer_text: str) -> ExistingEntity | None:
        """
        Find an existing performance matching work and performer.

        Returns the existing entity if found, None otherwise.
        """
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
