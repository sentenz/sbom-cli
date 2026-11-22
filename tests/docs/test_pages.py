"""Regression tests for the generated Zensical Pages artifact."""

import unittest
from pathlib import Path

SITE = Path("public")


class DocumentationPagesTests(unittest.TestCase):
    """Validate the published HTML, not only the build exit status."""

    def page(self, path):
        target = SITE / path / "index.html"
        self.assertTrue(target.is_file(), f"Missing generated page: {target}")
        return target.read_text(encoding="utf-8")

    def test_client_docstrings_are_rendered(self):
        html = self.page("reference/sbom/client")
        self.assertNotIn("::: sbom.client", html)
        self.assertIn("Represent a connection to a Dependency-Track server", html)
        self.assertIn("Upload an SBOM file to Dependency-Track", html)
        self.assertIn("upload_sbom", html)

    def test_exception_docstrings_are_rendered(self):
        html = self.page("reference/sbom/utils/exceptions")
        self.assertNotIn("::: sbom.utils.exceptions", html)
        self.assertIn("Report an unsuccessful HTTP response other than 404", html)
        self.assertIn("ValidationError", html)

    def test_gfm_pages_still_render(self):
        alerts = self.page("upload-methods")
        tables = self.page("decisions/adr-001-docstrings-style-python")
        self.assertIn('<aside class="admonition note">', alerts)
        self.assertIn("<table>", tables)


if __name__ == "__main__":
    unittest.main()
