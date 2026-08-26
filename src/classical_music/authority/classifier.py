from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal


DuplicateClassification = Literal[
    "confirmed_duplicate",
    "distinct_works",
    "catalogue_conflict",
    "needs_authority_review",
]

DERIVED_RELATION_TYPES = {
    "arrangement_of",
    "completion_of",
    "orchestration_of",
    "reconstruction_of",
    "revision_of",
    "suite_from",
    "version_of",
}


@dataclass(frozen=True)
class CatalogueIdentifier:
    namespace: str
    value: str
    source: str = "local"

    @property
    def normalized(self) -> str:
        return normalize_catalogue_identifier(self.namespace, self.value)


@dataclass(frozen=True)
class AuthorityCandidate:
    source: str
    identifier: str
    title: str | None = None
    relationship_to_cluster: str | None = None


@dataclass(frozen=True)
class WorkIdentity:
    work_id: str
    composer_id: str
    title: str
    work_group_id: str | None = None
    catalogues: tuple[CatalogueIdentifier, ...] = ()
    authority_candidates: tuple[AuthorityCandidate, ...] = ()
    relationship_types: tuple[str, ...] = ()

    @property
    def normalized_title(self) -> str:
        return normalize_title(self.title)

    @property
    def musicbrainz_ids(self) -> set[str]:
        return {
            candidate.identifier
            for candidate in self.authority_candidates
            if candidate.source == "musicbrainz" and candidate.identifier
        }

    @property
    def normalized_catalogues(self) -> set[str]:
        return {
            catalogue.normalized
            for catalogue in self.catalogues
            if catalogue.normalized and is_reliable_catalogue_namespace(self.composer_id, catalogue.namespace)
        }

    @property
    def has_catalogue_metadata(self) -> bool:
        return any(catalogue.normalized for catalogue in self.catalogues)

    @property
    def has_derived_relationship(self) -> bool:
        return any(rel in DERIVED_RELATION_TYPES for rel in self.relationship_types)


@dataclass(frozen=True)
class DuplicateCluster:
    rule_id: Literal["DUP-002", "DUP-003"]
    works: tuple[WorkIdentity, ...]


@dataclass(frozen=True)
class AuthorityEvidence:
    classification: DuplicateClassification
    curator_review_required: bool
    evidence: tuple[str, ...]
    proposed_action: str
    confidence: float = 0.0
    authority_ids: tuple[str, ...] = field(default_factory=tuple)


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.casefold().strip())


def normalize_catalogue_identifier(namespace: str, value: str) -> str:
    namespace_norm = re.sub(r"[^a-z0-9-]+", "", namespace.casefold().strip().replace("_", "-"))
    value_norm = re.sub(r"[\s.]+", "", value.casefold().strip())
    return f"{namespace_norm}:{value_norm}" if namespace_norm and value_norm else ""


def is_reliable_catalogue_namespace(composer_id: str, namespace: str) -> bool:
    namespace_norm = re.sub(r"[^a-z0-9-]+", "", namespace.casefold().strip().replace("_", "-"))
    if namespace_norm == "k" and composer_id != "wolfgang-amadeus-mozart":
        return False
    return True


def classify_duplicate_cluster(cluster: DuplicateCluster) -> AuthorityEvidence:
    works = cluster.works
    if len(works) < 2:
        return AuthorityEvidence(
            classification="needs_authority_review",
            curator_review_required=True,
            evidence=("Cluster has fewer than two Works to compare",),
            proposed_action="no_action",
        )

    composer_ids = {work.composer_id for work in works}
    if len(composer_ids) > 1:
        return AuthorityEvidence(
            classification="needs_authority_review",
            curator_review_required=True,
            evidence=("Cluster contains multiple composers; duplicate heuristic is not comparable",),
            proposed_action="review_cluster_input",
        )

    if any(work.has_derived_relationship for work in works):
        return AuthorityEvidence(
            classification="needs_authority_review",
            curator_review_required=True,
            evidence=("At least one Work has a version/arrangement/completion relationship",),
            proposed_action="review_work_relationships",
        )

    mbid_sets = [work.musicbrainz_ids for work in works]
    populated_mbid_sets = [ids for ids in mbid_sets if ids]
    if populated_mbid_sets and len(populated_mbid_sets) == len(works):
        common_mbids = set.intersection(*populated_mbid_sets)
        all_mbids = set.union(*populated_mbid_sets)
        if common_mbids:
            mbid = sorted(common_mbids)[0]
            return AuthorityEvidence(
                classification="confirmed_duplicate",
                curator_review_required=False,
                evidence=(f"All Works share MusicBrainz Work ID {mbid}",),
                authority_ids=(f"musicbrainz:{mbid}",),
                confidence=0.95,
                proposed_action="candidate_for_curator_approved_merge",
            )
        if len(all_mbids) > 1:
            return AuthorityEvidence(
                classification="distinct_works",
                curator_review_required=False,
                evidence=("Works have different MusicBrainz Work IDs",),
                authority_ids=tuple(f"musicbrainz:{mbid}" for mbid in sorted(all_mbids)),
                confidence=0.9,
                proposed_action="keep_separate",
            )

    catalogue_sets = [work.normalized_catalogues for work in works]
    populated_catalogue_sets = [ids for ids in catalogue_sets if ids]
    if populated_catalogue_sets and len(populated_catalogue_sets) == len(works):
        common_catalogues = set.intersection(*populated_catalogue_sets)
        all_catalogues = set.union(*populated_catalogue_sets)
        if common_catalogues:
            catalogue = sorted(common_catalogues)[0]
            return AuthorityEvidence(
                classification="confirmed_duplicate",
                curator_review_required=True,
                evidence=(f"All Works share normalized catalogue identifier {catalogue}",),
                authority_ids=tuple(sorted(common_catalogues)),
                confidence=0.75,
                proposed_action="candidate_for_authority_confirmed_merge",
            )
        if len(all_catalogues) > 1:
            return AuthorityEvidence(
                classification="distinct_works",
                curator_review_required=True,
                evidence=("Works have different normalized catalogue identifiers",),
                authority_ids=tuple(sorted(all_catalogues)),
                confidence=0.7,
                proposed_action="keep_separate_pending_authority_review",
            )

    if any(populated_mbid_sets) and (any(populated_catalogue_sets) or any(work.has_catalogue_metadata for work in works)):
        return AuthorityEvidence(
            classification="catalogue_conflict",
            curator_review_required=True,
            evidence=("Authority/catalogue evidence is partial or inconsistent across Works",),
            authority_ids=tuple(sorted(set().union(*populated_mbid_sets, *populated_catalogue_sets))),
            confidence=0.4,
            proposed_action="review_catalogue_authority_conflict",
        )

    same_title = len({work.normalized_title for work in works}) == 1
    if same_title:
        evidence = "Same composer and title only; no catalogue or authority identifier proves identity"
    else:
        evidence = "No sufficient authority evidence to classify cluster"
    return AuthorityEvidence(
        classification="needs_authority_review",
        curator_review_required=True,
        evidence=(evidence,),
        confidence=0.0,
        proposed_action="review_with_external_authority",
    )
