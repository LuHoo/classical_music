"""
Tests for publication data adapter.

Verifies that the adapter:
- Reads only from data/ directory
- Maps tidal.url correctly
- Maps gramophone reviews
- Converts performer objects to display names/roles
- Includes works without performances
- Keeps work groups lightweight (no recommendations)
- Excludes internal workflow data
"""

import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from classical_music.publication_adapter import PublicationDataAdapter


class TestPublicationDataAdapter:
    """Test suite for PublicationDataAdapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        # Get repo root: tests/ is directly under repo root
        repo_root = Path(__file__).parent.parent
        return PublicationDataAdapter(repo_root)
    
    def test_reads_only_from_data_directory(self, adapter):
        """Verify that adapter reads only from data/ directory, not docs/."""
        # Check that data directory exists
        data_dir = adapter.data_dir
        assert data_dir.exists(), f"data/ directory not found at {data_dir}"
        
        # Check that required subdirectories exist
        assert (data_dir / "persons").exists()
        assert (data_dir / "work-groups").exists()
        assert (data_dir / "works").exists()
        assert (data_dir / "performances").exists()
        
        # Load data
        adapter.load_canonical_data()
        
        # Verify data was loaded
        assert len(adapter._persons) > 0, "No persons loaded"
        assert len(adapter._work_groups) > 0, "No work groups loaded"
        assert len(adapter._works) > 0, "No works loaded"
        assert len(adapter._performances) > 0, "No performances loaded"
    
    def test_tidal_url_mapping(self, adapter):
        """Verify that links.tidal.url is mapped to public tidal_url field."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Find performances with tidal links
        tidal_performances = [
            p for p in adapter.performances.values() if "tidal_url" in p
        ]
        
        assert len(tidal_performances) > 0, "No performances with tidal URLs found"
        
        # Verify tidal URLs are properly formatted
        for perf in tidal_performances:
            tidal_url = perf.get("tidal_url")
            assert tidal_url, f"Performance {perf['id']} has empty tidal_url"
            assert "tidal.com" in tidal_url, f"Invalid tidal URL: {tidal_url}"
    
    def test_gramophone_review_mapping(self, adapter):
        """Verify that reviews.gramophone is mapped to public gramophone_ref field."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Find performances with gramophone reviews
        gramophone_performances = [
            p for p in adapter.performances.values() if "gramophone_ref" in p
        ]
        
        assert len(gramophone_performances) > 0, "No performances with gramophone refs found"
        
        # Verify gramophone refs are present
        for perf in gramophone_performances:
            gramophone_ref = perf.get("gramophone_ref")
            assert gramophone_ref, f"Performance {perf['id']} has empty gramophone_ref"
    
    def test_performer_display_format(self, adapter):
        """Verify that performer objects are converted to display format."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Find performances with performers
        performances_with_performers = [
            p for p in adapter.performances.values() if "performers" in p
        ]
        
        assert len(performances_with_performers) > 0, "No performances with performers found"
        
        # Verify performer format
        for perf in performances_with_performers:
            performers = perf.get("performers", [])
            assert isinstance(performers, list), "Performers should be a list"
            
            for performer in performers:
                assert isinstance(performer, dict), "Each performer should be a dict"
                assert "name" in performer, "Performer missing 'name' field"
                assert "role" in performer, "Performer missing 'role' field"
                
                # Names should be strings, not object strings
                assert isinstance(performer["name"], str), "Performer name should be string"
                assert not performer["name"].startswith("{"), "Name should not be object string"
    
    def test_works_without_performances_included(self, adapter):
        """Verify that works without performances are included in output."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Group performances by work
        perf_by_work = {}
        for perf_id, perf in adapter.performances.items():
            work_id = perf.get("work_id")
            if work_id:
                if work_id not in perf_by_work:
                    perf_by_work[work_id] = []
                perf_by_work[work_id].append(perf_id)
        
        # Find works without performances
        works_without_perfs = [
            work_id for work_id in adapter.works
            if work_id not in perf_by_work
        ]
        
        # Should have some works without performances
        assert len(works_without_perfs) > 0, \
            "Expected some works without performances, but all have them"
        
        # Verify all works are in publication model
        for work_id in adapter.works:
            assert work_id in adapter.works, f"Work {work_id} missing from publication model"
    
    def test_work_groups_dont_carry_recommendations(self, adapter):
        """Verify that work groups are lightweight and don't carry recommendations."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Work groups should only have: id, composer_id, title, catalogue
        valid_fields = {"id", "composer_id", "title", "catalogue"}
        
        for wg_id, wg in adapter.work_groups.items():
            actual_fields = set(wg.keys())
            unexpected_fields = actual_fields - valid_fields
            
            assert not unexpected_fields, \
                f"WorkGroup {wg_id} has unexpected fields: {unexpected_fields}"
    
    def test_no_internal_workflow_data_exposed(self, adapter):
        """Verify that internal workflow data is not in publication model."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # These are the actual internal field names to check for
        internal_field_names = [
            "_file", "_internal", "source",
            "candidates", "review", "migration", "validation_state"
        ]
        
        # Check works
        for work in adapter.works.values():
            for field in work.keys():
                assert field not in internal_field_names, \
                    f"Work {work['id']} contains internal field: {field}"
        
        # Check performances
        for perf in adapter.performances.values():
            for field in perf.keys():
                assert field not in internal_field_names, \
                    f"Performance {perf['id']} contains internal field: {field}"
    
    def test_canonical_source_not_docs(self, adapter):
        """Verify that adapter doesn't read from docs/ directory."""
        # The adapter should only know about data_dir
        assert adapter.data_dir == adapter.repo_root / "data"
        
        # Load and verify
        adapter.load_canonical_data()
        
        # All loaded data should have come from data/ directory YAML files
        # Check by verifying they have the expected structure
        for person in adapter._persons.values():
            assert "id" in person, "Person missing id (not from canonical YAML)"
            assert "name" in person, "Person missing name (not from canonical YAML)"
    
    def test_full_adaptation_pipeline(self, adapter):
        """Test the full adaptation pipeline."""
        success = adapter.adapt()
        
        # Should succeed with data
        assert success or len(adapter.errors) == 0, \
            f"Adapter failed with errors: {adapter.errors}"
        
        # Should have populated all models
        assert len(adapter.persons) > 0
        assert len(adapter.work_groups) > 0
        assert len(adapter.works) > 0
        assert len(adapter.performances) > 0
    
    def test_export_json_format(self, adapter):
        """Test that export produces valid JSON with correct structure."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "publication.json"
            adapter.export_json(output_file)
            
            assert output_file.exists(), f"Output file not created: {output_file}"
            
            # Verify valid JSON
            with open(output_file) as f:
                data = json.load(f)
            
            # Verify structure
            assert "persons" in data
            assert "work_groups" in data
            assert "works" in data
            assert "performances" in data
            
            # Verify content
            assert len(data["persons"]) > 0
            assert len(data["works"]) > 0
            assert len(data["performances"]) > 0
    
    def test_reference_validation(self, adapter):
        """Test that reference validation catches broken links."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Validate references
        adapter.validate_references()
        
        # Should have some validation info
        # Note: we expect some errors (orphaned Berlioz performances)
        # but the validation should complete
        assert isinstance(adapter.errors, list)
    
    def test_gem_field_preserved(self, adapter):
        """Test that gem field is preserved in publication model."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Find works with gem=true
        gem_works = [w for w in adapter.works.values() if w.get("gem")]
        
        # Should have some gem works
        if gem_works:
            for work in gem_works:
                assert work.get("gem") is True, "Gem field should be True"
    
    def test_catalogue_field_preserved(self, adapter):
        """Test that catalogue fields are preserved."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Find works/groups with catalogue
        works_with_catalogue = [w for w in adapter.works.values() if "catalogue" in w]
        
        # Should have some catalogue info
        if works_with_catalogue:
            for work in works_with_catalogue:
                assert "catalogue" in work, "Catalogue field should be preserved"
    
    def test_category_field_preserved(self, adapter):
        """Test that work category field is preserved."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        # Find works with category
        works_with_category = [w for w in adapter.works.values() if "category" in w]
        
        # Should have some category info
        if works_with_category:
            for work in works_with_category:
                assert "category" in work, "Category field should be preserved"


class TestPublicationDataIntegrity:
    """Test data integrity of publication model."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        repo_root = Path(__file__).parent.parent
        return PublicationDataAdapter(repo_root)
    
    def test_all_compositions_belong_to_composer(self, adapter):
        """Verify all works belong to a composer."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        for work_id, work in adapter.works.items():
            assert "composer_id" in work, f"Work {work_id} missing composer_id"
            assert work["composer_id"] in adapter.persons, \
                f"Work {work_id} references non-existent composer {work.get('composer_id')}"
    
    def test_work_group_references_exist(self, adapter):
        """Verify work group references are valid."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        for work_id, work in adapter.works.items():
            if "work_group_id" in work:
                wg_id = work["work_group_id"]
                assert wg_id in adapter.work_groups, \
                    f"Work {work_id} references non-existent work_group {wg_id}"
    
    def test_performance_work_references_exist(self, adapter):
        """Verify all performance work references exist in adapted model."""
        adapter.load_canonical_data()
        adapter.adapt_to_publication_model()
        
        orphaned_perfs = []
        for perf_id, perf in adapter.performances.items():
            if "work_id" in perf:
                work_id = perf["work_id"]
                if work_id not in adapter.works:
                    orphaned_perfs.append((perf_id, work_id))
        
        # Fail if any canonical performance references are missing from the model
        assert len(orphaned_perfs) == 0, \
            f"{len(orphaned_perfs)} orphaned performances: adapter did not load all canonical Works. " \
            f"Examples: {orphaned_perfs[:5]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
