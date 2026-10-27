"""Regression checks against built HTML, including the original slash/.html mismatch."""

import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "check_publication_links", Path(__file__).parents[1] / "scripts/check_publication_links.py"
)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.mark.parametrize("baseurl", ["", "/classical_music"])
def test_built_collection_links_resolve_with_root_or_repository_baseurl(tmp_path, baseurl):
    composer = tmp_path / "composers" / "vivaldi"
    composer.mkdir(parents=True)
    (composer / "index.html").write_text("<h1>Antonio Vivaldi</h1>")
    (tmp_path / "index.html").write_text(
        f'<a href="{baseurl}/composers/vivaldi/?source=index#works">Vivaldi</a>'
        '<a href="https://tidal.com/album/123">Listen</a>'
        '<a href="#summary">Summary</a>'
    )
    assert checker.check_links(tmp_path, baseurl) == (1, [])


def test_slash_link_to_html_file_fails_even_when_jekyll_build_succeeded(tmp_path):
    composers = tmp_path / "composers"
    composers.mkdir(parents=True)
    (composers / "vivaldi.html").write_text("<h1>Antonio Vivaldi</h1>")
    (tmp_path / "index.html").write_text(
        '<a href="/classical_music/composers/vivaldi/">Vivaldi</a>'
    )
    checked, failures = checker.check_links(tmp_path, "/classical_music")
    assert checked == 1
    assert len(failures) == 1
    assert "vivaldi/" in failures[0]


def test_internal_leak_link_fails_the_build(tmp_path):
    """A link into non-collection material must never resolve (issue #358)."""
    composers = tmp_path / "composers"
    composers.mkdir(parents=True)
    (composers / "index.html").write_text(
        '<a href="/classical_music/reports/review/index.html">Queue</a>'
    )
    checked, failures = checker.check_links(tmp_path, "/classical_music")
    assert checked == 1
    assert failures


def test_no_generated_publication_pages_is_a_failure(tmp_path):
    assert checker.check_links(tmp_path, "")[1]
