import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / '.github/ISSUE_TEMPLATE'
TEMPLATE = TEMPLATE_DIR / 'new-performance.md'
LEGACY_FORM = TEMPLATE_DIR / 'new-performance.yml'


class NewPerformanceIssueTemplateCase(unittest.TestCase):
    """#435/#440: the 'New performance' template is the curator's entry point.

    The template is a classic markdown template so that the full text —
    including the visible "Processing (script)" runbook — becomes the issue
    body. Issue-form markdown blocks never reach the created issue body (#440).
    The issue author supplies only the TIDAL album URL; work IDs are resolved
    by the registration script, never asked here.
    """

    def test_classic_template_exists_and_the_issue_form_is_gone(self):
        self.assertTrue(TEMPLATE.exists())
        self.assertFalse(LEGACY_FORM.exists())

    def test_template_is_english_with_a_required_album_url(self):
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn('name: New performance', text)
        self.assertIn('TIDAL album URL (required)', text)
        self.assertIn('tidal.com/album/', text)
        self.assertNotIn('Nieuwe uitvoering', text)

    def test_processing_runbook_lands_in_the_issue_body(self):
        # Klassiek template: alle tekst komt in de body terecht, dus het
        # verwerk-runbook hoeft niet als verborgen form-instructie te bestaan.
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn('## Processing (script)', text)
        self.assertIn('register_earmarked_recording.py', text)
        self.assertIn('--issue <nr>', text)
        self.assertIn('--comment', text)
        self.assertIn('--create-parking-issue', text)
        self.assertIn('./curator finish', text)

    def test_template_never_triggers_the_playlist_workflow(self):
        # Praktijkregel uit #366: alleen echte curator-vergelijkingsissues
        # krijgen het phase-2-label; dit template opent nieuwe uitvoeringsissues.
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertNotIn('phase-2-curator-workflow', text)

    def test_issue_form_templates_meet_github_top_level_schema(self):
        # GitHub laat een formulier in de kiemkeuze stilletjes vallen wanneer het
        # top-level schema niet klopt: 'description' is verplicht, 'about' bestaat
        # daar niet, en een lege 'labels: []'-lijst is evenmin geldig (#435).
        for template in sorted(TEMPLATE_DIR.glob('*.yml')):
            with self.subTest(template=template.name):
                text = template.read_text(encoding='utf-8')
                self.assertRegex(text, r'(?m)^description: \S')
                self.assertNotRegex(text, r'(?m)^about:')
                self.assertNotIn('labels: []', text)


if __name__ == '__main__':
    unittest.main()
