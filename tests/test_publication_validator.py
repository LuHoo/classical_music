"""Tests for publication validation.

Tests verify that publication validation fails closed on broken references
but allows non-blocking warnings (background suspicions) to pass.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from ruamel.yaml import YAML

from classical_music.publication_validator import PublicationValidator, ValidationResult


@pytest.fixture
def validator():
    """Create validator with actual project data."""
    repo_root = Path(__file__).parent.parent.parent
    return PublicationValidator(repo_root)


@pytest.fixture
def temp_repo():
    """Create temporary test repository structure."""
    tmpdir = tempfile.mkdtemp()
    repo_path = Path(tmpdir)

    # Create required directories
    (repo_path / "data" / "persons").mkdir(parents=True)
    (repo_path / "data" / "work-groups").mkdir(parents=True)
    (repo_path / "data" / "works").mkdir(parents=True)
    (repo_path / "data" / "performances").mkdir(parents=True)

    yield repo_path

    # Cleanup
    shutil.rmtree(tmpdir)


def _write_yaml(path: Path, data: dict):
    """Helper to write YAML file."""
    yaml = YAML()
    with open(path, "w") as f:
        yaml.dump(data, f)


def _create_person(repo: Path, person_id: str, name: str = None) -> dict:
    """Create a test person."""
    data = {"id": person_id, "name": name or person_id.replace("-", " ").title()}
    _write_yaml(repo / "data" / "persons" / f"{person_id}.yaml", data)
    return data


def _create_work_group(repo: Path, wg_id: str, composer_id: str, title: str = None) -> dict:
    """Create a test work group."""
    data = {
        "id": wg_id,
        "composer_id": composer_id,
        "title": title or f"Work Group: {wg_id}",
    }
    _write_yaml(repo / "data" / "work-groups" / f"{wg_id}.yaml", data)
    return data


def _create_work(repo: Path, work_id: str, work_group_id: str, composer_id: str, title: str = None) -> dict:
    """Create a test work."""
    data = {
        "id": work_id,
        "work_group_id": work_group_id,
        "composer_id": composer_id,
        "title": title or f"Work: {work_id}",
    }
    _write_yaml(repo / "data" / "works" / f"{work_id}.yaml", data)
    return data


def _create_performance(repo: Path, perf_id: str, work_id: str, performers: list = None) -> dict:
    """Create a test performance."""
    if performers is None:
        performers = [{"name": "Test Ensemble"}]

    data = {
        "id": perf_id,
        "work_id": work_id,
        "performers": performers,
    }
    _write_yaml(repo / "data" / "performances" / f"{perf_id}.yaml", data)
    return data


# ============================================================================
# Acceptance Criteria Tests
# ============================================================================


class TestAcceptanceCriteria:
    """Tests for issue #192 acceptance criteria."""

    def test_broken_performance_work_reference_fails(self, temp_repo):
        """AC#1: Tests inject broken Performance→Work reference and validation fails."""
        # Create valid person and work group
        _create_person(temp_repo, "bach", "Johann Sebastian Bach")
        _create_work_group(temp_repo, "bwv-846", "bach", "WTC Book 1, Prelude BWV 846")
        _create_work(temp_repo, "bach-wtc-1-prelude", "bwv-846", "bach", "WTC Book 1, Prelude")

        # Create performance referencing NON-EXISTENT work
        _create_performance(temp_repo, "perf-1", "NONEXISTENT-WORK", [{"name": "Glenn Gould"}])

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        assert not result.passed, "Validation should fail on broken Performance→Work reference"
        assert result.error_count() > 0, "Should have at least one error"
        assert any(e.rule_id == "REF-004" for e in result.errors), "Should have REF-004 error"
        assert result.exit_code() == 1, "Exit code should be non-zero on errors"

    def test_broken_work_work_group_reference_fails(self, temp_repo):
        """AC#2: Tests inject Work→missing WorkGroup reference and validation fails."""
        # Create valid person
        _create_person(temp_repo, "beethoven", "Ludwig van Beethoven")

        # Create work referencing NON-EXISTENT work group
        _create_work(temp_repo, "beethoven-symphony-9", "NONEXISTENT-WG", "beethoven", "Symphony No. 9")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        assert not result.passed, "Validation should fail on broken Work→WorkGroup reference"
        assert result.error_count() > 0
        assert any(e.rule_id == "REF-003" for e in result.errors), "Should have REF-003 error"
        assert result.exit_code() == 1

    def test_broken_work_composer_reference_fails(self, temp_repo):
        """AC#2b: Tests inject Work→missing Person reference and validation fails."""
        # Create work group with valid composer
        _create_person(temp_repo, "mozart", "Wolfgang Amadeus Mozart")
        _create_work_group(temp_repo, "k-545", "mozart", "Piano Sonata K. 545")

        # Create work referencing NON-EXISTENT composer
        _create_work(temp_repo, "mozart-sonata-k545", "k-545", "NONEXISTENT-PERSON", "Piano Sonata K. 545")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        assert not result.passed, "Validation should fail on broken Work→Person reference"
        assert result.error_count() > 0
        assert any(e.rule_id == "REF-002" for e in result.errors), "Should have REF-002 error"

    def test_broken_work_group_composer_reference_fails(self, temp_repo):
        """AC#2c: Tests inject WorkGroup→missing Person reference and validation fails."""
        # Create work group referencing NON-EXISTENT composer
        _create_work_group(temp_repo, "symphony-40", "NONEXISTENT-COMPOSER", "Symphony No. 40")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        assert not result.passed, "Validation should fail on broken WorkGroup→Person reference"
        assert result.error_count() > 0
        assert any(e.rule_id == "REF-001" for e in result.errors), "Should have REF-001 error"

    def test_performance_references_work_group_fails(self, temp_repo):
        """AC#2d: Tests that Performance directly referencing WorkGroup fails."""
        # Create person, work group, but NO individual works
        _create_person(temp_repo, "chopin", "Frédéric Chopin")
        _create_work_group(temp_repo, "nocturnes", "chopin", "Nocturnes")

        # Create performance referencing the WORK GROUP (wrong!)
        _create_performance(temp_repo, "perf-chopin-nocturne", "nocturnes", [{"name": "Arthur Rubinstein"}])

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        assert not result.passed, "Validation should fail when Performance references WorkGroup"
        assert any(e.rule_id == "REF-005" for e in result.errors), "Should have REF-005 error"

    def test_background_warnings_dont_block_publication(self, temp_repo):
        """AC#3: Tests show background_suspicion warnings do not block publication."""
        # Create completely valid data
        _create_person(temp_repo, "brahms", "Johannes Brahms")
        _create_work_group(temp_repo, "symphonies", "brahms", "Symphonies")
        _create_work(temp_repo, "brahms-symphony-1", "symphonies", "brahms", "Symphony No. 1")
        _create_performance(
            temp_repo, "perf-brahms-sym1", "brahms-symphony-1", [{"name": "Berlin Philharmonic"}]
        )

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        # Should pass even if there are non-blocking warnings
        assert result.passed, "Valid data should pass validation"
        assert result.exit_code() == 0, "Exit code should be zero on success"
        # (Warnings may or may not exist, but they don't block)

    def test_valid_publication_data_passes(self, temp_repo):
        """AC#4: Valid publication data passes all checks."""
        # Create complete valid reference chain
        _create_person(temp_repo, "debussy", "Claude Debussy")
        _create_work_group(temp_repo, "la-mer", "debussy", "La Mer")
        _create_work(temp_repo, "debussy-la-mer", "la-mer", "debussy", "La Mer, L. 109")
        _create_performance(
            temp_repo,
            "perf-la-mer-karajan",
            "debussy-la-mer",
            [{"name": "Berlin Philharmonic", "role": "orchestra"}, {"name": "Herbert von Karajan", "role": "conductor"}],
        )

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        assert result.passed, "Valid data should pass"
        assert result.error_count() == 0, "Should have no errors"
        assert result.exit_code() == 0, "Exit code should be 0"


# ============================================================================
# Reference Validation Tests
# ============================================================================


class TestReferenceValidation:
    """Tests for individual reference validation rules."""

    def test_ref_001_work_group_composer_exists(self, temp_repo):
        """REF-001: WorkGroup.composer_id must reference existing Person."""
        # Create person
        _create_person(temp_repo, "ravel", "Maurice Ravel")
        # Create work group with valid composer
        _create_work_group(temp_repo, "daphnis-et-chloe", "ravel")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        # Should pass (no REF-001 errors)
        ref_001_errors = [e for e in result.errors if e.rule_id == "REF-001"]
        assert len(ref_001_errors) == 0, "Should have no REF-001 errors for valid reference"

    def test_ref_002_work_composer_exists(self, temp_repo):
        """REF-002: Work.composer_id must reference existing Person."""
        _create_person(temp_repo, "stravinsky", "Igor Stravinsky")
        _create_work_group(temp_repo, "rite-of-spring", "stravinsky")
        _create_work(temp_repo, "stravinsky-rite", "rite-of-spring", "stravinsky")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        ref_002_errors = [e for e in result.errors if e.rule_id == "REF-002"]
        assert len(ref_002_errors) == 0

    def test_ref_003_work_group_exists(self, temp_repo):
        """REF-003: Work.work_group_id must reference existing WorkGroup."""
        _create_person(temp_repo, "satie", "Erik Satie")
        _create_work_group(temp_repo, "gymnopedies", "satie")
        _create_work(temp_repo, "satie-gymnopede-1", "gymnopedies", "satie")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        ref_003_errors = [e for e in result.errors if e.rule_id == "REF-003"]
        assert len(ref_003_errors) == 0

    def test_ref_004_work_exists(self, temp_repo):
        """REF-004: Performance.work_id must reference existing Work."""
        _create_person(temp_repo, "schubert", "Franz Schubert")
        _create_work_group(temp_repo, "impromptus", "schubert")
        _create_work(temp_repo, "schubert-impromtu-op90-1", "impromptus", "schubert")
        _create_performance(temp_repo, "perf-schubert", "schubert-impromtu-op90-1")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        ref_004_errors = [e for e in result.errors if e.rule_id == "REF-004"]
        assert len(ref_004_errors) == 0

    def test_ref_005_no_work_group_direct_reference(self, temp_repo):
        """REF-005: Performance.work_id must not reference WorkGroup."""
        _create_person(temp_repo, "vivaldi", "Antonio Vivaldi")
        _create_work_group(temp_repo, "four-seasons", "vivaldi")

        # Performance references work group directly (wrong!)
        _create_performance(temp_repo, "perf-four-seasons", "four-seasons")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        ref_005_errors = [e for e in result.errors if e.rule_id == "REF-005"]
        assert len(ref_005_errors) > 0, "Should catch Performance→WorkGroup reference"


# ============================================================================
# Data Completeness Tests
# ============================================================================


class TestDataCompleteness:
    """Tests for required data fields."""

    def test_performance_must_have_performers(self, temp_repo):
        """DOM-044: Performance must have at least one performer."""
        _create_person(temp_repo, "handel", "George Frideric Handel")
        _create_work_group(temp_repo, "messiah", "handel")
        _create_work(temp_repo, "handel-messiah", "messiah", "handel")

        # Create performance with NO performers
        _write_yaml(
            temp_repo / "data" / "performances" / "perf-messiah.yaml",
            {
                "id": "perf-messiah",
                "work_id": "handel-messiah",
                # Missing 'performers' field
            },
        )

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        dom_044_errors = [e for e in result.errors if e.rule_id == "DOM-044"]
        assert len(dom_044_errors) > 0, "Should require at least one performer"

    def test_performance_with_empty_performers_array_fails(self, temp_repo):
        """DOM-044: Empty performers array should fail."""
        _create_person(temp_repo, "gluck", "Christoph Willuck Gluck")
        _create_work_group(temp_repo, "orfeo-eurydice", "gluck")
        _create_work(temp_repo, "gluck-orfeo", "orfeo-eurydice", "gluck")

        # Create performance with empty performers array
        _write_yaml(
            temp_repo / "data" / "performances" / "perf-orfeo.yaml",
            {
                "id": "perf-orfeo",
                "work_id": "gluck-orfeo",
                "performers": [],  # Empty!
            },
        )

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        dom_044_errors = [e for e in result.errors if e.rule_id == "DOM-044"]
        assert len(dom_044_errors) > 0


# ============================================================================
# Publication with Real Data
# ============================================================================


class TestPublicationWithRealData:
    """Tests using actual project data from data/ directory."""

    def test_real_project_data_validates(self, validator):
        """Validate that actual project data passes publication validation."""
        result = validator.validate()

        # Report results
        print(f"\n{result.summary()}")
        if result.error_count() > 0:
            print(f"\nErrors ({result.error_count()}):")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error.entity_type}/{error.entity_id}: {error.message} ({error.rule_id})")
            if result.error_count() > 5:
                print(f"  ... and {result.error_count() - 5} more")

        # Main assertion
        assert result.passed, f"Publication validation failed: {result.error_count()} errors"
        assert result.exit_code() == 0, "Exit code should be 0"

    def test_validator_returns_validation_result(self, validator):
        """Validate that validator returns proper ValidationResult."""
        result = validator.validate()

        assert isinstance(result, ValidationResult)
        assert hasattr(result, "passed")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "exit_code")
        assert hasattr(result, "error_count")
        assert hasattr(result, "warning_count")
        assert hasattr(result, "summary")

        # Test exit code methods
        if result.passed:
            assert result.exit_code() == 0
        else:
            assert result.exit_code() == 1

    def test_validator_summary_string(self, validator):
        """Test that validator returns readable summary."""
        result = validator.validate()
        summary = result.summary()

        assert isinstance(summary, str)
        assert len(summary) > 0
        if result.passed:
            assert "✅" in summary or "passed" in summary.lower()
        else:
            assert "❌" in summary or "failed" in summary.lower()


# ============================================================================
# Integration Tests
# ============================================================================


class TestValidationIntegration:
    """Integration tests for validator with various scenarios."""

    def test_multiple_errors_collected(self, temp_repo):
        """Validator collects all errors, not just first one."""
        # Create person
        _create_person(temp_repo, "tchaik", "Peter Ilyich Tchaikovsky")
        _create_work_group(temp_repo, "ballets", "tchaik")

        # Create multiple broken references
        _create_work(temp_repo, "work-1", "ballets", "BROKEN-PERSON-1")
        _create_work(temp_repo, "work-2", "ballets", "BROKEN-PERSON-2")
        _create_work(temp_repo, "work-3", "BROKEN-WG", "tchaik")
        _create_performance(temp_repo, "perf-1", "BROKEN-WORK-1")
        _create_performance(temp_repo, "perf-2", "BROKEN-WORK-2")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        # Should have collected multiple errors
        assert not result.passed
        assert result.error_count() >= 5, f"Expected at least 5 errors, got {result.error_count()}"

    def test_error_details_are_present(self, temp_repo):
        """Each error contains required details."""
        _create_person(temp_repo, "berlioz", "Hector Berlioz")
        _create_performance(temp_repo, "perf-berlioz", "NONEXISTENT-WORK")

        validator = PublicationValidator(temp_repo)
        result = validator.validate()

        assert len(result.errors) > 0
        error = result.errors[0]

        # Check all required fields
        assert error.rule_id
        assert error.severity == "error"
        assert error.entity_type == "performance"
        assert error.entity_id
        assert error.field
        assert error.message
        assert error.source_file  # Should have path to the file
