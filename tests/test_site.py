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
    "--color-muted": "#5f6e69",
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
        scripts = [a for t, a in parse().tags if t == "script" and a.get("type") != "application/ld+json"]
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
        # Hidden-start opacity is allowed only inside the JS-gated reveal keyframes.
        without_keyframes = re.sub(r"@keyframes[^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
        # Rules that start hidden must be gated behind the JS-set .js class.
        no_comments = re.sub(r"/\*.*?\*/", "", without_keyframes, flags=re.S)
        for sel in re.findall(r"([^{}]*)\{[^{}]*opacity:\s*0\b[^{}]*\}", no_comments):
            for part in sel.split(","):
                self.assertTrue(part.strip().startswith(".js "), sel)
        for sel in re.findall(r"([^{}]*)\{[^{}]*animation:(?!\s*none)[^{}]*\}", without_keyframes):
            self.assertIn(".js ", sel, sel)
        # Only the collapsed menu may use display: none: once JS-gated, and once pre-JS but only when
        # scripting is enabled (avoids a layout shift), never when scripting is off.
        self.assertEqual(len(re.findall(r"display:\s*none", css)), 2)
        self.assertRegex(css, r"\.js \.nav-menu\[hidden\]\s*\{\s*display:\s*none")
        self.assertRegex(css, r"@media \(scripting: enabled\)[^{]*\{\s*html:not\(\.js\) \.nav-menu\s*\{\s*display:\s*none")


PAGES = [
    ("index.html", "Home"), ("about.html", "About Us"), ("services.html", "Services"),
    ("nsx-adviser.html", "NSX Adviser"), ("insights.html", "Insights"), ("contact.html", "Contact"),
]


class NavTests(unittest.TestCase):
    def page(self, name):
        p = Page()
        p.feed((ROOT / name).read_text(encoding="utf-8"))
        return p

    def test_every_page_has_same_nav_with_current_marker(self):
        for name, _ in PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            links = re.findall(r'<a class="nav-link[^"]*" href="([^"]+)"( aria-current="page")?>([^<]+)</a>', html)
            self.assertEqual([(h, l) for h, _, l in links], PAGES, name)
            self.assertEqual([h for h, c, _ in links if c], [name], name)
            self.assertEqual(html.count("<h1"), 1, name)
            for h, _ in PAGES:
                self.assertTrue((ROOT / h).is_file(), h)

    def test_native_toggle_markup(self):
        for name, _ in PAGES:
            p = self.page(name)
            btn = p.find("button", **{"class": "nav-toggle"})
            self.assertEqual(len(btn), 1, name)
            self.assertEqual(btn[0]["type"], "button")
            self.assertEqual(btn[0]["aria-expanded"], "false")
            self.assertEqual(btn[0]["aria-controls"], "site-menu")
            self.assertTrue(p.find("ul", id="site-menu"))
            self.assertTrue(p.find("nav", **{"aria-label": "Primary"}))

    def test_menu_not_hidden_in_markup_for_no_js(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotRegex(html, r'<ul[^>]*id="site-menu"[^>]*hidden')

    def test_js_behaviour_and_css_targets(self):
        js = read_css("assets/js/main.js")
        for needle in ("aria-expanded", "Escape", "toggle.focus()", "contains(event.target)"):
            self.assertIn(needle, js)
        css = all_css()
        self.assertRegex(css, r"\.nav-link\s*\{[^}]*min-height:\s*var\(--tap-min\)")
        self.assertRegex(css, r"\.nav-toggle:not\(\[hidden\]\)\s*\{[^}]*min-height:\s*var\(--tap-min\)")
        self.assertRegex(css, r"\.site-header\s*\{[^}]*position:\s*sticky")


class HeroTests(unittest.TestCase):
    def hero(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<section class="hero".*?</section>', html, re.S)
        self.assertTrue(m)
        return m.group(0)

    def test_two_relevant_ctas_to_local_routes(self):
        ctas = re.findall(r'<a class="button[^"]*" href="([^"]+)">([^<]+)</a>', self.hero())
        self.assertEqual(ctas, [("nsx-adviser.html", "Explore the adviser role"), ("about.html", "About ACTP")])

    def test_copy_omits_source_links_and_removed_disclaimer(self):
        text = re.sub(r"<[^>]+>", " ", self.hero()).lower()
        self.assertIn("listed by nsx as an international nominated adviser", text)
        lead = re.search(r'<p class="lead">.*?</p>', self.hero(), re.S).group(0)
        note = re.search(r'<p class="hero__note">.*?</p>', self.hero(), re.S).group(0)
        self.assertIn("listed by NSX", lead)
        self.assertNotIn("Source:", lead)
        self.assertIn("admission procedures", note)
        self.assertNotIn("Source:", note)
        self.assertNotIn("https://www.nsx.com.au/", lead + note)
        self.assertNotIn("adviser-profile/130", note)
        self.assertNotIn("not a licence, endorsement or promise of results", text)
        for banned in ("coming soon", "award", "trusted by", "clients", "years of experience", "guarantee"):
            self.assertNotIn(banned, text)

    def test_artwork_uses_growth_image_and_is_decorative(self):
        hero = self.hero()
        self.assertEqual(hero.count("<img"), 1)
        self.assertIn('<img src="assets/hero-growth.png"', hero)
        self.assertIn('width="1635" height="962"', hero)
        self.assertIn('alt=""', hero)
        self.assertRegex(hero, r'class="hero__art" aria-hidden="true"')
        self.assertNotIn("<svg", hero)

    def test_hero_layout_and_motion_css(self):
        css = all_css()
        self.assertRegex(css, r"\.hero__art img\s*\{[^}]*max-height:\s*360px")
        self.assertRegex(css, r"\.hero__grid\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)")
        self.assertRegex(css, r"min-width: 1024px\)\s*\{[^}]*\.hero__grid\s*\{[^}]*11fr[^}]*9fr")
        self.assertRegex(css, r"\.js \.hero__copy\s*\{[^}]*animation:")
        self.assertIn("prefers-reduced-motion: reduce", css)


class IntroTests(unittest.TestCase):
    def section(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<section class="section intro".*?</section>', html, re.S)
        self.assertTrue(m)
        return m.group(0)

    def test_semantic_headings_and_about_destination(self):
        sec = self.section()
        self.assertEqual(sec.count("<h2"), 1)
        self.assertNotIn("<h1", sec)
        self.assertIn('aria-labelledby="intro-title"', sec)
        self.assertRegex(sec, r'<a class="button" href="about.html">About ACTP</a>')
        self.assertTrue((ROOT / "about.html").is_file())

    def test_distinguishes_actp_from_arris_without_source_links(self):
        sec = self.section()
        text = re.sub(r"<[^>]+>", " ", sec)
        self.assertIn("International Nominated Adviser, a member since 2022", text)
        self.assertNotIn("Source:", sec)
        self.assertNotIn('href="https://www.nsx.com.au/', sec)
        self.assertIn("describes ACTP Sdn. Bhd. as a wholly owned subsidiary of Arris Holdings Berhad", text)
        self.assertIn("Arris is a separate company", text)
        self.assertIn("not presented here as ACTP's own", text)

    def test_no_invented_people_offices_or_outcomes(self):
        low = re.sub(r"<[^>]+>", " ", self.section()).lower()
        for banned in ("founder", "director", "our team", "office", "puchong", "years", "award",
                       "clients", "guarantee", "@", "+603"):
            self.assertNotIn(banned, low)

    def test_artwork_uses_teamwork_image_and_responsive_css(self):
        sec = self.section()
        self.assertEqual(sec.count("<img"), 1)
        self.assertIn('src="assets/hero-teammwork.png"', sec)
        self.assertIn('width="1355" height="1161"', sec)
        self.assertIn('alt=""', sec)
        self.assertTrue((ROOT / "assets/hero-teammwork.png").is_file())
        self.assertRegex(sec, r'class="intro__art" aria-hidden="true"')
        self.assertNotIn("<svg", sec)
        css = all_css()
        self.assertRegex(css, r"\.intro__art img\s*\{[^}]*width:\s*100%;[^}]*height:\s*auto;")
        self.assertRegex(css, r"min-width: 1024px\)\s*\{[^}]*\.intro__grid\s*\{[^}]*5fr[^}]*7fr")
        self.assertRegex(css, r"\.intro__grid\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)")


class ServicesTests(unittest.TestCase):
    def section(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<section class="section section--dark services".*?</section>', html, re.S)
        self.assertTrue(m)
        return m.group(0)

    def test_heading_structure_and_cta(self):
        sec = self.section()
        self.assertEqual(sec.count("<h2"), 1)
        self.assertNotIn("<h1", sec)
        self.assertIn('aria-labelledby="services-title"', sec)
        self.assertIn('<a class="button button--light" href="services.html">View services</a>', sec)

    def test_nsx_scope_is_attributed_and_generic(self):
        sec = self.section()
        text = re.sub(r"<[^>]+>", " ", sec)
        for phrase in ("Admission procedures", "Directors' obligations", "NSX Rules"):
            self.assertIn(phrase, text)
        self.assertIn('href="https://www.nsx.com.au/regulation/companies/nominated-adviser/"', sec)
        self.assertIn("not a catalogue of ACTP's engagements", text)
        self.assertIn("not a guarantee of admission, capital raising or any outcome", text)

    def test_arris_services_qualified_and_linked(self):
        sec = self.section()
        text = re.sub(r"<[^>]+>", " ", sec)
        self.assertIn('href="https://www.arris.com.my/"', sec)
        self.assertIn("does not establish these as ACTP services", re.sub(r"\s+", " ", text))
        for banned in ("ipo", "restructuring", "award", "clients", "years of experience"):
            self.assertNotIn(banned, text.lower())

    def test_distinct_panels_not_uniform_cards(self):
        sec = self.section()
        classes = re.findall(r'class="(services__panel services__panel--\w+)"', sec)
        self.assertEqual(len(set(classes)), 3)
        self.assertNotIn("card", sec)

    def test_responsive_and_contrast_css(self):
        css = all_css()
        self.assertRegex(css, r"\.services__grid\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)")
        self.assertRegex(css, r"min-width: 1024px\)\s*\{[^}]*\.services__grid\s*\{[^}]*4fr[^}]*8fr")
        self.assertIn(".services__panel:hover", css)
        self.assertRegex(css, r"\.button--light\s*\{[^}]*color:\s*var\(--color-forest-dark\)")

class NsxSectionTests(unittest.TestCase):
    def section(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<section class="section nsx".*?</section>', html, re.S)
        self.assertTrue(m)
        return m.group(0)

    def text(self):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.section()))

    def test_heading_structure_and_ctas(self):
        sec = self.section()
        self.assertEqual(sec.count("<h2"), 1)
        self.assertNotIn("<h1", sec)
        self.assertIn('aria-labelledby="nsx-title"', sec)
        self.assertIn('href="https://www.nsx.com.au/listing/adviser-profile/130/" rel="noopener">View the NSX listing', sec)
        self.assertIn('href="nsx-adviser.html">Learn about the adviser role</a>', sec)

    def test_status_attributed_to_nsx_list_and_profile(self):
        sec = self.section()
        self.assertIn('href="https://www.nsx.com.au/listing/adviser-list/"', sec)
        self.assertIn('href="https://www.nsx.com.au/listing/adviser-profile/130/"', sec)
        self.assertIn("appears on NSX's registered Nominated Advisers list as an International adviser, a member since 2022", self.text())

    def test_generic_role_per_nsx_explainer(self):
        sec = self.section()
        self.assertIn('href="https://www.nsx.com.au/regulation/companies/nominated-adviser/"', sec)
        text = self.text()
        for phrase in ("Admission procedures", "Directors' obligations", "NSX Rules", "NSX describes nominated advisers"):
            self.assertIn(phrase, text)

    def test_no_guarantee_or_false_credential(self):
        text = self.text()
        self.assertIn("not a licence, certification or endorsement", text)
        self.assertIn("does not promise that any issuer will be admitted", text)
        for banned in ("licensed by", "regulated by", "accredited", "approved by nsx", "we guarantee", "successful listing", "ipo", "award"):
            self.assertNotIn(banned, text.lower())

    def test_external_links_marked_and_responsive_css(self):
        sec = self.section()
        for href in re.findall(r'<a [^>]*href="(https://[^"]+)"[^>]*>', sec):
            self.assertIn('href="%s" rel="noopener"' % href, sec)
        css = all_css()
        self.assertRegex(css, r"\.nsx__grid\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)")
        self.assertRegex(css, r"min-width: 1024px\)\s*\{[^}]*\.nsx__grid\s*\{[^}]*5fr[^}]*7fr")
        self.assertIn("overflow-wrap: anywhere", css)


class ApproachSectionTests(unittest.TestCase):
    def section(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<section class="section section--soft approach".*?</section>', html, re.S)
        self.assertTrue(m)
        return m.group(0)

    def test_four_ordered_stages_in_order(self):
        sec = self.section()
        self.assertIn('<ol class="approach__steps"', sec)
        self.assertEqual(sec.count('<li class="approach__step">'), 4)
        names = re.findall(r"<h3>(.*?)</h3>", sec)
        self.assertEqual(names, ["Discover", "Strategise", "Execute", "Support"])
        self.assertEqual(len(re.findall(r"<h2", sec)), 1)
        self.assertNotIn("<h1", sec)

    def test_explicitly_illustrative_not_asserted_methodology(self):
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.section())).lower()
        self.assertIn("illustrative", text)
        self.assertIn("not acTP's confirmed methodology".lower(), text)
        self.assertIn("pending confirmation by actp", text)
        for banned in ["our proven", "guarantee", "we deliver", "years of experience"]:
            self.assertNotIn(banned, text.replace("makes no promise", ""))

    def test_no_js_visibility_and_reduced_motion(self):
        css = all_css()
        self.assertRegex(css, r"\.js \.reveal\s*\{[^}]*opacity: 0")
        self.assertNotRegex(css, r"(?m)^\.(approach__step|reveal)\s*\{[^}]*opacity: 0")
        self.assertRegex(css, r"prefers-reduced-motion: reduce\)\s*\{[^}]*\.js \.reveal[^}]*opacity: 1")
        self.assertRegex(css, r"min-width: 1024px\)\s*\{[^}]*\.approach__steps\s*\{[^}]*repeat\(4")
        js = (ROOT / "assets/js/main.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", js)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("setTimeout", js)
        for sel in (".intro__item", ".services__panel", ".nsx__block", ".insights__empty", ".contact-cta__panel"):
            self.assertIn(sel, js)
        # Reveal class is applied by JS only, never authored in markup.
        for page in ROOT.glob("*.html"):
            self.assertNotIn("reveal", page.read_text(encoding="utf-8"), page.name)


class InsightsSectionTests(unittest.TestCase):
    def section(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<section class="section insights".*?</section>', html, re.S)
        self.assertTrue(m)
        return m.group(0)

    def test_genuine_empty_state_without_fabricated_content(self):
        sec = self.section()
        self.assertIn("There are no published insights available yet.", sec)
        self.assertEqual(len(re.findall(r"<h2", sec)), 1)
        for tag in ("<article", "<time", "<img", "Read more"):
            self.assertNotIn(tag, sec)
        self.assertNotRegex(re.sub(r"<[^>]+>", " ", sec), r"\b(19|20)\d\d\b")
        self.assertNotIn('href="#"', sec)

    def test_links_resolve_to_existing_pages(self):
        for href in re.findall(r'href="([^"]+)"', self.section()):
            self.assertFalse(href.startswith("http") or href.startswith("#"), href)
            self.assertTrue((ROOT / href).exists(), href)

    def test_decorative_art_hidden_and_status_region(self):
        sec = self.section()
        self.assertIn('class="insights__art" aria-hidden="true"', sec)
        self.assertNotIn('role="status"', sec)  # static content is not a live region (A11Y-3)

    def test_responsive_css_and_pattern_documented(self):
        css = all_css()
        self.assertRegex(css, r"\.insights__grid\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)")
        self.assertRegex(css, r"min-width: 1024px\)\s*\{[^}]*\.insights__grid\s*\{[^}]*6fr[^}]*5fr")
        self.assertNotRegex(css, r"\.insights[^{]*\{[^}]*opacity: 0")
        doc = (ROOT / "docs/insights-pattern.md").read_text(encoding="utf-8")
        for field in ("Category", "Featured image", "Publication date", "Title", "Short description", "Read-more link"):
            self.assertIn(field, doc)


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


class ContactFooterTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_footer_on_every_page_has_six_links_and_labelled_contact(self):
        for name, _ in PAGES:
            html = self.read(name)
            nav = re.search(r'<nav class="site-footer__nav".*?</nav>', html, re.S).group(0)
            self.assertEqual(re.findall(r'href="([^"]+)"', nav), [p for p, _ in PAGES], name)
            self.assertIn("NSX-listed group contact", html, name)
            self.assertIn("not confirmed as an ACTP-owned mailbox", html, name)
            self.assertIn('href="mailto:contact@arris.com.my"', html, name)
            tels = re.findall(r'href="(tel:[^"]*)"', html)
            self.assertTrue(tels, name)
            for tel in tels:
                self.assertRegex(tel, r"^tel:\+[0-9]+$", name)
                self.assertEqual(tel, "tel:+" + "603" + "80763063", name)
            self.assertNotRegex(html, r"facebook|linkedin|twitter|instagram", name)

    def test_homepage_cta_targets_contact_and_is_contrast_safe(self):
        html = self.read("index.html")
        sec = re.search(r'<section class="section contact-cta".*?</section>', html, re.S).group(0)
        self.assertIn('<a class="button button--cta" href="contact.html">Get in Touch</a>', sec)
        css = all_css()
        self.assertRegex(css, r"\.contact-cta__panel\s*\{[^}]*background:\s*var\(--color-white\)")
        self.assertRegex(css, r"\.button--cta\s*\{[^}]*background:\s*var\(--color-forest-dark\)[^}]*color:\s*var\(--color-white\)")
        self.assertRegex(css, r"\.site-footer\s*\{[^}]*background:\s*var\(--color-forest-dark\)")

    def test_form_has_no_fake_success(self):
        html = self.read("contact.html")
        self.assertIn("<form", html)
        self.assertNotRegex(html.lower(), r"message sent|thank you for|successfully")
        # The static page never claims acceptance; only the server's response can, after SMTP success.
        self.assertNotIn("accepted by our mail service", html)
        self.assertIn("Acceptance by the mail service is not confirmation", html)


class SecondaryPageTests(unittest.TestCase):
    NSX = "https://www.nsx.com.au/listing/adviser-profile/130/"
    H1 = {
        "about.html": "About ACTP", "services.html": "Services",
        "nsx-adviser.html": "NSX Nominated Adviser", "insights.html": "Insights", "contact.html": "Contact",
    }

    def read(self, name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_unique_titles_h1s_descriptions_and_shared_shell(self):
        titles, descs = set(), set()
        for name, h1 in self.H1.items():
            html = self.read(name)
            self.assertEqual(re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S), [h1], name)
            titles.add(re.search(r"<title>(.*?)</title>", html).group(1))
            descs.add(re.search(r'name="description" content="([^"]+)"', html).group(1))
            for sheet in STYLESHEETS:
                self.assertIn(f'href="{sheet}"', html, name)
            self.assertIn('src="assets/js/main.js" defer', html, name)
            self.assertNotIn("being prepared", html, name)
            ids = re.findall(r'id="([^"]+)"', html)
            self.assertEqual(len(ids), len(set(ids)), name)
            heads = [int(n) for n in re.findall(r"<h([1-6])[ >]", html)]
            self.assertEqual(heads[0], 1, name)
            for a, b in zip(heads, heads[1:]):
                self.assertLessEqual(b - a, 1, name)
        self.assertEqual(len(titles), 5)
        self.assertEqual(len(descs), 5)

    def test_sections_labelled_and_links_resolve(self):
        for name in self.H1:
            html = self.read(name)
            for label in re.findall(r'<section[^>]*aria-labelledby="([^"]+)"', html):
                self.assertIn(f'id="{label}"', html, name)
            for href in re.findall(r'<a [^>]*href="([^"]+)"', html):
                self.assertNotEqual(href, "#", name)
                if href.startswith("#"):
                    self.assertIn(f'id="{href[1:]}"', html, (name, href))
                elif not re.match(r"[a-z]+:", href):
                    self.assertTrue((ROOT / href.split("#")[0].split("?")[0]).is_file(), (name, href))
            for tag in re.findall(r"<a [^>]*>", html):
                if "nsx.com.au" in tag and 'href="https://' in tag:
                    self.assertIn("noopener", tag, name)
            for src in re.findall(r'(?:src|href)="(assets/[^"]+)"', html):
                self.assertTrue((ROOT / src).is_file(), (name, src))

    def test_sourced_attribution(self):
        about = self.read("about.html")
        self.assertIn("wholly owned subsidiary of Arris Holdings Berhad", about)
        self.assertIn(self.NSX, about)
        self.assertIn("https://www.arris.com.my/", about)
        self.assertIn("pending confirmation by ACTP", about)
        self.assertIn("39, Jalan Kenari 17C", about)
        nsx = self.read("nsx-adviser.html")
        for url in (self.NSX, "https://www.nsx.com.au/listing/adviser-list/",
                    "https://www.nsx.com.au/regulation/companies/nominated-adviser/"):
            self.assertIn(url, nsx)
        self.assertIn("not a licence, certification or endorsement", nsx)
        svc = self.read("services.html")
        self.assertIn("pending confirmation by ACTP", svc)
        self.assertIn("not offered or implied here", svc)
        self.assertIn('href="nsx-adviser.html"', svc)
        self.assertIn('href="contact.html"', svc)

    def test_no_invented_claims(self):
        for name in self.H1:
            main = re.search(r"<main.*?</main>", self.read(name), re.S).group(0).lower()
            self.assertNotRegex(main, r"testimonial|award|years of experience|since 19|since 20(?!22)|our clients|our team|guarantee[sd]? (?:admission|success|results)", name)
            self.assertNotRegex(main, r"message sent|thank you for", name)
            if name != "contact.html":
                self.assertNotIn("<form", main, name)

    def test_insights_genuine_empty_state(self):
        main = re.search(r"<main.*?</main>", self.read("insights.html"), re.S).group(0)
        self.assertIn("There are no published insights available yet.", main)
        self.assertNotIn('role="status"', main)
        for bad in ("<article", "<time", "Read more", "<img", "<li"):
            self.assertNotIn(bad, main)

    def test_contact_accessible_and_truthful(self):
        html = self.read("contact.html")
        main = re.search(r"<main.*?</main>", html, re.S).group(0)
        self.assertIn("not a confirmed ACTP-owned mailbox", main)
        self.assertNotIn("no enquiry form yet", main.lower())
        self.assertIn('href="mailto:contact@arris.com.my"', main)
        self.assertRegex(main, r'href="tel:\+[0-9]+"')
        self.assertIn(self.NSX, main)
        self.assertIn('<main id="main" tabindex="-1">', html)
        self.assertIn('src="assets/actp-logo-432.png" width="432" height="146"', html)
        # fail closed: the form is inert inside a template; the visible default is the unavailable notice
        self.assertNotRegex(re.sub(r"<template.*?</template>", "", main, flags=re.S), r"<form|<input|<textarea|<button")
        notice = re.search(r'<div id="form-availability".*?</div>', main, re.S).group(0)
        self.assertIn("not available", notice)
        self.assertIn("nothing can be sent", notice)
        self.assertIn('href="contact-submit.php?form=1"', notice)
        form = re.search(r"<template id=\"enquiry-form-template\">(<form.*?</form>)</template>", main, re.S).group(1)
        self.assertIn('method="post"', form)
        self.assertIn('action="contact-submit.php"', form)
        for name in ("name", "email", "organisation", "message"):
            self.assertRegex(form, rf'<label for="field-{name}">')
            self.assertRegex(form, rf'id="field-{name}" name="{name}"')
        self.assertRegex(form, r'type="email"[^>]*autocomplete="email"')
        self.assertIn('autocomplete="name"', form)
        self.assertRegex(form, r'<button class="button" type="submit">')
        self.assertIn('id="form-status"', main)
        # honeypot is hidden from assistive tech and keyboard
        self.assertRegex(form, r'aria-hidden="true">.*?name="website" tabindex="-1"')
        # visible text says what the form can and cannot promise
        self.assertIn("not confirmation that anyone has read it", main)
        self.assertNotRegex(main, r"(?i)<input[^>]*type=\"hidden\"")
        self.assertNotRegex(html, r"smtp|password|mail_to")

    def test_secondary_page_css(self):
        css = all_css()
        self.assertRegex(css, r"\.page-boundary\s*\{[^}]*background:\s*var\(--color-white\)")
        self.assertIn(".contact-list a", css)
        self.assertIn("min-height: 44px", css)
        self.assertIn("minmax(0, 1fr)", css)


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
