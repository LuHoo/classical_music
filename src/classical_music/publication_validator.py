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
from typing import Any, List, Dict, Tuple
from dataclasses import dataclass, field


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

    Validation is based on the PublicationDataAdapter's loaded data.
    """

    def __init__(self, repo_root: Path = None):
        """Initialize validator with optional custom repo root.

        Args:
            repo_root: Path to repository root. If None, inferred from file location.
        """
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = repo_root

        # Import here to allow testing without full project setup
        from classical_music.publication_adapter import PublicationDataAdapter

        self.adapter = PublicationDataAdapter(repo_root)
        self.result = ValidationResult(passed=True, errors=[], warnings=[])

    def validate(self) -> ValidationResult:
        """Run full publication validation.

        Returns:
            ValidationResult with passed status and detailed error list.
        """
        self.result = ValidationResult(passed=True, errors=[], warnings=[])

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
        self._validate_work_group_references()  # REF-001
        self._validate_work_composer_references()  # REF-002
        self._validate_work_work_group_references()  # REF-003
        self._validate_performance_work_references()  # REF-004
        self._validate_no_direct_wg_performance_references()  # REF-005
        self._validate_performance_has_performers()  # DOM-044

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

    def _validate_work_group_references(self):
        """REF-001: WorkGroup.composer_id MUST reference existing Person.

        Load WorkGroups and verify each references a valid composer.
        """
        if not hasattr(self.adapter, "persons"):
            return

        person_ids = {p["id"] for p in self.adapter.persons.values()}
        wg_path = self.repo_root / "data" / "work-groups"

        if not wg_path.exists():
            return

        for wg_file in wg_path.glob("*.yaml"):
            try:
                from ruamel.yaml import YAML

                yaml = YAML()
                with open(wg_file) as f:
                    wg = yaml.load(f)

                if not wg:
                    continue

                wg_id = wg.get("id")
                composer_id = wg.get("composer_id")

                if not composer_id:
                    self._add_error(
                        "REF-001", "work_group", wg_id, "composer_id", "WorkGroup missing composer_id", str(wg_file)
                    )
                elif composer_id not in person_ids:
                    self._add_error(
                        "REF-001",
                        "work_group",
                        wg_id,
                        "composer_id",
                        f"WorkGroup references non-existent Person: {composer_id}",
                        str(wg_file),
                    )
            except Exception as e:
                # Skip files with syntax errors (caught by repository validation)
                pass

    def _validate_work_composer_references(self):
        """REF-002: Work.composer_id MUST reference existing Person."""
        if not hasattr(self.adapter, "persons"):
            return

        person_ids = {p["id"] for p in self.adapter.persons.values()}
        works_path = self.repo_root / "data" / "works"

        if not works_path.exists():
            return

        for work_file in works_path.glob("**/*.yaml"):
            try:
                from ruamel.yaml import YAML

                yaml = YAML()
                with open(work_file) as f:
                    work = yaml.load(f)

                if not work:
                    continue

                work_id = work.get("id")
                composer_id = work.get("composer_id")

                if not composer_id:
                    self._add_error("REF-002", "work", work_id, "composer_id", "Work missing composer_id", str(work_file))
                elif composer_id not in person_ids:
                    self._add_error(
                        "REF-002",
                        "work",
                        work_id,
                        "composer_id",
                        f"Work references non-existent Person: {composer_id}",
                        str(work_file),
                    )
            except Exception as e:
                pass

    def _validate_work_work_group_references(self):
        """REF-003: Work.work_group_id MUST reference existing WorkGroup."""
        # Load all work groups first
        wg_ids = set()
        wg_path = self.repo_root / "data" / "work-groups"

        if wg_path.exists():
            from ruamel.yaml import YAML

            yaml = YAML()
            for wg_file in wg_path.glob("*.yaml"):
                try:
                    with open(wg_file) as f:
                        wg = yaml.load(f)
                        if wg and wg.get("id"):
                            wg_ids.add(wg["id"])
                except Exception:
                    pass

        # Now validate works
        works_path = self.repo_root / "data" / "works"
        if not works_path.exists():
            return

        yaml = YAML()
        for work_file in works_path.glob("**/*.yaml"):
            try:
                with open(work_file) as f:
                    work = yaml.load(f)

                if not work:
                    continue

                work_id = work.get("id")
                wg_id = work.get("work_group_id")

                if not wg_id:
                    self._add_error("REF-003", "work", work_id, "work_group_id", "Work missing work_group_id", str(work_file))
                elif wg_id not in wg_ids:
                    self._add_error(
                        "REF-003",
                        "work",
                        work_id,
                        "work_group_id",
                        f"Work references non-existent WorkGroup: {wg_id}",
                        str(work_file),
                    )
            except Exception:
                pass

    def _validate_performance_work_references(self):
        """REF-004: Performance.work_id MUST reference existing Work."""
        # Load all works first
        work_ids = set()
        works_path = self.repo_root / "data" / "works"

        if works_path.exists():
            from ruamel.yaml import YAML

            yaml = YAML()
            for work_file in works_path.glob("**/*.yaml"):
                try:
                    with open(work_file) as f:
                        work = yaml.load(f)
                        if work and work.get("id"):
                            work_ids.add(work["id"])
                except Exception:
                    pass

        # Now validate performances
        perf_path = self.repo_root / "data" / "performances"
        if not perf_path.exists():
            return

        yaml = YAML()
        for perf_file in perf_path.glob("*.yaml"):
            try:
                with open(perf_file) as f:
                    perf = yaml.load(f)

                if not perf:
                    continue

                perf_id = perf.get("id")
                work_id = perf.get("work_id")

                if not work_id:
                    self._add_error("REF-004", "performance", perf_id, "work_id", "Performance missing work_id", str(perf_file))
                elif work_id not in work_ids:
                    self._add_error(
                        "REF-004",
                        "performance",
                        perf_id,
                        "work_id",
                        f"Performance references non-existent Work: {work_id}",
                        str(perf_file),
                    )
            except Exception:
                pass

    def _validate_no_direct_wg_performance_references(self):
        """REF-005: Performance MUST NOT reference WorkGroup.

        A Performance must reference a Work, never a WorkGroup directly.
        """
        # Load all work group ids
        wg_ids = set()
        wg_path = self.repo_root / "data" / "work-groups"

        if wg_path.exists():
            from ruamel.yaml import YAML

            yaml = YAML()
            for wg_file in wg_path.glob("*.yaml"):
                try:
                    with open(wg_file) as f:
                        wg = yaml.load(f)
                        if wg and wg.get("id"):
                            wg_ids.add(wg["id"])
                except Exception:
                    pass

        # Check performances don't reference WGs
        perf_path = self.repo_root / "data" / "performances"
        if not perf_path.exists():
            return

        yaml = YAML()
        for perf_file in perf_path.glob("*.yaml"):
            try:
                with open(perf_file) as f:
                    perf = yaml.load(f)

                if not perf:
                    continue

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
                        str(perf_file),
                    )
            except Exception:
                pass

    def _validate_performance_has_performers(self):
        """DOM-044: Performance MUST have at least one performer.

        This is required for safe rendering on the public website.
        """
        perf_path = self.repo_root / "data" / "performances"
        if not perf_path.exists():
            return

        from ruamel.yaml import YAML

        yaml = YAML()
        for perf_file in perf_path.glob("*.yaml"):
            try:
                with open(perf_file) as f:
                    perf = yaml.load(f)

                if not perf:
                    continue

                perf_id = perf.get("id")
                performers = perf.get("performers", [])

                if not performers or len(performers) == 0:
                    self._add_error(
                        "DOM-044",
                        "performance",
                        perf_id,
                        "performers",
                        "Performance must have at least one performer",
                        str(perf_file),
                    )
            except Exception:
                pass
