from __future__ import annotations

from pathlib import Path

from classical_music.migration.classifier import classify_review_reason
from classical_music.migration.models import ReviewReason
from classical_music.migration.parser import parse_composer_markdown


def test_parser_extracts_record_and_tidal(tmp_path: Path) -> None:
    path = tmp_path / "mozart.md"
    path.write_text(
        "# Wolfgang Amadeus Mozart\n\n"
        "## Operas\n"
        "**Don Giovanni**, K. 527 [*Netherlands Wind Ensemble*](http://www.tidal.com/track/123) (09/2024)\n",
        encoding="utf-8",
    )

    records = parse_composer_markdown(path)

    assert len(records) == 1
    record = records[0]
    assert record.work_text == "Don Giovanni"
    assert record.tidal_links == ["http://www.tidal.com/track/123"]
    assert record.performer_text == "Netherlands Wind Ensemble"
    assert record.gramophone_issue == "2024-09"
    assert record.catalogue == "K.527"


def test_parser_splits_prokofiev_juvenile_symphonies(tmp_path: Path) -> None:
    path = tmp_path / "prokofiev.md"
    path.write_text(
        "# Sergei Prokofiev\n\n"
        "## Orchestral\n"
        "**Symphonies** – two juvenile: Symphony (1902) and Symphony (1908)\n",
        encoding="utf-8",
    )

    records = parse_composer_markdown(path)

    assert [record.source_id for record in records] == ["prokofiev:4:1", "prokofiev:4:2"]
    assert [record.work_text for record in records] == ["Symphony (1902)", "Symphony (1908)"]
    assert [record.date_text for record in records] == ["1902", "1908"]


def test_parser_preserves_trailing_identity_parenthetical_after_recording(tmp_path: Path) -> None:
    path = tmp_path / "brahms.md"
    path.write_text(
        "# Brahms\n\n"
        "## Orchestral\n"
        "**Serenade No. 1 in D major**, Op. 11 (1857-1858) "
        "[*Linos Ensemble*](http://www.tidal.com/track/230183268) "
        "(original version for chamber orchestra)\n",
        encoding="utf-8",
    )

    records = parse_composer_markdown(path)

    assert len(records) == 1
    assert records[0].work_text == (
        "Serenade No. 1 in D major (1857-1858) "
        "(original version for chamber orchestra)"
    )
    assert records[0].catalogue == "Op.11"


def test_parser_omits_labelled_recording_links_from_work_identity(tmp_path: Path) -> None:
    path = tmp_path / "stravinsky.md"
    path.write_text(
        "# Stravinsky\n\n"
        "## Ballet\n"
        "**Petrushka** (1911, rev. 1947), K012 "
        "[1911 version: *London Philharmonic Orchestra, Vladimir Jurowski*](https://tidal.com/browse/track/205310046?u) "
        "[1947 version: *Orchestre de Paris, Klaus Mäkelä*](http://www.tidal.com/track/348355808) "
        "(01/2001)\n",
        encoding="utf-8",
    )

    records = parse_composer_markdown(path)

    assert len(records) == 1
    assert records[0].work_text == "Petrushka (1911, rev. 1947)"
    assert records[0].tidal_links == [
        "https://tidal.com/browse/track/205310046?u",
        "http://www.tidal.com/track/348355808",
    ]
    assert records[0].gramophone_issue == "2001-01"
    assert records[0].catalogue == "K.012"


def test_parser_extracts_performers_from_labelled_recording_link(tmp_path: Path) -> None:
    path = tmp_path / "berlioz.md"
    path.write_text(
        "# Berlioz\n\n"
        "## Orchestral\n"
        "**Waverley**, Op. 1 (1828) [Ouverture *LSO, Sir Colin Davis*](http://www.tidal.com/track/4505556)\n",
        encoding="utf-8",
    )

    records = parse_composer_markdown(path)

    assert len(records) == 1
    assert records[0].work_text == "Waverley (1828)"
    assert records[0].performer_text == "LSO, Sir Colin Davis"
    assert records[0].tidal_links == ["http://www.tidal.com/track/4505556"]
    assert records[0].catalogue == "Op.1"


def test_parser_preserves_completion_label_as_work_identity(tmp_path: Path) -> None:
    path = tmp_path / "mahler.md"
    path.write_text(
        "# Mahler\n\n"
        "## Late works\n"
        "**Symphony No. 10 in F sharp** (unfinished; continuous draft score) (1910) "
        "[Realisation and elaboration of the unfinished drafts by Yoel Gamzou, "
        "*International Mahler Orchestra, Yoel Gamzou*](http://www.tidal.com/track/88068553)\n",
        encoding="utf-8",
    )

    records = parse_composer_markdown(path)

    assert records[0].work_text == (
        "Symphony No. 10 in F sharp (unfinished; continuous draft score) (1910) "
        "(Realisation and elaboration of the unfinished drafts by Yoel Gamzou)"
    )
    assert records[0].performer_text == "International Mahler Orchestra, Yoel Gamzou"


def test_classifier_detects_arrangement_signal(tmp_path: Path) -> None:
    path = tmp_path / "beethoven.md"
    path.write_text(
        "# Beethoven\n\n"
        "## Orchestral\n"
        "**Arrangement of Symphony No. 5**, Op. 67 [*X*](http://www.tidal.com/track/1)\n",
        encoding="utf-8",
    )

    record = parse_composer_markdown(path)[0]
    classifications = classify_review_reason(record)

    assert classifications
    assert classifications[0].reason in {
        ReviewReason.ARRANGEMENT_ORCHESTRATION,
        ReviewReason.UNCERTAIN_MATCH,
    }
