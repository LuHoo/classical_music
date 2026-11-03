import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / '.github/ISSUE_TEMPLATE/new-performance.yml'


class NewPerformanceIssueTemplateCase(unittest.TestCase):
    """#435: the 'Nieuwe uitvoering' template is the curator's entry point.

    The issue author supplies only the TIDAL album URL; work IDs are resolved
    by the registration script, never asked here.
    """

    def test_template_exists_with_a_required_album_url_field(self):
        self.assertTrue(TEMPLATE.exists())
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn('name: Nieuwe uitvoering', text)
        self.assertIn('album_url', text)
        self.assertIn('tidal.com/browse/album/', text)
        self.assertIn('required: true', text)

    def test_template_carries_the_bash_kickoff_block(self):
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn('register_earmarked_recording.py', text)
        self.assertIn('--issue <nr>', text)
        self.assertIn('--comment', text)
        self.assertIn('--create-parking-issue', text)
        self.assertIn('./curator finish', text)

    def test_template_never_triggers_the_playlist_workflow(self):
        # Practijkregel uit #366: alleen echte curator-vergelijkingsissues
        # krijgen het phase-2-label; dit template opent nieuwe uitvoeringsissues.
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertNotIn('phase-2-curator-workflow', text)

    def test_template_meets_github_issue_form_top_level_schema(self):
        # GitHub laat een formulier in de kiemkeuze stilletjes vallen wanneer het
        # top-level schema niet klopt: 'description' is verplicht, 'about' bestaat
        # daar niet, en een lege 'labels: []'-lijst is evenmin geldig (#435).
        template_dir = ROOT / '.github/ISSUE_TEMPLATE'
        for template in sorted(template_dir.glob('*.yml')):
            with self.subTest(template=template.name):
                text = template.read_text(encoding='utf-8')
                self.assertRegex(text, r'(?m)^description: \S')
                self.assertNotRegex(text, r'(?m)^about:')
                self.assertNotIn('labels: []', text)


if __name__ == '__main__':
    unittest.main()
