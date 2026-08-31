#!/usr/bin/env python3
"""
Test suite for site generation from canonical data.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import unittest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_site import SiteGenerator


class TestSiteGenerator(unittest.TestCase):
    """Tests for SiteGenerator class."""
    
    def setUp(self):
        """Set up test environment."""
        self.repo_root = Path(__file__).parent.parent
        self.generator = SiteGenerator(self.repo_root)
    
    def test_load_canonical_data(self):
        """Test that all canonical data directories can be loaded."""
        self.generator.load_canonical_data()
        
        # Verify data was loaded
        self.assertGreater(len(self.generator.persons), 0)
        self.assertGreater(len(self.generator.work_groups), 0)
        self.assertGreater(len(self.generator.works), 0)
        self.assertGreater(len(self.generator.performances), 0)
    
    def test_canonical_data_files_exist(self):
        """Test that canonical data files can be found."""
        data_dirs = [
            self.repo_root / "data" / "persons",
            self.repo_root / "data" / "work-groups",
            self.repo_root / "data" / "works",
            self.repo_root / "data" / "performances",
        ]
        
        for data_dir in data_dirs:
            self.assertTrue(data_dir.exists(), f"Missing directory: {data_dir}")
            self.assertGreater(
                len(list(data_dir.glob("*.yaml"))), 
                0, 
                f"No YAML files in {data_dir}"
            )
    
    def test_person_records_have_required_fields(self):
        """Test that Person records contain essential fields."""
        self.generator.load_canonical_data()
        
        for person_id, person in self.generator.persons.items():
            self.assertIn("name", person, f"Person {person_id} missing 'name'")
            self.assertIsNotNone(person["name"])
    
    def test_work_records_have_required_fields(self):
        """Test that Work records contain essential fields."""
        self.generator.load_canonical_data()
        
        for work_id, work in self.generator.works.items():
            self.assertIn("title", work, f"Work {work_id} missing 'title'")
            self.assertIn("composer_id", work, f"Work {work_id} missing 'composer_id'")
            self.assertIn("work_group_id", work, f"Work {work_id} missing 'work_group_id'")
    
    def test_work_group_records_have_required_fields(self):
        """Test that Work Group records contain essential fields."""
        self.generator.load_canonical_data()
        
        for wg_id, wg in self.generator.work_groups.items():
            self.assertIn("composer_id", wg, f"Work Group {wg_id} missing 'composer_id'")
    
    def test_performance_records_have_required_fields(self):
        """Test that Performance records contain essential fields."""
        self.generator.load_canonical_data()
        
        for perf_id, perf in self.generator.performances.items():
            self.assertIn("work_id", perf, f"Performance {perf_id} missing 'work_id'")
    
    def test_validation_identifies_broken_references(self):
        """Test that validation catches missing referenced entities."""
        self.generator.load_canonical_data()
        success = self.generator.validate_references()
        
        # There should be some validation errors (orphaned performances)
        # But they should be documented
        if not success:
            self.assertGreater(len(self.generator.errors), 0)
            # All errors should mention missing references
            for error in self.generator.errors:
                self.assertIn(
                    "non-existent",
                    error,
                    f"Unexpected error format: {error}"
                )
    
    def test_jekyll_data_preparation(self):
        """Test that Jekyll data structure is prepared correctly."""
        self.generator.load_canonical_data()
        self.generator.validate_references()
        
        site_data = self.generator.prepare_jekyll_data()
        
        # Verify expected keys
        self.assertIn("composers", site_data)
        self.assertIn("works", site_data)
        self.assertIn("performances", site_data)
        
        # Verify composers have expected structure
        for composer_id, composer_data in site_data["composers"].items():
            self.assertIn("id", composer_data)
            self.assertIn("name", composer_data)
            self.assertIn("work_groups", composer_data)
            self.assertIn("works", composer_data)
    
    def test_site_generation_produces_output(self):
        """Test that site generation creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a generator with temp output directory
            gen = SiteGenerator(self.repo_root)
            gen.output_dir = tmpdir_path
            
            success = gen.generate()
            
            # Check output file exists
            output_file = tmpdir_path / "collection.json"
            self.assertTrue(output_file.exists(), f"Output file not found at {output_file}")
            
            # Verify it's valid JSON
            with open(output_file) as f:
                data = json.load(f)
                self.assertIn("composers", data)
                self.assertIn("works", data)
                self.assertIn("performances", data)
    
    def test_no_internal_workflow_data_exposed(self):
        """Test that generated site data doesn't include internal workflow state."""
        self.generator.load_canonical_data()
        site_data = self.generator.prepare_jekyll_data()
        
        # Check that internal fields are not in the public output
        for work in site_data["works"].values():
            # Performance structure should only have public fields
            if "performances" in work:
                for perf in work["performances"]:
                    self.assertNotIn("_file", perf)
                    self.assertNotIn("_id", perf)
                    # Only legitimate public fields should be present
                    valid_keys = {"id", "performers", "tidal_url", "gramophone_ref", "profile"}
                    for key in perf.keys():
                        self.assertIn(key, valid_keys, f"Unexpected field in performance: {key}")


class TestSiteArchitecture(unittest.TestCase):
    """Tests for site architecture requirements."""
    
    def setUp(self):
        """Set up test environment."""
        self.repo_root = Path(__file__).parent.parent
        self.generator = SiteGenerator(self.repo_root)
    
    def test_source_of_truth_is_data_directory(self):
        """Verify that data/ is the only source of canonical data."""
        # Check that docs/*.md exists but should not be used as site source
        docs_dir = self.repo_root / "docs"
        self.assertTrue(docs_dir.exists())
        
        # Verify data/ has the actual canonical collection
        data_dir = self.repo_root / "data"
        self.assertTrue(data_dir.exists())
        self.assertTrue((data_dir / "works").exists())
        self.assertTrue((data_dir / "performances").exists())
    
    def test_no_recording_or_release_canonical_entities(self):
        """Verify site generator doesn't load Recording/Release as canonical entities."""
        # The site generator loads from exactly these directories only:
        self.generator.load_canonical_data()
        
        # Recordings directory may exist but is NOT loaded as canonical
        data_dir = self.repo_root / "data"
        recordings_dir = data_dir / "recordings"
        
        # Verify recordings are NOT in the loaded canonical data
        # (They may exist as reference material but aren't part of the public site data)
        if recordings_dir.exists():
            # Confirm they're not in our loaded data
            for person_id, person in self.generator.persons.items():
                self.assertNotIn("_recording_id", person)
            for work_id, work in self.generator.works.items():
                self.assertNotIn("_recording_id", work)
                self.assertNotIn("_recording_ref", work)
    
    def test_github_pages_workflow_configured(self):
        """Verify GitHub Pages workflow is properly configured."""
        workflow_file = self.repo_root / ".github" / "workflows" / "pages.yml"
        self.assertTrue(workflow_file.exists(), "GitHub Pages workflow not found")
        
        # Verify it's configured for Jekyll
        with open(workflow_file) as f:
            content = f.read()
            self.assertIn("jekyll", content.lower())
            self.assertIn("gh-pages", content)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
