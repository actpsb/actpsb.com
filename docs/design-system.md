# ACTP design direction (2026-10-19)

Design authority: supplied logo at `assets/actp-logo.png` (841×284); preserve the original. Shooshy unavailable; Chase specifies and Dexter implements. Editorial corporate advisory, not a generic card grid: open off-white canvas, asymmetrical two-column hero, forest services field, restrained typographic NSX explainer, timeline, honest insights empty state, teal contact field. Original logo-inspired geometric linework is preferable to unlicensed stock or invented people/offices. No gold/navy. Alternate scale, rhythm and composition across sections.

## Color evidence and tokens

Canvas sampling of the actual PNG via browser `CanvasRenderingContext2D.getImageData`, grouping green/teal pixels into 16-channel buckets (`g > 1.25r`, `b > 1.1r`, `r < 175`), yielded most common buckets RGB (0,112,112) 8053 px, (0,144,128) 7088 px, (0,128,128) 6962 px, (0,96,96) 6822 px, (16,160,144) 5224 px. These are quantized samples of gradient artwork, NOT exact brand specifications. Adopt provisional accessible UI tokens: forest `#004D45`, dark `#003B36`, teal `#008F83`, accent `#00A896`, canvas `#F8FAF9`, white `#FFFFFF`, text `#1C2926`, muted `#667570`, line `#DCE6E2`. Verify text and focus contrast against actual surfaces, including hover states, to WCAG 2.2 AA (normal 4.5:1; large 3:1); brighter teal is decorative or on dark surfaces unless measured. Do not use white on light teal without contrast verification.

## Typography and spacing

Manrope headings, Inter body, font-display swap, preconnect only if remote font loading is chosen, robust system sans fallbacks and no render-blocking imports. Hero clamp(42px, 6vw, 80px), section titles clamp(32px, 4vw, 56px), card titles 22–28px, body 16–18px, labels 12–14px with sufficient contrast. Scale 8/16/24/32/48/64/80/96/120px; content max 1280px, reading measure ~680px. Vertical section padding 48–72 mobile, 72–96 tablet, 96–128 desktop. Break based on composition rather than arbitrary devices; no overflow at 320px.

## Interaction

Floating bounded sticky navigation, logo left, links/CTA right; mobile native button with aria-expanded and controlled menu; Escape closes, focus returns to trigger, outside dismissal and logical focus order; keep links accessible without JS. Visible focus, 44px touch targets. Hover 180–250ms, section reveal 500–700ms only on enhancement class activated by JS; content visible by default. `prefers-reduced-motion: reduce` removes movement and smooth scrolling. No scroll hijack or essential content obscured. Consistent accessible responsive header/footer across pages.
