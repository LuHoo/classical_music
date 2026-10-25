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


def test_pages_workflow_deploys_one_at_a_time_and_latest_push_wins():
    """Concurrent merges to main race on the gh-pages force-push (issue #380).

    Main pushes share one group so only the newest build+deploy runs; PR runs
    get their own group (they never deploy) so they cannot cancel an
    in-progress main deploy — the same per-PR/non-PR split as validate.yml.
    """
    workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")

    assert "concurrency:" in workflow
    assert "github.event_name == 'pull_request'" in workflow
    assert "format('pages-pr-{0}', github.event.pull_request.number)" in workflow
    assert "|| 'pages-deploy'" in workflow
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in workflow


def test_just_the_docs_head_custom_is_include_only():
    config = Path("_config.yml").read_text(encoding="utf-8")
    head_custom = Path("_includes/head_custom.html").read_text(encoding="utf-8")

    assert "head_custom:" not in config
    assert "publication.css" in head_custom


def test_generated_publication_pages_are_included_by_jekyll():
    config = Path("_config.yml").read_text(encoding="utf-8")

    assert "include:" in config
    assert "- publication" in config


def test_site_uses_bundled_theme_for_local_preview():
    config = Path("_config.yml").read_text(encoding="utf-8")

    assert "theme: just-the-docs" in config
    assert "remote_theme:" not in config
