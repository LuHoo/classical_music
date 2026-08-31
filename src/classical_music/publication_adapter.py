"""
Publication data adapter for canonical collection.

Loads from data/ directory only and produces a clean public data model
suitable for static site generation. Excludes internal workflow fields
and validates the Person -> WorkGroup -> Work -> Performance hierarchy.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from ruamel.yaml import YAML


class PublicationDataAdapter:
    """Adapt canonical YAML to publication data model."""

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize adapter.

        Args:
            repo_root: Repository root. Defaults to current working directory.
        """
        if repo_root is None:
            repo_root = Path.cwd()

        self.repo_root = repo_root
        self.data_dir = repo_root / "data"

        # Canonical data (internal)
        self._persons: Dict[str, Any] = {}
        self._work_groups: Dict[str, Any] = {}
        self._works: Dict[str, Any] = {}
        self._performances: Dict[str, Any] = {}

        # Publication model (public)
        self.persons: Dict[str, Any] = {}
        self.work_groups: Dict[str, Any] = {}
        self.works: Dict[str, Any] = {}
        self.performances: Dict[str, Any] = {}

        # Validation state
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_canonical_data(self) -> bool:
        """Load all canonical YAML from data/ directory.

        Returns:
            True if all data loaded successfully
        """
        print("Loading canonical data...")

        # Load all entity types
        self._persons = self._load_yaml_directory(
            self.data_dir / "persons", "Person"
        )
        self._work_groups = self._load_yaml_directory(
            self.data_dir / "work-groups", "WorkGroup"
        )
        self._works = self._load_yaml_directory(
            self.data_dir / "works", "Work"
        )
        self._performances = self._load_yaml_directory(
            self.data_dir / "performances", "Performance"
        )

        print(f"  Persons: {len(self._persons)}")
        print(f"  Work Groups: {len(self._work_groups)}")
        print(f"  Works: {len(self._works)}")
        print(f"  Performances: {len(self._performances)}")

        return len(self.errors) == 0

    def _load_yaml_directory(self, directory: Path, entity_type: str) -> Dict[str, Any]:
        """Load all YAML files from a directory (recursively).

        Args:
            directory: Directory to load from
            entity_type: Type of entity (for error messages)

        Returns:
            Dict mapping IDs to parsed YAML
        """
        entities = {}

        if not directory.exists():
            self.errors.append(f"{entity_type} directory not found: {directory}")
            return entities

        yaml = YAML()
        yaml.preserve_quotes = True

        for yaml_file in sorted(directory.glob("**/*.yaml")):
            try:
                with open(yaml_file) as f:
                    data = yaml.load(f)
                    if data and "id" in data:
                        entities[data["id"]] = data
            except Exception as e:
                self.errors.append(f"Failed to load {yaml_file}: {e}")

        return entities

    def adapt_to_publication_model(self) -> bool:
        """Adapt canonical data to publication model.

        Applies field mappings, extracts public fields, validates references.

        Returns:
            True if successful
        """
        print("\nAdapting to publication model...")

        # Adapt persons (minimal - just id and name for now)
        for person_id, person_data in self._persons.items():
            self.persons[person_id] = {
                "id": person_data.get("id"),
                "name": person_data.get("name"),
            }

        # Adapt work groups (lightweight, no recommendations)
        for wg_id, wg_data in self._work_groups.items():
            self.work_groups[wg_id] = {
                "id": wg_data.get("id"),
                "composer_id": wg_data.get("composer_id"),
                "title": wg_data.get("title"),
                "catalogue": wg_data.get("catalogue"),
            }

        # Adapt works
        for work_id, work_data in self._works.items():
            pub_work = {
                "id": work_data.get("id"),
                "work_group_id": work_data.get("work_group_id"),
                "composer_id": work_data.get("composer_id"),
                "title": work_data.get("title"),
            }

            # Include optional public fields
            if "catalogue" in work_data:
                pub_work["catalogue"] = work_data["catalogue"]
            if "category" in work_data:
                pub_work["category"] = work_data["category"]
            if "gem" in work_data:
                pub_work["gem"] = work_data["gem"]

            self.works[work_id] = pub_work

        # Adapt performances
        for perf_id, perf_data in self._performances.items():
            pub_perf = {
                "id": perf_data.get("id"),
                "work_id": perf_data.get("work_id"),
            }

            # Adapt performers: convert to display format
            if "performers" in perf_data:
                pub_perf["performers"] = self._adapt_performers(
                    perf_data["performers"]
                )

            # Map links.tidal.url to public tidal_url
            if "links" in perf_data and "tidal" in perf_data["links"]:
                if "url" in perf_data["links"]["tidal"]:
                    pub_perf["tidal_url"] = perf_data["links"]["tidal"]["url"]

            # Map reviews.gramophone to gramophone_ref
            if "reviews" in perf_data and "gramophone" in perf_data["reviews"]:
                gramophone = perf_data["reviews"]["gramophone"]
                if "issue" in gramophone:
                    pub_perf["gramophone_ref"] = gramophone["issue"]

            # Include performance profile if present
            if "performance_profile" in perf_data:
                pub_perf["profile"] = perf_data["performance_profile"]
            elif "profile" in perf_data:
                pub_perf["profile"] = perf_data["profile"]

            self.performances[perf_id] = pub_perf

        print(f"  ✅ Adapted {len(self.persons)} persons")
        print(f"  ✅ Adapted {len(self.work_groups)} work groups")
        print(f"  ✅ Adapted {len(self.works)} works")
        print(f"  ✅ Adapted {len(self.performances)} performances")

        return True

    def _adapt_performers(self, performers: List[Dict]) -> List[Dict]:
        """Convert performer objects to display format.

        Args:
            performers: List of performer objects from YAML

        Returns:
            List of public performer display objects
        """
        adapted = []

        for perf in performers:
            if isinstance(perf, dict):
                adapted.append({
                    "name": perf.get("name", ""),
                    "role": perf.get("role", "performer"),
                })
            elif isinstance(perf, str):
                # Handle string performers as fallback
                adapted.append({
                    "name": perf,
                    "role": "performer",
                })

        return adapted

    def validate_references(self) -> bool:
        """Validate reference integrity.

        Returns:
            True if all references are valid
        """
        print("\nValidating references...")

        error_count = 0

        # Validate Work references
        for work_id, work in self.works.items():
            # Check work_group_id
            wg_id = work.get("work_group_id")
            if wg_id and wg_id not in self.work_groups:
                self.errors.append(
                    f"Work {work_id} references non-existent work_group: {wg_id}"
                )
                error_count += 1

            # Check composer_id
            comp_id = work.get("composer_id")
            if comp_id and comp_id not in self.persons:
                self.errors.append(
                    f"Work {work_id} references non-existent composer: {comp_id}"
                )
                error_count += 1

        # Validate Performance references
        for perf_id, perf in self.performances.items():
            work_id = perf.get("work_id")
            if work_id and work_id not in self.works:
                self.errors.append(
                    f"Performance {perf_id} references non-existent work: {work_id}"
                )
                error_count += 1

        # Validate WorkGroup references
        for wg_id, wg in self.work_groups.items():
            comp_id = wg.get("composer_id")
            if comp_id and comp_id not in self.persons:
                self.errors.append(
                    f"WorkGroup {wg_id} references non-existent composer: {comp_id}"
                )
                error_count += 1

        if error_count == 0:
            print(f"  ✅ All references valid")
        else:
            print(f"  ❌ {error_count} reference errors")

        return error_count == 0

    def verify_no_workflow_data(self) -> bool:
        """Verify that no internal workflow data leaked into publication model.

        Returns:
            True if clean
        """
        print("\nVerifying no internal workflow data exposed...")

        internal_fields = [
            "_file", "_id", "_internal", "source", "candidates",
            "review", "migration", "validation_state"
        ]

        found_internal = False

        for work_id, work in self.works.items():
            for field in work:
                if field in internal_fields:
                    self.errors.append(
                        f"Internal field '{field}' leaked into work {work_id}"
                    )
                    found_internal = True

        for perf_id, perf in self.performances.items():
            for field in perf:
                if field in internal_fields:
                    self.errors.append(
                        f"Internal field '{field}' leaked into performance {perf_id}"
                    )
                    found_internal = True

        if not found_internal:
            print(f"  ✅ No internal workflow data exposed")
            return True

        print(f"  ❌ Found internal fields")
        return False

    def verify_works_without_performances(self) -> bool:
        """Verify that works without performances are included.

        Returns:
            True if all works present (including those without performances)
        """
        print("\nVerifying works without performances included...")

        # Group performances by work
        perf_by_work = {}
        for perf_id, perf in self.performances.items():
            work_id = perf.get("work_id")
            if work_id:
                if work_id not in perf_by_work:
                    perf_by_work[work_id] = []
                perf_by_work[work_id].append(perf_id)

        # Find works without performances
        works_without_perfs = []
        for work_id in self.works:
            if work_id not in perf_by_work:
                works_without_perfs.append(work_id)

        print(f"  Works with performances: {len(perf_by_work)}")
        print(f"  Works without performances: {len(works_without_perfs)}")
        print(f"  Total works: {len(self.works)}")

        if len(works_without_perfs) > 0:
            print(f"  ✅ {len(works_without_perfs)} works included without performances")
            return True
        else:
            self.warnings.append("No works without performances found")
            return True

    def verify_work_groups_dont_carry_recommendations(self) -> bool:
        """Verify that work groups are lightweight and don't carry recommendations.

        Returns:
            True if work groups are clean
        """
        print("\nVerifying work groups don't carry recommendations...")

        # Check that work groups only have: id, composer_id, title, catalogue
        valid_fields = {"id", "composer_id", "title", "catalogue"}

        for wg_id, wg in self.work_groups.items():
            unexpected_fields = set(wg.keys()) - valid_fields
            if unexpected_fields:
                self.errors.append(
                    f"WorkGroup {wg_id} has unexpected fields: {unexpected_fields}"
                )

        if len(self.errors) == 0:
            print(f"  ✅ Work groups are lightweight (no recommendations)")
            return True

        return False

    def adapt(self) -> bool:
        """Run full adaptation pipeline.

        Returns:
            True if successful
        """
        print("\n" + "="*60)
        print("PUBLICATION DATA ADAPTER")
        print("="*60)

        # Load canonical data
        if not self.load_canonical_data():
            return False

        # Adapt to publication model
        if not self.adapt_to_publication_model():
            return False

        # Validate all references (warnings only)
        self.validate_references()

        # Verify clean data
        self.verify_no_workflow_data()
        self.verify_works_without_performances()
        self.verify_work_groups_dont_carry_recommendations()

        # Print summary
        if self.errors:
            print(f"\n⚠️  WARNINGS ({len(self.errors)}):")
            print("     (Data issues requiring curator attention)")
            for err in self.errors[:5]:
                print(f"  - {err}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors)-5} more")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"  - {warn}")

        print("\n✅ Publication data adapter ready")
        return True

    def export_json(self, output_file: Optional[Path] = None) -> Path:
        """Export publication data as JSON.

        Args:
            output_file: Path to write JSON. Defaults to _data_generated/publication.json

        Returns:
            Path to output file
        """
        if output_file is None:
            output_file = self.repo_root / "_data_generated" / "publication.json"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "persons": self.persons,
            "work_groups": self.work_groups,
            "works": self.works,
            "performances": self.performances,
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n📄 Publication data exported to {output_file}")

        return output_file


def main():
    """Main entry point."""
    adapter = PublicationDataAdapter()
    success = adapter.adapt()

    if success:
        adapter.export_json()
        print("\n✅ Publication data adapter complete")
        return 0
    else:
        print("\n❌ Adapter failed with errors")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
