"""Regression tests for the shared raw catalog snapshot (issue #306).

These tests protect the guarantees that the snapshot must not weaken:
malformed YAML, duplicate mapping keys, duplicate canonical identifiers and
missing references stay detectable, consumers cannot mutate shared records,
and a second invocation in the same process observes source changes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from classical_music.catalog_snapshot import (
    CatalogSnapshot,
    FrozenDict,
    FrozenList,
    freeze,
)
from classical_music.publication_adapter import PublicationDataAdapter
from classical_music.publication_site import PublicationSiteGenerator
from classical_music.publication_validator import PublicationValidator


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        YAML().dump(data, handle)


def _seed_catalog(repo: Path) -> None:
    """Create a small but complete valid catalog."""
    for name in ("persons", "work-groups", "works", "performances"):
        (repo / "data" / name).mkdir(parents=True, exist_ok=True)

    _write_yaml(repo / "data" / "persons" / "bach.yaml", {"id": "bach", "name": "J. S. Bach"})
    _write_yaml(
        repo / "data" / "work-groups" / "bwv-1046.yaml",
        {"id": "bwv-1046", "composer_id": "bach", "title": "Brandenburg Concerto No. 1"},
    )
    _write_yaml(
        repo / "data" / "works" / "bwv-1046-work.yaml",
        {
            "id": "bwv-1046-work",
            "work_group_id": "bwv-1046",
            "composer_id": "bach",
            "title": "Brandenburg Concerto No. 1",
        },
    )
    _write_yaml(
        repo / "data" / "performances" / "perf-1.yaml",
        {
            "id": "perf-1",
            "work_id": "bwv-1046-work",
            "performers": [{"name": "Freiburger Barockorchester", "role": "ensemble"}],
            "links": {"tidal": {"url": "https://tidal.com/browse/album/1"}},
        },
    )


@pytest.fixture
def catalog(tmp_path: Path) -> Path:
    """A valid temporary catalog; never the real repository data."""
    _seed_catalog(tmp_path)
    return tmp_path


def _validate(repo: Path, capsys=None):
    result = PublicationValidator(repo).validate()
    if capsys is not None:
        capsys.readouterr()
    return result


# ---------------------------------------------------------------------------
# Snapshot construction and immutability
# ---------------------------------------------------------------------------


class TestSnapshotStructure:
    def test_snapshot_keeps_source_paths_and_ids(self, catalog: Path):
        snapshot = CatalogSnapshot.load(catalog)

        works = snapshot.records_for("Work")
        assert [record.path for record in works] == [
            catalog / "data" / "works" / "bwv-1046-work.yaml"
        ]
        assert snapshot.ids("Work") == frozenset({"bwv-1046-work"})
        assert snapshot.ids("Person") == frozenset({"bach"})
        assert works[0].error is None

    def test_missing_directory_is_reported_not_silently_skipped(self, tmp_path: Path):
        (tmp_path / "data").mkdir()
        snapshot = CatalogSnapshot.load(tmp_path)

        assert snapshot.missing_directory("Person") == tmp_path / "data" / "persons"
        assert snapshot.records_for("Person") == ()

    def test_every_file_is_parsed_exactly_once(self, catalog: Path, monkeypatch):
        parsed: list[str] = []
        original = YAML.load

        def counting_load(self, stream, *args, **kwargs):
            parsed.append(str(getattr(stream, "name", stream)))
            return original(self, stream, *args, **kwargs)

        monkeypatch.setattr(YAML, "load", counting_load)
        CatalogSnapshot.load(catalog)

        assert len(parsed) == len(set(parsed)) == 4


class TestImmutability:
    def test_records_reject_mutation(self, catalog: Path):
        snapshot = CatalogSnapshot.load(catalog)
        record = next(iter(snapshot.mappings("Performance")))

        with pytest.raises(TypeError):
            record.mapping["work_id"] = "tampered"
        with pytest.raises(TypeError):
            record.mapping.update({"work_id": "tampered"})
        with pytest.raises(TypeError):
            del record.mapping["work_id"]

    def test_nested_structures_are_frozen(self, catalog: Path):
        snapshot = CatalogSnapshot.load(catalog)
        record = next(iter(snapshot.mappings("Performance")))

        performers = record.mapping["performers"]
        assert isinstance(performers, FrozenList)
        assert isinstance(performers[0], FrozenDict)
        with pytest.raises(TypeError):
            performers.append({"name": "intruder"})
        with pytest.raises(TypeError):
            performers[0]["name"] = "intruder"
        with pytest.raises(TypeError):
            record.mapping["links"]["tidal"]["url"] = "https://example.invalid"

    def test_frozen_containers_stay_comparable_and_serialisable(self):
        frozen = freeze({"a": [1, {"b": 2}], "c": None})

        assert frozen == {"a": [1, {"b": 2}], "c": None}
        assert json.loads(json.dumps(frozen)) == {"a": [1, {"b": 2}], "c": None}

    def test_one_consumer_cannot_mutate_what_another_consumer_reads(self, catalog: Path, capsys):
        snapshot = CatalogSnapshot.load(catalog)

        first = PublicationDataAdapter(catalog, snapshot=snapshot)
        second = PublicationDataAdapter(catalog, snapshot=snapshot)
        assert first.load_canonical_data()
        assert second.load_canonical_data()
        capsys.readouterr()

        shared = first._works["bwv-1046-work"]
        with pytest.raises(TypeError):
            shared["title"] = "Tampered"

        assert second._works["bwv-1046-work"]["title"] == "Brandenburg Concerto No. 1"

    def test_adapter_output_does_not_alias_mutable_snapshot_state(self, catalog: Path, capsys):
        snapshot = CatalogSnapshot.load(catalog)
        adapter = PublicationDataAdapter(catalog, snapshot=snapshot)
        assert adapter.adapt()
        capsys.readouterr()

        # The publication model is freshly built and may be modified, but the
        # nested values it borrows from the snapshot stay read-only.
        adapter.works["bwv-1046-work"]["title"] = "Local edit"
        assert snapshot.ids("Work") == frozenset({"bwv-1046-work"})
        record = next(iter(snapshot.mappings("Work")))
        assert record.mapping["title"] == "Brandenburg Concerto No. 1"


# ---------------------------------------------------------------------------
# Preserved validation guarantees
# ---------------------------------------------------------------------------


class TestPreservedGuarantees:
    def test_valid_catalog_passes(self, catalog: Path, capsys):
        result = _validate(catalog, capsys)
        assert result.passed, [error.message for error in result.errors]

    def test_malformed_yaml_is_not_concealed(self, catalog: Path, capsys):
        (catalog / "data" / "works" / "broken.yaml").write_text("id: broken\n  bad: [1, 2\n")

        snapshot = CatalogSnapshot.load(catalog)
        broken = [record for record in snapshot.records_for("Work") if record.path.name == "broken.yaml"]
        assert len(broken) == 1
        assert broken[0].error is not None
        assert broken[0].mapping is None

        result = _validate(catalog, capsys)
        assert not result.passed
        assert any("broken.yaml" in error.message for error in result.errors)

    def test_duplicate_mapping_keys_are_rejected(self, catalog: Path, capsys):
        (catalog / "data" / "works" / "dup-keys.yaml").write_text(
            "id: dup-keys\n"
            "work_group_id: bwv-1046\n"
            "composer_id: bach\n"
            "title: First\n"
            "title: Second\n"
        )

        snapshot = CatalogSnapshot.load(catalog)
        record = next(r for r in snapshot.records_for("Work") if r.path.name == "dup-keys.yaml")
        assert record.error is not None
        assert "duplicate key" in record.error.lower()

        result = _validate(catalog, capsys)
        assert not result.passed
        assert any("dup-keys.yaml" in error.message for error in result.errors)

    def test_duplicate_canonical_ids_remain_visible_across_files(self, catalog: Path):
        _write_yaml(
            catalog / "data" / "works" / "duplicate-id.yaml",
            {
                "id": "bwv-1046-work",
                "work_group_id": "bwv-1046",
                "composer_id": "bach",
                "title": "Duplicate identifier",
            },
        )

        snapshot = CatalogSnapshot.load(catalog)
        ids = [record.record_id for record in snapshot.mappings("Work")]

        # The publication model indexes by id and would hide the collision;
        # the raw snapshot keeps both source records.
        assert ids.count("bwv-1046-work") == 2
        assert len(snapshot.ids("Work")) == 1

    def test_missing_references_are_reported(self, catalog: Path, capsys):
        _write_yaml(
            catalog / "data" / "performances" / "perf-2.yaml",
            {
                "id": "perf-2",
                "work_id": "does-not-exist",
                "performers": [{"name": "Test Ensemble"}],
            },
        )

        result = _validate(catalog, capsys)
        assert not result.passed
        assert any(error.rule_id == "REF-004" for error in result.errors)

    def test_each_reference_rule_still_runs(self, catalog: Path, capsys):
        _write_yaml(
            catalog / "data" / "work-groups" / "orphan-group.yaml",
            {"id": "orphan-group", "composer_id": "unknown-person", "title": "Orphan"},
        )
        _write_yaml(
            catalog / "data" / "works" / "orphan-work.yaml",
            {"id": "orphan-work", "work_group_id": "unknown-group", "composer_id": "unknown-person", "title": "Orphan"},
        )
        _write_yaml(
            catalog / "data" / "performances" / "perf-wg.yaml",
            {"id": "perf-wg", "work_id": "bwv-1046", "performers": [{"name": "Ensemble"}]},
        )
        _write_yaml(
            catalog / "data" / "performances" / "perf-empty.yaml",
            {"id": "perf-empty", "work_id": "bwv-1046-work", "performers": []},
        )

        result = _validate(catalog, capsys)
        rules = {error.rule_id for error in result.errors}

        assert {"REF-001", "REF-002", "REF-003", "REF-004", "REF-005", "DOM-044"} <= rules

    def test_errors_keep_their_source_file(self, catalog: Path, capsys):
        _write_yaml(
            catalog / "data" / "works" / "orphan-work.yaml",
            {"id": "orphan-work", "work_group_id": "unknown-group", "composer_id": "bach", "title": "Orphan"},
        )

        result = _validate(catalog, capsys)
        error = next(error for error in result.errors if error.rule_id == "REF-003")

        assert Path(error.source_file) == catalog / "data" / "works" / "orphan-work.yaml"

    def test_no_source_file_is_silently_ignored(self, catalog: Path, capsys):
        # A nested work file must be discovered just like a top-level one.
        _write_yaml(
            catalog / "data" / "works" / "bach" / "nested-work.yaml",
            {"id": "nested-work", "work_group_id": "unknown-group", "composer_id": "bach", "title": "Nested"},
        )

        result = _validate(catalog, capsys)
        assert any(
            error.rule_id == "REF-003" and "nested-work.yaml" in error.source_file
            for error in result.errors
        )


# ---------------------------------------------------------------------------
# Snapshot lifetime
# ---------------------------------------------------------------------------


class TestSnapshotLifetime:
    def test_second_validation_observes_a_changed_file(self, catalog: Path, capsys):
        assert _validate(catalog, capsys).passed

        _write_yaml(
            catalog / "data" / "performances" / "perf-1.yaml",
            {
                "id": "perf-1",
                "work_id": "removed-work",
                "performers": [{"name": "Freiburger Barockorchester"}],
            },
        )

        second = _validate(catalog, capsys)
        assert not second.passed
        assert any(error.rule_id == "REF-004" for error in second.errors)

    def test_second_validation_observes_newly_malformed_yaml(self, catalog: Path, capsys):
        assert _validate(catalog, capsys).passed

        (catalog / "data" / "works" / "bwv-1046-work.yaml").write_text("id: x\n  bad: [1, 2\n")

        second = _validate(catalog, capsys)
        assert not second.passed

    def test_repeated_validation_on_the_same_validator_reloads(self, catalog: Path, capsys):
        validator = PublicationValidator(catalog)
        assert validator.validate().passed
        capsys.readouterr()

        (catalog / "data" / "persons" / "bach.yaml").unlink()

        assert not validator.validate().passed
        capsys.readouterr()

    def test_second_build_reflects_catalog_changes(self, catalog: Path, capsys):
        output = catalog / "publication"
        generator = PublicationSiteGenerator(catalog, output)

        generator.generate()
        capsys.readouterr()
        assert (output / "works" / "bwv-1046-work.md").exists()

        _write_yaml(
            catalog / "data" / "works" / "bwv-1047-work.yaml",
            {
                "id": "bwv-1047-work",
                "work_group_id": "bwv-1046",
                "composer_id": "bach",
                "title": "Brandenburg Concerto No. 2",
            },
        )

        generator.generate()
        capsys.readouterr()
        assert (output / "works" / "bwv-1047-work.md").exists()

    def test_build_fails_when_the_catalog_becomes_invalid_between_builds(self, catalog: Path, capsys):
        generator = PublicationSiteGenerator(catalog, catalog / "publication")
        generator.generate()
        capsys.readouterr()

        _write_yaml(
            catalog / "data" / "performances" / "perf-1.yaml",
            {"id": "perf-1", "work_id": "gone", "performers": [{"name": "Ensemble"}]},
        )

        with pytest.raises(RuntimeError, match="Publication validation failed"):
            generator.generate()
        capsys.readouterr()

    def test_injected_snapshot_is_released_after_use(self, catalog: Path, capsys):
        generator = PublicationSiteGenerator(catalog, catalog / "publication")
        generator.generate()
        capsys.readouterr()

        assert generator.adapter.snapshot is None


# ---------------------------------------------------------------------------
# Equivalence between shared and independent loading
# ---------------------------------------------------------------------------


class TestSharedLoadingEquivalence:
    def test_shared_snapshot_yields_the_same_publication_model(self, catalog: Path, capsys):
        independent = PublicationDataAdapter(catalog)
        assert independent.adapt()

        shared = PublicationDataAdapter(catalog, snapshot=CatalogSnapshot.load(catalog))
        assert shared.adapt()
        capsys.readouterr()

        assert independent.persons == shared.persons
        assert independent.work_groups == shared.work_groups
        assert independent.works == shared.works
        assert independent.performances == shared.performances
        assert independent.errors == shared.errors

    def test_shared_snapshot_yields_the_same_validation_result(self, catalog: Path, capsys):
        _write_yaml(
            catalog / "data" / "works" / "orphan-work.yaml",
            {"id": "orphan-work", "work_group_id": "unknown-group", "composer_id": "bach", "title": "Orphan"},
        )

        independent = PublicationValidator(catalog).validate()
        shared = PublicationValidator(catalog, snapshot=CatalogSnapshot.load(catalog)).validate()
        capsys.readouterr()

        def fingerprint(result):
            return (
                result.passed,
                sorted(
                    (error.rule_id, error.entity_id, error.field, error.message, error.source_file)
                    for error in result.errors
                ),
            )

        assert fingerprint(independent) == fingerprint(shared)

    def test_build_reuses_one_snapshot_for_validation_and_generation(self, catalog: Path, capsys, monkeypatch):
        import classical_music.publication_site as publication_site

        loads = []
        original = CatalogSnapshot.load

        def counting_load(repo_root, *args, **kwargs):
            loads.append(repo_root)
            return original(repo_root, *args, **kwargs)

        monkeypatch.setattr(publication_site.CatalogSnapshot, "load", staticmethod(counting_load))

        PublicationSiteGenerator(catalog, catalog / "publication").generate()
        capsys.readouterr()

        assert len(loads) == 1
