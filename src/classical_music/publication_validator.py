"""Publication validation for canonical data before site generation.

This module validates that all canonical data required for publication is
internally consistent and complete. It implements fail-closed validation:
broken references block publication, but non-blocking warnings remain non-blocking.

Validation follows architecture-principles.md and validation-rules.md:
- REF-001: WorkGroup.composer_id → existing Person
- REF-002: Work.composer_id → existing Person
- REF-003: Work.work_group_id → existing WorkGroup
- REF-004: Performance.work_id → existing Work
- REF-005: Performance MUST NOT reference WorkGroup directly

Background suspicions and duplicate warnings remain non-blocking (they do not
prevent publication).
"""

from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from classical_music.catalog_snapshot import CatalogSnapshot


@dataclass
class ValidationError:
    """A validation error blocking publication."""

    rule_id: str
    severity: str  # "error" (blocks) or "warning" (non-blocking)
    entity_type: str
    entity_id: str
    field: str
    message: str
    source_file: str


@dataclass
class ValidationResult:
    """Result of publication validation."""

    passed: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def exit_code(self) -> int:
        """Exit code for command-line use. 0 = success, 1 = publication errors."""
        return 0 if self.passed else 1

    def error_count(self) -> int:
        """Count of blocking errors."""
        return len(self.errors)

    def warning_count(self) -> int:
        """Count of non-blocking warnings."""
        return len(self.warnings)

    def summary(self) -> str:
        """Return human-readable summary."""
        if self.passed:
            msg = "✅ Publication validation passed"
            if self.warning_count() > 0:
                msg += f" ({self.warning_count()} non-blocking warnings)"
            return msg
        else:
            return f"❌ Publication validation failed: {self.error_count()} errors, {self.warning_count()} warnings"


class PublicationValidator:
    """Validate canonical data is ready for publication.

    This validator checks that:
    1. All Works reference existing WorkGroups
    2. All Works reference existing Persons (composers)
    3. All WorkGroups reference existing Persons (composers)
    4. All Performances reference existing Works
    5. No Performance directly references a WorkGroup
    6. Each Performance has performers (requirement for safe rendering)

    Reference checks read the raw catalog snapshot, not the adapter's
    publication model: the publication model drops records the source
    validation must still be able to see.
    """

    def __init__(self, repo_root: Path = None, snapshot: Optional[CatalogSnapshot] = None):
        """Initialize validator with optional custom repo root.

        Args:
            repo_root: Path to repository root. If None, inferred from file location.
            snapshot: Shared raw catalog snapshot to reuse. When omitted, every
                call to :meth:`validate` parses ``data/`` again, so consecutive
                invocations always observe the current files.
        """
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = repo_root
        self.snapshot = snapshot

        # Import here to allow testing without full project setup
        from classical_music.publication_adapter import PublicationDataAdapter

        self.adapter = PublicationDataAdapter(repo_root, snapshot=snapshot)
        self.result = ValidationResult(passed=True, errors=[], warnings=[])

    def validate(self) -> ValidationResult:
        """Run full publication validation.

        Returns:
            ValidationResult with passed status and detailed error list.
        """
        self.result = ValidationResult(passed=True, errors=[], warnings=[])

        # A snapshot that was not injected is scoped to this call only, so a
        # second validation never reuses stale catalog content.
        snapshot = (
            self.snapshot
            if self.snapshot is not None
            else CatalogSnapshot.load(self.repo_root)
        )
        self.adapter.snapshot = snapshot

        try:
            return self._validate_with_snapshot(snapshot)
        finally:
            # The snapshot's lifetime ends with this validation.
            self.adapter.snapshot = self.snapshot

    def _validate_with_snapshot(self, snapshot: CatalogSnapshot) -> ValidationResult:
        """Run the publication checks against one shared raw catalog snapshot."""
        # Load canonical data. Publication validation must fail closed when the
        # canonical publication model cannot be built.
        if not self.adapter.adapt():
            for error in self.adapter.errors:
                self._add_error(
                    "LOAD-001",
                    "repository",
                    str(self.repo_root),
                    "data",
                    f"Publication data adapter failed: {error}",
                    str(self.repo_root / "data"),
                )

            if not self.adapter.errors:
                self._add_error(
                    "LOAD-001",
                    "repository",
                    str(self.repo_root),
                    "data",
                    "Publication data adapter failed",
                    str(self.repo_root / "data"),
                )

            self.result.passed = False
            return self.result

        # Run validation checks
        self._validate_work_group_references(snapshot)  # REF-001
        self._validate_work_composer_references(snapshot)  # REF-002
        self._validate_work_work_group_references(snapshot)  # REF-003
        self._validate_performance_work_references(snapshot)  # REF-004
        self._validate_no_direct_wg_performance_references(snapshot)  # REF-005
        self._validate_performance_has_performers(snapshot)  # DOM-044

        # Determine if validation passed
        # Passed only if no blocking errors (warnings don't block)
        self.result.passed = len(self.result.errors) == 0

        return self.result

    def _add_error(
        self, rule_id: str, entity_type: str, entity_id: str, field: str, message: str, source_file: str = ""
    ):
        """Add a blocking error."""
        self.result.errors.append(
            ValidationError(
                rule_id=rule_id,
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field=field,
                message=message,
                source_file=source_file,
            )
        )

    def _add_warning(
        self, rule_id: str, entity_type: str, entity_id: str, field: str, message: str, source_file: str = ""
    ):
        """Add a non-blocking warning (background suspicion)."""
        self.result.warnings.append(
            ValidationError(
                rule_id=rule_id,
                severity="warning",
                entity_type=entity_type,
                entity_id=entity_id,
                field=field,
                message=message,
                source_file=source_file,
            )
        )

    def _validate_work_group_references(self, snapshot: CatalogSnapshot):
        """REF-001: WorkGroup.composer_id MUST reference existing Person.

        Verify each WorkGroup references a valid composer.
        """
        if not hasattr(self.adapter, "persons"):
            return

        person_ids = {p["id"] for p in self.adapter.persons.values()}

        if snapshot.missing_directory("WorkGroup") is not None:
            return

        for record in snapshot.mappings("WorkGroup"):
            wg = record.mapping
            wg_id = wg.get("id")
            composer_id = wg.get("composer_id")

            if not composer_id:
                self._add_error(
                    "REF-001", "work_group", wg_id, "composer_id", "WorkGroup missing composer_id", str(record.path)
                )
            elif composer_id not in person_ids:
                self._add_error(
                    "REF-001",
                    "work_group",
                    wg_id,
                    "composer_id",
                    f"WorkGroup references non-existent Person: {composer_id}",
                    str(record.path),
                )

    def _validate_work_composer_references(self, snapshot: CatalogSnapshot):
        """REF-002: Work.composer_id MUST reference existing Person."""
        if not hasattr(self.adapter, "persons"):
            return

        person_ids = {p["id"] for p in self.adapter.persons.values()}

        if snapshot.missing_directory("Work") is not None:
            return

        for record in snapshot.mappings("Work"):
            work = record.mapping
            work_id = work.get("id")
            composer_id = work.get("composer_id")

            if not composer_id:
                self._add_error("REF-002", "work", work_id, "composer_id", "Work missing composer_id", str(record.path))
            elif composer_id not in person_ids:
                self._add_error(
                    "REF-002",
                    "work",
                    work_id,
                    "composer_id",
                    f"Work references non-existent Person: {composer_id}",
                    str(record.path),
                )

    def _validate_work_work_group_references(self, snapshot: CatalogSnapshot):
        """REF-003: Work.work_group_id MUST reference existing WorkGroup."""
        wg_ids = snapshot.ids("WorkGroup")

        if snapshot.missing_directory("Work") is not None:
            return

        for record in snapshot.mappings("Work"):
            work = record.mapping
            work_id = work.get("id")
            wg_id = work.get("work_group_id")

            if not wg_id:
                self._add_error("REF-003", "work", work_id, "work_group_id", "Work missing work_group_id", str(record.path))
            elif wg_id not in wg_ids:
                self._add_error(
                    "REF-003",
                    "work",
                    work_id,
                    "work_group_id",
                    f"Work references non-existent WorkGroup: {wg_id}",
                    str(record.path),
                )

    def _validate_performance_work_references(self, snapshot: CatalogSnapshot):
        """REF-004: Performance.work_id MUST reference existing Work."""
        work_ids = snapshot.ids("Work")

        if snapshot.missing_directory("Performance") is not None:
            return

        for record in snapshot.mappings("Performance"):
            perf = record.mapping
            perf_id = perf.get("id")
            work_id = perf.get("work_id")

            if not work_id:
                self._add_error("REF-004", "performance", perf_id, "work_id", "Performance missing work_id", str(record.path))
            elif work_id not in work_ids:
                self._add_error(
                    "REF-004",
                    "performance",
                    perf_id,
                    "work_id",
                    f"Performance references non-existent Work: {work_id}",
                    str(record.path),
                )

    def _validate_no_direct_wg_performance_references(self, snapshot: CatalogSnapshot):
        """REF-005: Performance MUST NOT reference WorkGroup.

        A Performance must reference a Work, never a WorkGroup directly.
        """
        wg_ids = snapshot.ids("WorkGroup")

        if snapshot.missing_directory("Performance") is not None:
            return

        for record in snapshot.mappings("Performance"):
            perf = record.mapping
            perf_id = perf.get("id")
            work_id = perf.get("work_id")

            # If work_id points to a work_group, it's an error
            if work_id and work_id in wg_ids:
                self._add_error(
                    "REF-005",
                    "performance",
                    perf_id,
                    "work_id",
                    f"Performance references WorkGroup {work_id}, must reference Work",
                    str(record.path),
                )

    def _validate_performance_has_performers(self, snapshot: CatalogSnapshot):
        """DOM-044: Performance MUST have at least one performer.

        This is required for safe rendering on the public website.
        """
        if snapshot.missing_directory("Performance") is not None:
            return

        for record in snapshot.mappings("Performance"):
            perf = record.mapping
            perf_id = perf.get("id")
            performers = perf.get("performers", [])

            if not performers or len(performers) == 0:
                self._add_error(
                    "DOM-044",
                    "performance",
                    perf_id,
                    "performers",
                    "Performance must have at least one performer",
                    str(record.path),
                )
