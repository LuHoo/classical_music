"""Test-suite isolation guarantees (issue #307).

These tests fail when the suite writes into the checkout, when a shared
read-only fixture is mutated, or when a full-catalog test is accidentally
pointed at the real publication output directory.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from classical_music.catalog_snapshot import CatalogSnapshot
from classical_music.publication_site import PublicationSiteGenerator

PROTECTED = ('data', 'reports', 'docs', 'side materials', '_data_generated')


def _tree_digest(root: Path, relative: str) -> str | None:
    """Digest of every file under one checkout directory, or None when absent."""
    directory = root / relative
    if not directory.exists():
        return None
    digest = hashlib.sha256()
    for path in sorted(directory.rglob('*')):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture(scope='module')
def checkout_digests(repository_root: Path) -> dict[str, str | None]:
    return {name: _tree_digest(repository_root, name) for name in PROTECTED}


def test_generating_a_site_never_writes_into_the_checkout(tmp_path, repository_root, checkout_digests):
    """A publication build must land in the test's temporary directory.

    PublicationSiteGenerator defaults its output to ``repo_root/publication``
    and clears that directory first, so every test must pass an explicit
    output path.
    """
    before_publication = _tree_digest(repository_root, 'publication')

    output = tmp_path / 'publication'
    result = PublicationSiteGenerator(repository_root, output).generate()

    assert result.output_dir == output
    assert result.page_count > 0
    assert list(output.rglob('*.md'))
    assert _tree_digest(repository_root, 'publication') == before_publication
    for name, digest in checkout_digests.items():
        assert _tree_digest(repository_root, name) == digest, name


def test_shared_catalog_snapshot_cannot_be_mutated(catalog_snapshot: CatalogSnapshot):
    """The session snapshot is shared, so it must reject every mutation."""
    record = next(iter(catalog_snapshot.mappings('Work')))

    with pytest.raises(TypeError):
        record.mapping['title'] = 'tampered'
    with pytest.raises(TypeError):
        record.mapping.update({'title': 'tampered'})


def test_shared_canonical_records_are_independent_per_consumer(canonical_records):
    """Consumers thaw records; a local edit must not leak into the fixture."""
    from copy import deepcopy

    works = canonical_records['works']
    work_id = next(iter(works))
    original = works[work_id]['title']

    local = deepcopy(works)
    local[work_id]['title'] = 'tampered'

    assert canonical_records['works'][work_id]['title'] == original


def test_shared_matcher_reports_the_real_catalog(canonical_matcher, repository_root):
    """The shared matcher must cover the complete real catalog, not a subset."""
    summary = canonical_matcher.matches_summary()

    assert summary['works'] == len(list((repository_root / 'data/works').rglob('*.yaml')))
    assert summary['persons'] == len(list((repository_root / 'data/persons').glob('*.yaml')))
    assert summary['performances'] == len(list((repository_root / 'data/performances').glob('*.yaml')))
