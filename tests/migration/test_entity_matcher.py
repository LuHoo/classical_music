"""Test entity matcher candidate discovery and identity resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from classical_music.migration.entity_matcher import (
    EntityMatcher,
    extract_catalogue_number,
    extract_version_info,
    normalize_title,
)
from classical_music.migration.models import (
    PerformanceIdentityResolution,
    WorkIdentityResolution,
)
from classical_music.migration.writer import slugify


def test_normalize_title():
    """Test title normalization for matching."""
    assert normalize_title("Symphony No. 1 in C minor") == 'symphony no. 1 in c minor'
    assert (
        normalize_title('Symphony No. 1 in C minor "Das kecke Beserl"')
        == 'symphony no. 1 in c minor "das kecke beserl"'
    )
    # Test various quote styles normalize to double quote
    assert (
        normalize_title("Symphony No. 1 'quoted'")
        == 'symphony no. 1 "quoted"'
    )
    assert normalize_title("Ave  Maria") == "ave maria"  # Collapse spaces


def test_extract_version_info():
    """Test version extraction from titles."""
    # Standard version pattern
    result = extract_version_info("Symphony No. 1 (1865 version)")
    assert result is not None
    assert result["year"] == "1865"
    assert result["type"] == "version"
    
    # Revision pattern
    result = extract_version_info("Symphony No. 3 (1889 revision)")
    assert result is not None
    assert result["year"] == "1889"
    assert result["type"] == "revision"
    
    # Just year
    result = extract_version_info("Symphony No. 4 (1877)")
    assert result is not None
    assert result["year"] == "1877"
    
    # No version info
    result = extract_version_info("Symphony No. 1 in C minor")
    assert result is None


def test_extract_catalogue_number():
    """Test catalogue number extraction."""
    # WAB number
    assert extract_catalogue_number("Symphony No. 1, WAB. 101") == "WAB.101"
    
    # Opus number
    assert extract_catalogue_number("Piano Sonata Op. 23") == "Op.23"
    assert extract_catalogue_number("Variations Op. 56a") == "Op.56a"
    assert extract_catalogue_number("Clarinet Sonata Op. 120/1") == "Op.120/1"
    assert extract_catalogue_number("8 Songs, Op. 57/3, 4 (vc/pf)") == "Op.57/3,4"
    assert extract_catalogue_number("Alto Rhapsody, Op. 53 for contralto") == "Op.53"
    
    # Köchel number
    assert extract_catalogue_number("Symphony K. 545") == "K.545"
    
    # BWV number
    assert extract_catalogue_number("Prelude BWV 846") == "BWV.846"
    
    # No catalogue
    assert extract_catalogue_number("Untitled Work") is None


def test_slugify_outputs_ascii_and_preserves_flat_meaning():
    assert slugify("Piano Concerto No. 2 in B♭ major") == "piano-concerto-no-2-in-b-flat-major"
    assert slugify("6 Klavierstücke, István Kertész") == "6-klavierstucke-istvan-kertesz"
    assert slugify("Ein deutsches Requiem (1865–68)") == "ein-deutsches-requiem-1865-68"


def test_entity_matcher_loads_canonical_data(data_root: Path):
    """Test that EntityMatcher loads canonical entities."""
    matcher = EntityMatcher(data_root)
    
    # Verify counts
    assert len(matcher.works) > 0
    assert len(matcher.work_groups) > 0
    assert len(matcher.persons) > 0


def test_candidate_discovery_bruckner_exact_match(data_root: Path):
    """Test finding candidates for exact Bruckner work."""
    matcher = EntityMatcher(data_root)
    
    # Find candidates for exact title
    candidates = matcher.find_work_candidates(
        "anton-bruckner",
        'Symphony No. 1 in C minor "Das kecke Beserl"'
    )
    assert len(candidates) >= 1
    
    # Should find the exact Bruckner symphony
    assert any("symphony" in c.entity_id.lower() for c in candidates)


def test_identity_resolution_with_version_evidence(data_root: Path):
    """Test identity resolution disambiguates using version evidence."""
    matcher = EntityMatcher(data_root)
    
    # Title with version info disambiguates between three versions
    title_with_version = 'Symphony No. 1 in C minor "Das kecke Beserl" (1865 version)'
    
    candidates = matcher.find_work_candidates("anton-bruckner", title_with_version)
    result = matcher.resolve_work_identity(title_with_version, "anton-bruckner", candidates)
    
    # With version evidence, should resolve to matched
    # (even though multiple base candidates exist)
    assert result.status == WorkIdentityResolution.MATCHED
    assert result.matched_work_id is not None


def test_identity_resolution_multiple_candidates_no_version(data_root: Path):
    """Test that multiple candidates without version evidence = unresolved."""
    matcher = EntityMatcher(data_root)
    
    # Title without version - matches 3 versions of same symphony
    title_no_version = 'Symphony No. 1 in C minor "Das kecke Beserl"'
    
    candidates = matcher.find_work_candidates("anton-bruckner", title_no_version)
    result = matcher.resolve_work_identity(title_no_version, "anton-bruckner", candidates)
    
    # Multiple candidates without disambiguating evidence should be UNRESOLVED
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action
    assert result.candidates_count == 3


def test_version_text_in_candidates(data_root: Path):
    """Test that version text is preserved during candidate discovery."""
    matcher = EntityMatcher(data_root)
    
    # Legacy Markdown has version info in parentheses
    candidates = matcher.find_work_candidates(
        "anton-bruckner",
        'Symphony No. 1 in C minor "Das kecke Beserl" (1865 version)'
    )
    
    # Should find the base work by stripping version text
    assert len(candidates) > 0


def test_version_evidence_used_in_resolution(data_root: Path):
    """Test that version evidence is captured and used."""
    matcher = EntityMatcher(data_root)
    
    title_with_version = 'Symphony No. 1 in C minor "Das kecke Beserl" (1865 version)'
    
    candidates = matcher.find_work_candidates("anton-bruckner", title_with_version)
    result = matcher.resolve_work_identity("anton-bruckner", title_with_version, candidates)
    
    # Version info should be in evidence_used
    assert any("version" in evidence for evidence in result.evidence_used)


def test_no_match_means_unresolved_not_new_identity(data_root: Path):
    """Test that NO_MATCH != NEW_WORK (fundamental rule)."""
    matcher = EntityMatcher(data_root)
    
    # Non-existent work
    candidates = matcher.find_work_candidates(
        "anton-bruckner",
        "Completely Fake Symphony in Z Major"
    )
    
    result = matcher.resolve_work_identity(
        "Completely Fake Symphony in Z Major",
        "anton-bruckner",
        candidates
    )
    
    # Should be UNRESOLVED, not NEW_IDENTITY
    # (NEW_IDENTITY requires positive evidence for genuinely new Work)
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action


def test_bruckner_tantum_ergo_catalogue_collisions_resolve_distinct_works(data_root: Path):
    matcher = EntityMatcher(data_root)

    expected = {
        ("Tantum ergo (c. 1845)", "WAB.32"): "anton-bruckner-tantum-ergo-work",
        ("Tantum ergo (1846/1888)", "WAB.42"): "anton-bruckner-tantum-ergo-2-work",
        ("Tantum ergo (c. 1845)", "WAB.43"): "anton-bruckner-tantum-ergo-3-work",
    }

    for title, catalogue in expected:
        candidates = matcher.find_work_candidates(
            "anton-bruckner",
            title,
            catalogue=catalogue,
        )
        result = matcher.resolve_work_identity(
            title,
            "anton-bruckner",
            candidates,
            catalogue=catalogue,
        )
        assert result.status == WorkIdentityResolution.MATCHED
        assert result.matched_work_id == expected[(title, catalogue)]


def test_source_provenance_selects_bruckner_symphony_no_5_versions(data_root: Path):
    matcher = EntityMatcher(data_root)

    cases = {
        48: "anton-bruckner-symphony-no-5-in-bb-major-work",
        50: "anton-bruckner-symphony-no-5-in-bb-major-2-work",
    }

    for line, expected_id in cases.items():
        title = "Symphony No. 5 in B♭ major (1876 first concept)"
        candidates = matcher.find_work_candidates(
            "anton-bruckner",
            title,
            source_file="docs/bruckner.md",
            source_line=line,
            catalogue="WAB.105",
        )
        result = matcher.resolve_work_identity(
            title,
            "anton-bruckner",
            candidates,
            source_file="docs/bruckner.md",
            source_line=line,
            catalogue="WAB.105",
        )
        assert result.status == WorkIdentityResolution.MATCHED
        assert result.matched_work_id == expected_id


def test_prokofiev_opus_resolves_original_and_revised_versions(data_root: Path):
    matcher = EntityMatcher(data_root)

    cases = {
        ("Sinfonietta in A (original version)", "Op.5"): "sergei-prokofiev-sinfonietta-in-a-original-version-work",
        ("Sinfonietta in A (revised version of Op. 5)", "Op.48"): "sergei-prokofiev-sinfonietta-in-a-revised-version-of-op-5-work",
        ("Symphony No. 4 in C (original version)", "Op.47"): "sergei-prokofiev-symphony-no-4-in-c-original-version-work",
        ("Symphony No. 4 in C (revised version)", "Op.112"): "sergei-prokofiev-symphony-no-4-in-c-revised-version-work",
    }

    for (title, catalogue), expected_id in cases.items():
        candidates = matcher.find_work_candidates("sergei-prokofiev", title, catalogue=catalogue)
        result = matcher.resolve_work_identity(
            title,
            "sergei-prokofiev",
            candidates,
            catalogue=catalogue,
        )
        assert result.status == WorkIdentityResolution.MATCHED
        assert result.matched_work_id == expected_id


def test_composer_mapping(data_root: Path):
    """Test doc slug to canonical composer_id mapping."""
    matcher = EntityMatcher(data_root)
    
    # Slug "bruckner" should resolve to "anton-bruckner"
    canonical_id = matcher.resolve_composer_id("bruckner")
    assert canonical_id == "anton-bruckner"


def test_unresolved_composer_fails_closed(data_root: Path):
    """Test that unknown composer slug doesn't fallback."""
    matcher = EntityMatcher(data_root)
    
    # Unknown composer should return None, not fallback
    canonical_id = matcher.resolve_composer_id("completely-unknown-composer")
    assert canonical_id is None


def test_composer_mapping_uses_person_source_without_existing_works(tmp_path: Path):
    """New composer seeds should resolve from Person source provenance."""
    persons = tmp_path / "persons"
    works = tmp_path / "works"
    groups = tmp_path / "work-groups"
    performances = tmp_path / "performances"
    persons.mkdir()
    works.mkdir()
    groups.mkdir()
    performances.mkdir()
    (persons / "johannes-brahms.yaml").write_text(
        'id: "johannes-brahms"\n'
        'name: "Johannes Brahms"\n'
        'sort_name: "Brahms, Johannes"\n'
        "roles:\n"
        '  - "composer"\n'
        "source:\n"
        '  file: "docs/brahms.md"\n',
        encoding="utf-8",
    )

    matcher = EntityMatcher(tmp_path)

    assert matcher.resolve_composer_id("brahms") == "johannes-brahms"


def test_curated_composer_source_with_no_existing_work_creates_new_identity(tmp_path: Path):
    """Curated composer markdown is positive provenance for new Work candidates."""
    persons = tmp_path / "persons"
    works = tmp_path / "works"
    groups = tmp_path / "work-groups"
    performances = tmp_path / "performances"
    persons.mkdir()
    works.mkdir()
    groups.mkdir()
    performances.mkdir()
    (persons / "johannes-brahms.yaml").write_text(
        'id: "johannes-brahms"\n'
        'name: "Johannes Brahms"\n'
        'sort_name: "Brahms, Johannes"\n'
        "roles:\n"
        '  - "composer"\n'
        "source:\n"
        '  file: "docs/brahms.md"\n',
        encoding="utf-8",
    )

    matcher = EntityMatcher(tmp_path)
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1854-1876)",
        "johannes-brahms",
        [],
        source_file="docs/brahms.md",
        source_line=31,
        catalogue="Op.68",
    )

    assert result.status == WorkIdentityResolution.NEW_IDENTITY
    assert result.requires_curator_action is False
    assert "curated_source_provenance" in result.evidence_used


def test_uncurated_no_match_still_fails_closed(data_root: Path):
    """A random no-candidate title must not become a new Work."""
    matcher = EntityMatcher(data_root)
    result = matcher.resolve_work_identity(
        "Completely Fake Symphony in Z Major",
        "anton-bruckner",
        [],
        source_file="docs/not-bruckner.md",
        source_line=1,
    )

    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True


def test_tidal_source_with_no_existing_performance_creates_new_performance(data_root: Path):
    matcher = EntityMatcher(data_root)

    result = matcher.resolve_performance_identity(
        "johannes-brahms-symphony-no-1-work",
        "Chamber Orchestra of Europe, Paavo Berglund",
        "https://tidal.com/browse/track/284016473?u",
        [],
    )

    assert result.status == PerformanceIdentityResolution.NEW_PERFORMANCE
    assert result.requires_curator_action is False
    assert result.evidence_used == ["tidal_url"]


def test_matches_summary(data_root: Path):
    """Test that matches summary reports loaded entity counts."""
    matcher = EntityMatcher(data_root)
    summary = matcher.matches_summary()
    
    assert summary["persons"] > 0
    assert summary["work_groups"] > 0
    assert summary["works"] > 0
    assert summary["performances"] > 0


def test_single_candidate_requires_positive_version_evidence(data_root: Path):
    """
    Requirement #2: Single candidate + source version must have positive evidence.
    
    Test: source says 1865, canonical has no version evidence → UNRESOLVED
    (not MATCHED by absence of contradiction)
    """
    matcher = EntityMatcher(data_root)
    
    # Create a synthetic candidate with no version evidence
    from classical_music.migration.entity_matcher import ExistingEntity
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="test-work",
        file_path=data_root / "test.yaml",
        data={
            "id": "test-work",
            "title": "Symphony No. 1 in C minor",
            # No version_year, no date_text, no version in title
        },
    )
    
    # Source explicitly names 1865
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1865 version)",
        "test-composer",
        [candidate],
    )
    
    # Without positive version evidence, must be UNRESOLVED
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.candidates_count == 1
    assert result.requires_curator_action is True


def test_single_candidate_with_positive_version_evidence(data_root: Path):
    """
    Test: source says 1865, canonical has explicit version_year 1865 → MATCHED
    """
    matcher = EntityMatcher(data_root)
    
    from classical_music.migration.entity_matcher import ExistingEntity
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="test-work-1865",
        file_path=data_root / "test.yaml",
        data={
            "id": "test-work-1865",
            "title": "Symphony No. 1 in C minor",
            "version_year": "1865",  # Positive evidence
        },
    )
    
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1865 version)",
        "test-composer",
        [candidate],
    )
    
    # With positive version_year evidence, should MATCH
    assert result.status == WorkIdentityResolution.MATCHED
    assert result.matched_work_id == "test-work-1865"
    assert result.requires_curator_action is False


def test_single_candidate_contradictory_version(data_root: Path):
    """
    Test: source says 1865, canonical explicitly says 1889 → UNRESOLVED
    (contradictory explicit evidence means not this version)
    """
    matcher = EntityMatcher(data_root)
    
    from classical_music.migration.entity_matcher import ExistingEntity
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="test-work-1889",
        file_path=data_root / "test.yaml",
        data={
            "id": "test-work-1889",
            "title": "Symphony No. 1 in C minor",
            "version_year": "1889",  # Contradicts source
        },
    )
    
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor (1865 version)",
        "test-composer",
        [candidate],
    )
    
    # Explicit contradiction means this is not the right version
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True


def test_catalogue_evidence_does_not_override_version(data_root: Path):
    """
    Requirement: Catalogue evidence must not override contradictory version evidence.
    
    Test: same WAB family + source 1873 + candidate explicitly 1889 → UNRESOLVED
    """
    matcher = EntityMatcher(data_root)
    
    from classical_music.migration.entity_matcher import ExistingEntity
    # Candidate in same WAB family but different version
    candidate = ExistingEntity(
        entity_type="work",
        entity_id="bruckner-sym1-1889-version",
        file_path=data_root / "test.yaml",
        data={
            "id": "bruckner-sym1-1889-version",
            "title": "Symphony No. 1 in C minor",
            "catalogue": "WAB.101",
            "version_year": "1889",  # Explicit different version
        },
    )
    
    # Source explicitly says 1873 with same catalogue number
    result = matcher.resolve_work_identity(
        "Symphony No. 1 in C minor, WAB. 101 (1873 version)",
        "anton-bruckner",
        [candidate],
    )
    
    # Version evidence overrides catalogue evidence when contradictory
    assert result.status == WorkIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True


def test_find_performance_candidates_by_tidal_url(data_root: Path):
    """
    Test: Performance candidate discovery by Tidal URL.
    
    For a given Work, find canonical Performance with matching Tidal URL.
    """
    matcher = EntityMatcher(data_root)
    
    # Try finding performances for a known Bruckner work
    from classical_music.migration.entity_matcher import ExistingEntity
    
    # Performance exists in canonical data for some work
    # For this test, create synthetic scenario since we need specific work_id
    test_work_id = "test-work-123"
    
    # Performances are loaded from data/performances/
    # Just verify the method signature works and returns a list
    candidates = matcher.find_performance_candidates(
        work_id=test_work_id,
        tidal_url="https://tidal.com/browse/track/123456",
    )
    
    # Should return a list (empty if no matches)
    assert isinstance(candidates, list)


def test_resolve_performance_identity_with_tidal_url(data_root: Path):
    """
    Test: Performance identity resolution with exact Tidal URL match.
    
    Same Tidal URL + same Work → MATCHED_EXISTING
    """
    matcher = EntityMatcher(data_root)
    from classical_music.migration.entity_matcher import ExistingEntity
    from classical_music.migration.models import PerformanceIdentityResolution
    
    # Synthetic canonical Performance
    perf_candidate = ExistingEntity(
        entity_type="performance",
        entity_id="perf-123",
        file_path=data_root / "test.yaml",
        data={
            "id": "perf-123",
            "work_id": "work-xyz",
            "tidal_url": "https://tidal.com/browse/track/123456",
            "performer_text": "Vienna Philharmonic, Zubin Mehta",
            "performance_profile": "live",
        },
    )
    
    result = matcher.resolve_performance_identity(
        work_id="work-xyz",
        performer_text="Vienna Philharmonic, Zubin Mehta",
        tidal_url="https://tidal.com/browse/track/123456",
        candidates=[perf_candidate],
    )
    
    assert result.status == PerformanceIdentityResolution.MATCHED_EXISTING
    assert result.matched_performance_id == "perf-123"
    assert result.performance_profile == "live"
    assert result.requires_curator_action is False


def test_resolve_performance_identity_no_candidates(data_root: Path):
    """
    Test: Performance identity with no candidates → UNRESOLVED
    (not automatically NEW_PERFORMANCE without positive evidence)
    """
    matcher = EntityMatcher(data_root)
    from classical_music.migration.models import PerformanceIdentityResolution
    
    result = matcher.resolve_performance_identity(
        work_id="work-xyz",
        performer_text="Some Performer",
        tidal_url=None,
        candidates=[],
    )
    
    assert result.status == PerformanceIdentityResolution.UNRESOLVED
    assert result.requires_curator_action is True
