# SEO and metadata

Scope: six pages (`index`, `about`, `services`, `nsx-adviser`, `insights`, `contact`).

## Per-page metadata

Each page has a unique `<title>`, `meta description`, `og:title`, `og:description` (equal to the title and description), plus `og:site_name`, `og:type`, `og:locale` and `theme-color`. `tests/test_seo.py` enforces uniqueness and parity.

## Hosting-dependent items (deliberately absent)

The production origin is not confirmed, and no deployment has been made. Therefore:

- No `<link rel="canonical">`, `og:url`, `og:image`, or JSON-LD `url`/`BreadcrumbList` (all need absolute URLs).
- No `sitemap.xml` (the sitemap protocol requires absolute URLs), and `robots.txt` has no `Sitemap:` line. It allows all crawling.

When the origin is confirmed, add canonical and `og:url` to each page, an absolute-URL `sitemap.xml` for the six routes, the `Sitemap:` line, and a 1200x630 `og:image` once an approved image exists. `tests/test_seo.py` fails if any of these appear before the origin is recorded in `ORIGIN_CONFIRMED`.

## Structured data

Home carries a minimal schema.org `Organization` (name, NSX-sourced description, `sameAs` the NSX profile). Address, phone, email, Arris `parentOrganization` and services are excluded until owner confirmation (see `content-sources.md`).

## Assets and fonts

No web fonts or third-party requests; `--font-heading`/`--font-body` fall back to system stacks. The logo has intrinsic `width`/`height`, `decoding="async"` and `fetchpriority="high"` (above the fold, so not lazy-loaded). Pages serve the 432x146 `actp-logo-432.png`; the 108 KB 841x284 PNG remains the unmodified original asset.
