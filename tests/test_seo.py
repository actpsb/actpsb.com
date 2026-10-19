import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index", "about", "services", "nsx-adviser", "insights", "contact"]
# Set to the confirmed production origin to enable canonical/sitemap checks.
ORIGIN_CONFIRMED = None


def read(n):
    return (ROOT / f"{n}.html").read_text(encoding="utf-8")


def meta(html, attr, key):
    m = re.search(rf'<meta {attr}="{key}" content="([^"]*)"', html)
    return m.group(1) if m else None


class SeoTests(unittest.TestCase):
    def test_unique_title_description_og(self):
        seen = {"title": set(), "desc": set()}
        for n in PAGES:
            h = read(n)
            title = re.search(r"<title>(.*?)</title>", h).group(1)
            desc = meta(h, "name", "description")
            self.assertTrue(title and desc, n)
            self.assertLessEqual(len(title), 60, n)
            self.assertTrue(50 <= len(desc) <= 170, (n, len(desc)))
            self.assertEqual(meta(h, "property", "og:title"), title, n)
            self.assertEqual(meta(h, "property", "og:description"), desc, n)
            for k in ("og:site_name", "og:type", "og:locale"):
                self.assertTrue(meta(h, "property", k), (n, k))
            seen["title"].add(title)
            seen["desc"].add(desc)
        self.assertEqual(len(seen["title"]), 6)
        self.assertEqual(len(seen["desc"]), 6)

    def test_origin_dependent_tags_absent_until_confirmed(self):
        if ORIGIN_CONFIRMED:
            self.skipTest("origin confirmed")
        for n in PAGES:
            h = read(n)
            for bad in ('rel="canonical"', "og:url", "og:image"):
                self.assertNotIn(bad, h, (n, bad))
        self.assertFalse((ROOT / "sitemap.xml").exists())
        robots = (ROOT / "robots.txt").read_text()
        self.assertNotIn("Sitemap:", robots)
        self.assertIn("User-agent: *", robots)

    def test_structured_data_valid_and_sourced(self):
        import json
        for n in PAGES:
            for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', read(n), re.S):
                d = json.loads(blob)
                self.assertEqual(d["@context"], "https://schema.org")
                self.assertEqual(d["@type"], "Organization")
                self.assertEqual(d["name"], "ACTP Sdn Bhd")
                for k in ("address", "telephone", "email", "parentOrganization", "url"):
                    self.assertNotIn(k, d, (n, k))
                for u in d["sameAs"]:
                    self.assertTrue(u.startswith("https://www.nsx.com.au/"), u)
        self.assertIn("application/ld+json", read("index"))

    def test_heading_order_alt_and_image_dimensions(self):
        for n in PAGES:
            h = read(n)
            levels = [int(x) for x in re.findall(r"<h([1-6])[ >]", h)]
            self.assertEqual(levels.count(1), 1, n)
            self.assertEqual(levels[0], 1, n)
            for a, b in zip(levels, levels[1:]):
                self.assertLessEqual(b - a, 1, n)
            for tag in re.findall(r"<img [^>]*>", h):
                for attr in ("alt=", "width=", "height="):
                    self.assertIn(attr, tag, (n, tag))

    def test_no_third_party_requests_or_webfonts(self):
        for n in PAGES:
            h = read(n)
            for m in re.findall(r'<(?:link|script|img)[^>]*(?:src|href)="(https?://[^"]+)"', h):
                self.fail((n, m))
        for css in (ROOT / "assets/css").glob("*.css"):
            t = css.read_text()
            self.assertNotIn("@import", t, css.name)
            self.assertNotIn("url(http", t, css.name)

    def test_internal_links_resolve_and_pages_interlinked(self):
        linked = set()
        for n in PAGES:
            for href in re.findall(r'<a [^>]*href="([^"]+)"', read(n)):
                if re.match(r"[a-z]+:", href) or href.startswith("#"):
                    continue
                self.assertTrue((ROOT / href.split("#")[0].split("?")[0]).is_file(), (n, href))
                linked.add(href.split("#")[0].split("?")[0])
        for n in PAGES:
            self.assertIn(f"{n}.html", linked)


if __name__ == "__main__":
    unittest.main()
