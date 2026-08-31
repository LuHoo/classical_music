#!/usr/bin/env python3
"""
Generate static site from canonical collection data.

Loads YAML from data/ and prepares it for Jekyll site generation.
Validates canonical references and creates site data structure.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

class SiteGenerator:
    """Generate Jekyll site data from canonical YAML."""
    
    def __init__(self, repo_root: Path = None):
        """Initialize site generator.
        
        Args:
            repo_root: Repository root path. Defaults to current directory parent.
        """
        if repo_root is None:
            repo_root = Path.cwd()
        
        self.repo_root = repo_root
        self.data_dir = repo_root / "data"
        self.output_dir = repo_root / "_data_generated"
        
        # Load canonical data
        self.persons: Dict[str, Any] = {}
        self.work_groups: Dict[str, Any] = {}
        self.works: Dict[str, Any] = {}
        self.performances: Dict[str, Any] = {}
        
        # Validation state
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def load_all_yaml(self, directory: Path, entity_type: str) -> Dict[str, Any]:
        """Load all YAML files from a directory.
        
        Args:
            directory: Directory containing YAML files
            entity_type: Type of entity (for error messages)
            
        Returns:
            Dict mapping file stems to parsed YAML
        """
        entities = {}
        
        if not directory.exists():
            self.errors.append(f"Directory not found: {directory}")
            return entities
        
        for yaml_file in sorted(directory.glob("*.yaml")):
            entity_id = yaml_file.stem
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    if data is None:
                        self.warnings.append(f"Empty YAML: {yaml_file}")
                        continue
                    entities[entity_id] = {
                        **data,
                        "_file": str(yaml_file.relative_to(self.repo_root)),
                        "_id": entity_id
                    }
            except Exception as e:
                self.errors.append(f"Error loading {yaml_file}: {e}")
        
        return entities
    
    def load_canonical_data(self) -> bool:
        """Load all canonical data from data/ directory.
        
        Returns:
            True if successful, False if errors occurred
        """
        print("Loading canonical data...")
        
        self.persons = self.load_all_yaml(self.data_dir / "persons", "Person")
        self.work_groups = self.load_all_yaml(self.data_dir / "work-groups", "WorkGroup")
        self.works = self.load_all_yaml(self.data_dir / "works", "Work")
        self.performances = self.load_all_yaml(self.data_dir / "performances", "Performance")
        
        print(f"  Persons: {len(self.persons)}")
        print(f"  Work Groups: {len(self.work_groups)}")
        print(f"  Works: {len(self.works)}")
        print(f"  Performances: {len(self.performances)}")
        
        return len(self.errors) == 0
    
    def validate_references(self) -> bool:
        """Validate that all canonical references are intact.
        
        Returns:
            True if all references valid, False otherwise
        """
        print("\nValidating canonical references...")
        
        # Validate Work references
        for work_id, work in self.works.items():
            work_group_id = work.get("work_group_id")
            if not work_group_id:
                self.errors.append(f"Work {work_id} missing work_group_id reference")
            elif work_group_id not in self.work_groups:
                self.errors.append(f"Work {work_id} references non-existent work_group: {work_group_id}")
            
            composer_id = work.get("composer_id")
            if not composer_id:
                self.errors.append(f"Work {work_id} missing composer_id reference")
            elif composer_id not in self.persons:
                self.errors.append(f"Work {work_id} references non-existent composer: {composer_id}")
        
        # Validate Performance references
        for perf_id, perf in self.performances.items():
            work_id = perf.get("work_id")
            if not work_id:
                self.errors.append(f"Performance {perf_id} missing work_id reference")
            elif work_id not in self.works:
                self.errors.append(f"Performance {perf_id} references non-existent work: {work_id}")
        
        # Validate Work Group references
        for wg_id, wg in self.work_groups.items():
            composer_id = wg.get("composer_id")
            if not composer_id:
                self.errors.append(f"Work Group {wg_id} missing composer_id reference")
            elif composer_id not in self.persons:
                self.errors.append(f"Work Group {wg_id} references non-existent composer: {composer_id}")
        
        if self.errors:
            print(f"  ❌ {len(self.errors)} validation errors")
            return False
        
        print(f"  ✅ All references valid")
        return True
    
    def prepare_jekyll_data(self) -> Dict[str, Any]:
        """Prepare site data for Jekyll templates.
        
        Returns:
            Dict with site structure ready for Jekyll
        """
        print("\nPreparing Jekyll data...")
        
        # Build composer index
        composer_index = {}
        for person_id, person in self.persons.items():
            composer_index[person_id] = {
                "id": person_id,
                "name": person.get("name"),
                "work_groups": [],
                "works": [],
                "performances": 0
            }
        
        # Add work groups to composers
        for wg_id, wg in self.work_groups.items():
            composer_id = wg.get("composer_id")
            if composer_id in composer_index:
                composer_index[composer_id]["work_groups"].append({
                    "id": wg_id,
                    "title": wg.get("title"),
                    "works": []
                })
        
        # Add works to work groups
        work_index = {}
        for work_id, work in self.works.items():
            work_index[work_id] = work
            wg_id = work.get("work_group_id")
            composer_id = work.get("composer_id")
            
            if composer_id in composer_index:
                # Add to work_groups
                for wg in composer_index[composer_id]["work_groups"]:
                    if wg["id"] == wg_id:
                        wg["works"].append({
                            "id": work_id,
                            "title": work.get("title"),
                            "gem": work.get("gem", False)
                        })
                
                # Also track in composer index
                composer_index[composer_id]["works"].append({
                    "id": work_id,
                    "title": work.get("title"),
                    "gem": work.get("gem", False)
                })
        
        # Add performances to works
        performance_index = {}
        for perf_id, perf in self.performances.items():
            performance_index[perf_id] = perf
            work_id = perf.get("work_id")
            
            if work_id in work_index:
                if "performances" not in work_index[work_id]:
                    work_index[work_id]["performances"] = []
                
                work_index[work_id]["performances"].append({
                    "id": perf_id,
                    "performers": perf.get("performers", []),
                    "tidal_url": perf.get("tidal_url"),
                    "gramophone_ref": perf.get("gramophone_ref"),
                    "profile": perf.get("performance_profile")
                })
        
        return {
            "composers": composer_index,
            "works": work_index,
            "performances": performance_index,
            "generated_at": str(Path.cwd())
        }
    
    def generate(self) -> bool:
        """Run full site generation pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        print("\n" + "="*60)
        print("CLASSICAL MUSIC SITE GENERATOR")
        print("="*60)
        
        # Load data
        if not self.load_canonical_data():
            self._print_errors()
            return False
        
        # Validate references (but continue with site generation - curators fix data issues)
        self.validate_references()
        
        # Prepare for Jekyll (works even with validation warnings)
        site_data = self.prepare_jekyll_data()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write site data as JSON for Jekyll
        output_file = self.output_dir / "collection.json"
        with open(output_file, "w") as f:
            json.dump(site_data, f, indent=2)
        
        # Try to show relative path, fall back to absolute
        try:
            relative_path = output_file.relative_to(self.repo_root)
            print(f"\n✅ Site data written to {relative_path}")
        except ValueError:
            print(f"\n✅ Site data written to {output_file}")
        
        # Generate individual page files
        self.generate_composer_pages()
        self.generate_work_pages()
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")
        
        if self.errors:
            print(f"\n⚠️  Reference validation issues ({len(self.errors)}):")
            print("     (These require curator investigation but did not block site generation)")
            for e in self.errors[:3]:  # Show first 3
                print(f"  - {e}")
            if len(self.errors) > 3:
                print(f"  ... and {len(self.errors)-3} more")
        
        return True
    
    def _print_errors(self):
        """Print all accumulated errors."""
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"  - {e}")
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")
    
    def generate_composer_pages(self):
        """Generate individual composer pages."""
        print("\nGenerating composer pages...")
        composers_dir = self.repo_root / "_pages" / "composers"
        composers_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for composer_id, composer in self.persons.items():
            page_content = f"""---
layout: composer
title: {composer.get('name', 'Unknown')}
permalink: /composers/{composer_id}/
composer_id: {composer_id}
---
"""
            
            page_file = composers_dir / f"{composer_id}.md"
            with open(page_file, "w") as f:
                f.write(page_content)
            
            count += 1
        
        print(f"  Created {count} composer pages")
        return count
    
    def generate_work_pages(self):
        """Generate individual work pages."""
        print("Generating work pages...")
        works_dir = self.repo_root / "_pages" / "works"
        works_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for work_id, work in self.works.items():
            work_title = work.get("title", "Unknown")
            page_content = f"""---
layout: work
title: {work_title}
permalink: /works/{work_id}/
work_id: {work_id}
---
"""
            
            page_file = works_dir / f"{work_id}.md"
            with open(page_file, "w") as f:
                f.write(page_content)
            
            count += 1
        
        print(f"  Created {count} work pages")
        return count


def main():
    """Main entry point."""
    generator = SiteGenerator()
    success = generator.generate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
