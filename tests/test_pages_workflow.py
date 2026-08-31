"""Tests for the reproducible GitHub Pages build workflow."""

from pathlib import Path


def test_pages_workflow_builds_on_pull_request_without_deploying_from_pr():
    workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "python -m classical_music.cli_validator" in workflow
    assert "python scripts/generate_publication_site.py" in workflow
    assert "bundle exec jekyll build" in workflow
    assert "test -f _site/publication/index.html" in workflow
    assert "if: github.event_name == 'push' && github.ref == 'refs/heads/main'" in workflow


def test_just_the_docs_head_custom_is_include_only():
    config = Path("_config.yml").read_text(encoding="utf-8")
    head_custom = Path("_includes/head_custom.html").read_text(encoding="utf-8")

    assert "head_custom:" not in config
    assert "publication.css" in head_custom


def test_generated_publication_pages_are_included_by_jekyll():
    config = Path("_config.yml").read_text(encoding="utf-8")

    assert "include:" in config
    assert "- publication" in config
