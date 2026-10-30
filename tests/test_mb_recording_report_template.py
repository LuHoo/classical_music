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
    # Re-runs stay possible: exclusions and context are optional, so a
    # curator can re-open the same issue after a report without editing
    # mandatory fields.
    assert "id: exclusies" in template
    assert template.count("required: false") == 2


def test_template_carries_its_own_guard_label_only():
    """Issue events trigger other workflows; the template must never carry
    the phase-2 curator-workflow label (issue #367)."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "mb-recording-report" in template
    assert "phase-2-curator-workflow" not in template
