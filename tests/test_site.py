import http.server
import re
import struct
import subprocess
import threading
import unittest
import urllib.request
import zlib
from functools import partial
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADING = "ACTP Sdn Bhd"
STYLESHEETS = [
    "assets/css/tokens.css",
    "assets/css/base.css",
    "assets/css/layout.css",
    "assets/css/components.css",
]
SCRIPTS = ["assets/js/main.js"]
# Provisional palette from docs/design-system.md.
TOKENS = {
    "--color-forest": "#004d45",
    "--color-forest-dark": "#003b36",
    "--color-teal": "#008f83",
    "--color-emerald": "#00a896",
    "--color-bright-teal": "#39bdaa",
    "--color-canvas": "#f8faf9",
    "--color-soft": "#f1f5f3",
    "--color-text": "#1c2926",
    "--color-muted": "#667570",
    "--color-line": "#dce6e2",
}
BANNED_TOOLING = [
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "webpack.config.js", "vite.config.js", "tailwind.config.js", "postcss.config.js",
]
VOID = {"meta", "link", "img", "br", "hr", "input"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.h1 = ""
        self._in_h1 = False
        self.order = []
        self.depth_stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag not in VOID:
            self.depth_stack.append(tag)
        if tag == "h1":
            self._in_h1 = True
            self.order.append("h1")
        if tag == "img":
            self.order.append("img")

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False
        if tag not in VOID and self.depth_stack:
            self.last_pop = self.depth_stack.pop()

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


def read_css(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def all_css():
    return "\n".join(read_css(s) for s in STYLESHEETS)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class HomepageTests(unittest.TestCase):
    def test_html_metadata(self):
        p = parse()
        self.assertTrue(p.find("html", lang="en"))
        self.assertTrue(p.find("meta", charset="utf-8"))
        self.assertTrue(any("width=device-width" in a.get("content", "") for a in p.find("meta", name="viewport")))
        self.assertTrue(p.find("meta", name="description"))
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"<title>{HEADING}</title>", html)

    def test_single_h1_and_logo_above(self):
        p = parse()
        self.assertEqual(p.h1.strip(), HEADING)
        self.assertEqual(p.order.count("h1"), 1)
        self.assertLess(p.order.index("img"), p.order.index("h1"))

    def test_semantic_landmarks_and_skip_link(self):
        p = parse()
        for tag in ("header", "main", "footer"):
            self.assertEqual(len(p.find(tag)), 1, tag)
        self.assertTrue(p.find("main", id="main"))
        skips = p.find("a", **{"class": "skip-link"})
        self.assertEqual([s["href"] for s in skips], ["#main"])

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

    def test_assets_are_unmodified_original_logo_file(self):
        self.assertEqual(check_png((ROOT / "assets/actp-logo.png").read_bytes()), (841, 284))

    def test_no_dead_hash_links_and_local_refs_resolve(self):
        p = parse()
        for a in p.find("a"):
            href = a.get("href", "")
            self.assertNotEqual(href, "#")
            if href.startswith("#"):
                self.assertTrue(p.find("main", id=href[1:]) or any(
                    t[1].get("id") == href[1:] for t in p.tags), href)
            elif not re.match(r"[a-z]+:", href):
                self.assertTrue((ROOT / href).is_file(), href)


class StructureTests(unittest.TestCase):
    def test_stylesheets_linked_in_order(self):
        links = parse().find("link", rel="stylesheet")
        self.assertEqual([l["href"] for l in links], STYLESHEETS)
        for s in STYLESHEETS:
            self.assertTrue((ROOT / s).is_file(), s)

    def test_script_deferred_and_local(self):
        scripts = [a for t, a in parse().tags if t == "script"]
        self.assertEqual([s["src"] for s in scripts], SCRIPTS)
        for s in scripts:
            self.assertIn("defer", s)
            self.assertTrue((ROOT / s["src"]).is_file())

    def test_design_tokens_match_design_system(self):
        css = read_css("assets/css/tokens.css").lower()
        for name, value in TOKENS.items():
            self.assertRegex(css, rf"{re.escape(name)}:\s*{value};")
        doc = (ROOT / "docs/design-system.md").read_text(encoding="utf-8").lower()
        for value in TOKENS.values():
            self.assertIn(value, doc)

    def test_layout_tokens(self):
        css = read_css("assets/css/tokens.css")
        self.assertIn("--container-max: 1280px", css)
        self.assertIn("--reading-max: 680px", css)
        for n, px in {1: 8, 2: 16, 3: 24, 4: 32, 6: 48, 8: 64, 10: 80, 12: 96, 15: 120}.items():
            self.assertIn(f"--space-{n}: {px}px", css)
        for bp in (480, 768, 1024, 1280):
            self.assertIn(f"(min-width: {bp}px)", css)

    def test_fluid_type_tokens(self):
        css = read_css("assets/css/tokens.css")
        self.assertIn("--text-hero: clamp(42px, 5.6vw, 80px)", css)
        self.assertIn("--text-h2: clamp(32px, 3.8vw, 56px)", css)

    def test_logo_rules(self):
        css = all_css()
        self.assertRegex(css, r"\.logo\s*\{[^}]*height:\s*auto")
        self.assertRegex(css, r"\.logo-wrap\s*\{[^}]*background:\s*#fff")

    def test_accessibility_baseline_css(self):
        css = all_css()
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertRegex(css, r"--tap-min:\s*44px")
        self.assertRegex(css, r"\.button\s*\{[^}]*min-height:\s*var\(--tap-min\)")

    def test_no_forbidden_palette_or_imports(self):
        css = all_css().lower()
        self.assertNotIn("@import", css)
        self.assertNotRegex(css, r"gold|navy")

    def test_no_framework_or_build_tooling(self):
        for name in BANNED_TOOLING:
            self.assertFalse(list(ROOT.glob(name)), name)
        html = (ROOT / "index.html").read_text(encoding="utf-8").lower()
        for lib in ("react", "vue", "angular", "svelte", "bootstrap", "jquery", "tailwind"):
            self.assertNotIn(lib, html)
        for js in (ROOT / "assets/js").glob("*.js"):
            self.assertNotRegex(js.read_text(encoding="utf-8"), r"\bimport\s.+from\s|require\(")

    def test_progressive_enhancement_does_not_hide_content(self):
        css = all_css()
        self.assertNotRegex(css, r"opacity:\s*0\b")
        self.assertNotRegex(css, r"display:\s*none")


class RepoHygieneTests(unittest.TestCase):
    def test_gitignore_covers_python_caches(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("__pycache__/", text)
        self.assertIn("*.py[cod]", text)

    def test_no_tracked_generated_files(self):
        try:
            out = subprocess.run(
                ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
            ).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git metadata unavailable")
        self.assertNotIn("__pycache__", out)
        self.assertNotRegex(out, r"\.pyc\b")

    def test_ci_triggers_and_command(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertRegex(ci, r"push:\s*\n\s*branches:\s*\[main\]")
        self.assertRegex(ci, r"\n\s*pull_request:")
        self.assertIn("python -m unittest discover -s tests -v", ci)


class ServerTests(unittest.TestCase):
    def test_local_http_server(self):
        handler = partial(QuietHandler, directory=str(ROOT))
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as srv:
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{srv.server_address[1]}/"
            targets = [("", "text/html"), ("assets/actp-logo.png", "image/png")]
            targets += [(s, "text/css") for s in STYLESHEETS]
            targets += [(s, "javascript") for s in SCRIPTS]
            try:
                for rel, ctype in targets:
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
