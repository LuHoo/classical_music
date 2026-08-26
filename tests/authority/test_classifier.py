from __future__ import annotations

from classical_music.authority import (
    AuthorityCandidate,
    CatalogueIdentifier,
    DuplicateCluster,
    WorkIdentity,
    classify_duplicate_cluster,
    normalize_catalogue_identifier,
)


def work(
    work_id: str,
    title: str,
    *,
    composer_id: str = "test-composer",
    catalogue: tuple[str, str] | None = None,
    mbid: str | None = None,
    relationships: tuple[str, ...] = (),
) -> WorkIdentity:
    catalogues = (CatalogueIdentifier(catalogue[0], catalogue[1]),) if catalogue else ()
    candidates = (AuthorityCandidate("musicbrainz", mbid),) if mbid else ()
    return WorkIdentity(
        work_id=work_id,
        composer_id=composer_id,
        title=title,
        work_group_id=f"{work_id}-group",
        catalogues=catalogues,
        authority_candidates=candidates,
        relationship_types=relationships,
    )


def classify(*works: WorkIdentity):
    return classify_duplicate_cluster(DuplicateCluster("DUP-003", tuple(works)))


def test_normalizes_catalogue_identifier() -> None:
    assert normalize_catalogue_identifier("Op.", "Op. 32a") == "op:op32a"
    assert normalize_catalogue_identifier("WAB", "WAB 42") == "wab:wab42"


def test_same_title_alone_needs_authority_review() -> None:
    result = classify(work("a", "Pastorale"), work("b", "Pastorale"))

    assert result.classification == "needs_authority_review"
    assert result.curator_review_required is True
    assert "title only" in result.evidence[0]


def test_same_catalogue_is_duplicate_evidence_but_still_requires_review() -> None:
    result = classify(
        work("a", "Symphony No. 1", catalogue=("WAB", "WAB 101")),
        work("b", "Symphony No. 1", catalogue=("WAB", "WAB 101")),
    )

    assert result.classification == "confirmed_duplicate"
    assert result.curator_review_required is True
    assert result.authority_ids == ("wab:wab101",)


def test_different_catalogues_are_distinct_work_evidence() -> None:
    result = classify(
        work("wab32", "Tantum ergo", composer_id="anton-bruckner", catalogue=("WAB", "WAB 32")),
        work("wab42", "Tantum ergo", composer_id="anton-bruckner", catalogue=("WAB", "WAB 42")),
        work("wab43", "Tantum ergo", composer_id="anton-bruckner", catalogue=("WAB", "WAB 43")),
    )

    assert result.classification == "distinct_works"
    assert result.proposed_action == "keep_separate_pending_authority_review"


def test_stravinsky_bare_k_catalogues_do_not_establish_identity() -> None:
    result = classify(
        work("k064", "Circus Polka", composer_id="igor-stravinsky", catalogue=("K", "K 064")),
        work("k066", "Circus Polka", composer_id="igor-stravinsky", catalogue=("K", "K 066")),
    )

    assert result.classification == "needs_authority_review"


def test_same_musicbrainz_work_id_is_strong_duplicate_evidence() -> None:
    result = classify(
        work("a", "Nobilissima visione", mbid="dd1b9bf9-d132-4f48-ab77-d27b289f6b2e"),
        work("b", "Nobilissima visione", mbid="dd1b9bf9-d132-4f48-ab77-d27b289f6b2e"),
    )

    assert result.classification == "confirmed_duplicate"
    assert result.curator_review_required is False
    assert result.authority_ids == ("musicbrainz:dd1b9bf9-d132-4f48-ab77-d27b289f6b2e",)


def test_different_musicbrainz_work_ids_are_distinct_evidence() -> None:
    result = classify(
        work("suite", "Nobilissima visione", mbid="dd1b9bf9-d132-4f48-ab77-d27b289f6b2e"),
        work("ballet", "Nobilissima visione", mbid="0989620a-0684-4e67-a3a2-919f51612663"),
    )

    assert result.classification == "distinct_works"
    assert result.curator_review_required is False


def test_missing_authority_data_remains_unresolved() -> None:
    result = classify(
        work("op32a", "Suite from Hamlet", composer_id="dmitri-shostakovich"),
        work("op116a", "Suite from Hamlet", composer_id="dmitri-shostakovich"),
    )

    assert result.classification == "needs_authority_review"


def test_derived_relationship_prevents_merge_classification() -> None:
    result = classify(
        work("original", "Circus Polka", composer_id="igor-stravinsky", catalogue=("K", "K 064")),
        work(
            "arrangement",
            "Circus Polka",
            composer_id="igor-stravinsky",
            catalogue=("K", "K 064"),
            relationships=("arrangement_of",),
        ),
    )

    assert result.classification == "needs_authority_review"
    assert result.proposed_action == "review_work_relationships"


def test_partial_authority_catalogue_mix_is_catalogue_conflict() -> None:
    result = classify(
        work("local", "Circus Polka", composer_id="igor-stravinsky", catalogue=("K", "K 066")),
        work("authority", "Circus Polka", composer_id="igor-stravinsky", mbid="musicbrainz-work"),
    )

    assert result.classification == "catalogue_conflict"
    assert result.curator_review_required is True
