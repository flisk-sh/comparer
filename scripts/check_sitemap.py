"""Check that a built comparer site publishes a sitemap matching its canonical URLs."""

import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.url = None

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        values = dict(attrs)
        if values.get("rel") == "canonical" and values.get("href"):
            self.url = values["href"]


def canonical_urls(site_dir):
    found = {}
    for path in sorted(Path(site_dir).rglob("*.html")):
        relative = path.relative_to(site_dir).as_posix()
        if relative == "404.html":
            continue
        parser = CanonicalParser()
        parser.feed(path.read_text(encoding="utf-8"))
        if parser.url:
            found[relative] = parser.url
    return found


def validate_site(site_dir):
    root = Path(site_dir)
    sitemap = root / "sitemap.xml"
    if not sitemap.is_file():
        return ["sitemap.xml is missing from the built site"]

    try:
        document = ET.parse(sitemap)
    except ET.ParseError as error:
        return [f"sitemap.xml is not valid XML: {error}"]

    if document.getroot().tag != f"{NS}urlset":
        return ["sitemap.xml must contain a sitemap urlset in the sitemaps.org namespace"]

    locations = [node.text.strip() for node in document.findall(f"{NS}url/{NS}loc") if node.text]
    problems = []
    if not locations:
        problems.append("sitemap.xml lists no pages")
    if len(locations) != len(set(locations)):
        problems.append("sitemap.xml lists a page more than once")
    if any("/comparer" not in location for location in locations):
        problems.append("sitemap.xml addresses must include the /comparer base path")
    if any("404" in location for location in locations):
        problems.append("sitemap.xml must not list the 404 page")

    canonicals = canonical_urls(root)
    for relative, url in canonicals.items():
        if url not in locations:
            problems.append(f"{relative} canonical {url} is missing from sitemap.xml")
    for url in locations:
        if url not in canonicals.values():
            problems.append(f"sitemap.xml address {url} has no matching canonical link")

    return problems


def main():
    site_dir = sys.argv[1] if len(sys.argv) > 1 else "_site"
    problems = validate_site(site_dir)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print(f"{site_dir}/sitemap.xml matches every public page canonical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
