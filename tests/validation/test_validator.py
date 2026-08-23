from __future__ import annotations

from pathlib import Path

from classical_music.validation.validator import DataValidator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_valid_minimal_dataset_has_no_errors(tmp_path: Path) -> None:
    _write(
        tmp_path / "data/persons/ludwig-van-beethoven.yaml",
        "id: ludwig-van-beethoven\nname: Ludwig van Beethoven\n",
    )
    _write(
        tmp_path / "data/work-groups/beethoven-symphony-5.yaml",
        (
            "id: beethoven-symphony-5\n"
            "composer_id: ludwig-van-beethoven\n"
            "title: Symphony No. 5\n"
        ),
    )
    _write(
        tmp_path / "data/works/beethoven-symphony-5-work.yaml",
        (
            "id: beethoven-symphony-5-work\n"
            "work_group_id: beethoven-symphony-5\n"
            "composer_id: ludwig-van-beethoven\n"
            "title: Symphony No. 5 in C minor\n"
        ),
    )
    _write(
        tmp_path / "data/performances/beethoven-symphony-5-kleiber.yaml",
        (
            "id: beethoven-symphony-5-kleiber\n"
            "work_id: beethoven-symphony-5-work\n"
            "performers:\n"
            "  - name: Carlos Kleiber\n"
            "    role: conductor\n"
        ),
    )

    report = DataValidator(tmp_path).run()

    assert report.error_count == 0


def test_performance_referencing_work_group_is_error(tmp_path: Path) -> None:
    _write(tmp_path / "data/persons/w-a-mozart.yaml", "id: w-a-mozart\nname: W. A. Mozart\n")
    _write(
        tmp_path / "data/work-groups/mozart-k550.yaml",
        "id: mozart-k550\ncomposer_id: w-a-mozart\ntitle: Symphony No. 40\n",
    )
    _write(
        tmp_path / "data/works/mozart-k550-work.yaml",
        "id: mozart-k550-work\nwork_group_id: mozart-k550\ncomposer_id: w-a-mozart\ntitle: Symphony No. 40 in G minor\n",
    )
    _write(
        tmp_path / "data/performances/mozart-k550-bad.yaml",
        (
            "id: mozart-k550-bad\n"
            "work_id: mozart-k550\n"
            "performers:\n"
            "  - name: SCO\n"
            "    role: orchestra\n"
        ),
    )

    report = DataValidator(tmp_path).run()
    assert any(f.rule_id == "REF-005" for f in report.findings)


def test_gem_on_performance_is_error(tmp_path: Path) -> None:
    _write(tmp_path / "data/persons/js-bach.yaml", "id: js-bach\nname: J. S. Bach\n")
    _write(
        tmp_path / "data/work-groups/bach-bwv-1052.yaml",
        "id: bach-bwv-1052\ncomposer_id: js-bach\ntitle: Keyboard Concerto BWV 1052\n",
    )
    _write(
        tmp_path / "data/works/bach-bwv-1052-work.yaml",
        "id: bach-bwv-1052-work\nwork_group_id: bach-bwv-1052\ncomposer_id: js-bach\ntitle: Keyboard Concerto in D minor\ngem: true\n",
    )
    _write(
        tmp_path / "data/performances/bach-err.yaml",
        (
            "id: bach-err\n"
            "work_id: bach-bwv-1052-work\n"
            "gem: true\n"
            "performers:\n"
            "  - name: Il Pomo d'Oro\n"
            "    role: orchestra\n"
        ),
    )

    report = DataValidator(tmp_path).run()
    assert any(f.rule_id == "REC-021" for f in report.findings)


def test_invalid_url_and_gramophone_issue_are_errors(tmp_path: Path) -> None:
    _write(tmp_path / "data/persons/gm.yaml", "id: gm\nname: Gustav Mahler\n")
    _write(
        tmp_path / "data/work-groups/mahler-5.yaml",
        "id: mahler-5\ncomposer_id: gm\ntitle: Symphony No. 5\n",
    )
    _write(
        tmp_path / "data/works/mahler-5-work.yaml",
        "id: mahler-5-work\nwork_group_id: mahler-5\ncomposer_id: gm\ntitle: Symphony No. 5\n",
    )
    _write(
        tmp_path / "data/performances/mahler-5-perf.yaml",
        (
            "id: mahler-5-perf\n"
            "work_id: mahler-5-work\n"
            "performers:\n"
            "  - name: BPO\n"
            "    role: orchestra\n"
            "links:\n"
            "  tidal:\n"
            "    url: tidal.com/track/123\n"
            "reviews:\n"
            "  gramophone:\n"
            "    issue: 2024/06\n"
        ),
    )

    report = DataValidator(tmp_path).run()
    assert any(f.rule_id == "SCH-006" for f in report.findings)
    assert any(f.rule_id == "SCH-007" for f in report.findings)
