import http.server
import re
import struct
import threading
import unittest
import urllib.request
import zlib
from functools import partial
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADING = "ACTP Website Coming Soon"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.h1 = ""
        self._in_h1 = False
        self.order = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "h1":
            self._in_h1 = True
            self.order.append("h1")
        if tag == "img":
            self.order.append("img")

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_h1:
            self.h1 += data

    def find(self, tag, **attrs):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in attrs.items())]


def parse():
    p = Page()
    p.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    return p


def check_png(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos, seen, width, height = 8, [], 0, 0
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        assert zlib.crc32(ctype + body) == crc, f"bad CRC in {ctype!r}"
        seen.append(ctype)
        if ctype == b"IHDR":
            width, height = struct.unpack(">II", body[:8])
        pos += 12 + length
    assert seen[0] == b"IHDR" and seen[-1] == b"IEND" and b"IDAT" in seen
    return width, height


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class SiteTests(unittest.TestCase):
    def test_html_metadata(self):
        p = parse()
        self.assertTrue(p.find("html", lang="en"))
        self.assertTrue(p.find("meta", charset="utf-8"))
        self.assertTrue(any("width=device-width" in a.get("content", "") for a in p.find("meta", name="viewport")))
        self.assertTrue(p.find("meta", name="description"))
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"<title>{HEADING}</title>", html)

    def test_exact_heading_and_logo_above(self):
        p = parse()
        self.assertEqual(p.h1.strip(), HEADING)
        self.assertLess(p.order.index("img"), p.order.index("h1"))

    def test_logo_reference_and_png(self):
        imgs = parse().find("img", **{"class": "logo"})
        self.assertEqual(len(imgs), 1)
        img = imgs[0]
        self.assertGreaterEqual(len(img.get("alt", "")), 15)
        self.assertIn("ACTP", img["alt"])
        path = ROOT / img["src"]
        self.assertTrue(path.is_file())
        w, h = check_png(path.read_bytes())
        self.assertAlmostEqual(w / h, 3.0, delta=0.3)
        self.assertEqual((int(img["width"]), int(img["height"])), (w, h))

    def test_css_reference_and_logo_rules(self):
        links = parse().find("link", rel="stylesheet")
        self.assertEqual([l["href"] for l in links], ["styles.css"])
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.logo\s*\{[^}]*height:\s*auto")
        self.assertRegex(css, r"\.logo-wrap\s*\{[^}]*background:\s*#fff")

    def test_local_http_server(self):
        handler = partial(QuietHandler, directory=str(ROOT))
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as srv:
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{srv.server_address[1]}/"
            try:
                for rel, ctype in (("", "text/html"), ("styles.css", "text/css"), ("assets/actp-logo.png", "image/png")):
                    with urllib.request.urlopen(base + rel, timeout=10) as r:
                        self.assertEqual(r.status, 200, rel)
                        self.assertIn(ctype, r.headers["Content-Type"])
                        body = r.read()
                        if rel.endswith(".png"):
                            check_png(body)
                        if rel == "":
                            self.assertIn(HEADING.encode(), body)
            finally:
                srv.shutdown()


if __name__ == "__main__":
    unittest.main()
