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
    the phase-2 curator-workflow label (issue #367)."""[\]HHSTUWÔUXYÝ^
[ÛÙ[ÏH]NB\ÜÙ\X\XÛÜ[Ë\\Ü[[\]B\ÜÙ\\ÙKLXÝ\]Ü]ÛÜÙÝÈÝ[[\]BY\ÝÝ[\]WÜÛZ\Ù\×ØØ[Y]WØÛÛ\X][Û
NÈ^XÝ]\ÚXÐZ[]H\]Z\YHÛÜÙÝÈ^K\ÙX\Ú\È[\ÝÜÝÈØ[Y]\ÈÜÛÛ\X][Û
[Y]Y[\\XØ[HYØZ[ÝHPÙX\ÚTNH\ÈZÙH	Ñ\ÈYY[H\IÈÝ[ØÛÜ\ÈL[][ÝY]	ÓYYÛ\\IÈ][ÝYX]Ú\ÈHY\[ÛÜÈ\Ý
K¢FV×ÆFRÒDTÕÄDUõDç&VE÷FWBVæ6öFæsÒ'WFbÓ" ¢76W'B&6öæf&×26æFFFW2"âFV×ÆFP¢76W'B&2¶æ÷vââ×W64'&ç¢"æ÷BâFV×ÆFP