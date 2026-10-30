"""Contract tests for the MB recording report issue template (issue #433)."""

from pathlib import Path

TEMPLATE_PATH = Path(".github/ISSUE_TEMPLATE/mb-recording-report.yml")


def test_template_asks_for_composer_and_work_only():
    """The curator fills in composer and work; everything else is optional."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "id: componist" in template
    assert "id: werk" in template
    # Both mandatory fields are validated as required.
    assert template.count("required: true") == 2
    # Context stays optional; exclusions are NOT a form field - the curator
    # cannot know MusicBrainz MBIDs before the first report runs, so they
    # are handled as replies to the checklist comment instead (issue #433).
    assert "id: toelichting" in template
    assert "id: exclusies" not in template
    assert template.count("required: false") == 1


def test_template_carries_its_own_guard_label_only():
    """Issue events trigger other workflows; the template must never carry
    the phase-2 curator-workflow label (issue #367)."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "mb-recording-report" in template
    assert "phase-2-curator-workflow" not in template


def test_template_promises_candidate_confirmation():
    """No exact MusicBrainz title required: the workflow fuzzy-searches and
    first posts candidates for confirmation (validated empirically against
    the MB search API: a typo like 'Das lied van de Erde' still scores 100
    unquoted, but 'Lied von der Erde' quoted matches a different work first)."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "confirms candidates" in template
    assert "as known in MusicBrainz" not in template
