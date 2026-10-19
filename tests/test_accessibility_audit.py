"""Structure checks for docs/qa/accessibility-audit.md (stdlib only)."""
import re
import unittest
from pathlib import Path

REPORT = Path(__file__).resolve().parent.parent / "docs" / "qa" / "accessibility-audit.md"


class AccessibilityAuditReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = REPORT.read_text(encoding="utf-8")

    def test_records_audited_sha(self):
        self.assertRegex(self.text, r"`[0-9a-f]{40}`")

    def test_has_required_sections(self):
        for heading in ("## Method", "## Findings", "## Limitations", "## Required fixes for ACTP-020"):
            self.assertIn(heading, self.text)

    def test_covers_all_six_pages(self):
        for page in ("index", "about", "services", "nsx-adviser", "insights", "contact"):
            self.assertIn(f"`{page}.html`", self.text)

    def test_covers_acceptance_areas(self):
        for term in ("Keyboard", "Escape", "contrast", "320px", "JavaScript off", "Reduced motion", "Forms"):
            self.assertRegex(self.text, re.compile(term, re.I))

    def test_does_not_claim_certification(self):
        self.assertIn("not a WCAG conformance claim", self.text)


if __name__ == "__main__":
    unittest.main()
