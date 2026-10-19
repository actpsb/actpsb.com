# Performance testing and optimisation (ACTP-020)

Base: `bb1f7d336ece703c2999aabb8401028c1c4bddd6` (origin/main at start). Pages: `index.html`, `about.html`, `services.html`, `nsx-adviser.html`, `insights.html`, `contact.html`.

This is a lab measurement from one machine, not a production or field result and not a WCAG conformance claim.

## Environment and method

- Lighthouse 13.5.0 CLI (installed in a scratch directory, not committed), HeadlessChrome 156 (`--headless=new --no-sandbox`), Linux x86_64 server.
- Site served by `python3 -m http.server` on 127.0.0.1. Mobile uses Lighthouse's default mobile emulation with simulated throttling; desktop uses `--preset=desktop`. One run per page and form factor.
- Limitations: no HTTP compression, no cache headers and no HTTP/2 from the Python server, so transfer sizes and the Lighthouse "cache lifetime" and compression findings do not reflect production hosting. Lighthouse warned that the host CPU is slower than it expects for mobile. Single run per URL, so small variance (a few points) is expected. No WebPageTest, real device or field data (CrUX) exists because the site is not deployed.

## Baseline (before changes)

Performance / Accessibility / Best Practices / SEO:

| Page | Mobile | Desktop |
|---|---|---|
| index | 91 / 96 / 96 / 100 | 100 / 96 / 96 / 100 |
| about | 92 / 96 / 96 / 100 | 100 / 95 / 96 / 100 |
| services | 92 / 96 / 96 / 100 | 100 / 95 / 96 / 100 |
| nsx-adviser | 92 / 96 / 96 / 100 | 100 / 95 / 96 / 100 |
| insights | 92 / 100 / 96 / 100 | 100 / 100 / 96 / 100 |
| contact | 92 / 96 / 96 / 100 | 100 / 96 / 96 / 100 |

Findings: mobile CLS 0.17 on every page; `.eyebrow` contrast 4.39:1 (A11Y-1); a console 404 for `/favicon.ico` (Best Practices 96); the 108 KB 841x284 logo served at about 104-144 CSS px (Lighthouse estimated 105 KiB saving).

## Changes

1. Layout shift (CLS 0.17 to 0): on narrow screens the page rendered the full link list until `main.js` added `.js` and collapsed it. A rule inside `@media (scripting: enabled) and (max-width: 1023.98px)` now hides the menu and keeps the header sticky before the script runs. With scripting disabled the media query does not match, so every link stays visible (checked below).
2. Logo: `assets/actp-logo-432.png` (432x146, 31 KB, same artwork resampled) is used by the five pages this task owns. The original `assets/actp-logo.png` (841x284, 108,400 bytes) is untouched, still required by tests as the original asset, and still used by `contact.html`.
3. `favicon.ico` (48x48, the peak symbol cropped from the logo, 2.9 KB) at the site root removes the console 404; browsers request this path without a `<link>`.
4. A11Y-1: `--color-muted` is now `#5f6e69` (4.87:1 on soft, 5.11:1 on canvas, 5.36:1 on white). `docs/design-system.md` and the token test are updated.
5. A11Y-2: `<main id="main" tabindex="-1">` on five pages and `main:focus { outline: none }`.
6. A11Y-3: `role="status"` removed from the static `.insights__empty` on `index.html` and `insights.html`; the tests now assert it is absent.

There is no web font, no third-party request, no image besides the logo and inline SVG art, one 2.7 KB script (deferred) and four small stylesheets (about 5 KB gzipped together). I did not add a build step, minification, bundling or a new font; none is warranted, and the `unminified-css` and `unused-css-rules` findings are 4 KiB and about 14 KiB respectively before compression.

## Results after changes

Performance / Accessibility / Best Practices / SEO (the Lighthouse agentic-browsing category is not part of the targets and is omitted):

| Page | Mobile | Desktop |
|---|---|---|
| index | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 |
| about | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 |
| services | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 |
| nsx-adviser | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 |
| insights | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 |
| contact | 99 / 100 / 100 / 100 | 100 / 100 / 100 / 100 |

Mobile LCP 1.4 to 1.8 s, CLS 0, TBT 0 ms on all pages. Every page meets the targets (Performance 90+, others 95+) in this lab setup.

## Behaviour verified after the changes (Chromium via CDP, `about.html` and `index.html`)

- 375px keyboard: first Tab stop is the skip link; the third is Menu. Enter opens the menu (`aria-expanded=true`), Escape closes it and returns focus to Menu, Space opens it again, Tab then reaches Home.
- Skip link: Enter sets `#main` and `document.activeElement` is `main`; `main` has no outline; the next Tab lands on the first link inside main.
- JavaScript off at 375px: the `js` class is absent, the Menu button is hidden and the nav list has `display: flex`, so all links remain reachable.
- Reduced motion: no `.reveal` elements and `scroll-behavior: auto`.
- 1280px: nav list visible, Menu button hidden.
- All six pages: `python -m unittest discover -s tests` (70 tests) passes, and Lighthouse ran on each page.

## Residual issues and handoffs

- `contact.html` is owned by ACTP-016 (Dexter) and was not edited. It still needs: `tabindex="-1"` on `<main id="main">` (A11Y-2); removal of `role="status"` from `.page-boundary` (A11Y-3), which also needs `tests/test_site.py` `test_contact_accessible_and_truthful` updated (if the form replaces that paragraph this may already be resolved); the `assets/actp-logo-432.png` logo reference with width/height 432x146 (the page scored 99 mobile Performance with the 841px logo). The contact-page contrast and CLS fixes are already effective because they are in shared CSS.
- No contact backend delivery exists in this task. The contact page states that no enquiry form is in place; ACTP-016 owns the approved cPanel, PHP and SMTP work.
- Production behaviour is unmeasured: the host must supply compression and caching (see below). Lighthouse "cache lifetime" and compression results will differ.
- Chromium only; no Safari, Firefox, screen reader or real device test.
- Canonical URLs, sitemap, `og:url` and `og:image` remain withheld until the production origin is confirmed (ACTP-017). Metadata, titles, descriptions, landmarks, one H1 and `aria-current` were rechecked on the six pages after the SEO commit: unchanged by this task apart from the `main` attribute above, with SEO category 100 on all pages.

## Deployment instructions (not deployed)

The site is static; upload the repository contents (HTML, `assets/`, `favicon.ico`, `robots.txt`) to the web root. No build step. Recommended server settings, which this task did not apply:

- Enable gzip or Brotli for HTML, CSS, JS and SVG.
- `Cache-Control: public, max-age=31536000, immutable` is safe only for versioned file names; the assets here are unversioned, so use a moderate `max-age` (for example 1 week) for `assets/` and `favicon.ico`, and `no-cache` for HTML, or rename assets when they change.
- Serve over HTTPS (Best Practices) with a correct `text/html; charset=utf-8` content type.
- After deploying, rerun Lighthouse against the production URL and record the result here; those numbers replace the lab values above.
