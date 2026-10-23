# Insights: company logos and future article pattern

## Current state

The homepage Success Stories section presents Nuren Group and Actcelerate International Group Limited as responsive transaction cards. Its content is unchanged by the Insights expansion. There is no carousel, video or PDF link in that section. The supporting Nuren admission PDF is retained as source material for the milestone dates, rather than linked from a public page.

At ACTP's request on 22 October 2026, `insights.html` now presents four company profiles rather than an article empty state. Nuren and Arris appear under Milestones & Appointments; Actcelerate and Sydney Sunny Glass appear under Nominated Adviser Relationships. Cards distinguish a listing milestone from a later adviser appointment, use supplied logos and source links where verified, and do not imply ACTP caused every original listing. The grid has one column on mobile and two from 768px, and works without JavaScript. A shared contact panel closes the page.

On 23 October 2026 the owner requested shorter milestone copy: the first two labels now read “ACTP's Role”, Nuren displays “Listed on 6th August 2024”, and Arris displays “Appointed on 1st November 2022” after the owner confirmed the appointment wording rather than a listing-date claim. Both explanatory milestone paragraphs were removed. The Sydney Sunny Glass card omits “Historical” and the delisting sentence, while retaining past-tense relationship wording and the AG1 identity clarification. These editorial removals do not establish current listing or adviser status.

## Copy sources

- Nuren's business overview follows its [corporate website](https://nurengroup.com/), without repeating unverified market-leadership claims.
- The supplied `assets/documents/nuren-group-nsx-admission.pdf` is an NSX letter dated 2 August 2024: admission was to occur that day, while first quotation was scheduled for 6 August 2024. The homepage uses the quotation date, also identified in Nuren's commencement announcement, rather than conflating these milestones. The statement is historical, not a claim of current listing status; NSX's NRN record now records removal on 30 June 2026.
- ACTP supplied research identifying Actcelerate International Group Limited (NSX: ACT), its focus on high-growth SMEs in Southeast Asia and Australia, and its investment sectors: financial services, information and communication technology, innovative retail and green technology. The homepage condenses that research to match Nuren's profile structure. [NSX's ACT record](https://www.nsx.com.au/marketdata/company-directory/details/ACT/) corroborates its diversified investment activity, 2 July 2018 listing date, trading code and ACTP's nominated adviser role. The earlier Ausgold identity ambiguity is resolved by ACTP's supplied Actcelerate research and replacement logo.
- The homepage contact sentence is a short invitation covering listing exploration, market preparation and ongoing obligations; the detailed entry-requirements sentence was replaced at ACTP's request.
- ACTP confirmed `contact@actpsb.com` as the public contact email on 23 October 2026. All page footers now use it; live operation and inbox delivery remain unverified (see `contact-backend.md`).
- Arris' [announcement dated 1 November 2022](https://www.nsx.com.au/ftp/news/021741547.PDF) records ACTP's appointment after the prior adviser's resignation. It is not evidence of ACTP managing Arris' original listing. The official list and ACTP profile contain inconsistent historical listing dates, so the Insights card uses the verified appointment date instead. At the owner's request, its public source link is now [Arris' NSX Records](https://www.nsx.com.au/marketdata/company-directory/AR2/); the announcement remains supporting evidence here.
- [NSX's official list](https://www.nsx.com.au/marketdata/official-list/) identifies ACTP as adviser for Arris (AR2) and Actcelerate (ACT). Actcelerate's 2018 listing predates ACTP's September 2022 recognition; it is shown as an adviser relationship, not an ACTP-led IPO.
- ACTP directly confirmed the Sydney Sunny Glass nominated adviser relationship, supplied the branded image, and subsequently provided [NSX's AG1 record](https://www.nsx.com.au/marketdata/company-directory/AG1/) as the corresponding company record. The Sydney-to-AG1 association and adviser role are owner-confirmed; the NSX overview verifies the issuer name Australia Sunny Glass Group Limited and delisting on 18 December 2025. The card retains past-tense relationship copy and links the official record, without implying current NSX listing or an ACTP-led original admission.

## Logo assets

Logos live in `assets/images/`. The supplied images have been renamed according to the visible artwork:

- `nuren-group-logo.png`: displayed for Nuren Group.
- `actelerate-international-group-logo.png`: the replacement supplied by ACTP, visibly identifying Actcelerate International Group Limited; replaces the former Ausgold asset. The filename preserves the supplied spelling. The white artwork uses a dark background for visibility.
- `sydney-sunny-glass-logo.png`: displayed for the owner-confirmed Sydney Sunny Glass adviser relationship associated by ACTP with Australia Sunny Glass Group Limited (AG1).
- `arris-holding-logo.png`: displayed for Arris Holdings Berhad using ACTP's supplied artwork.

Preserve logo proportions with contain sizing. Do not invent logos or add broken image references.

## Publishing rule

An article is published only with ACTP-approved copy, a named author or attributed source, a real publication date and permission for any image. Factual claims about NSX or Arris carry the source link and the boundaries in `content-sources.md`. No placeholder or draft articles are committed.

## Article card pattern (for when the first approved article exists)

For future articles on `insights.html`, add a separately labelled article section and keep the page heading and company profiles. The homepage company grid remains separate.

Each card is an `<article>` inside `<ul class="insights__list">` (one `<li>` per article) with these fields, in DOM order:

1. Category: short label (`<p class="eyebrow">`), taken from a fixed approved category list.
2. Featured image: optional. Use `<img>` with explicit `width`/`height`, `loading="lazy"` and meaningful `alt`; omit the image entirely when no licensed image exists (the card layout must work without one).
3. Publication date: `<time datetime="YYYY-MM-DD">` with the real date.
4. Title: `<h3>` containing the link to the article page, so the heading itself is the link.
5. Short description: one or two sentences, plain text.
6. Read-more link: `<a>` to the real article URL whose accessible name includes the article title (for example, visually hidden title text). It exists only when the target page exists.

Layout: one column below 768px, two columns from 768px, three from 1280px, using `minmax(0, 1fr)`; no fixed-height cards; long titles wrap. Cards are visible without JavaScript; any reveal effect follows the `.js` progressive-enhancement and reduced-motion rules in `design-system.md`.

When the first article is added, add tests that every article link resolves to an existing file. Company profiles must not be given fabricated article dates or authors.
