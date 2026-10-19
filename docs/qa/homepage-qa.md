# Homepage responsive and functional QA (ACTP-018)

Scope: `index.html` at commit 932aac9 (origin/main), served locally with `python -m http.server`, Chromium via CDP (headless, 15px scrollbar). No Lighthouse score is recorded; none was run.

## Viewports (320 / 375 / 768 / 1024 / 1440)

Full-page screenshots: `screenshots/home-<width>.png`. Measured after scrolling the full page.

| Width | scrollWidth (innerWidth) | Elements outside viewport | Nav |
|---|---|---|---|
| 320 | 320 (320) | 0 | Menu button, list collapsed |
| 375 | 375 (375) | 0 | Menu button, list collapsed |
| 768 | 753 (768; scrollbar) | 0 | Menu button, list collapsed |
| 1024 | 1009 (1024; scrollbar) | 0 | Inline links, no button |
| 1440 | 1425 (1440; scrollbar) | 0 | Inline links, no button |

No horizontal overflow at any width. `viewport-320-top.png` shows the 320px hero with no clipped text.

## Keyboard, menu, Escape (375px, real key events)

- Skip link is the first Tab stop.
- Enter and Space on the Menu button open the list (`aria-expanded=true`, list unhidden). Tab moves to Home.
- Escape closes the list and returns focus to the Menu button, after both Enter and Space opening.
- A click outside the nav closes it. Open state at 375px: `screenshots/menu-open-375.png`; at 768px: `menu-open-768.png`.
- Desktop (1440) tab order: skip link, logo, Home, About Us, Services, NSX Adviser, Insights, Contact, then body links. Every stop shows a 3px solid outline (`focus-visible-1440.png`).

## Reduced motion

With `prefers-reduced-motion: reduce`, no `.reveal` class is applied and all content panels compute opacity 1 (`reduced-motion-1440.png`). Without it, 14 reveal targets are set up and revealed on scroll or after the 3s safety timer.

## JavaScript disabled (375 and 1440)

The `js` class is absent, there are no `.reveal` elements, panels have opacity 1, the nav list is displayed and the Menu button is hidden. There is no overflow (`nojs-375.png`, `nojs-1440.png`).

## Links

All 35 anchors on the page: internal targets (`index.html`, `about.html`, `services.html`, `nsx-adviser.html`, `insights.html`, `contact.html`, `#main`) return 200. External: four NSX/Arris URLs (not fetched; destinations are named in the link text). `mailto:` and `tel:` are non-HTTP. No dead `#` anchors. No broken images.

## Defects

None found in this pass. Limits: Chromium only; no real-device or Safari/Firefox testing; screenshots reviewed at downscaled size for full pages, with 320px and open-menu views reviewed at full size.
