# Sitewide accessibility audit (ACTP-019)

Audited snapshot: `e2cf4f0d4303c10cde5b257562e4d3853a6359c7` (freshly fetched `origin/main`, includes ACTP-015 secondary pages and the first SEO commit). Pages: `index.html`, `about.html`, `services.html`, `nsx-adviser.html`, `insights.html`, `contact.html`.

This is a test record, not a WCAG conformance claim or certification. Parallel SEO work (ACTP-017) can change metadata and landmarks after this snapshot; ACTP-020 must recheck them.

## Method

- Served the snapshot with `python3 -m http.server` on 127.0.0.1 and drove Chromium through CDP: real `Input.dispatchKeyEvent` Tab, Enter, Space and Escape events, `Emulation.setDeviceMetricsOverride`, `Emulation.setScriptExecutionDisabled` and `Emulation.setEmulatedMedia`.
- Contrast: computed from rendered `getComputedStyle` colours, walking up to the first non-transparent background, using the WCAG relative-luminance formula. 4.5:1 for normal text, 3:1 for large text (24px, or 18.66px bold) and focus rings. Text inside `aria-hidden` or `hidden` is skipped. The Chromium viewport has a 15px scrollbar, so a 1280 window reports 1265 content width.
- Structure: DOM queries for landmarks, heading outline, accessible names, duplicate ids, `aria-labelledby` targets and image alt text.
- Phone links: the `tel:` hrefs were read as raw bytes (hex) from each file rather than from rendered or masked output.

## Result summary

| Area | Result |
|---|---|
| Keyboard traversal and focus visibility | Pass |
| Menu Escape and focus return | Pass |
| Headings, landmarks, accessible names | Pass, with one advisory |
| Text contrast | 1 defect (A11Y-1) |
| Forms | Not applicable; no form exists, which the page states truthfully |
| 320px, 256px, zoom-equivalent reflow, text spacing | Pass |
| JavaScript off | Pass |
| Reduced motion | Pass |
| Contact links | Pass |

## Findings

### A11Y-1 (defect, WCAG 1.4.3 Contrast Minimum): eyebrow text on the soft surface is 4.40:1

`.eyebrow` text uses `--color-muted` (#667570) at about 12.8px. Over `--color-soft` (#F1F5F3) this is 4.396:1, below 4.5:1. Over `--color-canvas` (#F8FAF9) it is 4.61:1 and passes. `docs/design-system.md` lists muted for canvas only, so the soft surface is outside the documented pairing.

Affected (6 instances): `index.html` "Company introduction" and "Illustrative process"; `about.html` "The group"; `services.html` "Next steps"; `nsx-adviser.html` "The role"; `contact.html` "Form". `insights.html` has none. Of 97, 46, 47, 49, 28 and 36 text nodes checked on the six pages respectively, these were the only failures.

Reproduce: load a page, run the contrast walk above, or compute `#667570` against `#F1F5F3`.

### A11Y-2 (advisory, not a confirmed defect): skip-link target is not focusable

`<main id="main">` has no `tabindex="-1"`. After activating the skip link the URL hash is `#main` but `document.activeElement` is not inside main. Chromium sets the sequential focus starting point at the fragment target, so the next Tab is expected to land inside main; I did not verify that next-Tab landing and did not test Safari or Firefox, where behaviour differs historically. Recommend adding `tabindex="-1"` to main (and checking the outline is suppressed only for programmatic focus), then retesting.

### A11Y-3 (advisory): `role="status"` on static content

`index.html` `.insights__empty` and `contact.html` `.page-boundary` carry `role="status"` but never change after load. A live region only announces updates, so this has no effect for most assistive technology, and no harm was observed. Consider removing the role and leaving them as plain paragraphs.

## Passing evidence

### Keyboard, focus and Escape

- Desktop (1280) Tab order on `contact.html`: skip link, logo, Home, About Us, Services, NSX Adviser, Insights, Contact, page links, then the footer links. No traps, order matches visual order.
- Skip link is the first Tab stop on `index.html`; Enter moves to `#main`.
- 375px on `about.html`: stops are skip link, logo, Menu. Enter and Space each open the menu (`aria-expanded` true, list unhidden); Tab enters Home; Escape closes it and returns focus to Menu, after both Enter and Space. Tabbing past the last menu link closes the menu.
- Real-Tab focus ring on every stop of all six pages (19 to 35 stops each): 3px solid, all `:focus-visible`. Dark-field stops use bright teal against forest or forest-dark at 4.21:1 to 5.38:1; light-field stops use forest-dark. Lowest measured ratio 4.21:1, above the 3:1 threshold.
- Interactive targets measured at least 44px high for nav links, buttons and the Menu button. A few inline prose links measure under 24px; WCAG 2.5.8 exempts targets inside a sentence.

### Headings, landmarks, names

- Every page has one `<main>`, lang `en`, one H1 and no skipped heading levels; each page has a unique `<title>` and the matching nav link has `aria-current="page"`.
- Landmarks: header, nav "Primary", main, footer, nav "Footer"; the homepage also has an aside labelled by its heading.
- No unnamed links or buttons, no duplicate ids, no broken `aria-labelledby`, no image without alt (the logo alt describes it, decorative SVGs are `aria-hidden`).
- External link text names the destination (for example "Source: NSX adviser profile", "(external)"). `rel` attributes are not an accessibility matter and were not assessed.

### Phone and email links

All seven `tel:` hrefs (one per page, two on `contact.html`) contain the bytes `tel:+603****3063`, a valid E.164 URI. Any masked rendering in tool output is display only. The `mailto:` links are plain addresses. The contact page says the details are an NSX-listed Arris group listing and not confirmed ACTP-owned.

### Forms

There is no form, input, select or textarea on any page, so there is no error semantics to test. `contact.html` says no enquiry form exists and why, which matches the page's actual state.

### Reflow, zoom, text spacing

- At 320px (305px content width) and 256px (equivalent to 1280px at 500% zoom), all six pages have no horizontal overflow, no element extending past the viewport and no clipped text.
- With 1.5 line-height, 0.12em letter-spacing, 0.16em word-spacing and 2em paragraph spacing forced at 375px, there was no overflow or clipping on any page.
- A true browser zoom control and 200% text-only resize were not exercised; viewport narrowing is the proxy.

### JavaScript off (375 and 1280)

On all six pages the `js` class is absent, the Menu button is not shown, all six nav links are visible, no `.reveal` elements exist and no content panel has opacity below 1. No overflow.

### Reduced motion

With `prefers-reduced-motion: reduce`: no `.reveal` class is applied, panels are fully visible, `scroll-behavior` is `auto`, and no element has an animation or transition. With no preference, the homepage sets up 14 reveal targets and `scroll-behavior` is `smooth`; 13 are below the fold and start hidden until scrolled or the 3s safety timer fires.

## Limitations

- Chromium only, via CDP, headless-style viewport emulation. No Safari, Firefox, real device, touch screen reader or magnification software.
- No screen reader (NVDA, JAWS, VoiceOver, TalkBack) was run; accessible names, landmark and heading findings come from the DOM, not from announced output.
- Contrast is computed from solid computed colours. Text over images or gradients would need separate checks; none exist on these pages.
- Colour-blindness, forced-colors/high-contrast mode, print and voice control were not tested.
- Browser Ctrl-plus zoom and text-only zoom were approximated by viewport width and spacing overrides.
- External links were not fetched. Links to local pages were not re-crawled here; see `homepage-qa.md` for the homepage pass.
- Rendered state changes from SEO commits after the audited SHA are not covered.

## Required fixes for ACTP-020

1. A11Y-1: make eyebrow text on `--color-soft` meet 4.5:1, e.g. use `--color-text` or `--color-forest` for `.eyebrow` on `.section--soft`, or darken `--color-muted` to at least 4.6:1 against #F1F5F3 while keeping canvas passing. Update `docs/design-system.md` pairing table to match. Retest all six pages.
2. A11Y-2: add `tabindex="-1"` to `<main id="main">` on all six pages, confirm focus moves into main on skip-link activation and next Tab goes to the first control in main, and that no persistent outline shows on mouse focus.
3. A11Y-3: remove `role="status"` from the two static elements, or justify and test it.
4. Recheck after SEO merges: title, description, `h1`, landmark and `aria-current` state on every page, and rerun the checks in this report against the final main.

ACTP-019 delivers this audit only. The defects above are unresolved until ACTP-020 fixes and retests them.

## ACTP-020 remediation and verification

Verified on the ACTP-020 branch based on `bb1f7d336ece703c2999aabb8401028c1c4bddd6`; measurements and method are in `docs/qa/performance.md`.

| Finding | Status | Verification |
|---|---|---|
| A11Y-1 eyebrow contrast | Fixed | `--color-muted` is now `#5f6e69`: 4.87:1 on `--color-soft`, 5.11:1 on canvas. Lighthouse `color-contrast` passes on all six pages (Accessibility 100). |
| A11Y-2 skip-link target | Fixed on five pages | `<main id="main" tabindex="-1">`; after Enter on the skip link `document.activeElement` is `main` with no outline, and the next Tab reaches the first link inside main. `contact.html` is owned by ACTP-016 and is still open there. |
| A11Y-3 static `role="status"` | Fixed on `index.html`, `insights.html` | Role removed, tests assert absence. `contact.html` `.page-boundary` is owned by ACTP-016 and is still open there. |

Rechecked after the SEO commit: titles, descriptions, landmarks, one H1 and `aria-current` are intact. Keyboard, menu (Enter, Space, Escape, focus return), JavaScript-off and reduced-motion behaviour were retested after the fixes with the same results as above. This remains a test record, not a conformance claim.
