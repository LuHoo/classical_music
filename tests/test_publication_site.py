"""Tests for generated publication Jekyll pages."""

from pathlib import Path

from ruamel.yaml import YAML

from classical_music.publication_site import PublicationSiteGenerator


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = YAML()
    with open(path, "w", encoding="utf-8") as handle:
        yaml.dump(data, handle)


def _seed_repo(repo: Path) -> None:
    _write_yaml(repo / "data" / "persons" / "bach.yaml", {"id": "bach", "name": "Johann Sebastian Bach"})
    _write_yaml(repo / "data" / "work-groups" / "cantatas.yaml", {"id": "cantatas", "composer_id": "bach", "title": "Cantatas"})
    _write_yaml(
        repo / "data" / "works" / "bach-cantata-1.yaml",
        {
            "id": "bach-cantata-1",
            "work_group_id": "cantatas",
            "composer_id": "bach",
            "title": "Cantata No. 1",
            "gem": True,
        },
    )
    _write_yaml(
        repo / "data" / "works" / "bach-cantata-2.yaml",
        {
            "id": "bach-cantata-2",
            "work_group_id": "cantatas",
            "composer_id": "bach",
            "title": "Cantata No. 2",
        },
    )
    _write_yaml(
        repo / "data" / "performances" / "bach-cantata-1-gardiner.yaml",
        {
            "id": "bach-cantata-1-gardiner",
            "work_id": "bach-cantata-1",
            "profile": "choir and orchestra",
            "performers": [
                {"name": "Monteverdi Choir", "role": "choir"},
                {"name": "English Baroque Soloists", "role": "ensemble"},
            ],
            "links": {"tidal": {"url": "https://tidal.com/browse/track/123"}},
            "reviews": {"gramophone": {"issue": "2024-01"}},
        },
    )
    _write_yaml(
        repo / "data" / "performances" / "bach-cantata-1-solo.yaml",
        {
            "id": "bach-cantata-1-solo",
            "work_id": "bach-cantata-1",
            "profile": "chamber version",
            "performers": [{"name": "Solo Ensemble", "role": "ensemble"}],
        },
    )


def test_minimal_site_generation_creates_expected_pages(tmp_path):
    _seed_repo(tmp_path)

    result = PublicationSiteGenerator(tmp_path).generate()

    assert result.page_count == 5
    assert (tmp_path / "publication" / "index.md").exists()
    assert (tmp_path / "publication" / "composers" / "index.md").exists()
    assert (tmp_path / "publication" / "composers" / "bach.md").exists()
    assert (tmp_path / "publication" / "works" / "bach-cantata-1.md").exists()


def test_publication_links_match_explicit_directory_permalinks(tmp_path):
    """Every collection link must resolve to a declared route, including with a base URL."""
    import re

    _seed_repo(tmp_path)
    PublicationSiteGenerator(tmp_path).generate()
    pages = list((tmp_path / "publication").rglob("*.md"))
    yaml = YAML(typ="safe")
    routes = set()
    for page in pages:
        front_matter = yaml.load(page.read_text().split("---", 2)[1])
        routes.add(front_matter["permalink"])
    assert len(routes) == len(pages)
    assert "/publication/composers/bach/" in routes
    assert "/publication/works/bach-cantata-1/" in routes
    for page in pages:
        for href in re.findall(r'href="\{\{ site.baseurl \}\}([^\"]+)"', page.read_text()):
            assert href in routes, f"{page.name} links to undeclared route {href}"


def test_excerpt_coverage_is_visible_and_escaped(tmp_path):
    _seed_repo(tmp_path)
    path = tmp_path / "data" / "performances" / "bach-cantata-1-gardiner.yaml"
    yaml = YAML()
    data = yaml.load(path.read_text())
    data["excerpt"] = "Aria only; <not the complete cantata>"
    _write_yaml(path, data)

    PublicationSiteGenerator(tmp_path).generate()

    page = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text()
    assert 'class="recommendation-coverage"' in page
    assert "Aria only; &lt;not the complete cantata&gt;" in page
    assert "<not the complete cantata>" not in page


def test_generated_pages_show_works_without_performances(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    work_page = (tmp_path / "publication" / "works" / "bach-cantata-2.md").read_text(encoding="utf-8")
    composer_page = (tmp_path / "publication" / "composers" / "bach.md").read_text(encoding="utf-8")

    assert '<p class="recommendation-empty">No recommendation yet.</p>' in work_page
    assert "Cantata No. 2" in composer_page
    assert '<strong>Cantata No. 2</strong>' in composer_page


def test_work_groups_are_navigation_only_not_recommendations(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    composer_page = (tmp_path / "publication" / "composers" / "bach.md").read_text(encoding="utf-8")

    assert "### Cantatas" in composer_page
    assert "Recommended Performances" not in composer_page


def test_work_page_renders_links_reviews_performer_roles_and_gem(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    work_page = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text(encoding="utf-8")

    assert '<span class="gem-badge">Gem</span>' in work_page
    assert '<span class="performer-credit">Monteverdi Choir <span class="performer-role">(choir)</span></span>' in work_page
    assert (
        '<span class="performer-credit">English Baroque Soloists <span class="performer-role">(ensemble)</span></span>'
        in work_page
    )
    assert '<a href="https://tidal.com/browse/track/123">Tidal</a>' in work_page
    assert "Gramophone: 2024-01" in work_page
    assert "{" not in work_page


def test_multiple_profiles_remain_distinct(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    work_page = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text(encoding="utf-8")

    assert "<h3>chamber version</h3>" in work_page
    assert "<h3>choir and orchestra</h3>" in work_page
    assert work_page.index("<h3>chamber version</h3>") != work_page.index("<h3>choir and orchestra</h3>")


def test_public_pages_include_mobile_friendly_polish_structure(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    home_page = (tmp_path / "publication" / "index.md").read_text(encoding="utf-8")
    composer_index = (tmp_path / "publication" / "composers" / "index.md").read_text(encoding="utf-8")
    composer_page = (tmp_path / "publication" / "composers" / "bach.md").read_text(encoding="utf-8")
    work_page = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text(encoding="utf-8")

    assert 'class="publication-summary"' in home_page
    assert 'class="composer-list"' in composer_index
    assert 'class="work-entry"' in composer_page
    assert 'class="recommendation-card"' in work_page


def test_work_pages_are_reachable_but_excluded_from_global_navigation(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    composer_page = (tmp_path / "publication" / "composers" / "bach.md").read_text(encoding="utf-8")
    work_page = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text(encoding="utf-8")

    assert "/publication/works/bach-cantata-1/" in composer_page
    assert "nav_exclude: true" in work_page
    assert "parent: Collection" not in work_page


def test_editorial_collection_order_and_work_specific_recommendations(tmp_path):
    _seed_repo(tmp_path)
    _write_yaml(tmp_path / "data" / "publication" / "bach.yaml", {
        "composer_id": "bach", "collections": [{
            "title": "Collected cantatas", "opus": "Op. 3", "date_text": "1711",
            "work_ids": ["bach-cantata-2", "bach-cantata-1"],
        }],
    })
    _write_yaml(tmp_path / "data" / "works" / "bach-cantata-1.yaml", {
        "id": "bach-cantata-1", "work_group_id": "cantatas", "composer_id": "bach",
        "title": "Cantata No. 1", "catalogue": {"bwv": "BWV 1", "opus": "Op. 3"}, "gem": True,
    })
    PublicationSiteGenerator(tmp_path).generate()
    page = (tmp_path / "publication" / "composers" / "bach.md").read_text()
    assert "## Works with opus number" in page
    assert "<strong>Collected cantatas</strong>, Op. 3 (1711)" in page
    assert page.index("Cantata No. 2") < page.index("BWV 1") < page.index("Monteverdi Choir")
    assert '<a href="https://tidal.com/browse/track/123"><em>Monteverdi Choir, English Baroque Soloists</em></a>' in page
    assert "chamber version" in page and "choir and orchestra" in page
    assert "💎" in page
    assert page.count('/publication/works/bach-cantata-1/') == 1
    assert page.count('/publication/works/bach-cantata-2/') == 1


def test_singleton_is_compact_with_dates_catalogue_and_partial_coverage(tmp_path):
    _seed_repo(tmp_path)
    path = tmp_path / "data" / "works" / "bach-cantata-1.yaml"
    yaml = YAML()
    work = yaml.load(path.read_text())
    work.update({"catalogue": {"bwv": "BWV 1", "opus": "Op. 3"}, "date_text": "1705–1706", "category": "Vocal"})
    _write_yaml(path, work)
    perf_path = tmp_path / "data" / "performances" / "bach-cantata-1-gardiner.yaml"
    perf = yaml.load(perf_path.read_text())
    perf["excerpt"] = "Aria only <excerpt>"
    _write_yaml(perf_path, perf)
    PublicationSiteGenerator(tmp_path).generate()
    page = (tmp_path / "publication" / "composers" / "bach.md").read_text()
    assert "## Vocal" in page
    assert "<strong>Cantata No. 1</strong></a>, BWV 1, Op. 3 (1705–1706)" in page
    assert "Aria only &lt;excerpt&gt;" in page
    assert "### Cantatas" not in page
    assert "no recommendation yet" not in page
    detail = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text()
    assert "Catalogue: BWV 1, Op. 3" in detail
    assert "{'bwv'" not in detail


def test_invalid_editorial_membership_blocks_generation(tmp_path):
    import pytest
    _seed_repo(tmp_path)
    for ids in (["missing"], ["bach-cantata-1", "bach-cantata-1"]):
        _write_yaml(tmp_path / "data" / "publication" / "bach.yaml", {
            "composer_id": "bach", "collections": [{"title": "Collection", "work_ids": ids}],
        })
        with pytest.raises(RuntimeError, match="Unknown, foreign or repeated"):
            PublicationSiteGenerator(tmp_path).generate()


def test_collection_shares_recommendation_only_across_covered_members(tmp_path):
    _seed_repo(tmp_path)
    _write_yaml(tmp_path / "data" / "works" / "third.yaml", {
        "id": "third", "work_group_id": "cantatas", "composer_id": "bach", "title": "Cantata No. 3",
    })
    yaml = YAML()
    for source in (tmp_path / "data" / "performances").glob('*.yaml'):
        perf = yaml.load(source.read_text())
        perf.update({"id": perf["id"] + "-third", "work_id": "third"})
        _write_yaml(source.with_name(source.stem + '-third.yaml'), perf)
    _write_yaml(tmp_path / "data" / "publication" / "bach.yaml", {
        "composer_id": "bach", "collections": [{"title": "Cantatas", "work_ids": ["bach-cantata-1", "third", "bach-cantata-2"]}],
    })
    PublicationSiteGenerator(tmp_path).generate()
    page = (tmp_path / "publication" / "composers" / "bach.md").read_text()
    assert page.count("Monteverdi Choir") == 1
    assert page.index("Cantata No. 3") < page.index("Monteverdi Choir") < page.index("Cantata No. 2")
    # An uncovered member breaks a run, so the link cannot imply its coverage.
    _write_yaml(tmp_path / "data" / "publication" / "bach.yaml", {
        "composer_id": "bach", "collections": [{"title": "Cantatas", "work_ids": ["bach-cantata-1", "bach-cantata-2", "third"]}],
    })
    PublicationSiteGenerator(tmp_path).generate()
    page = (tmp_path / "publication" / "composers" / "bach.md").read_text()
    assert page.count("Monteverdi Choir") == 2
