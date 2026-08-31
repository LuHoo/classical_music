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


def test_generated_pages_show_works_without_performances(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    work_page = (tmp_path / "publication" / "works" / "bach-cantata-2.md").read_text(encoding="utf-8")
    composer_page = (tmp_path / "publication" / "composers" / "bach.md").read_text(encoding="utf-8")

    assert "No recommendation yet." in work_page
    assert "Cantata No. 2" in composer_page
    assert "no recommendation yet" in composer_page


def test_work_groups_are_navigation_only_not_recommendations(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    composer_page = (tmp_path / "publication" / "composers" / "bach.md").read_text(encoding="utf-8")

    assert "## Cantatas" in composer_page
    assert "Recommended Performances" not in composer_page


def test_work_page_renders_links_reviews_performer_roles_and_gem(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    work_page = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text(encoding="utf-8")

    assert "Gem: yes" in work_page
    assert "Monteverdi Choir (choir)" in work_page
    assert "English Baroque Soloists (ensemble)" in work_page
    assert "[Tidal](https://tidal.com/browse/track/123)" in work_page
    assert "Gramophone: 2024-01" in work_page
    assert "{" not in work_page


def test_multiple_profiles_remain_distinct(tmp_path):
    _seed_repo(tmp_path)

    PublicationSiteGenerator(tmp_path).generate()

    work_page = (tmp_path / "publication" / "works" / "bach-cantata-1.md").read_text(encoding="utf-8")

    assert "### chamber version" in work_page
    assert "### choir and orchestra" in work_page
    assert work_page.index("### chamber version") != work_page.index("### choir and orchestra")
