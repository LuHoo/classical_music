from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.error import YAMLError

from .models import ValidationFinding, ValidationReport
from . import rules


REQUIRED_FIELDS: dict[str, set[str]] = {
    "persons": {"id", "name"},
    "work-groups": {"id", "composer_id", "title"},
    "works": {"id", "work_group_id", "composer_id", "title"},
    "performances": {"id", "work_id", "performers"},
}

ALLOWED_FIELDS: dict[str, set[str]] = {
    "persons": {
        "id",
        "name",
        "sort_name",
        "roles",
        "display_names",
        "aliases",
        "external_ids",
        "notes",
        "source",
    },
    "work-groups": {
        "id",
        "composer_id",
        "title",
        "catalogue",
        "aliases",
        "description",
        "external_ids",
        "notes",
        "source",
    },
    "works": {
        "id",
        "work_group_id",
        "composer_id",
        "title",
        "version",
        "catalogue",
        "year",
        "date_text",
        "key",
        "instrumentation",
        "gem",
        "aliases",
        "relationships",
        "external_ids",
        "notes",
        "category",
        "source",
    },
    "performances": {
        "id",
        "work_id",
        "performers",
        "profile",
        "version_assignment",
        "year",
        "dates",
        "location",
        "release",
        "links",
        "reviews",
        "external_ids",
        "keep_looking",
        "notes",
        "source",
    },
}

CANDIDATE_KEYS = {
    "candidate_work",
    "review_reason",
    "status",
    "candidate_status",
    "source_file",
    "source_line",
    "evidence",
}

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GRAMOPHONE_ISSUE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass
class Record:
    entity_type: str
    file_path: Path
    data: dict[str, Any]
    display_file: str


class DataValidator:
    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root
        self.data_root = repository_root / "data"
        self.yaml = YAML(typ="safe")
        self.yaml.allow_duplicate_keys = False

    def run(self, identity_gate_ids: set[str] | None = None) -> ValidationReport:
        report = ValidationReport()
        records: list[Record] = []

        for entity_type in ("persons", "work-groups", "works", "performances"):
            entity_dir = self.data_root / entity_type
            if not entity_dir.exists():
                continue
            for file_path in sorted(entity_dir.rglob("*.yaml")):
                loaded = self._load_yaml(entity_type, file_path, report)
                if loaded is None:
                    continue
                records.extend(self._to_records(entity_type, file_path, loaded, report))

        self._validate_entity_shapes(records, report)
        self._validate_cross_references(records, report)
        self._validate_duplicates(records, report, identity_gate_ids or set())

        return report

    def _load_yaml(
        self, entity_type: str, file_path: Path, report: ValidationReport
    ) -> dict[str, Any] | None:
        relative = str(file_path.relative_to(self.repository_root))
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_SCH_YAML_SYNTAX,
                    severity="error",
                    file=relative,
                    message=f"File cannot be read: {exc}",
                    entity_type=entity_type,
                )
            )
            return None

        try:
            loaded = self.yaml.load(text)
        except DuplicateKeyError as exc:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_SCH_DUPLICATE_KEYS,
                    severity="error",
                    file=relative,
                    message=f"Duplicate YAML key: {exc}",
                    entity_type=entity_type,
                )
            )
            return None
        except YAMLError as exc:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_SCH_YAML_SYNTAX,
                    severity="error",
                    file=relative,
                    message=f"Invalid YAML syntax: {exc}",
                    entity_type=entity_type,
                )
            )
            return None

        if not isinstance(loaded, dict):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_SCH_REQUIRED_FIELDS,
                    severity="error",
                    file=relative,
                    message="Top-level YAML value must be a mapping.",
                    entity_type=entity_type,
                )
            )
            return None

        return loaded

    def _to_records(
        self,
        entity_type: str,
        file_path: Path,
        loaded: dict[str, Any],
        report: ValidationReport,
    ) -> list[Record]:
        container_keys = {
            "persons": ["persons"],
            "work-groups": ["work_groups", "work-groups"],
            "works": ["works"],
            "performances": ["performances"],
        }

        records: list[Record] = []
        for container_key in container_keys.get(entity_type, []):
            if container_key not in loaded:
                continue
            items = loaded.get(container_key)
            if isinstance(items, list):
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_CAN_WORKFLOW_NOT_CANONICAL,
                        severity="error",
                        file=str(file_path.relative_to(self.repository_root)),
                        message=(
                            f"Grouped '{container_key}' container is not canonical repository "
                            "data. Split records into one-file-per-entity under data/."
                        ),
                        entity_type=entity_type,
                    )
                )
                return []

        return [
            Record(
                entity_type=entity_type,
                file_path=file_path,
                data=loaded,
                display_file=str(file_path.relative_to(self.repository_root)),
            )
        ]

    def _validate_entity_shapes(
        self, records: list[Record], report: ValidationReport
    ) -> None:
        ids_by_entity: dict[str, dict[str, Record]] = defaultdict(dict)

        for record in records:
            file_rel = record.display_file
            data = record.data
            required = REQUIRED_FIELDS[record.entity_type]
            allowed = ALLOWED_FIELDS[record.entity_type]

            missing = [field for field in sorted(required) if not data.get(field)]
            if missing:
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_SCH_REQUIRED_FIELDS,
                        severity="error",
                        file=file_rel,
                        message=(
                            f"Missing required field(s): {', '.join(missing)}"
                        ),
                        entity_type=record.entity_type,
                        field=",".join(missing),
                    )
                )

            unknown = sorted(set(data.keys()) - allowed)
            for field_name in unknown:
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_SCH_UNKNOWN_FIELDS,
                        severity="warning",
                        file=file_rel,
                        message=(
                            f"Unknown field '{field_name}' for entity type "
                            f"{record.entity_type}."
                        ),
                        entity_type=record.entity_type,
                        field=field_name,
                    )
                )

            self._validate_candidate_fields(record, report)
            self._validate_id(record, ids_by_entity, report)
            self._validate_urls(record, report)
            self._validate_gramophone(record, report)
            self._validate_gem_rules(record, report)
            self._validate_recommendation_fields(record, report)
            self._validate_empty_optional_fields(record, report)
            self._validate_work_group_domain(record, report)
            self._validate_work_domain(record, report)

            if record.entity_type == "performances":
                self._validate_performers(record, report)
                self._validate_performance_work_link_shape(record, report)

    def _validate_candidate_fields(self, record: Record, report: ValidationReport) -> None:
        file_rel = record.display_file
        intersect = sorted(CANDIDATE_KEYS.intersection(record.data.keys()))
        for key_name in intersect:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_CAN_CANDIDATE_NOT_CANONICAL,
                    severity="error",
                    file=file_rel,
                    message=(
                        f"Candidate workflow field '{key_name}' is forbidden in "
                        "canonical data."
                    ),
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field=key_name,
                )
            )

        workflow_keys = {
            "candidate_searches",
            "listening_queue",
            "comparison_state",
            "duplicate_evidence",
        }
        for key_name in sorted(workflow_keys.intersection(record.data.keys())):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_CAN_WORKFLOW_NOT_CANONICAL,
                    severity="error",
                    file=file_rel,
                    message=(
                        f"Workflow field '{key_name}' must not be stored in canonical data."
                    ),
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field=key_name,
                )
            )

    def _validate_id(
        self,
        record: Record,
        ids_by_entity: dict[str, dict[str, Record]],
        report: ValidationReport,
    ) -> None:
        file_rel = record.display_file
        identifier = record.data.get("id")
        if not isinstance(identifier, str) or not identifier:
            return

        if not ID_PATTERN.match(identifier):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_IDN_SLUG,
                    severity="error",
                    file=file_rel,
                    message=(
                        "ID must use lowercase ASCII slug form "
                        "(letters, numbers, hyphen)."
                    ),
                    entity_type=record.entity_type,
                    entity_id=identifier,
                    field="id",
                )
            )

        seen = ids_by_entity[record.entity_type]
        if identifier in seen:
            original = seen[identifier].display_file
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_IDN_UNIQUE_ID,
                    severity="error",
                    file=file_rel,
                    message=(
                        f"Duplicate ID '{identifier}' already defined in {original}."
                    ),
                    entity_type=record.entity_type,
                    entity_id=identifier,
                    field="id",
                )
            )
        else:
            seen[identifier] = record

    def _validate_urls(self, record: Record, report: ValidationReport) -> None:
        file_rel = record.display_file

        def walk(node: Any, path_parts: list[str]) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(value, [*path_parts, str(key)])
                return
            if isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, [*path_parts, str(index)])
                return

            if not isinstance(node, str):
                return

            field_name = path_parts[-1] if path_parts else ""
            if field_name != "url":
                return

            parsed = urlparse(node)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_SCH_ABSOLUTE_URL,
                        severity="error",
                        file=file_rel,
                        message=f"Invalid absolute URL: {node}",
                        entity_type=record.entity_type,
                        entity_id=str(record.data.get("id", "")) or None,
                        field=".".join(path_parts),
                    )
                )
                return

            if "tidal.com" in parsed.netloc and record.entity_type != "performances":
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_EXT_TIDAL_ON_PERFORMANCE,
                        severity="error",
                        file=file_rel,
                        message="Tidal URLs are only allowed on Performance links.",
                        entity_type=record.entity_type,
                        entity_id=str(record.data.get("id", "")) or None,
                        field=".".join(path_parts),
                    )
                )

        walk(record.data, [])

    def _validate_gramophone(self, record: Record, report: ValidationReport) -> None:
        if record.entity_type != "performances":
            return

        issue = (
            record.data.get("reviews", {})
            .get("gramophone", {})
            .get("issue")
            if isinstance(record.data.get("reviews"), dict)
            else None
        )
        if issue is None:
            return

        file_rel = record.display_file
        if not isinstance(issue, str) or not GRAMOPHONE_ISSUE_PATTERN.match(issue):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_SCH_GRM_ISSUE,
                    severity="error",
                    file=file_rel,
                    message="Gramophone issue must use YYYY-MM format.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="reviews.gramophone.issue",
                )
            )

    def _validate_gem_rules(self, record: Record, report: ValidationReport) -> None:
        file_rel = record.display_file
        has_gem = "gem" in record.data

        if record.entity_type == "works":
            return

        if has_gem:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_REC_GEM_NOT_WG_OR_PERF,
                    severity="error",
                    file=file_rel,
                    message="gem is only allowed on Work entities.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="gem",
                )
            )

    def _validate_recommendation_fields(
        self, record: Record, report: ValidationReport
    ) -> None:
        file_rel = record.display_file

        if record.entity_type == "performances" and record.data.get("recommended") is True:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_REC_NO_RECOMMENDED_TRUE,
                    severity="warning",
                    file=file_rel,
                    message="recommended: true is redundant for canonical performances.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="recommended",
                )
            )

        if record.entity_type != "performances" and "profile" in record.data:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_REC_PROFILE_ON_PERFORMANCE,
                    severity="error",
                    file=file_rel,
                    message="profile is only allowed on Performance entities.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="profile",
                )
            )

    def _validate_performers(self, record: Record, report: ValidationReport) -> None:
        file_rel = record.display_file
        performers = record.data.get("performers")

        if not isinstance(performers, list) or len(performers) == 0:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_PERFORMER_REQUIRED,
                    severity="error",
                    file=file_rel,
                    message="Performance must have at least one performer entry.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="performers",
                )
            )
            return

        for idx, performer in enumerate(performers):
            if not isinstance(performer, dict):
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_DOM_PERFORMER_REQUIRED,
                        severity="error",
                        file=file_rel,
                        message=f"Performer index {idx} must be a mapping.",
                        entity_type=record.entity_type,
                        entity_id=str(record.data.get("id", "")) or None,
                        field=f"performers.{idx}",
                    )
                )
                continue

            if not performer.get("person_id") and not performer.get("name"):
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_DOM_PERFORMER_REQUIRED,
                        severity="error",
                        file=file_rel,
                        message=(
                            f"Performer index {idx} must include person_id "
                            "or name."
                        ),
                        entity_type=record.entity_type,
                        entity_id=str(record.data.get("id", "")) or None,
                        field=f"performers.{idx}",
                    )
                )

        keep_looking = record.data.get("keep_looking")
        if keep_looking is not None and not isinstance(keep_looking, bool):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_SCH_KEEP_LOOKING_BOOL,
                    severity="error",
                    file=file_rel,
                    message="keep_looking must be boolean when present.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="keep_looking",
                )
            )

    def _validate_performance_work_link_shape(
        self, record: Record, report: ValidationReport
    ) -> None:
        file_rel = record.display_file
        work_id = record.data.get("work_id")
        if isinstance(work_id, list):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_PERF_NO_MULTI_WORK,
                    severity="error",
                    file=file_rel,
                    message="Performance must not contain multiple work references.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="work_id",
                )
            )
        elif work_id is None:
            return
        elif not isinstance(work_id, str):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_PERF_SINGLE_WORK_ID,
                    severity="error",
                    file=file_rel,
                    message="Performance work_id must be a single string value.",
                    entity_type=record.entity_type,
                    entity_id=str(record.data.get("id", "")) or None,
                    field="work_id",
                )
            )

    def _validate_cross_references(
        self, records: list[Record], report: ValidationReport
    ) -> None:
        people = self._ids_for(records, "persons")
        work_groups = self._ids_for(records, "work-groups")
        works = self._ids_for(records, "works")

        for record in records:
            data = record.data
            file_rel = record.display_file
            entity_id = str(data.get("id", "")) or None

            if record.entity_type == "work-groups":
                composer_id = data.get("composer_id")
                if isinstance(composer_id, str) and composer_id not in people:
                    report.findings.append(
                        ValidationFinding(
                            rule_id=rules.RULE_REF_WG_COMPOSER,
                            severity="error",
                            file=file_rel,
                            message=(
                                "Work Group composer_id must reference existing Person."
                            ),
                            entity_type=record.entity_type,
                            entity_id=entity_id,
                            field="composer_id",
                        )
                    )

            if record.entity_type == "works":
                composer_id = data.get("composer_id")
                if isinstance(composer_id, str) and composer_id not in people:
                    report.findings.append(
                        ValidationFinding(
                            rule_id=rules.RULE_REF_WORK_COMPOSER,
                            severity="error",
                            file=file_rel,
                            message="Work composer_id must reference existing Person.",
                            entity_type=record.entity_type,
                            entity_id=entity_id,
                            field="composer_id",
                        )
                    )
                group_id = data.get("work_group_id")
                if isinstance(group_id, str) and group_id not in work_groups:
                    report.findings.append(
                        ValidationFinding(
                            rule_id=rules.RULE_REF_WORK_GROUP,
                            severity="error",
                            file=file_rel,
                            message=(
                                "Work work_group_id must reference existing Work Group."
                            ),
                            entity_type=record.entity_type,
                            entity_id=entity_id,
                            field="work_group_id",
                        )
                    )

                relationships = data.get("relationships")
                if isinstance(relationships, list):
                    for index, relationship in enumerate(relationships):
                        if not isinstance(relationship, dict):
                            continue
                        related_work = relationship.get("work_id")
                        if isinstance(related_work, str) and related_work not in works:
                            report.findings.append(
                                ValidationFinding(
                                    rule_id=rules.RULE_REF_WORK_RELATIONSHIP_WORK,
                                    severity="error",
                                    file=file_rel,
                                    message=(
                                        "Work relationships must reference existing Works."
                                    ),
                                    entity_type=record.entity_type,
                                    entity_id=entity_id,
                                    field=f"relationships.{index}.work_id",
                                )
                            )

            if record.entity_type == "performances":
                work_id = data.get("work_id")
                if isinstance(work_id, str):
                    if work_id in work_groups:
                        report.findings.append(
                            ValidationFinding(
                                rule_id=rules.RULE_REF_PERF_NOT_WORK_GROUP,
                                severity="error",
                                file=file_rel,
                                message=(
                                    "Performance must not reference a Work Group as work_id."
                                ),
                                entity_type=record.entity_type,
                                entity_id=entity_id,
                                field="work_id",
                            )
                        )
                    elif work_id not in works:
                        report.findings.append(
                            ValidationFinding(
                                rule_id=rules.RULE_REF_PERF_WORK,
                                severity="error",
                                file=file_rel,
                                message="Performance work_id must reference existing Work.",
                                entity_type=record.entity_type,
                                entity_id=entity_id,
                                field="work_id",
                            )
                        )

                performers = data.get("performers")
                if isinstance(performers, list):
                    for index, performer in enumerate(performers):
                        if not isinstance(performer, dict):
                            continue
                        person_id = performer.get("person_id")
                        if isinstance(person_id, str) and person_id not in people:
                            report.findings.append(
                                ValidationFinding(
                                    rule_id=rules.RULE_REF_PERFORMER_PERSON,
                                    severity="error",
                                    file=file_rel,
                                    message=(
                                        f"Performer person_id '{person_id}' does not exist in persons."
                                    ),
                                    entity_type=record.entity_type,
                                    entity_id=entity_id,
                                    field=f"performers.{index}.person_id",
                                )
                            )

    def _validate_duplicates(
        self,
        records: list[Record],
        report: ValidationReport,
        identity_gate_ids: set[str],
    ) -> None:
        work_groups = [record for record in records if record.entity_type == "work-groups"]
        works = [record for record in records if record.entity_type == "works"]
        performances = [record for record in records if record.entity_type == "performances"]

        # Same composer + title for work groups.
        seen_work_group_key: dict[tuple[str, str], Record] = {}
        for record in work_groups:
            composer = str(record.data.get("composer_id", "")).strip().lower()
            title = str(record.data.get("title", "")).strip().lower()
            key = (composer, title)
            if not composer or not title:
                continue
            if key in seen_work_group_key:
                self._add_duplicate_warning(
                    report,
                    rules.RULE_DUP_WORK_GROUP,
                    record,
                    "Potential duplicate Work Group (same composer and title).",
                    identity_gate_ids,
                    {record.data.get("id"), seen_work_group_key[key].data.get("id")},
                )
            else:
                seen_work_group_key[key] = record

        # Same composer + title for works.
        seen_work_key: dict[tuple[str, str], Record] = {}
        normalized_titles_by_composer: dict[str, list[tuple[str, Record]]] = defaultdict(list)
        for record in works:
            composer = str(record.data.get("composer_id", "")).strip().lower()
            title = str(record.data.get("title", "")).strip().lower()
            key = (composer, title)
            if not composer or not title:
                continue
            if key in seen_work_key:
                self._add_duplicate_warning(
                    report,
                    rules.RULE_DUP_WORK,
                    record,
                    "Potential duplicate Work (same composer and title).",
                    identity_gate_ids,
                    {record.data.get("id"), seen_work_key[key].data.get("id")},
                )
            else:
                seen_work_key[key] = record

            normalized = self._normalize_title(title)
            normalized_titles_by_composer[composer].append((normalized, record))

        # Similar work titles (heuristic).
        for composer, title_pairs in normalized_titles_by_composer.items():
            for index, (title_a, record_a) in enumerate(title_pairs):
                for title_b, record_b in title_pairs[index + 1 :]:
                    if title_a == title_b:
                        continue
                    similarity = self._jaccard_tokens(title_a, title_b)
                    if similarity >= 0.85:
                        self._add_duplicate_warning(
                            report,
                            rules.RULE_DUP_WORK,
                            record_b,
                            (
                                "Potential similar Work title under same composer "
                                f"(similarity={similarity:.2f})."
                            ),
                            identity_gate_ids,
                            {record_a.data.get("id"), record_b.data.get("id")},
                        )

        # Performance duplicate warning heuristic.
        seen_perf_key: dict[tuple[str, str], Record] = {}
        for record in performances:
            work_id = str(record.data.get("work_id", "")).strip().lower()
            performer_fingerprint = self._performer_fingerprint(record.data.get("performers"))
            if not work_id or not performer_fingerprint:
                continue
            key = (work_id, performer_fingerprint)
            if key in seen_perf_key:
                self._add_duplicate_warning(
                    report,
                    rules.RULE_DUP_PERFORMANCE,
                    record,
                    "Potential duplicate Performance (same work and performers).",
                    identity_gate_ids,
                    {record.data.get("id"), seen_perf_key[key].data.get("id")},
                )
            else:
                seen_perf_key[key] = record

    def _ids_for(self, records: list[Record], entity_type: str) -> set[str]:
        ids: set[str] = set()
        for record in records:
            if record.entity_type != entity_type:
                continue
            identifier = record.data.get("id")
            if isinstance(identifier, str):
                ids.add(identifier)
        return ids

    def _add_duplicate_warning(
        self,
        report: ValidationReport,
        rule_id: str,
        record: Record,
        message: str,
        identity_gate_ids: set[str],
        related_ids: set[Any],
    ) -> None:
        report.findings.append(
            ValidationFinding(
                rule_id=rule_id,
                severity="warning",
                file=record.display_file,
                message=message,
                entity_type=record.entity_type,
                entity_id=str(record.data.get("id", "")) or None,
                status=(
                    "action_required"
                    if identity_gate_ids.intersection(
                        {str(identifier) for identifier in related_ids if identifier}
                    )
                    else "background_suspicion"
                ),
            )
        )

    def _validate_empty_optional_fields(self, record: Record, report: ValidationReport) -> None:
        file_rel = record.display_file
        required = REQUIRED_FIELDS[record.entity_type]
        for field_name, value in record.data.items():
            if field_name in required:
                continue
            if value is None:
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_SCH_EMPTY_OPTIONAL,
                        severity="warning",
                        file=file_rel,
                        message=(
                            f"Optional field '{field_name}' is empty and should be omitted."
                        ),
                        entity_type=record.entity_type,
                        entity_id=str(record.data.get("id", "")) or None,
                        field=field_name,
                    )
                )
            elif isinstance(value, str) and value.strip() == "":
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_SCH_EMPTY_OPTIONAL,
                        severity="warning",
                        file=file_rel,
                        message=(
                            f"Optional field '{field_name}' is empty and should be omitted."
                        ),
                        entity_type=record.entity_type,
                        entity_id=str(record.data.get("id", "")) or None,
                        field=field_name,
                    )
                )
            elif isinstance(value, (list, dict)) and len(value) == 0:
                report.findings.append(
                    ValidationFinding(
                        rule_id=rules.RULE_SCH_EMPTY_OPTIONAL,
                        severity="warning",
                        file=file_rel,
                        message=(
                            f"Optional field '{field_name}' is empty and should be omitted."
                        ),
                        entity_type=record.entity_type,
                        entity_id=str(record.data.get("id", "")) or None,
                        field=field_name,
                    )
                )

    def _validate_work_group_domain(self, record: Record, report: ValidationReport) -> None:
        if record.entity_type != "work-groups":
            return

        file_rel = record.display_file
        entity_id = str(record.data.get("id", "")) or None

        if "work_id" in record.data or "performers" in record.data:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_WORK_GROUP_NON_PERFORMABLE,
                    severity="error",
                    file=file_rel,
                    message="Work Group must be non-performable.",
                    entity_type=record.entity_type,
                    entity_id=entity_id,
                )
            )

        if "performances" in record.data:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_WORK_GROUP_NO_DIRECT_PERFORMANCES,
                    severity="error",
                    file=file_rel,
                    message="Work Group must not have direct performances.",
                    entity_type=record.entity_type,
                    entity_id=entity_id,
                    field="performances",
                )
            )

        if "recommended" in record.data:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_WORK_GROUP_NO_RECOMMENDATION,
                    severity="error",
                    file=file_rel,
                    message="Work Group must not have recommendation status.",
                    entity_type=record.entity_type,
                    entity_id=entity_id,
                    field="recommended",
                )
            )

    def _validate_work_domain(self, record: Record, report: ValidationReport) -> None:
        if record.entity_type != "works":
            return

        file_rel = record.display_file
        entity_id = str(record.data.get("id", "")) or None

        if "work_group_ids" in record.data:
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_WORK_NOT_MULTI_GROUP,
                    severity="error",
                    file=file_rel,
                    message="Work must not belong to multiple Work Groups.",
                    entity_type=record.entity_type,
                    entity_id=entity_id,
                    field="work_group_ids",
                )
            )

        work_group_id = record.data.get("work_group_id")
        if isinstance(work_group_id, list):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_WORK_NOT_MULTI_GROUP,
                    severity="error",
                    file=file_rel,
                    message="Work must not belong to multiple Work Groups.",
                    entity_type=record.entity_type,
                    entity_id=entity_id,
                    field="work_group_id",
                )
            )
        elif work_group_id is not None and not isinstance(work_group_id, str):
            report.findings.append(
                ValidationFinding(
                    rule_id=rules.RULE_DOM_WORK_SINGLE_GROUP,
                    severity="error",
                    file=file_rel,
                    message="Work must have exactly one work_group_id string.",
                    entity_type=record.entity_type,
                    entity_id=entity_id,
                    field="work_group_id",
                )
            )

    def _normalize_title(self, title: str) -> str:
        collapsed = re.sub(r"\s+", " ", title).strip().lower()
        collapsed = re.sub(r"[^a-z0-9\s]", "", collapsed)
        return collapsed

    def _jaccard_tokens(self, text_a: str, text_b: str) -> float:
        a = set(text_a.split())
        b = set(text_b.split())
        if not a or not b:
            return 0.0
        return len(a.intersection(b)) / len(a.union(b))

    def _performer_fingerprint(self, performers: Any) -> str:
        if not isinstance(performers, list):
            return ""
        parts: list[str] = []
        for performer in performers:
            if not isinstance(performer, dict):
                continue
            name = str(performer.get("person_id") or performer.get("name") or "").strip().lower()
            role = str(performer.get("role") or "").strip().lower()
            if name:
                parts.append(f"{name}:{role}")
        return "|".join(sorted(parts))
