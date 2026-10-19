# Insights: empty state and future article pattern

## Current state

The homepage "Insights" section (`index.html`, `.insights`) shows a plain empty state: "There are no published insights available yet." `insights.html` shows the same empty state under its own H1, with links to `nsx-adviser.html` and `index.html`. The homepage section holds no article cards, images, dates, categories, "Read more" links or promised publication schedule. Its links go to `nsx-adviser.html` and `insights.html`. The decorative linework is `aria-hidden`; the empty-state panel is a `role="status"` region.

## Publishing rule

An article is published only with ACTP-approved copy, a named author or attributed source, a real publication date and permission for any image. Factual claims about NSX or Arris carry the source link and the boundaries in `content-sources.md`. No placeholder or draft articles are committed.

## Article card pattern (for when the first approved article exists)

Replace the `.insights__empty` panel with a list of articles; keep the section heading, `.insights__lead` is replaced by a short approved introduction.

Each card is an `<article>` inside `<ul class="insights__list">` (one `<li>` per article) with these fields, in DOM order:

1. Category: short label (`<p class="eyebrow">`), taken from a fixed approved category list.
2. Featured image: optional. Use `<img>` with explicit `width`/`height`, `loading="lazy"` and meaningful `alt`; omit the image entirely when no licensed image exists (the card layout must work without one).
3. Publication date: `<time datetime="YYYY-MM-DD">` with the real date.
4. Title: `<h3>` containing the link to the article page, so the heading itself is the link.
5. Short description: one or two sentences, plain text.
6. Read-more link: `<a>` to the real article URL whose accessible name includes the article title (for example, visually hidden title text). It exists only when the target page exists.

Layout: one column below 768px, two columns from 768px, three from 1280px, using `minmax(0, 1fr)`; no fixed-height cards; long titles wrap. Cards are visible without JavaScript; any reveal effect follows the `.js` progressive-enhancement and reduced-motion rules in `design-system.md`.

When the first article is added, update `insights.html` the same way, remove the empty-state text and its tests, and add tests that every card link resolves to an existing file.
