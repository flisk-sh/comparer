import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_sitemap import validate_site

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://flisk-sh.github.io/comparer"

PAGES = {
    "index.html": f"{BASE}/",
    "about/index.html": f"{BASE}/about/",
    "pick/index.html": f"{BASE}/pick/",
    "extras/index.html": f"{BASE}/extras/",
    "404.html": f"{BASE}/404.html",
}


def write_fixture(directory, locations):
    site = Path(directory)
    urls = "".join(f"<url><loc>{location}</loc></url>" for location in locations)
    (site / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>",
        encoding="utf-8",
    )
    for relative, canonical in PAGES.items():
        path = site / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'<html><head><link rel="canonical" href="{canonical}"></head></html>', encoding="utf-8")


class SitemapTest(unittest.TestCase):
    def test_template_exists_and_uses_jekyll_pages(self):
        template = ROOT / "sitemap.xml"
        self.assertTrue(template.is_file(), "sitemap.xml template is missing")
        text = template.read_text(encoding="utf-8")
        self.assertIn("site.html_pages", text)
        self.assertIn("absolute_url", text)
        self.assertIn("404", text)

    def test_missing_sitemap_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(any("missing" in problem for problem in validate_site(directory)))

    def test_sitemap_matching_canonicals_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            write_fixture(directory, [PAGES[key] for key in ("index.html", "about/index.html", "pick/index.html", "extras/index.html")])
            self.assertEqual(validate_site(directory), [])

    def test_404_and_missing_page_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            write_fixture(directory, [PAGES["index.html"], PAGES["404.html"]])
            problems = validate_site(directory)
        self.assertTrue(any("404" in problem for problem in problems))
        self.assertTrue(any("missing from sitemap" in problem for problem in problems))

    def test_duplicate_address_and_wrong_base_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            write_fixture(directory, [PAGES["index.html"], PAGES["index.html"], "https://flisk-sh.github.io/about/"])
            problems = validate_site(directory)
        self.assertTrue(any("more than once" in problem for problem in problems))
        self.assertTrue(any("base path" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
